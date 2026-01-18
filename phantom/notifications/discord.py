"""
Discord Webhook Notifications
Sends rich embeds for successes, failures, and restocks
"""

from typing import Optional, Dict, Any
from datetime import datetime
import httpx
import structlog

from ..core.task import Task, TaskResult

logger = structlog.get_logger()


class DiscordNotifier:
    """
    Discord webhook integration for notifications
    
    Features:
    - Rich embeds with product images
    - Color-coded by status
    - Quick links to checkout/order
    - Profit calculations
    """
    
    # Embed colors
    COLOR_SUCCESS = 0x00FF00  # Green
    COLOR_DECLINE = 0xFF0000  # Red
    COLOR_CARTED = 0xFFFF00   # Yellow
    COLOR_RESTOCK = 0x00FFFF  # Cyan
    COLOR_INFO = 0x7289DA    # Discord blue
    
    def __init__(
        self,
        webhook_url: str,
        success_webhook: Optional[str] = None,
        failure_webhook: Optional[str] = None,
        restock_webhook: Optional[str] = None
    ):
        self.webhook_url = webhook_url
        self.success_webhook = success_webhook or webhook_url
        self.failure_webhook = failure_webhook or webhook_url
        self.restock_webhook = restock_webhook or webhook_url
        
        self._session: Optional[httpx.AsyncClient] = None
        logger.info("DiscordNotifier initialized")
    
    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None:
            self._session = httpx.AsyncClient(timeout=10.0)
        return self._session
    
    async def _send_webhook(self, url: str, payload: Dict[str, Any]) -> bool:
        """Send webhook request"""
        try:
            session = await self._get_session()
            response = await session.post(url, json=payload)
            return response.status_code in (200, 204)
        except Exception as e:
            logger.error("Discord webhook failed", error=str(e))
            return False
    
    async def send_success(self, task: Task, result: TaskResult):
        """Send success notification"""
        embed = {
            "title": "✅ Successful Checkout!",
            "color": self.COLOR_SUCCESS,
            "fields": [
                {"name": "Product", "value": task.product.name if task.product else "Unknown", "inline": True},
                {"name": "Site", "value": task.config.site_name, "inline": True},
                {"name": "Size", "value": task.product.size if task.product else "N/A", "inline": True},
                {"name": "Order #", "value": result.order_number or "N/A", "inline": True},
                {"name": "Price", "value": f"${result.total_price:.2f}" if result.total_price else "N/A", "inline": True},
                {"name": "Checkout Time", "value": f"{result.checkout_time:.2f}s" if result.checkout_time else "N/A", "inline": True},
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Phantom Bot"}
        }
        
        # Add product image if available
        if task.product and task.product.image_url:
            embed["thumbnail"] = {"url": task.product.image_url}
        
        # Add checkout link
        if result.checkout_url:
            embed["url"] = result.checkout_url
        
        payload = {"embeds": [embed]}
        await self._send_webhook(self.success_webhook, payload)
    
    async def send_decline(self, task: Task, result: TaskResult):
        """Send decline notification"""
        embed = {
            "title": "❌ Card Declined",
            "color": self.COLOR_DECLINE,
            "fields": [
                {"name": "Product", "value": task.product.name if task.product else "Unknown", "inline": True},
                {"name": "Site", "value": task.config.site_name, "inline": True},
                {"name": "Error", "value": result.error_message or "Unknown error", "inline": False},
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Phantom Bot"}
        }
        
        if result.checkout_url:
            embed["url"] = result.checkout_url
            embed["description"] = f"[Complete manually]({result.checkout_url})"
        
        payload = {"embeds": [embed]}
        await self._send_webhook(self.failure_webhook, payload)
    
    async def send_carted(self, task: Task, checkout_url: str):
        """Send carted notification"""
        embed = {
            "title": "🛒 Product Carted!",
            "color": self.COLOR_CARTED,
            "description": f"[Complete Checkout]({checkout_url})",
            "fields": [
                {"name": "Product", "value": task.product.name if task.product else "Unknown", "inline": True},
                {"name": "Site", "value": task.config.site_name, "inline": True},
                {"name": "Size", "value": task.product.size if task.product else "N/A", "inline": True},
            ],
            "url": checkout_url,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Phantom Bot - Complete checkout quickly!"}
        }
        
        if task.product and task.product.image_url:
            embed["thumbnail"] = {"url": task.product.image_url}
        
        payload = {"embeds": [embed]}
        await self._send_webhook(self.webhook_url, payload)
    
    async def send_restock(
        self,
        product_name: str,
        site: str,
        sizes: list,
        url: str,
        image_url: Optional[str] = None,
        price: Optional[float] = None,
        estimated_profit: Optional[float] = None
    ):
        """Send restock notification"""
        fields = [
            {"name": "Product", "value": product_name, "inline": True},
            {"name": "Site", "value": site, "inline": True},
            {"name": "Sizes", "value": ", ".join(sizes) if sizes else "Various", "inline": True},
        ]
        
        if price:
            fields.append({"name": "Price", "value": f"${price:.2f}", "inline": True})
        
        if estimated_profit:
            profit_color = "🟢" if estimated_profit > 30 else "🟡" if estimated_profit > 0 else "🔴"
            fields.append({"name": "Est. Profit", "value": f"{profit_color} ${estimated_profit:.2f}", "inline": True})
        
        embed = {
            "title": "🔄 Restock Detected!",
            "color": self.COLOR_RESTOCK,
            "description": f"[View Product]({url})",
            "fields": fields,
            "url": url,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Phantom Bot - Act fast!"}
        }
        
        if image_url:
            embed["thumbnail"] = {"url": image_url}
        
        payload = {"embeds": [embed]}
        await self._send_webhook(self.restock_webhook, payload)
    
    async def send_release_reminder(
        self,
        release_name: str,
        release_time: datetime,
        retail_price: float,
        estimated_profit: Optional[float] = None,
        image_url: Optional[str] = None
    ):
        """Send release reminder"""
        time_until = release_time - datetime.now()
        minutes = int(time_until.total_seconds() / 60)
        
        embed = {
            "title": f"⏰ Release in {minutes} minutes!",
            "color": self.COLOR_INFO,
            "fields": [
                {"name": "Product", "value": release_name, "inline": True},
                {"name": "Time", "value": release_time.strftime("%I:%M %p"), "inline": True},
                {"name": "Retail", "value": f"${retail_price:.2f}", "inline": True},
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Phantom Bot"}
        }
        
        if estimated_profit:
            embed["fields"].append({
                "name": "Est. Profit",
                "value": f"${estimated_profit:.2f}",
                "inline": True
            })
        
        if image_url:
            embed["thumbnail"] = {"url": image_url}
        
        payload = {"embeds": [embed]}
        await self._send_webhook(self.webhook_url, payload)
    
    async def send_daily_summary(
        self,
        checkouts: int,
        declines: int,
        total_spent: float,
        total_profit: float
    ):
        """Send daily summary"""
        embed = {
            "title": "📊 Daily Summary",
            "color": self.COLOR_INFO,
            "fields": [
                {"name": "Checkouts", "value": str(checkouts), "inline": True},
                {"name": "Declines", "value": str(declines), "inline": True},
                {"name": "Success Rate", "value": f"{checkouts/(checkouts+declines)*100:.1f}%" if checkouts+declines > 0 else "N/A", "inline": True},
                {"name": "Total Spent", "value": f"${total_spent:.2f}", "inline": True},
                {"name": "Est. Profit", "value": f"${total_profit:.2f}", "inline": True},
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Phantom Bot - Daily Report"}
        }
        
        payload = {"embeds": [embed]}
        await self._send_webhook(self.webhook_url, payload)
    
    async def close(self):
        if self._session:
            await self._session.aclose()
