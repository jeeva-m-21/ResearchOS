---
description: Autonomously complete the next backlog task
agent: orchestrator
---
Run ONE full delivery cycle: read .opencode/tasks/STATE.md and BACKLOG.md, select the next unblocked TODO, write a plan into STATE.md, delegate implementation + tests, run ruff/mypy and the relevant test, get @reviewer approval, commit, and mark the task DONE. If it fails twice, log a BLOCKED note and move to the next task. $ARGUMENTS