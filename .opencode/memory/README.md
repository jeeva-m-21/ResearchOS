# ResearchOS Memory System

Persistent project memory that survives agent restarts, container rebuilds, and model changes.

## Structure

```
memory/
  README.md           — This file
  architecture.md     — Architecture evolution log
  decisions.md        — Decision history with rationale
  lessons.md          — Validated lessons learned
  improvements.json   — Improvement proposals (scored, prioritized)
  failures.json       — Root cause analysis entries
  metrics.json        — Historical build/test/performance metrics
  opportunities.json  — Opportunity scanner findings
  workflows.json      — Workflow evolution history
  prompt_history.json — Agent prompt version tracking
```

## Rules

1. **Append, never overwrite** — New entries go on top, old context preserved.
2. **Timestamps** — Every entry has an ISO 8601 UTC timestamp.
3. **Confidence** — Only persist validated knowledge. Assumptions are documented as hypotheses.
4. **Evidence** — Every lesson includes related files, commit hash, and validation method.
5. **Rollback** — Every change is reversible via git.

## Usage

- **Before a task**: Read `lessons.md` and `decisions.md` to avoid repeating mistakes.
- **After a task**: Run the evolution cycle to observe, analyze, learn, and persist.
- **When blocked**: Check `failures.json` for prior occurrences of similar issues.
- **When planning**: Check `opportunities.json` for pre-scoped improvement candidates.
