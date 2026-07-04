# ResearchOS - Production Deployment Architecture

## Overview

This document defines production deployment strategies for ResearchOS across multiple platforms, from single-container development to enterprise Kubernetes deployments.

---

## Deployment Tiers

| Tier | Platform | Use Case | SLA |
|------|----------|----------|-----|
| **Development** | Single Docker | Local development, testing | N/A |
| **Self-Hosted** | Docker Compose | Small teams, POC | 99% |
| **Production** | Kubernetes (self-managed) | Medium organizations | 99.9% |
| **Enterprise SaaS** | AWS/Azure/GCP | Large organizations | 99.99% |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        LOAD BALANCER / CDN                           │    │
│  │  - TLS Termination                                                   │    │
│  │  - SSL Certificates (Let's Encrypt / ACM)                           │    │
│  │  - DDoS Protection                                                   │    │
│  │  - Static Assets (CDN)                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                          │
│                                    ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        API GATEWAY                                   │    │
│  │  - Rate Limiting                                                    │    │
│  │  - Authentication (JWT)                                             │    │
│  │  - Request Routing                                                   │    │
│  │  - Circuit Breaking                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                          │
│         ┌──────────────────────────┼──────────────────────────┐            │
│         │                          │                          │            │
│         ▼                          ▼                          ▼            │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐        │
│  │   Backend   │          │  Frontend   │          │   Workers   │        │
│  │   (FastAPI) │          │  (Next.js)  │          │   (Async)   │        │
│  │             │          │             │          │             │        │
│  │ HPA: 3-20   │          │ HPA: 2-10   │          │ HPA: 2-20   │        │
│  └─────────────┘          └─────────────┘          └─────────────┘        │
│         │                       │                        │                │
│         └───────────────────────┼────────────────────────┘                │
│                                 │                                          │
│                                 ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        STATEFUL LAYER                                │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │  PostgreSQL  │  │    Redis     │  │Object Storage│              │    │
│  │  │   Primary    │  │   Cluster    │  │   (S3/GCS)   │              │    │
│  │  │  + Replicas  │  │              │  │              │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  │  ┌──────────────┐                                                  │    │
│  │  │ Elasticsearch│  (Optional for large-scale search)              │    │
│  │  └──────────────┘                                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        MONITORING & OBSERVABILITY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Prometheus  │  │   Grafana    │  │   Jaeger     │  │   Loki       │   │
│  │   (Metrics)  │  │ (Dashboards) │  │  (Tracing)   │  │   (Logs)     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ AlertManager │  │  PagerDuty   │  │    Slack     │                  │
│  │  (Alerting)  │  │ (Escalation) │  │  (ChatOps)   │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        BACKUP & DISASTER RECOVERY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  PostgreSQL  │  │   WAL        │  │   Object     │  │  Cross-Region│   │
│  │   Backups    │  │  Archiving   │  │  Replication │  │   Failover   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐                                  │
│  │  PITR        │  │  Standby      │                                  │
│  │ (Time Travel)│  │  Region       │                                  │
│  └──────────────┘  └──────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Resource Sizing

### Development (Single Docker)

| Component | Resources | Storage |
|-----------|-----------|----------|
| All-in-One | 2 CPU, 4GB RAM | 20GB |

### Self-Hosted (Docker Compose)

| Component | Resources | Storage | Replicas |
|-----------|-----------|----------|----------|
| Backend | 1 CPU, 2GB RAM | - | 1 |
| Frontend | 0.5 CPU, 512MB RAM | - | 1 |
| PostgreSQL | 2 CPU, 4GB RAM | 100GB SSD | 1 |
| Redis | 1 CPU, 2GB RAM | 10GB | 1 |
| MinIO | 1 CPU, 2GB RAM | 500GB | 1 |

### Production (Kubernetes)

| Component | Resources (Request) | Resources (Limit) | Replicas | HPA |
|-----------|---------------------|--------------------|---------|-----|
| Backend | 500m CPU, 1GB RAM | 2 CPU, 4GB RAM | 3 | 3-20 |
| Frontend | 250m CPU, 256MB RAM | 1 CPU, 512MB RAM | 2 | 2-10 |
| Workers | 500m CPU, 1GB RAM | 2 CPU, 4GB RAM | 2 | 2-20 |
| PostgreSQL | 4 CPU, 16GB RAM | 8 CPU, 32GB RAM | 1 primary + 2 replicas | - |
| Redis | 2 CPU, 8GB RAM | 4 CPU, 16GB RAM | 3 (cluster) | - |
|Embedding Worker| 2 CPU, 4GB RAM | 4 CPU, 8GB RAM | 2 | 2-10 |

### Enterprise SaaS

| Component | Resources | Replicas | Multi-AZ | Multi-Region |
|-----------|-----------|----------|-----------|--------------|
| Backend (per region) | 8 CPU, 32GB RAM | 10 | Yes | Active-Active |
| PostgreSQL | 16 CPU, 64GB RAM | 3 | Yes | Async Replication |
| Redis | 8 CPU, 32GB RAM | 6 | Yes | Cross-Region |
| Object Storage | S3/GCS/R2 | - | Yes | Cross-Region |

---

## Storage Architecture

### PostgreSQL Storage

```
┌─────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL STORAGE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Primary Volume (SSD/NVMe)                                       │
│  ├── /var/lib/postgresql/data                                    │
│  │   ├── base/          # Database files                        │
│  │   ├── pg_wal/        # Write-ahead logs                      │
│  │   └── pg_stat/       # Statistics                            │
│  │                                                                │
│  ├── Estimated Size Calculation:                                 │
│  │   ├── Base tables: ~10GB per 1000 experiments               │
│  │   ├── Metrics: ~1GB per 1M rows                              │
│  │   ├── Nodes: ~100MB per 10K nodes                            │
│  │   └── Events: ~5GB per 1M events                              │
│  │                                                                │
│  └── Growth Rate: ~100GB/year per 10K users                     │
│                                                                   │
│  WAL Archival (S3/GCS)                                           │
│  ├── Continuous WAL archiving                                    │
│  └── 7-day retention (configurable)                             │
│                                                                   │
│  Backup Storage (S3/GCS)                                         │
│  ├── Daily full backups                                          │
│  ├── Hourly incremental backups                                  │
│  └── 30-day retention                                            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Object Storage

```
┌─────────────────────────────────────────────────────────────────┐
│                    OBJECT STORAGE                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Bucket Structure:                                                │
│  researchos-{org_id}-{region}                                    │
│  ├── artifacts/                                                  │
│  │   ├── {artifact_id}/                                          │
│  │   │   ├── v1/file.bin                                         │
│  │   │   ├── v2/file.bin                                         │
│  │   │   └── metadata.json                                       │
│  │   └── tmp/              # Upload staging                      │
│  ├── notebooks/                                                  │
│  │   └── {notebook_id}/                                          │
│  │       └── exports/                                             │
│  ├── backups/                                                    │
│  │   ├── postgres/                                               │
│  │   └── redis/                                                  │
│  └── exports/                                                    │
│      └── paper_{id}.pdf                                          │
│                                                                   │
│  lifecycle Rules:                                                 │
│  ├── Transition to IA (Infrequent Access) after 90 days         │
│  ├── Transition to Glacier after 365 days                        │
│  └── Delete after 2555 days (7 years)                           │
│                                                                   │
│  Versioning: Enabled                                              │
│  Encryption: SSE-S3 or SSE-KMS                                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Autoscaling Strategy

### Horizontal Pod Autoscaler (HPA)

```yaml
# Backend HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60
      selectPolicy: Min
```

### Vertical Pod Autoscaler (VPA)

```yaml
# Backend VPA
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: backend-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: backend
      minAllowed:
        cpu: 250m
        memory: 512Mi
      maxAllowed:
        cpu: 4
        memory: 8Gi
      controlledResources: ["cpu", "memory"]
      controlledValues: RequestsAndLimits
```

### Kafka-like Consumer Scaling (Redis Streams)

```python
# Autoscaling workers based on stream length
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: embedding-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: External
    external:
      metric:
        name: redis_stream_length
        selector:
          matchLabels:
            stream: events
      target:
        type: AverageValue
        averageValue: "100"
```

---

## Monitoring Stack

### Prometheus Metrics

```yaml
# ServiceMonitor for backend
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-metrics
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: metrics
    path: /metrics
    interval: 15s
    scrapeTimeout: 10s
```

### Key Metrics

```yaml
# Custom metrics exposed by backend
metrics:
  # Request metrics
  - http_requests_total{method, endpoint, status}
  - http_request_duration_seconds{method, endpoint}
  - http_requests_in_flight{method}
  
  # Business metrics
  - experiments_total{organization_id, status}
  - runs_total{experiment_id, status}
  - metrics_logged_total{experiment_id, key}
  - search_queries_total{organization_id}
  - search_latency_seconds{organization_id}
  
  # AI metrics
  - llm_requests_total{provider, model}
  - llm_tokens_total{provider, model, type}
  - llm_latency_seconds{provider, model}
  - embedding_requests_total{provider}
  
  # Event metrics
  - events_emitted_total{event_type, organization_id}
  - events_processed_total{event_type, consumer_group}
  - event_processing_latency_seconds{event_type}
  - dlq_size{consumer_group}
  
  # Database metrics
  - db_connections_active
  - db_query_duration_seconds{query}
  - db_pool_size
  
  # Redis metrics
  - redis_connections_active
  - redis_memory_used_bytes
  - redis_stream_length{stream}
```

### Grafana Dashboards

```
dashboards/
├── researchos-overview.json        # High-level system health
├── researchos-api.json              # API performance
├── researchos-experiments.json      # Experiment metrics
├── researchos-ai.json               # AI/LLM usage
├── researchos-events.json           # Event processing
├── researchos-database.json         # PostgreSQL metrics
├── researchos-redis.json            # Redis metrics
├── researchos-kubernetes.json       # K8s cluster health
└── researchos-cost.json             # Cost analysis
```

### Alerting Rules

```yaml
# PrometheusRule for alerts
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: researchos-alerts
spec:
  groups:
  - name: researchos.rules
    rules:
    # Availability alerts
    - alert: BackendDown
      expr: up{job="backend"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Backend instance down"
        
    - alert: HighErrorRate
      expr: |
        sum(rate(http_requests_total{status=~"5.."}[5m])) 
        / sum(rate(http_requests_total[5m])) > 0.05
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High error rate (>5%)"
        
    # Performance alerts
    - alert: HighLatency
      expr: |
        histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "P99 latency > 1s"
        
    - alert: SlowSearch
      expr: |
        histogram_quantile(0.99, rate(search_latency_seconds_bucket[5m])) > 0.2
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "P99 search latency > 200ms (SLA: <100ms)"
        
    # Database alerts
    - alert: PostgreSQLDown
      expr: pg_up == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "PostgreSQL down"
        
    - alert: PostgreSQLReplicationLag
      expr: pg_replication_lag_seconds > 30
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "PostgreSQL replication lag > 30s"
        
    - alert: PostgreSQLDiskSpace
      expr: |
        pg_database_size_bytes / pg_filesystem_size_bytes > 0.85
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "PostgreSQL disk usage > 85%"
        
    # Redis alerts
    - alert: RedisDown
      expr: redis_up == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Redis down"
        
    - alert: RedisMemoryHigh
      expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Redis memory usage > 90%"
        
    # Event processing alerts
    - alert: ConsumerLagHigh
      expr: redis_stream_length{stream="events"} > 10000
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Event consumer lag > 10000 messages"
        
    - alert: DLQGrowing
      expr: rate(dlq_size[5m]) > 10
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Dead letter queue growing rapidly"
        
    # Cost alerts
    - alert: HighLLMCost
      expr: |
        sum(rate(llm_tokens_total[1h])) * 0.00003 > 100
      for: 1h
      labels:
        severity: warning
      annotations:
        summary: "LLM cost projected > $100/hour"
```

### Grafana Dashboard (Overview)

```
┌────────────────────────────────────────────────────────────────────┐
│                      ResearchOS Overview                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │ Request Rate     │  │ Error Rate       │  │ P99 Latency      │ │
│  │ 1,234 req/s      │  │ 0.03%            │  │ 45ms             │ │
│  │ ▁▂▃▄▅▆▇█▇▆▅▄▃▂  │  │ ▁▁▁▁▁▁▁▁▁▁▁▁     │  │ ▂▃▄▃▂▁          │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Active Experiments                           │ │
│  │  ████████████████████████████████████ Running: 42               │ │
│  │  ████████████████ Completed: 128                               │ │
│  │  ██ Failed: 8                                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────┐  ┌────────────────────────────┐  │
│  │      Database               │  │        Redis               │  │
│  │  Connections: 45/100        │  │ Memory: 4.2GB/8GB         │  │
│  │  Query P99: 12ms           │  │ Ops/s: 15,234              │  │
│  │  Disk: 450GB/1TB           │  │ Stream Pending: 23         │  │
│  └────────────────────────────┘  └────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                  Event Processing                               │ │
│  │  Emitted: 1,234,567 | Processed: 1,234,540 | DLQ: 27         │ │
│  │  ████████████████████████████████████████████████████ 99.9%    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## Distributed Tracing (OpenTelemetry + Jaeger)

```python
# Tracing instrumentation
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Auto-instrument PostgreSQL
AsyncPGInstrumentor().instrument()

# Auto-instrument Redis
RedisInstrumentor().instrument()

# Custom spans
@app.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: UUID):
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("get_experiment") as span:
        span.set_attribute("experiment_id", str(experiment_id))
        
        experiment = await experiment_repo.get(experiment_id)
        span.set_attribute("experiment.name", experiment.name)
        
        return experiment
```

### Trace Sampling

```yaml
# Jaeger sampling strategy
{
  "default_strategy": {
    "type": "probabilistic",
    "param": 0.1
  },
  "sampling_strategies": {
    "GET /api/v1/search": {
      "type": "probabilistic",
      "param": 1.0
    },
    "POST /api/v1/events": {
      "type": "probabilistic",
      "param": 0.01
    }
  }
}
```

---

## Backup Strategy

### PostgreSQL Backups

```yaml
# backup-job.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:16
            command:
            - /bin/bash
            - -c
            - |
              pg_dump -Fc $DATABASE_URL > /backup/researchos_$(date +%Y%m%d_%H%M%S).dump
              aws s3 cp /backup/researchos_$(date +%Y%m%d_%H%M%S).dump s3://researchos-backups/postgres/
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: url
            volumeMounts:
            - name: backup
              mountPath: /backup
          volumes:
          - name: backup
            emptyDir: {}
          restartPolicy: OnFailure
```

### WAL Archiving

```
# postgresql.conf
wal_level = replica
archive_mode = on
archive_timeout = 300  # 5 minutes
archive_command = 'aws s3 cp %p s3://researchos-wal/%f'
```

### Point-in-Time Recovery (PITR)

```bash
# Restore to specific point in time
pgbackrest restore \
  --stanza=researchos \
  --target-time="2024-01-15 10:30:00" \
  --target-action=pause
```

### Backup Retention

```
┌────────────────────────────────────────────────────────────────┐
│                    BACKUP RETENTION                             │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Full Backups:                                                   │
│  ├── Daily: Keep 7 days                                         │
│  ├── Weekly: Keep 4 weeks                                       │
│  ├── Monthly: Keep 12 months                                    │
│  └── Yearly: Keep 7 years                                       │
│                                                                  │
│  WAL Archives:                                                   │
│  └── Keep 30 days for PITR                                      │
│                                                                  │
│  Storage Locations:                                              │
│  ├── Primary: S3 (us-east-1)                                    │
│  ├── Secondary: S3 (eu-west-1) - Cross-region replication      │
│  └── Glacier: After 90 days                                     │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Disaster Recovery

### Recovery Point Objective (RPO) & Recovery Time Objective (RTO)

| Scenario | RPO | RTO | Strategy |
|----------|-----|-----|----------|
| Single AZ failure | 0 | <5 min | Multi-AZ deployment |
| Region failure | <15 min | <30 min | Cross-region failover |
| Data corruption | <1 hour | <2 hours | PITR from backup |
| Ransomware | <24 hours | <4 hours | Immutable backups |

### Disaster Recovery Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DISASTER RECOVERY                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Primary Region (us-east-1)                                             │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │    │
│  │  │  Backend    │    │ PostgreSQL  │    │   Redis     │       │    │
│  │  │   Active    │    │   Primary   │    │   Primary   │       │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘       │    │
│  │                          │                   │                │    │
│  │                          │ Async Replication  │                │    │
│  │                          ▼                   ▼                │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                    │                                      │
│                                    │ Cross-Region Replication              │
│                                    ▼                                      │
│  Standby Region (eu-west-1)                                              │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │    │
│  │  │  Backend    │    │ PostgreSQL  │    │   Redis     │       │    │
│  │  │  Standby    │    │  Replica    │    │   Replica   │       │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘       │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  Failover Process:                                                        │
│  1. DNS update (Route 53) to standby region                             │
│  2. Promote PostgreSQL replica to primary                               │
│  3. Promote Redis replica to primary                                    │
│  4. Scale backend in standby region                                      │
│  5. Notify stakeholders                                                  │
│                                                                           │
│  Recovery Time: <30 minutes                                              │
│  Recovery Point: <15 minutes (async replication lag)                    │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Failover Runbook

```yaml
# failover-runbook.yaml
name: Cross-Region Failover
description: Failover from us-east-1 to eu-west-1
triggers:
  - Region availability < 95%
  - Manual trigger by ops team

steps:
  - name: Verify Standby Health
    action: health-check
    region: eu-west-1
    services:
      - postgresql
      - redis
      - object-storage
      
  - name: Promote PostgreSQL
    action: promote-replica
    region: eu-west-1
    
  - name: Promote Redis
    action: promote-replica
    region: eu-west-1
    
  - name: Update DNS
    action: update-route53
    zone: researchos.ai
    records:
      - api.researchos.ai -> eu-west-1-lb
      - app.researchos.ai -> eu-west-1-cdn
      
  - name: Scale Backend
    action: scale-deployment
    region: eu-west-1
    deployment: backend
    replicas: 10
    
  - name: Verify Traffic
    action: verify-traffic
    endpoint: https://api.researchos.ai/health
    expected_status: 200
    
  - name: Notify Stakeholders
    action: notify
    channels:
      - pagerduty
      - slack
    message: "Failover to eu-west-1 complete"
```

---

## Performance Optimization

### Connection Pooling Strategy

```python
# src/infrastructure/database/pool.py

import asyncpg
from contextlib import asynccontextmanager

class DatabasePool:
    """
    Optimized connection pool for PostgreSQL.
    
    Critical for performance under load.
    """
    
    def __init__(self, database_url: str, pool_size: int = 20):
        self.database_url = database_url
        self.pool_size = pool_size
        self.pool = None
    
    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            dsn=self.database_url,
            min_size=5,                    # Minimum connections always open
            max_size=self.pool_size,        # Limit to prevent exhaustion
            max_queries=50000,              # Reset after 50K queries
            max_inactive_connection_lifetime=300,  # Close idle after 5 min
            command_timeout=60,             # Query timeout
            statement_cache_size=100,       # Cache prepared statements
        )
    
    @asynccontextmanager
    async def acquire(self):
        async with self.pool.acquire() as conn:
            yield conn
    
    async def close(self):
        await self.pool.close()

# Pool sizing formula:
# Recommended = ((CPU cores * 2) + effective_spindle_count)
# For 4 CPU + SSD: (4 * 2) + 4 = 12 connections
# Max should not exceed PostgreSQL max_connections (default 100)

# Per environment:
POOL_SIZES = {
    'development': 5,
    'production': 20,
    'enterprise': 50
}
```

### Redis Connection Pooling

```python
# src/infrastructure/cache/redis_pool.py

import redis.asyncio as redis

class RedisPool:
    """
    Redis connection pool with health checks.
    """
    
    def __init__(self, redis_url: str, pool_size: int = 10):
        self.redis_url = redis_url
        self.pool_size = pool_size
        self.client = None
    
    async def initialize(self):
        self.client = redis.from_url(
            self.redis_url,
            max_connections=self.pool_size,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            health_check_interval=30,  # Check every 30 seconds
        )
    
    async def close(self):
        await self.client.close()
```

### CDN Configuration

```hcl
# infra/terraform/cdn.tf

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  price_class         = "PriceClass_100"  # US/EU only for cost
  http_version        = "http2"
  
  origin {
    domain_name = aws_lb.frontend.dns_name
    origin_id   = "frontend-origin"
    
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Static assets - aggressive caching (1 year)
  ordered_cache_behavior {
    path_pattern           = "/_next/static/*"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods        = ["GET", "HEAD"]
    
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"  # CachingOptimized
    
    compress = true
  }
  
  # Images - moderate caching
  ordered_cache_behavior {
    path_pattern           = "/_next/image*"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods        = ["GET", "HEAD"]
    
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    
    compress = true
  }
  
  # Default - API calls, no caching
  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods        = ["GET", "HEAD"]
    
    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"  # CachingDisabled
  }
  
  # Compression
  default.compress = true
  
  # SSL
  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.frontend.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
```

### Rate Limiting Service

```python
# src/application/rate_limiter.py

from redis.asyncio import Redis
from dataclasses import dataclass

@dataclass
class RateLimitConfig:
    requests_per_hour: int
    requests_per_minute: int
    experiments_per_month: int

RATE_LIMITS = {
    'free': RateLimitConfig(
        requests_per_hour=100,
        requests_per_minute=10,
        experiments_per_month=5
    ),
    'pro': RateLimitConfig(
        requests_per_hour=1000,
        requests_per_minute=100,
        experiments_per_month=50
    ),
    'enterprise': RateLimitConfig(
        requests_per_hour=10000,
        requests_per_minute=1000,
        experiments_per_month=-1  # Unlimited
    )
}

class RateLimiter:
    """
    Sliding window rate limiting per organization.
    """
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def check_limit(
        self,
        organization_id: str,
        plan: str
    ) -> tuple[bool, dict]:
        """
        Check if organization is within rate limits.
        
        Returns:
            (allowed: bool, metadata: dict with remaining, reset_time)
        """
        limits = RATE_LIMITS[plan]
        
        hour_key = f"rate:{organization_id}:hour"
        minute_key = f"rate:{organization_id}:minute"
        
        # Sliding window counts
        hour_count = await self.redis.incr(hour_key)
        minute_count = await self.redis.incr(minute_key)
        
        # Set expiry on first increment
        if hour_count == 1:
            await self.redis.expire(hour_key, 3600)
        if minute_count == 1:
            await self.redis.expire(minute_key, 60)
        
        allowed = (
            hour_count <= limits.requests_per_hour and
            minute_count <= limits.requests_per_minute
        )
        
        return allowed, {
            'hour_remaining': max(0, limits.requests_per_hour - hour_count),
            'minute_remaining': max(0, limits.requests_per_minute - minute_count),
            'limit_hour': limits.requests_per_hour,
            'limit_minute': limits.requests_per_minute
        }
```

---

## Security

### Network Security

```yaml
# Network Policy for backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgresql
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### Secrets Management

```yaml
# ExternalSecret for database credentials
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: postgres-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: ClusterSecretStore
  target:
    name: postgres-credentials
    creationPolicy: Owner
  data:
  - secretKey: url
    remoteRef:
      key: researchos/postgres
      property: url
  - secretKey: password
    remoteRef:
      key: researchos/postgres
      property: password
```

---

## Next Steps

- Docker deployment guide → [11-deployment-docker.md](./11-deployment-docker.md)
- Kubernetes deployment guide → [12-deployment-kubernetes.md](./12-deployment-kubernetes.md)
- AWS deployment guide → [13-deployment-aws.md](./13-deployment-aws.md)
