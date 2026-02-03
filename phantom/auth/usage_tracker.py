"""Track user usage and enforce tier limits"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import structlog

logger = structlog.get_logger()

class UsageTracker:
    """Track and enforce usage limits per user"""
    
    def __init__(self):
        # In-memory storage for now - replace with Redis for production
        self.daily_tasks: Dict[str, Dict[str, int]] = {}
        self.active_tasks: Dict[str, int] = {}
        self.active_monitors: Dict[str, int] = {}
    
    def _get_date_key(self) -> str:
        """Get current date as key"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def check_task_limit(self, user_id: str, max_tasks: int, max_daily: int) -> Dict[str, Any]:
        """Check if user can create a new task"""
        # Check concurrent task limit
        current_tasks = self.active_tasks.get(user_id, 0)
        if current_tasks >= max_tasks:
            return {
                "allowed": False,
                "error": f"Maximum concurrent tasks ({max_tasks}) reached. Upgrade for more.",
                "current": current_tasks,
                "limit": max_tasks
            }
        
        # Check daily limit
        date_key = self._get_date_key()
        if user_id not in self.daily_tasks:
            self.daily_tasks[user_id] = {}
        
        daily_count = self.daily_tasks[user_id].get(date_key, 0)
        if daily_count >= max_daily:
            return {
                "allowed": False,
                "error": f"Daily task limit ({max_daily}) reached. Resets at midnight.",
                "current": daily_count,
                "limit": max_daily
            }
        
        return {
            "allowed": True,
            "current_tasks": current_tasks,
            "daily_count": daily_count,
            "limits": {
                "max_tasks": max_tasks,
                "max_daily": max_daily
            }
        }
    
    def increment_task(self, user_id: str):
        """Increment task counters when task is created"""
        # Increment concurrent tasks
        self.active_tasks[user_id] = self.active_tasks.get(user_id, 0) + 1
        
        # Increment daily tasks
        date_key = self._get_date_key()
        if user_id not in self.daily_tasks:
            self.daily_tasks[user_id] = {}
        self.daily_tasks[user_id][date_key] = self.daily_tasks[user_id].get(date_key, 0) + 1
        
        logger.info(
            "Task created",
            user_id=user_id,
            active_tasks=self.active_tasks[user_id],
            daily_tasks=self.daily_tasks[user_id][date_key]
        )
    
    def decrement_task(self, user_id: str):
        """Decrement concurrent task count when task completes"""
        if user_id in self.active_tasks and self.active_tasks[user_id] > 0:
            self.active_tasks[user_id] -= 1
    
    def check_monitor_limit(self, user_id: str, max_monitors: int) -> Dict[str, Any]:
        """Check if user can add more monitors"""
        current_monitors = self.active_monitors.get(user_id, 0)
        
        if current_monitors >= max_monitors:
            return {
                "allowed": False,
                "error": f"Maximum monitors ({max_monitors}) reached. Upgrade for more.",
                "current": current_monitors,
                "limit": max_monitors
            }
        
        return {
            "allowed": True,
            "current": current_monitors,
            "limit": max_monitors
        }
    
    def set_monitors(self, user_id: str, count: int):
        """Set number of active monitors for user"""
        self.active_monitors[user_id] = count
        logger.info("Monitors updated", user_id=user_id, count=count)
    
    def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get current usage statistics for user"""
        date_key = self._get_date_key()
        
        return {
            "active_tasks": self.active_tasks.get(user_id, 0),
            "active_monitors": self.active_monitors.get(user_id, 0),
            "daily_tasks": self.daily_tasks.get(user_id, {}).get(date_key, 0),
            "date": date_key
        }
    
    def cleanup_old_data(self):
        """Clean up old daily task data (run periodically)"""
        cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        for user_id in list(self.daily_tasks.keys()):
            for date_key in list(self.daily_tasks[user_id].keys()):
                if date_key < cutoff_date:
                    del self.daily_tasks[user_id][date_key]
