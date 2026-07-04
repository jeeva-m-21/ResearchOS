---
name: docker-python
description: Use when running Python tooling (ruff, mypy, pytest, alembic) via Docker. All Python operations must go through `docker exec researchos-backend-1`. DO NOT use this for file editing — only for executing commands inside the container.
---

# Docker Python Tooling (ResearchOS)

This project's Python tooling runs **inside** Docker containers. The host Python is externally-managed and `make install` will fail.

## Quick Reference

| What | Command |
|---|---|
| Start services | `make docker-up` |
| Lint | `docker exec researchos-backend-1 ruff check {path}` |
| Lint + auto-fix | `docker exec researchos-backend-1 ruff check {path} --fix` |
| Type check | `docker exec researchos-backend-1 mypy --explicit-package-bases {path}` |
| Run a specific test | `docker exec researchos-backend-1 pytest {path} -v` |
| Run all tests | `docker exec researchos-backend-1 pytest tests/ -v` |
| New migration | `docker exec researchos-backend-1 alembic revision -m "{message}"` |
| Apply migrations | `docker exec researchos-backend-1 alembic upgrade head` |
| Python one-liner | `docker exec researchos-backend-1 python -c "{code}"` |

## Important Notes

1. **Mypy fix**: Always use `--explicit-package-bases` to avoid "Source file found twice" error caused by both `/app` and `/app/src` being on PYTHONPATH.
2. **Ruff paths**: Changed files are under `backend/src/` (not `backend/src/backend/`). Use correct paths: `ruff check src/api/routes/search.py`.
3. **pgvector**: Install via `docker exec researchos-backend-1 pip install pgvector`. Already in `pyproject.toml` after T-007.
4. **SDK tests**: The SDK (`sdk/python`) is NOT mounted in the backend container. To validate SDK changes, use `docker cp` and `pip install -e --force-reinstall` inside the container.
5. **Dependencies**: Never run `pip install`, `make install`, or create a venv on the host. If something is missing inside the container, run `docker exec researchos-backend-1 pip install {package}`.
