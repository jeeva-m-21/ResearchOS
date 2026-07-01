# Research OS — Agent Rules

## What we're building
Experiment-memory platform. Wedge: "never lose an experiment."
Stack: Python (FastAPI + SDK), Next.js/TS, Postgres+pgvector (Supabase), R2.

## Golden rules
- Small, reviewable diffs. One concern per change.
- Never invent APIs — match the contract in docs/.
- Tests with every backend/SDK change (pytest); type-check web (tsc).
- Ingest endpoints MUST stay idempotent (client event ids).
- Secrets only via env vars. Never commit keys.
- Ask before schema changes or new dependencies.
- Respect the frozen v1 scope; reject deferred features.

## Architecture
- Backend is hexagonal: domain -> ports -> adapters. Domain has no I/O.
- Swap providers via adapters/llm/registry.py. Never hard-code a vendor.

## Commands
- install: make install
- api:  make run
- test: make test | lint: make lint | types: make type

## Style
- Python: ruff + mypy strict, type hints everywhere.
- TS: eslint + prettier, no any.
