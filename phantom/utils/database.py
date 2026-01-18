"""
Database management for Phantom Bot
Handles all persistent storage using SQLAlchemy
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Type, TypeVar
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
import structlog

from .config import get_config

logger = structlog.get_logger()

Base = declarative_base()
T = TypeVar('T', bound=Base)


class Profile(Base):
    """Checkout profile model"""
    __tablename__ = 'profiles'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    group_id = Column(String(36), ForeignKey('profile_groups.id'), nullable=True)
    
    # Personal Info
    email = Column(String(255))
    phone = Column(String(50))
    
    # Shipping
    shipping_first_name = Column(String(100))
    shipping_last_name = Column(String(100))
    shipping_address1 = Column(String(255))
    shipping_address2 = Column(String(255))
    shipping_city = Column(String(100))
    shipping_state = Column(String(100))
    shipping_zip = Column(String(20))
    shipping_country = Column(String(100), default="United States")
    shipping_country_code = Column(String(10), default="US")
    
    # Billing (encrypted)
    billing_same_as_shipping = Column(Boolean, default=True)
    billing_first_name = Column(String(100))
    billing_last_name = Column(String(100))
    billing_address1 = Column(String(255))
    billing_address2 = Column(String(255))
    billing_city = Column(String(100))
    billing_state = Column(String(100))
    billing_zip = Column(String(20))
    billing_country = Column(String(100))
    billing_country_code = Column(String(10))
    
    # Payment (encrypted)
    card_holder = Column(String(255))
    card_number_encrypted = Column(Text)  # Encrypted
    card_expiry = Column(String(10))  # MM/YY
    card_cvv_encrypted = Column(Text)  # Encrypted
    card_type = Column(String(20))  # visa, mastercard, amex
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    total_checkouts = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    
    # Relationships
    group = relationship("ProfileGroup", back_populates="profiles")
    tasks = relationship("Task", back_populates="profile")


class ProfileGroup(Base):
    """Profile group model"""
    __tablename__ = 'profile_groups'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    color = Column(String(20), default="#7289DA")
    created_at = Column(DateTime, default=func.now())
    
    profiles = relationship("Profile", back_populates="group")


class Proxy(Base):
    """Proxy model"""
    __tablename__ = 'proxies'
    
    id = Column(String(36), primary_key=True)
    group_id = Column(String(36), ForeignKey('proxy_groups.id'))
    
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255))
    password = Column(String(255))
    protocol = Column(String(10), default="http")  # http, https, socks5
    
    # Health tracking
    status = Column(String(20), default="untested")  # untested, good, slow, bad
    last_tested = Column(DateTime)
    response_time = Column(Float)  # ms
    failure_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    
    # Usage tracking
    last_used = Column(DateTime)
    total_requests = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    
    group = relationship("ProxyGroup", back_populates="proxies")
    
    @property
    def url(self) -> str:
        """Get proxy URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def display_string(self) -> str:
        """Get display string (host:port:user:pass format)"""
        if self.username and self.password:
            return f"{self.host}:{self.port}:{self.username}:{self.password}"
        return f"{self.host}:{self.port}"


class ProxyGroup(Base):
    """Proxy group model"""
    __tablename__ = 'proxy_groups'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    color = Column(String(20), default="#7289DA")
    created_at = Column(DateTime, default=func.now())
    
    proxies = relationship("Proxy", back_populates="group")


class Task(Base):
    """Checkout task model"""
    __tablename__ = 'tasks'
    
    id = Column(String(36), primary_key=True)
    group_id = Column(String(36), ForeignKey('task_groups.id'))
    profile_id = Column(String(36), ForeignKey('profiles.id'))
    proxy_group_id = Column(String(36), ForeignKey('proxy_groups.id'))
    
    # Site configuration
    site_type = Column(String(50), nullable=False)  # shopify, footsites, nike, adidas
    site_name = Column(String(100), nullable=False)  # DTLR, Foot Locker, etc.
    site_url = Column(String(500))
    
    # Product configuration
    monitor_input = Column(Text)  # Keywords or URL
    product_url = Column(String(500))
    product_name = Column(String(255))
    product_sku = Column(String(100))
    product_image = Column(String(500))
    
    # Size configuration
    sizes = Column(JSON)  # List of sizes
    size_preference = Column(String(20), default="preferred")  # preferred, random, any
    
    # Mode and delays
    mode = Column(String(50), default="normal")  # normal, fast, safe, preload
    monitor_delay = Column(Integer, default=3000)
    retry_delay = Column(Integer, default=2000)
    
    # Price filters
    min_price = Column(Float)
    max_price = Column(Float)
    
    # Status
    status = Column(String(50), default="idle")  # idle, monitoring, waiting, carted, checkout, success, failed
    status_message = Column(Text)
    status_color = Column(String(20), default="neutral")
    is_running = Column(Boolean, default=False)
    
    # Options
    retry_on_decline = Column(Boolean, default=False)
    retry_on_error = Column(Boolean, default=True)
    use_captcha_harvester = Column(Boolean, default=True)
    
    # Results
    checkout_url = Column(String(500))
    order_number = Column(String(100))
    checkout_time = Column(Float)  # seconds
    total_price = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    group = relationship("TaskGroup", back_populates="tasks")
    profile = relationship("Profile", back_populates="tasks")
    proxy_group = relationship("ProxyGroup")


class TaskGroup(Base):
    """Task group model"""
    __tablename__ = 'task_groups'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    color = Column(String(20), default="#7289DA")
    created_at = Column(DateTime, default=func.now())
    
    tasks = relationship("Task", back_populates="group")


class Monitor(Base):
    """Product monitor model"""
    __tablename__ = 'monitors'
    
    id = Column(String(36), primary_key=True)
    group_id = Column(String(36), ForeignKey('monitor_groups.id'))
    
    # Site configuration
    site_type = Column(String(50), nullable=False)
    site_name = Column(String(100), nullable=False)
    site_url = Column(String(500))
    
    # Keywords
    positive_keywords = Column(JSON)  # List of positive keywords
    negative_keywords = Column(JSON)  # List of negative keywords
    
    # Monitoring settings
    delay = Column(Integer, default=3000)
    error_delay = Column(Integer, default=5000)
    
    # Status
    status = Column(String(50), default="idle")
    is_running = Column(Boolean, default=False)
    last_check = Column(DateTime)
    products_found = Column(Integer, default=0)
    
    # Webhooks
    webhook_url = Column(String(500))
    
    created_at = Column(DateTime, default=func.now())
    
    group = relationship("MonitorGroup", back_populates="monitors")


class MonitorGroup(Base):
    """Monitor group model"""
    __tablename__ = 'monitor_groups'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    color = Column(String(20), default="#7289DA")
    created_at = Column(DateTime, default=func.now())
    
    monitors = relationship("Monitor", back_populates="group")


class ProductCache(Base):
    """Cached product information"""
    __tablename__ = 'product_cache'
    
    id = Column(String(36), primary_key=True)
    site = Column(String(100), nullable=False)
    product_url = Column(String(500), unique=True)
    
    # Product info
    title = Column(String(500))
    sku = Column(String(100))
    price = Column(Float)
    image_url = Column(String(500))
    
    # Availability
    available = Column(Boolean, default=False)
    sizes_available = Column(JSON)
    
    # Market data
    stockx_price = Column(Float)
    goat_price = Column(Float)
    estimated_profit = Column(Float)
    
    # Timestamps
    first_seen = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())


class CheckoutLog(Base):
    """Checkout attempt log"""
    __tablename__ = 'checkout_logs'
    
    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), ForeignKey('tasks.id'))
    
    # Checkout details
    site = Column(String(100))
    product_name = Column(String(255))
    product_sku = Column(String(100))
    size = Column(String(20))
    price = Column(Float)
    
    # Result
    success = Column(Boolean, default=False)
    order_number = Column(String(100))
    error_message = Column(Text)
    
    # Timing
    checkout_time = Column(Float)
    timestamp = Column(DateTime, default=func.now())
    
    # Analytics
    proxy_used = Column(String(255))
    captcha_time = Column(Float)


class RestockHistory(Base):
    """Historical restock data for ML predictions"""
    __tablename__ = 'restock_history'
    
    id = Column(String(36), primary_key=True)
    site = Column(String(100))
    product_sku = Column(String(100))
    product_name = Column(String(255))
    
    restock_time = Column(DateTime)
    day_of_week = Column(Integer)
    hour = Column(Integer)
    
    # Context
    was_hyped = Column(Boolean, default=False)
    retail_price = Column(Float)
    resale_price = Column(Float)


class DatabaseManager:
    """Async database manager"""
    
    _instance: Optional['DatabaseManager'] = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """Initialize database connection"""
        config = get_config()
        
        if config.database.type == "sqlite":
            db_path = Path(config.database.sqlite.get("path", "data/phantom.db"))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite+aiosqlite:///{db_path}"
        else:
            pg = config.database.postgresql
            db_url = f"postgresql+asyncpg://{pg.get('username')}:{pg.get('password')}@{pg.get('host')}:{pg.get('port')}/{pg.get('database')}"
        
        self._engine = create_async_engine(db_url, echo=config.app.debug)
        self._session_factory = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)
        
        # Create tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized", url=db_url.split('@')[-1] if '@' in db_url else db_url)
    
    @asynccontextmanager
    async def session(self):
        """Get a database session"""
        if self._session_factory is None:
            await self.initialize()
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def get(self, model: Type[T], id: str) -> Optional[T]:
        """Get a record by ID"""
        async with self.session() as session:
            return await session.get(model, id)
    
    async def get_all(self, model: Type[T]) -> List[T]:
        """Get all records of a model"""
        async with self.session() as session:
            result = await session.execute(
                session.query(model)
            )
            return result.scalars().all()
    
    async def add(self, obj: Base) -> Base:
        """Add a new record"""
        async with self.session() as session:
            session.add(obj)
            await session.flush()
            return obj
    
    async def delete(self, obj: Base):
        """Delete a record"""
        async with self.session() as session:
            await session.delete(obj)
    
    async def close(self):
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()


# Global database instance
db = DatabaseManager()


async def init_db():
    """Initialize the database"""
    await db.initialize()


async def get_db():
    """Get database session for FastAPI dependency injection"""
    async with db.session() as session:
        yield session
