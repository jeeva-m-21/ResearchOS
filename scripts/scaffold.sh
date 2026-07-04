#!/bin/bash

# ResearchOS Project Scaffolding Script
# Creates complete folder structure based on architecture docs

set -e

echo "🏗️  Creating ResearchOS project structure..."

# ============================================
# BACKEND
# ============================================
echo "Creating backend structure..."

mkdir -p backend/src/domain/{experiments,notebooks,papers,artifacts,graph,ai,shared}
mkdir -p backend/src/application/{experiments,notebooks,papers,artifacts,search,ai,auth}
mkdir -p backend/src/infrastructure/{persistence/{postgres,redis},adapters/{llm,embeddings,storage},events,workers}
mkdir -p backend/src/api/{routes,dependencies,middleware}
mkdir -p backend/tests/{unit,integration,e2e}
mkdir -p backend/alembic/versions
mkdir -p backend/config
mkdir -p backend/scripts

# Backend domain files
cat > backend/src/domain/__init__.py << 'EOF'
"""ResearchOS Domain Layer"""
EOF

cat > backend/src/domain/experiments/__init__.py << 'EOF'
"""Experiments bounded context"""
from .entities import Experiment, Run, Metric
from .events import ExperimentStarted, MetricLogged, RunCompleted
from .repositories import IExperimentRepository, IRunRepository

__all__ = [
    "Experiment", "Run", "Metric",
    "ExperimentStarted", "MetricLogged", "RunCompleted",
    "IExperimentRepository", "IRunRepository"
]
EOF

cat > backend/src/domain/experiments/entities.py << 'EOF'
"""Experiment domain entities"""
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class ExperimentStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Experiment(BaseModel):
    """Experiment aggregate root"""
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    project_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    hypothesis_id: Optional[UUID] = None
    status: ExperimentStatus = ExperimentStatus.CREATED
    parameters: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: UUID

class Run(BaseModel):
    """Run entity"""
    id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    run_number: int = Field(ge=1)
    status: ExperimentStatus = ExperimentStatus.CREATED
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    git_commit: Optional[str] = None
    parameters: dict = Field(default_factory=dict)
    metrics: list["Metric"] = Field(default_factory=list)

class Metric(BaseModel):
    """Metric value object"""
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    key: str = Field(min_length=1, max_length=255)
    value: float
    step: int = Field(ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
EOF

cat > backend/src/domain/experiments/events.py << 'EOF'
"""Experiment domain events"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class ExperimentStarted(BaseModel):
    """Event: Experiment started"""
    event_type: str = "experiment.started"
    event_id: UUID = Field(default_factory=lambda: __import__('uuid').uuid4())
    aggregate_id: UUID
    aggregate_type: str = "Experiment"
    version: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    experiment_id: UUID
    organization_id: UUID
    project_id: UUID
    started_by: UUID

class MetricLogged(BaseModel):
    """Event: Metric logged"""
    event_type: str = "metric.logged"
    event_id: UUID = Field(default_factory=lambda: __import__('uuid').uuid4())
    aggregate_id: UUID
    aggregate_type: str = "Run"
    version: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    run_id: UUID
    experiment_id: UUID
    metric_key: str
    metric_value: float
    step: int

class RunCompleted(BaseModel):
    """Event: Run completed"""
    event_type: str = "run.completed"
    event_id: UUID = Field(default_factory=lambda: __import__('uuid').uuid4())
    aggregate_id: UUID
    aggregate_type: str = "Run"
    version: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    run_id: UUID
    experiment_id: UUID
    status: str
    duration_ms: Optional[int] = None
EOF

cat > backend/src/domain/experiments/repositories.py << 'EOF'
"""Experiment repository interfaces"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from .entities import Experiment, Run, Metric

class IExperimentRepository(ABC):
    """Experiment repository interface"""
    
    @abstractmethod
    async def get_by_id(self, experiment_id: UUID) -> Optional[Experiment]:
        pass
    
    @abstractmethod
    async def get_by_project(self, project_id: UUID, limit: int = 100, offset: int = 0) -> List[Experiment]:
        pass
    
    @abstractmethod
    async def save(self, experiment: Experiment) -> None:
        pass
    
    @abstractmethod
    async def delete(self, experiment_id: UUID) -> None:
        pass

class IRunRepository(ABC):
    """Run repository interface"""
    
    @abstractmethod
    async def get_by_id(self, run_id: UUID) -> Optional[Run]:
        pass
    
    @abstractmethod
    async def get_by_experiment(self, experiment_id: UUID) -> List[Run]:
        pass
    
    @abstractmethod
    async def save(self, run: Run) -> None:
        pass

class IMetricRepository(ABC):
    """Metric repository interface"""
    
    @abstractmethod
    async def log(self, metric: Metric) -> None:
        pass
    
    @abstractmethod
    async def get_by_run(self, run_id: UUID, keys: Optional[List[str]] = None) -> List[Metric]:
        pass
EOF

# Shared domain
cat > backend/src/domain/shared/__init__.py << 'EOF'
"""Shared kernel"""
from .value_objects import OrganizationId, UserId, ProjectId, Timestamps
from .events import DomainEvent

__all__ = ["OrganizationId", "UserId", "ProjectId", "Timestamps", "DomainEvent"]
EOF

cat > backend/src/domain/shared/value_objects.py << 'EOF'
"""Shared value objects"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class OrganizationId(BaseModel):
    value: UUID

class UserId(BaseModel):
    value: UUID

class ProjectId(BaseModel):
    value: UUID

class Timestamps(BaseModel):
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
EOF

cat > backend/src/domain/shared/events.py << 'EOF'
"""Base domain event"""
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

class DomainEvent(BaseModel):
    """Base event model"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    aggregate_id: UUID
    aggregate_type: str
    version: int = Field(ge=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
EOF

# API layer
cat > backend/src/api/__init__.py << 'EOF'
"""ResearchOS API Layer"""
EOF

cat > backend/src/api/main.py << 'EOF'
"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .routes import experiments, search, health

app = FastAPI(
    title="ResearchOS API",
    description="Research Operating System API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(experiments.router, prefix="/v1/experiments", tags=["Experiments"])
app.include_router(search.router, prefix="/v1/search", tags=["Search"])

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
EOF

cat > backend/src/api/routes/__init__.py << 'EOF'
"""API Routes"""
EOF

cat > backend/src/api/routes/health.py << 'EOF'
"""Health check endpoints"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health():
    """Health check"""
    return {"status": "healthy"}

@router.get("/ready")
async def readiness():
    """Readiness check"""
    # TODO: Check database and Redis
    return {"status": "ready"}
EOF

cat > backend/src/api/routes/experiments.py << 'EOF'
"""Experiment endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import List, Optional

router = APIRouter()

@router.post("/")
async def create_experiment(
    name: str,
    project_id: UUID,
    description: Optional[str] = None,
):
    """Create a new experiment"""
    # TODO: Implement
    return {"id": "TODO", "name": name, "project_id": str(project_id)}

@router.get("/{experiment_id}")
async def get_experiment(experiment_id: UUID):
    """Get experiment by ID"""
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Not implemented")

@router.get("/{experiment_id}/runs")
async def list_runs(experiment_id: UUID):
    """List runs for experiment"""
    # TODO: Implement
    return []

@router.post("/{experiment_id}/runs")
async def start_run(experiment_id: UUID):
    """Start a new run"""
    # TODO: Implement
    return {"run_id": "TODO"}
EOF

cat > backend/src/api/routes/search.py << 'EOF'
"""Search endpoints"""
from fastapi import APIRouter, Query
from typing import Optional, List

router = APIRouter()

@router.get("/")
async def search(
    q: str = Query(min_length=1, max_length=500),
    types: Optional[List[str]] = Query(None),
    limit: int = Query(default=10, ge=1, le=100),
):
    """Hybrid search across research objects"""
    # TODO: Implement
    return {
        "results": [],
        "total": 0,
        "query": q
    }
EOF

# Infrastructure
cat > backend/src/infrastructure/__init__.py << 'EOF'
"""ResearchOS Infrastructure Layer"""
EOF

cat > backend/src/infrastructure/database.py << 'EOF'
"""Database connection pool"""
import asyncpg
from typing import Optional
import os

class Database:
    """PostgreSQL connection pool"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self, database_url: str):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            dsn=database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def fetch_one(self, query: str, *args):
        """Fetch single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetch_all(self, query: str, *args):
        """Fetch all rows"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute(self, query: str, *args):
        """Execute query"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

db = Database()
EOF

cat > backend/src/infrastructure/events/__init__.py << 'EOF'
"""Event infrastructure"""
EOF

cat > backend/src/infrastructure/events/producer.py << 'EOF'
"""Event producer using Redis Streams"""
import redis.asyncio as redis
import json
from uuid import UUID

class EventProducer:
    """Redis Streams event producer"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def emit(self, event) -> str:
        """Emit event to stream"""
        stream_key = f"events:org_{event.organization_id if hasattr(event, 'organization_id') else 'default'}"
        
        message = {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "aggregate_id": str(event.aggregate_id),
            "aggregate_type": event.aggregate_type,
            "version": event.version,
            "timestamp": event.timestamp.isoformat(),
            "payload": event.model_dump_json()
        }
        
        stream_id = await self.redis.xadd(
            stream_key,
            message,
            maxlen=100000
        )
        
        return stream_id.decode()
EOF

# Config
cat > backend/config/settings.py << 'EOF'
"""Application settings"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application configuration"""
    
    # App
    APP_NAME: str = "ResearchOS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    
    # Redis
    REDIS_URL: str
    
    # Storage
    STORAGE_BACKEND: str = "s3"
    S3_BUCKET: Optional[str] = None
    S3_REGION: str = "us-east-1"
    
    # LLM
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
EOF

cat > backend/pyproject.toml << 'EOF'
[project]
name = "researchos-backend"
version = "1.0.0"
description = "ResearchOS Backend API"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.0",
    "python-multipart>=0.0.6",
    "prometheus-client>=0.19.0",
    "opentelemetry-api>=1.22.0",
    "opentelemetry-instrumentation-fastapi>=0.43b0",
    "alembic>=1.13.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "black>=24.1.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.11"
strict = true
EOF

cat > backend/alembic.ini << 'EOF'
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = %(DATABASE_URL)s

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

cat > backend/alembic/env.py << 'EOF'
"""Alembic environment configuration"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

config = context.config

if config.get_main_option("sqlalchemy.url") is None:
    config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", ""))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

# ============================================
# FRONTEND
# ============================================
echo "Creating frontend structure..."

mkdir -p frontend/app/{api,experiments,notebooks,search,papers}
mkdir -p frontend/components/{ui,experiments,notebooks,papers,graph}
mkdir -p frontend/lib/{api,hooks,utils}
mkdir -p frontend/styles

cat > frontend/package.json << 'EOF'
{
  "name": "researchos-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.0",
    "zustand": "^4.4.0",
    "date-fns": "^3.2.0",
    "recharts": "^2.10.0",
    "@uiw/react-codemirror": "^4.21.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.56.0",
    "eslint-config-next": "^15.0.0"
  }
}
EOF

cat > frontend/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
EOF

cat > frontend/next.config.js << 'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig
EOF

cat > frontend/tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF

cat > frontend/app/layout.tsx << 'EOF'
import './globals.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
EOF

cat > frontend/app/page.tsx << 'EOF'
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold">ResearchOS</h1>
      <p className="mt-4 text-lg text-gray-600">
        Research Operating System
      </p>
    </main>
  )
}
EOF

cat > frontend/app/globals.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-start-rgb: 214, 219, 220;
  --background-end-rgb: 255, 255, 255;
}

body {
  color: rgb(var(--foreground-rgb));
  background: linear-gradient(
      to bottom,
      transparent,
      rgb(var(--background-end-rgb))
    )
    rgb(var(--background-start-rgb));
}
EOF

cat > frontend/lib/api/client.ts << 'EOF'
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

export default api
EOF

# ============================================
# PYTHON SDK
# ============================================
echo "Creating Python SDK structure..."

mkdir -p sdk/python/researchos
mkdir -p sdk/python/tests

cat > sdk/python/researchos/__init__.py << 'EOF'
"""ResearchOS Python SDK"""
from .client import ResearchOSClient
from .experiment import Experiment

_client: ResearchOSClient = None

def init(experiment: str, project: str = None, api_key: str = None, **kwargs) -> None:
    """Initialize ResearchOS"""
    global _client
    _client = ResearchOSClient(api_key=api_key, **kwargs)
    _client.init_experiment(experiment, project=project)

def log_metric(key: str, value: float, step: int = None, **metadata) -> None:
    """Log a metric"""
    if _client is None:
        raise RuntimeError("Call researchos.init() first")
    _client.log_metric(key, value, step=step, **metadata)

def log_parameters(params: dict) -> None:
    """Log parameters"""
    for key, value in params.items():
        _client.log_parameter(key, value)

def finish(status: str = "completed") -> None:
    """Finish the run"""
    if _client:
        _client.finish(status=status)

__all__ = ["init", "log_metric", "log_parameters", "finish", "Experiment"]
EOF

cat > sdk/python/researchos/client.py << 'EOF'
"""ResearchOS client"""
import os
from uuid import UUID, uuid4
from typing import Optional
import time

class ResearchOSClient:
    """Main SDK client"""
    
    def __init__(
        self,
        api_url: str = None,
        api_key: str = None,
        organization_id: UUID = None,
        offline: bool = False,
    ):
        self.api_url = api_url or os.getenv("RESEARCHOS_API_URL", "https://api.researchos.ai")
        self.api_key = api_key or os.getenv("RESEARCHOS_API_KEY")
        self.organization_id = organization_id
        self.offline = offline
        
        self.experiment_id: Optional[UUID] = None
        self.run_id: Optional[UUID] = None
        self.step_counters: dict[str, int] = {}
    
    def init_experiment(self, name: str, project: str = None, **kwargs) -> UUID:
        """Initialize experiment"""
        self.experiment_id = uuid4()
        # TODO: Implement actual initialization
        return self.experiment_id
    
    def start_run(self, parameters: dict = None) -> UUID:
        """Start a new run"""
        self.run_id = uuid4()
        # TODO: Implement
        return self.run_id
    
    def log_metric(self, key: str, value: float, step: int = None, **metadata) -> None:
        """Log a metric"""
        if not self.run_id:
            raise RuntimeError("No active run")
        
        if step is None:
            self.step_counters[key] = self.step_counters.get(key, 0) + 1
            step = self.step_counters[key]
        
        # TODO: Implement WAL persistence
        pass
    
    def log_parameter(self, key: str, value) -> None:
        """Log a parameter"""
        # TODO: Implement
        pass
    
    def finish(self, status: str = "completed") -> None:
        """Finish the run"""
        # TODO: Implement
        self.run_id = None
EOF

cat > sdk/python/researchos/experiment.py << 'EOF'
"""Experiment context"""
from uuid import UUID
from typing import Optional

class Experiment:
    """Experiment context manager"""
    
    def __init__(self, name: str, project: str = None):
        self.name = name
        self.project = project
        self._started = False
    
    def __enter__(self):
        # TODO: Initialize experiment
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: Finish experiment
        pass
EOF

cat > sdk/python/pyproject.toml << 'EOF'
[project]
name = "researchos"
version = "1.0.0"
description = "ResearchOS Python SDK"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.26.0",
    "pydantic>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "black>=24.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 88
EOF

# ============================================
# INFRASTRUCTURE
# ============================================
echo "Creating infrastructure structure..."

mkdir -p infra/terraform
mkdir -p helm/researchos/templates
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/{dashboards,datasources}

cat > helm/researchos/Chart.yaml << 'EOF'
apiVersion: v2
name: researchos
description: ResearchOS Helm Chart
type: application
version: 1.0.0
appVersion: "1.0.0"
EOF

cat > helm/researchos/values.yaml << 'EOF'
# Default values for researchos
namespace:
  create: true
  name: researchos

backend:
  replicaCount: 3
  image:
    repository: researchos/backend
    tag: "1.0.0"
  service:
    type: ClusterIP
    port: 8000
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2
      memory: 4Gi

frontend:
  replicaCount: 2
  image:
    repository: researchos/frontend
    tag: "1.0.0"
  service:
    type: ClusterIP
    port: 3000

postgresql:
  enabled: true
  auth:
    database: researchos

redis:
  enabled: true
  auth:
    enabled: true

ingress:
  enabled: true
  className: nginx
EOF

# ============================================
# ROOT FILES
# ============================================
echo "Creating root files..."

cat > docker-compose.yml << 'EOF'
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: researchos
      POSTGRES_PASSWORD: researchos
      POSTGRES_DB: researchos
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  postgres-data:
  redis-data:
EOF

cat > Makefile << 'EOF'
.PHONY: help install dev test docker-build docker-up clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make dev          - Start development server"
	@echo "  make test         - Run all tests"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start Docker Compose"
	@echo "  make clean        - Clean build artifacts"

install:
	cd backend && pip install -e ".[dev]"
	cd sdk/python && pip install -e ".[dev]"
	cd frontend && npm install

dev:
	docker-compose up -d postgres redis
	cd backend && uvicorn src.api.main:app --reload --port 8000 &

test:
	cd backend && pytest tests/
	cd frontend && npm test

docker-build:
	docker build -t researchos-backend:latest ./backend
	docker build -t researchos-frontend:latest ./frontend

docker-up:
	docker-compose up -d

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf .ruff_cache .mypy_cache
EOF

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv/

# Node
node_modules/
.npm
.pnpm-store/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Type checking
.mypy_cache/
.ruff_cache/

# Build
.next/
out/

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment
.env
.env.local
.env.*.local

# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfvars

# OS
.DS_Store
Thumbs.db

# Misc
*.bak
*.tmp
.cache/
EOF

cat > README.md << 'EOF'
# ResearchOS

Research Operating System - A unified platform for managing AI/ML research workflows.

## Quick Start

```bash
# Install dependencies
make install

# Start development environment
make dev

# Run tests
make test
```

## Architecture

- **Backend**: FastAPI with hexagonal architecture
- **Frontend**: Next.js 15 with App Router
- **Database**: PostgreSQL + pgvector
- **Cache/Queue**: Redis
- **Events**: Redis Streams

## Documentation

See `docs/` for detailed architecture documentation.

## License

MIT
EOF

echo "✅ ResearchOS project structure created successfully!"
echo ""
echo "Next steps:"
echo "  1. cd backend && pip install -e '.[dev]'"
echo "  2. cd frontend && npm install"
echo "  3. docker-compose up -d"
echo "  4. make dev"
