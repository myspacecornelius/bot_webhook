"""
Monitor service — orchestrates monitor lifecycle, config persistence, restock analysis.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

import structlog

from ..domain.errors import NotFoundError
from ..domain.models import (
    AutoTaskConfig,
    FootsiteSetup,
    ShopifySetup,
    ShopifyStoreAdd,
    ShopifyStoreUpdate,
)
from ..monitors.manager import monitor_manager
from ..monitors.products import product_db

logger = structlog.get_logger()


class MonitorService:
    """Monitor lifecycle, Shopify store management, and restock analysis."""

    # ── Lifecycle ─────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        return monitor_manager.get_stats()

    async def start(self) -> None:
        await monitor_manager.start()

    async def stop(self) -> None:
        await monitor_manager.stop()

    # ── Shopify ───────────────────────────────────────────────

    def setup_shopify(self, data: ShopifySetup) -> Dict[str, Any]:
        monitor_manager.setup_shopify(
            target_sizes=data.target_sizes, use_defaults=data.use_defaults
        )
        store_count = (
            len(monitor_manager.shopify_monitor.stores)
            if monitor_manager.shopify_monitor
            else 0
        )
        return {"message": "Shopify monitoring configured", "stores": store_count}

    def add_shopify_store(self, data: ShopifyStoreAdd) -> Dict[str, str]:
        monitor_manager.add_shopify_store(
            data.name, data.url, data.delay_ms, data.target_sizes
        )
        return {"message": f"Store '{data.name}' added"}

    def get_shopify_stores(self) -> Dict[str, Any]:
        stores = []
        if monitor_manager.shopify_monitor:
            for store_id, monitor in monitor_manager.shopify_monitor.stores.items():
                store = monitor.store
                stores.append(
                    {
                        "id": store_id,
                        "name": store.name,
                        "url": store.url,
                        "enabled": store.enabled,
                        "delay_ms": store.delay_ms,
                        "target_sizes": monitor.target_sizes or [],
                        "last_check": (
                            store.last_check.isoformat() if store.last_check else None
                        ),
                        "success_count": store.success_count,
                        "error_count": store.error_count,
                        "products_found": store.products_found,
                    }
                )
        return {"stores": stores}

    def update_shopify_store(
        self, store_id: str, updates: ShopifyStoreUpdate
    ) -> Dict[str, str]:
        if not monitor_manager.shopify_monitor:
            raise NotFoundError("Shopify monitor")
        if store_id not in monitor_manager.shopify_monitor.stores:
            raise NotFoundError("Store", store_id)

        monitor = monitor_manager.shopify_monitor.stores[store_id]
        if updates.enabled is not None:
            monitor.store.enabled = updates.enabled
        if updates.delay_ms is not None:
            monitor.store.delay_ms = updates.delay_ms
        if updates.target_sizes is not None:
            monitor.target_sizes = updates.target_sizes

        return {"message": f"Store '{monitor.store.name}' updated"}

    async def delete_shopify_store(self, store_id: str) -> Dict[str, str]:
        if not monitor_manager.shopify_monitor:
            raise NotFoundError("Shopify monitor")
        if store_id not in monitor_manager.shopify_monitor.stores:
            raise NotFoundError("Store", store_id)

        monitor = monitor_manager.shopify_monitor.stores.pop(store_id)
        await monitor.close()
        return {"message": f"Store '{monitor.store.name}' deleted"}

    # ── Footsites ─────────────────────────────────────────────

    def setup_footsites(self, data: FootsiteSetup) -> Dict[str, str]:
        monitor_manager.setup_footsites(
            sites=data.sites,
            keywords=data.keywords,
            target_sizes=data.target_sizes,
            delay_ms=data.delay_ms,
        )
        return {"message": "Footsite monitoring configured"}

    # ── Auto Tasks ────────────────────────────────────────────

    def configure_auto_tasks(self, data: AutoTaskConfig) -> Dict[str, Any]:
        monitor_manager.enable_auto_tasks(
            data.enabled, data.min_confidence, data.min_priority
        )
        return {"message": "Auto-task configuration updated", "enabled": data.enabled}

    # ── Events ────────────────────────────────────────────────

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        events = monitor_manager.get_recent_events(limit)
        return [
            {
                "type": e.event_type,
                "source": e.source,
                "store": e.store_name,
                "product": e.product.title,
                "url": e.product.url,
                "sizes": e.product.sizes_available[:10],
                "price": e.product.price,
                "matched": e.matched_product.name if e.matched_product else None,
                "confidence": e.match_confidence,
                "priority": e.priority,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ]

    def get_high_priority_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        events = monitor_manager.get_high_priority_events(limit)
        return [
            {
                "type": e.event_type,
                "source": e.source,
                "store": e.store_name,
                "product": e.product.title,
                "url": e.product.url,
                "sizes": e.product.sizes_available[:10],
                "matched": e.matched_product.name if e.matched_product else None,
                "profit": (
                    e.matched_product.profit_dollar if e.matched_product else None
                ),
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ]

    # ── Rate Limits ───────────────────────────────────────────

    def get_rate_limits(self) -> Dict[str, Any]:
        stats = {}
        if monitor_manager.shopify_monitor:
            for store in monitor_manager.shopify_monitor.stores:
                stats[store.name] = {
                    "url": store.url,
                    "delay_ms": store.delay_ms,
                    "request_count": getattr(store, "_request_count", 0),
                    "rate_limited": getattr(store, "_rate_limited", False),
                    "last_request": getattr(store, "_last_request", None),
                }
        return {"stores": stats}

    # ── Config Persistence ────────────────────────────────────

    async def save_config(self) -> Dict[str, Any]:
        import uuid

        from ..utils.database import db

        if not monitor_manager.shopify_monitor:
            return {"message": "No monitor configuration to save", "count": 0}

        saved_count = 0
        async with db.session() as session:
            for store in monitor_manager.shopify_monitor.stores:
                existing = await session.execute(
                    "SELECT id FROM monitor_stores WHERE url = :url",
                    {"url": store.url},
                )
                row = existing.first()

                if row:
                    await session.execute(
                        """UPDATE monitor_stores SET
                           name = :name, enabled = :enabled, delay_ms = :delay_ms,
                           target_sizes = :target_sizes, updated_at = CURRENT_TIMESTAMP
                           WHERE id = :id""",
                        {
                            "id": row[0],
                            "name": store.name,
                            "enabled": True,
                            "delay_ms": store.delay_ms,
                            "target_sizes": json.dumps(store.target_sizes or []),
                        },
                    )
                else:
                    await session.execute(
                        """INSERT INTO monitor_stores (id, name, url, enabled, delay_ms, target_sizes)
                           VALUES (:id, :name, :url, :enabled, :delay_ms, :target_sizes)""",
                        {
                            "id": str(uuid.uuid4()),
                            "name": store.name,
                            "url": store.url,
                            "enabled": True,
                            "delay_ms": store.delay_ms,
                            "target_sizes": json.dumps(store.target_sizes or []),
                        },
                    )
                saved_count += 1
            await session.commit()

        return {
            "message": f"Saved {saved_count} monitor configurations",
            "count": saved_count,
        }

    async def load_config(self) -> Dict[str, Any]:
        from ..utils.database import db

        async with db.session() as session:
            result = await session.execute(
                "SELECT id, name, url, enabled, delay_ms, target_sizes "
                "FROM monitor_stores WHERE enabled = 1"
            )
            rows = result.fetchall()

        stores = [
            {
                "id": row[0],
                "name": row[1],
                "url": row[2],
                "enabled": bool(row[3]),
                "delay_ms": row[4],
                "target_sizes": json.loads(row[5]) if row[5] else [],
            }
            for row in rows
        ]
        return {"stores": stores, "count": len(stores)}

    async def restore_config(self) -> Dict[str, Any]:
        from ..utils.database import db

        async with db.session() as session:
            result = await session.execute(
                "SELECT name, url, delay_ms, target_sizes "
                "FROM monitor_stores WHERE enabled = 1"
            )
            rows = result.fetchall()

        if not rows:
            return {"message": "No saved configuration to restore", "count": 0}

        for row in rows:
            name, url, delay_ms, target_sizes = row
            sizes = json.loads(target_sizes) if target_sizes else None
            monitor_manager.add_shopify_store(name, url, delay_ms, sizes)

        return {"message": f"Restored {len(rows)} monitors", "count": len(rows)}

    # ── Restock Analysis ──────────────────────────────────────

    def get_restock_history(self, hours: int = 24, limit: int = 50) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(hours=hours)
        history = []

        for event in monitor_manager._events:
            if event.event_type == "restock" and event.timestamp >= cutoff:
                history.append(
                    {
                        "product_id": event.product.sku or "",
                        "product_title": event.product.title,
                        "store_name": event.store_name,
                        "sizes_restocked": event.product.sizes_available[:10],
                        "timestamp": event.timestamp.isoformat(),
                        "price": event.product.price,
                        "image_url": event.product.image_url,
                    }
                )

        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"history": history[:limit]}

    def get_restock_stats(self) -> Dict[str, Any]:
        now = datetime.now()
        restocks_24h = 0
        restocks_7d = 0
        product_counts: Dict[str, int] = defaultdict(int)

        for event in monitor_manager._events:
            if event.event_type == "restock":
                age = now - event.timestamp
                if age <= timedelta(hours=24):
                    restocks_24h += 1
                if age <= timedelta(days=7):
                    restocks_7d += 1
                    product_counts[event.product.title] += 1

        patterns_detected = sum(1 for c in product_counts.values() if c >= 2)

        return {
            "restocks_last_24h": restocks_24h,
            "restocks_last_7d": restocks_7d,
            "patterns_detected": patterns_detected,
            "predicted_restocks_24h": patterns_detected,
        }

    def get_restock_patterns(self, days: int = 7) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)

        product_restocks: Dict[str, list] = defaultdict(list)
        for event in monitor_manager._events:
            if event.event_type == "restock" and event.timestamp >= cutoff:
                key = f"{event.store_name}:{event.product.title}"
                product_restocks[key].append(event)

        patterns = []
        for key, events in product_restocks.items():
            if len(events) < 2:
                continue

            store_name, product_title = key.split(":", 1)
            events.sort(key=lambda e: e.timestamp)

            intervals = [
                (events[i].timestamp - events[i - 1].timestamp).total_seconds() / 3600
                for i in range(1, len(events))
            ]
            avg_interval = sum(intervals) / len(intervals) if intervals else None

            next_predicted = None
            confidence = 0.0
            if avg_interval and len(events) >= 2:
                next_predicted = (
                    events[-1].timestamp + timedelta(hours=avg_interval)
                ).isoformat()
                confidence = min(0.9, 0.3 + 0.15 * len(events))

            patterns.append(
                {
                    "product_title": product_title,
                    "store_name": store_name,
                    "restock_count": len(events),
                    "last_restock": (
                        events[-1].timestamp.isoformat() if events else None
                    ),
                    "average_interval_hours": (
                        round(avg_interval, 1) if avg_interval else None
                    ),
                    "next_predicted_restock": next_predicted,
                    "confidence_score": round(confidence, 2),
                }
            )

        patterns.sort(key=lambda x: x["restock_count"], reverse=True)
        return {"patterns": patterns}

    # ── Curated Products ──────────────────────────────────────

    def get_curated_products(self) -> Dict[str, Any]:
        return {
            "stats": product_db.get_stats(),
            "products": [p.to_dict() for p in product_db.get_enabled()],
        }

    def get_high_priority_products(self) -> Dict[str, Any]:
        return {"products": [p.to_dict() for p in product_db.get_high_priority()]}

    def get_profitable_products(self, min_profit: float = 50) -> Dict[str, Any]:
        return {
            "products": [p.to_dict() for p in product_db.get_profitable(min_profit)]
        }

    def load_products_json(self, path: str) -> Dict[str, Any]:
        count = monitor_manager.load_products_from_json(path)
        return {"message": f"Loaded {count} products", "count": count}


monitor_service = MonitorService()
