---
description: Keep shipping until the backlog is clear or blocked
agent: orchestrator
---
Repeat the delivery cycle continuously until every task in .opencode/tasks/BACKLOG.md is DONE or BLOCKED. After each task, append a one-line result to STATE.md and continue automatically without waiting for input. Stop only when (a) no unblocked TODO remains, or (b) you reach your step limit. Then print a summary of what shipped and what is blocked. $ARGUMENTS