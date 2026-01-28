"""
Multi-Provider Captcha Solver
Integrates with 2Captcha, CapMonster, Anti-Captcha, and local harvesters
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import httpx
import structlog

logger = structlog.get_logger()


class CaptchaType(Enum):
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    FUNCAPTCHA = "funcaptcha"
    IMAGE = "image"


class SolverProvider(Enum):
    TWO_CAPTCHA = "2captcha"
    ANTI_CAPTCHA = "anticaptcha"
    CAPMONSTER = "capmonster"
    HARVESTER = "harvester"


@dataclass
class CaptchaTask:
    """A captcha solving task"""
    captcha_type: CaptchaType
    site_key: str
    page_url: str
    action: Optional[str] = None  # For reCAPTCHA v3
    min_score: float = 0.3  # For reCAPTCHA v3
    invisible: bool = False
    data_s: Optional[str] = None  # For some reCAPTCHA
    enterprise: bool = False


@dataclass
class CaptchaResult:
    """Result of captcha solving"""
    success: bool
    token: Optional[str] = None
    error: Optional[str] = None
    solve_time: float = 0.0
    cost: float = 0.0
    provider: Optional[str] = None


class BaseSolverProvider(ABC):
    """Base class for captcha solver providers"""
    
    @abstractmethod
    async def solve(self, task: CaptchaTask) -> CaptchaResult:
        pass
    
    @abstractmethod
    async def get_balance(self) -> float:
        pass


class TwoCaptchaProvider(BaseSolverProvider):
    """2Captcha.com integration"""
    
    API_BASE = "https://2captcha.com"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session: Optional[httpx.AsyncClient] = None
    
    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None:
            self._session = httpx.AsyncClient(timeout=120.0)
        return self._session
    
    async def solve(self, task: CaptchaTask) -> CaptchaResult:
        """Solve captcha using 2Captcha"""
        import time
        start = time.time()
        
        try:
            session = await self._get_session()
            
            # Submit task
            if task.captcha_type == CaptchaType.RECAPTCHA_V2:
                submit_data = {
                    "key": self.api_key,
                    "method": "userrecaptcha",
                    "googlekey": task.site_key,
                    "pageurl": task.page_url,
                    "json": 1,
                }
                if task.invisible:
                    submit_data["invisible"] = 1
                if task.enterprise:
                    submit_data["enterprise"] = 1
                    
            elif task.captcha_type == CaptchaType.RECAPTCHA_V3:
                submit_data = {
                    "key": self.api_key,
                    "method": "userrecaptcha",
                    "googlekey": task.site_key,
                    "pageurl": task.page_url,
                    "version": "v3",
                    "action": task.action or "verify",
                    "min_score": task.min_score,
                    "json": 1,
                }
                
            elif task.captcha_type == CaptchaType.HCAPTCHA:
                submit_data = {
                    "key": self.api_key,
                    "method": "hcaptcha",
                    "sitekey": task.site_key,
                    "pageurl": task.page_url,
                    "json": 1,
                }
            else:
                return CaptchaResult(success=False, error=f"Unsupported captcha type: {task.captcha_type}")
            
            response = await session.post(f"{self.API_BASE}/in.php", data=submit_data)
            result = response.json()
            
            if result.get("status") != 1:
                return CaptchaResult(
                    success=False,
                    error=result.get("error_text", "Submit failed"),
                    provider="2captcha"
                )
            
            task_id = result.get("request")
            
            # Poll for result
            for _ in range(60):  # Max 2 minutes
                await asyncio.sleep(2)
                
                poll_response = await session.get(
                    f"{self.API_BASE}/res.php",
                    params={"key": self.api_key, "action": "get", "id": task_id, "json": 1}
                )
                poll_result = poll_response.json()
                
                if poll_result.get("status") == 1:
                    solve_time = time.time() - start
                    return CaptchaResult(
                        success=True,
                        token=poll_result.get("request"),
                        solve_time=solve_time,
                        cost=0.003,  # Approximate cost
                        provider="2captcha"
                    )
                
                if poll_result.get("request") != "CAPCHA_NOT_READY":
                    return CaptchaResult(
                        success=False,
                        error=poll_result.get("error_text", "Unknown error"),
                        provider="2captcha"
                    )
            
            return CaptchaResult(success=False, error="Timeout", provider="2captcha")
            
        except Exception as e:
            return CaptchaResult(success=False, error=str(e), provider="2captcha")
    
    async def get_balance(self) -> float:
        """Get account balance"""
        try:
            session = await self._get_session()
            response = await session.get(
                f"{self.API_BASE}/res.php",
                params={"key": self.api_key, "action": "getbalance", "json": 1}
            )
            result = response.json()
            return float(result.get("request", 0))
        except Exception:
            return 0.0


class CapMonsterProvider(BaseSolverProvider):
    """CapMonster.cloud integration"""
    
    API_BASE = "https://api.capmonster.cloud"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session: Optional[httpx.AsyncClient] = None
    
    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None:
            self._session = httpx.AsyncClient(timeout=120.0)
        return self._session
    
    async def solve(self, task: CaptchaTask) -> CaptchaResult:
        """Solve captcha using CapMonster"""
        import time
        start = time.time()
        
        try:
            session = await self._get_session()
            
            # Prepare task
            if task.captcha_type == CaptchaType.RECAPTCHA_V2:
                task_data = {
                    "type": "NoCaptchaTaskProxyless",
                    "websiteURL": task.page_url,
                    "websiteKey": task.site_key,
                }
                if task.invisible:
                    task_data["isInvisible"] = True
                    
            elif task.captcha_type == CaptchaType.RECAPTCHA_V3:
                task_data = {
                    "type": "RecaptchaV3TaskProxyless",
                    "websiteURL": task.page_url,
                    "websiteKey": task.site_key,
                    "minScore": task.min_score,
                    "pageAction": task.action or "verify",
                }
                
            elif task.captcha_type == CaptchaType.HCAPTCHA:
                task_data = {
                    "type": "HCaptchaTaskProxyless",
                    "websiteURL": task.page_url,
                    "websiteKey": task.site_key,
                }
            else:
                return CaptchaResult(success=False, error=f"Unsupported type: {task.captcha_type}")
            
            # Create task
            response = await session.post(
                f"{self.API_BASE}/createTask",
                json={"clientKey": self.api_key, "task": task_data}
            )
            result = response.json()
            
            if result.get("errorId", 0) != 0:
                return CaptchaResult(
                    success=False,
                    error=result.get("errorDescription", "Create task failed"),
                    provider="capmonster"
                )
            
            task_id = result.get("taskId")
            
            # Poll for result
            for _ in range(60):
                await asyncio.sleep(2)
                
                poll_response = await session.post(
                    f"{self.API_BASE}/getTaskResult",
                    json={"clientKey": self.api_key, "taskId": task_id}
                )
                poll_result = poll_response.json()
                
                if poll_result.get("status") == "ready":
                    solution = poll_result.get("solution", {})
                    solve_time = time.time() - start
                    return CaptchaResult(
                        success=True,
                        token=solution.get("gRecaptchaResponse") or solution.get("token"),
                        solve_time=solve_time,
                        cost=0.002,
                        provider="capmonster"
                    )
                
                if poll_result.get("errorId", 0) != 0:
                    return CaptchaResult(
                        success=False,
                        error=poll_result.get("errorDescription"),
                        provider="capmonster"
                    )
            
            return CaptchaResult(success=False, error="Timeout", provider="capmonster")
            
        except Exception as e:
            return CaptchaResult(success=False, error=str(e), provider="capmonster")
    
    async def get_balance(self) -> float:
        """Get account balance"""
        try:
            session = await self._get_session()
            response = await session.post(
                f"{self.API_BASE}/getBalance",
                json={"clientKey": self.api_key}
            )
            result = response.json()
            return float(result.get("balance", 0))
        except Exception:
            return 0.0


class CaptchaSolver:
    """
    Multi-provider captcha solver with fallback support
    
    Features:
    - Multiple provider support
    - Automatic fallback on failure
    - Balance monitoring
    - Harvester integration
    """
    
    def __init__(self):
        self.providers: Dict[str, BaseSolverProvider] = {}
        self.priority: List[str] = []
        self._harvester = None
        logger.info("CaptchaSolver initialized")
    
    def add_provider(self, name: str, provider: BaseSolverProvider, priority: int = 0):
        """Add a solver provider"""
        self.providers[name] = provider
        self.priority.append(name)
        self.priority.sort(key=lambda x: priority)
    
    def configure_2captcha(self, api_key: str, priority: int = 1):
        """Configure 2Captcha provider"""
        self.add_provider("2captcha", TwoCaptchaProvider(api_key), priority)
    
    def configure_capmonster(self, api_key: str, priority: int = 0):
        """Configure CapMonster provider"""
        self.add_provider("capmonster", CapMonsterProvider(api_key), priority)
    
    def set_harvester(self, harvester):
        """Set local captcha harvester"""
        self._harvester = harvester
    
    async def solve(
        self,
        page_url: str,
        site_key: str,
        captcha_type: CaptchaType = CaptchaType.RECAPTCHA_V2,
        action: Optional[str] = None,
        use_harvester: bool = True,
        **kwargs
    ) -> CaptchaResult:
        """
        Solve a captcha using available providers
        Falls back through providers on failure
        """
        task = CaptchaTask(
            captcha_type=captcha_type,
            site_key=site_key,
            page_url=page_url,
            action=action,
            **kwargs
        )
        
        # Try harvester first if available
        if use_harvester and self._harvester:
            result = await self._harvester.get_token(page_url, site_key)
            if result.success:
                logger.info("Captcha solved via harvester", solve_time=result.solve_time)
                return result
        
        # Try providers in priority order
        for provider_name in self.priority:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            
            result = await provider.solve(task)
            
            if result.success:
                logger.info(
                    "Captcha solved",
                    provider=provider_name,
                    solve_time=f"{result.solve_time:.2f}s",
                    cost=f"${result.cost:.4f}"
                )
                return result
            
            logger.warning(
                "Captcha solve failed, trying next provider",
                provider=provider_name,
                error=result.error
            )
        
        return CaptchaResult(success=False, error="All providers failed")
    
    async def get_balances(self) -> Dict[str, float]:
        """Get balance for all providers"""
        balances = {}
        for name, provider in self.providers.items():
            balances[name] = await provider.get_balance()
        return balances
