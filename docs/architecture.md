# Architecture

## System Overview

Phantom Bot is a monorepo with three packages:

| Package  | Tech              | Path                  | Purpose                                      |
| -------- | ----------------- | --------------------- | -------------------------------------------- |
| Backend  | Python / FastAPI  | `phantom/`, `main.py` | API server, business logic, data persistence |
| Frontend | React / TS / Vite | `frontend/`           | Dashboard UI                                 |
| Desktop  | Electron          | `electron/`           | Optional native wrapper                      |

```
┌─────────────┐     HTTP/WS      ┌──────────────┐
│   Frontend   │ ◄──────────────► │   Backend    │
│  (React/TS)  │                  │  (FastAPI)   │
└─────────────┘                  └──────┬───────┘
       │                                │
       │  (optional)                    │
┌──────┴──────┐              ┌──────────┴──────────┐
│  Electron   │              │  SQLite / PostgreSQL │
│   Shell     │              └─────────────────────┘
└─────────────┘
```

## Backend Layering (Target)

```
phantom/
├── domain/          # Pure models + business rules (no I/O)
├── services/        # Use-case orchestration
├── api/             # Thin FastAPI route handlers
├── adapters/        # DB, HTTP clients, Discord, WebSockets
├── workers/         # Background job handlers
├── core/            # Engine, task/proxy/profile managers
├── monitors/        # Site monitoring (Shopify, Footsites)
├── checkout/        # Checkout flow modules
├── evasion/         # Anti-bot (fingerprint, TLS, humanizer)
├── intelligence/    # Market research, pricing, calendar
├── captcha/         # Captcha solving integrations
├── notifications/   # Discord, desktop alerts
├── auth/            # License validation, middleware
└── utils/           # Config, crypto, database
```

**Import rules:**

- `domain/` imports nothing from `phantom/` (pure Python only)
- `services/` imports from `domain/` and `adapters/`
- `api/` imports from `services/` and `domain/`
- `adapters/` imports from `domain/` only

## Frontend Structure

```
frontend/src/
├── api/             # Type-safe HTTP client (client.ts, types.ts)
├── components/      # UI components (Dashboard, Tasks, Monitors, etc.)
├── hooks/           # Custom hooks (useQueries, useWebSocket)
├── store/           # Zustand state management
├── lib/             # Utilities
└── types/           # TypeScript type definitions
```

## Key Design Decisions

1. **Monorepo with boundaries** — Single repo, but frontend only talks to backend via HTTP. No shared runtime.
2. **FastAPI + Pydantic** — Auto-generated OpenAPI schema serves as the contract.
3. **Singleton engine** — `PhantomEngine` is a singleton orchestrating all components.
4. **SQLAlchemy + aiosqlite** — Async database access, can swap to PostgreSQL.
5. **structlog** — Structured logging throughout backend.

## Data Flow

1. **Webhook/Monitor → Event** — Monitors detect products → emit events
2. **Event → Task** — High-priority events auto-create checkout tasks
3. **Task → Checkout** — Engine routes tasks to site-specific checkout modules
4. **Checkout → Notification** — Results sent via Discord webhooks
