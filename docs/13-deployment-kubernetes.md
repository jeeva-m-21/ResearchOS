# ResearchOS - Kubernetes Deployment

## Overview

Production-grade Kubernetes deployment with Helm charts, autoscaling, and production best practices.

---

## Prerequisites

- Kubernetes 1.28+
- Helm 3.14+
- kubectl configured
- PersistentVolume support
- Ingress controller (nginx or Traefik)
- Cert-Manager for TLS

---

## Helm Chart Structure

```
helm/researchos/
├── Chart.yaml
├── values.yaml
├── values-production.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── namespace.yaml
│   ├── backend/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml
│   │   ├── configmap.yaml
│   │   └── ingress.yaml
│   ├── frontend/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   ├── workers/
│   │   └── embedding-worker-deployment.yaml
│   ├── postgres/
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── backup-cronjob.yaml
│   ├── redis/
│   │   ├── statefulset.yaml
│   │   └── service.yaml
│   ├── monitoring/
│   │   ├── prometheus-servicemonitor.yaml
│   │   ├── grafana-dashboard-configmap.yaml
│   │   └── prometheus-rule.yaml
│   └── secrets/
│       ├── external-secret.yaml
│       └── sealed-secret.yaml
└── charts/
    └── postgres-cluster/
```

---

## Chart.yaml

```yaml
# helm/researchos/Chart.yaml

apiVersion: v2
name: researchos
description: ResearchOS - Research Operating System

type: application
version: 1.0.0
appVersion: "1.0.0"

dependencies:
  - name: postgresql
    version: "15.0.0"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled
    
  - name: redis
    version: "18.0.0"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
    
  - name: kube-prometheus-stack
    version: "55.0.0"
    repository: "https://prometheus-community.github.io/helm-charts"
    condition: monitoring.enabled
```

---

## values.yaml

```yaml
# helm/researchos/values.yaml

# Global settings
global:
  imageRegistry: ""
  imagePullSecrets: []
  storageClass: ""

# Namespace
namespace:
  create: true
  name: researchos

# Backend API
backend:
  replicaCount: 3
  image:
    repository: researchos/backend
    tag: "1.0.0"
    pullPolicy: IfNotPresent
  
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
  
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80
  
  readinessProbe:
    httpGet:
      path: /ready
      port: 8000
    initialDelaySeconds: 10
    periodSeconds: 10
  
  livenessProbe:
    httpGet:
      path: /health
      port: 8000
    initialDelaySeconds: 30
    periodSeconds: 10
  
  nodeSelector: {}
  tolerations: []
  affinity: {}

# Frontend (Next.js)
frontend:
  replicaCount: 2
  image:
    repository: researchos/frontend
    tag: "1.0.0"
    pullPolicy: IfNotPresent
  
  service:
    type: ClusterIP
    port: 3000
  
  resources:
    requests:
      cpu: 250m
      memory: 256Mi
    limits:
      cpu: 1
      memory: 512Mi
  
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

# Embedding Workers
workers:
  embedding:
    replicaCount: 2
    image:
      repository: researchos/backend
      tag: "1.0.0"
    command: ["python", "-m", "src.workers.embedding_worker"]
    
    resources:
      requests:
        cpu: 1
        memory: 2Gi
      limits:
        cpu: 4
        memory: 8Gi
    
    autoscaling:
      enabled: true
      minReplicas: 2
      maxReplicas: 10

# PostgreSQL
postgresql:
  enabled: true
  
  auth:
    postgresPassword: ""
    username: researchos
    password: ""
    database: researchos
  
  primary:
    persistence:
      enabled: true
      size: 100Gi
      storageClass: gp3
    
    resources:
      requests:
        cpu: 2
        memory: 4Gi
      limits:
        cpu: 8
        memory: 16Gi
    
    podAnnotations:
      prometheus.io/scrape: "true"
      prometheus.io/port: "9187"
  
  readReplicas:
    replicaCount: 2
    
    persistence:
      enabled: true
      size: 100Gi
    
    resources:
      requests:
        cpu: 1
        memory: 2Gi
  
  backup:
    enabled: true
    schedule: "0 2 * * *"
    retention: 7

# Redis
redis:
  enabled: true
  
  architecture: standalone
  
  auth:
    enabled: true
    password: ""
  
  master:
    persistence:
      enabled: true
      size: 10Gi
    
    resources:
      requests:
        cpu: 500m
        memory: 1Gi
      limits:
        cpu: 2
        memory: 4Gi
  
  cluster:
    nodes: 3
    replicas: 1

# Ingress
ingress:
  enabled: true
  className: nginx
  
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
  
  hosts:
    - host: researchos.example.com
      paths:
        - path: /
          service: frontend
        - path: /api
          service: backend
        - path: /ws
          service: backend
  
  tls:
    - secretName: researchos-tls
      hosts:
        - researchos.example.com
        - api.researchos.example.com

# Monitoring
monitoring:
  enabled: true
  
  prometheus:
    retention: 30d
    storage: 50Gi
  
  grafana:
    adminPassword: ""
  
  alertmanager:
    enabled: true
    slack:
      enabled: false
      apiUrl: ""
      channel: ""

# Secrets
secrets:
  backend: researchos-secrets
  
  externalSecrets:
    enabled: false
    secretStore:
      name: aws-secretsmanager
      kind: ClusterSecretStore

# Object Storage
storage:
  backend: s3
  
  s3:
    bucket: researchos-artifacts
    region: us-east-1
    endpoint: ""  # For MinIO
  
  minio:
    enabled: false

# LLM Configuration
llm:
  provider: openai
  
  openai:
    apiKey: ""
    model: gpt-4o
    embeddingModel: text-embedding-3-small
  
  anthropic:
    apiKey: ""
    model: claude-3-5-sonnet-20241022
```

---

## Backend Deployment

```yaml
# helm/researchos/templates/backend/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "researchos.fullname" . }}-backend
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "researchos.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  replicas: {{ .Values.backend.replicaCount }}
  selector:
    matchLabels:
      {{- include "researchos.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: backend
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
      labels:
        {{- include "researchos.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: backend
    spec:
      serviceAccountName: {{ include "researchos.serviceAccountName" . }}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: backend
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
          readOnlyRootFilesystem: true
        image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
        imagePullPolicy: {{ .Values.backend.image.pullPolicy }}
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {{ .Values.secrets.backend }}
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: {{ .Values.secrets.backend }}
              key: redis-url
        - name: RESEARCHOS_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: {{ .Values.secrets.backend }}
              key: secret-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: {{ .Values.secrets.backend }}
              key: openai-api-key
              optional: true
        - name: PROMETHEUS_ENABLED
          value: "true"
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://{{ include "researchos.fullname" . }}-jaeger:4317"
        - name: S3_BUCKET
          value: {{ .Values.storage.s3.bucket }}
        - name: S3_REGION
          value: {{ .Values.storage.s3.region }}
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: {{ .Values.secrets.backend }}
              key: aws-access-key-id
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: {{ .Values.secrets.backend }}
              key: aws-secret-access-key
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        resources:
          {{- toYaml .Values.backend.resources | nindent 10 }}
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: {{ .Values.backend.readinessProbe.initialDelaySeconds }}
          periodSeconds: {{ .Values.backend.readinessProbe.periodSeconds }}
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: {{ .Values.backend.livenessProbe.initialDelaySeconds }}
          periodSeconds: {{ .Values.backend.livenessProbe.periodSeconds }}
      volumes:
      - name: tmp
        emptyDir: {}
      {{- with .Values.backend.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.backend.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.backend.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

---

## Service Monitor

```yaml
# helm/researchos/templates/monitoring/prometheus-servicemonitor.yaml

{{- if .Values.monitoring.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "researchos.fullname" . }}-backend
  labels:
    {{- include "researchos.labels" . | nindent 4 }}
    release: prometheus
spec:
  selector:
    matchLabels:
      {{- include "researchos.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: backend
  endpoints:
  - port: http
    path: /metrics
    interval: 15s
    scrapeTimeout: 10s
{{- end }}
```

---

## Horizontal Pod Autoscaler

```yaml
# helm/researchos/templates/backend/hpa.yaml

{{- if .Values.backend.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "researchos.fullname" . }}-backend
  labels:
    {{- include "researchos.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "researchos.fullname" . }}-backend
  minReplicas: {{ .Values.backend.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.backend.autoscaling.maxReplicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.backend.autoscaling.targetCPUUtilizationPercentage }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ .Values.backend.autoscaling.targetMemoryUtilizationPercentage }}
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
{{- end }}
```

---

## PostgreSQL Backup CronJob

```yaml
# helm/researchos/templates/postgres/backup-cronjob.yaml

{{- if .Values.postgresql.backup.enabled }}
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {{ include "researchos.fullname" . }}-backup
spec:
  schedule: {{ .Values.postgresql.backup.schedule | quote }}
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:16-alpine
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -Fc $DATABASE_URL > /backup/researchos_$(date +%Y%m%d_%H%M%S).dump
              aws s3 cp /backup/researchos_$(date +%Y%m%d_%H%M%S).dump s3://{{ .Values.storage.s3.bucket }}/backups/postgres/
              # Clean up old backups
              find /backup -name "*.dump" -mtime +{{ .Values.postgresql.backup.retention }} -delete
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.secrets.backend }}
                  key: database-url
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.secrets.backend }}
                  key: aws-access-key-id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.secrets.backend }}
                  key: aws-secret-access-key
            volumeMounts:
            - name: backup
              mountPath: /backup
          volumes:
          - name: backup
            emptyDir: {}
          restartPolicy: OnFailure
{{- end }}
```

---

## PrometheusRule (Alerts)

```yaml
# helm/researchos/templates/monitoring/prometheus-rule.yaml

{{- if .Values.monitoring.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: {{ include "researchos.fullname" . }}-alerts
  labels:
    {{- include "researchos.labels" . | nindent 4 }}
    release: prometheus
spec:
  groups:
  - name: researchos.rules
    rules:
    - alert: BackendDown
      expr: up{job="{{ include "researchos.fullname" . }}-backend"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Backend instance down"
        description: "Backend pod {{ "{{" }} $labels.pod {{ "}}" }} is down for more than 1 minute."
    
    - alert: HighErrorRate
      expr: |
        sum(rate(http_requests_total{job="{{ include "researchos.fullname" . }}-backend",status=~"5.."}[5m])) 
        / sum(rate(http_requests_total{job="{{ include "researchos.fullname" . }}-backend"}[5m])) > 0.05
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High error rate (>5%)"
    
    - alert: SlowSearchLatency
      expr: |
        histogram_quantile(0.99, sum(rate(search_latency_seconds_bucket{job="{{ include "researchos.fullname" . }}-backend"}[5m])) by (le)) > 0.1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "P99 search latency exceeds 100ms SLA"
{{- end }}
```

---

## Installation

```bash
# Add Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Create namespace
kubectl create namespace researchos

# Create secrets
kubectl create secret generic researchos-secrets \
  --namespace=researchos \
  --from-literal=database-url='postgresql://researchos:password@researchos-postgresql:5432/researchos' \
  --from-literal=redis-url='redis://researchos-redis-master:6379/0' \
  --from-literal=secret-key='$(openssl rand -hex 32)' \
  --from-literal=openai-api-key='sk-...' \
  --from-literal=aws-access-key-id='AKIA...' \
  --from-literal=aws-secret-access-key='...'

# Install with Helm
helm install researchos ./helm/researchos \
  --namespace researchos \
  --values helm/researchos/values-production.yaml \
  --set ingress.hosts[0].host=researchos.yourdomain.com \
  --set ingress.tls[0].hosts[0]=researchos.yourdomain.com

# Verify installation
kubectl get pods -n researchos
kubectl get services -n researchos
kubectl get ingress -n researchos
```

---

## Next Steps

- AWS deployment → [14-deployment-aws.md](./14-deployment-aws.md)
- Monitoring setup → [15-monitoring.md](./15-monitoring.md)
