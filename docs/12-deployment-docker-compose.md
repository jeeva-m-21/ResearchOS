# ResearchOS - Docker Compose Deployment

## Overview

Self-hosted deployment using Docker Compose for small teams and proof-of-concept deployments.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DOCKER COMPOSE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│           ┌─────────────────────────────────────────────┐               │
│           │              Traefik (Reverse Proxy)         │               │
│           │  - SSL Termination (Let's Encrypt)          │               │
│           │  - Load Balancing                            │               │
│           └─────────────────────────────────────────────┘               │
│                             │                                            │
│            ┌────────────────┼────────────────┐                          │
│            ▼                ▼                ▼                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │   Frontend   │  │   Backend    │  │   Workers     │                │
│  │   (Next.js)  │  │   (FastAPI)  │  │   (Async)     │                │
│  │              │  │              │  │               │                │
│  │  Port: 3000  │  │  Port: 8000  │  │  (no port)    │                │
│  └──────────────┘  └──────────────┘  └──────────────┘                │
│            │                │                │                          │
│            └────────────────┼────────────────┘                          │
│                             │                                            │
│            ┌────────────────┼────────────────┐                          │
│            ▼                ▼                ▼                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │  PostgreSQL  │  │    Redis     │  │    MinIO     │                │
│  │              │  │              │  │   (S3-like)  │                │
│  │  Port: 5432  │  │  Port: 6379  │  │  Port: 9000  │                │
│  └──────────────┘  └──────────────┘  └──────────────┘                │
│                                                                             │
│  Monitoring:                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │  Prometheus  │  │   Grafana    │  │   Jaeger     │                │
│  │  Port: 9090  │  │  Port: 3001  │  │  Port: 16686 │                │
│  └──────────────┘  └──────────────┘  └──────────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## docker-compose.yml

```yaml
# docker-compose.yml

version: "3.9"

services:
  # ============================================
  # Reverse Proxy
  # ============================================
  traefik:
    image: traefik:v3.0
    command:
      - "--api.dashboard=true"
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
      - "8081:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik-letsencrypt:/letsencrypt
    networks:
      - frontend
      - backend
    restart: unless-stopped

  # ============================================
  # Frontend
  # ============================================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`${DOMAIN}`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
      - "traefik.http.services.frontend.loadbalancer.server.port=3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.${DOMAIN}
    networks:
      - frontend
    restart: unless-stopped

  # ============================================
  # Backend
  # ============================================
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`api.${DOMAIN}`)"
      - "traefik.http.routers.backend.entrypoints=websecure"
      - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
      - "traefik.http.services.backend.loadbalancer.server.port=8000"
    environment:
      - DATABASE_URL=postgresql://researchos:${POSTGRES_PASSWORD}@postgres:5432/researchos
      - REDIS_URL=redis://redis:6379/0
      - RESEARCHOS_SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - STORAGE_BACKEND=s3
      - S3_ENDPOINT=http://minio:9000
      - S3_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - S3_SECRET_KEY=${MINIO_SECRET_KEY}
      - S3_BUCKET=researchos
      - PROMETHEUS_ENABLED=true
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_started
    volumes:
      - backend-data:/data
    networks:
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 4G
        reservations:
          cpus: "0.5"
          memory: 1G

  # ============================================
  # Workers (Event Processing)
  # ============================================
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    command: ["python", "-m", "src.workers.embedding_worker"]
    environment:
      - DATABASE_URL=postgresql://researchos:${POSTGRES_PASSWORD}@postgres:5432/researchos
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    networks:
      - backend
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1"
          memory: 2G

  # ============================================
  # PostgreSQL
  # ============================================
  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=researchos
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=researchos
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U researchos"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 4G

  # ============================================
  # Redis
  # ============================================
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend
    restart: unless-stopped

  # ============================================
  # MinIO (S3-compatible Object Storage)
  # ============================================
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_ACCESS_KEY}
      - MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY}
    volumes:
      - minio-data:/data
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.minio.rule=Host(`storage.${DOMAIN}`)"
      - "traefik.http.routers.minio.entrypoints=websecure"
      - "traefik.http.routers.minio.tls.certresolver=letsencrypt"
      - "traefik.http.services.minio.loadbalancer.server.port=9000"
    networks:
      - backend
    restart: unless-stopped

  # ============================================
  # Monitoring: Prometheus
  # ============================================
  prometheus:
    image: prom/prometheus:v2.48.0
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--storage.tsdb.retention.time=30d"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prometheus.rule=Host(`prometheus.${DOMAIN}`)"
      - "traefik.http.routers.prometheus.entrypoints=websecure"
      - "traefik.http.routers.prometheus.tls.certresolver=letsencrypt"
      - "traefik.http.services.prometheus.loadbalancer.server.port=9090"
    networks:
      - backend
      - monitoring
    restart: unless-stopped

  # ============================================
  # Monitoring: Grafana
  # ============================================
  grafana:
    image: grafana/grafana:10.2.0
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.${DOMAIN}`)"
      - "traefik.http.routers.grafana.entrypoints=websecure"
      - "traefik.http.routers.grafana.tls.certresolver=letsencrypt"
      - "traefik.http.services.grafana.loadbalancer.server.port=3000"
    networks:
      - monitoring
    restart: unless-stopped

  # ============================================
  # Monitoring: Jaeger (Tracing)
  # ============================================
  jaeger:
    image: jaegertracing/all-in-one:1.52
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.jaeger.rule=Host(`jaeger.${DOMAIN}`)"
      - "traefik.http.routers.jaeger.entrypoints=websecure"
      - "traefik.http.routers.jaeger.tls.certresolver=letsencrypt"
      - "traefik.http.services.jaeger.loadbalancer.server.port=16686"
    networks:
      - backend
      - monitoring
    restart: unless-stopped

  # ============================================
  # Backup
  # ============================================
  backup:
    image: prodrigestivill/postgres-backup-local:16-alpine
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=researchos
      - POSTGRES_USER=researchos
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - SCHEDULE=@daily
      - BACKUP_KEEP_DAYS=7
      - BACKUP_KEEP_WEEKS=4
      - BACKUP_KEEP_MONTHS=12
    volumes:
      - ./backups:/backups
    depends_on:
      - postgres
    networks:
      - backend
    restart: unless-stopped

networks:
  frontend:
  backend:
  monitoring:

volumes:
  postgres-data:
  redis-data:
  minio-data:
  backend-data:
  traefik-letsencrypt:
  prometheus-data:
  grafana-data:
```

---

## Environment File

```bash
# .env

# Domain
DOMAIN=researchos.local
ACME_EMAIL=admin@researchos.local

# Database
POSTGRES_PASSWORD=your-secure-postgres-password

# Application
SECRET_KEY=your-secret-key-at-least-32-characters

# Object Storage
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin-secret-key

# LLM
OPENAI_API_KEY=sk-...

# Monitoring
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your-grafana-password
```

---

## Prometheus Configuration

```yaml
# monitoring/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093

rule_files:
  - /etc/prometheus/rules/*.yml

scrape_configs:
  - job_name: prometheus
    static_configs:
    - targets: ['localhost:9090']

  - job_name: backend
    static_configs:
    - targets: ['backend:8000']
    metrics_path: /metrics

  - job_name: postgres
    static_configs:
    - targets: ['postgres-exporter:9187']

  - job_name: redis
    static_configs:
    - targets: ['redis-exporter:9121']

  - job_name: node
    static_configs:
    - targets: ['node-exporter:9100']
```

---

## Grafana Datasources

```yaml
# monitoring/grafana/datasources/prometheus.yml

apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
```

---

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/researchos/researchos.git
cd researchos

# 2. Create environment file
cp .env.example .env
nano .env  # Edit with your values

# 3. Create secrets
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "POSTGRES_PASSWORD=$(openssl rand -hex 16)" >> .env

# 4. Start services
docker compose up -d

# 5. Run migrations
docker compose exec backend alembic upgrade head

# 6. Check logs
docker compose logs -f

# 7. View services
open https://researchos.local        # Frontend
open https://api.researchos.local    # API
open https://grafana.researchos.local # Monitoring
```

---

## Maintenance

### Backup

```bash
# Manual backup
docker compose exec backup backup

# View backups
ls -la backups/
```

### Restore

```bash
# Restore database
docker compose exec postgres psql -U researchos -d researchos < backups/latest.sql.gz
```

### Update

```bash
# Pull latest images
docker compose pull

# Rebuild containers
docker compose up -d --build

# Run migrations
docker compose exec backend alembic upgrade head
```

### Logs

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f backend

# View last 100 lines
docker compose logs --tail=100 backend
```

---

## Next Steps

- Kubernetes deployment → [13-deployment-kubernetes.md](./13-deployment-kubernetes.md)
- Monitoring setup → [15-monitoring.md](./15-monitoring.md)
