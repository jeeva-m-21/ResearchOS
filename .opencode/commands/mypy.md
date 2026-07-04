---
description: Run mypy type checker with --explicit-package-bases. Usage: :mypy <path> [path ...]
agent: general
---

Run `mypy --explicit-package-bases` on the specified Python file(s) inside the Docker container. The `--explicit-package-bases` flag is required because the container has both `/app` and `/app/src` on PYTHONPATH, which otherwise causes "Source file found twice" errors.

Target path(s) from $ARGUMENTS, or if empty: `src/`. Run:

```
docker exec researchos-backend-1 mypy --explicit-package-bases $ARGUMENTS
```

Fix ALL type errors. Report the final error count (must be 0 for clean approval).
