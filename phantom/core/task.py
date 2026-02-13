"""
Task Management for Phantom Bot
Handles checkout task creation, execution, and lifecycle
"""

import asyncio
import uuid
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Awaitable
from enum import Enum
from datetime import datetime
import structlog

from ..utils.config import get_config

logger = structlog.get_logger()


class TaskStatus(Enum):
    IDLE = "idle"
    STARTING = "starting"
    MONITORING = "monitoring"
    WAITING_RESTOCK = "waiting_restock"
    PRODUCT_FOUND = "product_found"
    ADDING_TO_CART = "adding_to_cart"
    CARTED = "carted"
    SUBMITTING_INFO = "submitting_info"
    SUBMITTING_PAYMENT = "submitting_payment"
    PROCESSING = "processing"
    CHECKOUT_QUEUE = "checkout_queue"
    SOLVING_CAPTCHA = "solving_captcha"
    SUCCESS = "success"
    DECLINED = "declined"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    ERROR = "error"


class TaskMode(Enum):
    NORMAL = "normal"
    FAST = "fast"
    SAFE = "safe"
    PRELOAD = "preload"
    REQUEST = "request"


@dataclass
class TaskProduct:
    """Product information for a task"""

    url: Optional[str] = None
    name: Optional[str] = None
    sku: Optional[str] = None
    variant_id: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[float] = None
    size: Optional[str] = None


@dataclass
class TaskResult:
    """Result of a completed task"""

    success: bool = False
    order_number: Optional[str] = None
    checkout_url: Optional[str] = None
    error_message: Optional[str] = None
    checkout_time: Optional[float] = None
    total_price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TaskConfig:
    """Configuration for a task"""

    site_type: str = "shopify"
    site_name: str = ""
    site_url: str = ""
    monitor_input: str = ""
    product_url: Optional[str] = None
    sizes: List[str] = field(default_factory=list)
    size_preference: str = "preferred"
    mode: TaskMode = TaskMode.NORMAL
    monitor_delay: int = 3000
    retry_delay: int = 2000
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    profile_id: Optional[str] = None
    profile_group_id: Optional[str] = None
    proxy_group_id: Optional[str] = None
    retry_on_decline: bool = False
    retry_on_error: bool = True
    max_retries: int = 3
    use_captcha_harvester: bool = True


@dataclass
class Task:
    """A checkout task"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    group_id: Optional[str] = None
    config: TaskConfig = field(default_factory=TaskConfig)
    status: TaskStatus = TaskStatus.IDLE
    status_message: str = ""
    is_running: bool = False
    product: Optional[TaskProduct] = None
    result: Optional[TaskResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    _retry_count: int = 0
    _cancel_requested: bool = False

    def update_status(self, status: TaskStatus, message: str = ""):
        self.status = status
        self.status_message = message


@dataclass
class TaskGroup:
    """Group of tasks"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    color: str = "#7289DA"
    task_ids: List[str] = field(default_factory=list)
    running_count: int = 0
    success_count: int = 0
    failed_count: int = 0


class TaskManager:
    """Manages checkout tasks with concurrent execution.

    Features
    --------
    - Semaphore-bounded concurrency (default 50 simultaneous tasks)
    - Automatic retry with exponential backoff
    - Per-site rate limiting to avoid triggering bot detection
    - Status-change and success callbacks for WebSocket / Discord notifications
    """

    def __init__(self, max_concurrent: int = 50):
        self.config = get_config()
        self.tasks: Dict[str, Task] = {}
        self.groups: Dict[str, TaskGroup] = {}

        # Concurrency control
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running_tasks: Dict[str, asyncio.Task] = {}

        # Handler & callbacks
        self._checkout_handler: Optional[Callable[[Task], Awaitable[TaskResult]]] = None
        self._on_status_change: Optional[Callable[[Task], Awaitable[None]]] = None
        self._on_success: Optional[Callable[[Task], Awaitable[None]]] = None

        # Per-site rate limiting  (domain → asyncio.Lock + last-request time)
        self._site_locks: Dict[str, asyncio.Lock] = {}
        self._site_last_request: Dict[str, float] = {}
        self._min_site_delay: float = 0.5  # seconds between requests to same site

        logger.info("TaskManager initialized", max_concurrent=max_concurrent)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_checkout_handler(self, handler: Callable[[Task], Awaitable[TaskResult]]):
        self._checkout_handler = handler

    def set_on_status_change(self, callback: Callable[[Task], Awaitable[None]]):
        """Called every time a task's status changes."""
        self._on_status_change = callback

    def set_on_success(self, callback: Callable[[Task], Awaitable[None]]):
        """Called when a task completes successfully."""
        self._on_success = callback

    # ------------------------------------------------------------------
    # Task & Group CRUD
    # ------------------------------------------------------------------

    def create_task(self, config: TaskConfig, group_id: Optional[str] = None) -> Task:
        task = Task(config=config, group_id=group_id)
        self.tasks[task.id] = task
        if group_id and group_id in self.groups:
            self.groups[group_id].task_ids.append(task.id)
        return task

    def create_group(self, name: str, color: str = "#7289DA") -> TaskGroup:
        group = TaskGroup(name=name, color=color)
        self.groups[group.id] = group
        return group

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def start_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task or task.is_running or not self._checkout_handler:
            return False
        async_task = asyncio.create_task(self._run_task(task))
        self._running_tasks[task_id] = async_task
        return True

    async def _run_task(self, task: Task):
        async with self._semaphore:
            task.is_running = True
            task.started_at = datetime.now()
            task._retry_count = 0
            await self._set_status(task, TaskStatus.STARTING, "Initializing...")

            max_retries = task.config.max_retries if task.config.retry_on_error else 0

            while task._retry_count <= max_retries:
                if task._cancel_requested:
                    await self._set_status(task, TaskStatus.CANCELLED)
                    break

                try:
                    # Per-site rate limiting
                    await self._acquire_site_slot(task.config.site_url)

                    result = await self._checkout_handler(task)
                    task.result = result

                    if result.success:
                        await self._set_status(
                            task,
                            TaskStatus.SUCCESS,
                            f"Order: {result.order_number}",
                        )
                        if self._on_success:
                            try:
                                await self._on_success(task)
                            except Exception:
                                pass
                        break

                    # ---- Decide whether to retry ----
                    is_decline = (
                        result.error_message
                        and "decline" in result.error_message.lower()
                    )

                    should_retry = (
                        (task.config.retry_on_error and not is_decline)
                        or (task.config.retry_on_decline and is_decline)
                    ) and task._retry_count < max_retries

                    if should_retry:
                        task._retry_count += 1
                        delay = self._backoff_delay(
                            task._retry_count, task.config.retry_delay
                        )

                        await self._set_status(
                            task,
                            TaskStatus.FAILED,
                            f"{result.error_message} — retrying in {delay:.0f}s ({task._retry_count}/{max_retries})",
                        )

                        await asyncio.sleep(delay)
                        await self._set_status(task, TaskStatus.STARTING, "Retrying...")
                        continue

                    # Not retrying
                    final_status = (
                        TaskStatus.DECLINED if is_decline else TaskStatus.FAILED
                    )
                    await self._set_status(
                        task, final_status, result.error_message or "Failed"
                    )
                    break

                except asyncio.CancelledError:
                    await self._set_status(task, TaskStatus.CANCELLED)
                    break

                except Exception as e:
                    if task._retry_count < max_retries and task.config.retry_on_error:
                        task._retry_count += 1
                        delay = self._backoff_delay(
                            task._retry_count, task.config.retry_delay
                        )
                        await self._set_status(
                            task,
                            TaskStatus.ERROR,
                            f"{e} — retrying in {delay:.0f}s",
                        )
                        await asyncio.sleep(delay)
                        continue
                    await self._set_status(task, TaskStatus.ERROR, str(e))
                    break

            task.is_running = False
            task.completed_at = datetime.now()
            self._running_tasks.pop(task.id, None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _set_status(self, task: Task, status: TaskStatus, message: str = ""):
        """Update task status and fire callback."""
        task.update_status(status, message)
        if self._on_status_change:
            try:
                await self._on_status_change(task)
            except Exception:
                pass

    async def _acquire_site_slot(self, site_url: str):
        """Per-site rate limiting to avoid triggering bot detection."""
        if not site_url:
            return

        from urllib.parse import urlparse

        domain = urlparse(site_url).netloc or site_url

        if domain not in self._site_locks:
            self._site_locks[domain] = asyncio.Lock()

        async with self._site_locks[domain]:
            last = self._site_last_request.get(domain, 0)
            elapsed = time.time() - last
            if elapsed < self._min_site_delay:
                await asyncio.sleep(self._min_site_delay - elapsed)
            self._site_last_request[domain] = time.time()

    @staticmethod
    def _backoff_delay(retry_count: int, base_delay_ms: int) -> float:
        """Exponential backoff with jitter."""
        import random

        base = (base_delay_ms / 1000) * (2 ** (retry_count - 1))
        jitter = random.uniform(0, base * 0.3)
        return min(base + jitter, 30.0)  # cap at 30s

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def stop_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task or not task.is_running:
            return False
        task._cancel_requested = True
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
        return True

    def delete_task(self, task_id: str) -> bool:
        """Remove a task from the manager. Stops it first if running."""
        if task_id not in self.tasks:
            return False
        self.stop_task(task_id)
        self._running_tasks.pop(task_id, None)
        del self.tasks[task_id]
        logger.info("task_deleted", task_id=task_id)
        return True

    async def start_all(self) -> int:
        started = 0
        for task_id in self.tasks:
            if await self.start_task(task_id):
                started += 1
        return started

    async def stop_all(self) -> int:
        stopped = 0
        for task_id in list(self._running_tasks.keys()):
            if self.stop_task(task_id):
                stopped += 1
        return stopped

    def get_stats(self) -> Dict[str, Any]:
        completed = [t for t in self.tasks.values() if t.completed_at]

        avg_checkout_time = None
        if completed:
            times = [
                t.result.checkout_time
                for t in completed
                if t.result and t.result.checkout_time
            ]
            if times:
                avg_checkout_time = sum(times) / len(times)

        return {
            "total": len(self.tasks),
            "running": len(self._running_tasks),
            "idle": sum(1 for t in self.tasks.values() if t.status == TaskStatus.IDLE),
            "success": sum(
                1 for t in self.tasks.values() if t.status == TaskStatus.SUCCESS
            ),
            "failed": sum(
                1 for t in self.tasks.values() if t.status == TaskStatus.FAILED
            ),
            "declined": sum(
                1 for t in self.tasks.values() if t.status == TaskStatus.DECLINED
            ),
            "avg_checkout_time": round(avg_checkout_time, 2)
            if avg_checkout_time
            else None,
            "total_retries": sum(t._retry_count for t in self.tasks.values()),
        }
