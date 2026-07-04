# ResearchOS Autonomy State
Last updated: 2026-07-04

## Current task
T-004 — Wire event emission into experiment lifecycle

## Plan
1. @backend: study experiment routes to find where to emit events
2. @backend: emit `experiment.started` in POST /v1/experiments/
3. @backend: emit `run.started` in POST /v1/experiments/{exp_id}/runs
4. @backend: emit `metric.logged` in POST /v1/experiments/{exp_id}/runs/{run_id}/metrics
5. @test: write test that creates experiment+run+metric and verifies events appear in Redis Stream
6. @test: ruff + mypy + pytest feedback loop

## Log
- 2026-07-04: T-001 DONE. Fixed POST /auth/api-keys: cleaned unused imports, trailing whitespace in auth.py and schemas/auth.py. Added tests/test_auth_api_keys.py with 2 passing tests. Commit: dc9edc3 "feat: fix POST /auth/api-keys with lint cleanup and test".
- 2026-07-04: T-002 DONE. Added tests/test_logout.py with 3 tests confirming `POST /auth/logout`: valid refresh_token → 200, missing body → 422, missing refresh_token field → 422. No source changes needed — schema and endpoint already correct. All 5 tests pass, ruff+mypy clean.
- 2026-07-04: T-003 DONE. Fixed events router: removed duplicate event type listing, fixed user_id typo, cleaned 33 ruff lint issues (import ordering, trailing whitespace, unused var). Verified /v1/events/health returns 200 with redis=connected and /v1/events/types returns unique entries. Commit: 7f939cd "fix: events router bugs and lint cleanup (T-003)".

## Blocked (needs human)
(none)
