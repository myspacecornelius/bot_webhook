"""
Base Monitor Class
Foundation for all site-specific monitors
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Awaitable
from datetime import datetime
from enum import Enum
import structlog

from .keywords import KeywordMatcher
from ..utils.config import get_config

logger = structlog.get_logger()


class MonitorStatus(Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    FOUND = "found"
    ERROR = "error"
    STOPPED = "stopped"
    RATE_LIMITED = "rate_limited"


@dataclass
class ProductInfo:
    """Information about a monitored product"""
    url: str
    title: str
    sku: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    available: bool = False
    sizes_available: List[str] = field(default_factory=list)
    variants: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MonitorResult:
    """Result from a monitor check"""
    success: bool
    products: List[ProductInfo] = field(default_factory=list)
    error: Optional[str] = None
    response_time: float = 0.0
    rate_limited: bool = False


@dataclass
class MonitorConfig:
    """Configuration for a monitor"""
    site_name: str
    site_url: str
    keywords: str = ""
    delay: int = 3000  # ms
    error_delay: int = 5000  # ms
    webhook_url: Optional[str] = None
    proxy_group_id: Optional[str] = None
    enabled: bool = True


class BaseMonitor(ABC):
    """
    Abstract base class for all product monitors
    Subclass this for site-specific implementations
    """
    
    def __init__(self, config: MonitorConfig):
        self.config = config
        self.app_config = get_config()
        self.keyword_matcher = KeywordMatcher.from_string(config.keywords)
        
        self.status = MonitorStatus.IDLE
        self.status_message = ""
        self.is_running = False
        
        self._task: Optional[asyncio.Task] = None
        self._stop_requested = False
        self._check_count = 0
        self._error_count = 0
        self._last_check: Optional[datetime] = None
        self._found_products: Dict[str, ProductInfo] = {}
        
        # Callbacks
        self._on_product_found: Optional[Callable[[ProductInfo], Awaitable[None]]] = None
        self._on_status_change: Optional[Callable[[MonitorStatus, str], Awaitable[None]]] = None
        
        logger.info("Monitor initialized", site=config.site_name)
    
    def set_callbacks(
        self,
        on_product_found: Optional[Callable[[ProductInfo], Awaitable[None]]] = None,
        on_status_change: Optional[Callable[[MonitorStatus, str], Awaitable[None]]] = None
    ):
        """Set event callbacks"""
        self._on_product_found = on_product_found
        self._on_status_change = on_status_change
    
    async def start(self):
        """Start the monitor"""
        if self.is_running:
            return
        
        self._stop_requested = False
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        
        await self._update_status(MonitorStatus.STARTING, "Initializing...")
        logger.info("Monitor started", site=self.config.site_name)
    
    async def stop(self):
        """Stop the monitor"""
        self._stop_requested = True
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self.is_running = False
        await self._update_status(MonitorStatus.STOPPED, "Stopped")
        logger.info("Monitor stopped", site=self.config.site_name)
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        await self._update_status(MonitorStatus.RUNNING, "Monitoring...")
        
        while not self._stop_requested:
            try:
                result = await self.check()
                self._check_count += 1
                self._last_check = datetime.now()
                
                if result.success:
                    self._error_count = 0
                    
                    for product in result.products:
                        if self._is_new_product(product):
                            await self._handle_new_product(product)
                    
                    delay = self.config.delay / 1000
                else:
                    self._error_count += 1
                    
                    if result.rate_limited:
                        await self._update_status(
                            MonitorStatus.RATE_LIMITED,
                            "Rate limited, backing off..."
                        )
                        delay = self.config.error_delay * 2 / 1000
                    else:
                        delay = self.config.error_delay / 1000
                
                await asyncio.sleep(delay)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Monitor error", site=self.config.site_name, error=str(e))
                self._error_count += 1
                await self._update_status(MonitorStatus.ERROR, str(e))
                await asyncio.sleep(self.config.error_delay / 1000)
    
    def _is_new_product(self, product: ProductInfo) -> bool:
        """Check if this is a new product we haven't seen"""
        key = f"{product.url}:{','.join(sorted(product.sizes_available))}"
        
        if key in self._found_products:
            old = self._found_products[key]
            # Check if availability changed
            if old.sizes_available == product.sizes_available:
                return False
        
        self._found_products[key] = product
        return True
    
    async def _handle_new_product(self, product: ProductInfo):
        """Handle a newly found product"""
        # Check if it matches keywords
        matches, confidence = self.keyword_matcher.matches(
            product.title,
            product.sku
        )
        
        if not matches:
            return
        
        logger.info(
            "Product found!",
            site=self.config.site_name,
            title=product.title,
            sizes=product.sizes_available,
            confidence=confidence
        )
        
        await self._update_status(
            MonitorStatus.FOUND,
            f"Found: {product.title}"
        )
        
        if self._on_product_found:
            await self._on_product_found(product)
    
    async def _update_status(self, status: MonitorStatus, message: str = ""):
        """Update monitor status"""
        self.status = status
        self.status_message = message
        
        if self._on_status_change:
            await self._on_status_change(status, message)
    
    @abstractmethod
    async def check(self) -> MonitorResult:
        """
        Perform a single check for products
        Must be implemented by subclasses
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics"""
        return {
            "site": self.config.site_name,
            "status": self.status.value,
            "status_message": self.status_message,
            "is_running": self.is_running,
            "check_count": self._check_count,
            "error_count": self._error_count,
            "products_found": len(self._found_products),
            "last_check": self._last_check.isoformat() if self._last_check else None,
        }


class MonitorManager:
    """Manages multiple monitors"""
    
    def __init__(self):
        self.monitors: Dict[str, BaseMonitor] = {}
        self._on_product_found: Optional[Callable[[str, ProductInfo], Awaitable[None]]] = None
        logger.info("MonitorManager initialized")
    
    def add_monitor(self, monitor_id: str, monitor: BaseMonitor):
        """Add a monitor"""
        self.monitors[monitor_id] = monitor
        
        # Set up callback to forward to manager callback
        async def forward_callback(product: ProductInfo):
            if self._on_product_found:
                await self._on_product_found(monitor_id, product)
        
        monitor.set_callbacks(on_product_found=forward_callback)
    
    def set_product_callback(self, callback: Callable[[str, ProductInfo], Awaitable[None]]):
        """Set callback for when any monitor finds a product"""
        self._on_product_found = callback
    
    async def start_all(self):
        """Start all monitors"""
        for monitor in self.monitors.values():
            await monitor.start()
    
    async def stop_all(self):
        """Stop all monitors"""
        for monitor in self.monitors.values():
            await monitor.stop()
    
    async def start(self, monitor_id: str):
        """Start a specific monitor"""
        if monitor_id in self.monitors:
            await self.monitors[monitor_id].start()
    
    async def stop(self, monitor_id: str):
        """Stop a specific monitor"""
        if monitor_id in self.monitors:
            await self.monitors[monitor_id].stop()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stats for all monitors"""
        return {
            monitor_id: monitor.get_stats()
            for monitor_id, monitor in self.monitors.items()
        }
