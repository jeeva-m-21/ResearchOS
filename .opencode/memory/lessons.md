# Validated Lessons

Persistent knowledge that prevents repeating mistakes and accelerates development.

## Format

```markdown
### YYYY-MM-DD: Lesson Title
- **Problem**: What went wrong
- **Root Cause**: Why it happened
- **Solution**: How it was fixed
- **Evidence**: Commit hash, test name, or metric
- **Confidence**: High/Medium/Low
- **Reusability**: How often this pattern occurs
- **Tags**: comma-separated keywords
```

---

### 2026-07-04: PYTHONPATH=/app/src Is Wrong for Script Imports
- **Problem**: Scripts in `backend/` couldn't import `from src.xxx import yyy`. Python looked for `/app/src/src/__init__.py` instead of `/app/src/__init__.py`.
- **Root Cause**: Python adds each entry in `PYTHONPATH` to `sys.path` literally. `PYTHONPATH=/app/src` means Python searches `/app/src/` for the `src` module. It finds `/app/src/src/` (directory), which doesn't have `__init__.py` at the expected level.
- **Solution**: `.pth` file adding `/app` to sys.path globally. Or `sys.path.insert(0, '/app')` per script.
- **Evidence**: Commit 38868f6, commit c1ef5f5.
- **Confidence**: High.
- **Reusability**: Every container rebuild loses the .pth file — must re-create.
- **Tags**: PYTHONPATH, docker, imports, sys.path

### 2026-07-04: pgvector Embedding Format Must Be List, Not String
- **Problem**: Search endpoint returned 500. pgvector rejected embedding value.
- **Root Cause**: Embedding was serialized as a string representation of a list (`'[0.1, 0.2, ...]'`) instead of a PostgreSQL array (`{0.1,0.2,...}`).
- **Solution**: Convert embedding list to pgvector-compatible string format `'{0.1,0.2,...}'`.
- **Evidence**: Commit 1d18c42, test test_search_returns_results.
- **Confidence**: High.
- **Reusability**: Any pgvector operation. Use `'{' + ','.join(map(str, values)) + '}'`.
- **Tags**: pgvector, embeddings, postgres, search

### 2026-07-04: Node Type ENUM Needs Cast for Parameterized Queries
- **Problem**: Search with `types` filter returned 0 results. SQLAlchemy didn't cast string to node_type ENUM.
- **Root Cause**: PostgreSQL ENUM types require explicit cast when binding string parameters in parameterized queries.
- **Solution**: Use `::node_type` cast in SQL or cast parameter to text and compare as text.
- **Evidence**: Commit 1d18c42, test test_search_with_type_filter.
- **Confidence**: High.
- **Reusability**: Any custom ENUM type in PostgreSQL with asyncpg.
- **Tags**: postgres, enum, asyncpg, type-casting

### 2026-07-04: Alembic Revision Creates Files with Unique Hash
- **Problem**: Needed to create new migration but couldn't find the generated file.
- **Root Cause**: Alembic generates filenames with random revision hashes (e.g., `06776428afc7_add_notebooks_blocks_tables.py`).
- **Solution**: After `alembic revision -m "..."`, use `ls -t backend/alembic/versions/ | head -1` to find the newest file.
- **Evidence**: T-008 implementation.
- **Confidence**: High.
- **Reusability**: Every new migration.
- **Tags**: alembic, migration, workflow

### 2026-07-04: Agent Model Name Format Varies by Provider
- **Problem**: Subagent creation failed with "Model not found: amazon-bedrock/us.deepseek.v3.2".
- **Root Cause**: The model name format `amazon-bedrock/us.deepseek.v3.2` in subagent configs doesn't match the available model list. The correct format is just `deepseek.v3.2`.
- **Solution**: Use `deepseek.v3.2` (without provider prefix) when the provider is Bedrock.
- **Evidence**: Repeated errors when launching subagents.
- **Confidence**: High.
- **Reusability**: Whenever adding new subagents.
- **Tags**: models, bedorck, agent-config

### 2026-07-04: docker cp to Bind-Mounted Paths Creates Host Files
- **Problem**: Copying files to `/app/` inside the container created duplicate files on the host at `backend/`.
- **Root Cause**: Docker bind mount maps `backend/` → `/app/`. Any file created at `/app/*` inside the container appears on the host at `backend/*`.
- **Solution**: Copy SDK files to a non-mounted path (e.g., `/tmp/`) or use `pip install -e` from the host SDK directory.
- **Evidence**: T-010 cleanup step.
- **Confidence**: High.
- **Reusability**: Always. Check bind mounts before docker cp.
- **Tags**: docker, bind-mount, docker-cp
