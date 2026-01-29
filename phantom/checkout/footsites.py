"""
Footsites Checkout Module
Supports Foot Locker, Champs, Eastbay, Finish Line
"""

import asyncio
import time
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx
from urllib.parse import urlencode
import structlog

from ..core.task import Task, TaskResult, TaskStatus
from ..core.profile import Profile
from ..core.proxy import Proxy

logger = structlog.get_logger()


@dataclass
class FootsiteSession:
    """Footsite checkout session data"""
    cart_id: str
    session_token: str
    csrf_token: str
    site: str
    product_id: Optional[str] = None
    variant_id: Optional[str] = None


class FootsitesCheckout:
    """
    Footsites checkout automation
    
    Supports:
    - Foot Locker (footlocker.com)
    - Champs Sports (champssports.com)
    - Eastbay (eastbay.com)
    - Finish Line (finishline.com)
    
    Features:
    - Adyen payment processing
    - Queue handling
    - Account-based checkout
    """
    
    SITE_CONFIGS = {
        "footlocker": {
            "domain": "www.footlocker.com",
            "api_base": "https://www.footlocker.com/api",
            "cart_api": "https://www.footlocker.com/api/v3/cart",
            "checkout_api": "https://www.footlocker.com/api/checkout",
        },
        "champs": {
            "domain": "www.champssports.com",
            "api_base": "https://www.champssports.com/api",
            "cart_api": "https://www.champssports.com/api/v3/cart",
            "checkout_api": "https://www.champssports.com/api/checkout",
        },
        "eastbay": {
            "domain": "www.eastbay.com",
            "api_base": "https://www.eastbay.com/api",
            "cart_api": "https://www.eastbay.com/api/v3/cart",
            "checkout_api": "https://www.eastbay.com/api/checkout",
        },
        "finishline": {
            "domain": "www.finishline.com",
            "api_base": "https://www.finishline.com/api",
            "cart_api": "https://www.finishline.com/api/v3/cart",
            "checkout_api": "https://www.finishline.com/api/checkout",
        },
    }
    
    def __init__(self):
        logger.info("FootsitesCheckout initialized")
    
    async def checkout(
        self,
        task: Task,
        profile: Profile,
        proxy: Optional[Proxy] = None,
        captcha_solver: Any = None
    ) -> TaskResult:
        """Execute checkout for a task"""
        start_time = time.time()
        
        site_name = task.config.site_name.lower()
        if site_name not in self.SITE_CONFIGS:
            return TaskResult(
                success=False,
                error_message=f"Unsupported site: {site_name}"
            )
        
        site_config = self.SITE_CONFIGS[site_name]
        
        task.update_status(TaskStatus.MONITORING, "Finding product...")
        
        try:
            session = await self._create_session(proxy, site_config)
            
            # Step 1: Find product
            product_id, variant_id = await self._find_product(
                session,
                site_config,
                task.config.monitor_input,
                task.config.sizes
            )
            
            if not product_id or not variant_id:
                return TaskResult(
                    success=False,
                    error_message="Product not found or out of stock"
                )
            
            # Step 2: Add to cart
            task.update_status(TaskStatus.ADDING_TO_CART, "Adding to cart...")
            
            cart_result = await self._add_to_cart(
                session,
                site_config,
                product_id,
                variant_id
            )
            
            if not cart_result:
                return TaskResult(
                    success=False,
                    error_message="Failed to add to cart"
                )
            
            task.update_status(TaskStatus.CARTED, "Added to cart!")
            
            # Step 3: Create checkout session
            checkout_session = await self._create_checkout_session(
                session,
                site_config,
                cart_result
            )
            
            if not checkout_session:
                return TaskResult(
                    success=False,
                    error_message="Failed to create checkout session"
                )
            
            # Step 4: Submit shipping info
            task.update_status(TaskStatus.SUBMITTING_INFO, "Submitting info...")
            
            shipping_result = await self._submit_shipping(
                session,
                site_config,
                checkout_session,
                profile
            )
            
            if not shipping_result:
                return TaskResult(
                    success=False,
                    error_message="Failed to submit shipping info"
                )
            
            # Step 5: Submit payment
            task.update_status(TaskStatus.SUBMITTING_PAYMENT, "Submitting payment...")
            
            payment_result = await self._submit_payment(
                session,
                site_config,
                checkout_session,
                profile,
                captcha_solver
            )
            
            checkout_time = time.time() - start_time
            
            if payment_result.get("success"):
                order_number = payment_result.get("order_number", "Unknown")
                task.update_status(TaskStatus.SUCCESS, f"Order: {order_number}")
                
                return TaskResult(
                    success=True,
                    order_number=order_number,
                    checkout_time=checkout_time,
                    total_price=payment_result.get("total")
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
                    checkout_time=checkout_time
                )
        
        except Exception as e:
            logger.error("Footsites checkout error", error=str(e), task_id=task.id[:8])
            return TaskResult(
                success=False,
                error_message=str(e)
            )
        finally:
            if 'session' in locals():
                await session.aclose()
    
    async def _create_session(self, proxy: Optional[Proxy], site_config: Dict) -> httpx.AsyncClient:
        """Create HTTP session"""
        proxies = None
        if proxy:
            proxies = {"all://": proxy.url}
        
        return httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            proxies=proxies,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": f"https://{site_config['domain']}",
                "Referer": f"https://{site_config['domain']}/",
            }
        )
    
    async def _find_product(
        self,
        session: httpx.AsyncClient,
        site_config: Dict,
        monitor_input: str,
        target_sizes: List[str]
    ) -> tuple[Optional[str], Optional[str]]:
        """Find product and variant"""
        try:
            # Search API
            search_url = f"{site_config['api_base']}/products/search"
            params = {"query": monitor_input, "limit": 24}
            
            response = await session.get(search_url, params=params)
            
            if response.status_code != 200:
                return None, None
            
            data = response.json()
            products = data.get("products", [])
            
            if not products:
                return None, None
            
            # Find matching product
            for product in products:
                product_id = product.get("id")
                
                # Get product details for variants
                detail_url = f"{site_config['api_base']}/products/{product_id}"
                detail_response = await session.get(detail_url)
                
                if detail_response.status_code != 200:
                    continue
                
                detail_data = detail_response.json()
                variants = detail_data.get("variants", [])
                
                # Find matching size
                for variant in variants:
                    if not variant.get("available"):
                        continue
                    
                    size = str(variant.get("size", "")).strip()
                    
                    if target_sizes:
                        if size in target_sizes or any(s in size for s in target_sizes):
                            return product_id, variant.get("id")
                    else:
                        return product_id, variant.get("id")
            
            return None, None
        
        except Exception as e:
            logger.error("Find product error", error=str(e))
            return None, None
    
    async def _add_to_cart(
        self,
        session: httpx.AsyncClient,
        site_config: Dict,
        product_id: str,
        variant_id: str
    ) -> Optional[Dict]:
        """Add product to cart"""
        try:
            cart_url = site_config["cart_api"]
            
            payload = {
                "productId": product_id,
                "variantId": variant_id,
                "quantity": 1
            }
            
            response = await session.post(
                cart_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in (200, 201):
                return response.json()
            
            return None
        
        except Exception as e:
            logger.error("Add to cart error", error=str(e))
            return None
    
    async def _create_checkout_session(
        self,
        session: httpx.AsyncClient,
        site_config: Dict,
        cart_data: Dict
    ) -> Optional[FootsiteSession]:
        """Create checkout session"""
        try:
            checkout_url = f"{site_config['checkout_api']}/session"
            
            response = await session.post(checkout_url)
            
            if response.status_code not in (200, 201):
                return None
            
            data = response.json()
            
            return FootsiteSession(
                cart_id=cart_data.get("id", ""),
                session_token=data.get("sessionToken", ""),
                csrf_token=data.get("csrfToken", ""),
                site=site_config["domain"]
            )
        
        except Exception as e:
            logger.error("Create checkout session error", error=str(e))
            return None
    
    async def _submit_shipping(
        self,
        session: httpx.AsyncClient,
        site_config: Dict,
        checkout_session: FootsiteSession,
        profile: Profile
    ) -> bool:
        """Submit shipping information"""
        shipping = profile.shipping
        
        payload = {
            "email": profile.email,
            "phone": profile.phone,
            "shippingAddress": {
                "firstName": shipping.first_name,
                "lastName": shipping.last_name,
                "address1": shipping.address1,
                "address2": shipping.address2,
                "city": shipping.city,
                "state": shipping.state,
                "postalCode": shipping.zip_code,
                "country": "US",
            },
            "shippingMethod": "standard"
        }
        
        try:
            url = f"{site_config['checkout_api']}/shipping"
            
            response = await session.post(
                url,
                json=payload,
                headers={
                    "X-Session-Token": checkout_session.session_token,
                    "X-CSRF-Token": checkout_session.csrf_token,
                }
            )
            
            return response.status_code in (200, 201)
        
        except Exception as e:
            logger.error("Submit shipping error", error=str(e))
            return False
    
    async def _submit_payment(
        self,
        session: httpx.AsyncClient,
        site_config: Dict,
        checkout_session: FootsiteSession,
        profile: Profile,
        captcha_solver: Any
    ) -> Dict[str, Any]:
        """Submit payment via Adyen"""
        billing = profile.billing_address
        card = profile.card
        
        # Adyen encrypted card data (simplified - real implementation needs Adyen SDK)
        encrypted_card = await self._encrypt_card_data(card)
        
        payload = {
            "billingAddress": {
                "firstName": billing.first_name,
                "lastName": billing.last_name,
                "address1": billing.address1,
                "address2": billing.address2,
                "city": billing.city,
                "state": billing.state,
                "postalCode": billing.zip_code,
                "country": "US",
            },
            "payment": {
                "method": "card",
                "encryptedCardData": encrypted_card,
            }
        }
        
        try:
            url = f"{site_config['checkout_api']}/payment"
            
            response = await session.post(
                url,
                json=payload,
                headers={
                    "X-Session-Token": checkout_session.session_token,
                    "X-CSRF-Token": checkout_session.csrf_token,
                }
            )
            
            if response.status_code in (200, 201):
                data = response.json()
                
                if data.get("status") == "success":
                    return {
                        "success": True,
                        "order_number": data.get("orderNumber"),
                        "total": data.get("total")
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("message", "Payment failed")
                    }
            
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            logger.error("Submit payment error", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _encrypt_card_data(self, card) -> str:
        """Encrypt card data for Adyen (placeholder)"""
        # Real implementation would use Adyen Web SDK
        # This is a simplified placeholder
        return f"encrypted_{card.number[-4:]}"
