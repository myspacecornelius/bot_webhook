"""
FastAPI Routes for Phantom Bot Web UI
"""

import asyncio
import json
from datetime import datetime
from typing import Optional, List, Set
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog

from ..core.engine import engine
from ..core.task import TaskConfig, TaskMode
from ..core.profile import Profile, Address, PaymentCard

logger = structlog.get_logger()


# Pydantic models for API
class ProfileCreate(BaseModel):
    name: str
    email: str
    phone: str = ""
    shipping_first_name: str
    shipping_last_name: str
    shipping_address1: str
    shipping_address2: str = ""
    shipping_city: str
    shipping_state: str
    shipping_zip: str
    shipping_country: str = "United States"
    billing_same_as_shipping: bool = True
    card_holder: str
    card_number: str
    card_expiry: str
    card_cvv: str


class TaskCreate(BaseModel):
    site_type: str = "shopify"
    site_name: str
    site_url: str
    monitor_input: str
    sizes: List[str] = []
    mode: str = "normal"
    profile_id: Optional[str] = None
    proxy_group_id: Optional[str] = None
    monitor_delay: int = 3000
    retry_delay: int = 2000


class ShopifySetup(BaseModel):
    target_sizes: Optional[List[str]] = None
    use_defaults: bool = True


class ShopifyStoreAdd(BaseModel):
    name: str
    url: str
    delay_ms: int = 3000
    target_sizes: Optional[List[str]] = None


class FootsiteSetup(BaseModel):
    sites: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    target_sizes: Optional[List[str]] = None
    delay_ms: int = 5000


class AutoTaskConfig(BaseModel):
    enabled: bool = True
    min_confidence: float = 0.7
    min_priority: str = "medium"


class ProxyGroupCreate(BaseModel):
    name: str
    proxies: str  # Newline-separated


class ProxyTest(BaseModel):
    group_id: Optional[str] = None


# WebSocket connection manager for real-time events
class ConnectionManager:
    """Manages WebSocket connections for real-time event broadcasting"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket client connected", total=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info("WebSocket client disconnected", total=len(self.active_connections))
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        data = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.active_connections.discard(conn)


ws_manager = ConnectionManager()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Phantom Bot API",
        description="Advanced Sneaker Automation Suite",
        version="1.0.0"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ============ Authentication ============
    
    class LicenseValidation(BaseModel):
        license_key: str
    
    class CheckoutRequest(BaseModel):
        tier: str
        email: str
    
    @app.post("/api/auth/validate")
    async def validate_license(data: LicenseValidation):
        """Validate a license key"""
        # For local development, accept any non-empty key
        # In production, this would verify against a license server
        if not data.license_key or len(data.license_key) < 4:
            raise HTTPException(status_code=401, detail="Invalid license key")
        
        # Return user data for the frontend
        return {
            "valid": True,
            "user": {
                "license_key": data.license_key[:8] + "...",
                "tier": "pro",
                "expires_at": "2027-12-31T23:59:59Z",
            }
        }
    
    @app.post("/api/auth/checkout")
    async def create_checkout_session(data: CheckoutRequest):
        """Create a checkout session (placeholder for Stripe integration)"""
        # Placeholder - would create Stripe session in production
        return {
            "session_id": "demo_session",
            "url": f"https://phantom-bot.com/checkout?tier={data.tier}&email={data.email}"
        }
    
    # ============ Status ============
    
    @app.get("/api/status")
    async def get_status():
        """Get overall bot status"""
        return engine.get_status()
    
    @app.post("/api/start")
    async def start_engine(background_tasks: BackgroundTasks):
        """Start the bot engine"""
        background_tasks.add_task(engine.start)
        return {"message": "Engine starting..."}
    
    @app.post("/api/stop")
    async def stop_engine(background_tasks: BackgroundTasks):
        """Stop the bot engine"""
        background_tasks.add_task(engine.stop)
        return {"message": "Engine stopping..."}

    
    # ============ Profiles ============
    
    @app.get("/api/profiles")
    async def list_profiles():
        """List all profiles"""
        return {
            "profiles": [p.to_dict() for p in engine.profile_manager.profiles.values()],
            "groups": [{"id": g.id, "name": g.name, "color": g.color} 
                      for g in engine.profile_manager.groups.values()]
        }
    
    @app.get("/api/profiles/{profile_id}")
    async def get_profile(profile_id: str):
        """Get a specific profile"""
        profile = engine.profile_manager.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile.to_dict()
    
    @app.post("/api/profiles")
    async def create_profile(data: ProfileCreate):
        """Create a new profile"""
        profile = Profile(
            name=data.name,
            email=data.email,
            phone=data.phone,
            billing_same_as_shipping=data.billing_same_as_shipping,
            shipping=Address(
                first_name=data.shipping_first_name,
                last_name=data.shipping_last_name,
                address1=data.shipping_address1,
                address2=data.shipping_address2,
                city=data.shipping_city,
                state=data.shipping_state,
                zip_code=data.shipping_zip,
                country=data.shipping_country,
            ),
            card=PaymentCard(holder=data.card_holder, expiry=data.card_expiry)
        )
        profile.card.number = data.card_number
        profile.card.cvv = data.card_cvv
        
        engine.profile_manager.add_profile(profile)
        return {"id": profile.id, "message": "Profile created"}
    
    @app.delete("/api/profiles/{profile_id}")
    async def delete_profile(profile_id: str):
        """Delete a profile"""
        if engine.profile_manager.delete_profile(profile_id):
            return {"message": "Profile deleted"}
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # ============ Proxies ============
    
    @app.get("/api/proxies")
    async def list_proxies():
        """List proxy groups and stats"""
        return {
            "stats": engine.proxy_manager.get_stats(),
            "groups": list(engine.proxy_manager.groups.keys()),
        }
    
    @app.post("/api/proxies/groups")
    async def create_proxy_group(data: ProxyGroupCreate):
        """Create a proxy group"""
        ids = engine.proxy_manager.add_proxies_from_string(data.proxies, data.name)
        return {"group": data.name, "count": len(ids)}
    
    @app.post("/api/proxies/test")
    async def test_proxies(group_id: Optional[str] = None):
        """Test all proxies"""
        await engine.proxy_manager.test_all_proxies(group_id)
        return engine.proxy_manager.get_stats(group_id)
    
    @app.delete("/api/proxies/groups/{group_id}")
    async def delete_proxy_group(group_id: str):
        """Delete a proxy group"""
        if group_id in engine.proxy_manager.groups:
            for proxy_id in list(engine.proxy_manager.groups[group_id]):
                engine.proxy_manager.remove_proxy(proxy_id)
            del engine.proxy_manager.groups[group_id]
            return {"message": "Group deleted"}
        raise HTTPException(status_code=404, detail="Group not found")
    
    # ============ Tasks ============
    
    @app.get("/api/tasks")
    async def list_tasks():
        """List all tasks"""
        return {
            "tasks": [t.to_dict() for t in engine.task_manager.tasks.values()],
            "stats": engine.task_manager.get_stats(),
        }
    
    @app.post("/api/tasks")
    async def create_task(data: TaskCreate):
        """Create a new task"""
        config = TaskConfig(
            site_type=data.site_type,
            site_name=data.site_name,
            site_url=data.site_url,
            monitor_input=data.monitor_input,
            sizes=data.sizes,
            mode=TaskMode(data.mode),
            profile_id=data.profile_id,
            proxy_group_id=data.proxy_group_id,
            monitor_delay=data.monitor_delay,
            retry_delay=data.retry_delay,
        )
        
        task = engine.task_manager.create_task(config)
        return {"id": task.id, "message": "Task created"}
    
    @app.post("/api/tasks/{task_id}/start")
    async def start_task(task_id: str, background_tasks: BackgroundTasks):
        """Start a task"""
        async def _start():
            await engine.task_manager.start_task(task_id)
        background_tasks.add_task(_start)
        return {"message": "Task starting..."}
    
    @app.post("/api/tasks/{task_id}/stop")
    async def stop_task(task_id: str):
        """Stop a task"""
        if engine.task_manager.stop_task(task_id):
            return {"message": "Task stopping..."}
        raise HTTPException(status_code=404, detail="Task not found or not running")
    
    @app.delete("/api/tasks/{task_id}")
    async def delete_task(task_id: str):
        """Delete a task"""
        if engine.task_manager.delete_task(task_id):
            return {"message": "Task deleted"}
        raise HTTPException(status_code=404, detail="Task not found")
    
    @app.post("/api/tasks/start-all")
    async def start_all_tasks(background_tasks: BackgroundTasks):
        """Start all tasks"""
        background_tasks.add_task(engine.task_manager.start_all)
        return {"message": "Starting all tasks..."}
    
    @app.post("/api/tasks/stop-all")
    async def stop_all_tasks(background_tasks: BackgroundTasks):
        """Stop all tasks"""
        background_tasks.add_task(engine.task_manager.stop_all)
        return {"message": "Stopping all tasks..."}
    
    # ============ Intelligence ============
    
    @app.get("/api/intelligence/trending")
    async def get_trending():
        """Get trending products"""
        if engine._intelligence:
            trending = await engine._intelligence.price_tracker.get_trending_products()
            return {"trending": trending}
        return {"trending": []}
    
    @app.post("/api/intelligence/research")
    async def research_product(name: str, sku: str, retail_price: float):
        """Research a product"""
        if engine._intelligence:
            research = await engine._intelligence.research_product(name, sku, retail_price)
            return {
                "name": research.name,
                "sku": research.sku,
                "keywords": research.keywords,
                "sites": research.recommended_sites,
                "hype_score": research.hype_score,
                "profit": research.profit_analysis.estimated_profit if research.profit_analysis else None,
            }
        raise HTTPException(status_code=503, detail="Intelligence module not available")
    
    # ============ Captcha ============
    
    @app.get("/api/captcha/balances")
    async def get_captcha_balances():
        """Get captcha solver balances"""
        if engine._captcha_solver:
            return await engine._captcha_solver.get_balances()
        return {}
    
    # ============ Monitors ============
    
    from ..monitors.manager import monitor_manager
    from ..monitors.products import product_db
    
    @app.get("/api/monitors/status")
    async def get_monitors_status():
        """Get monitor status and statistics"""
        return monitor_manager.get_stats()
    
    @app.post("/api/monitors/start")
    async def start_monitors(background_tasks: BackgroundTasks):
        """Start all monitors"""
        async def _start():
            await monitor_manager.start()
        background_tasks.add_task(_start)
        return {"message": "Monitors starting..."}
    
    @app.post("/api/monitors/stop")
    async def stop_monitors(background_tasks: BackgroundTasks):
        """Stop all monitors"""
        async def _stop():
            await monitor_manager.stop()
        background_tasks.add_task(_stop)
        return {"message": "Monitors stopping..."}
    
    @app.post("/api/monitors/shopify/setup")
    async def setup_shopify_monitors(data: ShopifySetup):
        """Set up Shopify monitoring with default stores"""
        monitor_manager.setup_shopify(target_sizes=data.target_sizes, use_defaults=data.use_defaults)
        store_count = len(monitor_manager.shopify_monitor.stores) if monitor_manager.shopify_monitor else 0
        return {"message": "Shopify monitoring configured", "stores": store_count}
    
    @app.post("/api/monitors/shopify/add-store")
    async def add_shopify_store(data: ShopifyStoreAdd):
        """Add a Shopify store to monitor"""
        monitor_manager.add_shopify_store(data.name, data.url, data.delay_ms, data.target_sizes)
        return {"message": f"Store '{data.name}' added"}
    
    @app.post("/api/monitors/config/save")
    async def save_monitor_config():
        """Save current monitor configuration to database for persistence"""
        from ..utils.database import db
        import uuid
        
        if not monitor_manager.shopify_monitor:
            return {"message": "No monitor configuration to save", "count": 0}
        
        saved_count = 0
        async with db.session() as session:
            for store in monitor_manager.shopify_monitor.stores:
                # Check if store already exists
                existing = await session.execute(
                    "SELECT id FROM monitor_stores WHERE url = :url",
                    {"url": store.url}
                )
                row = existing.first()
                
                if row:
                    # Update existing
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
                        }
                    )
                else:
                    # Insert new
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
                        }
                    )
                saved_count += 1
            await session.commit()
        
        return {"message": f"Saved {saved_count} monitor configurations", "count": saved_count}
    
    @app.get("/api/monitors/config/load")
    async def load_monitor_config():
        """Load monitor configuration from database"""
        from ..utils.database import db
        
        async with db.session() as session:
            result = await session.execute(
                "SELECT id, name, url, enabled, delay_ms, target_sizes FROM monitor_stores WHERE enabled = 1"
            )
            rows = result.fetchall()
        
        stores = []
        for row in rows:
            stores.append({
                "id": row[0],
                "name": row[1],
                "url": row[2],
                "enabled": bool(row[3]),
                "delay_ms": row[4],
                "target_sizes": json.loads(row[5]) if row[5] else [],
            })
        
        return {"stores": stores, "count": len(stores)}
    
    @app.post("/api/monitors/config/restore")
    async def restore_monitor_config():
        """Restore monitor configuration from database and start monitors"""
        from ..utils.database import db
        
        async with db.session() as session:
            result = await session.execute(
                "SELECT name, url, delay_ms, target_sizes FROM monitor_stores WHERE enabled = 1"
            )
            rows = result.fetchall()
        
        if not rows:
            return {"message": "No saved configuration to restore", "count": 0}
        
        # Set up monitors from saved config
        for row in rows:
            name, url, delay_ms, target_sizes = row
            sizes = json.loads(target_sizes) if target_sizes else None
            monitor_manager.add_shopify_store(name, url, delay_ms, sizes)
        
        return {"message": f"Restored {len(rows)} monitors", "count": len(rows)}
    
    @app.post("/api/monitors/footsites/setup")
    async def setup_footsite_monitors(data: FootsiteSetup):
        """Set up Footsite monitoring"""
        monitor_manager.setup_footsites(sites=data.sites, keywords=data.keywords, target_sizes=data.target_sizes, delay_ms=data.delay_ms)
        return {"message": "Footsite monitoring configured"}
    
    @app.get("/api/monitors/events")
    async def get_monitor_events(limit: int = 50):
        """Get recent monitor events"""
        events = monitor_manager.get_recent_events(limit)
        return {
            "count": len(events),
            "events": [
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
        }
    
    @app.get("/api/monitors/events/high-priority")
    async def get_high_priority_events(limit: int = 20):
        """Get high priority monitor events"""
        events = monitor_manager.get_high_priority_events(limit)
        return {
            "count": len(events),
            "events": [
                {
                    "type": e.event_type,
                    "source": e.source,
                    "store": e.store_name,
                    "product": e.product.title,
                    "url": e.product.url,
                    "sizes": e.product.sizes_available[:10],
                    "matched": e.matched_product.name if e.matched_product else None,
                    "profit": e.matched_product.profit_dollar if e.matched_product else None,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in events
            ]
        }
    
    @app.post("/api/monitors/auto-tasks")
    async def configure_auto_tasks(data: AutoTaskConfig):
        """Configure automatic task creation"""
        monitor_manager.enable_auto_tasks(data.enabled, data.min_confidence, data.min_priority)
        return {"message": "Auto-task configuration updated", "enabled": data.enabled}
    
    # ============ Curated Products ============
    
    @app.get("/api/products/curated")
    async def get_curated_products():
        """Get curated product database"""
        return {
            "stats": product_db.get_stats(),
            "products": [p.to_dict() for p in product_db.get_enabled()]
        }
    
    @app.get("/api/products/curated/high-priority")
    async def get_high_priority_products():
        """Get high priority curated products"""
        return {
            "products": [p.to_dict() for p in product_db.get_high_priority()]
        }
    
    @app.get("/api/products/curated/profitable")
    async def get_profitable_products(min_profit: float = 50):
        """Get profitable curated products"""
        return {
            "products": [p.to_dict() for p in product_db.get_profitable(min_profit)]
        }
    
    @app.post("/api/products/load-json")
    async def load_products_json(path: str):
        """Load curated products from JSON file"""
        count = monitor_manager.load_products_from_json(path)
        return {"message": f"Loaded {count} products", "count": count}
    
    # ============ Import/Export ============
    
    @app.post("/api/import/valor")
    async def import_valor(config_path: str):
        """Import Valor bot configuration"""
        try:
            counts = await engine.import_valor_config(config_path)
            return {"message": "Import successful", **counts}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # ============ WebSocket for Real-time Events ============
    
    @app.websocket("/ws/events")
    async def websocket_events(websocket: WebSocket):
        """WebSocket endpoint for real-time monitor events"""
        await ws_manager.connect(websocket)
        try:
            while True:
                # Keep connection alive, listen for client messages
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    # Handle ping/pong or client commands
                    if data == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except asyncio.TimeoutError:
                    # Send heartbeat
                    await websocket.send_text(json.dumps({"type": "heartbeat"}))
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
        except Exception:
            ws_manager.disconnect(websocket)
    
    # ============ Batch Profile Import ============
    
    @app.post("/api/profiles/import")
    async def import_profiles(file: UploadFile = File(...)):
        """Import profiles from CSV or JSON file"""
        content = await file.read()
        filename = file.filename or ""
        
        try:
            profiles_created = 0
            
            if filename.endswith(".json"):
                data = json.loads(content.decode("utf-8"))
                profiles_list = data if isinstance(data, list) else data.get("profiles", [])
                
                for p in profiles_list:
                    profile = Profile(
                        name=p.get("name", "Imported"),
                        email=p.get("email", ""),
                        phone=p.get("phone", ""),
                        shipping=Address(
                            first_name=p.get("shipping_first_name", ""),
                            last_name=p.get("shipping_last_name", ""),
                            address1=p.get("shipping_address1", ""),
                            address2=p.get("shipping_address2", ""),
                            city=p.get("shipping_city", ""),
                            state=p.get("shipping_state", ""),
                            zip_code=p.get("shipping_zip", ""),
                            country=p.get("shipping_country", "United States"),
                        ),
                        payment=PaymentCard(
                            holder_name=p.get("card_holder", ""),
                            number=p.get("card_number", ""),
                            expiry=p.get("card_expiry", ""),
                            cvv=p.get("card_cvv", ""),
                        ),
                    )
                    engine.profile_manager.add_profile(profile)
                    profiles_created += 1
                    
            elif filename.endswith(".csv"):
                import csv
                import io
                reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
                
                for row in reader:
                    profile = Profile(
                        name=row.get("name", "Imported"),
                        email=row.get("email", ""),
                        phone=row.get("phone", ""),
                        shipping=Address(
                            first_name=row.get("shipping_first_name", ""),
                            last_name=row.get("shipping_last_name", ""),
                            address1=row.get("shipping_address1", ""),
                            address2=row.get("shipping_address2", ""),
                            city=row.get("shipping_city", ""),
                            state=row.get("shipping_state", ""),
                            zip_code=row.get("shipping_zip", ""),
                            country=row.get("shipping_country", "United States"),
                        ),
                        payment=PaymentCard(
                            holder_name=row.get("card_holder", ""),
                            number=row.get("card_number", ""),
                            expiry=row.get("card_expiry", ""),
                            cvv=row.get("card_cvv", ""),
                        ),
                    )
                    engine.profile_manager.add_profile(profile)
                    profiles_created += 1
            else:
                raise HTTPException(status_code=400, detail="File must be .json or .csv")
            
            return {"message": f"Imported {profiles_created} profiles", "count": profiles_created}
            
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # ============ Rate Limit Stats ============
    
    @app.get("/api/monitors/rate-limits")
    async def get_rate_limits():
        """Get rate limit statistics per store"""
        stats = {}
        
        if monitor_manager.shopify_monitor:
            for store in monitor_manager.shopify_monitor.stores:
                stats[store.name] = {
                    "url": store.url,
                    "delay_ms": store.delay_ms,
                    "request_count": getattr(store, '_request_count', 0),
                    "rate_limited": getattr(store, '_rate_limited', False),
                    "last_request": getattr(store, '_last_request', None),
                }
        
        return {"stores": stats}
    
    # ============ Analytics Data ============
    
    @app.get("/api/analytics/checkout")
    async def get_checkout_analytics():
        """Get checkout success/failure analytics"""
        tasks = list(engine.task_manager.tasks.values())
        
        success_count = sum(1 for t in tasks if t.result and t.result.success)
        failed_count = sum(1 for t in tasks if t.result and not t.result.success)
        pending_count = sum(1 for t in tasks if not t.result and t.is_running)
        
        # Group by site
        by_site = {}
        for t in tasks:
            site = t.config.site_name or "unknown"
            if site not in by_site:
                by_site[site] = {"success": 0, "failed": 0, "total": 0}
            by_site[site]["total"] += 1
            if t.result:
                if t.result.success:
                    by_site[site]["success"] += 1
                else:
                    by_site[site]["failed"] += 1
        
        return {
            "total_tasks": len(tasks),
            "success": success_count,
            "failed": failed_count,
            "pending": pending_count,
            "success_rate": (success_count / len(tasks) * 100) if tasks else 0,
            "by_site": by_site,
        }
    
    # ============ Quick Tasks ============
    
    class QuickTaskCreate(BaseModel):
        url: str
        sizes: Optional[List[str]] = None
        quantity: int = 1
        mode: str = "fast"
        profile_id: Optional[str] = None
        proxy_group_id: Optional[str] = None
        auto_start: bool = True
    
    class QuickTaskBatch(BaseModel):
        urls: List[str]
        sizes: Optional[List[str]] = None
        mode: str = "fast"
        auto_start: bool = True
    
    @app.post("/api/tasks/quick")
    async def create_quick_task(data: QuickTaskCreate, background_tasks: BackgroundTasks):
        """Create a task from a product URL with auto-detection"""
        import re
        from urllib.parse import urlparse
        
        url = data.url.strip()
        
        # Parse URL to detect site
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        
        # Extract site name from domain
        site_name = domain.split(".")[0].title()
        site_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Auto-detect site type
        site_type = "shopify"  # Default, could be extended
        
        # Extract product identifier from URL
        path = parsed.path
        monitor_input = url  # Use full URL as monitor input
        
        # Extract product name if possible
        product_match = re.search(r'/products?/([^/?]+)', path)
        if product_match:
            product_slug = product_match.group(1)
            monitor_input = product_slug.replace("-", " ").title()
        
        tasks_created = []
        for _ in range(data.quantity):
            config = TaskConfig(
                site_type=site_type,
                site_name=site_name,
                site_url=site_url,
                product_url=url,
                monitor_input=monitor_input,
                sizes=data.sizes or [],
                mode=TaskMode(data.mode),
                profile_id=data.profile_id,
                proxy_group_id=data.proxy_group_id,
                monitor_delay=1000,
                retry_delay=1500,
            )
            
            task = engine.task_manager.create_task(config)
            tasks_created.append(task.id)
            
            if data.auto_start:
                async def _start(tid=task.id):
                    await engine.task_manager.start_task(tid)
                background_tasks.add_task(_start)
        
        return {
            "id": tasks_created[0] if len(tasks_created) == 1 else tasks_created,
            "message": f"Created {len(tasks_created)} quick task(s)",
            "site_name": site_name,
            "site_type": site_type,
            "monitor_input": monitor_input,
        }
    
    @app.post("/api/tasks/quick-batch")
    async def create_quick_tasks_batch(data: QuickTaskBatch, background_tasks: BackgroundTasks):
        """Create multiple tasks from a list of URLs"""
        ids = []
        for url in data.urls:
            single = QuickTaskCreate(
                url=url,
                sizes=data.sizes,
                mode=data.mode,
                auto_start=data.auto_start
            )
            result = await create_quick_task(single, background_tasks)
            if isinstance(result["id"], list):
                ids.extend(result["id"])
            else:
                ids.append(result["id"])
        
        return {"ids": ids, "message": f"Created {len(ids)} tasks"}
    
    # ============ Shopify Stores Management ============
    
    @app.get("/api/monitors/shopify/stores")
    async def get_shopify_stores():
        """List all configured Shopify stores with their stats"""
        stores = []
        
        if monitor_manager.shopify_monitor:
            for store_id, monitor in monitor_manager.shopify_monitor.stores.items():
                store = monitor.store
                stores.append({
                    "id": store_id,
                    "name": store.name,
                    "url": store.url,
                    "enabled": store.enabled,
                    "delay_ms": store.delay_ms,
                    "target_sizes": monitor.target_sizes or [],
                    "last_check": store.last_check.isoformat() if store.last_check else None,
                    "success_count": store.success_count,
                    "error_count": store.error_count,
                    "products_found": store.products_found,
                })
        
        return {"stores": stores}
    
    class ShopifyStoreUpdate(BaseModel):
        enabled: Optional[bool] = None
        delay_ms: Optional[int] = None
        target_sizes: Optional[List[str]] = None
    
    @app.patch("/api/monitors/shopify/stores/{store_id}")
    async def update_shopify_store(store_id: str, updates: ShopifyStoreUpdate):
        """Update a Shopify store's settings"""
        if not monitor_manager.shopify_monitor:
            raise HTTPException(status_code=404, detail="No Shopify monitor configured")
        
        if store_id not in monitor_manager.shopify_monitor.stores:
            raise HTTPException(status_code=404, detail="Store not found")
        
        monitor = monitor_manager.shopify_monitor.stores[store_id]
        
        if updates.enabled is not None:
            monitor.store.enabled = updates.enabled
        if updates.delay_ms is not None:
            monitor.store.delay_ms = updates.delay_ms
        if updates.target_sizes is not None:
            monitor.target_sizes = updates.target_sizes
        
        return {"message": f"Store '{monitor.store.name}' updated"}
    
    @app.delete("/api/monitors/shopify/stores/{store_id}")
    async def delete_shopify_store(store_id: str):
        """Remove a Shopify store from monitoring"""
        if not monitor_manager.shopify_monitor:
            raise HTTPException(status_code=404, detail="No Shopify monitor configured")
        
        if store_id not in monitor_manager.shopify_monitor.stores:
            raise HTTPException(status_code=404, detail="Store not found")
        
        monitor = monitor_manager.shopify_monitor.stores.pop(store_id)
        await monitor.close()
        
        return {"message": f"Store '{monitor.store.name}' deleted"}
    
    # ============ Restock History ============
    
    @app.get("/api/monitors/restock-history")
    async def get_restock_history(hours: int = 24, limit: int = 50):
        """Get recent restock events"""
        from datetime import timedelta
        
        history = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Get restock events from monitor manager
        for event in monitor_manager._events:
            if event.event_type == "restock" and event.timestamp >= cutoff:
                history.append({
                    "product_id": event.product.sku or "",
                    "product_title": event.product.title,
                    "store_name": event.store_name,
                    "sizes_restocked": event.product.sizes_available[:10],
                    "timestamp": event.timestamp.isoformat(),
                    "price": event.product.price,
                    "image_url": event.product.image_url,
                })
        
        # Sort by most recent and limit
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"history": history[:limit]}
    
    @app.get("/api/monitors/restock-stats")
    async def get_restock_stats():
        """Get restock statistics"""
        from datetime import timedelta
        from collections import defaultdict
        
        now = datetime.now()
        restocks_24h = 0
        restocks_7d = 0
        product_counts = defaultdict(int)
        
        for event in monitor_manager._events:
            if event.event_type == "restock":
                age = now - event.timestamp
                if age <= timedelta(hours=24):
                    restocks_24h += 1
                if age <= timedelta(days=7):
                    restocks_7d += 1
                    product_counts[event.product.title] += 1
        
        # Count products with multiple restocks (patterns)
        patterns_detected = sum(1 for count in product_counts.values() if count >= 2)
        
        return {
            "restocks_last_24h": restocks_24h,
            "restocks_last_7d": restocks_7d,
            "patterns_detected": patterns_detected,
            "predicted_restocks_24h": patterns_detected,  # Simplified prediction
        }
    
    @app.get("/api/monitors/restock-patterns")
    async def get_restock_patterns(days: int = 7):
        """Get detected restock patterns with predictions"""
        from datetime import timedelta
        from collections import defaultdict
        
        now = datetime.now()
        cutoff = now - timedelta(days=days)
        
        # Group restocks by product
        product_restocks = defaultdict(list)
        
        for event in monitor_manager._events:
            if event.event_type == "restock" and event.timestamp >= cutoff:
                key = f"{event.store_name}:{event.product.title}"
                product_restocks[key].append(event)
        
        patterns = []
        for key, events in product_restocks.items():
            if len(events) < 2:
                continue
            
            store_name, product_title = key.split(":", 1)
            
            # Sort by timestamp
            events.sort(key=lambda e: e.timestamp)
            
            # Calculate average interval
            intervals = []
            for i in range(1, len(events)):
                diff = (events[i].timestamp - events[i-1].timestamp).total_seconds() / 3600
                intervals.append(diff)
            
            avg_interval = sum(intervals) / len(intervals) if intervals else None
            
            # Predict next restock
            next_predicted = None
            confidence = 0.0
            if avg_interval and len(events) >= 2:
                next_predicted = (events[-1].timestamp + timedelta(hours=avg_interval)).isoformat()
                confidence = min(0.9, 0.3 + 0.15 * len(events))  # More restocks = higher confidence
            
            patterns.append({
                "product_title": product_title,
                "store_name": store_name,
                "restock_count": len(events),
                "last_restock": events[-1].timestamp.isoformat() if events else None,
                "average_interval_hours": round(avg_interval, 1) if avg_interval else None,
                "next_predicted_restock": next_predicted,
                "confidence_score": round(confidence, 2),
            })
        
        # Sort by restock count
        patterns.sort(key=lambda x: x["restock_count"], reverse=True)
        
        return {"patterns": patterns}
    
    return app


# Helper function to broadcast events via WebSocket
async def broadcast_monitor_event(event_data: dict):
    """Broadcast a monitor event to all connected WebSocket clients"""
    await ws_manager.broadcast({
        "type": "monitor_event",
        "data": event_data
    })


def setup_websocket_broadcasts():
    """
    Setup WebSocket broadcast integration with monitor events.
    Called from main.py after app is created to wire up real-time updates.
    """
    from ..monitors.manager import monitor_manager
    
    try:
        # Register the broadcast callback if monitor_manager has event hooks
        if hasattr(monitor_manager, 'on_event'):
            async def broadcast_wrapper(event):
                await broadcast_monitor_event(event)
            monitor_manager.on_event = broadcast_wrapper
            logger.info("WebSocket broadcasts configured for monitor events")
        else:
            logger.debug("Monitor manager does not support event hooks yet")
    except Exception as e:
        logger.warning(f"Could not setup WebSocket broadcasts: {e}")
