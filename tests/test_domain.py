"""
Unit tests for domain layer — errors, models, events.
"""

import pytest
from datetime import datetime

from phantom.domain.errors import (
    DuplicateError,
    ForbiddenError,
    NotFoundError,
    PhantomError,
    RateLimitError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from phantom.domain.models import (
    TaskCreate,
    QuickTaskCreate,
    ProfileCreate,
    WebhookEvent,
    WebhookConfig,
)
from phantom.domain.events import (
    DomainEvent,
    TaskStarted,
    CheckoutSuccess,
    WebhookReceived,
)


# ── Error Hierarchy ───────────────────────────────────────────


class TestErrors:
    def test_base_error(self):
        err = PhantomError("test error")
        assert err.message == "test error"
        assert str(err) == "test error"

    def test_not_found_with_id(self):
        err = NotFoundError("Task", "abc-123")
        assert "Task" in err.message
        assert "abc-123" in err.message
        assert err.resource == "Task"
        assert err.identifier == "abc-123"

    def test_not_found_without_id(self):
        err = NotFoundError("Profile")
        assert err.message == "Profile not found"

    def test_validation_error(self):
        err = ValidationError("Bad email", field="email")
        assert err.field == "email"
        assert err.message == "Bad email"

    def test_rate_limit_retry_after(self):
        err = RateLimitError(retry_after=30)
        assert err.retry_after == 30

    def test_duplicate_error(self):
        err = DuplicateError("webhook", "key-abc")
        assert "webhook" in err.message
        assert "key-abc" in err.message
        assert err.key == "key-abc"

    def test_service_unavailable(self):
        err = ServiceUnavailableError("Intelligence module")
        assert "Intelligence module" in err.message

    def test_error_inheritance(self):
        """All domain errors inherit from PhantomError."""
        for cls in [
            NotFoundError,
            ValidationError,
            UnauthorizedError,
            ForbiddenError,
            RateLimitError,
            DuplicateError,
            ServiceUnavailableError,
        ]:
            assert issubclass(cls, PhantomError)


# ── Models (Pydantic) ─────────────────────────────────────────


class TestModels:
    def test_task_create_defaults(self):
        task = TaskCreate(
            site_name="Kith",
            site_url="https://kith.com",
            monitor_input="Yeezy",
        )
        assert task.site_type == "shopify"
        assert task.mode == "normal"
        assert task.sizes == []
        assert task.monitor_delay == 3000

    def test_quick_task_defaults(self):
        qt = QuickTaskCreate(url="https://kith.com/products/yeezy-350")
        assert qt.quantity == 1
        assert qt.mode == "fast"
        assert qt.auto_start is True

    def test_webhook_config(self):
        cfg = WebhookConfig(
            hmac_secret="secret123",
            rate_limit_per_minute=100,
        )
        assert cfg.hmac_secret == "secret123"
        assert cfg.rate_limit_per_minute == 100

    def test_webhook_event_model(self):
        evt = WebhookEvent(
            source="shopify",
            event_type="orders/create",
            payload={"order_id": 123},
        )
        assert evt.source == "shopify"
        assert evt.id is None  # optional

    def test_profile_create_required_fields(self):
        with pytest.raises(Exception):
            # Missing required fields should fail
            ProfileCreate(name="Test")  # type: ignore


# ── Events (Dataclasses) ──────────────────────────────────────


class TestEvents:
    def test_domain_event_timestamp(self):
        evt = DomainEvent()
        assert isinstance(evt.timestamp, datetime)
        assert evt.correlation_id is None

    def test_task_started_event(self):
        evt = TaskStarted(
            task_id="t-1",
            site_type="shopify",
            site_name="Kith",
            correlation_id="corr-abc",
        )
        assert evt.task_id == "t-1"
        assert evt.correlation_id == "corr-abc"

    def test_checkout_success_event(self):
        evt = CheckoutSuccess(
            task_id="t-2",
            product_name="Yeezy 350",
            site_name="Kith",
            total_price=220.0,
            order_number="ORDER-999",
        )
        assert evt.order_number == "ORDER-999"
        assert evt.total_price == 220.0

    def test_webhook_received_event(self):
        evt = WebhookReceived(
            webhook_id="wh-1",
            source="shopify",
            event_type="products/create",
            payload={"title": "New Product"},
        )
        assert evt.payload["title"] == "New Product"
