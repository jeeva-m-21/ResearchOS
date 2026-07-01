.PHONY: install lint type test run migrate

install:
	uv sync && pnpm install

lint:
	uv run ruff check . && pnpm -r lint

type:
	uv run mypy apps/api packages/sdk && pnpm -r typecheck

test:
	uv run pytest && pnpm -r test

run:
	docker compose up -d && uv run uvicorn researchos_api.main:app --reload --app-dir apps/api/src

migrate:
	uv run alembic -c apps/api/alembic.ini upgrade head
