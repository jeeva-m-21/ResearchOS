.PHONY: help install dev test docker-build docker-up clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make dev          - Start development server"
	@echo "  make test         - Run all tests"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start Docker Compose"
	@echo "  make clean        - Clean build artifacts"

install:
	cd backend && pip install -e ".[dev]"
	cd sdk/python && pip install -e ".[dev]"
	cd frontend && npm install

dev:
	docker-compose up -d postgres redis
	cd backend && uvicorn src.api.main:app --reload --port 8000 &

test:
	cd backend && pytest tests/
	cd frontend && npm test

docker-build:
	docker build -t researchos-backend:latest ./backend
	docker build -t researchos-frontend:latest ./frontend

docker-up:
	docker-compose up -d

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf .ruff_cache .mypy_cache
