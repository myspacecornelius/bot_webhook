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
from urllib.parse import urlencode, urlparse
import structlog

from ..core.task import Task, TaskResult, TaskStatus, TaskProduct
from ..core.profile import Profile
from ..core.proxy import Proxy
from ..evasion.fingerprint import FingerprintManager
from ..evasion.humanizer import Humanizer

logger = structlog.get_logger()


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
        self.fingerprint_manager = FingerprintManager()
        self.humanizer = Humanizer()
        logger.info("ShopifyCheckout initialized")
    
    async def checkout(
        self,
        task: Task,
        profile: Profile,
        proxy: Optional[Proxy] = None,
        captcha_solver: Any = None
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
                bypass_result = await self._bypass_password_page(session, task.config.site_url)
                if not bypass_result:
                    return TaskResult(
                        success=False,
                        error_message="Site is password protected - bypass failed"
                    )
            
            # Step 1: Find product and add to cart
            task.update_status(TaskStatus.ADDING_TO_CART, "Adding to cart...")
            
            variant_id = await self._find_variant(
                session,
                task.config.site_url,
                task.config.monitor_input,
                task.config.sizes
            )
            
            if not variant_id:
                return TaskResult(
                    success=False,
                    error_message="Product not found or out of stock"
                )
            
            cart_result = await self._add_to_cart(session, task.config.site_url, variant_id)
            
            if not cart_result:
                return TaskResult(
                    success=False,
                    error_message="Failed to add to cart"
                )
            
            task.update_status(TaskStatus.CARTED, "Added to cart!")
            
            # Step 2: Create checkout
            checkout_session = await self._create_checkout(session, task.config.site_url)
            
            if not checkout_session:
                return TaskResult(
                    success=False,
                    error_message="Failed to create checkout",
                    checkout_url=f"{task.config.site_url}/cart"
                )
            
            # Step 3: Submit customer info
            task.update_status(TaskStatus.SUBMITTING_INFO, "Submitting info...")
            
            info_result = await self._submit_customer_info(
                session,
                checkout_session,
                profile
            )
            
            if not info_result:
                return TaskResult(
                    success=False,
                    error_message="Failed to submit customer info",
                    checkout_url=checkout_session.checkout_url
                )
            
            # Step 4: Select shipping
            shipping_result = await self._submit_shipping(session, checkout_session)
            
            if not shipping_result:
                return TaskResult(
                    success=False,
                    error_message="Failed to select shipping",
                    checkout_url=checkout_session.checkout_url
                )
            
            # Step 5: Submit payment
            task.update_status(TaskStatus.SUBMITTING_PAYMENT, "Submitting payment...")
            
            # Check for captcha
            if captcha_solver and await self._has_captcha(session, checkout_session):
                task.update_status(TaskStatus.SOLVING_CAPTCHA, "Solving captcha...")
                captcha_token = await captcha_solver.solve(checkout_session.checkout_url)
                
                if not captcha_token:
                    return TaskResult(
                        success=False,
                        error_message="Failed to solve captcha",
                        checkout_url=checkout_session.checkout_url
                    )
            else:
                captcha_token = None
            
            payment_result = await self._submit_payment(
                session,
                checkout_session,
                profile,
                captcha_token
            )
            
            checkout_time = time.time() - start_time
            
            if payment_result.get("success"):
                task.update_status(TaskStatus.SUCCESS, f"Order: {payment_result.get('order_number')}")
                
                return TaskResult(
                    success=True,
                    order_number=payment_result.get("order_number"),
                    checkout_url=checkout_session.checkout_url,
                    checkout_time=checkout_time,
                    total_price=checkout_session.total_price
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
                    checkout_time=checkout_time
                )
                
        except Exception as e:
            logger.error("Checkout error", error=str(e), task_id=task.id[:8])
            return TaskResult(
                success=False,
                error_message=str(e)
            )
        finally:
            if 'session' in locals():
                await session.aclose()
    
    async def _create_session(self, proxy: Optional[Proxy], seed: str) -> httpx.AsyncClient:
        """Create HTTP session with fingerprint"""
        fingerprint = self.fingerprint_manager.generate(seed=seed)
        
        proxies = None
        if proxy:
            proxies = {"all://": proxy.url}
        
        return httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            proxies=proxies,
            headers={
                "User-Agent": fingerprint.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            }
        )
    
    async def _find_variant(
        self,
        session: httpx.AsyncClient,
        site_url: str,
        monitor_input: str,
        target_sizes: List[str]
    ) -> Optional[int]:
        """Find product variant matching criteria"""
        base_url = site_url.rstrip('/')
        
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
                        if size not in target_sizes and not any(s in size for s in target_sizes):
                            continue
                    
                    return variant.get("id")
            
            return None
            
        except Exception as e:
            logger.error("Find variant error", error=str(e))
            return None
    
    async def _add_to_cart(
        self,
        session: httpx.AsyncClient,
        site_url: str,
        variant_id: int
    ) -> bool:
        """Add variant to cart"""
        base_url = site_url.rstrip('/')
        
        try:
            response = await session.post(
                f"{base_url}/cart/add.js",
                json={"items": [{"id": variant_id, "quantity": 1}]},
                headers={"Content-Type": "application/json"}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error("Add to cart error", error=str(e))
            return False
    
    async def _create_checkout(
        self,
        session: httpx.AsyncClient,
        site_url: str
    ) -> Optional[CheckoutSession]:
        """Create checkout session"""
        base_url = site_url.rstrip('/')
        
        try:
            # Navigate to checkout
            response = await session.get(f"{base_url}/checkout")
            
            if response.status_code != 200:
                return None
            
            # Extract checkout token from URL
            checkout_url = str(response.url)
            
            # Parse checkout token
            match = re.search(r'/checkouts/([a-z0-9]+)', checkout_url)
            if not match:
                return None
            
            checkout_token = match.group(1)
            
            # Extract shop ID
            shop_match = re.search(r'/(\d+)/checkouts/', checkout_url)
            shop_id = shop_match.group(1) if shop_match else ""
            
            return CheckoutSession(
                checkout_url=checkout_url,
                checkout_token=checkout_token,
                shop_id=shop_id
            )
            
        except Exception as e:
            logger.error("Create checkout error", error=str(e))
            return None
    
    async def _submit_customer_info(
        self,
        session: httpx.AsyncClient,
        checkout: CheckoutSession,
        profile: Profile
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
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            return response.status_code in (200, 302)
            
        except Exception as e:
            logger.error("Submit info error", error=str(e))
            return False
    
    async def _submit_shipping(
        self,
        session: httpx.AsyncClient,
        checkout: CheckoutSession
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
                    data={"checkout[shipping_rate][id]": checkout.shipping_rate_id}
                )
            
            return True
            
        except Exception as e:
            logger.error("Submit shipping error", error=str(e))
            return False
    
    async def _has_captcha(
        self,
        session: httpx.AsyncClient,
        checkout: CheckoutSession
    ) -> bool:
        """Check if checkout has captcha"""
        try:
            response = await session.get(f"{checkout.checkout_url}?step=payment_method")
            return "captcha" in response.text.lower() or "recaptcha" in response.text.lower()
        except Exception:
            return False
    
    async def _submit_payment(
        self,
        session: httpx.AsyncClient,
        checkout: CheckoutSession,
        profile: Profile,
        captcha_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit payment information"""
        billing = profile.billing_address
        card = profile.card
        
        # Get payment gateway token
        gateway_token = await self._get_payment_token(session, checkout, card)
        
        if not gateway_token:
            return {"success": False, "error": "Failed to get payment token"}
        
        data = {
            "checkout[payment_gateway]": gateway_token.get("gateway_id", ""),
            "checkout[credit_card][vault]": "false",
            "checkout[different_billing_address]": "false" if profile.billing_same_as_shipping else "true",
            "complete": "1",
            "checkout[client_details][browser_width]": "1920",
            "checkout[client_details][browser_height]": "1080",
            "checkout[client_details][javascript_enabled]": "1",
        }
        
        if not profile.billing_same_as_shipping:
            data.update({
                "checkout[billing_address][first_name]": billing.first_name,
                "checkout[billing_address][last_name]": billing.last_name,
                "checkout[billing_address][address1]": billing.address1,
                "checkout[billing_address][address2]": billing.address2,
                "checkout[billing_address][city]": billing.city,
                "checkout[billing_address][province]": billing.state,
                "checkout[billing_address][zip]": billing.zip_code,
                "checkout[billing_address][country]": billing.country,
            })
        
        if captcha_token:
            data["g-recaptcha-response"] = captcha_token
        
        try:
            payment_url = f"{checkout.checkout_url}?step=payment_method"
            
            response = await session.post(
                payment_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            # Check for success
            response_url = str(response.url)
            response_text = response.text
            
            if "thank_you" in response_url or "orders/" in response_url:
                # Extract order number
                order_match = re.search(r'Order\s*#?\s*(\d+)', response_text)
                order_number = order_match.group(1) if order_match else "Unknown"
                
                return {"success": True, "order_number": order_number}
            
            # Check for decline
            if "declined" in response_text.lower():
                return {"success": False, "error": "Card declined"}
            
            if "error" in response_text.lower():
                error_match = re.search(r'class="notice--error"[^>]*>([^<]+)', response_text)
                error_msg = error_match.group(1).strip() if error_match else "Payment error"
                return {"success": False, "error": error_msg}
            
            return {"success": False, "error": "Unknown payment result"}
            
        except Exception as e:
            logger.error("Submit payment error", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _get_payment_token(
        self,
        session: httpx.AsyncClient,
        checkout: CheckoutSession,
        card
    ) -> Optional[Dict[str, Any]]:
        """Get payment gateway token for card"""
        # This would integrate with Shopify's payment processing
        # For now, return a placeholder
        return {
            "gateway_id": "credit_card",
            "token": "placeholder"
        }
    
    async def _is_password_protected(
        self,
        session: httpx.AsyncClient,
        site_url: str
    ) -> bool:
        """Check if site is password protected"""
        base_url = site_url.rstrip('/')
        
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
        passwords: Optional[List[str]] = None
    ) -> bool:
        """
        Attempt to bypass password-protected Shopify page
        
        Strategies:
        1. Try common passwords (if enabled)
        2. Access products.json directly (sometimes not protected)
        3. Use cart.js endpoint directly
        4. Try preview links
        """
        base_url = site_url.rstrip('/')
        
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
                token_match = re.search(r'name="authenticity_token"[^>]*value="([^"]+)"', content)
                
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
                    follow_redirects=True
                )
                
                # Check if we got through
                final_url = str(response.url)
                if "password" not in final_url.lower():
                    logger.info("Password bypass successful", password=password[:3] + "***")
                    return True
                    
            except Exception:
                continue
        
        # Strategy 3: Try accessing via preview token in URL (if any were shared)
        try:
            preview_response = await session.get(f"{base_url}?preview_theme_id=current")
            if preview_response.status_code == 200 and "password" not in preview_response.text.lower():
                logger.info("Password bypass via preview theme")
                return True
        except Exception:
            pass
        
        logger.warning("Password bypass failed - all strategies exhausted")
        return False
