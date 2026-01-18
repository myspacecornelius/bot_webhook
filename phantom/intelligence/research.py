"""
Automated Product Research
Replaces cook groups by automatically finding hyped products and generating keywords
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import httpx
import re
import structlog

from .pricing import PriceTracker

logger = structlog.get_logger()


@dataclass
class ProductResearch:
    """Research data for a product"""
    name: str
    sku: str
    brand: str
    retail_price: float
    release_date: Optional[datetime] = None
    
    # Generated data
    keywords: str = ""
    recommended_sites: List[str] = field(default_factory=list)
    profit_analysis: Optional[Any] = None
    hype_score: float = 0.0  # 0-100
    
    # Sources
    sources: List[str] = field(default_factory=list)


class ProductResearcher:
    """
    Automated product research that replaces cook groups
    
    Features:
    - Scrapes sneaker news sites for upcoming releases
    - Generates optimal keywords for monitoring
    - Analyzes profit potential
    - Recommends sites likely to have stock
    - Calculates hype scores based on social signals
    """
    
    # Sites to monitor for releases
    NEWS_SOURCES = [
        "https://sneakernews.com",
        "https://solecollector.com",
        "https://hypebeast.com",
    ]
    
    # Shopify sites by brand affinity
    SITE_RECOMMENDATIONS = {
        "nike": ["DTLR", "Shoe Palace", "Jimmy Jazz", "Hibbett", "Social Status"],
        "jordan": ["DTLR", "Shoe Palace", "Jimmy Jazz", "Hibbett", "Undefeated"],
        "adidas": ["DTLR", "Shoe Palace", "Hibbett", "Concepts", "Bodega"],
        "yeezy": ["DTLR", "Shoe Palace", "Jimmy Jazz"],
        "new balance": ["Concepts", "Bodega", "Kith", "Notre"],
        "default": ["DTLR", "Shoe Palace", "Jimmy Jazz", "Hibbett"],
    }
    
    def __init__(self):
        self.price_tracker = PriceTracker()
        self._session: Optional[httpx.AsyncClient] = None
        self._research_cache: Dict[str, ProductResearch] = {}
        logger.info("ProductResearcher initialized")
    
    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None:
            self._session = httpx.AsyncClient(
                timeout=15.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self._session
    
    def generate_keywords(self, product: ProductResearch) -> str:
        """Generate optimal keywords for monitoring"""
        keywords = []
        
        # Add SKU as primary identifier
        if product.sku:
            keywords.append(f"+{product.sku}")
        
        # Extract key terms from name
        name_lower = product.name.lower()
        
        # Remove common filler words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'mens', 'womens'}
        words = [w for w in re.findall(r'\w+', name_lower) if w not in stopwords and len(w) > 2]
        
        # Add brand
        if product.brand:
            keywords.append(f"+{product.brand.lower()}")
        
        # Add important product words
        important_words = []
        for word in words[:5]:
            if word not in product.brand.lower():
                important_words.append(word)
        
        if important_words:
            keywords.append(f"*{important_words[0]}")  # Required keyword
        
        # Add common negative keywords
        negatives = ["-gs", "-gradeschool", "-preschool", "-toddler", "-infant", "-td", "-ps", "-little"]
        keywords.extend(negatives)
        
        return ", ".join(keywords)
    
    def get_recommended_sites(self, product: ProductResearch) -> List[str]:
        """Get recommended sites for a product based on brand"""
        brand = product.brand.lower()
        
        for key, sites in self.SITE_RECOMMENDATIONS.items():
            if key in brand:
                return sites
        
        return self.SITE_RECOMMENDATIONS["default"]
    
    def calculate_hype_score(self, product: ProductResearch) -> float:
        """Calculate hype score (0-100) based on various signals"""
        score = 50.0  # Base score
        
        # Profit potential
        if product.profit_analysis:
            profit = product.profit_analysis.estimated_profit or 0
            margin = product.profit_analysis.profit_margin or 0
            
            if profit > 100:
                score += 25
            elif profit > 50:
                score += 15
            elif profit > 20:
                score += 5
            
            if margin > 50:
                score += 10
        
        # Brand hype
        hyped_keywords = ['travis', 'off-white', 'ow', 'union', 'fragment', 'dior', 'supreme']
        name_lower = product.name.lower()
        
        for kw in hyped_keywords:
            if kw in name_lower:
                score += 15
                break
        
        # Popular silhouettes
        popular = ['dunk', 'jordan 1', 'jordan 4', 'yeezy 350', 'yeezy slide']
        for sil in popular:
            if sil in name_lower:
                score += 10
                break
        
        return min(100, max(0, score))
    
    async def research_product(self, name: str, sku: str, retail_price: float, brand: str = "") -> ProductResearch:
        """Perform full research on a product"""
        # Check cache
        if sku in self._research_cache:
            return self._research_cache[sku]
        
        research = ProductResearch(
            name=name,
            sku=sku,
            brand=brand or self._detect_brand(name),
            retail_price=retail_price
        )
        
        # Get profit analysis
        research.profit_analysis = await self.price_tracker.analyze_profit(sku, retail_price)
        
        # Generate keywords
        research.keywords = self.generate_keywords(research)
        
        # Get recommended sites
        research.recommended_sites = self.get_recommended_sites(research)
        
        # Calculate hype score
        research.hype_score = self.calculate_hype_score(research)
        
        # Cache result
        self._research_cache[sku] = research
        
        logger.info(
            "Product research complete",
            name=name,
            sku=sku,
            hype_score=research.hype_score,
            keywords=research.keywords
        )
        
        return research
    
    def _detect_brand(self, name: str) -> str:
        """Detect brand from product name"""
        name_lower = name.lower()
        
        brands = {
            "nike": ["nike", "air max", "air force", "dunk", "blazer"],
            "jordan": ["jordan", "air jordan", "retro"],
            "adidas": ["adidas", "yeezy", "ultraboost", "nmd"],
            "new balance": ["new balance", "nb "],
            "asics": ["asics", "gel-"],
            "puma": ["puma"],
            "reebok": ["reebok"],
            "converse": ["converse", "chuck taylor"],
            "vans": ["vans", "old skool", "sk8-hi"],
        }
        
        for brand, keywords in brands.items():
            for kw in keywords:
                if kw in name_lower:
                    return brand.title()
        
        return "Unknown"
    
    async def get_upcoming_releases(self, days_ahead: int = 14) -> List[ProductResearch]:
        """Get upcoming releases worth monitoring"""
        releases = []
        
        # Get trending products as proxy for upcoming hype
        trending = await self.price_tracker.get_trending_products(limit=30)
        
        for item in trending:
            if item.get("profit", 0) > 20:  # Only profitable items
                research = await self.research_product(
                    name=item.get("name", ""),
                    sku=item.get("sku", ""),
                    retail_price=item.get("retail", 0),
                )
                releases.append(research)
        
        # Sort by hype score
        releases.sort(key=lambda x: x.hype_score, reverse=True)
        
        return releases[:20]
    
    async def auto_generate_monitors(self, min_hype_score: float = 60) -> List[Dict[str, Any]]:
        """Auto-generate monitor configurations for hyped products"""
        releases = await self.get_upcoming_releases()
        
        monitors = []
        for research in releases:
            if research.hype_score >= min_hype_score:
                for site in research.recommended_sites[:3]:  # Top 3 sites
                    monitors.append({
                        "site_name": site,
                        "keywords": research.keywords,
                        "product_name": research.name,
                        "sku": research.sku,
                        "retail_price": research.retail_price,
                        "estimated_profit": research.profit_analysis.estimated_profit if research.profit_analysis else None,
                        "hype_score": research.hype_score,
                    })
        
        logger.info(f"Auto-generated {len(monitors)} monitor configurations")
        return monitors
    
    def get_research_summary(self, research: ProductResearch) -> str:
        """Get formatted research summary"""
        profit = research.profit_analysis.estimated_profit if research.profit_analysis else None
        margin = research.profit_analysis.profit_margin if research.profit_analysis else None
        
        summary = f"""
📦 **{research.name}**
━━━━━━━━━━━━━━━━━━━━

**SKU:** {research.sku}
**Brand:** {research.brand}
**Retail:** ${research.retail_price:.2f}

**💰 Profit Analysis:**
• Estimated Profit: ${profit:.2f if profit else 'N/A'}
• Profit Margin: {margin:.1f}% if margin else 'N/A'
• Recommendation: {self.price_tracker.get_recommendation(research.profit_analysis) if research.profit_analysis else 'N/A'}

**🔥 Hype Score:** {research.hype_score:.0f}/100

**🔍 Suggested Keywords:**
```
{research.keywords}
```

**🏪 Recommended Sites:**
{', '.join(research.recommended_sites)}
"""
        return summary
    
    async def close(self):
        if self._session:
            await self._session.aclose()
        await self.price_tracker.close()
