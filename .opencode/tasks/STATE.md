# ResearchOS Autonomy State
Last updated: 2026-07-04

## Current task
T-005 — First event consumer: store events to PostgreSQL

## Plan
1. @db: create Alembic migration `003_event_store.py` — create `events` + `processed_events` tables
2. @backend: add `organization_id` to base `DomainEvent` (all concrete events have it)
3. @backend: create `src/infrastructure/events/store.py` — EventStore class that writes to events table via Database singleton
4. @backend: wire a minimal EventStore consumer into the app lifespan (reads experiment.started + metric.logged from Redis Stream, calls EventStore.store_event)
5. @test: write test_event_store.py — starts the consumer, emits an event via the API, waits, verifies row in PostgreSQL
6. @backend/@test: ruff + mypy + specific test feedback loop

## Log
- 2026-07-04: T-001 DONE. Fixed POST /auth/api-keys: cleaned unused imports, trailing whitespace in auth.py and schemas/auth.py. Added tests/test_auth_api_keys.py with 2 passing tests. Commit: dc9edc3 "feat: fix POST /auth/api-keys with lint cleanup and test".
- 2026-07-04: T-002 DONE. Added tests/test_logout.py with 3 tests confirming `POST /auth/logout`: valid refresh_token → 200, missing body → 422, missing refresh_token field → 422. No source changes needed — schema and endpoint already correct. All 5 tests pass, ruff+mypy clean.
- 2026-07-04: T-003 DONE. Fixed events router: removed duplicate event type listing, fixed user_id typo, cleaned 33 ruff lint issues (import ordering, trailing whitespace, unused var). Verified /v1/events/health returns 200 with redis=connected and /v1/events/types returns unique entries. Commit: 7f939cd "fix: events router bugs and lint cleanup (T-003)".
- 2026-07-04: T-004 DONE. Wired event emission into experiment lifecycle. Created shared EventProducer dependency; added RunStarted domain event; refactored all experiment events to inherit from DomainEvent; emitted events on create_experiment, start_run, log_metric. Added 2 acceptance tests. All 7 tests pass, ruff+mypy clean. Commit: 9c98648 "feat: wire event emission into experiment lifecycle (T-004)".

## Blocked (needs human)
(none)
