---
description: Builds and tests the FastAPI backend + domain + adapters.
mode: subagent
model: deepseek/deepseek-v4-pro
temperature: 0.1
tools: { read: true, write: true, edit: true, bash: true }
---
You own apps/api. Keep routers thin, logic in domain/services, I/O behind
ports. Keep ingest idempotent. Write pytest for every endpoint. Confirm before
schema changes; prefer small alembic migrations.
