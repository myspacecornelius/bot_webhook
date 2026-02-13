"""
Unit tests for service layer — WebhookService, TaskService.
"""

import pytest
import hashlib
import hmac
import json
from unittest.mock import AsyncMock

from phantom.services.webhook_service import (
    WebhookService,
    IdempotencyStore,
    SlidingWindowRateLimiter,
)
from phantom.domain.errors import DuplicateError, RateLimitError, UnauthorizedError
from phantom.domain.models import WebhookConfig


# ── IdempotencyStore ──────────────────────────────────────────


class TestIdempotencyStore:
    def test_new_key_accepted(self):
        store = IdempotencyStore()
        assert store.check_and_mark("key-1") is True

    def test_duplicate_key_raises(self):
        store = IdempotencyStore()
        store.check_and_mark("key-1")
        with pytest.raises(DuplicateError):
            store.check_and_mark("key-1")

    def test_different_keys_accepted(self):
        store = IdempotencyStore()
        store.check_and_mark("a")
        store.check_and_mark("b")
        store.check_and_mark("c")
        assert store.size == 3


# ── SlidingWindowRateLimiter ──────────────────────────────────


class TestRateLimiter:
    def test_under_limit(self):
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            limiter.check("source-a")  # Should not raise

    def test_over_limit_raises(self):
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        limiter.check("source-a")
        limiter.check("source-a")
        limiter.check("source-a")
        with pytest.raises(RateLimitError):
            limiter.check("source-a")

    def test_different_sources_independent(self):
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
        limiter.check("a")
        limiter.check("a")
        limiter.check("b")  # b has its own counter
        with pytest.raises(RateLimitError):
            limiter.check("a")  # a is full

    def test_stats(self):
        limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)
        limiter.check("x")
        limiter.check("x")
        limiter.check("y")
        stats = limiter.get_stats()
        assert stats["x"] == 2
        assert stats["y"] == 1


# ── WebhookService ────────────────────────────────────────────


class TestWebhookService:
    @pytest.fixture
    def service(self):
        return WebhookService()

    @pytest.mark.asyncio
    async def test_basic_receive(self, service):
        event = await service.receive(
            source="test",
            payload={"event_type": "order_created", "data": {}},
        )
        assert event.source == "test"
        assert event.event_type == "order_created"

    @pytest.mark.asyncio
    async def test_hmac_verification_pass(self, service):
        secret = "my-secret-key"
        payload = {"event_type": "test", "value": 42}
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        sig = (
            "sha256="
            + hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        )

        service.configure_source("secure", WebhookConfig(hmac_secret=secret))
        event = await service.receive(
            source="secure",
            payload=payload,
            signature=sig,
        )
        assert event.event_type == "test"

    @pytest.mark.asyncio
    async def test_hmac_verification_fail(self, service):
        service.configure_source("secure", WebhookConfig(hmac_secret="real-secret"))
        with pytest.raises(UnauthorizedError):
            await service.receive(
                source="secure",
                payload={"event_type": "test"},
                signature="sha256=bad_signature",
            )

    @pytest.mark.asyncio
    async def test_missing_signature_rejected(self, service):
        service.configure_source("secure", WebhookConfig(hmac_secret="secret"))
        with pytest.raises(UnauthorizedError, match="Missing"):
            await service.receive(source="secure", payload={"event_type": "test"})

    @pytest.mark.asyncio
    async def test_idempotency_dedupe(self, service):
        await service.receive(
            source="test",
            payload={"event_type": "a"},
            idempotency_key="unique-1",
        )
        with pytest.raises(DuplicateError):
            await service.receive(
                source="test",
                payload={"event_type": "a"},
                idempotency_key="unique-1",
            )

    @pytest.mark.asyncio
    async def test_rate_limiting(self, service):
        service._rate_limiter = SlidingWindowRateLimiter(
            max_requests=2, window_seconds=60
        )
        await service.receive(source="s", payload={"event_type": "a"})
        await service.receive(source="s", payload={"event_type": "b"})
        with pytest.raises(RateLimitError):
            await service.receive(source="s", payload={"event_type": "c"})

    @pytest.mark.asyncio
    async def test_handler_fanout(self, service):
        handler = AsyncMock()
        service.register_handler(handler)

        await service.receive(source="t", payload={"event_type": "test"})
        handler.assert_called_once()

    def test_stats(self, service):
        stats = service.get_stats()
        assert "total_received" in stats
        assert "idempotency_keys_cached" in stats
        assert "rate_limit_usage" in stats
