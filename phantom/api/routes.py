"""
FastAPI Routes for Phantom Bot Web UI

Thin handler layer — delegates all business logic to services/.
Models imported from domain/models.py.
Error handling via domain/errors.py + api/error_handlers.py.
"""

import asyncio
import json
from typing import Optional, Set

from fastapi import (
    BackgroundTasks,
    FastAPI,
    Header,
    HTTPException,
    Request,
    UploadFile,
    File,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
import structlog

from ..core.engine import engine
from ..domain.errors import ServiceUnavailableError, UnauthorizedError
from ..domain.models import (
    AutoTaskConfig,
    CheckoutRequest,
    FootsiteSetup,
    LicenseValidation,
    ProfileCreate,
    ProxyGroupCreate,
    QuickTaskBatch,
    QuickTaskCreate,
    ShopifySetup,
    ShopifyStoreAdd,
    ShopifyStoreUpdate,
    TaskCreate,
)
from ..services.task_service import task_service
from ..services.profile_service import profile_service
from ..services.monitor_service import monitor_service
from ..services.webhook_service import webhook_service
from .error_handlers import install_error_handlers
from .middleware import RequestIDMiddleware

logger = structlog.get_logger()


# ── WebSocket Connection Manager ─────────────────────────────


class ConnectionManager:
    """Manages WebSocket connections for real-time event broadcasting."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("ws_connected", total=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info("ws_disconnected", total=len(self.active_connections))

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        data = json.dumps(message)
        disconnected = []
        for conn in self.active_connections:
            try:
                await conn.send_text(data)
            except Exception:
                disconnected.append(conn)
        for conn in disconnected:
            self.active_connections.discard(conn)


ws_manager = ConnectionManager()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title="Phantom Bot API",
        description="Advanced Sneaker Automation Suite",
        version="1.0.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Central error handlers (domain → HTTP mapping)
    install_error_handlers(app)

    # Request ID + duration logging
    app.add_middleware(RequestIDMiddleware)

    # ============ Authentication ============

    @app.post("/api/auth/validate")
    async def validate_license(data: LicenseValidation):
        """Validate a license key."""
        print(f"DEBUG: validating license key: {data.license_key}")  # DEBUG LOG
        if not data.license_key or len(data.license_key) < 4:
            print("DEBUG: license key too short")
            raise UnauthorizedError("Invalid license key")
        return {
            "valid": True,
            "user": {
                "license_key": data.license_key[:8] + "...",
                "tier": "pro",
                "expires_at": "2027-12-31T23:59:59Z",
            },
        }

    @app.post("/api/auth/checkout")
    async def create_checkout_session(data: CheckoutRequest):
        """Create a checkout session (placeholder for Stripe)."""
        return {
            "session_id": "demo_session",
            "url": f"https://phantom-bot.com/checkout?tier={data.tier}&email={data.email}",
        }

    # ============ Status ============

    @app.get("/api/status")
    async def get_status():
        return engine.get_status()

    @app.post("/api/start")
    async def start_engine(background_tasks: BackgroundTasks):
        background_tasks.add_task(engine.start)
        return {"message": "Engine starting..."}

    @app.post("/api/stop")
    async def stop_engine(background_tasks: BackgroundTasks):
        background_tasks.add_task(engine.stop)
        return {"message": "Engine stopping..."}

    # ============ Profiles ============

    @app.get("/api/profiles")
    async def list_profiles():
        return profile_service.list_profiles()

    @app.get("/api/profiles/{profile_id}")
    async def get_profile(profile_id: str):
        return profile_service.get_profile(profile_id)

    @app.post("/api/profiles")
    async def create_profile(data: ProfileCreate):
        return profile_service.create_profile(data)

    @app.delete("/api/profiles/{profile_id}")
    async def delete_profile(profile_id: str):
        return profile_service.delete_profile(profile_id)

    @app.post("/api/profiles/import")
    async def import_profiles(file: UploadFile = File(...)):
        content = await file.read()
        return profile_service.import_profiles(content, file.filename or "")

    # ============ Proxies ============

    @app.get("/api/proxies")
    async def list_proxies():
        return {
            "stats": engine.proxy_manager.get_stats(),
            "groups": list(engine.proxy_manager.groups.keys()),
        }

    @app.post("/api/proxies/groups")
    async def create_proxy_group(data: ProxyGroupCreate):
        ids = engine.proxy_manager.add_proxies_from_string(data.proxies, data.name)
        return {"group": data.name, "count": len(ids)}

    @app.post("/api/proxies/test")
    async def test_proxies(group_id: Optional[str] = None):
        await engine.proxy_manager.test_all_proxies(group_id)
        return engine.proxy_manager.get_stats(group_id)

    @app.delete("/api/proxies/groups/{group_id}")
    async def delete_proxy_group(group_id: str):
        from ..domain.errors import NotFoundError

        if group_id in engine.proxy_manager.groups:
            for proxy_id in list(engine.proxy_manager.groups[group_id]):
                engine.proxy_manager.remove_proxy(proxy_id)
            del engine.proxy_manager.groups[group_id]
            return {"message": "Group deleted"}
        raise NotFoundError("Proxy group", group_id)

    # ============ Tasks ============

    @app.get("/api/tasks")
    async def list_tasks():
        return await task_service.list_tasks()

    @app.post("/api/tasks")
    async def create_task(data: TaskCreate):
        return task_service.create_task(data)

    @app.post("/api/tasks/{task_id}/start")
    async def start_task(task_id: str, background_tasks: BackgroundTasks):
        background_tasks.add_task(task_service.start_task, task_id)
        return {"message": "Task starting..."}

    @app.post("/api/tasks/{task_id}/stop")
    async def stop_task(task_id: str):
        return task_service.stop_task(task_id)

    @app.delete("/api/tasks/{task_id}")
    async def delete_task(task_id: str):
        return task_service.delete_task(task_id)

    @app.post("/api/tasks/start-all")
    async def start_all_tasks(background_tasks: BackgroundTasks):
        background_tasks.add_task(task_service.start_all)
        return {"message": "Starting all tasks..."}

    @app.post("/api/tasks/stop-all")
    async def stop_all_tasks(background_tasks: BackgroundTasks):
        background_tasks.add_task(task_service.stop_all)
        return {"message": "Stopping all tasks..."}

    @app.post("/api/tasks/quick")
    async def create_quick_task(
        data: QuickTaskCreate, background_tasks: BackgroundTasks
    ):
        task_ids = task_service.create_quick_task(data)
        if data.auto_start:
            for tid in task_ids:
                background_tasks.add_task(task_service.start_task, tid)
        return {
            "id": task_ids[0] if len(task_ids) == 1 else task_ids,
            "message": f"Created {len(task_ids)} quick task(s)",
        }

    @app.post("/api/tasks/quick-batch")
    async def create_quick_tasks_batch(
        data: QuickTaskBatch, background_tasks: BackgroundTasks
    ):
        all_ids = []
        for url in data.urls:
            single = QuickTaskCreate(
                url=url, sizes=data.sizes, mode=data.mode, auto_start=data.auto_start
            )
            ids = task_service.create_quick_task(single)
            all_ids.extend(ids)
            if data.auto_start:
                for tid in ids:
                    background_tasks.add_task(task_service.start_task, tid)
        return {"ids": all_ids, "message": f"Created {len(all_ids)} tasks"}

    # ============ Analytics ============

    @app.get("/api/analytics/checkout")
    async def get_checkout_analytics():
        return task_service.get_checkout_analytics()

    # ============ Intelligence ============

    @app.get("/api/intelligence/trending")
    async def get_trending():
        if engine._intelligence:
            trending = await engine._intelligence.price_tracker.get_trending_products()
            return {"trending": trending}
        return {"trending": []}

    @app.post("/api/intelligence/research")
    async def research_product(name: str, sku: str, retail_price: float):
        if not engine._intelligence:
            raise ServiceUnavailableError("Intelligence module")
        research = await engine._intelligence.research_product(name, sku, retail_price)
        return {
            "name": research.name,
            "sku": research.sku,
            "keywords": research.keywords,
            "sites": research.recommended_sites,
            "hype_score": research.hype_score,
            "profit": research.profit_analysis.estimated_profit
            if research.profit_analysis
            else None,
        }

    # ============ Captcha ============

    @app.get("/api/captcha/balances")
    async def get_captcha_balances():
        if engine._captcha_solver:
            return await engine._captcha_solver.get_balances()
        return {}

    # ============ Monitors ============

    @app.get("/api/monitors/status")
    async def get_monitors_status():
        return monitor_service.get_status()

    @app.post("/api/monitors/start")
    async def start_monitors(background_tasks: BackgroundTasks):
        background_tasks.add_task(monitor_service.start)
        return {"message": "Monitors starting..."}

    @app.post("/api/monitors/stop")
    async def stop_monitors(background_tasks: BackgroundTasks):
        background_tasks.add_task(monitor_service.stop)
        return {"message": "Monitors stopping..."}

    @app.post("/api/monitors/shopify/setup")
    async def setup_shopify_monitors(data: ShopifySetup):
        return monitor_service.setup_shopify(data)

    @app.post("/api/monitors/shopify/add-store")
    async def add_shopify_store(data: ShopifyStoreAdd):
        return monitor_service.add_shopify_store(data)

    @app.get("/api/monitors/shopify/stores")
    async def get_shopify_stores():
        return monitor_service.get_shopify_stores()

    @app.patch("/api/monitors/shopify/stores/{store_id}")
    async def update_shopify_store(store_id: str, updates: ShopifyStoreUpdate):
        return monitor_service.update_shopify_store(store_id, updates)

    @app.delete("/api/monitors/shopify/stores/{store_id}")
    async def delete_shopify_store(store_id: str):
        return await monitor_service.delete_shopify_store(store_id)

    @app.post("/api/monitors/footsites/setup")
    async def setup_footsite_monitors(data: FootsiteSetup):
        return monitor_service.setup_footsites(data)

    @app.post("/api/monitors/auto-tasks")
    async def configure_auto_tasks(data: AutoTaskConfig):
        return monitor_service.configure_auto_tasks(data)

    @app.get("/api/monitors/events")
    async def get_monitor_events(limit: int = 50):
        return {"count": limit, "events": monitor_service.get_recent_events(limit)}

    @app.get("/api/monitors/events/high-priority")
    async def get_high_priority_events(limit: int = 20):
        events = monitor_service.get_high_priority_events(limit)
        return {"count": len(events), "events": events}

    @app.get("/api/monitors/rate-limits")
    async def get_rate_limits():
        return monitor_service.get_rate_limits()

    @app.post("/api/monitors/config/save")
    async def save_monitor_config():
        return await monitor_service.save_config()

    @app.get("/api/monitors/config/load")
    async def load_monitor_config():
        return await monitor_service.load_config()

    @app.post("/api/monitors/config/restore")
    async def restore_monitor_config():
        return await monitor_service.restore_config()

    # ============ Restock ============

    @app.get("/api/monitors/restock-history")
    async def get_restock_history(hours: int = 24, limit: int = 50):
        return monitor_service.get_restock_history(hours, limit)

    @app.get("/api/monitors/restock-stats")
    async def get_restock_stats():
        return monitor_service.get_restock_stats()

    @app.get("/api/monitors/restock-patterns")
    async def get_restock_patterns(days: int = 7):
        return monitor_service.get_restock_patterns(days)

    # ============ Curated Products ============

    @app.get("/api/products/curated")
    async def get_curated_products():
        return monitor_service.get_curated_products()

    @app.get("/api/products/curated/high-priority")
    async def get_high_priority_products():
        return monitor_service.get_high_priority_products()

    @app.get("/api/products/curated/profitable")
    async def get_profitable_products(min_profit: float = 50):
        return monitor_service.get_profitable_products(min_profit)

    @app.post("/api/products/load-json")
    async def load_products_json(path: str):
        return monitor_service.load_products_json(path)

    # ============ Import/Export ============

    @app.post("/api/import/valor")
    async def import_valor(config_path: str):
        try:
            counts = await engine.import_valor_config(config_path)
            return {"message": "Import successful", **counts}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ============ Webhooks ============

    @app.post("/api/webhooks/{source}", tags=["webhooks"])
    async def receive_webhook(
        source: str,
        request: Request,
        x_webhook_signature: Optional[str] = Header(None),
        x_idempotency_key: Optional[str] = Header(None),
    ):
        """Receive and process an inbound webhook."""
        payload = await request.json()
        event = await webhook_service.receive(
            source=source,
            payload=payload,
            signature=x_webhook_signature,
            idempotency_key=x_idempotency_key,
        )
        return {
            "status": "accepted",
            "event_type": event.event_type,
            "webhook_id": event.webhook_id,
        }

    @app.get("/api/webhooks/stats", tags=["webhooks"])
    async def get_webhook_stats():
        """Get webhook processing statistics."""
        return webhook_service.get_stats()

    @app.get("/api/webhooks/events", tags=["webhooks"])
    async def get_webhook_events(limit: int = 50):
        """Get recent webhook events."""
        return {"events": webhook_service.get_recent_events(limit)}

    # ============ WebSocket ============

    @app.websocket("/ws/events")
    async def websocket_events(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_text(), timeout=30.0
                    )
                    if data == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except asyncio.TimeoutError:
                    await websocket.send_text(json.dumps({"type": "heartbeat"}))
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
        except Exception:
            ws_manager.disconnect(websocket)

    return app


# ── WebSocket helpers (used by other modules) ────────────────


async def broadcast_monitor_event(event_data: dict):
    """Broadcast a monitor event to all connected WebSocket clients."""
    await ws_manager.broadcast({"type": "monitor_event", "data": event_data})


def setup_websocket_broadcasts():
    """Wire up monitor events to WebSocket broadcasts."""
    from ..monitors.manager import monitor_manager

    try:
        if hasattr(monitor_manager, "on_event"):

            async def broadcast_wrapper(event):
                await broadcast_monitor_event(event)

            monitor_manager.on_event = broadcast_wrapper
            logger.info("ws_broadcasts_configured")
        else:
            logger.debug("monitor_manager_no_event_hooks")
    except Exception as e:
        logger.warning("ws_broadcast_setup_failed", error=str(e))
