"""
Preload Mode Engine — Shopify Checkout Session Pre-creation

Reverse engineered from Valor AIO's "Preload" mode:
  - Pre-carts a cheap in-stock item before the drop
  - Holds a live checkout session (session cookies stay warm)
  - At drop time: clears cart → adds target → submits payment on the SAME session
  - Eliminates queue/checkpoint for the actual product

Key Valor settings replicated:
  mode: "Preload"
  delayStart: 550 (ms before session creation)
  stopAfter: 80-180 (seconds before giving up)
  checkpointAutoRunLink: true
  autoSwitchMode: true (fallback to Normal/Fast on detection)
"""

import asyncio
import time
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import structlog

from ..core.proxy import Proxy
from ..core.profile import Profile
from .session import CheckoutSession as SessionFactory

logger = structlog.get_logger()


class PreloadState(Enum):
    """Lifecycle states for a preloaded session"""

    IDLE = "idle"
    WARMING = "warming"  # Finding a cheap item to pre-cart
    SESSION_ACTIVE = "active"  # Checkout session held open
    SWAPPING = "swapping"  # Clearing cart and adding target product
    CHECKING_OUT = "checking_out"  # Submitting payment
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class PreloadedSession:
    """A pre-created Shopify checkout session"""

    id: str
    site_url: str
    state: PreloadState = PreloadState.IDLE

    # Session data
    http_session: Any = None  # The warm HTTP client (cookies intact)
    checkout_url: Optional[str] = None
    checkout_token: Optional[str] = None
    shop_id: Optional[str] = None

    # Pre-cart item
    precart_variant_id: Optional[int] = None
    precart_product_name: Optional[str] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    session_created_at: Optional[datetime] = None
    last_keepalive: Optional[datetime] = None
    expires_at: Optional[datetime] = None  # Session timeout

    # Config
    stop_after_seconds: int = 120
    keepalive_interval: int = 30  # Ping session every N seconds

    @property
    def is_alive(self) -> bool:
        if not self.session_created_at:
            return False
        elapsed = (datetime.now() - self.session_created_at).total_seconds()
        return (
            elapsed < self.stop_after_seconds
            and self.state == PreloadState.SESSION_ACTIVE
        )

    @property
    def age_seconds(self) -> float:
        if not self.session_created_at:
            return 0.0
        return (datetime.now() - self.session_created_at).total_seconds()


class PreloadEngine:
    """
    Manages preloaded Shopify checkout sessions.

    Usage:
        engine = PreloadEngine()

        # Before the drop: warm up a session
        session = await engine.create_preloaded_session(
            site_url="https://www.shoepalace.com",
            proxy=my_proxy,
        )

        # At drop time: swap cart and checkout
        result = await engine.swap_and_checkout(
            session_id=session.id,
            target_variant_id=12345678,
            profile=my_profile,
        )
    """

    # Items that are almost always in stock on Shopify stores (cheap accessories)
    PRECART_SEARCH_TERMS = [
        "socks",
        "laces",
        "sticker",
        "keychain",
        "pin",
        "hat",
        "beanie",
        "lanyard",
    ]

    # TTL for products.json cache (seconds) — cheap accessories rarely change
    _PRECART_CACHE_TTL: float = 90.0

    def __init__(self, max_sessions: int = 20):
        self.sessions: Dict[str, PreloadedSession] = {}
        self._session_factory = SessionFactory()
        self._keepalive_tasks: Dict[str, asyncio.Task] = {}
        self._max_sessions = max_sessions
        # Per-domain cache: base_url → (fetched_at, products_list)
        self._precart_cache: Dict[str, Tuple[float, List]] = {}
        logger.info("PreloadEngine initialized", max_sessions=max_sessions)

    # ------------------------------------------------------------------
    # Session Creation
    # ------------------------------------------------------------------

    async def create_preloaded_session(
        self,
        site_url: str,
        proxy: Optional[Proxy] = None,
        stop_after: int = 120,
        delay_start_ms: int = 550,
    ) -> PreloadedSession:
        """Create a preloaded checkout session on a Shopify store.

        1. Find a cheap in-stock item
        2. Add it to cart
        3. Navigate to /checkout to create a live session
        4. Hold the session open with periodic keepalives
        """
        import uuid

        session_id = str(uuid.uuid4())
        base_url = site_url.rstrip("/")

        preloaded = PreloadedSession(
            id=session_id,
            site_url=base_url,
            stop_after_seconds=stop_after,
        )
        self.sessions[session_id] = preloaded

        try:
            # Delay start (Valor uses 550ms)
            if delay_start_ms > 0:
                await asyncio.sleep(delay_start_ms / 1000)

            preloaded.state = PreloadState.WARMING

            # Create HTTP session with TLS evasion
            http_session = await self._session_factory.create(
                proxy=proxy,
                seed=f"preload-{session_id}",
            )
            preloaded.http_session = http_session

            # Step 1: Find a cheap in-stock item to pre-cart
            variant_id, product_name = await self._find_precart_item(
                http_session, base_url
            )

            if not variant_id:
                preloaded.state = PreloadState.FAILED
                logger.error("Preload failed: no suitable precart item", site=base_url)
                return preloaded

            preloaded.precart_variant_id = variant_id
            preloaded.precart_product_name = product_name

            # Step 2: Add precart item to cart
            cart_ok = await self._add_to_cart(http_session, base_url, variant_id)
            if not cart_ok:
                preloaded.state = PreloadState.FAILED
                logger.error(
                    "Preload failed: could not add precart item", site=base_url
                )
                return preloaded

            # Step 3: Navigate to /checkout to create session
            checkout_data = await self._create_checkout_session(http_session, base_url)
            if not checkout_data:
                preloaded.state = PreloadState.FAILED
                logger.error(
                    "Preload failed: checkout session creation failed", site=base_url
                )
                return preloaded

            preloaded.checkout_url = checkout_data["checkout_url"]
            preloaded.checkout_token = checkout_data["checkout_token"]
            preloaded.shop_id = checkout_data.get("shop_id", "")
            preloaded.session_created_at = datetime.now()
            preloaded.state = PreloadState.SESSION_ACTIVE

            logger.info(
                "Preloaded session created",
                session_id=session_id[:8],
                site=base_url,
                precart=product_name,
                checkout_token=preloaded.checkout_token[:8],
            )

            # Step 4: Start keepalive loop
            keepalive_task = asyncio.create_task(self._keepalive_loop(session_id))
            self._keepalive_tasks[session_id] = keepalive_task

            return preloaded

        except Exception as e:
            preloaded.state = PreloadState.FAILED
            logger.error("Preload session creation error", error=str(e))
            return preloaded

    # ------------------------------------------------------------------
    # Cart Swap & Checkout (the money move)
    # ------------------------------------------------------------------

    async def swap_and_checkout(
        self,
        session_id: str,
        target_variant_id: int,
        profile: Profile,
        captcha_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Swap the pre-carted item for the target and checkout.

        This is the critical path — executes at drop time:
        1. Clear cart
        2. Add target variant
        3. Submit customer info (already on checkout page)
        4. Submit shipping
        5. Submit payment
        """
        preloaded = self.sessions.get(session_id)
        if not preloaded or not preloaded.is_alive:
            return {"success": False, "error": "Preloaded session expired or not found"}

        # Stop keepalive — we're going hot
        self._stop_keepalive(session_id)

        preloaded.state = PreloadState.SWAPPING
        session = preloaded.http_session
        base_url = preloaded.site_url

        start_time = time.time()

        try:
            # Step 1: Clear cart
            clear_ok = await self._clear_cart(session, base_url)
            if not clear_ok:
                logger.warning("Cart clear failed, attempting add anyway")

            # Step 2: Add target product
            add_ok = await self._add_to_cart(session, base_url, target_variant_id)
            if not add_ok:
                preloaded.state = PreloadState.FAILED
                return {
                    "success": False,
                    "error": "Failed to add target product to cart",
                }

            # Step 3: Refresh checkout with new cart
            # The session cookies are still warm, so visiting /checkout
            # should reuse the existing checkout session with updated cart
            preloaded.state = PreloadState.CHECKING_OUT

            checkout_data = await self._refresh_checkout(session, base_url)
            if checkout_data:
                preloaded.checkout_url = checkout_data["checkout_url"]
                preloaded.checkout_token = checkout_data["checkout_token"]

            # Step 4: Submit customer info
            info_ok = await self._submit_customer_info(
                session, preloaded.checkout_url, profile
            )
            if not info_ok:
                return {
                    "success": False,
                    "error": "Failed to submit customer info",
                    "checkout_url": preloaded.checkout_url,
                }

            # Step 5: Select shipping
            shipping_ok = await self._submit_shipping(session, preloaded.checkout_url)
            if not shipping_ok:
                return {
                    "success": False,
                    "error": "Failed to select shipping",
                    "checkout_url": preloaded.checkout_url,
                }

            # Step 6: Vault card and submit payment
            from .shopify import ShopifyCheckout, CheckoutSession as ShopifyCS

            checkout_obj = ShopifyCS(
                checkout_url=preloaded.checkout_url,
                checkout_token=preloaded.checkout_token,
                shop_id=preloaded.shop_id or "",
            )

            shopify_checkout = ShopifyCheckout()
            payment_result = await shopify_checkout._submit_payment(
                session, checkout_obj, profile, captcha_token
            )

            checkout_time = time.time() - start_time

            if payment_result.get("success"):
                preloaded.state = PreloadState.COMPLETED
                logger.info(
                    "Preload checkout SUCCESS",
                    session_id=session_id,
                    order=payment_result.get("order_number"),
                    time=f"{checkout_time:.2f}s",
                )
                return {
                    "success": True,
                    "order_number": payment_result.get("order_number"),
                    "checkout_time": checkout_time,
                    "checkout_url": preloaded.checkout_url,
                    "mode": "preload",
                }
            else:
                preloaded.state = PreloadState.FAILED
                return {
                    "success": False,
                    "error": payment_result.get("error", "Payment failed"),
                    "checkout_time": checkout_time,
                    "checkout_url": preloaded.checkout_url,
                    "mode": "preload",
                }

        except Exception as e:
            preloaded.state = PreloadState.FAILED
            logger.error("Preload swap_and_checkout error", error=str(e))
            return {"success": False, "error": str(e)}

        finally:
            # Clean up session and clear the reference so the keepalive
            # loop (if it somehow wasn't cancelled) doesn't use a closed session
            if session:
                try:
                    await session.aclose()
                except Exception:
                    pass
                preloaded.http_session = None

    # ------------------------------------------------------------------
    # Internal: Cart operations
    # ------------------------------------------------------------------

    async def _find_precart_item(self, session, base_url: str) -> tuple:
        """Find a cheap in-stock item to pre-cart.

        Searches products.json for accessories/small items that are
        likely always in stock. Returns (variant_id, product_name).
        Results are cached per domain for _PRECART_CACHE_TTL seconds so
        concurrent session creations for the same store share one fetch.
        """
        try:
            cached = self._precart_cache.get(base_url)
            if cached and (time.time() - cached[0]) < self._PRECART_CACHE_TTL:
                products = cached[1]
                logger.debug("Precart cache hit", site=base_url)
            else:
                response = await session.get(
                    f"{base_url}/products.json?limit=250",
                    headers={"Accept": "application/json"},
                )

                if response.status_code != 200:
                    return None, None

                data = response.json()
                products = data.get("products", [])
                self._precart_cache[base_url] = (time.time(), products)

            # Sort by price ascending — we want the cheapest available item
            candidates = []

            for product in products:
                title = product.get("title", "").lower()
                variants = product.get("variants", [])

                for variant in variants:
                    if not variant.get("available", False):
                        continue

                    price = float(variant.get("price", "9999"))
                    variant_id = variant.get("id")

                    # Prefer items matching our search terms (socks, laces, etc)
                    is_preferred = any(
                        term in title for term in self.PRECART_SEARCH_TERMS
                    )

                    candidates.append(
                        {
                            "variant_id": variant_id,
                            "product_name": product.get("title", "Unknown"),
                            "price": price,
                            "preferred": is_preferred,
                        }
                    )

            if not candidates:
                return None, None

            # Sort: preferred items first, then by price
            candidates.sort(key=lambda x: (not x["preferred"], x["price"]))

            best = candidates[0]
            logger.debug(
                "Precart item found",
                product=best["product_name"][:40],
                price=best["price"],
            )

            return best["variant_id"], best["product_name"]

        except Exception as e:
            logger.error("Find precart item error", error=str(e))
            return None, None

    async def _add_to_cart(self, session, base_url: str, variant_id: int) -> bool:
        """Add a variant to cart via cart/add.js"""
        try:
            response = await session.post(
                f"{base_url}/cart/add.js",
                json={"items": [{"id": variant_id, "quantity": 1}]},
                headers={"Content-Type": "application/json"},
            )
            return response.status_code == 200
        except Exception as e:
            logger.error("Add to cart error", error=str(e))
            return False

    async def _clear_cart(self, session, base_url: str) -> bool:
        """Clear the cart via cart/clear.js"""
        try:
            response = await session.post(
                f"{base_url}/cart/clear.js",
                headers={"Content-Type": "application/json"},
            )
            return response.status_code == 200
        except Exception as e:
            logger.error("Clear cart error", error=str(e))
            return False

    async def _create_checkout_session(
        self, session, base_url: str
    ) -> Optional[Dict[str, str]]:
        """Navigate to /checkout to create a live session"""
        try:
            response = await session.get(f"{base_url}/checkout")

            if response.status_code != 200:
                return None

            checkout_url = str(response.url)

            # Parse checkout token
            match = re.search(r"/checkouts/([a-z0-9]+)", checkout_url)
            if not match:
                return None

            checkout_token = match.group(1)

            shop_match = re.search(r"/(\d+)/checkouts/", checkout_url)
            shop_id = shop_match.group(1) if shop_match else ""

            return {
                "checkout_url": checkout_url,
                "checkout_token": checkout_token,
                "shop_id": shop_id,
            }

        except Exception as e:
            logger.error("Create checkout session error", error=str(e))
            return None

    async def _refresh_checkout(
        self, session, base_url: str
    ) -> Optional[Dict[str, str]]:
        """Refresh the checkout page to pick up the new cart contents.

        Unlike _create_checkout_session, we already have cookies so
        Shopify should update the existing checkout with the new cart.
        """
        try:
            response = await session.get(f"{base_url}/checkout")

            if response.status_code not in (200, 302):
                logger.warning(
                    "Checkout refresh failed",
                    status=response.status_code,
                    site=base_url,
                )
                return None

            checkout_url = str(response.url)

            match = re.search(r"/checkouts/([a-z0-9]+)", checkout_url)
            if not match:
                return None

            return {
                "checkout_url": checkout_url,
                "checkout_token": match.group(1),
            }
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Internal: Checkout form submission
    # ------------------------------------------------------------------

    async def _submit_customer_info(
        self, session, checkout_url: str, profile: Profile
    ) -> bool:
        """Submit customer info on the preloaded checkout"""
        shipping = profile.shipping

        data = {
            "checkout[email]": profile.email,
            "checkout[shipping_address][first_name]": shipping.first_name,
            "checkout[shipping_address][last_name]": shipping.last_name,
            "checkout[shipping_address][address1]": shipping.address1,
            "checkout[shipping_address][address2]": shipping.address2,
            "checkout[shipping_address][city]": shipping.city,
            "checkout[shipping_address][province]": shipping.state,
            "checkout[shipping_address][zip]": shipping.zip_code,
            "checkout[shipping_address][country]": shipping.country,
            "checkout[shipping_address][phone]": profile.phone,
        }

        try:
            response = await session.post(
                checkout_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            return response.status_code in (200, 302)
        except Exception as e:
            logger.error("Submit info error (preload)", error=str(e))
            return False

    async def _submit_shipping(self, session, checkout_url: str) -> bool:
        """Select shipping on the preloaded checkout"""
        try:
            shipping_url = f"{checkout_url}?step=shipping_method"
            response = await session.get(shipping_url)

            if response.status_code != 200:
                return False

            rate_match = re.search(r'data-shipping-method="([^"]+)"', response.text)

            if not rate_match:
                logger.warning(
                    "No shipping rate found in checkout page", url=checkout_url[:60]
                )
                return False

            submit = await session.post(
                shipping_url,
                data={"checkout[shipping_rate][id]": rate_match.group(1)},
            )
            return submit.status_code in (200, 302)
        except Exception as e:
            logger.error("Submit shipping error (preload)", error=str(e))
            return False

    # ------------------------------------------------------------------
    # Keepalive
    # ------------------------------------------------------------------

    async def _keepalive_loop(self, session_id: str):
        """Periodically ping the checkout session to keep it alive.

        Shopify checkout sessions expire after 5-10 minutes of inactivity.
        We send a lightweight GET to the checkout URL to reset the timer.
        """
        preloaded = self.sessions.get(session_id)
        if not preloaded:
            return

        while preloaded.is_alive:
            try:
                await asyncio.sleep(preloaded.keepalive_interval)

                if not preloaded.is_alive:
                    break

                # Lightweight ping — just hit the checkout URL
                if preloaded.http_session and preloaded.checkout_url:
                    response = await preloaded.http_session.get(
                        preloaded.checkout_url,
                    )
                    preloaded.last_keepalive = datetime.now()

                    logger.debug(
                        "Keepalive sent",
                        session_id=session_id,
                        status=response.status_code,
                        age=f"{preloaded.age_seconds:.0f}s",
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Keepalive error", session_id=session_id, error=str(e))

        # Mark expired if we exit the loop
        if preloaded.state == PreloadState.SESSION_ACTIVE:
            preloaded.state = PreloadState.EXPIRED
            logger.info("Preload session expired", session_id=session_id)

    def _stop_keepalive(self, session_id: str):
        """Cancel the keepalive task for a session"""
        task = self._keepalive_tasks.pop(session_id, None)
        if task:
            task.cancel()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active preloaded sessions"""
        return [
            {
                "id": s.id[:8],
                "site": s.site_url,
                "state": s.state.value,
                "precart": s.precart_product_name,
                "age": f"{s.age_seconds:.0f}s" if s.session_created_at else "N/A",
                "checkout_token": s.checkout_token[:8] if s.checkout_token else None,
            }
            for s in self.sessions.values()
        ]

    async def cleanup(self):
        """Clean up all sessions and tasks"""
        for session_id in list(self._keepalive_tasks.keys()):
            self._stop_keepalive(session_id)

        for preloaded in self.sessions.values():
            if preloaded.http_session:
                try:
                    await preloaded.http_session.aclose()
                except Exception:
                    pass

        self.sessions.clear()
        logger.info("PreloadEngine cleaned up")


# Module-level singleton
preload_engine = PreloadEngine()
