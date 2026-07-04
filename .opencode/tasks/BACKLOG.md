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
- status: DONE
- deps: none
- agents: @backend, @test
- acceptance: POST /events/health returns {"redis": "connected"} or gracefully handled; ruff+mypy clean
- notes: duplicate listing in list_event_types, user_id typo in test_emit_event

## T-004 — Wire event emission into experiment lifecycle
- status: DONE
- deps: T-003
- agents: @backend, @test
- acceptance: creating an experiment emits experiment.started to Redis Stream; test verifies via stream read
- notes: emit events from POST /v1/experiments, POST /v1/experiments/{id}/runs, POST metrics

## T-005 — First event consumer: store events to PostgreSQL
- status: DONE
- deps: T-004
- agents: @backend, @db, @test
- acceptance: test_event_store_persists_experiment_started passes; 8/8 tests pass
- notes: EventStore class created; event-store consumer group wired into lifespan; migration adds events + processed_events tables; commit 6793932

## T-006 — Python SDK: package skeleton + WAL
- status: DONE
- deps: T-003
- agents: @sdk, @test
- acceptance: `python -c "from researchos import WAL; w=WAL('/tmp/test', ...); w.append(...)"` works; 4 WAL tests pass
- notes: protocol/events.py, protocol/validation.py, wal.py created; commit f629398

## T-007 — Search: pgvector HNSW index + hybrid search endpoint
- status: DONE
- deps: T-003
- agents: @backend, @db, @test
- acceptance: GET /v1/search?q=transformer returns 200 with results; type filter works; suggestions work; 5 tests pass
- notes: hybrid search (vector + BM25 + RRF), suggestions via trigram, 10 seed nodes, 5 tests

## T-008 — Notebooks: DB migration + CRUD endpoints
- status: DONE
- deps: none
- agents: @db, @backend, @test
- acceptance: POST /v1/notebooks creates a notebook; GET returns it; 3+ tests pass
- notes: migration for notebooks + blocks tables (see schema docs); basic create/list/get endpoints. Commit c724da6.

## T-009 — Event system: DLQ retry + consumer monitoring
- status: DONE
- deps: T-004
- agents: @backend, @test
- acceptance: DLQ events can be retried via API endpoint; consumer health reports lag
- notes: POST /events/dlq/{group}/retry calls DeadLetterQueue.retry_all(); consumer health endpoint. Commit b83b17b.

## T-010 — SDK: Sync client for offline→online push
- status: DONE
- deps: T-006
- agents: @sdk, @backend, @test
- acceptance: SDK sync() pushes WAL events to /v1/events/batch and returns success
- notes: Syncer class reads WAL, converts to DomainEvent, POSTs batch, tracks offset. Commit caae373.

## T-011 — Persistent Learning Module
- status: DONE
- deps: T-010
- agents: @backend, @architect
- acceptance: python scripts/learn.py --cycle runs and validates (0 failures)
- notes: Evolution cycle (Observe-Analyze-Plan-Implement-Validate-Reflect-Learn-Persist). Memory schemas in .opencode/memory/. Orchestrator prompt updated. Commits caae373 + 818c832.

## T-012 — MCP & Plugin Ecosystem Integration Module
- status: DOING
- deps: T-011
- agents: @architect, @backend, @test
- acceptance: python scripts/ecosystem.py --discover scans MCP servers + plugins and writes mcp_registry.json; python scripts/ecosystem.py --evaluate scores capabilities; ruff + mypy clean
- notes: Discovery scanner for MCP servers, npm/pip plugins, git hooks, LSP servers. Evaluation engine scoring on compatibility, security, maintenance, relevance. Registry persists to .opencode/memory/{mcp_registry.json,capabilities.json}. Integrated into learn.py observe phase.
