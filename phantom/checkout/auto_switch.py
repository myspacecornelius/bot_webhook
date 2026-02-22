"""
Auto-Switch Mode — Dynamic Task Mode Selection

Reverse-engineered from Valor AIO's autoSwitchMode feature:
  - Monitors checkout conditions in real-time
  - Dynamically switches between Normal → Fast → Preload
  - Reacts to queue detection, checkpoint, rate limiting
  - Falls back gracefully when a mode fails

Key Valor settings replicated:
  autoSwitchMode: true
  checkpointAutoRunLink: true

Decision tree:
  1. Start in configured mode (user's choice)
  2. If Preload session available → use PRELOAD
  3. If product is high-demand (low stock, many watchers) → FAST
  4. If queue detected → switch to NORMAL (more patient)
  5. If captcha required → switch to SAFE
  6. If declined → rotate profile and retry with FAST
"""

import time
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum
import structlog

from ..core.task import TaskMode

logger = structlog.get_logger()


class SwitchReason(Enum):
    """Why a mode switch was triggered"""

    INITIAL = "initial"
    QUEUE_DETECTED = "queue_detected"
    CHECKPOINT_DETECTED = "checkpoint_detected"
    RATE_LIMITED = "rate_limited"
    PRELOAD_AVAILABLE = "preload_available"
    PRELOAD_EXPIRED = "preload_expired"
    HIGH_DEMAND = "high_demand"
    LOW_STOCK = "low_stock"
    CAPTCHA_REQUIRED = "captcha_required"
    DECLINED = "declined"
    TIMEOUT = "timeout"
    MANUAL = "manual"


@dataclass
class SwitchEvent:
    """Record of a mode switch"""

    from_mode: TaskMode
    to_mode: TaskMode
    reason: SwitchReason
    timestamp: float = field(default_factory=time.time)
    details: str = ""


@dataclass
class AutoSwitchConfig:
    """Configuration for auto-switch behavior"""

    enabled: bool = True

    # Mode priorities (higher = preferred)
    mode_priority: Dict[str, int] = field(
        default_factory=lambda: {
            "preload": 4,
            "fast": 3,
            "normal": 2,
            "safe": 1,
        }
    )

    # Conditions
    switch_on_queue: bool = True  # Switch when queue detected
    switch_on_checkpoint: bool = True  # Switch when checkpoint detected
    switch_on_rate_limit: bool = True  # Switch when rate limited
    switch_on_captcha: bool = True  # Switch to SAFE on captcha
    switch_on_decline: bool = True  # Retry on decline

    # Limits
    max_switches_per_task: int = 5  # Don't switch forever
    cooldown_seconds: float = 3.0  # Min time between switches

    # Preload preferences
    prefer_preload: bool = True  # Use preload when available
    fallback_on_preload_expire: TaskMode = TaskMode.FAST


class AutoSwitchMode:
    """
    Dynamically switches task checkout mode based on real-time conditions.

    Usage:
        switcher = AutoSwitchMode(config)

        # Check if mode should change
        new_mode = switcher.evaluate(
            current_mode=TaskMode.NORMAL,
            task_id="abc",
            signals={"queue_detected": True},
        )

        # Log decision
        if new_mode != current_mode:
            switcher.record_switch(task_id, current, new_mode, reason)
    """

    # Mode transition table — what to switch TO given a signal
    TRANSITION_TABLE: Dict[str, TaskMode] = {
        "queue_detected": TaskMode.NORMAL,  # Queues need patience
        "checkpoint_detected": TaskMode.SAFE,  # Checkpoints need care
        "rate_limited": TaskMode.SAFE,  # Slow down
        "captcha_required": TaskMode.SAFE,  # Need captcha handling
        "high_demand": TaskMode.FAST,  # Speed matters
        "low_stock": TaskMode.FAST,  # Race to checkout
        "preload_available": TaskMode.PRELOAD,  # Best option
        "preload_expired": TaskMode.FAST,  # Fallback
        "declined": TaskMode.FAST,  # Try again quickly
        "timeout": TaskMode.FAST,  # Try faster
    }

    # Signals that are safety downgrades — always override current mode
    SAFETY_SIGNALS: frozenset = frozenset(
        {
            "queue_detected",
            "checkpoint_detected",
            "rate_limited",
            "captcha_required",
        }
    )

    # Signal name → SwitchReason enum mapping (avoids case mismatch)
    SIGNAL_TO_REASON: Dict[str, SwitchReason] = {
        "queue_detected": SwitchReason.QUEUE_DETECTED,
        "checkpoint_detected": SwitchReason.CHECKPOINT_DETECTED,
        "rate_limited": SwitchReason.RATE_LIMITED,
        "captcha_required": SwitchReason.CAPTCHA_REQUIRED,
        "high_demand": SwitchReason.HIGH_DEMAND,
        "low_stock": SwitchReason.LOW_STOCK,
        "preload_available": SwitchReason.PRELOAD_AVAILABLE,
        "preload_expired": SwitchReason.PRELOAD_EXPIRED,
        "declined": SwitchReason.DECLINED,
        "timeout": SwitchReason.TIMEOUT,
    }

    def __init__(self, config: Optional[AutoSwitchConfig] = None):
        self.config = config or AutoSwitchConfig()
        self._switch_history: Dict[str, List[SwitchEvent]] = {}
        self._last_switch_time: Dict[str, float] = {}

    def evaluate(
        self,
        current_mode: TaskMode,
        task_id: str,
        signals: Dict[str, bool],
    ) -> TaskMode:
        """Evaluate whether the task mode should change.

        Args:
            current_mode: Current task mode
            task_id: Task identifier
            signals: Dict of condition → bool (e.g. {"queue_detected": True})

        Returns:
            The recommended mode (same as current if no switch needed)
        """
        if not self.config.enabled:
            return current_mode

        # Check switch limits
        task_switches = len(self._switch_history.get(task_id, []))
        if task_switches >= self.config.max_switches_per_task:
            return current_mode

        # Check cooldown
        last_time = self._last_switch_time.get(task_id, 0)
        if time.time() - last_time < self.config.cooldown_seconds:
            return current_mode

        # Separate safety downgrades from upgrade signals so they are
        # evaluated independently — safety always wins, upgrades only win
        # if they are higher priority than the current mode.
        safety_mode: Optional[TaskMode] = None
        safety_reason: Optional[str] = None
        upgrade_mode: Optional[TaskMode] = None
        upgrade_reason: Optional[str] = None
        upgrade_priority: int = self.config.mode_priority.get(current_mode.value, 0)

        for signal, is_active in signals.items():
            if not is_active:
                continue

            # Check if signal should trigger a switch
            if signal == "queue_detected" and not self.config.switch_on_queue:
                continue
            if signal == "checkpoint_detected" and not self.config.switch_on_checkpoint:
                continue
            if signal == "rate_limited" and not self.config.switch_on_rate_limit:
                continue
            if signal == "captcha_required" and not self.config.switch_on_captcha:
                continue
            if signal == "declined" and not self.config.switch_on_decline:
                continue

            suggested = self.TRANSITION_TABLE.get(signal)
            if not suggested:
                continue

            if signal in self.SAFETY_SIGNALS:
                # Safety downgrade: pick the most conservative (lowest priority)
                suggested_priority = self.config.mode_priority.get(suggested.value, 0)
                current_safety_priority = (
                    self.config.mode_priority.get(safety_mode.value, 999)
                    if safety_mode
                    else 999
                )
                if suggested_priority < current_safety_priority:
                    safety_mode = suggested
                    safety_reason = signal
            else:
                # Upgrade signal: only switch if strictly higher priority
                suggested_priority = self.config.mode_priority.get(suggested.value, 0)
                if suggested_priority > upgrade_priority:
                    upgrade_mode = suggested
                    upgrade_reason = signal
                    upgrade_priority = suggested_priority

        # Safety downgrades take precedence over upgrades
        best_mode = safety_mode or upgrade_mode or current_mode
        best_reason = safety_reason or upgrade_reason

        if best_mode != current_mode and best_reason:
            reason_enum = self.SIGNAL_TO_REASON.get(best_reason, SwitchReason.MANUAL)
            self.record_switch(task_id, current_mode, best_mode, reason_enum)

            logger.info(
                "Auto-switch mode",
                task_id=task_id[:8],
                from_mode=current_mode.value,
                to_mode=best_mode.value,
                reason=best_reason,
            )

        return best_mode

    def record_switch(
        self,
        task_id: str,
        from_mode: TaskMode,
        to_mode: TaskMode,
        reason: SwitchReason,
        details: str = "",
    ):
        """Record a mode switch for tracking"""
        if task_id not in self._switch_history:
            self._switch_history[task_id] = []

        event = SwitchEvent(
            from_mode=from_mode,
            to_mode=to_mode,
            reason=reason,
            details=details,
        )
        self._switch_history[task_id].append(event)
        self._last_switch_time[task_id] = time.time()

    def get_history(self, task_id: str) -> List[Dict]:
        """Get switch history for a task"""
        events = self._switch_history.get(task_id, [])
        return [
            {
                "from": e.from_mode.value,
                "to": e.to_mode.value,
                "reason": e.reason.value,
                "time": e.timestamp,
                "details": e.details,
            }
            for e in events
        ]

    def get_switch_count(self, task_id: str) -> int:
        """Get number of switches for a task"""
        return len(self._switch_history.get(task_id, []))

    def reset(self, task_id: Optional[str] = None):
        """Reset switch history"""
        if task_id:
            self._switch_history.pop(task_id, None)
            self._last_switch_time.pop(task_id, None)
        else:
            self._switch_history.clear()
            self._last_switch_time.clear()


# Module-level singleton
auto_switch = AutoSwitchMode()
