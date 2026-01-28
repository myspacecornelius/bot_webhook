"""
Advanced Proxy Management for Phantom Bot
Features: Health monitoring, smart rotation, ban detection, geographic distribution
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set
from enum import Enum
import httpx
from collections import defaultdict
import structlog

from ..utils.config import get_config
from ..utils.crypto import crypto

logger = structlog.get_logger()


class ProxyStatus(Enum):
    UNTESTED = "untested"
    GOOD = "good"
    SLOW = "slow"
    BAD = "bad"
    BANNED = "banned"
    RATE_LIMITED = "rate_limited"


@dataclass
class ProxyStats:
    """Statistics for a single proxy"""
    success_count: int = 0
    failure_count: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    last_response_time: float = 0.0
    last_used: float = 0.0
    last_tested: float = 0.0
    consecutive_failures: int = 0
    ban_count: int = 0
    sites_banned: Set[str] = field(default_factory=set)


@dataclass
class Proxy:
    """Proxy representation with full metadata"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    group_id: Optional[str] = None
    id: Optional[str] = None
    
    status: ProxyStatus = ProxyStatus.UNTESTED
    stats: ProxyStats = field(default_factory=ProxyStats)
    
    # Geographic info (detected)
    country: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    is_residential: bool = False
    is_datacenter: bool = False
    
    def __post_init__(self):
        if self.id is None:
            self.id = crypto.generate_task_id()
    
    @property
    def url(self) -> str:
        """Get proxy URL for requests"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def display(self) -> str:
        """Display string for UI"""
        if self.username:
            return f"{self.host}:{self.port}:{self.username}:****"
        return f"{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.stats.total_requests == 0:
            return 0.0
        return self.stats.success_count / self.stats.total_requests
    
    @classmethod
    def from_string(cls, proxy_string: str, group_id: Optional[str] = None) -> 'Proxy':
        """Parse proxy from string format (host:port:user:pass or host:port)"""
        parts = proxy_string.strip().split(':')
        
        if len(parts) >= 4:
            return cls(
                host=parts[0],
                port=int(parts[1]),
                username=parts[2],
                password=':'.join(parts[3:]),  # Handle passwords with colons
                group_id=group_id
            )
        elif len(parts) == 2:
            return cls(
                host=parts[0],
                port=int(parts[1]),
                group_id=group_id
            )
        else:
            raise ValueError(f"Invalid proxy format: {proxy_string}")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "protocol": self.protocol,
            "group_id": self.group_id,
            "status": self.status.value,
            "country": self.country,
            "is_residential": self.is_residential,
        }


class ProxyRotationStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    STICKY = "sticky"
    SMART = "smart"  # ML-based selection
    FASTEST = "fastest"
    LEAST_USED = "least_used"


class ProxyManager:
    """
    Advanced proxy management with intelligent rotation and health monitoring
    """
    
    def __init__(self):
        self.config = get_config()
        self.proxies: Dict[str, Proxy] = {}  # id -> Proxy
        self.groups: Dict[str, List[str]] = defaultdict(list)  # group_id -> [proxy_ids]
        
        # Rotation state
        self._rotation_index: Dict[str, int] = defaultdict(int)  # group_id -> index
        self._sticky_assignments: Dict[str, str] = {}  # task_id -> proxy_id
        self._site_proxy_cache: Dict[str, Dict[str, str]] = defaultdict(dict)  # site -> {task_id: proxy_id}
        
        # Health monitoring
        self._health_check_task: Optional[asyncio.Task] = None
        self._banned_proxies: Dict[str, Set[str]] = defaultdict(set)  # site -> {proxy_ids}
        
        # Rate limiting
        self._request_times: Dict[str, List[float]] = defaultdict(list)  # proxy_id -> [timestamps]
        
        logger.info("ProxyManager initialized")
    
    async def start(self):
        """Start the proxy manager and health monitoring"""
        if self.config.proxy.test_on_start:
            await self.test_all_proxies()
        
        # Start health check loop
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Proxy health monitoring started")
    
    async def stop(self):
        """Stop the proxy manager"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("ProxyManager stopped")
    
    def add_proxy(self, proxy: Proxy) -> str:
        """Add a single proxy"""
        self.proxies[proxy.id] = proxy
        if proxy.group_id:
            self.groups[proxy.group_id].append(proxy.id)
        logger.debug("Proxy added", proxy=proxy.display, group=proxy.group_id)
        return proxy.id
    
    def add_proxies_from_string(self, proxy_string: str, group_id: str) -> List[str]:
        """Add multiple proxies from newline-separated string"""
        proxy_ids = []
        for line in proxy_string.strip().split('\n'):
            line = line.strip()
            if line:
                try:
                    proxy = Proxy.from_string(line, group_id)
                    proxy_ids.append(self.add_proxy(proxy))
                except ValueError as e:
                    logger.warning("Failed to parse proxy", line=line, error=str(e))
        
        logger.info("Proxies added", count=len(proxy_ids), group=group_id)
        return proxy_ids
    
    def remove_proxy(self, proxy_id: str):
        """Remove a proxy"""
        if proxy_id in self.proxies:
            proxy = self.proxies[proxy_id]
            if proxy.group_id and proxy_id in self.groups[proxy.group_id]:
                self.groups[proxy.group_id].remove(proxy_id)
            del self.proxies[proxy_id]
            logger.debug("Proxy removed", proxy_id=proxy_id)
    
    def get_proxy(
        self,
        group_id: Optional[str] = None,
        task_id: Optional[str] = None,
        site: Optional[str] = None,
        strategy: Optional[ProxyRotationStrategy] = None
    ) -> Optional[Proxy]:
        """
        Get the next proxy based on rotation strategy
        
        Args:
            group_id: Specific proxy group to use
            task_id: Task ID for sticky sessions
            site: Site name to avoid banned proxies
            strategy: Override default rotation strategy
        """
        if strategy is None:
            strategy = ProxyRotationStrategy(self.config.proxy.rotation_strategy)
        
        # Get available proxies
        if group_id:
            proxy_ids = self.groups.get(group_id, [])
        else:
            proxy_ids = list(self.proxies.keys())
        
        if not proxy_ids:
            logger.warning("No proxies available", group=group_id)
            return None
        
        # Filter out bad/banned proxies
        available = []
        for pid in proxy_ids:
            proxy = self.proxies.get(pid)
            if proxy and proxy.status not in (ProxyStatus.BAD, ProxyStatus.BANNED):
                # Check site-specific bans
                if site and pid in self._banned_proxies.get(site, set()):
                    continue
                available.append(proxy)
        
        if not available:
            logger.warning("All proxies filtered out", group=group_id, site=site)
            # Fallback to any proxy
            available = [self.proxies[pid] for pid in proxy_ids if pid in self.proxies]
        
        if not available:
            return None
        
        # Apply rotation strategy
        if strategy == ProxyRotationStrategy.STICKY and task_id:
            return self._get_sticky_proxy(task_id, available, site)
        elif strategy == ProxyRotationStrategy.RANDOM:
            return random.choice(available)
        elif strategy == ProxyRotationStrategy.ROUND_ROBIN:
            return self._get_round_robin_proxy(group_id or "default", available)
        elif strategy == ProxyRotationStrategy.FASTEST:
            return min(available, key=lambda p: p.stats.avg_response_time or float('inf'))
        elif strategy == ProxyRotationStrategy.LEAST_USED:
            return min(available, key=lambda p: p.stats.total_requests)
        elif strategy == ProxyRotationStrategy.SMART:
            return self._get_smart_proxy(available, site)
        
        return random.choice(available)
    
    def _get_round_robin_proxy(self, group_id: str, proxies: List[Proxy]) -> Proxy:
        """Get next proxy in round-robin order"""
        index = self._rotation_index[group_id]
        proxy = proxies[index % len(proxies)]
        self._rotation_index[group_id] = (index + 1) % len(proxies)
        return proxy
    
    def _get_sticky_proxy(self, task_id: str, proxies: List[Proxy], site: Optional[str]) -> Proxy:
        """Get or assign a sticky proxy for a task"""
        # Check if task already has an assignment
        if task_id in self._sticky_assignments:
            proxy_id = self._sticky_assignments[task_id]
            if proxy_id in self.proxies:
                proxy = self.proxies[proxy_id]
                # Verify it's still valid
                if proxy in proxies:
                    return proxy
        
        # Assign new proxy
        proxy = random.choice(proxies)
        self._sticky_assignments[task_id] = proxy.id
        return proxy
    
    def _get_smart_proxy(self, proxies: List[Proxy], site: Optional[str]) -> Proxy:
        """
        Smart proxy selection using multiple factors:
        - Success rate
        - Response time
        - Recent usage
        - Site-specific performance
        """
        now = time.time()
        
        def score_proxy(proxy: Proxy) -> float:
            score = 0.0
            
            # Success rate (0-40 points)
            score += proxy.success_rate * 40
            
            # Response time (0-30 points, faster = better)
            if proxy.stats.avg_response_time > 0:
                # Normalize: 100ms = 30pts, 1000ms = 15pts, 5000ms = 0pts
                time_score = max(0, 30 - (proxy.stats.avg_response_time / 166.67))
                score += time_score
            else:
                score += 15  # Unknown = average
            
            # Freshness (0-20 points, less recent = better to distribute load)
            if proxy.stats.last_used > 0:
                seconds_since_use = now - proxy.stats.last_used
                freshness = min(20, seconds_since_use / 3)  # Max at 60 seconds
                score += freshness
            else:
                score += 20  # Never used = good
            
            # Consecutive failures penalty
            score -= proxy.stats.consecutive_failures * 10
            
            # Add randomness to prevent always picking same proxy
            score += random.uniform(0, 10)
            
            return score
        
        # Sort by score and return best
        scored = [(p, score_proxy(p)) for p in proxies]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[0][0]
    
    def record_success(self, proxy_id: str, response_time: float, site: Optional[str] = None):
        """Record a successful request"""
        if proxy_id not in self.proxies:
            return
        
        proxy = self.proxies[proxy_id]
        stats = proxy.stats
        
        stats.success_count += 1
        stats.total_requests += 1
        stats.consecutive_failures = 0
        stats.last_response_time = response_time
        stats.last_used = time.time()
        
        # Update average response time
        if stats.avg_response_time == 0:
            stats.avg_response_time = response_time
        else:
            stats.avg_response_time = (stats.avg_response_time * 0.8) + (response_time * 0.2)
        
        # Update status
        if proxy.status in (ProxyStatus.UNTESTED, ProxyStatus.SLOW):
            proxy.status = ProxyStatus.GOOD
    
    def record_failure(self, proxy_id: str, site: Optional[str] = None, is_ban: bool = False):
        """Record a failed request"""
        if proxy_id not in self.proxies:
            return
        
        proxy = self.proxies[proxy_id]
        stats = proxy.stats
        
        stats.failure_count += 1
        stats.total_requests += 1
        stats.consecutive_failures += 1
        stats.last_used = time.time()
        
        if is_ban:
            stats.ban_count += 1
            if site:
                stats.sites_banned.add(site)
                self._banned_proxies[site].add(proxy_id)
            
            if stats.ban_count >= 3:
                proxy.status = ProxyStatus.BANNED
        elif stats.consecutive_failures >= self.config.proxy.ban_threshold:
            proxy.status = ProxyStatus.BAD
            
            if self.config.proxy.auto_remove_bad:
                self.remove_proxy(proxy_id)
    
    async def test_proxy(self, proxy: Proxy) -> bool:
        """Test a single proxy"""
        test_url = self.config.proxy.test_url
        timeout = self.config.proxy.timeout
        
        try:
            start = time.time()
            async with httpx.AsyncClient(
                proxies={"all://": proxy.url},
                timeout=timeout,
                verify=False
            ) as client:
                response = await client.get(test_url)
                elapsed = (time.time() - start) * 1000  # ms
                
                if response.status_code == 200:
                    proxy.status = ProxyStatus.GOOD if elapsed < 2000 else ProxyStatus.SLOW
                    proxy.stats.last_tested = time.time()
                    proxy.stats.avg_response_time = elapsed
                    logger.debug("Proxy test passed", proxy=proxy.display, time_ms=elapsed)
                    return True
                else:
                    proxy.status = ProxyStatus.BAD
                    return False
                    
        except Exception as e:
            proxy.status = ProxyStatus.BAD
            logger.debug("Proxy test failed", proxy=proxy.display, error=str(e))
            return False
    
    async def test_all_proxies(self, group_id: Optional[str] = None):
        """Test all proxies concurrently"""
        if group_id:
            proxy_ids = self.groups.get(group_id, [])
        else:
            proxy_ids = list(self.proxies.keys())
        
        proxies = [self.proxies[pid] for pid in proxy_ids if pid in self.proxies]
        
        if not proxies:
            return
        
        logger.info("Testing proxies", count=len(proxies))
        
        # Test in batches to avoid overwhelming
        batch_size = 50
        for i in range(0, len(proxies), batch_size):
            batch = proxies[i:i + batch_size]
            await asyncio.gather(*[self.test_proxy(p) for p in batch])
        
        # Log results
        good = sum(1 for p in proxies if p.status == ProxyStatus.GOOD)
        slow = sum(1 for p in proxies if p.status == ProxyStatus.SLOW)
        bad = sum(1 for p in proxies if p.status == ProxyStatus.BAD)
        
        logger.info("Proxy test complete", good=good, slow=slow, bad=bad)
    
    async def _health_check_loop(self):
        """Periodic health check loop"""
        interval = self.config.proxy.health_check_interval
        
        while True:
            try:
                await asyncio.sleep(interval)
                await self.test_all_proxies()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check error", error=str(e))
    
    def get_stats(self, group_id: Optional[str] = None) -> Dict:
        """Get proxy statistics"""
        if group_id:
            proxy_ids = self.groups.get(group_id, [])
        else:
            proxy_ids = list(self.proxies.keys())
        
        proxies = [self.proxies[pid] for pid in proxy_ids if pid in self.proxies]
        
        return {
            "total": len(proxies),
            "good": sum(1 for p in proxies if p.status == ProxyStatus.GOOD),
            "slow": sum(1 for p in proxies if p.status == ProxyStatus.SLOW),
            "bad": sum(1 for p in proxies if p.status == ProxyStatus.BAD),
            "banned": sum(1 for p in proxies if p.status == ProxyStatus.BANNED),
            "untested": sum(1 for p in proxies if p.status == ProxyStatus.UNTESTED),
            "avg_response_time": sum(p.stats.avg_response_time for p in proxies) / len(proxies) if proxies else 0,
            "total_requests": sum(p.stats.total_requests for p in proxies),
            "success_rate": sum(p.success_rate for p in proxies) / len(proxies) if proxies else 0,
        }
    
    def clear_bans(self, site: Optional[str] = None):
        """Clear ban records"""
        if site:
            self._banned_proxies[site].clear()
            for proxy in self.proxies.values():
                proxy.stats.sites_banned.discard(site)
        else:
            self._banned_proxies.clear()
            for proxy in self.proxies.values():
                proxy.stats.sites_banned.clear()
                proxy.stats.ban_count = 0
                if proxy.status == ProxyStatus.BANNED:
                    proxy.status = ProxyStatus.UNTESTED
        
        logger.info("Ban records cleared", site=site or "all")
    
    def export_proxies(self, group_id: Optional[str] = None, status: Optional[ProxyStatus] = None) -> str:
        """Export proxies as string"""
        if group_id:
            proxy_ids = self.groups.get(group_id, [])
        else:
            proxy_ids = list(self.proxies.keys())
        
        lines = []
        for pid in proxy_ids:
            proxy = self.proxies.get(pid)
            if proxy:
                if status is None or proxy.status == status:
                    if proxy.username and proxy.password:
                        lines.append(f"{proxy.host}:{proxy.port}:{proxy.username}:{proxy.password}")
                    else:
                        lines.append(f"{proxy.host}:{proxy.port}")
        
        return '\n'.join(lines)
