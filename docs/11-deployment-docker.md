# ResearchOS - Docker Deployment

## Overview

Single-container development deployment for local testing and quick prototyping.

---

## Dockerfile (All-in-One)

```dockerfile
# backend/Dockerfile

# ============================================
# Stage 1: Build Frontend
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ .
RUN npm run build

# ============================================
# Stage 2: Build Backend
# ============================================
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/pyproject.toml backend/poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction

# Copy backend code
COPY backend/src ./src
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./

# ============================================
# Stage 3: Production Image
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=backend-builder /app .

# Copy frontend build
COPY --from=frontend-builder /app/frontend/out /app/frontend

# Create non-root user
RUN useradd -m -u 1000 researchos && \
    chown -R researchos:researchos /app

USER researchos

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Environment Variables

```bash
# .env.example

# Application
RESEARCHOS_ENV=production
RESEARCHOS_SECRET_KEY=your-secret-key-change-this
RESEARCHOS_API_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://researchos:password@localhost:5432/researchos
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0

# Object Storage (local mode)
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=/data/artifacts

# LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Embeddings
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Monitoring
PROMETHEUS_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

## Run Commands

### Build Image

```bash
docker build -t researchos:latest -f backend/Dockerfile .
```

### Run Container

```bash
docker run -d \
  --name researchos \
  -p 8000:8000 \
  -v researchos-data:/data \
  -e DATABASE_URL=postgresql://researchos:password@postgres:5432/researchos \
  -e REDIS_URL=redis://redis:6379/0 \
  -e RESEARCHOS_SECRET_KEY=$(openssl rand -hex 32) \
  researchos:latest
```

### Quick Start (with embedded databases)

```bash
# Development mode with SQLite and in-memory Redis
docker run -d \
  --name researchos-dev \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///data/researchos.db \
  -e REDIS_URL=redis://localhost:6379/0 \
  -e RESEARCHOS_ENV=development \
  researchos:latest
```

---

## Health Endpoints

```python
# src/api/routes/health.py

from fastapi import APIRouter, Response
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/ready")
async def readiness_check():
    # Check database
    try:
        await db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = "unhealthy"
    
    # Check Redis
    try:
        await redis.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = "unhealthy"
    
    all_healthy = db_status == "healthy" and redis_status == "healthy"
    
    status_code = 200 if all_healthy else 503
    
    return Response(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "database": db_status,
            "redis": redis_status
        }
    )

@router.get("/metrics")
async def prometheus_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

---

## Next Steps

- Docker Compose deployment → [12-deployment-docker-compose.md](./12-deployment-docker-compose.md)
