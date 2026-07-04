---
description: Run ruff linter with auto-fix on the given path(s). Usage: :ruff <path> [path ...]
agent: general
---

Run `ruff check --fix` on the specified Python file(s) inside the Docker container. Fix ALL reported errors. If no path is given, check the entire `src/` tree.

Target path(s) from $ARGUMENTS, or if empty: `src/`. Run:

```
docker exec researchos-backend-1 ruff check $ARGUMENTS --fix
```

If errors remain after --fix, run without --fix to see them and fix manually. Report the final error count (must be 0 for approval).
