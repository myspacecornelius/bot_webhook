"""
Local Captcha Harvester
Uses browser windows for manual captcha solving (one-click tokens)
"""

import asyncio
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import structlog

from .solver import CaptchaResult

logger = structlog.get_logger()


@dataclass
class HarvestedToken:
    """A harvested captcha token"""
    token: str
    site_key: str
    domain: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_valid(self) -> bool:
        """Check if token is still valid (< 110 seconds old)"""
        return (datetime.now() - self.timestamp).total_seconds() < 110


class CaptchaHarvester:
    """
    Local captcha harvester using browser automation
    
    Features:
    - Pre-solves captchas for fast checkout
    - Maintains token pool per site
    - Automatic token refresh
    - One-click solving with Gmail sessions
    """
    
    def __init__(self, max_tokens_per_site: int = 5):
        self.max_tokens = max_tokens_per_site
        self._tokens: Dict[str, deque] = {}  # domain -> deque of tokens
        self._browsers: List = []
        self._running = False
        self._harvest_task: Optional[asyncio.Task] = None
        logger.info("CaptchaHarvester initialized")
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    def _get_token_key(self, domain: str, site_key: str) -> str:
        """Get key for token storage"""
        return f"{domain}:{site_key}"
    
    async def start(self, sites: List[Dict[str, str]]):
        """
        Start harvesting for specified sites
        
        sites: List of {"url": "...", "site_key": "..."}
        """
        if self._running:
            return
        
        self._running = True
        self._harvest_task = asyncio.create_task(self._harvest_loop(sites))
        logger.info("Harvester started", sites=len(sites))
    
    async def stop(self):
        """Stop harvesting"""
        self._running = False
        
        if self._harvest_task:
            self._harvest_task.cancel()
            try:
                await self._harvest_task
            except asyncio.CancelledError:
                pass
        
        # Close browsers
        for browser in self._browsers:
            try:
                await browser.close()
            except Exception:
                pass
        
        self._browsers.clear()
        logger.info("Harvester stopped")
    
    async def _harvest_loop(self, sites: List[Dict[str, str]]):
        """Main harvesting loop"""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=False)
                self._browsers.append(browser)
                
                # Create context with session
                context = await browser.new_context()
                
                while self._running:
                    for site in sites:
                        url = site.get("url", "")
                        site_key = site.get("site_key", "")
                        
                        if not url or not site_key:
                            continue
                        
                        domain = self._get_domain(url)
                        key = self._get_token_key(domain, site_key)
                        
                        # Check if we need more tokens
                        current_count = self._count_valid_tokens(key)
                        if current_count >= self.max_tokens:
                            continue
                        
                        # Harvest token
                        try:
                            token = await self._harvest_single(context, url, site_key)
                            if token:
                                self._store_token(domain, site_key, token)
                                logger.debug("Token harvested", domain=domain)
                        except Exception as e:
                            logger.warning("Harvest failed", domain=domain, error=str(e))
                    
                    # Clean expired tokens
                    self._clean_expired()
                    
                    await asyncio.sleep(5)  # Rate limit
                    
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install")
        except Exception as e:
            logger.error("Harvester error", error=str(e))
    
    async def _harvest_single(self, context, url: str, site_key: str) -> Optional[str]:
        """Harvest a single captcha token"""
        page = await context.new_page()
        
        try:
            # Create a minimal page with captcha
            captcha_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://www.google.com/recaptcha/api.js" async defer></script>
            </head>
            <body>
                <div class="g-recaptcha" data-sitekey="{site_key}" data-callback="onSolved"></div>
                <script>
                    function onSolved(token) {{
                        window.captchaToken = token;
                    }}
                </script>
            </body>
            </html>
            """
            
            await page.set_content(captcha_html)
            await page.wait_for_selector('.g-recaptcha', timeout=5000)
            
            # Wait for user to solve (or auto-solve if one-click)
            for _ in range(60):  # Max 60 seconds
                token = await page.evaluate("window.captchaToken")
                if token:
                    return token
                await asyncio.sleep(1)
            
            return None
            
        finally:
            await page.close()
    
    def _store_token(self, domain: str, site_key: str, token: str):
        """Store a harvested token"""
        key = self._get_token_key(domain, site_key)
        
        if key not in self._tokens:
            self._tokens[key] = deque(maxlen=self.max_tokens)
        
        self._tokens[key].append(HarvestedToken(
            token=token,
            site_key=site_key,
            domain=domain
        ))
    
    def _count_valid_tokens(self, key: str) -> int:
        """Count valid tokens for a key"""
        if key not in self._tokens:
            return 0
        return sum(1 for t in self._tokens[key] if t.is_valid)
    
    def _clean_expired(self):
        """Remove expired tokens"""
        for key in list(self._tokens.keys()):
            self._tokens[key] = deque(
                [t for t in self._tokens[key] if t.is_valid],
                maxlen=self.max_tokens
            )
    
    async def get_token(self, url: str, site_key: str) -> CaptchaResult:
        """Get a harvested token for a site"""
        domain = self._get_domain(url)
        key = self._get_token_key(domain, site_key)
        
        if key not in self._tokens:
            return CaptchaResult(success=False, error="No tokens available")
        
        # Find valid token
        while self._tokens[key]:
            token = self._tokens[key].popleft()
            if token.is_valid:
                return CaptchaResult(
                    success=True,
                    token=token.token,
                    solve_time=0.0,
                    cost=0.0,
                    provider="harvester"
                )
        
        return CaptchaResult(success=False, error="No valid tokens")
    
    def get_stats(self) -> Dict[str, int]:
        """Get token statistics"""
        stats = {}
        for key, tokens in self._tokens.items():
            valid = sum(1 for t in tokens if t.is_valid)
            stats[key] = valid
        return stats
    
    def add_manual_token(self, domain: str, site_key: str, token: str):
        """Manually add a token (e.g., from external source)"""
        self._store_token(domain, site_key, token)
        logger.debug("Manual token added", domain=domain)
