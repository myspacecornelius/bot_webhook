# Setup Guide

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- 4GB+ RAM

## Quick Start

```bash
# Install everything (Python venv + npm + pre-commit hooks)
make install

# Start development servers (backend :8080 + frontend :5173)
make dev
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

## Manual Setup

```bash
# 1. Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers (for advanced features)
playwright install chromium

# 4. Install frontend dependencies
cd frontend && npm install && cd ..

# 5. Copy environment config
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Edit `config.yaml` for captcha providers, notifications, and performance tuning:

```yaml
captcha:
    primary_provider: "2captcha"
    providers:
        2captcha:
            api_key: "YOUR_KEY"

notifications:
    discord:
        enabled: true
        webhook_url: "https://discord.com/api/webhooks/..."

performance:
    max_concurrent_tasks: 50
    max_concurrent_monitors: 20
```

## First Run

1. **Add Profile** — Go to Profiles tab, add shipping/billing info
2. **Add Proxies** — Go to Proxies tab, add residential proxies
3. **Start Monitors** — Go to Monitors tab, setup Shopify stores
4. **Create Task** — Go to Tasks tab, create test task on low-value item

## Troubleshooting

| Problem              | Fix                                                 |
| -------------------- | --------------------------------------------------- |
| Module not found     | `pip install -r requirements.txt --force-reinstall` |
| Frontend won't start | `cd frontend && rm -rf node_modules && npm install` |
| Database errors      | `rm data/phantom.db` then restart server            |
| Proxy issues         | Verify format: `http://user:pass@ip:port`           |
| Captcha errors       | Check API key and balance at provider dashboard     |
