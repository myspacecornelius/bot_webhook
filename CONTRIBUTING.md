# Contributing to Phantom Bot

Thank you for your interest in contributing! This guide will help you get set up.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/phantom-bot
cd phantom-bot

# Install everything (Python venv + npm + pre-commit hooks)
make install

# Start development servers (backend :8080 + frontend :5173)
make dev
```

## Code Quality

We enforce code quality with automated tools. Pre-commit hooks run automatically on every commit.

### Manual checks

```bash
make lint      # Check Python (ruff) + TypeScript (eslint)
make format    # Auto-fix formatting
make typecheck # Run mypy type checking
make test      # Run test suite
```

### Python Style

- **Formatter/Linter**: [ruff](https://docs.astral.sh/ruff/) (replaces black, isort, flake8)
- **Type hints**: Required on all public functions
- **Docstrings**: Required on all classes and public methods
- **Imports**: Sorted automatically by ruff

### TypeScript/React Style

- **Formatter**: [Prettier](https://prettier.io/)
- **Linter**: ESLint with React hooks plugin
- **Types**: Strict TypeScript — no `any` unless justified

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system design.

**Key rules:**

- `phantom/domain/` — Pure models. No I/O, no framework imports.
- `phantom/services/` — Business logic. Calls adapters, never called by adapters.
- `phantom/api/` — Thin HTTP handlers. Validate input → call service → return response.
- `phantom/adapters/` — External integrations (DB, Discord, HTTP clients).

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear, atomic commits
3. Ensure `make lint` and `make test` pass
4. Open a PR with a description of what changed and why
5. Request review

## Commit Messages

Use conventional commits:

```
feat: add webhook HMAC verification
fix: handle timeout in proxy health check
refactor: extract task service from routes
docs: update setup guide for new Makefile
```
