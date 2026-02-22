"""
Nike SNKRS Checkout Module — FLOW Mode

Reverse-engineered from Valor AIO's Nike FLOW checkout approach:
  - Uses Nike's Buying API for headless checkout
  - Session creation → product launch monitoring → cart → checkout
  - Handles Nike's anti-bot protections (device fingerprinting, session validation)
  - Supports size-specific variant targeting
  - Integrates with auto-task spawner for multi-task drops

Key Valor settings replicated:
  mode: "FLOW" (Nike API-based checkout)
  sizeRange: ["14", "13", "12"]
  taskCount: 19 (via Quick Task)
  stopAfter: 180

Nike SNKRS API endpoints (reverse-engineered):
  - Buy: /buy/checkout_previews/v3/ (preview order)
  - Buy: /buy/orders/v1/ (submit order)
  - Launch: /launch/entries/v2/ (LEO draw entries)
  - Product: /product_feed/threads/v3/ (product data)
"""

import asyncio
import hashlib
import time
import uuid
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import structlog

from ..core.task import Task, TaskResult, TaskStatus, TaskMode, TaskProduct
from ..core.profile import Profile
from ..core.proxy import Proxy
from .session import CheckoutSession as SessionFactory

logger = structlog.get_logger()


# Nike API base URLs
NIKE_API_BASE = "https://api.nike.com"
NIKE_SNKRS_BASE = "https://www.nike.com"
NIKE_UNITE_BASE = "https://unite.nike.com"

# Common headers for Nike API
NIKE_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "x-nike-caller-id": "nike:snkrs:web:1.0",
    "appid": "com.nike.commerce.snkrs.web",
    "nike-api-caller-id": "nike:snkrs:web:1.0",
}


class NikeCheckoutMode(str, Enum):
    """Nike-specific checkout modes"""

    FLOW = "flow"  # Direct API checkout
    LEO = "leo"  # LEO draw entry (lottery)
    DAN = "dan"  # DAN entry (first come first serve)
    EXCLUSIVE = "excl"  # Exclusive access


@dataclass
class NikeSession:
    """Active Nike checkout session"""

    access_token: str
    refresh_token: str = ""
    uupm_id: str = ""  # Unified user profile management ID
    visitor_id: str = ""
    checkout_id: str = ""
    checkout_token: str = ""
    expires_at: float = 0.0

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def auth_header(self) -> str:
        return f"Bearer {self.access_token}"


@dataclass
class NikeProduct:
    """Nike product data"""

    sku: str  # Style-color code e.g. "FQ3549-100"
    name: str = ""
    product_id: str = ""  # Nike's internal product ID
    merchant_id: str = ""
    channel: str = ""  # SNKRS, NIKE_DOT_COM
    launch_type: str = ""  # LEO, DAN, FLOW
    launch_id: str = ""
    available_skus: Dict[str, str] = field(default_factory=dict)  # size → skuId
    price: float = 0.0
    currency: str = "USD"
    image_url: str = ""
    release_date: Optional[str] = None
    is_available: bool = False

    def get_sku_for_size(self, size: str) -> Optional[str]:
        """Get the SKU ID for a specific size"""
        return self.available_skus.get(size)

    def get_available_sizes(self) -> List[str]:
        return list(self.available_skus.keys())


class NikeCheckout:
    """
    Nike SNKRS checkout automation via API.

    Supports FLOW (direct buy), LEO (draw), and DAN (FCFS) launch types.
    Implements Valor's FLOW checkout approach for headless purchasing.

    Usage:
        nike = NikeCheckout()
        result = await nike.checkout(task, profile, proxy)
    """

    # Size chart: US Men's → Nike skuId format
    SIZE_MAP = {
        "3.5": "3.5",
        "4": "4",
        "4.5": "4.5",
        "5": "5",
        "5.5": "5.5",
        "6": "6",
        "6.5": "6.5",
        "7": "7",
        "7.5": "7.5",
        "8": "8",
        "8.5": "8.5",
        "9": "9",
        "9.5": "9.5",
        "10": "10",
        "10.5": "10.5",
        "11": "11",
        "11.5": "11.5",
        "12": "12",
        "12.5": "12.5",
        "13": "13",
        "13.5": "13.5",
        "14": "14",
        "15": "15",
        "16": "16",
        "17": "17",
        "18": "18",
    }

    def __init__(self):
        self._session_factory = SessionFactory()
        self._sessions: Dict[str, NikeSession] = {}

    async def checkout(
        self,
        task: Task,
        profile: Profile,
        proxy: Optional[Proxy] = None,
        captcha_solver: Any = None,
    ) -> TaskResult:
        """
        Execute Nike checkout for a task.

        Flow:
        1. Authenticate with Nike account (from profile)
        2. Fetch product data and match variant
        3. Create checkout preview (cart)
        4. Submit order (payment)
        5. Return result
        """
        start_time = time.time()
        sku = task.config.monitor_input
        target_sizes = task.config.sizes or []
        session = None

        logger.info(
            "Nike checkout starting",
            task_id=task.id[:8],
            sku=sku,
            sizes=target_sizes[:5],
            mode=task.config.mode.value,
        )

        try:
            # Step 1: Create HTTP session
            session = await self._session_factory.create(
                proxy=proxy,
                seed=f"nike-{task.id}",
                extra_headers=NIKE_HEADERS,
            )

            # Step 2: Authenticate
            task.update_status(TaskStatus.STARTING, "Authenticating...")
            nike_session = await self._authenticate(session, profile)

            if not nike_session:
                return TaskResult(
                    success=False,
                    error_message="Nike authentication failed",
                )

            # Step 3: Find product
            task.update_status(TaskStatus.MONITORING, f"Finding {sku}...")
            product = await self._get_product(session, nike_session, sku)

            if not product:
                return TaskResult(
                    success=False,
                    error_message=f"Product not found: {sku}",
                )

            # Update task with product info
            task.product = TaskProduct(
                name=product.name,
                sku=product.sku,
                image_url=product.image_url,
                price=product.price,
                url=f"{NIKE_SNKRS_BASE}/launch/t/{product.sku}",
            )

            # Step 4: Match size
            variant_sku_id, matched_size = self._match_size(product, target_sizes)
            if not variant_sku_id:
                return TaskResult(
                    success=False,
                    error_message=f"No matching size available. Available: {product.get_available_sizes()[:5]}",
                )

            task.product.size = matched_size
            task.update_status(TaskStatus.PRODUCT_FOUND, f"Matched size {matched_size}")

            # Step 5: Route by launch type / mode
            if product.launch_type == "LEO":
                result = await self._checkout_leo(
                    session, nike_session, product, variant_sku_id, profile
                )
            elif task.config.mode == TaskMode.FAST or product.launch_type == "DAN":
                result = await self._checkout_flow(
                    session, nike_session, product, variant_sku_id, profile
                )
            else:
                # Default FLOW checkout
                result = await self._checkout_flow(
                    session, nike_session, product, variant_sku_id, profile
                )

            checkout_time = time.time() - start_time
            result.checkout_time = checkout_time

            if result.success:
                logger.info(
                    "Nike checkout SUCCESS",
                    task_id=task.id[:8],
                    sku=sku,
                    size=matched_size,
                    order=result.order_number,
                    time=f"{checkout_time:.2f}s",
                )

            return result

        except Exception as e:
            logger.error("Nike checkout error", task_id=task.id[:8], error=str(e))
            return TaskResult(
                success=False,
                error_message=str(e),
                checkout_time=time.time() - start_time,
            )
        finally:
            if session is not None:
                try:
                    await session.aclose()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def _authenticate(self, session, profile: Profile) -> Optional[NikeSession]:
        """Authenticate with Nike account.

        Uses Nike's Unite authentication service.
        Email/password from the profile's nike_account field.
        """
        nike_email = getattr(profile, "nike_email", None) or profile.email
        nike_password = getattr(profile, "nike_password", None)

        if not nike_password:
            logger.warning("No Nike password in profile, attempting guest flow")
            return await self._guest_session(session)

        try:
            auth_payload = {
                "client_id": "PbCREuPr3iaFANEDjtiEzXooFl7mXGQ7",
                "grant_type": "password",
                "username": nike_email,
                "password": nike_password,
                "ux_id": "com.nike.commerce.snkrs.web",
                "keepMeLoggedIn": True,
            }

            response = await session.post(
                f"{NIKE_UNITE_BASE}/loginWithSetCookie",
                json=auth_payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

            if response.status_code != 200:
                logger.error("Nike auth failed", status=response.status_code)
                return None

            data = response.json()

            nike_session = NikeSession(
                access_token=data.get("access_token", ""),
                refresh_token=data.get("refresh_token", ""),
                uupm_id=data.get("user_id", ""),
                visitor_id=str(uuid.uuid4()),
                expires_at=time.time() + data.get("expires_in", 3600),
            )

            logger.info("Nike authenticated", user_id=nike_session.uupm_id[:8])
            return nike_session

        except Exception as e:
            logger.error("Nike auth error", error=str(e))
            return None

    async def _guest_session(self, session) -> Optional[NikeSession]:
        """Create a guest session for non-account checkouts"""
        try:
            response = await session.post(
                f"{NIKE_UNITE_BASE}/guestLogin",
                json={
                    "client_id": "PbCREuPr3iaFANEDjtiEzXooFl7mXGQ7",
                    "grant_type": "client_credentials",
                    "ux_id": "com.nike.commerce.snkrs.web",
                },
            )

            if response.status_code != 200:
                return None

            data = response.json()
            return NikeSession(
                access_token=data.get("access_token", ""),
                visitor_id=str(uuid.uuid4()),
                expires_at=time.time() + data.get("expires_in", 3600),
            )
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Product Discovery
    # ------------------------------------------------------------------

    async def _get_product(
        self, session, nike_session: NikeSession, sku: str
    ) -> Optional[NikeProduct]:
        """Fetch product data from Nike's product feed API."""
        headers = {
            "Authorization": nike_session.auth_header,
            **NIKE_HEADERS,
        }

        try:
            # Try product feed endpoint
            response = await session.get(
                f"{NIKE_API_BASE}/product_feed/threads/v3/",
                params={
                    "filter": f"marketplace(US)AND(publishedContent.properties.coverCard.properties.seo.slug CONTAINS '{sku.lower()}')",
                    "anchor": "0",
                    "count": "1",
                    "fields": "active,id,productInfo",
                },
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                objects = data.get("objects", [])

                if objects:
                    return self._parse_product_thread(objects[0], sku)

            # Fallback: try direct product endpoint
            response = await session.get(
                f"{NIKE_API_BASE}/cic/browse/v2",
                params={
                    "queryid": "products",
                    "anonymousId": nike_session.visitor_id,
                    "country": "us",
                    "endpoint": f"/product_feed/rollup_threads/v2?filter=marketplace(US)AND(language(en)AND(CLOSE(styleColor({sku}))))",
                    "language": "en",
                    "localizedRangeStr": "{lowestPrice} — {highestPrice}",
                },
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("data", {}).get("products", {}).get("objects"):
                    product_data = data["data"]["products"]["objects"][0]
                    return self._parse_browse_product(product_data, sku)

            logger.warning("Product not found via API", sku=sku)
            return None

        except Exception as e:
            logger.error("Product fetch error", sku=sku, error=str(e))
            return None

    def _parse_product_thread(self, thread: Dict, sku: str) -> NikeProduct:
        """Parse product data from thread API response"""
        product_info = (thread.get("productInfo") or [{}])[0]
        merch_product = product_info.get("merchProduct", {})
        merch_price = product_info.get("merchPrice", {})
        availability = product_info.get("availability", {})
        launch_view = product_info.get("launchView", {})

        # Build size map
        available_skus = {}
        for sku_data in product_info.get("skus", []):
            if sku_data.get("available", False):
                size = sku_data.get("nikeSize", sku_data.get("localizedSize", ""))
                sku_id = sku_data.get("skuId", "")
                if size and sku_id:
                    available_skus[size] = sku_id

        # Check availability from launch view
        is_available = False
        if launch_view.get("method") in ["LEO", "DAN", "FLOW"]:
            is_available = launch_view.get("startEntry", False)
        else:
            is_available = availability.get("available", False)

        # Get image
        image_url = ""
        images = product_info.get("imageUrls", {})
        image_url = images.get("productImageUrl", images.get("squarishURL", ""))

        return NikeProduct(
            sku=sku,
            name=merch_product.get("labelName", ""),
            product_id=merch_product.get("id", ""),
            merchant_id=merch_product.get("merchantId", ""),
            channel=merch_product.get("channelType", ""),
            launch_type=launch_view.get("method", "FLOW"),
            launch_id=launch_view.get("id", ""),
            available_skus=available_skus,
            price=merch_price.get("currentPrice", 0.0),
            currency=merch_price.get("currency", "USD"),
            image_url=image_url,
            release_date=launch_view.get("startEntryDate"),
            is_available=is_available,
        )

    def _parse_browse_product(self, product_data: Dict, sku: str) -> NikeProduct:
        """Parse product data from browse API response"""
        product_info = (product_data.get("productInfo") or [{}])[0]
        merch_product = product_info.get("merchProduct", {})
        merch_price = product_info.get("merchPrice", {})

        available_skus = {}
        for sku_data in product_info.get("availableSkus", []):
            if sku_data.get("available", False):
                size = sku_data.get("nikeSize", "")
                sku_id = sku_data.get("skuId", "")
                if size and sku_id:
                    available_skus[size] = sku_id

        return NikeProduct(
            sku=sku,
            name=merch_product.get("labelName", ""),
            product_id=merch_product.get("id", ""),
            merchant_id=merch_product.get("merchantId", ""),
            available_skus=available_skus,
            price=merch_price.get("currentPrice", 0.0),
            is_available=bool(available_skus),
        )

    # ------------------------------------------------------------------
    # Size Matching
    # ------------------------------------------------------------------

    def _match_size(
        self, product: NikeProduct, target_sizes: List[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Match target sizes to available product sizes.

        Returns (sku_id, matched_size) or (None, None).
        """
        available = product.available_skus

        if not available:
            return None, None

        # Try target sizes in order of preference
        if target_sizes:
            for size in target_sizes:
                # Try exact match
                if size in available:
                    return available[size], size
                # Try with .0 suffix
                if f"{size}.0" in available:
                    return available[f"{size}.0"], f"{size}.0"
                # Try normalized
                normalized = size.replace("M ", "").replace("W ", "").strip()
                if normalized in available:
                    return available[normalized], normalized

        # No target sizes or no match — pick random available
        first_size = next(iter(available))
        return available[first_size], first_size

    # ------------------------------------------------------------------
    # FLOW Checkout (Direct Buy API)
    # ------------------------------------------------------------------

    async def _checkout_flow(
        self,
        session,
        nike_session: NikeSession,
        product: NikeProduct,
        sku_id: str,
        profile: Profile,
    ) -> TaskResult:
        """FLOW checkout — direct buy via Nike's Buying API.

        Steps:
        1. Create checkout preview (validates payment + reserves item)
        2. Submit the order
        """
        headers = {
            "Authorization": nike_session.auth_header,
            **NIKE_HEADERS,
        }

        shipping = profile.shipping

        # Step 1: Checkout preview (cart + validation)
        preview_payload = {
            "request": [
                {
                    "skuId": sku_id,
                    "productId": product.product_id,
                    "quantity": 1,
                    "recipient": {
                        "firstName": shipping.first_name,
                        "lastName": shipping.last_name,
                    },
                    "shippingAddress": {
                        "address1": shipping.address1,
                        "address2": shipping.address2 or "",
                        "city": shipping.city,
                        "state": shipping.state,
                        "postalCode": shipping.zip_code,
                        "country": shipping.country or "US",
                        "phone": profile.phone or "",
                    },
                    "contactInfo": {
                        "email": profile.email,
                        "phoneNumber": profile.phone or "",
                    },
                    "currency": product.currency,
                    "locale": "en_US",
                    "channel": "SNKRS",
                    "skuQuantity": 1,
                }
            ],
            "country": "US",
            "currency": "USD",
        }

        try:
            logger.debug("Submitting checkout preview", sku=product.sku)

            response = await session.post(
                f"{NIKE_API_BASE}/buy/checkout_previews/v3/",
                json=preview_payload,
                headers=headers,
            )

            if response.status_code not in (200, 201):
                error_text = response.text[:200] if response.text else "Unknown"
                return TaskResult(
                    success=False,
                    error_message=f"Checkout preview failed ({response.status_code}): {error_text}",
                )

            preview_data = response.json()
            checkout_id = preview_data.get("checkoutId", "")

            if not checkout_id:
                return TaskResult(
                    success=False,
                    error_message="No checkout ID returned from preview",
                )

            nike_session.checkout_id = checkout_id

        except Exception as e:
            return TaskResult(
                success=False,
                error_message=f"Preview error: {str(e)}",
            )

        # Step 2: Submit payment / order
        payment_data = self._build_payment_payload(profile, product)

        order_payload = {
            "checkoutId": checkout_id,
            "paymentToken": payment_data.get("payment_token", ""),
            "total": product.price,
            "currency": product.currency,
        }

        try:
            logger.debug("Submitting order", checkout_id=checkout_id[:8])

            response = await session.post(
                f"{NIKE_API_BASE}/buy/orders/v1/",
                json=order_payload,
                headers=headers,
            )

            if response.status_code in (200, 201, 202):
                order_data = response.json()
                order_number = order_data.get("orderNumber", order_data.get("id", ""))

                return TaskResult(
                    success=True,
                    order_number=order_number,
                    checkout_url=f"{NIKE_SNKRS_BASE}/orders/{order_number}",
                    total_price=product.price,
                )
            else:
                error_text = response.text[:200] if response.text else "Unknown"
                return TaskResult(
                    success=False,
                    error_message=f"Order submission failed ({response.status_code}): {error_text}",
                )

        except Exception as e:
            return TaskResult(
                success=False,
                error_message=f"Order error: {str(e)}",
            )

    # ------------------------------------------------------------------
    # LEO Entry (Draw/Lottery)
    # ------------------------------------------------------------------

    async def _checkout_leo(
        self,
        session,
        nike_session: NikeSession,
        product: NikeProduct,
        sku_id: str,
        profile: Profile,
    ) -> TaskResult:
        """LEO (Let Everyone Order) draw entry.

        LEO drops are lottery-based. We submit an entry and wait
        for the result. Nike picks winners randomly.
        """
        headers = {
            "Authorization": nike_session.auth_header,
            **NIKE_HEADERS,
        }

        shipping = profile.shipping

        entry_payload = {
            "skuId": sku_id,
            "launchId": product.launch_id,
            "locale": "en_US",
            "currency": product.currency,
            "channel": "SNKRS",
            "shippingAddress": {
                "address1": shipping.address1,
                "address2": shipping.address2 or "",
                "city": shipping.city,
                "state": shipping.state,
                "postalCode": shipping.zip_code,
                "country": shipping.country or "US",
            },
            "contactInfo": {
                "email": profile.email,
                "phoneNumber": profile.phone or "",
            },
        }

        payment_data = self._build_payment_payload(profile, product)
        if payment_data:
            entry_payload["paymentToken"] = payment_data.get("payment_token", "")

        try:
            logger.info(
                "Submitting LEO entry", sku=product.sku, launch_id=product.launch_id
            )

            response = await session.post(
                f"{NIKE_API_BASE}/launch/entries/v2/",
                json=entry_payload,
                headers=headers,
            )

            if response.status_code in (200, 201, 202):
                entry_data = response.json()
                entry_id = entry_data.get("id", "")
                entry_status = entry_data.get("result", {}).get("status", "PENDING")

                if entry_status == "WINNER":
                    return TaskResult(
                        success=True,
                        order_number=entry_data.get("orderNumber", entry_id),
                        total_price=product.price,
                    )
                elif entry_status == "PENDING":
                    # LEO draws can take minutes to resolve
                    resolved = await self._poll_leo_result(
                        session, nike_session, entry_id
                    )
                    return resolved
                else:
                    return TaskResult(
                        success=False,
                        error_message=f"LEO entry status: {entry_status}",
                    )
            else:
                return TaskResult(
                    success=False,
                    error_message=f"LEO entry failed ({response.status_code})",
                )

        except Exception as e:
            return TaskResult(
                success=False,
                error_message=f"LEO error: {str(e)}",
            )

    async def _poll_leo_result(
        self,
        session,
        nike_session: NikeSession,
        entry_id: str,
        max_polls: int = 30,
        interval: float = 10.0,
    ) -> TaskResult:
        """Poll for LEO draw result"""
        headers = {
            "Authorization": nike_session.auth_header,
            **NIKE_HEADERS,
        }

        for i in range(max_polls):
            await asyncio.sleep(interval)

            try:
                response = await session.get(
                    f"{NIKE_API_BASE}/launch/entries/v2/{entry_id}",
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    status = data.get("result", {}).get("status", "PENDING")

                    if status == "WINNER":
                        return TaskResult(
                            success=True,
                            order_number=data.get("orderNumber", entry_id),
                        )
                    elif status in ("NON_WINNER", "DRAW_CLOSED"):
                        return TaskResult(
                            success=False,
                            error_message=f"LEO draw: {status}",
                        )

                    logger.debug(f"LEO poll {i+1}/{max_polls}: {status}")

            except Exception as e:
                logger.warning(f"LEO poll error: {e}")

        return TaskResult(
            success=False,
            error_message="LEO draw timed out (no result after polling)",
        )

    # ------------------------------------------------------------------
    # Payment
    # ------------------------------------------------------------------

    def _build_payment_payload(
        self, profile: Profile, product: NikeProduct
    ) -> Dict[str, str]:
        """Build payment token for Nike checkout.

        Nike uses a tokenized payment approach. The payment info
        is either:
        - A saved payment method ID (from the account)
        - A new card that gets tokenized via Nike's payment provider
        """
        card = profile.card
        if not card:
            return {}

        # Build a payment reference token
        # In production, this would be tokenized through Nike's payment gateway
        payment_ref = hashlib.sha256(
            f"{card.number}:{card.exp_month}:{card.exp_year}:{product.product_id}".encode()
        ).hexdigest()[:32]

        return {
            "payment_token": payment_ref,
            "card_type": self._detect_card_type(card.number),
            "last_four": card.number[-4:] if card.number else "",
        }

    @staticmethod
    def _detect_card_type(card_number: str) -> str:
        """Detect card type from number"""
        if not card_number:
            return "unknown"
        first = card_number[0]
        if first == "4":
            return "VISA"
        elif first == "5":
            return "MASTERCARD"
        elif first == "3":
            return "AMEX"
        elif first == "6":
            return "DISCOVER"
        return "unknown"

    # ------------------------------------------------------------------
    # Status & Management
    # ------------------------------------------------------------------

    def get_active_sessions(self) -> List[Dict[str, str]]:
        """Get all active Nike sessions"""
        return [
            {
                "user_id": s.uupm_id[:8],
                "expired": s.is_expired,
                "checkout_id": s.checkout_id[:8] if s.checkout_id else "none",
            }
            for s in self._sessions.values()
        ]
