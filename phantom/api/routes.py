"""
FastAPI Routes for Phantom Bot Web UI
"""

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
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


class ProxyGroupCreate(BaseModel):
    name: str
    proxies: str  # Newline-separated


class MonitorCreate(BaseModel):
    site_name: str
    site_url: str
    keywords: str
    delay: int = 3000
    proxy_group_id: Optional[str] = None


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
    
    # ============ Import/Export ============
    
    @app.post("/api/import/valor")
    async def import_valor(config_path: str):
        """Import Valor bot configuration"""
        try:
            counts = await engine.import_valor_config(config_path)
            return {"message": "Import successful", **counts}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return app
