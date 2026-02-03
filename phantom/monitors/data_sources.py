"""
Dynamic Data Sources for Product Information
Fetches live pricing and trending products from external sources
"""

import asyncio
import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
import httpx
import structlog
import re

logger = structlog.get_logger()


@dataclass
class ExternalProduct:
    """Product data from an external source"""
    name: str
    brand: str
    style_code: Optional[str] = None
    colorway: Optional[str] = None
    retail_price: float = 0.0
    market_price: float = 0.0  # Current resale price
    last_sale_price: float = 0.0
    price_premium: float = 0.0  # How much above retail
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    source: str = "unknown"
    fetched_at: datetime = field(default_factory=datetime.now)
    
    # Generated keywords
    positive_keywords: List[str] = field(default_factory=list)
    negative_keywords: List[str] = field(default_factory=list)
    
    @property
    def profit_potential(self) -> float:
        """Calculate potential profit"""
        if self.retail_price > 0 and self.market_price > 0:
            return self.market_price - self.retail_price
        return 0.0
    
    @property
    def is_profitable(self) -> bool:
        """Check if resale is profitable (>$30 margin after fees)"""
        return self.profit_potential > 50  # Account for ~$20 in fees
    
    def generate_keywords(self):
        """Auto-generate keywords from product info"""
        keywords = []
        
        # Add style code if available
        if self.style_code:
            keywords.append(self.style_code.upper())
            # Also add without hyphen
            keywords.append(self.style_code.replace("-", "").upper())
        
        # Extract key terms from name
        name_lower = self.name.lower()
        
        # Remove common filler words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'mens', 'womens', 'shoes'}
        words = [w for w in re.split(r'\s+', name_lower) if w not in stopwords and len(w) > 2]
        
        # Add brand
        if self.brand:
            keywords.append(self.brand.lower())
        
        # Add significant words
        keywords.extend(words[:5])
        
        # Add colorway
        if self.colorway:
            keywords.append(self.colorway.lower())
        
        self.positive_keywords = list(set(keywords))
        
        # Standard negative keywords for adult sizes only
        self.negative_keywords = [
            "gs", "gradeschool", "grade school",
            "ps", "preschool", "pre school", 
            "td", "toddler",
            "infant", "kids", "youth",
            "replica", "rep", "fake", "ua"
        ]


class DataSource(ABC):
    """Abstract base class for external data sources"""
    
    def __init__(self, cache_ttl_minutes: int = 30):
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._session: Optional[httpx.AsyncClient] = None
        self._last_request_time = 0.0
        self._min_delay = 2.0  # Minimum seconds between requests
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session"""
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.9",
                }
            )
        return self._session
    
    async def _rate_limited_request(self, url: str, **kwargs) -> httpx.Response:
        """Make a rate-limited request"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            await asyncio.sleep(self._min_delay - elapsed)
        
        self._last_request_time = time.time()
        session = await self._get_session()
        return await session.get(url, **kwargs)
    
    def _get_cache_key(self, *args) -> str:
        """Generate cache key from arguments"""
        return hashlib.md5(str(args).encode()).hexdigest()
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self._cache:
            value, cached_at = self._cache[key]
            if datetime.now() - cached_at < self.cache_ttl:
                return value
        return None
    
    def _set_cached(self, key: str, value: Any):
        """Cache a value"""
        self._cache[key] = (value, datetime.now())
    
    @abstractmethod
    async def fetch_trending(self, limit: int = 50) -> List[ExternalProduct]:
        """Fetch trending/popular products"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[ExternalProduct]:
        """Search for products"""
        pass
    
    @abstractmethod
    async def get_price(self, style_code: str) -> Optional[ExternalProduct]:
        """Get current pricing for a specific product"""
        pass
    
    async def close(self):
        """Close the session"""
        if self._session:
            await self._session.aclose()
            self._session = None


class StockXSource(DataSource):
    """
    StockX data source - fetches trending products and pricing
    Uses public browse/search endpoints
    """
    
    BASE_URL = "https://stockx.com"
    API_URL = "https://stockx.com/api"
    
    BRAND_SLUGS = {
        "nike": "nike",
        "jordan": "air-jordan",
        "adidas": "adidas",
        "yeezy": "adidas-yeezy",
        "new balance": "new-balance",
        "asics": "asics",
        "converse": "converse",
    }
    
    def __init__(self):
        super().__init__(cache_ttl_minutes=15)
        self._min_delay = 3.0  # Be respectful to StockX
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get session with StockX-specific headers"""
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": "https://stockx.com/",
                    "Origin": "https://stockx.com",
                    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"macOS"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                }
            )
        return self._session
    
    async def fetch_trending(self, limit: int = 50) -> List[ExternalProduct]:
        """Fetch trending sneakers from StockX"""
        cache_key = self._get_cache_key("trending", limit)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        products = []
        
        try:
            # Use the browse endpoint for trending sneakers
            url = f"{self.API_URL}/browse"
            params = {
                "productCategory": "sneakers",
                "_tags": "trending",
                "page": 1,
                "resultsPerPage": min(limit, 40),
                "sort": "most-active",
            }
            
            response = await self._rate_limited_request(url, params=params)
            
            if response.status_code != 200:
                logger.warning("StockX trending request failed", status=response.status_code)
                return products
            
            data = response.json()
            
            for item in data.get("Products", []):
                product = self._parse_product(item)
                if product:
                    products.append(product)
            
            self._set_cached(cache_key, products)
            logger.info("Fetched StockX trending", count=len(products))
            
        except Exception as e:
            logger.error("StockX fetch_trending error", error=str(e))
        
        return products
    
    async def search(self, query: str, limit: int = 20) -> List[ExternalProduct]:
        """Search StockX for products"""
        cache_key = self._get_cache_key("search", query, limit)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        products = []
        
        try:
            url = f"{self.API_URL}/browse"
            params = {
                "productCategory": "sneakers",
                "_search": query,
                "page": 1,
                "resultsPerPage": min(limit, 40),
            }
            
            response = await self._rate_limited_request(url, params=params)
            
            if response.status_code != 200:
                logger.warning("StockX search failed", status=response.status_code, query=query)
                return products
            
            data = response.json()
            
            for item in data.get("Products", []):
                product = self._parse_product(item)
                if product:
                    products.append(product)
            
            self._set_cached(cache_key, products)
            logger.info("StockX search complete", query=query, count=len(products))
            
        except Exception as e:
            logger.error("StockX search error", error=str(e), query=query)
        
        return products
    
    async def get_price(self, style_code: str) -> Optional[ExternalProduct]:
        """Get pricing for a specific style code"""
        cache_key = self._get_cache_key("price", style_code)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Search by style code
            results = await self.search(style_code, limit=5)
            
            # Find exact match
            style_upper = style_code.upper().replace("-", "")
            for product in results:
                if product.style_code:
                    product_style = product.style_code.upper().replace("-", "")
                    if product_style == style_upper:
                        self._set_cached(cache_key, product)
                        return product
            
            # Return first result if no exact match
            if results:
                self._set_cached(cache_key, results[0])
                return results[0]
                
        except Exception as e:
            logger.error("StockX get_price error", error=str(e), style_code=style_code)
        
        return None
    
    async def fetch_by_brand(self, brand: str, limit: int = 30) -> List[ExternalProduct]:
        """Fetch trending products for a specific brand"""
        slug = self.BRAND_SLUGS.get(brand.lower())
        if not slug:
            return await self.search(brand, limit)
        
        cache_key = self._get_cache_key("brand", brand, limit)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        products = []
        
        try:
            url = f"{self.API_URL}/browse"
            params = {
                "productCategory": "sneakers",
                "brand": slug,
                "page": 1,
                "resultsPerPage": min(limit, 40),
                "sort": "most-active",
            }
            
            response = await self._rate_limited_request(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("Products", []):
                    product = self._parse_product(item)
                    if product:
                        products.append(product)
            
            self._set_cached(cache_key, products)
            
        except Exception as e:
            logger.error("StockX fetch_by_brand error", error=str(e), brand=brand)
        
        return products
    
    def _parse_product(self, data: Dict) -> Optional[ExternalProduct]:
        """Parse StockX product data"""
        try:
            # Extract pricing
            market_data = data.get("market", {})
            retail_price = float(data.get("retailPrice", 0) or 0)
            
            # Get lowest ask as market price
            market_price = float(market_data.get("lowestAsk", 0) or 0)
            last_sale = float(market_data.get("lastSale", 0) or 0)
            
            # Calculate premium
            price_premium = 0.0
            if retail_price > 0 and market_price > 0:
                price_premium = ((market_price - retail_price) / retail_price) * 100
            
            product = ExternalProduct(
                name=data.get("title", data.get("name", "")),
                brand=data.get("brand", ""),
                style_code=data.get("styleId", ""),
                colorway=data.get("colorway", ""),
                retail_price=retail_price,
                market_price=market_price,
                last_sale_price=last_sale,
                price_premium=price_premium,
                image_url=data.get("media", {}).get("imageUrl"),
                product_url=f"{self.BASE_URL}/{data.get('urlKey', '')}",
                source="stockx",
            )
            
            product.generate_keywords()
            return product
            
        except Exception as e:
            logger.warning("Failed to parse StockX product", error=str(e))
            return None


class GOATSource(DataSource):
    """
    GOAT data source - fetches pricing and product info
    """
    
    BASE_URL = "https://www.goat.com"
    API_URL = "https://www.goat.com/api/v1"
    ALGOLIA_URL = "https://2fwotdvm2o-dsn.algolia.net/1/indexes"
    
    def __init__(self):
        super().__init__(cache_ttl_minutes=15)
        self._min_delay = 3.0
    
    async def fetch_trending(self, limit: int = 50) -> List[ExternalProduct]:
        """Fetch trending sneakers from GOAT"""
        cache_key = self._get_cache_key("trending", limit)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        products = []
        
        try:
            # Use Algolia search endpoint (commonly used by GOAT)
            url = f"{self.ALGOLIA_URL}/product_variants_v2/query"
            
            headers = {
                "x-algolia-api-key": "ac96de6fef0e02bb95d433d8d5c7038a",  # Public API key
                "x-algolia-application-id": "2FWOTDVM2O",
                "Content-Type": "application/json",
            }
            
            payload = {
                "query": "",
                "hitsPerPage": min(limit, 50),
                "facetFilters": [["product_category:shoes"]],
                "sortFacetValuesBy": "count",
            }
            
            session = await self._get_session()
            response = await session.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.warning("GOAT trending request failed", status=response.status_code)
                return products
            
            data = response.json()
            
            for hit in data.get("hits", []):
                product = self._parse_product(hit)
                if product:
                    products.append(product)
            
            self._set_cached(cache_key, products)
            logger.info("Fetched GOAT trending", count=len(products))
            
        except Exception as e:
            logger.error("GOAT fetch_trending error", error=str(e))
        
        return products
    
    async def search(self, query: str, limit: int = 20) -> List[ExternalProduct]:
        """Search GOAT for products"""
        cache_key = self._get_cache_key("search", query, limit)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        products = []
        
        try:
            url = f"{self.ALGOLIA_URL}/product_variants_v2/query"
            
            headers = {
                "x-algolia-api-key": "ac96de6fef0e02bb95d433d8d5c7038a",
                "x-algolia-application-id": "2FWOTDVM2O",
                "Content-Type": "application/json",
            }
            
            payload = {
                "query": query,
                "hitsPerPage": min(limit, 50),
                "facetFilters": [["product_category:shoes"]],
            }
            
            session = await self._get_session()
            response = await session.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                for hit in data.get("hits", []):
                    product = self._parse_product(hit)
                    if product:
                        products.append(product)
            
            self._set_cached(cache_key, products)
            logger.info("GOAT search complete", query=query, count=len(products))
            
        except Exception as e:
            logger.error("GOAT search error", error=str(e), query=query)
        
        return products
    
    async def get_price(self, style_code: str) -> Optional[ExternalProduct]:
        """Get pricing for a specific style code"""
        results = await self.search(style_code, limit=5)
        
        style_upper = style_code.upper().replace("-", "")
        for product in results:
            if product.style_code:
                product_style = product.style_code.upper().replace("-", "")
                if product_style == style_upper:
                    return product
        
        return results[0] if results else None
    
    def _parse_product(self, data: Dict) -> Optional[ExternalProduct]:
        """Parse GOAT product data"""
        try:
            retail_price = float(data.get("retail_price_cents", 0) or 0) / 100
            market_price = float(data.get("lowest_price_cents", 0) or 0) / 100
            
            price_premium = 0.0
            if retail_price > 0 and market_price > 0:
                price_premium = ((market_price - retail_price) / retail_price) * 100
            
            product = ExternalProduct(
                name=data.get("name", ""),
                brand=data.get("brand_name", ""),
                style_code=data.get("sku", ""),
                colorway=data.get("color", ""),
                retail_price=retail_price,
                market_price=market_price,
                last_sale_price=market_price,  # GOAT doesn't expose last sale easily
                price_premium=price_premium,
                image_url=data.get("main_picture_url"),
                product_url=f"{self.BASE_URL}/sneakers/{data.get('slug', '')}",
                source="goat",
            )
            
            product.generate_keywords()
            return product
            
        except Exception as e:
            logger.warning("Failed to parse GOAT product", error=str(e))
            return None


class MonitorLearnedSource(DataSource):
    """
    Learns products from monitor discoveries
    Builds a database of products found across monitored stores
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        super().__init__(cache_ttl_minutes=60)
        self._learned_products: Dict[str, ExternalProduct] = {}
        self._seen_titles: Set[str] = set()
        self.storage_path = storage_path
    
    def add_discovered_product(
        self,
        title: str,
        price: float,
        url: str,
        sku: Optional[str] = None,
        sizes: Optional[List[str]] = None,
        image_url: Optional[str] = None,
        store_name: Optional[str] = None,
    ) -> Optional[ExternalProduct]:
        """Add a product discovered by monitors"""
        
        # Normalize title for deduplication
        title_normalized = self._normalize_title(title)
        
        if title_normalized in self._seen_titles:
            # Update existing product if price changed
            existing = self._learned_products.get(title_normalized)
            if existing and price != existing.retail_price:
                existing.retail_price = price
            return existing
        
        self._seen_titles.add(title_normalized)
        
        # Extract brand from title
        brand = self._extract_brand(title)
        
        # Extract style code from title or SKU
        style_code = sku or self._extract_style_code(title)
        
        product = ExternalProduct(
            name=title,
            brand=brand,
            style_code=style_code,
            retail_price=price,
            market_price=0.0,  # Unknown for newly discovered
            image_url=image_url,
            product_url=url,
            source=f"monitor:{store_name}" if store_name else "monitor",
        )
        
        product.generate_keywords()
        self._learned_products[title_normalized] = product
        
        logger.debug("Learned new product", title=title[:50], brand=brand)
        return product
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        # Remove special characters and extra spaces
        normalized = re.sub(r'[^\w\s]', ' ', title.lower())
        normalized = ' '.join(normalized.split())
        return normalized
    
    def _extract_brand(self, title: str) -> str:
        """Extract brand from product title"""
        title_lower = title.lower()
        
        brands = [
            ("jordan", ["jordan", "air jordan", "aj1", "aj4", "aj11"]),
            ("nike", ["nike", "air force", "dunk", "air max"]),
            ("adidas", ["adidas", "yeezy"]),
            ("yeezy", ["yeezy"]),
            ("new balance", ["new balance", "nb 550", "nb 2002"]),
            ("asics", ["asics", "gel lyte", "gel kayano"]),
            ("converse", ["converse", "chuck"]),
            ("puma", ["puma"]),
            ("reebok", ["reebok"]),
            ("vans", ["vans", "old skool"]),
        ]
        
        for brand, patterns in brands:
            for pattern in patterns:
                if pattern in title_lower:
                    return brand
        
        return "unknown"
    
    def _extract_style_code(self, title: str) -> Optional[str]:
        """Extract style code from title"""
        # Common Nike/Jordan style code pattern: XX0000-000
        match = re.search(r'[A-Z]{2}\d{4}[-\s]?\d{3}', title.upper())
        if match:
            return match.group().replace(" ", "-")
        
        # Adidas pattern: XX0000
        match = re.search(r'[A-Z]{2}\d{4,5}', title.upper())
        if match:
            return match.group()
        
        return None
    
    async def fetch_trending(self, limit: int = 50) -> List[ExternalProduct]:
        """Return most recently learned products"""
        products = list(self._learned_products.values())
        # Sort by most recent
        products.sort(key=lambda p: p.fetched_at, reverse=True)
        return products[:limit]
    
    async def search(self, query: str, limit: int = 20) -> List[ExternalProduct]:
        """Search learned products"""
        query_lower = query.lower()
        matches = []
        
        for product in self._learned_products.values():
            if query_lower in product.name.lower():
                matches.append(product)
            elif product.style_code and query_lower in product.style_code.lower():
                matches.append(product)
        
        return matches[:limit]
    
    async def get_price(self, style_code: str) -> Optional[ExternalProduct]:
        """Get learned product by style code"""
        style_upper = style_code.upper().replace("-", "")
        
        for product in self._learned_products.values():
            if product.style_code:
                if product.style_code.upper().replace("-", "") == style_upper:
                    return product
        
        return None
    
    def get_all_products(self) -> List[ExternalProduct]:
        """Get all learned products"""
        return list(self._learned_products.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        products = list(self._learned_products.values())
        brands = {}
        for p in products:
            brands[p.brand] = brands.get(p.brand, 0) + 1
        
        return {
            "total_learned": len(products),
            "by_brand": brands,
            "with_style_code": sum(1 for p in products if p.style_code),
        }


class AggregatedDataSource:
    """
    Aggregates data from multiple sources
    Provides unified interface for fetching product data
    """
    
    def __init__(self):
        self.stockx = StockXSource()
        self.goat = GOATSource()
        self.learned = MonitorLearnedSource()
        
        self._all_sources = [self.stockx, self.goat]
        logger.info("AggregatedDataSource initialized")
    
    async def fetch_trending(self, limit: int = 50) -> List[ExternalProduct]:
        """Fetch trending products from all sources"""
        all_products = []
        
        # Fetch from both sources concurrently
        results = await asyncio.gather(
            self.stockx.fetch_trending(limit=limit),
            self.goat.fetch_trending(limit=limit),
            return_exceptions=True
        )
        
        for result in results:
            if isinstance(result, list):
                all_products.extend(result)
            elif isinstance(result, Exception):
                logger.warning("Source fetch failed", error=str(result))
        
        # Deduplicate by style code
        seen_styles = set()
        unique_products = []
        
        for product in all_products:
            key = product.style_code or product.name
            if key not in seen_styles:
                seen_styles.add(key)
                unique_products.append(product)
        
        # Sort by profit potential
        unique_products.sort(key=lambda p: p.profit_potential, reverse=True)
        
        return unique_products[:limit]
    
    async def search(self, query: str, limit: int = 20) -> List[ExternalProduct]:
        """Search all sources"""
        all_products = []
        
        results = await asyncio.gather(
            self.stockx.search(query, limit=limit),
            self.goat.search(query, limit=limit),
            self.learned.search(query, limit=limit),
            return_exceptions=True
        )
        
        for result in results:
            if isinstance(result, list):
                all_products.extend(result)
        
        # Deduplicate
        seen = set()
        unique = []
        for p in all_products:
            key = p.style_code or p.name
            if key not in seen:
                seen.add(key)
                unique.append(p)
        
        return unique[:limit]
    
    async def get_best_price(self, style_code: str) -> Optional[Dict[str, Any]]:
        """Get pricing from all sources and compare"""
        results = await asyncio.gather(
            self.stockx.get_price(style_code),
            self.goat.get_price(style_code),
            return_exceptions=True
        )
        
        prices = {}
        for result in results:
            if isinstance(result, ExternalProduct):
                prices[result.source] = {
                    "market_price": result.market_price,
                    "retail_price": result.retail_price,
                    "product": result,
                }
        
        if not prices:
            return None
        
        # Find lowest price
        lowest_source = min(prices.keys(), key=lambda s: prices[s]["market_price"])
        
        return {
            "style_code": style_code,
            "prices": prices,
            "best_source": lowest_source,
            "best_price": prices[lowest_source]["market_price"],
        }
    
    def add_learned_product(self, **kwargs) -> Optional[ExternalProduct]:
        """Add a product discovered by monitors"""
        return self.learned.add_discovered_product(**kwargs)
    
    async def close(self):
        """Close all source sessions"""
        await asyncio.gather(
            self.stockx.close(),
            self.goat.close(),
            return_exceptions=True
        )


# Convenience function to create default aggregated source
def create_data_source() -> AggregatedDataSource:
    """Create and return the default aggregated data source"""
    return AggregatedDataSource()
