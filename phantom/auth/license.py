"""License key validation and user tier management"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import secrets
import structlog

logger = structlog.get_logger()

class UserTier:
    """User subscription tiers"""
    STARTER = "starter"
    PRO = "pro"
    ELITE = "elite"
    ENTERPRISE = "enterprise"

class TierLimits:
    """Usage limits per tier"""
    LIMITS = {
        UserTier.STARTER: {
            "max_tasks": 5,
            "max_monitors": 2,
            "max_tasks_per_day": 20,
            "proxy_enabled": False,
            "quick_tasks": False,
            "auto_tasks": False,
            "api_access": False,
        },
        UserTier.PRO: {
            "max_tasks": 50,
            "max_monitors": 10,
            "max_tasks_per_day": 200,
            "proxy_enabled": True,
            "quick_tasks": True,
            "auto_tasks": False,
            "api_access": False,
        },
        UserTier.ELITE: {
            "max_tasks": 999999,
            "max_monitors": 999999,
            "max_tasks_per_day": 999999,
            "proxy_enabled": True,
            "quick_tasks": True,
            "auto_tasks": True,
            "api_access": True,
        },
        UserTier.ENTERPRISE: {
            "max_tasks": 999999,
            "max_monitors": 999999,
            "max_tasks_per_day": 999999,
            "proxy_enabled": True,
            "quick_tasks": True,
            "auto_tasks": True,
            "api_access": True,
        }
    }
    
    @classmethod
    def get_limits(cls, tier: str) -> Dict[str, Any]:
        """Get limits for a tier"""
        return cls.LIMITS.get(tier, cls.LIMITS[UserTier.STARTER])

class LicenseValidator:
    """Validates license keys and manages user authentication"""
    
    def __init__(self, secret_key: str):
        self.secret = secret_key
    
    def generate_license(
        self, 
        user_id: str, 
        email: str,
        tier: str = UserTier.STARTER,
        duration_days: int = 30
    ) -> str:
        """Generate a new license key"""
        expiration = datetime.utcnow() + timedelta(days=duration_days)
        
        payload = {
            "user_id": user_id,
            "email": email,
            "tier": tier,
            "exp": int(expiration.timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
            "jti": secrets.token_urlsafe(16),  # Unique token ID
        }
        
        license_key = jwt.encode(payload, self.secret, algorithm="HS256")
        logger.info("Generated license", user_id=user_id, tier=tier, expires=expiration.isoformat())
        
        return license_key
    
    def validate(self, license_key: str) -> Dict[str, Any]:
        """Validate license key and return user info + limits"""
        try:
            payload = jwt.decode(license_key, self.secret, algorithms=["HS256"])
            
            # Check expiration
            exp_timestamp = payload.get("exp")
            if not exp_timestamp or datetime.utcnow().timestamp() > exp_timestamp:
                logger.warning("License expired", user_id=payload.get("user_id"))
                return {
                    "valid": False,
                    "error": "License expired",
                    "error_code": "EXPIRED"
                }
            
            tier = payload.get("tier", UserTier.STARTER)
            limits = TierLimits.get_limits(tier)
            
            return {
                "valid": True,
                "user_id": payload["user_id"],
                "email": payload.get("email"),
                "tier": tier,
                "limits": limits,
                "expires_at": datetime.fromtimestamp(exp_timestamp).isoformat(),
                "jti": payload.get("jti"),
            }
            
        except jwt.ExpiredSignatureError:
            return {
                "valid": False,
                "error": "License expired",
                "error_code": "EXPIRED"
            }
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid license key", error=str(e))
            return {
                "valid": False,
                "error": "Invalid license key",
                "error_code": "INVALID"
            }
        except Exception as e:
            logger.error("License validation error", error=str(e))
            return {
                "valid": False,
                "error": "Validation failed",
                "error_code": "ERROR"
            }
    
    def refresh_license(self, license_key: str, duration_days: int = 30) -> Optional[str]:
        """Refresh an existing license (extend expiration)"""
        validation = self.validate(license_key)
        
        if not validation["valid"]:
            return None
        
        # Generate new license with same user info but new expiration
        return self.generate_license(
            user_id=validation["user_id"],
            email=validation["email"],
            tier=validation["tier"],
            duration_days=duration_days
        )
