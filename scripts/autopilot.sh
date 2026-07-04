#!/usr/bin/env bash
# Run OpenCode fully hands-free with an iteration cap and a full log.
# Usage: ./scripts/autopilot.sh [max_iterations]
set -euo pipefail

MAX_ITERS="${1:-20}"
LOG=".opencode/tasks/autopilot.log"

make docker-up   # ensure Postgres + Redis are up

for i in $(seq 1 "$MAX_ITERS"); do
  echo "=== autopilot iteration $i / $MAX_ITERS ===" | tee -a "$LOG"
  opencode run --agent orchestrator --dangerously-skip-permissions "/next" 2>&1 | tee -a "$LOG"
  if tail -n 40 "$LOG" | grep -qi "backlog clear"; then
    echo "Backlog clear — stopping." | tee -a "$LOG"
    break
  fi
done