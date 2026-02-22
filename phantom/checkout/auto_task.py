"""
Auto-Task Spawner — Monitor → Checkout Pipeline

Reverse engineered from Valor AIO's monitor-to-task architecture:
  - Monitor detects SKU/keyword match → auto-creates N checkout tasks
  - Configurable task count per monitor (Valor uses 2-19)
  - Supports both regular and preloaded checkout sessions
  - Stop-after timeout kills stuck tasks (Valor: 80-180 seconds)
  - Auto-cleanup of completed task groups

Key Valor settings replicated:
  taskCount: 2-19 (Nike Quick Task uses 19)
  stopAfter: 80-180 (seconds)
  deleteAfterStop: true
  minSizesLoaded: 1 (trigger on partial stock)
  autoSwitchMode: true
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import structlog

from ..core.task import TaskConfig, TaskMode, TaskManager, TaskStatus
from ..monitors.shopify_monitor import DetectedProduct, ProductInfo
from .preload import preload_engine

logger = structlog.get_logger()


class SpawnStrategy(Enum):
    """How to spawn checkout tasks"""

    NORMAL = "normal"  # Standard checkout flow
    PRELOAD = "preload"  # Use pre-created checkout sessions
    FAST = "fast"  # Skip non-essential steps
    AUTO = "auto"  # Try preload first, fallback to fast


@dataclass
class AutoTaskConfig:
    """Configuration for auto-task spawning from monitors"""

    # Task creation
    task_count: int = 4  # Number of tasks to spawn per detection
    spawn_strategy: SpawnStrategy = SpawnStrategy.AUTO

    # Profiles & Proxies
    profile_ids: List[str] = field(default_factory=list)
    profile_group_id: Optional[str] = None
    proxy_group_id: Optional[str] = None
    rotate_profiles: bool = True  # Use different profile per task

    # Filtering
    target_sizes: List[str] = field(default_factory=list)
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_sizes_loaded: int = 1  # Min available sizes to trigger

    # Timeouts
    stop_after_seconds: int = 120  # Kill task after N seconds
    delete_after_stop: bool = True  # Clean up stopped tasks

    # Rate limiting
    max_spawns_per_product: int = 1  # Don't re-spawn for same product
    cooldown_seconds: int = 30  # Min time between spawns for same store


@dataclass
class QuickTaskConfig:
    """Nike Quick Task configuration — one-click task creation.

    Modeled after Valor's nikeQuickTask:
        enabled: true
        sizeRange: ["14", "13"]
        proxyGroup: {id, name}
        profileGroup: {id, name, profiles}
        taskCount: 19
    """

    enabled: bool = True
    sku: str = ""
    site_type: str = "nike"
    task_count: int = 4
    size_range: List[str] = field(default_factory=list)
    profile_group_id: Optional[str] = None
    profile_ids: List[str] = field(default_factory=list)
    proxy_group_id: Optional[str] = None
    stop_after_seconds: int = 180


@dataclass
class SpawnRecord:
    """Record of a spawned task group"""

    group_id: str
    product_title: str
    product_sku: Optional[str]
    store_name: str
    product_key: str  # Dedup key used at spawn time
    task_count: int
    delete_after_stop: bool = True  # Captured at spawn time
    spawned_at: datetime = field(default_factory=datetime.now)
    task_ids: List[str] = field(default_factory=list)
    stopped: bool = False


class AutoTaskSpawner:
    """
    Connects monitors to the task manager, automatically creating
    checkout tasks when products are detected.

    Usage:
        spawner = AutoTaskSpawner(task_manager)
        spawner.configure(AutoTaskConfig(task_count=4, ...))

        # Wire to monitor callbacks
        monitor.set_product_callback(spawner.on_product_detected)

        # Or use Quick Task for instant SKU → tasks
        await spawner.quick_task(QuickTaskConfig(sku="FQ3549-100", ...))
    """

    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
        self.config = AutoTaskConfig()
        self._spawn_history: Dict[str, SpawnRecord] = {}
        self._product_spawned: Dict[str, float] = {}  # product_key → timestamp
        self._stop_timers: Dict[str, asyncio.Task] = {}
        self._preload_engine = preload_engine

        logger.info("AutoTaskSpawner initialized")

    def configure(self, config: AutoTaskConfig):
        """Update spawn configuration"""
        self.config = config
        logger.info(
            "AutoTaskSpawner configured",
            task_count=config.task_count,
            strategy=config.spawn_strategy.value,
            stop_after=config.stop_after_seconds,
        )

    # ------------------------------------------------------------------
    # Monitor callback
    # ------------------------------------------------------------------

    async def on_product_detected(self, detected: DetectedProduct):
        """Callback invoked by MultiStoreMonitor when a product is found.

        This is THE bridge between monitoring and checkout.
        """
        product = detected.info
        store = detected.store

        # Build dedup key
        product_key = f"{store.name}:{product.sku or product.title}"

        # Check if already spawned recently
        last_spawn = self._product_spawned.get(product_key, 0)
        if time.time() - last_spawn < self.config.cooldown_seconds:
            logger.debug(
                "Skipping spawn (cooldown)",
                product=product.title[:40],
                store=store.name,
            )
            return

        # Check max spawns (use the same dedup key to avoid None-SKU collisions)
        spawn_count = sum(
            1
            for r in self._spawn_history.values()
            if r.product_key == product_key and not r.stopped
        )
        if spawn_count >= self.config.max_spawns_per_product:
            return

        # Check size availability
        available_sizes = product.sizes_available or []
        if len(available_sizes) < self.config.min_sizes_loaded:
            logger.debug(
                "Skipping spawn (insufficient sizes)",
                product=product.title[:40],
                available=len(available_sizes),
                required=self.config.min_sizes_loaded,
            )
            return

        # Filter by target sizes
        if self.config.target_sizes:
            matching = [s for s in available_sizes if s in self.config.target_sizes]
            if not matching:
                return
            available_sizes = matching

        # Check price range
        if product.price:
            if self.config.min_price and product.price < self.config.min_price:
                return
            if self.config.max_price and product.price > self.config.max_price:
                return

        # SPAWN TASKS
        logger.info(
            "🚀 Auto-spawning tasks",
            product=product.title[:50],
            store=store.name,
            sku=product.sku,
            sizes=available_sizes[:5],
            task_count=self.config.task_count,
        )

        record = await self._spawn_tasks(product, store, product_key)

        if record:
            self._product_spawned[product_key] = time.time()
            self._spawn_history[record.group_id] = record

    # ------------------------------------------------------------------
    # Quick Task (instant SKU → N tasks)
    # ------------------------------------------------------------------

    async def quick_task(self, config: QuickTaskConfig) -> Optional[SpawnRecord]:
        """Create tasks instantly for a given SKU.

        Modeled after Valor's Nike Quick Task which spawns 19 tasks at once.
        Can be used for any site type.
        """
        # Create task group
        group = self.task_manager.create_group(
            name=f"QT: {config.sku}",
            color="#FF6B35",  # Orange for quick tasks
        )

        qt_key = f"qt:{config.site_type}:{config.sku}"
        record = SpawnRecord(
            group_id=group.id,
            product_title=f"Quick Task: {config.sku}",
            product_sku=config.sku,
            store_name=config.site_type.upper(),
            product_key=qt_key,
            task_count=config.task_count,
            delete_after_stop=True,
        )

        # Spawn N tasks — create all first, then start concurrently
        for i in range(config.task_count):
            task_config = TaskConfig(
                site_type=config.site_type,
                monitor_input=config.sku,
                sizes=config.size_range,
                mode=TaskMode.FAST,
                profile_id=self._get_profile_id(config.profile_ids, i),
                profile_group_id=config.profile_group_id,
                proxy_group_id=config.proxy_group_id,
                max_retries=2,
            )

            task = self.task_manager.create_task(task_config, group_id=group.id)
            record.task_ids.append(task.id)

        await asyncio.gather(
            *[self.task_manager.start_task(tid) for tid in record.task_ids]
        )

        # Set stop timer
        if config.stop_after_seconds > 0:
            timer = asyncio.create_task(
                self._stop_after_timeout(record, config.stop_after_seconds)
            )
            self._stop_timers[group.id] = timer

        self._spawn_history[group.id] = record

        logger.info(
            "Quick Task spawned",
            sku=config.sku,
            task_count=config.task_count,
            sizes=config.size_range,
        )

        return record

    # ------------------------------------------------------------------
    # Internal: task spawning
    # ------------------------------------------------------------------

    async def _spawn_tasks(
        self,
        product: ProductInfo,
        store: Any,
        product_key: str,
    ) -> Optional[SpawnRecord]:
        """Spawn checkout tasks for a detected product"""

        # Create task group
        group_name = f"{product.title[:30]} [{store.name}]"
        group = self.task_manager.create_group(name=group_name, color="#00D26A")

        record = SpawnRecord(
            group_id=group.id,
            product_title=product.title,
            product_sku=product.sku,
            store_name=store.name,
            product_key=product_key,
            task_count=self.config.task_count,
            delete_after_stop=self.config.delete_after_stop,
        )

        # Spawn N tasks — create all first, then start concurrently
        for i in range(self.config.task_count):
            mode = self._resolve_mode(i)

            task_config = TaskConfig(
                site_type="shopify",
                site_name=store.name,
                site_url=store.url,
                monitor_input=product.sku or product.title,
                product_url=product.url,
                sizes=self.config.target_sizes or product.sizes_available,
                mode=mode,
                profile_id=self._get_profile_id(self.config.profile_ids, i),
                profile_group_id=self.config.profile_group_id,
                proxy_group_id=self.config.proxy_group_id,
                min_price=self.config.min_price,
                max_price=self.config.max_price,
                retry_on_decline=self.config.rotate_profiles,
                max_retries=2,
            )

            task = self.task_manager.create_task(task_config, group_id=group.id)
            record.task_ids.append(task.id)

        await asyncio.gather(
            *[self.task_manager.start_task(tid) for tid in record.task_ids]
        )

        # Set stop timer
        if self.config.stop_after_seconds > 0:
            timer = asyncio.create_task(
                self._stop_after_timeout(record, self.config.stop_after_seconds)
            )
            self._stop_timers[group.id] = timer

        return record

    def _resolve_mode(self, task_index: int) -> TaskMode:
        """Decide checkout mode for this task.

        AUTO strategy: first task uses PRELOAD (if available),
        rest use FAST for redundancy.
        """
        strategy = self.config.spawn_strategy

        if strategy == SpawnStrategy.NORMAL:
            return TaskMode.NORMAL
        elif strategy == SpawnStrategy.FAST:
            return TaskMode.FAST
        elif strategy == SpawnStrategy.PRELOAD:
            return TaskMode.PRELOAD
        else:  # AUTO
            if task_index == 0:
                return TaskMode.PRELOAD
            return TaskMode.FAST

    def _get_profile_id(self, profile_ids: List[str], index: int) -> Optional[str]:
        """Get profile ID for a task, rotating through available profiles"""
        if not profile_ids:
            return None
        return profile_ids[index % len(profile_ids)]

    # ------------------------------------------------------------------
    # Stop-after timeout
    # ------------------------------------------------------------------

    async def _stop_after_timeout(self, record: SpawnRecord, timeout: int):
        """Stop all tasks in a group after a timeout."""
        try:
            await asyncio.sleep(timeout)

            # Check if any task succeeded
            any_success = any(
                (t := self.task_manager.tasks.get(tid)) is not None
                and t.status == TaskStatus.SUCCESS
                for tid in record.task_ids
            )

            if any_success:
                logger.info(
                    "Task group has a success, stopping remaining",
                    group=record.group_id[:8],
                )
            else:
                logger.info(
                    "Task group timed out",
                    group=record.group_id[:8],
                    timeout=timeout,
                )

            # Stop all running tasks in the group
            for task_id in record.task_ids:
                task = self.task_manager.tasks.get(task_id)
                if task and task.is_running:
                    self.task_manager.stop_task(task_id)

            record.stopped = True

            # Delete if configured — use value captured at spawn time
            if record.delete_after_stop:
                await asyncio.sleep(5)  # Brief delay for status to propagate
                for task_id in record.task_ids:
                    self.task_manager.delete_task(task_id)
                logger.debug("Task group cleaned up", group=record.group_id[:8])

        except asyncio.CancelledError:
            pass

    # ------------------------------------------------------------------
    # Stats & Management
    # ------------------------------------------------------------------

    def get_spawn_history(self) -> List[Dict[str, Any]]:
        """Get history of spawned task groups"""
        return [
            {
                "group_id": r.group_id,
                "product": r.product_title[:40],
                "sku": r.product_sku,
                "store": r.store_name,
                "tasks": r.task_count,
                "spawned_at": r.spawned_at.isoformat(),
                "stopped": r.stopped,
            }
            for r in self._spawn_history.values()
        ]

    def get_active_groups(self) -> List[SpawnRecord]:
        """Get currently active (not stopped) task groups"""
        return [r for r in self._spawn_history.values() if not r.stopped]

    async def stop_group(self, group_id: str):
        """Manually stop all tasks in a spawned group"""
        record = self._spawn_history.get(group_id)
        if not record:
            return

        # Cancel the stop timer
        timer = self._stop_timers.pop(group_id, None)
        if timer:
            timer.cancel()

        # Stop tasks
        for task_id in record.task_ids:
            self.task_manager.stop_task(task_id)

        record.stopped = True

    async def cleanup(self):
        """Clean up all timers and pending tasks"""
        for timer in self._stop_timers.values():
            timer.cancel()
        self._stop_timers.clear()
