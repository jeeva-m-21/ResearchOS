.PHONY: help dev docker-up docker-down test lint typecheck build clean

SHELL := /bin/bash

help:
	@echo "ResearchOS Commands"
	@echo "==================="
	@echo "  make dev          — Start full MVP (Docker + Backend + Frontend)"
	@echo "  make docker-up    — Start PostgreSQL + Redis containers only"
	@echo "  make docker-down  — Stop all Docker containers"
	@echo "  make test         — Run backend + frontend tests"
	@echo "  make lint         — Run ruff lint on backend"
	@echo "  make typecheck    — Run mypy type check on backend"
	@echo "  make build        — Build frontend for production"
	@echo "  make clean        — Clean build artifacts"

# ── Start MVP (Docker + Backend + Frontend) ──
dev:
	@./start.sh

# ── Docker services ──────────────────────────
docker-up:
	docker compose up -d postgres redis

docker-down:
	docker compose down

# ── Tests ────────────────────────────────────
test:
	@echo "Running backend tests..."
	@docker exec researchos-backend-1 pytest tests/ -v
	@echo ""
	@echo "Running frontend type check..."
	@cd frontend && npx tsc --noEmit

# ── Lint & Type Check ───────────────────────
lint:
	@docker exec researchos-backend-1 ruff check src/

typecheck:
	@docker exec researchos-backend-1 mypy src/

# ── Build ────────────────────────────────────
build:
	@cd frontend && npm run build

# ── Clean ──────────────────────────────────
clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .ruff_cache .mypy_cache 2>/dev/null || true
	@rm -rf frontend/.next 2>/dev/null || true
	@echo "Cleaned build artifacts"
