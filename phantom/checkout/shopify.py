"""
Shopify Checkout Module
High-speed checkout automation for Shopify stores
"""

import asyncio
import time
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx
import structlog

from ..core.task import Task, TaskResult, TaskStatus
from ..core.profile import Profile
from ..core.proxy import Proxy
from ..evasion.humanizer import Humanizer
from .session import CheckoutSession as SessionFactory

logger = structlog.get_logger()

# Maximum retries when hitting Shopify checkpoint pages
_MAX_CHECKPOINT_RETRIES = 3


@dataclass
class CheckoutSession:
    """Shopify checkout session data"""

    checkout_url: str
    checkout_token: str
    shop_id: str
    payment_url: Optional[str] = None
    shipping_rate_id: Optional[str] = None
    total_price: Optional[float] = None


class ShopifyCheckout:
    """
    Advanced Shopify checkout automation

    Modes:
    - Normal: Standard checkout flow
    - Fast: Pre-filled checkout, minimal waits
    - Safe: Extra delays, human-like behavior
    - Request: Pure HTTP requests (fastest)
    """

    def __init__(self):
        self.session_factory = SessionFactory()
        self.humanizer = Humanizer()
        logger.info("ShopifyCheckout initialized")

    async def checkout(
        self,
        task: Task,
        profile: Profile,
        proxy: Optional[Proxy] = None,
        captcha_solver: Any = None,
    ) -> TaskResult:
        """Execute checkout for a task"""
        start_time = time.time()

        task.update_status(TaskStatus.MONITORING, "Finding product...")

        try:
            # Create session with proxy
            session = await self._create_session(proxy, task.id)

            # Check for password page and attempt bypass
            if await self._is_password_protected(session, task.config.site_url):
                task.update_status(TaskStatus.MONITORING, "Bypassing password page...")
                bypass_result = await self._bypass_password_page(
                    session, task.config.site_url
                )
                if not bypass_result:
                    return TaskResult(
                        success=False,
                        error_message="Site is password protected - bypass failed",
                    )

            # Step 1: Find product and add to cart
            task.update_status(TaskStatus.ADDING_TO_CART, "Adding to cart...")

            variant_id = await self._find_variant(
                session,
                task.config.site_url,
                task.config.monitor_input,
                task.config.sizes,
            )

            if not variant_id:
                return TaskResult(
                    success=False, error_message="Product not found or out of stock"
                )

            cart_result = await self._add_to_cart(
                session, task.config.site_url, variant_id
            )

            if not cart_result:
                return TaskResult(success=False, error_message="Failed to add to cart")

            task.update_status(TaskStatus.CARTED, "Added to cart!")

            # Step 2: Create checkout
            checkout_session = await self._create_checkout(
                session, task.config.site_url
            )

            if not checkout_session:
                return TaskResult(
                    success=False,
                    error_message="Failed to create checkout",
                    checkout_url=f"{task.config.site_url}/cart",
                )

            # Step 3: Submit customer info
            task.update_status(TaskStatus.SUBMITTING_INFO, "Submitting info...")

            info_result = await self._submit_customer_info(
                session, checkout_session, profile
            )

            if not info_result:
                return TaskResult(
                    success=False,
                    error_message="Failed to submit customer info",
                    checkout_url=checkout_session.checkout_url,
                )

            # Step 4: Select shipping
            shipping_result = await self._submit_shipping(session, checkout_session)

            if not shipping_result:
                return TaskResult(
                    success=False,
                    error_message="Failed to select shipping",
                    checkout_url=checkout_session.checkout_url,
                )

            # Step 5: Submit payment
            task.update_status(TaskStatus.SUBMITTING_PAYMENT, "Submitting payment...")

            # Check for captcha
            if captcha_solver and await self._has_captcha(session, checkout_session):
                task.update_status(TaskStatus.SOLVING_CAPTCHA, "Solving captcha...")
                captcha_token = await captcha_solver.solve(
                    checkout_session.checkout_url
                )

                if not captcha_token:
                    return TaskResult(
                        success=False,
                        error_message="Failed to solve captcha",
                        checkout_url=checkout_session.checkout_url,
                    )
            else:
                captcha_token = None

            payment_result = await self._submit_payment(
                session, checkout_session, profile, captcha_token
            )

            checkout_time = time.time() - start_time

            if payment_result.get("success"):
                task.update_status(
                    TaskStatus.SUCCESS, f"Order: {payment_result.get('order_number')}"
                )

                return TaskResult(
                    success=True,
                    order_number=payment_result.get("order_number"),
                    checkout_url=checkout_session.checkout_url,
                    checkout_time=checkout_time,
                    total_price=checkout_session.total_price,
                )
            else:
                error = payment_result.get("error", "Payment failed")

                if "declined" in error.lower():
                    task.update_status(TaskStatus.DECLINED, error)
                else:
                    task.update_status(TaskStatus.FAILED, error)

                return TaskResult(
                    success=False,
                    error_message=error,
                    checkout_url=checkout_session.checkout_url,
                    checkout_time=checkout_time,
                )

        except Exception as e:
            logger.error("Checkout error", error=str(e), task_id=task.id[:8])
            return TaskResult(success=False, error_message=str(e))
        finally:
            if "session" in locals():
                await session.aclose()

    async def _create_session(self, proxy: Optional[Proxy], seed: str):
        """Create HTTP session with TLS evasion via curl-cffi."""
        return await self.session_factory.create(proxy=proxy, seed=seed)

    async def _find_variant(
        self,
        session: httpx.AsyncClient,
        site_url: str,
        monitor_input: str,
        target_sizes: List[str],
    ) -> Optional[int]:
        """Find product variant matching criteria"""
        base_url = site_url.rstrip("/")

        # Check if monitor_input is a URL or keywords
        if monitor_input.startswith("http"):
            # Direct product URL
            handle = monitor_input.split("/products/")[-1].split("?")[0]
            url = f"{base_url}/products/{handle}.json"
        else:
            # Search products.json
            url = f"{base_url}/products.json?limit=250"

        try:
            response = await session.get(url)

            if response.status_code != 200:
                return None

            data = response.json()

            if "product" in data:
                products = [data["product"]]
            else:
                products = data.get("products", [])

            # Filter by keywords
            keywords = monitor_input.lower().split()

            for product in products:
                title = product.get("title", "").lower()

                # Check if title matches keywords
                if not all(kw in title for kw in keywords if not kw.startswith("-")):
                    continue

                # Check negative keywords
                if any(kw[1:] in title for kw in keywords if kw.startswith("-")):
                    continue

                # Find matching variant
                for variant in product.get("variants", []):
                    if not variant.get("available"):
                        continue

                    # Check size
                    size = str(variant.get("option1", "")).strip()

                    if target_sizes:
                        if size not in target_sizes and not any(
                            s in size for s in target_sizes
                        ):
                            continue

                    return variant.get("id")

            return None

        except Exception as e:
            logger.error("Find variant error", error=str(e))
            return None

    async def _add_to_cart(
        self, session: httpx.AsyncClient, site_url: str, variant_id: int
    ) -> bool:
        """Add variant to cart"""
        base_url = site_url.rstrip("/")

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

    async def _create_checkout(
        self, session, site_url: str
    ) -> Optional[CheckoutSession]:
        """Create checkout session, handling checkpoint / queue pages."""
        base_url = site_url.rstrip("/")

        for attempt in range(_MAX_CHECKPOINT_RETRIES):
            try:
                response = await session.get(f"{base_url}/checkout")

                if response.status_code != 200:
                    return None

                body = response.text
                checkout_url = str(response.url)

                # --- Checkpoint / queue detection ---
                if self._is_checkpoint(body):
                    logger.warning(
                        "Shopify checkpoint detected",
                        attempt=attempt + 1,
                    )
                    # Wait and retry with the same session (cookies carry over)
                    await asyncio.sleep(2 + attempt * 3)
                    continue

                # Parse checkout token from redirect URL
                match = re.search(r"/checkouts/([a-z0-9]+)", checkout_url)
                if not match:
                    return None

                checkout_token = match.group(1)

                shop_match = re.search(r"/(\d+)/checkouts/", checkout_url)
                shop_id = shop_match.group(1) if shop_match else ""

                return CheckoutSession(
                    checkout_url=checkout_url,
                    checkout_token=checkout_token,
                    shop_id=shop_id,
                )

            except Exception as e:
                logger.error("Create checkout error", error=str(e))
                return None

        logger.error("Checkpoint not cleared after retries")
        return None

    @staticmethod
    def _is_checkpoint(html: str) -> bool:
        """Detect Shopify bot-protection checkpoint page."""
        lower = html.lower()
        return (
            (
                "checkpoint" in lower
                and ("verify you are human" in lower or "shopify" in lower)
            )
            or "queue" in lower
            and "throttle" in lower
        )

    async def _submit_customer_info(
        self, session: httpx.AsyncClient, checkout: CheckoutSession, profile: Profile
    ) -> bool:
        """Submit customer and shipping info"""
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
                checkout.checkout_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            return response.status_code in (200, 302)

        except Exception as e:
            logger.error("Submit info error", error=str(e))
            return False

    async def _submit_shipping(
        self, session: httpx.AsyncClient, checkout: CheckoutSession
    ) -> bool:
        """Select shipping method"""
        try:
            # Get shipping rates
            shipping_url = f"{checkout.checkout_url}?step=shipping_method"
            response = await session.get(shipping_url)

            if response.status_code != 200:
                return False

            # Find first shipping rate
            content = response.text
            rate_match = re.search(r'data-shipping-method="([^"]+)"', content)

            if rate_match:
                checkout.shipping_rate_id = rate_match.group(1)

                # Submit shipping selection
                await session.post(
                    shipping_url,
                    data={"checkout[shipping_rate][id]": checkout.shipping_rate_id},
                )

            return True

        except Exception as e:
            logger.error("Submit shipping error", error=str(e))
            return False

    async def _has_captcha(
        self, session: httpx.AsyncClient, checkout: CheckoutSession
    ) -> bool:
        """Check if checkout has captcha"""
        try:
            response = await session.get(f"{checkout.checkout_url}?step=payment_method")
            return (
                "captcha" in response.text.lower()
                or "recaptcha" in response.text.lower()
            )
        except Exception:
            return False

    async def _submit_payment(
        self,
        session,
        checkout: CheckoutSession,
        profile: Profile,
        captcha_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit payment using Shopify's card vault token."""
        billing = profile.billing_address
        card = profile.card

        # ---- 1. Vault the card via deposit.shopifycs.com ----
        vault = await self._vault_card(session, checkout, card)
        if not vault:
            return {"success": False, "error": "Failed to vault card"}

        # ---- 2. Extract gateway ID from payment page ----
        gateway_id = await self._extract_gateway_id(session, checkout)

        # ---- 3. Assemble payment form ----
        data = {
            "checkout[payment_gateway]": gateway_id,
            "checkout[credit_card][vault]": "false",
            "checkout[different_billing_address]": (
                "false" if profile.billing_same_as_shipping else "true"
            ),
            "complete": "1",
            "checkout[client_details][browser_width]": "1920",
            "checkout[client_details][browser_height]": "1080",
            "checkout[client_details][javascript_enabled]": "1",
            # The vaulted card session — this is the key field
            "s": vault["session_id"],
        }

        if not profile.billing_same_as_shipping:
            data.update(
                {
                    "checkout[billing_address][first_name]": billing.first_name,
                    "checkout[billing_address][last_name]": billing.last_name,
                    "checkout[billing_address][address1]": billing.address1,
                    "checkout[billing_address][address2]": billing.address2,
                    "checkout[billing_address][city]": billing.city,
                    "checkout[billing_address][province]": billing.state,
                    "checkout[billing_address][zip]": billing.zip_code,
                    "checkout[billing_address][country]": billing.country,
                }
            )

        if captcha_token:
            data["g-recaptcha-response"] = captcha_token

        try:
            payment_url = f"{checkout.checkout_url}?step=payment_method"

            response = await session.post(
                payment_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            response_url = str(response.url)
            response_text = response.text

            # ---- Success detection ----
            if "thank_you" in response_url or "orders/" in response_url:
                order_match = re.search(r"Order\s*#?\s*(\d+)", response_text)
                order_number = order_match.group(1) if order_match else "Unknown"
                return {"success": True, "order_number": order_number}

            # ---- Processing / polling (3DS, slow gateway) ----
            if "processing" in response_url:
                return await self._poll_order_status(session, response_url)

            # ---- Decline / error ----
            if "declined" in response_text.lower():
                return {"success": False, "error": "Card declined"}

            if "error" in response_text.lower():
                error_match = re.search(
                    r'class="notice--error"[^>]*>([^<]+)', response_text
                )
                error_msg = (
                    error_match.group(1).strip() if error_match else "Payment error"
                )
                return {"success": False, "error": error_msg}

            return {"success": False, "error": "Unknown payment result"}

        except Exception as e:
            logger.error("Submit payment error", error=str(e))
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Shopify Card Vault (deposit.shopifycs.com)
    # ------------------------------------------------------------------

    async def _vault_card(
        self,
        session,
        checkout: CheckoutSession,
        card,
    ) -> Optional[Dict[str, str]]:
        """Tokenize the card via Shopify's card vault endpoint.

        Shopify front-ends POST card data to ``deposit.shopifycs.com/sessions``
        and receive a ``session_id`` that is submitted instead of raw card data.
        """
        vault_url = "https://deposit.shopifycs.com/sessions"

        payload = {
            "credit_card": {
                "number": card.number,
                "name": card.holder,
                "month": int(card.expiry_month),
                "year": int(card.expiry_year_full),
                "verification_value": card.cvv,
            }
        }

        try:
            import json as _json

            response = await session.post(
                vault_url,
                data=_json.dumps(payload),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Origin": "https://checkout.shopifycs.com",
                },
            )

            if response.status_code != 200:
                logger.error(
                    "Card vault failed",
                    status=response.status_code,
                    body=response.text[:200],
                )
                return None

            data = response.json()
            session_id = data.get("id")

            if not session_id:
                logger.error("Card vault returned no session id", data=data)
                return None

            logger.info("Card vaulted successfully")
            return {"session_id": session_id}

        except Exception as e:
            logger.error("Card vault error", error=str(e))
            return None

    async def _extract_gateway_id(
        self,
        session,
        checkout: CheckoutSession,
    ) -> str:
        """Extract the payment_gateway ID from the checkout payment page."""
        try:
            response = await session.get(f"{checkout.checkout_url}?step=payment_method")
            html = response.text

            # Look for data-select-gateway or payment_gateway hidden input
            match = re.search(r'data-select-gateway="(\d+)"', html) or re.search(
                r'name="checkout\[payment_gateway\]"[^>]*value="(\d+)"', html
            )

            if match:
                return match.group(1)

            # Fallback: search for any gateway ID pattern
            gw_match = re.search(r'"payment_gateway"\s*:\s*"?(\d+)', html)
            if gw_match:
                return gw_match.group(1)

        except Exception as e:
            logger.warning("Could not extract gateway id", error=str(e))

        # Final fallback — most Shopify stores use this default
        return "credit_card"

    async def _poll_order_status(
        self,
        session,
        processing_url: str,
        max_polls: int = 20,
        interval: float = 2.0,
    ) -> Dict[str, Any]:
        """Poll a processing URL until the order resolves."""
        for _ in range(max_polls):
            await asyncio.sleep(interval)
            try:
                resp = await session.get(processing_url)
                url = str(resp.url)
                text = resp.text

                if "thank_you" in url or "orders/" in url:
                    order_match = re.search(r"Order\s*#?\s*(\d+)", text)
                    return {
                        "success": True,
                        "order_number": (
                            order_match.group(1) if order_match else "Unknown"
                        ),
                    }

                if "stock_problems" in url or "declined" in text.lower():
                    return {"success": False, "error": "Card declined or OOS"}

            except Exception:
                continue

        return {"success": False, "error": "Payment processing timed out"}

    async def _is_password_protected(
        self, session: httpx.AsyncClient, site_url: str
    ) -> bool:
        """Check if site is password protected"""
        base_url = site_url.rstrip("/")

        try:
            response = await session.get(base_url, follow_redirects=False)

            # Check for password page redirect
            if response.status_code in (301, 302, 307, 308):
                location = response.headers.get("location", "")
                if "password" in location.lower():
                    return True

            # Check response content for password form
            if response.status_code == 200:
                content = response.text.lower()
                if "password" in content and "enter store using password" in content:
                    return True
                if 'id="password"' in content or 'name="password"' in content:
                    return True

            return False

        except Exception as e:
            logger.warning("Password check error", error=str(e))
            return False

    async def _bypass_password_page(
        self,
        session: httpx.AsyncClient,
        site_url: str,
        passwords: Optional[List[str]] = None,
    ) -> bool:
        """
        Attempt to bypass password-protected Shopify page

        Strategies:
        1. Try common passwords (if enabled)
        2. Access products.json directly (sometimes not protected)
        3. Use cart.js endpoint directly
        4. Try preview links
        """
        base_url = site_url.rstrip("/")

        # Strategy 1: Try direct API access (often not password protected)
        try:
            api_urls = [
                f"{base_url}/products.json",
                f"{base_url}/collections.json",
                f"{base_url}/cart.js",
            ]

            for api_url in api_urls:
                response = await session.get(api_url)
                if response.status_code == 200:
                    logger.info("Password bypass via direct API access", url=api_url)
                    return True

        except Exception:
            pass

        # Strategy 2: Try common/leaked passwords
        common_passwords = passwords or [
            "",  # Sometimes empty works
            "password",
            "shop",
            "preview",
            "sneakers",
            "launch",
            "drop",
            "exclusive",
        ]

        password_url = f"{base_url}/password"

        for password in common_passwords:
            try:
                # Get the password page to extract form token
                page_response = await session.get(password_url)

                if page_response.status_code != 200:
                    continue

                # Extract authenticity token
                content = page_response.text
                token_match = re.search(
                    r'name="authenticity_token"[^>]*value="([^"]+)"', content
                )

                form_token = token_match.group(1) if token_match else ""

                # Submit password
                data = {
                    "password": password,
                    "authenticity_token": form_token,
                }

                response = await session.post(
                    password_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    follow_redirects=True,
                )

                # Check if we got through
                final_url = str(response.url)
                if "password" not in final_url.lower():
                    logger.info(
                        "Password bypass successful", password=password[:3] + "***"
                    )
                    return True

            except Exception:
                continue

        # Strategy 3: Try accessing via preview token in URL (if any were shared)
        try:
            preview_response = await session.get(f"{base_url}?preview_theme_id=current")
            if (
                preview_response.status_code == 200
                and "password" not in preview_response.text.lower()
            ):
                logger.info("Password bypass via preview theme")
                return True
        except Exception:
            pass

        logger.warning("Password bypass failed - all strategies exhausted")
        return False
