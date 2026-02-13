# Security

## Secrets Management

- All sensitive values (API keys, webhook secrets, encryption keys) stored in `.env` — **never committed**.
- Card data encrypted at rest using AES-256 (`phantom/utils/crypto.py`).
- Database credentials use environment variables in production.

## Authentication & Authorization

- License key validation with HMAC signatures (`phantom/auth/license.py`).
- Auth middleware protects API endpoints (`phantom/auth/middleware.py`).
- Usage tracking enforces tier-based limits (`phantom/auth/usage_tracker.py`).

## Network Security

- All outbound HTTP requests should use TLS verification and timeouts.
- Webhook endpoints verify inbound signatures (HMAC-SHA256).
- CORS configured per deployment environment.
- Rate limiting on API endpoints (per key / per IP).

## Audit History

### Issues Found & Fixed

- Duplicate `ProxyGroupCreate` model in routes.py — **merged**
- Unused `MonitorCreate` model — **removed**
- Duplicate `shopify.py` monitor file — **deleted** (370 lines of dead code)

### Recommendations

- [ ] Run `pip audit` monthly for Python dependency CVEs
- [ ] Run `npm audit` monthly for frontend dependency CVEs
- [ ] Add CSP headers in production
- [ ] Implement session management with expiry
- [ ] Add request rate limiting middleware
