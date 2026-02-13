# Deployment Guide

## Backend (Fly.io)

The backend deploys to Fly.io using the `Dockerfile` and `fly.toml` at the project root.

```bash
# First-time setup
flyctl launch

# Deploy
flyctl deploy

# Check status
flyctl status
```

**Production URL**: `https://phantom-bot-api.fly.dev`

## Frontend (Netlify)

### Option 1: Netlify Drop (Easiest)

1. Build: `cd frontend && npm run build`
2. Go to https://app.netlify.com/drop
3. Drag `frontend/dist` folder

### Option 2: Git Integration

1. Push code to GitHub
2. Connect repo to Netlify
3. Build settings:
    - **Command**: `cd frontend && npm run build`
    - **Publish dir**: `frontend/dist`
    - **Env vars**: `VITE_API_URL=https://phantom-bot-api.fly.dev/api`

## Docker

```bash
# Build
make docker
# or: docker build -t phantom-bot:latest .

# Run
docker run -p 8080:8080 --env-file .env phantom-bot:latest
```

## Environment Variables

| Variable              | Description                                | Required         |
| --------------------- | ------------------------------------------ | ---------------- |
| `CAPTCHA_API_KEY`     | 2Captcha or CapMonster key                 | Yes              |
| `DISCORD_WEBHOOK_URL` | Discord notifications                      | No               |
| `DATABASE_URL`        | PostgreSQL connection (defaults to SQLite) | No               |
| `SECRET_KEY`          | JWT signing key                            | Yes (production) |

## Production Checklist

- [ ] Set `SECRET_KEY` environment variable
- [ ] Configure PostgreSQL (not SQLite) for multi-user
- [ ] Enable CORS for your frontend domain
- [ ] Set up monitoring / health checks
- [ ] Configure log aggregation (JSON logs)
