# ResearchOS Autonomy State
Last updated: 2026-07-04

## Current task
T-003 — Fix events router bugs

## Plan
1. @backend: fix duplicate entry in list_event_types (lines 299-303 duplicate "experiment.started")
2. @backend: fix user_id typo on line 386 (user_id.user_id -> user_data.user_id)
3. Run ruff + mypy on events.py
4. Acceptance: POST /events/health returns 200 (or graceful error if Redis unreachable)

## Log
- 2026-07-04: T-001 DONE. Fixed POST /auth/api-keys: cleaned unused imports, trailing whitespace in auth.py and schemas/auth.py. Added tests/test_auth_api_keys.py with 2 passing tests. Commit: dc9edc3 "feat: fix POST /auth/api-keys with lint cleanup and test".
- 2026-07-04: T-002 DONE. Added tests/test_logout.py with 3 tests confirming `POST /auth/logout`: valid refresh_token → 200, missing body → 422, missing refresh_token field → 422. No source changes needed — schema and endpoint already correct. All 5 tests pass, ruff+mypy clean.

## Blocked (needs human)
(none)
