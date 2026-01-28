"""
Configuration management for Phantom Bot
Handles loading, validation, and access to all configuration settings
"""

import os
import yaml
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import structlog

logger = structlog.get_logger()


class CaptchaProviderConfig(BaseModel):
    api_key: str = ""


class CaptchaConfig(BaseModel):
    primary_provider: str = "2captcha"
    fallback_provider: str = "anticaptcha"
    providers: Dict[str, CaptchaProviderConfig] = Field(default_factory=dict)
    ai_solver: Dict[str, Any] = Field(default_factory=dict)
    harvester: Dict[str, Any] = Field(default_factory=dict)


class ProxyConfig(BaseModel):
    test_on_start: bool = True
    test_url: str = "https://www.google.com"
    timeout: int = 10
    rotation_strategy: str = "smart"
    health_check_interval: int = 300
    ban_threshold: int = 3
    auto_remove_bad: bool = False
    sticky_duration: int = 300


class PerformanceConfig(BaseModel):
    max_concurrent_tasks: int = 50
    max_concurrent_monitors: int = 25
    request_timeout: int = 30
    checkout_timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0


class DelayConfig(BaseModel):
    monitor: Dict[str, int] = Field(default_factory=lambda: {"default": 3000, "aggressive": 1500, "safe": 5000})
    retry: Dict[str, int] = Field(default_factory=lambda: {"default": 2000, "aggressive": 1000, "safe": 3500})
    checkout: Dict[str, Any] = Field(default_factory=lambda: {"default": 0, "humanized": True})


class EvasionConfig(BaseModel):
    fingerprint: Dict[str, bool] = Field(default_factory=dict)
    tls: Dict[str, Any] = Field(default_factory=dict)
    humanizer: Dict[str, bool] = Field(default_factory=dict)
    headers: Dict[str, bool] = Field(default_factory=dict)


class IntelligenceConfig(BaseModel):
    enabled: bool = True
    stockx: Dict[str, Any] = Field(default_factory=dict)
    goat: Dict[str, Any] = Field(default_factory=dict)
    ebay: Dict[str, Any] = Field(default_factory=dict)
    restock_prediction: Dict[str, Any] = Field(default_factory=dict)
    research: Dict[str, Any] = Field(default_factory=dict)


class DiscordConfig(BaseModel):
    enabled: bool = True
    webhook_url: str = ""
    success_webhook: str = ""
    failure_webhook: str = ""
    restock_webhook: str = ""
    mention_role: str = ""
    embed_color: int = 0x7289DA


class NotificationsConfig(BaseModel):
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    desktop: Dict[str, bool] = Field(default_factory=lambda: {"enabled": True, "sound": True})
    email: Dict[str, Any] = Field(default_factory=dict)


class DatabaseConfig(BaseModel):
    type: str = "sqlite"
    sqlite: Dict[str, str] = Field(default_factory=lambda: {"path": "data/phantom.db"})
    postgresql: Dict[str, Any] = Field(default_factory=dict)


class WebConfig(BaseModel):
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8080
    secret_key: str = ""
    session_timeout: int = 3600
    cors_origins: List[str] = Field(default_factory=list)
    
    @validator('secret_key', always=True)
    def generate_secret_key(cls, v):
        if not v:
            return secrets.token_urlsafe(32)
        return v


class ShopifyStore(BaseModel):
    name: str
    url: str
    checkout_url: str = ""
    queue_bypass: bool = False
    
    @validator('checkout_url', always=True)
    def set_checkout_url(cls, v, values):
        if not v and 'url' in values:
            return f"{values['url']}/checkout"
        return v


class SitesConfig(BaseModel):
    shopify: Dict[str, Any] = Field(default_factory=dict)
    footsites: Dict[str, Any] = Field(default_factory=dict)
    nike: Dict[str, Any] = Field(default_factory=dict)
    adidas: Dict[str, Any] = Field(default_factory=dict)


class SizesConfig(BaseModel):
    default: List[str] = Field(default_factory=list)
    preferred: List[str] = Field(default_factory=list)
    random_fallback: bool = True


class AppConfig(BaseModel):
    name: str = "Phantom Bot"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"


class PhantomConfig(BaseModel):
    """Main configuration model for Phantom Bot"""
    app: AppConfig = Field(default_factory=AppConfig)
    license: Dict[str, str] = Field(default_factory=dict)
    captcha: CaptchaConfig = Field(default_factory=CaptchaConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    delays: DelayConfig = Field(default_factory=DelayConfig)
    evasion: EvasionConfig = Field(default_factory=EvasionConfig)
    intelligence: IntelligenceConfig = Field(default_factory=IntelligenceConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    sites: SitesConfig = Field(default_factory=SitesConfig)
    sizes: SizesConfig = Field(default_factory=SizesConfig)
    calendar: Dict[str, Any] = Field(default_factory=dict)


class ConfigManager:
    """Singleton configuration manager"""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[PhantomConfig] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load()
    
    @property
    def config(self) -> PhantomConfig:
        if self._config is None:
            self.load()
        return self._config
    
    def load(self, config_path: Optional[str] = None) -> PhantomConfig:
        """Load configuration from YAML file"""
        if config_path is None:
            # Look for config in standard locations
            possible_paths = [
                Path("config.yaml"),
                Path("config.yml"),
                Path.home() / ".phantom" / "config.yaml",
                Path(__file__).parent.parent.parent / "config.yaml",
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = str(path)
                    break
        
        if config_path and Path(config_path).exists():
            logger.info("Loading configuration", path=config_path)
            with open(config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
            self._config = PhantomConfig(**raw_config)
        else:
            logger.warning("No configuration file found, using defaults")
            self._config = PhantomConfig()
        
        # Override with environment variables
        self._apply_env_overrides()
        
        return self._config
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        env_mappings = {
            "PHANTOM_LICENSE_KEY": ("license", "key"),
            "PHANTOM_2CAPTCHA_KEY": ("captcha", "providers", "2captcha", "api_key"),
            "PHANTOM_ANTICAPTCHA_KEY": ("captcha", "providers", "anticaptcha", "api_key"),
            "PHANTOM_DISCORD_WEBHOOK": ("notifications", "discord", "webhook_url"),
            "PHANTOM_DEBUG": ("app", "debug"),
            "PHANTOM_LOG_LEVEL": ("app", "log_level"),
        }
        
        for env_var, path in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                self._set_nested(path, value)
    
    def _set_nested(self, path: tuple, value: Any):
        """Set a nested configuration value"""
        obj = self._config
        for key in path[:-1]:
            if hasattr(obj, key):
                obj = getattr(obj, key)
            elif isinstance(obj, dict):
                obj = obj.get(key, {})
        
        final_key = path[-1]
        if hasattr(obj, final_key):
            # Convert value type if needed
            current = getattr(obj, final_key)
            if isinstance(current, bool):
                value = value.lower() in ('true', '1', 'yes')
            elif isinstance(current, int):
                value = int(value)
            setattr(obj, final_key, value)
        elif isinstance(obj, dict):
            obj[final_key] = value
    
    def save(self, config_path: str = "config.yaml"):
        """Save current configuration to file"""
        with open(config_path, 'w') as f:
            yaml.dump(self._config.model_dump(), f, default_flow_style=False)
        logger.info("Configuration saved", path=config_path)
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Get a configuration value by dot notation"""
        obj = self._config
        for key in keys:
            if hasattr(obj, key):
                obj = getattr(obj, key)
            elif isinstance(obj, dict) and key in obj:
                obj = obj[key]
            else:
                return default
        return obj
    
    def set(self, *keys: str, value: Any):
        """Set a configuration value"""
        self._set_nested(keys, value)


# Global config instance
config_manager = ConfigManager()


def get_config() -> PhantomConfig:
    """Get the current configuration"""
    return config_manager.config


def get(key: str, default: Any = None) -> Any:
    """Quick access to config values using dot notation"""
    keys = key.split('.')
    return config_manager.get(*keys, default=default)
