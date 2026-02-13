# Phantom Bot — Development Commands
# Usage: make <target>

.DEFAULT_GOAL := help
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

# ─── Development ──────────────────────────────────────────────

.PHONY: dev
dev: ## Start backend + frontend dev servers
	@echo "Starting backend on :8080 and frontend on :5173..."
	@$(MAKE) -j2 dev-backend dev-frontend

.PHONY: dev-backend
dev-backend: ## Start backend dev server
	$(VENV)/bin/python main.py --mode server --port 8080

.PHONY: dev-frontend
dev-frontend: ## Start frontend dev server
	cd frontend && npm run dev

# ─── Quality ──────────────────────────────────────────────────

.PHONY: lint
lint: ## Run all linters
	$(VENV)/bin/ruff check phantom/ main.py
	$(VENV)/bin/ruff format --check phantom/ main.py
	cd frontend && npm run lint

.PHONY: format
format: ## Auto-format all code
	$(VENV)/bin/ruff format phantom/ main.py
	$(VENV)/bin/ruff check --fix phantom/ main.py
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,css,json}"

.PHONY: typecheck
typecheck: ## Run type checking
	$(VENV)/bin/mypy phantom/ --ignore-missing-imports

.PHONY: test
test: ## Run all tests
	$(PYTEST) tests/ -v --tb=short

.PHONY: test-cov
test-cov: ## Run tests with coverage
	$(PYTEST) tests/ -v --tb=short --cov=phantom --cov-report=term-missing

# ─── Setup ────────────────────────────────────────────────────

.PHONY: install
install: ## Install all dependencies
	$(PYTHON) -m venv $(VENV) || true
	$(PIP) install -r requirements.txt
	$(PIP) install pre-commit ruff
	$(VENV)/bin/pre-commit install
	cd frontend && npm install

# ─── Build & Deploy ───────────────────────────────────────────

.PHONY: build
build: ## Build frontend for production
	cd frontend && npm run build

.PHONY: docker
docker: ## Build Docker image
	docker build -t phantom-bot:latest .

.PHONY: release
release: build ## Build production release
	@echo "Production frontend built in frontend/dist/"
	@echo "Deploy with: fly deploy (or docker push)"

# ─── Utilities ────────────────────────────────────────────────

.PHONY: clean
clean: ## Remove build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
