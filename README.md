# 👻 Phantom Bot — Advanced Sneaker Automation Suite

> **All-in-one sneaker bot with built-in market intelligence**

## Quick Start

```bash
make install   # Set up Python venv, npm, pre-commit hooks
make dev       # Start backend (:8080) + frontend (:5173)
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8080
- **API Docs (Swagger)**: http://localhost:8080/docs

## Features

| Category          | Highlights                                                               |
| ----------------- | ------------------------------------------------------------------------ |
| **Checkout**      | Shopify (Normal/Fast/Safe), Footsites (FL, Champs, Eastbay, Finish Line) |
| **Monitoring**    | Multi-store Shopify, Footsite keywords, auto-task creation               |
| **Anti-Bot**      | Fingerprint randomization, TLS rotation (JA3/JA4), request humanization  |
| **Intelligence**  | Live StockX/GOAT pricing, profit calculator, release calendar            |
| **Captcha**       | 2Captcha, CapMonster, multi-provider fallback                            |
| **Notifications** | Discord webhooks (success/failure/restock), desktop alerts               |
| **UI**            | Glassmorphism dark theme, WebSocket real-time updates, responsive layout |

## Project Structure

```
phantom-bot/
├── main.py                # Entry point (CLI + server modes)
├── config.yaml            # Main configuration
├── Makefile               # dev, test, lint, format, docker, release
├── phantom/               # Python backend
│   ├── api/               # FastAPI routes + WebSocket
│   ├── core/              # Engine, tasks, proxies, profiles
│   ├── monitors/          # Shopify, Footsite monitoring
│   ├── checkout/          # Site-specific checkout modules
│   ├── evasion/           # Anti-detection (fingerprint, TLS)
│   ├── intelligence/      # Market research, pricing
│   ├── auth/              # License validation, middleware
│   ├── captcha/           # Captcha solving
│   ├── notifications/     # Discord, desktop alerts
│   └── utils/             # Config, crypto, database
├── frontend/              # React + TypeScript + Vite
│   └── src/
│       ├── api/           # Type-safe API client
│       ├── components/    # Dashboard, Tasks, Monitors, etc.
│       ├── hooks/         # useQueries, useWebSocket
│       └── store/         # Zustand state management
├── electron/              # Optional desktop wrapper
└── docs/                  # Documentation
```

## Development

```bash
make dev       # Start backend + frontend dev servers
make lint      # Run ruff (Python) + eslint (TypeScript)
make format    # Auto-format all code
make test      # Run test suite
make typecheck # Run mypy
make docker    # Build Docker image
```

## Build & Startup

### Manual Setup

If you prefer running without `make`:

**1. Frontend (React/Vite)**

```bash
cd frontend
npm install
npm run build   # Builds production assets to frontend/dist/
```

**2. Backend (Python)**

```bash
# Create venv and install deps
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Server Mode (API + WebSockets + Monitors)
python main.py --mode server --port 8080

# Start CLI Mode (Headless Monitors/Helpers)
python main.py --mode cli
```

### Docker Deployment

Build the all-in-one image (serves frontend + backend):

1. **Create Environment File**

    ```bash
    cp .env.example .env
    # Edit .env with your secrets if needed
    ```

2. **Build & Run**
    ```bash
    docker build -t phantom-bot:latest .
    docker run --env-file .env -p 8080:8080 phantom-bot:latest
    ```

## Documentation

| Doc                                  | Purpose                                |
| ------------------------------------ | -------------------------------------- |
| [Setup](docs/setup.md)               | Installation, configuration, first run |
| [Deploy](docs/deploy.md)             | Fly.io, Netlify, Docker deployment     |
| [Architecture](docs/architecture.md) | System design, layering, data flow     |
| [Security](docs/security.md)         | Secrets, auth, audit findings          |
| [Electron](docs/electron.md)         | Building the desktop app               |
| [Roadmap](docs/roadmap.md)           | Feature status and priorities          |
| [Contributing](CONTRIBUTING.md)      | Dev setup, code standards, PR process  |

## Configuration

Edit `config.yaml`:

```yaml
captcha:
    provider: "2captcha"
    api_key: "YOUR_API_KEY"

notifications:
    discord_webhook: "https://discord.com/api/webhooks/..."

performance:
    max_concurrent_tasks: 50
    max_concurrent_monitors: 20
```

## License

Proprietary — All rights reserved.
