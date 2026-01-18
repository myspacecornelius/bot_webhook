#!/usr/bin/env python3
"""
Phantom Bot - Advanced Sneaker Automation Suite
Main entry point
"""

import asyncio
import argparse
import sys
import structlog
import uvicorn

from phantom.core.engine import engine
from phantom.api.routes import create_app
from phantom.utils.config import get_config
from phantom.notifications.discord import DiscordNotifier
from phantom.intelligence.research import ProductResearcher
from phantom.captcha.solver import CaptchaSolver
from phantom.checkout.shopify import ShopifyCheckout


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(colors=True)
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def setup_engine():
    """Initialize and configure the engine"""
    config = get_config()
    
    # Set up notifications
    if config.notifications.discord.webhook_url:
        notifier = DiscordNotifier(
            webhook_url=config.notifications.discord.webhook_url,
            success_webhook=config.notifications.discord.success_webhook,
            failure_webhook=config.notifications.discord.failure_webhook,
        )
        engine.set_notifier(notifier)
    
    # Set up intelligence
    intelligence = ProductResearcher()
    engine.set_intelligence(intelligence)
    
    # Set up captcha solver
    captcha_solver = CaptchaSolver()
    two_captcha_cfg = config.captcha.providers.get("2captcha")
    capmonster_cfg = config.captcha.providers.get("capmonster")
    if two_captcha_cfg and two_captcha_cfg.api_key:
        captcha_solver.configure_2captcha(two_captcha_cfg.api_key)
    if capmonster_cfg and capmonster_cfg.api_key:
        captcha_solver.configure_capmonster(capmonster_cfg.api_key)
    engine.set_captcha_solver(captcha_solver)
    
    # Register checkout modules
    engine.register_checkout_module("shopify", ShopifyCheckout())
    
    logger.info("Engine configured")


async def run_cli():
    """Run in CLI mode"""
    await setup_engine()
    await engine.start()
    
    print("\n" + "="*50)
    print("  PHANTOM BOT - Advanced Sneaker Automation")
    print("="*50 + "\n")
    
    print("Commands:")
    print("  status  - Show bot status")
    print("  start   - Start all tasks")
    print("  stop    - Stop all tasks")
    print("  quit    - Exit the bot")
    print()
    
    try:
        while True:
            cmd = input("phantom> ").strip().lower()
            
            if cmd == "quit" or cmd == "exit":
                break
            elif cmd == "status":
                status = engine.get_status()
                print(f"\nRunning: {status['running']}")
                print(f"Tasks: {status['tasks']}")
                print(f"Proxies: {status['proxies']}")
                print()
            elif cmd == "start":
                count = await engine.task_manager.start_all()
                print(f"Started {count} tasks")
            elif cmd == "stop":
                count = await engine.task_manager.stop_all()
                print(f"Stopped {count} tasks")
            elif cmd == "help":
                print("Commands: status, start, stop, quit")
            else:
                print(f"Unknown command: {cmd}")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    
    await engine.stop()


async def run_server(host: str, port: int):
    """Run in server mode with web UI"""
    await setup_engine()
    await engine.start()
    
    app = create_app()
    
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    finally:
        await engine.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Phantom Bot - Advanced Sneaker Automation")
    parser.add_argument(
        "--mode",
        choices=["cli", "server"],
        default="server",
        help="Run mode (default: server)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Server port (default: 8080)"
    )
    parser.add_argument(
        "--import-valor",
        metavar="PATH",
        help="Import Valor bot configuration"
    )
    
    args = parser.parse_args()
    
    print("""
    ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
    ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
    ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
    ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
    ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
                                                            v1.0.0
    """)
    
    if args.mode == "cli":
        asyncio.run(run_cli())
    else:
        logger.info(f"Starting server on {args.host}:{args.port}")
        asyncio.run(run_server(args.host, args.port))


if __name__ == "__main__":
    main()
