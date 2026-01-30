"""Authentication middleware for FastAPI"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import structlog

from .license import LicenseValidator, UserTier

logger = structlog.get_logger()
security = HTTPBearer(auto_error=False)

class AuthMiddleware:
    """Middleware for validating license keys on API requests"""
    
    def __init__(self, license_validator: LicenseValidator):
        self.validator = license_validator
    
    async def __call__(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials] = None):
        """Validate license key from Authorization header"""
        
        # Skip auth for public endpoints
        public_paths = ["/api/status", "/api/health", "/docs", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in public_paths):
            return None
        
        # Get license key from header
        license_key = None
        if credentials:
            license_key = credentials.credentials
        elif "X-License-Key" in request.headers:
            license_key = request.headers["X-License-Key"]
        
        if not license_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="License key required. Get yours at https://phantom-bot.com/pricing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate license
        validation = self.validator.validate(license_key)
        
        if not validation["valid"]:
            error_code = validation.get("error_code", "INVALID")
            error_msg = validation.get("error", "Invalid license")
            
            if error_code == "EXPIRED":
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="License expired. Renew at https://phantom-bot.com/billing"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid license: {error_msg}"
                )
        
        # Attach user info to request state
        request.state.user_id = validation["user_id"]
        request.state.user_email = validation.get("email")
        request.state.tier = validation["tier"]
        request.state.limits = validation["limits"]
        
        logger.info(
            "Request authenticated",
            user_id=validation["user_id"],
            tier=validation["tier"],
            path=request.url.path
        )
        
        return validation

async def get_current_user(request: Request) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return {
        "user_id": request.state.user_id,
        "email": request.state.user_email,
        "tier": request.state.tier,
        "limits": request.state.limits,
    }

def check_tier_limit(request: Request, feature: str) -> bool:
    """Check if user's tier allows a specific feature"""
    if not hasattr(request.state, "limits"):
        return False
    
    limits = request.state.limits
    return limits.get(feature, False)

def require_tier(min_tier: str):
    """Decorator to require minimum tier for endpoint"""
    tier_hierarchy = {
        UserTier.STARTER: 0,
        UserTier.PRO: 1,
        UserTier.ELITE: 2,
        UserTier.ENTERPRISE: 3,
    }
    
    async def dependency(request: Request):
        user_tier = getattr(request.state, "tier", UserTier.STARTER)
        
        if tier_hierarchy.get(user_tier, 0) < tier_hierarchy.get(min_tier, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {min_tier} tier or higher. Upgrade at https://phantom-bot.com/pricing"
            )
        
        return True
    
    return dependency
