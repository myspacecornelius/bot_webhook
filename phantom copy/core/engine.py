"""
Phantom Engine - Main orchestrator for the bot
Coordinates all components: tasks, monitors, proxies, profiles
"""

import asyncio
from typing import Optional, Dict, Any
import structlog

from ..utils.config import get_config, ConfigManager
from ..utils.database import db, init_db
from .proxy import ProxyManager
from .profile import ProfileManager
from .task import TaskManager, Task, TaskResult

logger = structlog.get_logger()


class PhantomEngine:
    """
    Main engine that orchestrates all bot components
    """
    
    _instance: Optional['PhantomEngine'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self.config = get_config()
        self.proxy_manager = ProxyManager()
        self.profile_manager = ProfileManager()
        self.task_manager = TaskManager(
            max_concurrent=self.config.performance.max_concurrent_tasks
        )
        
        # Component references (injected later)
        self._monitor_manager = None
        self._checkout_modules: Dict[str, Any] = {}
        self._captcha_solver = None
        self._notifier = None
        self._intelligence = None
        
        self._running = False
        self._initialized = True
        
        logger.info("PhantomEngine initialized")
    
    async def start(self):
        """Start the engine and all components"""
        if self._running:
            logger.warning("Engine already running")
            return
        
        logger.info("Starting Phantom Engine...")
        
        # Initialize database
        await init_db()
        
        # Start proxy manager
        await self.proxy_manager.start()
        
        # Set up task manager checkout handler
        self.task_manager.set_checkout_handler(self._handle_checkout)
        
        # Start monitors if available
        if self._monitor_manager:
            await self._monitor_manager.start()
        
        self._running = True
        logger.info("Phantom Engine started successfully")
    
    async def stop(self):
        """Stop the engine and all components"""
        if not self._running:
            return
        
        logger.info("Stopping Phantom Engine...")
        
        # Stop all tasks
        await self.task_manager.stop_all()
        
        # Stop monitors
        if self._monitor_manager:
            await self._monitor_manager.stop()
        
        # Stop proxy manager
        await self.proxy_manager.stop()
        
        # Close database
        await db.close()
        
        self._running = False
        logger.info("Phantom Engine stopped")
    
    def register_checkout_module(self, site_type: str, module: Any):
        """Register a checkout module for a site type"""
        self._checkout_modules[site_type] = module
        logger.debug("Checkout module registered", site_type=site_type)
    
    def set_monitor_manager(self, manager: Any):
        """Set the monitor manager and wire it to TaskManager for auto-task creation"""
        self._monitor_manager = manager
        # Connect TaskManager to MonitorManager for auto-task creation
        if hasattr(manager, 'set_task_manager'):
            manager.set_task_manager(self.task_manager)
    
    def set_captcha_solver(self, solver: Any):
        """Set the captcha solver"""
        self._captcha_solver = solver
    
    def set_notifier(self, notifier: Any):
        """Set the notification handler"""
        self._notifier = notifier
    
    def set_intelligence(self, intelligence: Any):
        """Set the market intelligence module"""
        self._intelligence = intelligence
    
    async def _handle_checkout(self, task: Task) -> TaskResult:
        """Main checkout handler - routes to appropriate module"""
        site_type = task.config.site_type
        
        if site_type not in self._checkout_modules:
            return TaskResult(
                success=False,
                error_message=f"No checkout module for site type: {site_type}"
            )
        
        module = self._checkout_modules[site_type]
        
        # Get proxy
        proxy = self.proxy_manager.get_proxy(
            group_id=task.config.proxy_group_id,
            task_id=task.id,
            site=task.config.site_name
        )
        
        # Get profile
        profile = None
        if task.config.profile_id:
            profile = self.profile_manager.get_profile(task.config.profile_id)
        elif task.config.profile_group_id:
            profile = self.profile_manager.get_random_profile(task.config.profile_group_id)
        
        if not profile:
            return TaskResult(
                success=False,
                error_message="No profile available"
            )
        
        # Execute checkout
        try:
            result = await module.checkout(
                task=task,
                profile=profile,
                proxy=proxy,
                captcha_solver=self._captcha_solver
            )
            
            # Record results
            if result.success:
                if proxy:
                    self.proxy_manager.record_success(proxy.id, 0, task.config.site_name)
                if result.total_price:
                    self.profile_manager.record_checkout(profile.id, result.total_price)
                
                # Send notification
                if self._notifier:
                    await self._notifier.send_success(task, result)
            else:
                if proxy:
                    self.proxy_manager.record_failure(proxy.id, task.config.site_name)
                
                if self._notifier and "declined" in (result.error_message or "").lower():
                    await self._notifier.send_decline(task, result)
            
            return result
            
        except Exception as e:
            logger.error("Checkout error", task_id=task.id[:8], error=str(e))
            if proxy:
                self.proxy_manager.record_failure(proxy.id, task.config.site_name)
            return TaskResult(success=False, error_message=str(e))
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall engine status"""
        return {
            "running": self._running,
            "tasks": self.task_manager.get_stats(),
            "proxies": self.proxy_manager.get_stats(),
            "profiles": {
                "total": len(self.profile_manager.profiles),
                "groups": len(self.profile_manager.groups),
            },
            "modules": list(self._checkout_modules.keys()),
        }
    
    async def import_valor_config(self, config_path: str) -> Dict[str, int]:
        """Import configuration from Valor bot format"""
        import json
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        counts = {"profiles": 0, "proxies": 0, "tasks": 0}
        
        # Import profiles
        counts["profiles"] = self.profile_manager.import_from_valor(data)
        
        # Import proxies
        proxies_data = data.get("proxies", {})
        for group_id, group_data in proxies_data.get("groups", {}).items():
            proxy_string = group_data.get("proxyString", "")
            if proxy_string:
                ids = self.proxy_manager.add_proxies_from_string(proxy_string, group_id)
                counts["proxies"] += len(ids)
        
        logger.info("Valor config imported", **counts)
        return counts


# Global engine instance
engine = PhantomEngine()


async def get_engine() -> PhantomEngine:
    """Get the engine instance"""
    return engine
