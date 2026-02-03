#!/usr/bin/env python3
"""
Phantom Bot Setup Script
Interactive setup wizard for first-time configuration
"""

import os
import sys
import asyncio
import yaml
from pathlib import Path
from typing import Optional

def print_banner():
    """Print welcome banner"""
    print("\n" + "="*60)
    print("  👻 PHANTOM BOT - Setup Wizard")
    print("="*60 + "\n")

def get_input(prompt: str, default: Optional[str] = None) -> str:
    """Get user input with optional default"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(prompt).strip()
    return value if value else (default or "")

def get_yes_no(prompt: str, default: bool = True) -> bool:
    """Get yes/no input"""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
    
    return response in ('y', 'yes')

def setup_captcha() -> dict:
    """Configure captcha providers"""
    print("\n📝 Captcha Configuration")
    print("-" * 40)
    print("Captcha solving is REQUIRED for checkout.")
    print("Recommended: 2Captcha (https://2captcha.com)")
    print()
    
    providers = {}
    
    if get_yes_no("Configure 2Captcha?", True):
        api_key = get_input("2Captcha API Key")
        if api_key:
            providers["2captcha"] = {"api_key": api_key}
    
    if get_yes_no("Configure CapMonster (optional fallback)?", False):
        api_key = get_input("CapMonster API Key")
        if api_key:
            providers["capmonster"] = {"api_key": api_key}
    
    return {
        "primary_provider": "2captcha",
        "fallback_provider": "capmonster" if "capmonster" in providers else "",
        "providers": providers
    }

def setup_notifications() -> dict:
    """Configure notifications"""
    print("\n🔔 Notification Configuration")
    print("-" * 40)
    print("Get notified of successes, failures, and restocks.")
    print()
    
    discord_config = {"enabled": False}
    
    if get_yes_no("Configure Discord webhooks?", True):
        webhook = get_input("Discord Webhook URL")
        if webhook:
            discord_config = {
                "enabled": True,
                "webhook_url": webhook,
                "success_webhook": get_input("Success Webhook (optional, press Enter to skip)") or "",
                "failure_webhook": get_input("Failure Webhook (optional, press Enter to skip)") or "",
                "restock_webhook": get_input("Restock Webhook (optional, press Enter to skip)") or "",
            }
    
    return {
        "discord": discord_config,
        "desktop": {
            "enabled": get_yes_no("Enable desktop notifications?", True),
            "sound": True
        }
    }

def setup_intelligence() -> dict:
    """Configure market intelligence"""
    print("\n🧠 Market Intelligence Configuration")
    print("-" * 40)
    print("Phantom Bot can track resale prices and calculate profit.")
    print()
    
    enabled = get_yes_no("Enable market intelligence features?", True)
    
    return {
        "enabled": enabled,
        "stockx": {"enabled": enabled},
        "goat": {"enabled": enabled},
        "ebay": {"enabled": enabled},
        "research": {
            "auto_keywords": enabled,
            "trending_products": enabled,
            "profit_threshold": 20
        }
    }

def setup_performance() -> dict:
    """Configure performance settings"""
    print("\n⚡ Performance Configuration")
    print("-" * 40)
    print("Adjust based on your system and proxy capacity.")
    print()
    
    max_tasks = int(get_input("Max concurrent tasks", "50"))
    max_monitors = int(get_input("Max concurrent monitors", "25"))
    
    return {
        "max_concurrent_tasks": max_tasks,
        "max_concurrent_monitors": max_monitors,
        "request_timeout": 30,
        "checkout_timeout": 60,
        "retry_attempts": 3,
        "retry_delay": 1.0
    }

async def test_database():
    """Test database initialization"""
    print("\n💾 Initializing database...")
    try:
        from phantom.utils.database import init_db
        await init_db()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def create_config(config_data: dict):
    """Create configuration file"""
    config_path = Path("config.yaml")
    
    # Load existing config as template
    if config_path.exists():
        with open(config_path, 'r') as f:
            base_config = yaml.safe_load(f)
    else:
        base_config = {}
    
    # Update with user settings
    base_config.update(config_data)
    
    # Write to config.local.yaml
    local_config_path = Path("config.local.yaml")
    with open(local_config_path, 'w') as f:
        yaml.dump(base_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n✅ Configuration saved to {local_config_path}")

def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    required = [
        "fastapi", "uvicorn", "httpx", "aiohttp", "playwright",
        "sqlalchemy", "cryptography", "structlog", "pydantic"
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("\nRun: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    dirs = ["data", "logs", "data/ml_models"]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")

def print_next_steps():
    """Print next steps for user"""
    print("\n" + "="*60)
    print("  🎉 Setup Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("\n1. Add Profiles:")
    print("   - Navigate to web UI > Profiles tab")
    print("   - Add your shipping/billing information")
    print("\n2. Add Proxies:")
    print("   - Navigate to web UI > Proxies tab")
    print("   - Add proxy groups (residential recommended)")
    print("\n3. Start Monitoring:")
    print("   - Navigate to web UI > Monitors tab")
    print("   - Setup Shopify and/or Footsite monitors")
    print("\n4. Create Tasks:")
    print("   - Navigate to web UI > Tasks tab")
    print("   - Create tasks for products you want to cop")
    print("\nTo start the bot:")
    print("\n  Backend:  python main.py --mode server --port 8081")
    print("  Frontend: cd frontend && npm run dev")
    print("\nThen open: http://localhost:5173")
    print("\nDocumentation: See SETUP_GUIDE.md for detailed instructions")
    print("\n" + "="*60 + "\n")

async def main():
    """Main setup flow"""
    print_banner()
    
    print("Welcome to Phantom Bot!")
    print("This wizard will help you configure the bot for first use.\n")
    
    if not get_yes_no("Continue with setup?", True):
        print("Setup cancelled.")
        return
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install dependencies first.")
        return
    
    # Create directories
    create_directories()
    
    # Gather configuration
    config = {
        "app": {
            "name": "Phantom Bot",
            "version": "1.0.0",
            "debug": False,
            "log_level": "INFO"
        }
    }
    
    # Captcha (required)
    config["captcha"] = setup_captcha()
    
    if not config["captcha"]["providers"]:
        print("\n⚠️  Warning: No captcha provider configured.")
        print("Captcha solving is required for most checkouts.")
        if not get_yes_no("Continue anyway?", False):
            return
    
    # Notifications
    config["notifications"] = setup_notifications()
    
    # Intelligence
    config["intelligence"] = setup_intelligence()
    
    # Performance
    config["performance"] = setup_performance()
    
    # Create config file
    create_config(config)
    
    # Initialize database
    if not await test_database():
        print("\n⚠️  Database initialization failed, but you can continue.")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
