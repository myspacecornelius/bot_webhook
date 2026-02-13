"""
Checkout Session Factory
Creates HTTP sessions with TLS fingerprint evasion via curl-cffi.
Falls back to plain httpx if curl-cffi is unavailable.
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import httpx
import structlog

from ..core.proxy import Proxy
from ..evasion.fingerprint import FingerprintManager, BrowserFingerprint
from ..evasion.tls import TLSManager

logger = structlog.get_logger()

# Detect curl-cffi availability once at import time
try:
    from curl_cffi.requests import AsyncSession as CurlAsyncSession

    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    CurlAsyncSession = None  # type: ignore[misc,assignment]


class CheckoutSession:
    """
    Unified session factory for all checkout modules.

    When curl-cffi is available the session impersonates a real browser at the
    TLS layer (JA3/JA4 fingerprint, H2 settings, cipher order).  The
    ``FingerprintManager`` adds realistic higher-level headers (User-Agent,
    Sec-CH-UA, Accept-Language, etc.).

    If curl-cffi is *not* installed the factory falls back to a standard
    ``httpx.AsyncClient`` — still usable, but without TLS-level evasion.
    """

    def __init__(
        self,
        browser_type: str = "chrome",
        timeout: float = 30.0,
    ) -> None:
        self.browser_type = browser_type
        self.timeout = timeout
        self.tls_manager = TLSManager()
        self.fingerprint_manager = FingerprintManager()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create(
        self,
        *,
        proxy: Optional[Proxy] = None,
        seed: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Return an async HTTP client with TLS evasion.

        Parameters
        ----------
        proxy:
            Optional proxy to route traffic through.
        seed:
            Deterministic seed for reproducible fingerprints (e.g. task id).
        extra_headers:
            Additional headers merged on top of the generated fingerprint.

        Returns
        -------
        An ``AsyncSession`` (curl-cffi) or ``httpx.AsyncClient``.
        Both expose ``.get`` / ``.post`` / ``.aclose``.
        """
        fingerprint = self.fingerprint_manager.generate(
            browser_type=self.browser_type,
            seed=seed,
        )
        headers = self._build_headers(fingerprint, extra_headers)

        if HAS_CURL_CFFI:
            return self._create_curl_session(proxy, headers)
        return self._create_httpx_session(proxy, headers)

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------

    def _build_headers(
        self,
        fp: BrowserFingerprint,
        extra: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "User-Agent": fp.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": ",".join(fp.languages) + ";q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

        # Chromium-specific Sec-CH-UA headers
        impersonation = self.tls_manager.get_impersonation(self.browser_type)
        sec_headers = self.tls_manager.get_sec_ch_ua(impersonation)
        if sec_headers:
            headers.update(sec_headers)

        if extra:
            headers.update(extra)

        return headers

    def _create_curl_session(
        self,
        proxy: Optional[Proxy],
        headers: Dict[str, str],
    ) -> CurlAsyncSession:  # type: ignore[return-type]
        impersonation = self.tls_manager.get_impersonation(self.browser_type)

        kwargs: Dict[str, Any] = {
            "impersonate": impersonation.value,
            "timeout": self.timeout,
            "headers": headers,
            "allow_redirects": True,
        }

        if proxy:
            kwargs["proxies"] = {"https": proxy.url, "http": proxy.url}

        logger.debug(
            "curl-cffi session created",
            impersonation=impersonation.value,
            proxy=proxy.display if proxy else None,
        )

        return CurlAsyncSession(**kwargs)  # type: ignore[return-value]

    def _create_httpx_session(
        self,
        proxy: Optional[Proxy],
        headers: Dict[str, str],
    ) -> httpx.AsyncClient:
        proxy_url = proxy.url if proxy else None

        logger.warning(
            "curl-cffi unavailable — using plain httpx (no TLS evasion)",
            proxy=proxy.display if proxy else None,
        )

        return httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            proxy=proxy_url,
            headers=headers,
        )


# Module-level convenience instance
checkout_session_factory = CheckoutSession()
