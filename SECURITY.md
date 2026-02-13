# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 1.x     | ✅        |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT open a public issue.**
2. Email **security@phantom-bot.com** with:
    - Description of the vulnerability
    - Steps to reproduce
    - Potential impact
3. You will receive an acknowledgment within **48 hours**.
4. We will work with you to understand and resolve the issue before public disclosure.

## Security Practices

### Secrets Management

- All sensitive values (API keys, webhook secrets, encryption keys) are stored in `.env` files or environment variables — **never committed to git**.
- Card data is encrypted at rest using AES-256 (see `phantom/utils/crypto.py`).

### Authentication

- License key validation with HMAC signatures.
- Auth middleware protects all API endpoints (see `phantom/auth/middleware.py`).

### Dependencies

- Dependencies are pinned with minimum versions in `requirements.txt` and `package-lock.json`.
- Run `pip audit` and `npm audit` periodically to check for known vulnerabilities.

### Network

- All outbound HTTP requests should use timeouts and TLS verification.
- Webhook endpoints verify inbound signatures (HMAC-SHA256).
