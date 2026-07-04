# ResearchOS - Monitoring & Disaster Recovery

## Overview

Comprehensive monitoring, alerting, and disaster recovery strategy for ResearchOS.

---

## Monitoring Stack

```
┌────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Application Layer                                             │ │
│  │  - OpenTelemetry SDK (traces, metrics)                        │ │
│  │  - Structured logging (JSON)                                   │ │
│  │  - Prometheus exporters                                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Collection Layer                                              │ │
│  │  - Prometheus (metrics scrape)                                 │ │
│  │  - OpenTelemetry Collector (traces)                            │ │
│  │  - Promtail (logs)                                              │ │
│  │  - StatsD Exporter (custom metrics)                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Storage Layer                                                  │ │
│  │  - Prometheus TSDB (metrics, 30d retention)                   │ │
│  │  - Jaeger (traces, 7d retention)                               │ │
│  │  - Loki (logs, 30d retention)                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Visualization Layer                                           │ │
│  │  - Grafana (dashboards)                                        │ │
│  │  - Jaeger UI (trace exploration)                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Alerting Layer                                                 │ │
│  │  - Alertmanager (dedup, routing)                               │ │
│  │  - PagerDuty (escalation)                                      │ │
│  │  - Slack (notifications)                                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## Metrics Architecture

### Application Metrics

```python
# src/api/middleware/metrics.py

from prometheus_client import Counter, Histogram, Gauge, Info
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

http_requests_in_flight = Gauge(
    'http_requests_in_flight',
    'Number of HTTP requests currently being processed',
    ['method']
)

# Business metrics
experiments_total = Gauge(
    'researchos_experiments_total',
    'Total experiments',
    ['organization_id', 'status']
)

runs_total = Gauge(
    'researchos_runs_total',
    'Total runs',
    ['experiment_id', 'status']
)

search_queries_total = Counter(
    'researchos_search_queries_total',
    'Total search queries',
    ['organization_id']
)

search_latency_seconds = Histogram(
    'researchos_search_latency_seconds',
    'Search query latency',
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.2, 0.5, 1.0]
)

# LLM metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['provider', 'model']
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['provider', 'model', 'type']
)

llm_latency_seconds = Histogram(
    'llm_latency_seconds',
    'LLM API request latency',
    ['provider', 'model'],
    buckets=[0.5, 1, 2, 5, 10, 30, 60]
)

# Event metrics
events_emitted_total = Counter(
    'events_emitted_total',
    'Total events emitted',
    ['event_type', 'organization_id']
)

events_processed_total = Counter(
    'events_processed_total',
    'Total events processed',
    ['event_type', 'consumer_group', 'status']
)

dlq_size = Gauge(
    'dlq_size',
    'Dead letter queue size',
    ['consumer_group']
)
```

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: researchos-prod
    region: us-east-1

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093

rule_files:
  - /etc/prometheus/rules/*.yml

scrape_configs:
  # Kubernetes pod discovery
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
    - role: pod
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)
    - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
      action: replace
      regex: ([^:]+)(?::\d+)?;(\d+)
      replacement: $1:$2
      target_label: __address__

  # PostgreSQL exporter
  - job_name: postgresql
    static_configs:
    - targets: ['postgres-exporter:9187']

  # Redis exporter
  - job_name: redis
    static_configs:
    - targets: ['redis-exporter:9121']

  # Node exporter
  - job_name: node
    static_configs:
    - targets: ['node-exporter:9100']

remote_write:
  - url: https://prometheus-us-east-1.amazonaws.com/workspaces/xxx/api/v1/remote_write
    sigv4:
      region: us-east-1
```

---

## Grafana Dashboards

### System Overview Dashboard

```json
{
  "dashboard": {
    "title": "ResearchOS Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [{
          "expr": "sum(rate(http_requests_total[5m]))",
          "legendFormat": "req/s"
        }]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [{
          "expr": "sum(rate(http_requests_total{status_code=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
          "legendFormat": "error rate"
        }],
        "alert": {
          "conditions": [{
            "evaluator": {"params": [0.05], "type": "gt"}
          }]
        }
      },
      {
        "title": "P99 Latency",
        "type": "graph",
        "targets": [{
          "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
          "legendFormat": "p99"
        }]
      },
      {
        "title": "Active Experiments",
        "type": "stat",
        "targets": [{
          "expr": "sum(researchos_experiments_total{status=\"running\"})",
          "legendFormat": "Running"
        }]
      },
      {
        "title": "Search Latency (SLA: <100ms)",
        "type": "graph",
        "targets": [{
          "expr": "histogram_quantile(0.99, sum(rate(researchos_search_latency_seconds_bucket[5m])) by (le)) * 1000",
          "legendFormat": "p99 (ms)"
        }],
        "thresholds": [
          {"value": 100, "color": "yellow"},
          {"value": 200, "color": "red"}
        ]
      },
      {
        "title": "LLM Cost/Hour",
        "type": "stat",
        "targets": [{
          "expr": "sum(rate(llm_tokens_total{type=\"output\"}[1h])) * 0.00003",
          "legendFormat": "$/hour"
        }]
      },
      {
        "title": "Event Processing Lag",
        "type": "graph",
        "targets": [{
          "expr": "redis_stream_length{stream=\"events\"}",
          "legendFormat": "{{stream}}"
        }]
      }
    ]
  }
}
```

---

## Alerting Rules

### Critical Alerts

```yaml
# monitoring/prometheus/rules/critical.yml

groups:
- name: critical.rules
  rules:
  - alert: InstanceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Instance {{ $labels.instance }} down"
      description: "{{ $labels.instance }} has been down for more than 1 minute."

  - alert: BackendDown
    expr: up{job="backend"} == 0
    for: 1m
    labels:
      severity: critical
      team: backend
    annotations:
      summary: "Backend pod down"
      runbook_url: "https://runbooks.researchos.ai/backend-down"

  - alert: PostgreSQLDown
    expr: pg_up == 0
    for: 1m
    labels:
      severity: critical
      team: dba
    annotations:
      summary: "PostgreSQL database down"

  - alert: RedisDown
    expr: redis_up == 0
    for: 1m
    labels:
      severity: critical
      team: backend
    annotations:
      summary: "Redis down"

  - alert: HighErrorRate
    expr: |
      sum(rate(http_requests_total{status_code=~"5.."}[5m])) 
      / sum(rate(http_requests_total[5m])) > 0.1
    for: 2m
    labels:
      severity: critical
      team: backend
    annotations:
      summary: "Error rate > 10%"
      description: "{{ $value | humanizePercentage }} of requests are failing"

  - alert: SearchSLAViolation
    expr: |
      histogram_quantile(0.99, sum(rate(researchos_search_latency_seconds_bucket[5m])) by (le)) > 0.1
    for: 5m
    labels:
      severity: critical
      team: search
    annotations:
      summary: "Search latency violates SLA (>100ms)"
```

### Warning Alerts

```yaml
# monitoring/prometheus/rules/warning.yml

groups:
- name: warning.rules
  rules:
  - alert: HighMemoryUsage
    expr: |
      container_memory_working_set_bytes / container_spec_memory_limit_bytes > 0.85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Memory usage > 85%"
      description: "{{ $labels.pod }} is using {{ $value | humanizePercentage }} of memory"

  - alert: PostgreSQLDiskSpace
    expr: |
      pg_database_size_bytes / pg_filesystem_size_bytes > 0.85
    for: 10m
    labels:
      severity: warning
      team: dba
    annotations:
      summary: "PostgreSQL disk usage > 85%"

  - alert: RedisMemoryHigh
    expr: |
      redis_memory_used_bytes / redis_memory_max_bytes > 0.85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Redis memory usage > 85%"

  - alert: ConsumerLag
    expr: redis_stream_length > 5000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Event consumer lag > 5000 messages"

  - alert: DLQGrowing
    expr: rate(dlq_size[5m]) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Dead letter queue is growing"

  - alert: HighLLMCost
    expr: |
      sum(rate(llm_tokens_total{type="output"}[1h])) * 0.00003 > 50
    for: 1h
    labels:
      severity: warning
      team: finance
    annotations:
      summary: "LLM cost > $50/hour"
```

---

## Distributed Tracing

### OpenTelemetry Setup

```python
# src/api/tracing.py

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

def setup_tracing(service_name: str, environment: str):
    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("APP_VERSION", "1.0"),
        "deployment.environment": environment,
    })
    
    provider = TracerProvider(resource=resource)
    
    processor = BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
        )
    )
    provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)
    
    # Auto-instrument
    FastAPIInstrumentor.instrument_app(app)
    AsyncPGInstrumentor().instrument()
    RedisInstrumentor().instrument()

# Usage
@app.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: UUID):
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("get_experiment") as span:
        span.set_attribute("experiment_id", str(experiment_id))
        
        experiment = await experiment_repo.get(experiment_id)
        
        span.set_attribute("experiment.name", experiment.name)
        span.set_attribute("experiment.status", experiment.status)
        
        return experiment
```

---

## Backup Strategy

### Backup Schedule

```
┌────────────────────────────────────────────────────────────────────┐
│                    BACKUP SCHEDULE                                   │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PostgreSQL                                                          │
│  ├── FullBackup: Daily at 2 AM UTC                                │
│  ├── WAL Archiving: Continuous                                    │
│  ├── Point-in-Time Recovery: 30 days                             │
│  └── Retention: 30 days (daily), 12 months (monthly)            │
│                                                                      │
│  Redis                                                               │
│  ├── RDB Snapshot: Every 6 hours                                  │
│  └── AOF: Every write operation (fsync every second)            │
│                                                                      │
│  S3 Objects                                                          │
│  ├── Versioning: Enabled                                          │
│  ├── Cross-region replication: Enabled                           │
│  └── Lifecycle: IA after 90 days, Glacier after 365 days        │
│                                                                      │
│  Kubernetes                                                          │
│  ├── etcd Backup: Daily                                           │
│  └── Secret Backup: Daily (sealed secrets)                       │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘
```

### Backup Scripts

```bash
#!/bin/bash
# scripts/backup-postgres.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="researchos_${TIMESTAMP}.dump"

# Create backup
pg_dump -Fc $DATABASE_URL > "/tmp/${BACKUP_FILE}"

# Upload to S3
aws s3 cp "/tmp/${BACKUP_FILE}" \
  "s3://researchos-backups/postgres/${BACKUP_FILE}" \
  --storage-class STANDARD_IA

# Verify
if ! aws s3 ls "s3://researchos-backups/postgres/${BACKUP_FILE}"; then
  echo "Backup failed" >&2
  exit 1
fi

# Clean up
rm "/tmp/${BACKUP_FILE}"

# Delete old backups (dry-run first)
aws s3 ls s3://researchos-backups/postgres/ | \
  awk '{print $4}' | \
  awk -F '_' '{print $1}' | \
  sort | \
  head -n -30 | \
  while read prefix; do
    aws s3 rm "s3://researchos-backups/postgres/" --recursive --exclude "*" --include "${prefix}*"
  done

echo "Backup completed: ${BACKUP_FILE}"
```

---

## Disaster Recovery

### RPO/RTO Targets

| Scenario | RPO | RTO | Strategy |
|----------|-----|-----|----------|
| Single pod failure | 0 | 30s | Kubernetes auto-restart |
| Node failure | 0 | 2 min | Pod rescheduling |
| AZ failure | 0 | 5 min | Multi-AZ deployment |
| Region failure | 15 min | 30 min | Cross-region failover |
| Data corruption | 1 hour | 2 hours | PITR from backup |
| Ransomware | 24 hours | 4 hours | Immutable backups |

### Failover Playbooks

```yaml
# runbooks/failover-region.yaml

name: Cross-Region Failover
description: Failover from us-east-1 to eu-west-1

triggers:
  - Region availability < 95%
  - Manual trigger by SRE team

steps:
  - name: 1. Assess Situation
    action: assess
    tasks:
      - Check primary region status
      - Verify standby region health
      - Estimate data loss (replication lag)
      - Notify stakeholders

  - name: 2. Promote PostgreSQL (eu-west-1)
    action: promote-postgres
    region: eu-west-1
    tasks:
      - Stop replication from primary
      - Promote replica to primary
      - Verify database connectivity
      - Update connection strings

  - name: 3. Promote Redis (eu-west-1)
    action: promote-redis
    region: eu-west-1
    tasks:
      - Promote replica to primary
      - Verify connectivity

  - name: 4. Update DNS
    action: update-dns
    provider: route53
    records:
      - name: api.researchos.ai
        type: CNAME
        value: eu-west-1-api.researchos.ai
        ttl: 60
      - name: app.researchos.ai
        type: CNAME
        value: eu-west-1-app.researchos.ai
        ttl: 60

  - name: 5. Scale Backend (eu-west-1)
    action: scale-deployment
    region: eu-west-1
    namespace: researchos
    deployment: backend
    replicas: 10

  - name: 6. Verify Traffic
    action: verify
    endpoint: https://api.researchos.ai/health
    check:
      status_code: 200
      latency_p99: < 200ms

  - name: 7. Notify Stakeholders
    action: notify
    channels:
      - pagerduty
      - slack
    message: |
      Failover to eu-west-1 completed successfully.
      - RPO: Measured lag
      - RTO: Measured duration
      - Data loss: Estimated
      See runbook for details.

rollback:
  - Update DNS back to primary
  - Scale down standby region
  - Resume replication
```

---

## Recovery Procedures

### Point-in-Time Recovery (PostgreSQL)

```bash
#!/bin/bash
# scripts/pitr-recovery.sh

TARGET_TIME=$1  # Format: "2024-01-15 10:30:00"
BASE_BACKUP=$2  # S3 path to base backup

# Download base backup
aws s3 cp "${BASE_BACKUP}" /tmp/base.dump
pg_restore -d researchos_recovery /tmp/base.dump

# Replay WAL up to target time
export PGPORT=5433
pg_ctl -D /var/lib/postgresql/recovery start -o "-c restore_command='aws s3 cp s3://researchos-wal/%f %p' -c recovery_target_time='${TARGET_TIME}' -c recovery_target_action='pause'"

# Wait for recovery
sleep 60

# Verify data
psql -p 5433 -d researchos_recovery -c "SELECT count(*) FROM experiments WHERE created_at <= '${TARGET_TIME}'"

# Promote if correct
pg_ctl -D /var/lib/postgresql/recovery promote
```

### S3 Cross-Region Recovery

```bash
#!/bin/bash
# scripts/s3-recovery.sh

BUCKET=researchos-artifacts-prod
BACKUP_BUCKET=researchos-artifacts-backup

# Enable versioning on backup bucket
aws s3api put-bucket-versioning \
  --bucket ${BACKUP_BUCKET} \
  --versioning-configuration Status=Enabled

# Cross-region replication
aws s3 sync \
  s3://${BUCKET} \
  s3://researchos-artifacts-eu/ \
  --storage-class STANDARD_IA
```

---

## Cost Optimization

### Resource Recommendations

```yaml
# Horizontal Pod Autoscaler cost optimization
backend:
  autoscaling:
    # Scale down during low traffic
    minReplicas: 2
    maxReplicas: 10
    
    # Use preemptible/spot for workers
    nodeSelector:
      node.kubernetes.io/instance-type: spot

# Right-sizing recommendations
resources:
  backend:
    # Start conservative
    requests:
      cpu: 250m
      memory: 512Mi
    # Allow burst
    limits:
      cpu: 2
      memory: 4Gi
  
  embedding_worker:
    # Embedding is compute-intensive
    requests:
      cpu: 1
      memory: 2Gi
    limits:
      cpu: 4
      memory: 8Gi
```

### Cost Alerts

```yaml
# monitoring/prometheus/rules/cost.yml

groups:
- name: cost.rules
  rules:
  - alert: HighComputeCost
    expr: |
      sum(rate(container_cpu_usage_seconds_total[1h])) * 0.05 > 100
    for: 6h
    labels:
      severity: warning
      team: finance
    annotations:
      summary: "Compute cost > $100/hour"

  - alert: HighDataTransferCost
    expr: |
      sum(rate(container_network_transmit_bytes_total[1h])) / 1e9 * 0.09 > 50
    labels:
      severity: warning
      team: finance
    annotations:
      summary: "Data transfer cost > $50/hour"
```

---

## Runbooks

```markdown
# Runbook: Backend High Latency

## Symptoms
- P99 latency > 500ms
- Alert: SlowResponseTime

## Investigation

### 1. Check Pod Metrics
```bash
kubectl top pods -n researchos -l app=backend
kubectl describe pod -n researchos -l app=backend | grep -A 5 Events
```

### 2. Check Database
```bash
kubectl exec -n researchos postgres-primary -- psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

### 3. Check Redis
```bash
kubectl exec -n researchos redis-primary -- redis-cli --latency-history
```

### 4. Check Traces
```
Open Jaeger UI and filter by slow traces (>500ms)
```

## Resolution

### High CPU
- Scale up: `kubectl scale deployment backend -n researchos --replicas=10`
- Investigate expensive queries

### Database Lock
- Identify blocking query
- `SELECT pg_cancel_backend(pid)` if necessary

### Memory Pressure
- Increase memory limits
- Check for memory leaks

## Escalation
- Slack: #sre-incidents
- PagerDuty: Backend team
```

---

## Backup Restore Testing

### Monthly Restore Verification

```yaml
# .github/workflows/backup-restore-test.yml

name: Monthly Backup Restore Test

on:
  schedule:
    - cron: '0 0 1 * *'  # First day of month at midnight UTC
  workflow_dispatch:

jobs:
  restore-test:
    runs-on: ubuntu-latest
    steps:
    - name: Create Test Environment
      run: |
        kubectl create namespace restore-test
        
    - name: Download Latest Backup
      run: |
        LATEST=$(aws s3 ls s3://researchos-backups/postgres/ | sort | tail -1 | awk '{print $4}')
        aws s3 cp s3://researchos-backups/postgres/${LATEST} /tmp/backup.dump
        
    - name: Restore Backup
      run: |
        # Deploy PostgreSQL
        kubectl run postgres-restore --image=postgres:16 -n restore-test \
          --env="POSTGRES_PASSWORD=test" \
          --env="POSTGRES_DB=researchos_test"
        
        sleep 30  # Wait for startup
        
        # Copy backup
        kubectl cp /tmp/backup.dump restore-test/postgres-restore:/tmp/backup.dump
        
        # Restore
        kubectl exec -n restore-test postgres-restore -- \
          pg_restore -U postgres -d researchos_test /tmp/backup.dump
        
    - name: Verify Data Integrity
      run: |
        # Check table counts
        kubectl exec -n restore-test postgres-restore -- \
          psql -U postgres -d researchos_test -c "
            SELECT
              (SELECT count(*) FROM experiments) as experiments,
              (SELECT count(*) FROM runs) as runs,
              (SELECT count(*) FROM metrics) as metrics,
              (SELECT count(*) FROM nodes) as nodes;
          "
        
        # Check referential integrity
        kubectl exec -n restore-test postgres-restore -- \
          psql -U postgres -d researchos_test -c "
            SELECT COUNT(*) as integrity_errors FROM (
              SELECT * FROM metrics m
              LEFT JOIN runs r ON m.run_id = r.id
              WHERE r.id IS NULL
            ) t;
          "
    
    - name: Measure RTO
      id: rto
      run: |
        START=$(date -d "1 hour ago" +%s)
        END=$(date +%s)
        RTO=$((END - START))
        echo "RTO_SECONDS=${RTO}" >> $GITHUB_OUTPUT
        echo "Restore completed in ${RTO} seconds"
        
    - name: Update Runbook
      run: |
        # Update runbook with actual RTO
        echo "- Last Restore: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> docs/RESTORE_LOG.md
        echo "- RTO: ${{ steps.rto.outputs.RTO_SECONDS }} seconds" >> docs/RESTORE_LOG.md
        echo "- Status: PASS" >> docs/RESTORE_LOG.md
        
    - name: Cleanup Test Environment
      if: always()
      run: |
        kubectl delete namespace restore-test --ignore-not-found=true
        
    - name: Notify on Failure
      if: failure()
      run: |
        curl -X POST "${{ secrets.SLACK_WEBHOOK_URL }}" \
          -H 'Content-type: application/json' \
          -d '{"text":"⚠️ Backup restore test FAILED. Check GitHub Actions."}'
        
    - name: Notify on Success
      run: |
        curl -X POST "${{ secrets.SLACK_WEBHOOK_URL }}" \
          -H 'Content-type: application/json' \
          -d "{\"text\":\"✅ Backup restore test PASSED. RTO: ${{ steps.rto.outputs.RTO_SECONDS }}s\"}"
```

### Restore Test Checklist

```
Monthly Restore Test Checklist:

Date: _______________
Backup File: _______________

□ Download latest backup from S3
□ Create isolated test environment
□ Restore backup to test PostgreSQL
□ Verify table counts match production
□ Check referential integrity
□ Verify pgvector indexes work
□ Test sample queries
□ Measure actual RTO
□ Document any issues
□ Update runbook
□ Cleanup test environment
□ Notify team of results

Results:
- Experiments restored: _______
- Runs restored: _______
- Metrics restored: _______
- Nodes restored: _______
- RTO: _______ seconds (target: <30 minutes)
- Issues found: _______

Sign-off: _______________
```

---

## Next Steps

- All deployment documentation complete
- Begin implementation phase
