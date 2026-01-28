"""
Release Calendar
Tracks upcoming sneaker releases from multiple sources
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import httpx
import structlog

logger = structlog.get_logger()


class ReleaseType(Enum):
    SNKRS = "snkrs"
    CONFIRMED = "confirmed"
    SHOPIFY = "shopify"
    FOOTSITES = "footsites"
    RAFFLE = "raffle"
    GENERAL = "general"


@dataclass
class Release:
    """A sneaker release"""
    id: str
    name: str
    brand: str
    sku: str
    retail_price: float
    release_date: datetime
    release_type: ReleaseType
    
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    colorway: str = ""
    
    # Research data
    estimated_resale: Optional[float] = None
    estimated_profit: Optional[float] = None
    hype_score: float = 0.0
    
    # Status
    is_live: bool = False
    is_sold_out: bool = False
    
    # Notifications
    notify_enabled: bool = True
    auto_create_tasks: bool = False
    
    sources: List[str] = field(default_factory=list)


class ReleaseCalendar:
    """
    Aggregates release calendars from multiple sources
    
    Sources:
    - Nike SNKRS
    - Adidas Confirmed
    - Sneaker News
    - Sole Collector
    """
    
    def __init__(self):
        self.releases: Dict[str, Release] = {}
        self._session: Optional[httpx.AsyncClient] = None
        self._last_sync: Optional[datetime] = None
        logger.info("ReleaseCalendar initialized")
    
    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None:
            self._session = httpx.AsyncClient(
                timeout=15.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self._session
    
    async def sync(self):
        """Sync releases from all sources"""
        logger.info("Syncing release calendar...")
        
        # Fetch from multiple sources concurrently
        tasks = [
            self._fetch_snkrs_releases(),
            self._fetch_sneakernews_releases(),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error("Calendar sync error", error=str(result))
            elif isinstance(result, list):
                for release in result:
                    self.releases[release.id] = release
        
        self._last_sync = datetime.now()
        logger.info(f"Calendar synced: {len(self.releases)} releases")
    
    async def _fetch_snkrs_releases(self) -> List[Release]:
        """Fetch releases from Nike SNKRS"""
        releases = []
        
        try:
            session = await self._get_session()
            
            # Nike SNKRS upcoming feed
            url = "https://api.nike.com/product_feed/threads/v2"
            params = {
                "filter": "marketplace(US)",
                "filter": "language(en)",
                "filter": "upcoming(true)",
                "anchor": "0",
                "count": "50"
            }
            
            response = await session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("objects", []):
                    product = item.get("productInfo", [{}])[0]
                    
                    release = Release(
                        id=f"snkrs_{product.get('merchProduct', {}).get('id', '')}",
                        name=product.get("productContent", {}).get("fullTitle", ""),
                        brand="Nike",
                        sku=product.get("merchProduct", {}).get("styleColor", ""),
                        retail_price=product.get("merchPrice", {}).get("currentPrice", 0),
                        release_date=datetime.fromisoformat(
                            item.get("publishedContent", {}).get("publishStartDate", "").replace("Z", "+00:00")
                        ) if item.get("publishedContent", {}).get("publishStartDate") else datetime.now(),
                        release_type=ReleaseType.SNKRS,
                        image_url=product.get("imageUrls", {}).get("productImageUrl"),
                        colorway=product.get("productContent", {}).get("colorDescription", ""),
                        sources=["Nike SNKRS"]
                    )
                    releases.append(release)
                    
        except Exception as e:
            logger.error("SNKRS fetch failed", error=str(e))
        
        return releases
    
    async def _fetch_sneakernews_releases(self) -> List[Release]:
        """Fetch releases from Sneaker News"""
        releases = []
        
        try:
            session = await self._get_session()
            
            # Sneaker News release dates page
            url = "https://sneakernews.com/release-dates/"
            response = await session.get(url)
            
            if response.status_code == 200:
                # Parse HTML for release info
                # This is a simplified example - real implementation would use BeautifulSoup
                pass
                
        except Exception as e:
            logger.error("SneakerNews fetch failed", error=str(e))
        
        return releases
    
    def get_upcoming(self, days: int = 7) -> List[Release]:
        """Get releases in the next N days"""
        cutoff = datetime.now() + timedelta(days=days)
        now = datetime.now()
        
        upcoming = [
            r for r in self.releases.values()
            if now <= r.release_date <= cutoff
        ]
        
        upcoming.sort(key=lambda x: x.release_date)
        return upcoming
    
    def get_today(self) -> List[Release]:
        """Get today's releases"""
        today = datetime.now().date()
        
        return [
            r for r in self.releases.values()
            if r.release_date.date() == today
        ]
    
    def get_by_brand(self, brand: str) -> List[Release]:
        """Get releases by brand"""
        brand_lower = brand.lower()
        return [
            r for r in self.releases.values()
            if r.brand.lower() == brand_lower
        ]
    
    def get_profitable(self, min_profit: float = 20) -> List[Release]:
        """Get releases with estimated profit above threshold"""
        return [
            r for r in self.releases.values()
            if r.estimated_profit and r.estimated_profit >= min_profit
        ]
    
    def get_hyped(self, min_hype: float = 70) -> List[Release]:
        """Get releases with high hype score"""
        return [
            r for r in self.releases.values()
            if r.hype_score >= min_hype
        ]
    
    def set_notification(self, release_id: str, enabled: bool = True):
        """Enable/disable notification for a release"""
        if release_id in self.releases:
            self.releases[release_id].notify_enabled = enabled
    
    def set_auto_task(self, release_id: str, enabled: bool = True):
        """Enable/disable auto task creation for a release"""
        if release_id in self.releases:
            self.releases[release_id].auto_create_tasks = enabled
    
    def get_releases_needing_tasks(self) -> List[Release]:
        """Get releases that should have tasks auto-created"""
        now = datetime.now()
        window_start = now - timedelta(hours=1)  # 1 hour before release
        window_end = now + timedelta(hours=24)  # Up to 24 hours ahead
        
        return [
            r for r in self.releases.values()
            if r.auto_create_tasks
            and window_start <= r.release_date <= window_end
            and not r.is_sold_out
        ]
    
    def format_calendar(self, releases: List[Release]) -> str:
        """Format releases as readable calendar"""
        if not releases:
            return "No upcoming releases"
        
        lines = ["📅 **Upcoming Releases**\n"]
        
        current_date = None
        for release in releases:
            date = release.release_date.date()
            
            if date != current_date:
                current_date = date
                lines.append(f"\n**{date.strftime('%A, %B %d')}**")
            
            time_str = release.release_date.strftime("%I:%M %p")
            profit_str = f"(+${release.estimated_profit:.0f})" if release.estimated_profit else ""
            hype_str = "🔥" * int(release.hype_score / 25) if release.hype_score > 50 else ""
            
            lines.append(f"  • {time_str} - {release.name} ${release.retail_price:.0f} {profit_str} {hype_str}")
        
        return "\n".join(lines)
    
    async def close(self):
        if self._session:
            await self._session.aclose()


# Need asyncio for gather
import asyncio
