# ResearchOS Autonomy State
Last updated: 2026-07-04

## Current task
T-007 — Search: pgvector HNSW index + hybrid search endpoint — DONE

## Log
- 2026-07-04: T-001 DONE. Commit dc9edc3.
- 2026-07-04: T-002 DONE. Commit dc9edc3.
- 2026-07-04: T-003 DONE. Commit 7f939cd.
- 2026-07-04: T-004 DONE. Commit 9c98648.
- 2026-07-04: T-005 DONE. Commit 6793932.
- 2026-07-04: T-006 DONE. Commit f629398.
- 2026-07-04: T-007 DONE. Hybrid search (vector + BM25 + RRF), suggestions via trigram, seed script for 10 nodes, 5 tests covering results/type-filter/pagination/validation/suggestions. Fixed: embedding dim 384→1536, embedding param string format, suggestions DISTINCT query, node_type ENUM cast. All 13 tests pass, ruff clean.
- 2026-07-04: Dev loop optimized — opencode.json fixed (removed alembic deny rule), AGENTS.md references added, docker-python skill created, 4 feedback commands (ruff/mypy/test/feedback) created, all subagent prompts rewritten (shorter + explicit USE THE `write` TOOL)

## Blocked (needs human)
(none)
