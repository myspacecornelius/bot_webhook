"""
Domain events — typed event definitions for internal communication.
Services emit events; adapters/workers consume them.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


@dataclass
class TaskStarted(DomainEvent):
    task_id: str = ""
    site_type: str = ""
    site_name: str = ""


@dataclass
class TaskCompleted(DomainEvent):
    task_id: str = ""
    success: bool = False
    order_number: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class CheckoutSuccess(DomainEvent):
    task_id: str = ""
    product_name: str = ""
    site_name: str = ""
    total_price: float = 0.0
    order_number: str = ""


@dataclass
class CheckoutFailed(DomainEvent):
    task_id: str = ""
    product_name: str = ""
    site_name: str = ""
    error_message: str = ""


@dataclass
class RestockDetected(DomainEvent):
    product_title: str = ""
    store_name: str = ""
    sizes_available: list = field(default_factory=list)
    price: float = 0.0
    url: str = ""


@dataclass
class MonitorEvent(DomainEvent):
    event_type: str = ""  # "new_product", "restock", "price_change"
    source: str = ""
    store_name: str = ""
    product_data: Dict[str, Any] = field(default_factory=dict)
    priority: str = "medium"


@dataclass
class WebhookReceived(DomainEvent):
    webhook_id: str = ""
    source: str = ""
    event_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
