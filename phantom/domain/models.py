"""
Domain models — pure Pydantic schemas for API input/output.
These are the shared contract between api/ and services/.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


# ─── Enums ────────────────────────────────────────────────────


class TaskMode(str, Enum):
    NORMAL = "normal"
    FAST = "fast"
    SAFE = "safe"


class SiteType(str, Enum):
    SHOPIFY = "shopify"
    FOOTSITES = "footsites"
    NIKE = "nike"


class EventPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ─── Profile ──────────────────────────────────────────────────


class ProfileCreate(BaseModel):
    name: str
    email: str
    phone: str = ""
    shipping_first_name: str
    shipping_last_name: str
    shipping_address1: str
    shipping_address2: str = ""
    shipping_city: str
    shipping_state: str
    shipping_zip: str
    shipping_country: str = "United States"
    billing_same_as_shipping: bool = True
    card_holder: str
    card_number: str
    card_expiry: str
    card_cvv: str


# ─── Task ─────────────────────────────────────────────────────


class TaskCreate(BaseModel):
    site_type: str = "shopify"
    site_name: str
    site_url: str
    monitor_input: str
    sizes: List[str] = []
    mode: str = "normal"
    profile_id: Optional[str] = None
    proxy_group_id: Optional[str] = None
    monitor_delay: int = 3000
    retry_delay: int = 2000


class QuickTaskCreate(BaseModel):
    url: str
    sizes: Optional[List[str]] = None
    quantity: int = 1
    mode: str = "fast"
    profile_id: Optional[str] = None
    proxy_group_id: Optional[str] = None
    auto_start: bool = True


class QuickTaskBatch(BaseModel):
    urls: List[str]
    sizes: Optional[List[str]] = None
    mode: str = "fast"
    auto_start: bool = True


# ─── Proxy ────────────────────────────────────────────────────


class ProxyGroupCreate(BaseModel):
    name: str
    proxies: str  # Newline-separated proxy strings


class ProxyTest(BaseModel):
    group_id: Optional[str] = None


# ─── Monitor ──────────────────────────────────────────────────


class ShopifySetup(BaseModel):
    target_sizes: Optional[List[str]] = None
    use_defaults: bool = True


class ShopifyStoreAdd(BaseModel):
    name: str
    url: str
    delay_ms: int = 3000
    target_sizes: Optional[List[str]] = None


class ShopifyStoreUpdate(BaseModel):
    enabled: Optional[bool] = None
    delay_ms: Optional[int] = None
    target_sizes: Optional[List[str]] = None


class FootsiteSetup(BaseModel):
    sites: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    target_sizes: Optional[List[str]] = None
    delay_ms: int = 5000


class AutoTaskConfig(BaseModel):
    enabled: bool = True
    min_confidence: float = 0.7
    min_priority: str = "medium"


# ─── Auth ─────────────────────────────────────────────────────


class LicenseValidation(BaseModel):
    license_key: str


class CheckoutRequest(BaseModel):
    tier: str
    email: str


# ─── Webhook (Phase 4) ───────────────────────────────────────


class WebhookEvent(BaseModel):
    """Inbound webhook event payload."""

    id: Optional[str] = None
    source: str
    event_type: str
    payload: dict
    received_at: Optional[datetime] = None


class WebhookConfig(BaseModel):
    """Webhook endpoint configuration."""

    hmac_secret: Optional[str] = None
    allowed_ips: List[str] = []
    rate_limit_per_minute: int = 60
