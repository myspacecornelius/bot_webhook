"""
Enhanced Restock Tracking System
Tracks restock history, patterns, and predictions
"""

import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class RestockEvent:
    """A single restock event"""
    product_id: str
    product_title: str
    store_name: str
    store_url: str
    sizes_restocked: List[str]
    timestamp: datetime
    price: Optional[float] = None
    image_url: Optional[str] = None
    variant_ids: List[int] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "product_title": self.product_title,
            "store_name": self.store_name,
            "store_url": self.store_url,
            "sizes_restocked": self.sizes_restocked,
            "timestamp": self.timestamp.isoformat(),
            "price": self.price,
            "image_url": self.image_url,
            "variant_ids": self.variant_ids,
        }


@dataclass
class RestockPattern:
    """Detected restock pattern for a product"""
    product_id: str
    product_title: str
    store_name: str
    restock_count: int = 0
    last_restock: Optional[datetime] = None
    average_interval_hours: Optional[float] = None
    restock_times: List[datetime] = field(default_factory=list)
    common_sizes: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
    def predict_next_restock(self) -> Optional[datetime]:
        """Predict when next restock might occur"""
        if not self.average_interval_hours or not self.last_restock:
            return None
        
        return self.last_restock + timedelta(hours=self.average_interval_hours)
    
    def to_dict(self) -> dict:
        next_restock = self.predict_next_restock()
        return {
            "product_id": self.product_id,
            "product_title": self.product_title,
            "store_name": self.store_name,
            "restock_count": self.restock_count,
            "last_restock": self.last_restock.isoformat() if self.last_restock else None,
            "average_interval_hours": self.average_interval_hours,
            "next_predicted_restock": next_restock.isoformat() if next_restock else None,
            "common_sizes": self.common_sizes,
            "confidence_score": self.confidence_score,
        }


class RestockTracker:
    """
    Tracks and analyzes restock events
    
    Features:
    - Historical restock tracking
    - Pattern detection
    - Restock prediction
    - Size availability analysis
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        
        # Storage
        self._restock_history: List[RestockEvent] = []
        self._product_patterns: Dict[str, RestockPattern] = {}
        self._size_frequency: Dict[str, Dict[str, int]] = {}  # product_id -> {size: count}
        
        # Tracking
        self._product_first_seen: Dict[str, datetime] = {}
        self._product_last_oos: Dict[str, datetime] = {}
        
        logger.info("RestockTracker initialized")
    
    def record_restock(
        self,
        product_id: str,
        product_title: str,
        store_name: str,
        store_url: str,
        sizes_restocked: List[str],
        price: Optional[float] = None,
        image_url: Optional[str] = None,
        variant_ids: Optional[List[int]] = None
    ):
        """Record a restock event"""
        event = RestockEvent(
            product_id=product_id,
            product_title=product_title,
            store_name=store_name,
            store_url=store_url,
            sizes_restocked=sizes_restocked,
            timestamp=datetime.now(),
            price=price,
            image_url=image_url,
            variant_ids=variant_ids or []
        )
        
        # Add to history
        self._restock_history.append(event)
        
        # Trim history if needed
        if len(self._restock_history) > self.max_history:
            self._restock_history = self._restock_history[-self.max_history:]
        
        # Update patterns
        self._update_pattern(event)
        
        # Update size frequency
        self._update_size_frequency(product_id, sizes_restocked)
        
        logger.info(
            "Restock recorded",
            product=product_title[:50],
            store=store_name,
            sizes=sizes_restocked[:5]
        )
    
    def _update_pattern(self, event: RestockEvent):
        """Update restock pattern for a product"""
        key = f"{event.store_name}:{event.product_id}"
        
        if key not in self._product_patterns:
            self._product_patterns[key] = RestockPattern(
                product_id=event.product_id,
                product_title=event.product_title,
                store_name=event.store_name
            )
        
        pattern = self._product_patterns[key]
        pattern.restock_count += 1
        pattern.restock_times.append(event.timestamp)
        pattern.last_restock = event.timestamp
        
        # Calculate average interval if we have multiple restocks
        if len(pattern.restock_times) >= 2:
            intervals = []
            for i in range(1, len(pattern.restock_times)):
                delta = pattern.restock_times[i] - pattern.restock_times[i-1]
                intervals.append(delta.total_seconds() / 3600)  # hours
            
            pattern.average_interval_hours = sum(intervals) / len(intervals)
            
            # Calculate confidence based on consistency
            if len(intervals) >= 3:
                variance = sum((x - pattern.average_interval_hours) ** 2 for x in intervals) / len(intervals)
                std_dev = variance ** 0.5
                # Lower std dev = higher confidence
                pattern.confidence_score = max(0, 1 - (std_dev / pattern.average_interval_hours))
    
    def _update_size_frequency(self, product_id: str, sizes: List[str]):
        """Track which sizes restock most frequently"""
        if product_id not in self._size_frequency:
            self._size_frequency[product_id] = {}
        
        for size in sizes:
            self._size_frequency[product_id][size] = self._size_frequency[product_id].get(size, 0) + 1
    
    def get_restock_history(
        self,
        store_name: Optional[str] = None,
        product_id: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[RestockEvent]:
        """Get restock history with filters"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        filtered = [
            event for event in self._restock_history
            if event.timestamp >= cutoff
            and (not store_name or event.store_name == store_name)
            and (not product_id or event.product_id == product_id)
        ]
        
        # Sort by timestamp descending
        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        
        return filtered[:limit]
    
    def get_pattern(self, store_name: str, product_id: str) -> Optional[RestockPattern]:
        """Get restock pattern for a specific product"""
        key = f"{store_name}:{product_id}"
        return self._product_patterns.get(key)
    
    def get_all_patterns(self, min_restocks: int = 2) -> List[RestockPattern]:
        """Get all patterns with minimum restock count"""
        patterns = [
            p for p in self._product_patterns.values()
            if p.restock_count >= min_restocks
        ]
        
        # Sort by confidence and restock count
        patterns.sort(key=lambda x: (x.confidence_score, x.restock_count), reverse=True)
        
        return patterns
    
    def get_predicted_restocks(self, hours_ahead: int = 24) -> List[Dict]:
        """Get products predicted to restock in the next N hours"""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours_ahead)
        
        predictions = []
        
        for pattern in self._product_patterns.values():
            next_restock = pattern.predict_next_restock()
            
            if next_restock and now <= next_restock <= cutoff:
                predictions.append({
                    "product_title": pattern.product_title,
                    "store_name": pattern.store_name,
                    "predicted_time": next_restock,
                    "confidence": pattern.confidence_score,
                    "hours_until": (next_restock - now).total_seconds() / 3600,
                    "common_sizes": pattern.common_sizes,
                })
        
        # Sort by time
        predictions.sort(key=lambda x: x["predicted_time"])
        
        return predictions
    
    def get_hot_sizes(self, product_id: str, top_n: int = 5) -> List[tuple]:
        """Get most frequently restocked sizes for a product"""
        if product_id not in self._size_frequency:
            return []
        
        size_counts = self._size_frequency[product_id]
        sorted_sizes = sorted(size_counts.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_sizes[:top_n]
    
    def get_stats(self) -> Dict:
        """Get overall restock statistics"""
        now = datetime.now()
        
        # Recent restocks
        last_24h = len(self.get_restock_history(hours=24))
        last_7d = len(self.get_restock_history(hours=168))
        
        # Patterns
        total_patterns = len(self._product_patterns)
        high_confidence = len([p for p in self._product_patterns.values() if p.confidence_score > 0.7])
        
        # Predictions
        upcoming = len(self.get_predicted_restocks(hours_ahead=24))
        
        return {
            "total_restocks_tracked": len(self._restock_history),
            "restocks_last_24h": last_24h,
            "restocks_last_7d": last_7d,
            "patterns_detected": total_patterns,
            "high_confidence_patterns": high_confidence,
            "predicted_restocks_24h": upcoming,
            "unique_products": len(self._size_frequency),
        }
    
    def clear_old_history(self, days: int = 30):
        """Clear restock history older than N days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        original_count = len(self._restock_history)
        self._restock_history = [
            event for event in self._restock_history
            if event.timestamp >= cutoff
        ]
        
        removed = original_count - len(self._restock_history)
        
        if removed > 0:
            logger.info(f"Cleared {removed} old restock events")
        
        return removed


# Global instance
restock_tracker = RestockTracker()
