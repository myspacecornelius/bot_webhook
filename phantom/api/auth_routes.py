"""Authentication and licensing API routes"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
import structlog
import stripe
import os

from ..auth.license import LicenseValidator, UserTier
from ..auth.middleware import get_current_user
from ..auth.usage_tracker import UsageTracker

logger = structlog.get_logger()
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Initialize services
LICENSE_SECRET = os.getenv("LICENSE_SECRET", "your-secret-key-change-in-production")
license_validator = LicenseValidator(LICENSE_SECRET)
usage_tracker = UsageTracker()

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

class LicenseActivation(BaseModel):
    license_key: str

class LicenseGeneration(BaseModel):
    email: EmailStr
    tier: str = UserTier.STARTER
    duration_days: int = 30

class StripeCheckout(BaseModel):
    tier: str
    email: EmailStr

@router.post("/validate")
async def validate_license(activation: LicenseActivation):
    """Validate a license key"""
    validation = license_validator.validate(activation.license_key)
    
    if not validation["valid"]:
        raise HTTPException(
            status_code=401,
            detail=validation.get("error", "Invalid license")
        )
    
    # Get usage stats
    usage = usage_tracker.get_usage_stats(validation["user_id"])
    
    return {
        "valid": True,
        "user": {
            "id": validation["user_id"],
            "email": validation.get("email"),
            "tier": validation["tier"],
            "expires_at": validation["expires_at"],
        },
        "limits": validation["limits"],
        "usage": usage
    }

@router.post("/generate")
async def generate_license(gen: LicenseGeneration):
    """Generate a new license key (admin only - add auth later)"""
    # TODO: Add admin authentication
    
    import uuid
    user_id = str(uuid.uuid4())
    
    license_key = license_validator.generate_license(
        user_id=user_id,
        email=gen.email,
        tier=gen.tier,
        duration_days=gen.duration_days
    )
    
    return {
        "license_key": license_key,
        "user_id": user_id,
        "tier": gen.tier,
        "expires_in_days": gen.duration_days
    }

@router.get("/usage")
async def get_usage(user = Depends(get_current_user)):
    """Get current user's usage statistics"""
    usage = usage_tracker.get_usage_stats(user["user_id"])
    
    return {
        "user_id": user["user_id"],
        "tier": user["tier"],
        "limits": user["limits"],
        "usage": usage,
        "percentage": {
            "tasks": (usage["active_tasks"] / user["limits"]["max_tasks"]) * 100 if user["limits"]["max_tasks"] > 0 else 0,
            "daily": (usage["daily_tasks"] / user["limits"]["max_tasks_per_day"]) * 100 if user["limits"]["max_tasks_per_day"] > 0 else 0,
        }
    }

@router.post("/checkout")
async def create_checkout_session(checkout: StripeCheckout):
    """Create Stripe checkout session for subscription"""
    
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured")
    
    # Pricing IDs (create these in Stripe Dashboard)
    price_ids = {
        UserTier.STARTER: os.getenv("STRIPE_PRICE_STARTER", "price_starter"),
        UserTier.PRO: os.getenv("STRIPE_PRICE_PRO", "price_pro"),
        UserTier.ELITE: os.getenv("STRIPE_PRICE_ELITE", "price_elite"),
    }
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_ids.get(checkout.tier, price_ids[UserTier.STARTER]),
                "quantity": 1,
            }],
            mode="subscription",
            success_url="https://phantom-bot.com/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://phantom-bot.com/pricing",
            customer_email=checkout.email,
            metadata={
                "tier": checkout.tier,
            }
        )
        
        return {"checkout_url": session.url, "session_id": session.id}
        
    except Exception as e:
        logger.error("Stripe checkout error", error=str(e))
        raise HTTPException(500, f"Checkout failed: {str(e)}")

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except Exception as e:
        logger.error("Webhook signature verification failed", error=str(e))
        raise HTTPException(400, "Invalid signature")
    
    # Handle subscription events
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Generate license key
        import uuid
        user_id = str(uuid.uuid4())
        tier = session["metadata"].get("tier", UserTier.STARTER)
        email = session["customer_email"]
        
        license_key = license_validator.generate_license(
            user_id=user_id,
            email=email,
            tier=tier,
            duration_days=30
        )
        
        # TODO: Send license key via email
        # TODO: Store in database
        
        logger.info(
            "Subscription created",
            user_id=user_id,
            email=email,
            tier=tier,
            session_id=session["id"]
        )
        
        return {"status": "success", "license_key": license_key}
    
    elif event["type"] == "customer.subscription.deleted":
        # Handle subscription cancellation
        # TODO: Revoke license key
        pass
    
    return {"status": "received"}

# Export for use in other modules
__all__ = ["router", "license_validator", "usage_tracker"]
