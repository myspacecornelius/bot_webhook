"""
Price Tracking & Profit Analysis
Monitors resale markets to determine profitability
"""

import asyncio
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class MarketPrice:
    """Price data from a market"""
    source: str  # stockx, goat, ebay
    lowest_ask: Optional[float] = None
    highest_bid: Optional[float] = None
    last_sale: Optional[float] = None
    sales_last_72h: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProfitAnalysis:
    """Profit analysis for a product"""
    sku: str
    retail_price: float
    market_prices: Dict[str, MarketPrice] = field(default_factory=dict)
    
    @property
    def best_resale(self) -> Optional[float]:
        """Get best resale price across markets"""
        prices = [p.lowest_ask for p in self.market_prices.values() if p.lowest_ask]
        return min(prices) if prices else None
    
    @property
    def estimated_profit(self) -> Optional[float]:
        """Calculate estimated profit after fees"""
        if not self.best_resale:
            return None
        
        # Assume ~13% fees (StockX/GOAT average)
        net_resale = self.best_resale * 0.87
        return net_resale - self.retail_price
    
    @property
    def profit_margin(self) -> Optional[float]:
        """Calculate profit margin percentage"""
        if not self.estimated_profit:
            return None
        return (self.estimated_profit / self.retail_price) * 100
    
    @property
    def is_profitable(self) -> bool:
        """Check if product is worth copping"""
        profit = self.estimated_profit
        return profit is not None and profit > 20  # $20 minimum profit


class PriceTracker:
    """
    Tracks resale prices across StockX, GOAT, and eBay
    Provides real-time profit analysis
    """
    
    def __init__(self):
        self._cache: Dict[str, ProfitAnalysis] = {}
        self._cache_ttl = 300  # 5 minutes
        self._session: Optional[httpx.AsyncClient] = None
        logger.info("PriceTracker initialized")
    
    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None:
            self._session = httpx.AsyncClient(
                timeout=15.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self._session
    
    async def get_stockx_price(self, sku: str) -> Optional[MarketPrice]:
        """Get price from StockX"""
        try:
            session = await self._get_session()
            
            # StockX search API
            search_url = f"https://stockx.com/api/browse?_search={sku}"
            
            response = await session.get(search_url)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            products = data.get("Products", [])
            
            if not products:
                return None
            
            product = products[0]
            market = product.get("market", {})
            
            return MarketPrice(
                source="stockx",
                lowest_ask=market.get("lowestAsk"),
                highest_bid=market.get("highestBid"),
                last_sale=market.get("lastSale"),
                sales_last_72h=market.get("salesLast72Hours", 0)
            )
            
        except Exception as e:
            logger.warning("StockX price fetch failed", sku=sku, error=str(e))
            return None
    
    async def get_goat_price(self, sku: str) -> Optional[MarketPrice]:
        """Get price from GOAT"""
        try:
            session = await self._get_session()
            
            # GOAT search API
            search_url = f"https://www.goat.com/api/v1/product_templates?query={sku}"
            
            response = await session.get(search_url)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            products = data.get("productTemplates", [])
            
            if not products:
                return None
            
            product = products[0]
            
            return MarketPrice(
                source="goat",
                lowest_ask=product.get("lowestPriceCents", 0) / 100 if product.get("lowestPriceCents") else None,
                last_sale=product.get("lastSoldPriceCents", 0) / 100 if product.get("lastSoldPriceCents") else None,
            )
            
        except Exception as e:
            logger.warning("GOAT price fetch failed", sku=sku, error=str(e))
            return None
    
    async def analyze_profit(self, sku: str, retail_price: float) -> ProfitAnalysis:
        """Get full profit analysis for a product"""
        # Check cache
        if sku in self._cache:
            cached = self._cache[sku]
            age = (datetime.now() - list(cached.market_prices.values())[0].timestamp).seconds
            if age < self._cache_ttl:
                return cached
        
        # Fetch prices concurrently
        stockx_task = self.get_stockx_price(sku)
        goat_task = self.get_goat_price(sku)
        
        stockx_price, goat_price = await asyncio.gather(stockx_task, goat_task)
        
        analysis = ProfitAnalysis(sku=sku, retail_price=retail_price)
        
        if stockx_price:
            analysis.market_prices["stockx"] = stockx_price
        if goat_price:
            analysis.market_prices["goat"] = goat_price
        
        # Cache result
        self._cache[sku] = analysis
        
        logger.info(
            "Profit analysis complete",
            sku=sku,
            retail=retail_price,
            resale=analysis.best_resale,
            profit=analysis.estimated_profit,
            margin=f"{analysis.profit_margin:.1f}%" if analysis.profit_margin else "N/A"
        )
        
        return analysis
    
    async def get_trending_products(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending products with high resale value"""
        try:
            session = await self._get_session()
            
            # StockX trending
            url = "https://stockx.com/api/browse?sort=most-active&order=DESC"
            response = await session.get(url)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            products = data.get("Products", [])[:limit]
            
            trending = []
            for p in products:
                market = p.get("market", {})
                retail = p.get("retailPrice", 0)
                resale = market.get("lowestAsk", 0)
                
                if retail and resale:
                    profit = (resale * 0.87) - retail
                    trending.append({
                        "name": p.get("title"),
                        "sku": p.get("styleId"),
                        "retail": retail,
                        "resale": resale,
                        "profit": profit,
                        "margin": (profit / retail * 100) if retail else 0,
                        "sales_72h": market.get("salesLast72Hours", 0),
                    })
            
            # Sort by profit
            trending.sort(key=lambda x: x.get("profit", 0), reverse=True)
            
            return trending
            
        except Exception as e:
            logger.error("Failed to get trending products", error=str(e))
            return []
    
    def get_recommendation(self, analysis: ProfitAnalysis) -> str:
        """Get buy/pass recommendation"""
        if not analysis.estimated_profit:
            return "⚪ UNKNOWN - No price data"
        
        margin = analysis.profit_margin or 0
        profit = analysis.estimated_profit
        
        if margin >= 50 and profit >= 50:
            return "🟢 STRONG BUY - High profit potential"
        elif margin >= 30 and profit >= 30:
            return "🟢 BUY - Good profit margin"
        elif margin >= 15 and profit >= 20:
            return "🟡 CONSIDER - Moderate profit"
        elif margin >= 0:
            return "🟠 RISKY - Low margin"
        else:
            return "🔴 PASS - Will likely lose money"
    
    async def close(self):
        if self._session:
            await self._session.aclose()
