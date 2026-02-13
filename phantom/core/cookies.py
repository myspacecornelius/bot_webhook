"""
Cookie & Session Persistence

Manages cookie jars per task/site so that sessions can be reused across
retries and checkpoint resolutions.  This is critical for Shopify stores
that issue checkpoint cookies — if you lose the cookie jar, the checkpoint
must be re-solved from scratch.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Optional, Any
from http.cookies import SimpleCookie
import structlog

logger = structlog.get_logger()


class CookieStore:
    """Per-task cookie persistence.

    Usage::

        store = CookieStore()

        # Save after a request
        store.save("task-123", "kith.com", {"_shopify_y": "abc", "cart": "xyz"})

        # Load on retry
        cookies = store.load("task-123", "kith.com")
        session.cookies.update(cookies)

        # Clear after checkout completes
        store.clear("task-123")
    """

    def __init__(self, persist_dir: Optional[str] = None):
        # In-memory store  { task_id → { domain → { name: value } } }
        self._jars: Dict[str, Dict[str, Dict[str, str]]] = {}

        # Optional disk persistence for crash recovery
        self._persist_dir = Path(persist_dir) if persist_dir else None
        if self._persist_dir:
            self._persist_dir.mkdir(parents=True, exist_ok=True)

        logger.debug("CookieStore initialized", persist=bool(persist_dir))

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def save(
        self,
        task_id: str,
        domain: str,
        cookies: Dict[str, str],
        *,
        merge: bool = True,
    ) -> None:
        """Store cookies for a task + domain pair.

        Parameters
        ----------
        merge:
            If True (default), new cookies are merged with existing ones.
            If False, the existing cookies for this domain are replaced.
        """
        if task_id not in self._jars:
            self._jars[task_id] = {}

        if merge and domain in self._jars[task_id]:
            self._jars[task_id][domain].update(cookies)
        else:
            self._jars[task_id][domain] = dict(cookies)

        if self._persist_dir:
            self._write_disk(task_id)

    def load(
        self,
        task_id: str,
        domain: Optional[str] = None,
    ) -> Dict[str, str]:
        """Load cookies for a task, optionally filtered by domain."""
        task_jars = self._jars.get(task_id, {})

        if domain:
            return dict(task_jars.get(domain, {}))

        # Merge all domains
        merged: Dict[str, str] = {}
        for domain_cookies in task_jars.values():
            merged.update(domain_cookies)
        return merged

    def clear(self, task_id: str) -> None:
        """Remove all cookies for a task."""
        self._jars.pop(task_id, None)
        if self._persist_dir:
            path = self._persist_dir / f"{task_id}.json"
            path.unlink(missing_ok=True)

    def clear_domain(self, task_id: str, domain: str) -> None:
        """Remove cookies for a specific domain within a task."""
        if task_id in self._jars:
            self._jars[task_id].pop(domain, None)

    # ------------------------------------------------------------------
    # Helpers for extracting cookies from responses
    # ------------------------------------------------------------------

    @staticmethod
    def extract_from_headers(
        set_cookie_headers: list[str],
    ) -> Dict[str, str]:
        """Parse Set-Cookie headers into a simple {name: value} dict."""
        cookies: Dict[str, str] = {}
        for header in set_cookie_headers:
            sc = SimpleCookie()
            sc.load(header)
            for morsel_name, morsel in sc.items():
                cookies[morsel_name] = morsel.value
        return cookies

    @staticmethod
    def extract_from_response(response: Any) -> Dict[str, str]:
        """Extract cookies from an httpx / curl-cffi response object."""
        cookies: Dict[str, str] = {}
        try:
            # httpx.Response
            if hasattr(response, "cookies"):
                for name, value in response.cookies.items():
                    cookies[name] = value
            # curl-cffi response (cookies as dict)
            elif hasattr(response, "cookies") and isinstance(response.cookies, dict):
                cookies.update(response.cookies)
        except Exception:
            pass
        return cookies

    # ------------------------------------------------------------------
    # Disk persistence  (optional crash recovery)
    # ------------------------------------------------------------------

    def _write_disk(self, task_id: str) -> None:
        if not self._persist_dir:
            return
        try:
            path = self._persist_dir / f"{task_id}.json"
            data = {
                "task_id": task_id,
                "saved_at": time.time(),
                "domains": self._jars.get(task_id, {}),
            }
            path.write_text(json.dumps(data))
        except Exception as e:
            logger.warning("Cookie persist failed", error=str(e))

    def load_from_disk(self, task_id: str) -> bool:
        """Restore cookies from disk (e.g. after crash restart)."""
        if not self._persist_dir:
            return False
        path = self._persist_dir / f"{task_id}.json"
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text())
            self._jars[task_id] = data.get("domains", {})
            return True
        except Exception as e:
            logger.warning("Cookie load failed", error=str(e))
            return False

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        total_cookies = sum(
            len(cookies)
            for domains in self._jars.values()
            for cookies in domains.values()
        )
        return {
            "active_tasks": len(self._jars),
            "total_cookies": total_cookies,
        }


# Module-level singleton
cookie_store = CookieStore()
