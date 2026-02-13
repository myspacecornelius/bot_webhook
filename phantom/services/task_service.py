"""
Task service — orchestrates task creation, lifecycle, and analytics.
Encapsulates the business logic that was previously inline in routes.py.
"""

import re
from typing import Any, Dict, List
from urllib.parse import urlparse

import structlog

from ..core.engine import engine
from ..core.task import TaskConfig, TaskMode
from ..domain.errors import NotFoundError
from ..domain.models import QuickTaskCreate, TaskCreate

logger = structlog.get_logger()


class TaskService:
    """Task creation, lifecycle management, and analytics."""

    async def list_tasks(self) -> Dict[str, Any]:
        return {
            "tasks": [t.to_dict() for t in engine.task_manager.tasks.values()],
            "stats": engine.task_manager.get_stats(),
        }

    def create_task(self, data: TaskCreate) -> Dict[str, Any]:
        config = TaskConfig(
            site_type=data.site_type,
            site_name=data.site_name,
            site_url=data.site_url,
            monitor_input=data.monitor_input,
            sizes=data.sizes,
            mode=TaskMode(data.mode),
            profile_id=data.profile_id,
            proxy_group_id=data.proxy_group_id,
            monitor_delay=data.monitor_delay,
            retry_delay=data.retry_delay,
        )
        task = engine.task_manager.create_task(config)
        return {"id": task.id, "message": "Task created"}

    async def start_task(self, task_id: str) -> None:
        await engine.task_manager.start_task(task_id)

    def stop_task(self, task_id: str) -> Dict[str, str]:
        if engine.task_manager.stop_task(task_id):
            return {"message": "Task stopping..."}
        raise NotFoundError("Task", task_id)

    def delete_task(self, task_id: str) -> Dict[str, str]:
        if engine.task_manager.delete_task(task_id):
            return {"message": "Task deleted"}
        raise NotFoundError("Task", task_id)

    async def start_all(self) -> None:
        await engine.task_manager.start_all()

    async def stop_all(self) -> None:
        await engine.task_manager.stop_all()

    # ── Quick Task ────────────────────────────────────────────

    def create_quick_task(self, data: QuickTaskCreate) -> List[str]:
        """Parse product URL, auto-detect site, and create task(s).

        Returns list of created task IDs.
        """
        url = data.url.strip()
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")

        site_name = domain.split(".")[0].title()
        site_url = f"{parsed.scheme}://{parsed.netloc}"
        site_type = "shopify"

        path = parsed.path
        monitor_input = url

        product_match = re.search(r"/products?/([^/?]+)", path)
        if product_match:
            product_slug = product_match.group(1)
            monitor_input = product_slug.replace("-", " ").title()

        task_ids: List[str] = []
        for _ in range(data.quantity):
            config = TaskConfig(
                site_type=site_type,
                site_name=site_name,
                site_url=site_url,
                product_url=url,
                monitor_input=monitor_input,
                sizes=data.sizes or [],
                mode=TaskMode(data.mode),
                profile_id=data.profile_id,
                proxy_group_id=data.proxy_group_id,
                monitor_delay=1000,
                retry_delay=1500,
            )
            task = engine.task_manager.create_task(config)
            task_ids.append(task.id)

        return task_ids

    # ── Analytics ─────────────────────────────────────────────

    def get_checkout_analytics(self) -> Dict[str, Any]:
        tasks = list(engine.task_manager.tasks.values())
        stats = engine.task_manager.get_stats()

        success_count = stats.get("success", 0)
        failed_count = stats.get("failed", 0) + stats.get("declined", 0)
        pending_count = stats.get("running", 0) + stats.get("idle", 0)
        total = stats.get("total", 0)

        by_site: Dict[str, Dict[str, int]] = {}
        for t in tasks:
            site = t.config.site_name or "unknown"
            if site not in by_site:
                by_site[site] = {"success": 0, "failed": 0, "total": 0}
            by_site[site]["total"] += 1
            if t.result:
                if t.result.success:
                    by_site[site]["success"] += 1
                else:
                    by_site[site]["failed"] += 1

        return {
            "total_tasks": total,
            "success": success_count,
            "failed": failed_count,
            "declined": stats.get("declined", 0),
            "pending": pending_count,
            "success_rate": round((success_count / total * 100), 1) if total > 0 else 0,
            "avg_checkout_time": stats.get("avg_checkout_time"),
            "total_retries": stats.get("total_retries", 0),
            "by_site": by_site,
        }


task_service = TaskService()
