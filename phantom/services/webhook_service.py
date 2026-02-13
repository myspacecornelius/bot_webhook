"""
Webhook service — HMAC verification, idempotency, rate limiting, and event pipeline.

Receives raw webhook payloads from the API layer, verifies authenticity,
deduplicates, rate-limits per source, normalizes, and fans out to handlers.
"""

import hashlib
import hmac
import time
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, List, Optional

import structlog

from ..domain.errors import DuplicateError, RateLimitError, UnauthorizedError
from ..domain.events import WebhookReceived
from ..domain.models import WebhookConfig

logger = structlog.get_logger()

# Type alias for async webhook handlers
WebhookHandler = Callable[[WebhookReceived], Coroutine[Any, Any, None]]


class IdempotencyStore:
    """In-memory idempotency key store with TTL expiration."""

    def __init__(self, ttl_seconds: int = 3600):
        self._seen: Dict[str, float] = {}  # key → timestamp
        self._ttl = ttl_seconds

    def check_and_mark(self, key: str) -> bool:
        """Return True if key is NEW (not seen). Raises DuplicateError if seen."""
        self._evict_expired()

        if key in self._seen:
            raise DuplicateError("webhook", key)

        self._seen[key] = time.time()
        return True

    def _evict_expired(self) -> None:
        cutoff = time.time() - self._ttl
        self._seen = {k: v for k, v in self._seen.items() if v > cutoff}

    @property
    def size(self) -> int:
        return len(self._seen)


class SlidingWindowRateLimiter:
    """Per-source sliding window rate limiter."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._buckets: Dict[str, List[float]] = defaultdict(list)

    def check(self, source: str) -> None:
        """Raise RateLimitError if source exceeds limit."""
        now = time.time()
        cutoff = now - self._window

        # Trim expired entries
        self._buckets[source] = [t for t in self._buckets[source] if t > cutoff]

        if len(self._buckets[source]) >= self._max:
            retry_after = int(self._buckets[source][0] - cutoff) + 1
            raise RateLimitError(
                f"Source '{source}' exceeded {self._max} requests per {self._window}s",
                retry_after=max(retry_after, 1),
            )

        self._buckets[source].append(now)

    def get_stats(self) -> Dict[str, int]:
        now = time.time()
        cutoff = now - self._window
        return {
            source: len([t for t in times if t > cutoff])
            for source, times in self._buckets.items()
        }


class WebhookService:
    """Webhook ingestion pipeline: verify → dedupe → rate-limit → fan-out."""

    def __init__(self):
        self._configs: Dict[str, WebhookConfig] = {}
        self._handlers: List[WebhookHandler] = []
        self._idempotency = IdempotencyStore(ttl_seconds=3600)
        self._rate_limiter = SlidingWindowRateLimiter(
            max_requests=60, window_seconds=60
        )
        self._event_log: List[WebhookReceived] = []
        self._max_log_size = 500

    # ── Configuration ─────────────────────────────────────────

    def configure_source(self, source: str, config: WebhookConfig) -> None:
        """Register HMAC secret and rate limits for a webhook source."""
        self._configs[source] = config
        if config.rate_limit_per_minute:
            self._rate_limiter._max = config.rate_limit_per_minute
        logger.info("webhook_source_configured", source=source)

    def register_handler(self, handler: WebhookHandler) -> None:
        """Register a handler that receives all verified webhook events."""
        self._handlers.append(handler)

    # ── Pipeline ──────────────────────────────────────────────

    async def receive(
        self,
        source: str,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> WebhookReceived:
        """
        Full pipeline: verify → dedupe → rate-limit → normalize → fan-out.

        Raises:
            UnauthorizedError: Invalid HMAC signature
            DuplicateError: Duplicate idempotency key
            RateLimitError: Source exceeded rate limit
        """
        config = self._configs.get(source)

        # 1. HMAC verification
        if config and config.hmac_secret:
            if not signature:
                raise UnauthorizedError("Missing webhook signature")
            if not self.verify_signature(payload, signature, config.hmac_secret):
                raise UnauthorizedError("Invalid webhook signature")

        # 2. Rate limiting
        self._rate_limiter.check(source)

        # 3. Idempotency check
        if idempotency_key:
            self._idempotency.check_and_mark(idempotency_key)

        # 4. Normalize into domain event
        event = WebhookReceived(
            webhook_id=idempotency_key or "",
            source=source,
            event_type=payload.get("event_type", payload.get("type", "unknown")),
            payload=payload,
        )

        # 5. Persist to in-memory log
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size :]

        # 6. Fan-out to registered handlers
        for handler in self._handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    "webhook_handler_error",
                    source=source,
                    handler=handler.__name__,
                    error=str(e),
                )

        logger.info(
            "webhook_processed",
            source=source,
            event_type=event.event_type,
            idempotency_key=idempotency_key,
        )

        return event

    # ── HMAC ──────────────────────────────────────────────────

    @staticmethod
    def verify_signature(
        payload: Dict[str, Any],
        signature: str,
        secret: str,
    ) -> bool:
        """Verify HMAC-SHA256 signature of a webhook payload."""
        import json

        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)

    # ── Queries ───────────────────────────────────────────────

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        events = self._event_log[-limit:]
        return [
            {
                "webhook_id": e.webhook_id,
                "source": e.source,
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in reversed(events)
        ]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_received": len(self._event_log),
            "idempotency_keys_cached": self._idempotency.size,
            "rate_limit_usage": self._rate_limiter.get_stats(),
            "configured_sources": list(self._configs.keys()),
        }


webhook_service = WebhookService()
