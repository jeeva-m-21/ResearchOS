---
description: Run the full feedback loop (ruff fix → mypy → pytest all). Usage: :feedback <path>
agent: general
---

Run the complete feedback loop on the given file or directory inside Docker. If no path is given, use `src/`.

Steps:
1. `docker exec researchos-backend-1 ruff check {path} --fix`
2. `docker exec researchos-backend-1 mypy --explicit-package-bases {path}`
3. `docker exec researchos-backend-1 pytest tests/ -v`

If ruff leaves errors, check them without --fix. If mypy reports errors, fix them. If tests fail, fix either the source or the test. Report the final status of all three steps.
