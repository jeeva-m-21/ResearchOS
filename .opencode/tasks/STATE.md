# ResearchOS Autonomy State
Last updated: 2026-07-04

## Current task
T-006 — Python SDK: package skeleton + WAL

## Plan
1. @sdk: create `researchos/protocol/` — events.py (BaseEvent, event types), validation.py (serialize/deserialize)
2. @sdk: create `researchos/wal.py` — WAL class with append/read/offset/lock
3. @sdk: update `researchos/__init__.py` to export WAL
4. @test: write `tests/test_wal.py` — tests append, read, offset, crash-safety
5. @orchestrator: verify via `pip install -e sdk/python && python -c "from researchos import WAL; w=WAL('/tmp/test', ...)"`

## Log
- 2026-07-04: T-001 DONE. Fixed POST /auth/api-keys. Commit dc9edc3.
- 2026-07-04: T-002 DONE. Added logout tests. Commit dc9edc3.
- 2026-07-04: T-003 DONE. Fixed events router. Commit 7f939cd.
- 2026-07-04: T-004 DONE. Event emission in experiment lifecycle. Commit 9c98648.
- 2026-07-04: T-005 DONE. Event consumer persists to PostgreSQL. Commit 6793932.

## Blocked (needs human)
(none)
