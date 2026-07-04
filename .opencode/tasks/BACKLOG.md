# ResearchOS Backlog
Ordered, smallest-shippable tasks. The orchestrator works top-down and only starts a task whose deps are DONE.

Task format:
## T-XXX — <title>
- status: TODO | DOING | DONE | BLOCKED
- deps: none | T-YYY
- agents: @backend, @test
- acceptance: <the one test / command that must pass>
- notes: <one line of context>

## T-001 — Fix GET /auth/api-keys 404
- status: DONE
- deps: none
- agents: @backend, @test
- acceptance: test_auth_api_keys_post_creates_key passes; ruff + mypy clean
- notes: endpoint should be POST /auth/api-keys; remove/redirect the bad GET

## T-002 — logout requires refresh_token body
- status: DONE
- deps: none
- agents: @backend, @test
- acceptance: test_logout_with_refresh_token returns 200; missing body returns 422
- notes: validate refresh_token in the request model

## T-003 — Fix events router bugs
- status: TODO
- deps: none
- agents: @backend, @test
- acceptance: POST /events/health returns {"redis": "connected"} or gracefully handled; ruff+mypy clean
- notes: duplicate listing in list_event_types, user_id typo in test_emit_event

## T-004 — Wire event emission into experiment lifecycle
- status: TODO
- deps: T-003
- agents: @backend, @test
- acceptance: creating an experiment emits experiment.started to Redis Stream; test verifies via stream read
- notes: emit events from POST /v1/experiments, POST /v1/experiments/{id}/runs, POST metrics

## T-005 — First event consumer: store events to PostgreSQL
- status: TODO
- deps: T-004
- agents: @backend, @db, @test
- acceptance: consumer writes events from stream to events table; test reads events back
- notes: subclass EventConsumer, register handlers for experiment.started, metric.logged, write to events table

## T-006 — Python SDK: package skeleton + WAL
- status: TODO
- deps: T-003
- agents: @sdk, @test
- acceptance: `pip install sdk/python && python -c "from researchos import WAL; w=WAL('/tmp/test'); w.append(...)"` works
- notes: minimal sdk/python package.json -> pyproject.toml; WAL class with append/read/offset

## T-007 — Search: pgvector HNSW index + hybrid search endpoint
- status: TODO
- deps: T-003
- agents: @backend, @db, @test
- acceptance: GET /v1/search?q=test returns 200 with results array; query uses vector + BM25
- notes: replace stub with real hybrid search; requires existing nodes with embeddings
