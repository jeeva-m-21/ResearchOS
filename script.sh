#!/usr/bin/env bash
# =============================================================================
#  Research OS — one-shot monorepo scaffold
#  Usage: create an empty folder, cd into it, then:  bash bootstrap.sh
# =============================================================================
set -euo pipefail

echo "==> directory tree"
mkdir -p \
  .opencode/agent .github/workflows docs infra/terraform infra/deploy \
  apps/api/src/researchos_api/api/v1 \
  apps/api/src/researchos_api/domain/services \
  apps/api/src/researchos_api/ports \
  apps/api/src/researchos_api/adapters/db \
  apps/api/src/researchos_api/adapters/llm \
  apps/api/src/researchos_api/adapters/embeddings \
  apps/api/src/researchos_api/adapters/storage \
  apps/api/src/researchos_api/adapters/queue \
  apps/api/src/researchos_api/agents \
  apps/api/src/researchos_api/workers \
  apps/api/src/researchos_api/observability \
  apps/api/migrations apps/api/tests/unit apps/api/tests/integration \
  apps/web/src/app apps/web/src/features/notebook \
  apps/web/src/components/ui apps/web/src/lib apps/web/src/styles apps/web/e2e \
  packages/sdk/src/researchos/capture \
  packages/sdk/src/researchos/integrations packages/sdk/tests

# ---------------------------------------------------------------- root files
echo "==> root files"
cat > README.md <<'EOF'
# Research OS
Experiment-memory platform. Wedge: "never lose an experiment."
Stack: Python (FastAPI + SDK), Next.js/TS, Postgres+pgvector (Supabase), R2.

## Quickstart
    make install
    make run
EOF

cat > .gitignore <<'EOF'
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
node_modules/
.next/
dist/
.env
.env.*
!.env.example
.DS_Store
EOF

cat > .env.example <<'EOF'
# Copy to .env and fill in. NEVER commit .env.
RESEARCHOS_API_KEY=
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/researchos
REDIS_URL=redis://localhost:6379/0
S3_BUCKET=researchos-artifacts
S3_ENDPOINT_URL=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
DEEPSEEK_API_KEY=
EMBEDDING_API_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000
GITHUB_TOKEN=
SUPABASE_TOKEN=
EOF

cat > pnpm-workspace.yaml <<'EOF'
packages:
  - "apps/*"
  - "packages/*"
EOF

cat > package.json <<'EOF'
{
  "name": "research-os",
  "private": true,
  "packageManager": "pnpm@9",
  "scripts": {
    "dev": "turbo run dev",
    "lint": "turbo run lint",
    "typecheck": "turbo run typecheck",
    "test": "turbo run test",
    "build": "turbo run build"
  },
  "devDependencies": { "turbo": "^2.0.0" }
}
EOF

cat > turbo.json <<'EOF'
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "dev": { "cache": false, "persistent": true },
    "lint": {}, "typecheck": {}, "test": {},
    "build": { "dependsOn": ["^build"], "outputs": [".next/**", "dist/**"] }
  }
}
EOF

cat > pyproject.toml <<'EOF'
[tool.uv.workspace]
members = ["apps/api", "packages/sdk"]

[tool.ruff]
line-length = 100
target-version = "py311"
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
strict = true

[tool.pytest.ini_options]
addopts = "-q"
EOF

cat > docker-compose.yml <<'EOF'
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: researchos
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
  redis:
    image: redis:7
    ports: ["6379:6379"]
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio12345
    ports: ["9000:9000", "9001:9001"]
EOF

cat > Makefile <<'EOF'
.PHONY: install lint type test run migrate

install:
	uv sync && pnpm install

lint:
	uv run ruff check . && pnpm -r lint

type:
	uv run mypy apps/api packages/sdk && pnpm -r typecheck

test:
	uv run pytest && pnpm -r test

run:
	docker compose up -d && uv run uvicorn researchos_api.main:app --reload --app-dir apps/api/src

migrate:
	uv run alembic -c apps/api/alembic.ini upgrade head
EOF

cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-yaml
      - id: detect-private-key
EOF

cat > .github/workflows/ci.yml <<'EOF'
name: ci
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - run: make install
      - run: make lint
      - run: make type
      - run: make test
EOF

# ---------------------------------------------------------------- opencode
echo "==> opencode config"
cat > opencode.json <<'EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "model": "deepseek/deepseek-v4-pro",
  "small_model": "deepseek/deepseek-chat",
  "autoupdate": true,
  "provider": {
    "deepseek": { "options": { "timeout": 600000, "setCacheKey": true } }
  },
  "mcp": {
    "github": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
      "environment": { "GITHUB_PERSONAL_ACCESS_TOKEN": "{env:GITHUB_TOKEN}" },
      "enabled": true
    },
    "supabase": {
      "type": "local",
      "command": ["npx", "-y", "@supabase/mcp-server-supabase"],
      "environment": { "SUPABASE_ACCESS_TOKEN": "{env:SUPABASE_TOKEN}" },
      "enabled": true
    },
    "context7": {
      "type": "local",
      "command": ["npx", "-y", "@upstash/context7-mcp"],
      "enabled": true
    }
  }
}
EOF

# ---------------------------------------------------------------- AGENTS.md
echo "==> AGENTS.md files"
cat > AGENTS.md <<'EOF'
# Research OS — Agent Rules

## What we're building
Experiment-memory platform. Wedge: "never lose an experiment."
Stack: Python (FastAPI + SDK), Next.js/TS, Postgres+pgvector (Supabase), R2.

## Golden rules
- Small, reviewable diffs. One concern per change.
- Never invent APIs — match the contract in docs/.
- Tests with every backend/SDK change (pytest); type-check web (tsc).
- Ingest endpoints MUST stay idempotent (client event ids).
- Secrets only via env vars. Never commit keys.
- Ask before schema changes or new dependencies.
- Respect the frozen v1 scope; reject deferred features.

## Architecture
- Backend is hexagonal: domain -> ports -> adapters. Domain has no I/O.
- Swap providers via adapters/llm/registry.py. Never hard-code a vendor.

## Commands
- install: make install
- api:  make run
- test: make test | lint: make lint | types: make type

## Style
- Python: ruff + mypy strict, type hints everywhere.
- TS: eslint + prettier, no any.
EOF

cat > apps/api/AGENTS.md <<'EOF'
# apps/api rules
- Routers stay thin: parse -> call a domain service -> serialize.
- Business logic in domain/services. Domain imports no framework/DB.
- Reach DB/LLM/storage only through ports/. Implement in adapters/.
- Every endpoint gets a pytest. Ingest must be idempotent.
- Migrations via alembic; never edit the DB by hand.
EOF

cat > packages/sdk/AGENTS.md <<'EOF'
# packages/sdk rules
- Public API stays 2-line simple: init / log_params / log_metric / finish.
- Everything buffers to local disk and resyncs (Colab sessions drop).
- Framework hooks are strategies under integrations/.
- This ships to PyPI: keep the README and public surface pristine.
EOF

cat > apps/web/AGENTS.md <<'EOF'
# apps/web rules
- Next.js App Router. Feature-sliced under src/features.
- UI primitives from components/ui (shadcn). Notebook uses TipTap.
- public/[slug] pages must be server-rendered for SEO.
- All API calls go through src/lib/api.
EOF

# ---------------------------------------------------------------- subagents
echo "==> subagents"
cat > .opencode/agent/build-orchestrator.md <<'EOF'
---
description: Plans work, splits it across specialists, gates on tests. Does not write code itself.
mode: primary
model: deepseek/deepseek-v4-pro
temperature: 0.2
tools: { read: true, write: false, edit: false, bash: true }
---
You are the build orchestrator for Research OS. Read AGENTS.md and docs/.
Decompose each task, delegate to the right subagent, and do NOT consider work
done until reviewer-agent approves and test-agent is green. Keep changes small
and strictly within the frozen v1 scope.
EOF

cat > .opencode/agent/backend-agent.md <<'EOF'
---
description: Builds and tests the FastAPI backend + domain + adapters.
mode: subagent
model: deepseek/deepseek-v4-pro
temperature: 0.1
tools: { read: true, write: true, edit: true, bash: true }
---
You own apps/api. Keep routers thin, logic in domain/services, I/O behind
ports. Keep ingest idempotent. Write pytest for every endpoint. Confirm before
schema changes; prefer small alembic migrations.
EOF

cat > .opencode/agent/sdk-agent.md <<'EOF'
---
description: Builds the researchos Python SDK (capture, hooks, resync).
mode: subagent
model: deepseek/deepseek-v4-pro
temperature: 0.1
tools: { read: true, write: true, edit: true, bash: true }
---
You own packages/sdk. Keep the public API 2-line simple. Buffer to disk and
resync. Framework hooks are strategies under integrations/. Ships to PyPI —
keep the surface and README clean. Test with pytest.
EOF

cat > .opencode/agent/frontend-agent.md <<'EOF'
---
description: Builds the Next.js web app (App Router, shadcn, TipTap).
mode: subagent
model: deepseek/deepseek-v4-pro
temperature: 0.3
tools: { read: true, write: true, edit: true, bash: true }
---
You own apps/web. Feature-sliced under src/features. Use components/ui (shadcn).
Notebook uses TipTap. public/[slug] must be server-rendered for SEO. Network
calls go through src/lib/api. Keep it typed (no any).
EOF

cat > .opencode/agent/db-migration-agent.md <<'EOF'
---
description: Owns the database schema and alembic migrations only.
mode: subagent
model: deepseek/deepseek-v4-pro
temperature: 0.0
tools: { read: true, write: true, edit: true, bash: true }
---
You own apps/api/migrations and the SQLAlchemy models. Generate small,
reversible alembic migrations. No destructive changes without explicit
confirmation and a note in the migration.
EOF

cat > .opencode/agent/infra-devops-agent.md <<'EOF'
---
description: Owns infra/, CI, Docker, and deploy config.
mode: subagent
model: deepseek/deepseek-v4-pro
temperature: 0.1
tools: { read: true, write: true, edit: true, bash: true }
---
You own infra/, .github/workflows, Dockerfiles, docker-compose, fly/vercel
config. Keep local == CI. Secrets only via env. Pin versions. Reproducible
deploys.
EOF

cat > .opencode/agent/test-agent.md <<'EOF'
---
description: Writes and repairs tests across the repo.
mode: subagent
model: deepseek/deepseek-v4-pro
temperature: 0.0
tools: { read: true, write: true, edit: true, bash: true }
---
You write pytest (unit + integration) and web tests. Unit tests hit the domain
with fake adapters (no I/O). Integration tests use docker-compose services.
Only create/modify files under tests/ and e2e/.
EOF

cat > .opencode/agent/security-agent.md <<'EOF'
---
description: Read-only security audit (secrets, authz, deps).
mode: subagent
model: deepseek/deepseek-v4-pro
temperature: 0.0
tools: { read: true, write: false, edit: false, bash: true }
---
You audit for leaked secrets, missing authorization checks, unsafe SQL, and
vulnerable dependencies. Report findings; never modify code. Verify API keys
are hashed and project visibility is enforced server-side.
EOF

cat > .opencode/agent/docs-agent.md <<'EOF'
---
description: Maintains docs/, READMEs, and the changelog.
mode: subagent
model: deepseek/deepseek-v4-pro
temperature: 0.3
tools: { read: true, write: true, edit: true, bash: false }
---
You keep docs/ and READMEs in sync with the code. Only edit documentation
files. Keep packages/sdk/README.md accurate — it is the PyPI landing page.
EOF

cat > .opencode/agent/reviewer-agent.md <<'EOF'
---
description: Read-only diff review + runs tests. Gates merges.
mode: subagent
model: deepseek/deepseek-v4-pro
temperature: 0.0
tools: { read: true, write: false, edit: false, bash: true }
---
You review diffs for correctness, scope creep, and the golden rules in
AGENTS.md. Run the tests. Approve only if they pass and the change is minimal.
Never modify code — request changes instead.
EOF

# ---------------------------------------------------------------- backend
echo "==> backend skeleton"
cat > apps/api/pyproject.toml <<'EOF'
[project]
name = "researchos-api"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "pydantic>=2",
  "pydantic-settings>=2",
  "sqlalchemy>=2",
  "psycopg[binary]>=3",
  "alembic>=1.13",
  "pgvector>=0.3",
  "redis>=5",
  "rq>=1.16",
  "boto3>=1.34",
  "httpx>=0.27",
]
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
[tool.hatch.build.targets.wheel]
packages = ["src/researchos_api"]
EOF

cat > apps/api/alembic.ini <<'EOF'
[alembic]
script_location = migrations
sqlalchemy.url = ${DATABASE_URL}
EOF

# python package markers
find apps/api/src/researchos_api -type d -exec touch {}/__init__.py \;

cat > apps/api/src/researchos_api/config.py <<'EOF'
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/researchos"
    redis_url: str = "redis://localhost:6379/0"
    s3_bucket: str = "researchos-artifacts"
    deepseek_api_key: str = ""
    embedding_api_key: str = ""


settings = Settings()
EOF

cat > apps/api/src/researchos_api/main.py <<'EOF'
from fastapi import FastAPI

from .api.v1 import ask, experiments, ingest, public, search


def create_app() -> FastAPI:
    app = FastAPI(title="Research OS API", version="0.1.0")
    for mod in (experiments, ingest, search, ask):
        app.include_router(mod.router, prefix="/v1")
    app.include_router(public.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
EOF

# routers (unquoted heredoc so $r expands)
for r in experiments ingest search ask public; do
cat > apps/api/src/researchos_api/api/v1/$r.py <<EOF
from fastapi import APIRouter

router = APIRouter(tags=["$r"])


@router.get("/$r/ping")
def ping() -> dict[str, str]:
    return {"router": "$r"}
EOF
done

# ports
cat > apps/api/src/researchos_api/ports/llm.py <<'EOF'
from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, prompt: str, **kwargs) -> str: ...
EOF

cat > apps/api/src/researchos_api/ports/embeddings.py <<'EOF'
from typing import Protocol, Sequence


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...
EOF

cat > apps/api/src/researchos_api/ports/storage.py <<'EOF'
from typing import Protocol


class ObjectStore(Protocol):
    def presign_put(self, key: str) -> str: ...
    def get_url(self, key: str) -> str: ...
EOF

# adapters: pluggable LLM factory
cat > apps/api/src/researchos_api/adapters/llm/deepseek.py <<'EOF'
import httpx


class DeepSeekProvider:
    """Concrete LLMProvider. Swap freely via the registry."""

    def __init__(self, model: str = "deepseek-v4-pro") -> None:
        self.model = model
        self._client = httpx.Client(timeout=600)

    def complete(self, prompt: str, **kwargs) -> str:
        # TODO: wire the real DeepSeek / opencode-compatible endpoint
        raise NotImplementedError
EOF

cat > apps/api/src/researchos_api/adapters/llm/registry.py <<'EOF'
from .deepseek import DeepSeekProvider

_PROVIDERS = {"deepseek": DeepSeekProvider}


def get_llm(name: str = "deepseek"):
    """Factory: name -> LLMProvider. Add providers here, not in the domain."""
    return _PROVIDERS[name]()
EOF

cat > apps/api/src/researchos_api/domain/services/recall_service.py <<'EOF'
from ...ports.embeddings import Embedder
from ...ports.llm import LLMProvider


class RecallService:
    """Ask/RAG: retrieve -> rerank -> generate -> cite (no citation, no claim)."""

    def __init__(self, llm: LLMProvider, embedder: Embedder) -> None:
        self.llm = llm
        self.embedder = embedder

    def ask(self, question: str) -> dict:
        # TODO: hybrid retrieval over pgvector + grounded answer with block ids
        return {"answer": "", "citations": []}
EOF

cat > apps/api/tests/unit/test_health.py <<'EOF'
from fastapi.testclient import TestClient

from researchos_api.main import app


def test_health() -> None:
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
EOF
touch apps/api/tests/__init__.py apps/api/tests/conftest.py

cat > apps/api/Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["uv", "run", "uvicorn", "researchos_api.main:app", "--host", "0.0.0.0", "--app-dir", "src"]
EOF

# ---------------------------------------------------------------- sdk
echo "==> sdk skeleton"
cat > packages/sdk/pyproject.toml <<'EOF'
[project]
name = "researchos"
version = "0.1.0"
description = "Never lose an experiment again."
readme = "README.md"
requires-python = ">=3.9"
dependencies = ["httpx>=0.27"]
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
[tool.hatch.build.targets.wheel]
packages = ["src/researchos"]
EOF

cat > packages/sdk/README.md <<'EOF'
# researchos
Track any ML experiment in 2 lines. This README is the PyPI landing page.

    !pip install researchos
    import researchos as ros
    ros.init(project="my-model")
EOF

cat > packages/sdk/src/researchos/__init__.py <<'EOF'
from .client import Client

_client: Client | None = None


def init(project: str, api_key: str | None = None) -> None:
    global _client
    _client = Client(project=project, api_key=api_key)


def log_params(params: dict) -> None:
    assert _client is not None, "call ros.init() first"
    _client.log_params(params)


def log_metric(key: str, value: float, step: int | None = None) -> None:
    assert _client is not None, "call ros.init() first"
    _client.log_metric(key, value, step)


def log_artifact(kind: str, obj) -> None:
    assert _client is not None, "call ros.init() first"
    _client.log_artifact(kind, obj)


def finish() -> None:
    assert _client is not None, "call ros.init() first"
    _client.finish()
EOF

cat > packages/sdk/src/researchos/client.py <<'EOF'
import os


class Client:
    """Idempotent, buffered ingest client. Resyncs if the session drops."""

    def __init__(self, project: str, api_key: str | None = None) -> None:
        self.project = project
        self.api_key = api_key or os.getenv("RESEARCHOS_API_KEY", "")

    def log_params(self, params: dict) -> None: ...
    def log_metric(self, key: str, value: float, step: int | None = None) -> None: ...
    def log_artifact(self, kind: str, obj) -> None: ...
    def finish(self) -> None: ...  # snapshots code + env, computes repro score
EOF

touch packages/sdk/src/researchos/buffer.py \
      packages/sdk/src/researchos/capture/code.py \
      packages/sdk/src/researchos/capture/env.py \
      packages/sdk/src/researchos/capture/magic.py \
      packages/sdk/src/researchos/integrations/pytorch.py \
      packages/sdk/src/researchos/integrations/keras.py \
      packages/sdk/src/researchos/integrations/sklearn.py \
      packages/sdk/src/researchos/integrations/hf_trainer.py

cat > packages/sdk/tests/test_import.py <<'EOF'
import researchos as ros


def test_public_surface() -> None:
    for fn in ("init", "log_params", "log_metric", "log_artifact", "finish"):
        assert hasattr(ros, fn)
EOF

# ---------------------------------------------------------------- web
echo "==> web skeleton"
cat > apps/web/package.json <<'EOF'
{
  "name": "@research-os/web",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run"
  },
  "dependencies": { "next": "^15", "react": "^19", "react-dom": "^19" },
  "devDependencies": { "typescript": "^5", "vitest": "^2" }
}
EOF

cat > apps/web/tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "strict": true,
    "jsx": "preserve",
    "moduleResolution": "bundler",
    "target": "ES2022",
    "lib": ["dom", "ES2022"],
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  }
}
EOF

cat > apps/web/next.config.ts <<'EOF'
import type { NextConfig } from "next"
const config: NextConfig = { reactStrictMode: true }
export default config
EOF

cat > apps/web/src/app/page.tsx <<'EOF'
export default function Home() {
  return <main>Research OS — never lose an experiment.</main>
}
EOF

cat > apps/web/src/lib/api.ts <<'EOF'
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) throw new Error(`API ${res.status}`)
  return res.json() as Promise<T>
}
EOF

# ---------------------------------------------------------------- docs + git
echo "==> docs + git"
cat > docs/README.md <<'EOF'
# docs
Mirror the Notion specs here so agents can read them offline:
- master-spec.md (data model, API, SDK, infra)
- optimized-product.md, product-plan.md
EOF

git init -q 2>/dev/null || true

echo
echo "✅ Research OS scaffolded."
echo "Next:"
echo "  1) cp .env.example .env   # fill in keys"
echo "  2) make install"
echo "  3) make run               # http://localhost:8000/health"
echo "  4) opencode               # confirm model with: opencode models"