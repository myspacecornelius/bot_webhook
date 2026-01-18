"""
Desktop Notifications
Native OS notifications for important events
"""

import platform
from typing import Optional
import structlog

logger = structlog.get_logger()


class DesktopNotifier:
    """
    Cross-platform desktop notifications
    Uses plyer for compatibility across Windows, macOS, and Linux
    """
    
    def __init__(self, app_name: str = "Phantom Bot"):
        self.app_name = app_name
        self._available = self._check_availability()
        
        if self._available:
            logger.info("DesktopNotifier initialized")
        else:
            logger.warning("Desktop notifications not available")
    
    def _check_availability(self) -> bool:
        """Check if notifications are available"""
        try:
            from plyer import notification
            return True
        except ImportError:
            return False
    
    def notify(
        self,
        title: str,
        message: str,
        timeout: int = 10,
        app_icon: Optional[str] = None
    ):
        """Send a desktop notification"""
        if not self._available:
            return
        
        try:
            from plyer import notification
            
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                app_icon=app_icon,
                timeout=timeout
            )
            
        except Exception as e:
            logger.warning("Desktop notification failed", error=str(e))
    
    def success(self, product_name: str, site: str, order_number: str):
        """Notify successful checkout"""
        self.notify(
            title="✅ Checkout Success!",
            message=f"{product_name}\n{site}\nOrder: {order_number}",
            timeout=15
        )
    
    def decline(self, product_name: str, site: str):
        """Notify card decline"""
        self.notify(
            title="❌ Card Declined",
            message=f"{product_name}\n{site}\nCheck webhook for details",
            timeout=10
        )
    
    def carted(self, product_name: str, site: str):
        """Notify product carted"""
        self.notify(
            title="🛒 Product Carted!",
            message=f"{product_name}\n{site}\nComplete checkout quickly!",
            timeout=30
        )
    
    def restock(self, product_name: str, site: str, sizes: list):
        """Notify restock detected"""
        self.notify(
            title="🔄 Restock Detected!",
            message=f"{product_name}\n{site}\nSizes: {', '.join(sizes[:5])}",
            timeout=20
        )
    
    def release_reminder(self, product_name: str, minutes: int):
        """Notify upcoming release"""
        self.notify(
            title=f"⏰ Release in {minutes} minutes!",
            message=product_name,
            timeout=30
        )
    
    def error(self, message: str):
        """Notify error"""
        self.notify(
            title="⚠️ Error",
            message=message,
            timeout=10
        )
    
    def play_sound(self, sound_type: str = "success"):
        """Play notification sound"""
        system = platform.system()
        
        try:
            if system == "Darwin":  # macOS
                import subprocess
                if sound_type == "success":
                    subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], check=False)
                else:
                    subprocess.run(["afplay", "/System/Library/Sounds/Basso.aiff"], check=False)
                    
            elif system == "Windows":
                import winsound
                if sound_type == "success":
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
                else:
                    winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
                    
        except Exception as e:
            logger.debug("Sound playback failed", error=str(e))
