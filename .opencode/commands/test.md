---
description: Run a specific test file. Usage: :test <path> [extra pytest args]
agent: general
---

Run `pytest -v` on the specified test file(s) inside the Docker container. If no path is given, run all tests.

Usage examples:
- `:test tests/test_search.py` — run specific test file
- `:test tests/test_wal.py -k test_append` — run specific test by name
- `:test tests/` — run all tests

Command:
```
docker exec researchos-backend-1 pytest $ARGUMENTS -v
```

Report the pass/fail summary.
