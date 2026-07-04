# ResearchOS - AWS Deployment Guide

## Overview

Production deployment on AWS using EKS, RDS, ElastiCache, and S3.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AWS ARCHITECTURE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Route 53 (DNS)                                                               │
│  ├── researchos.ai → CloudFront                               │
│  └── api.researchos.ai → ALB                                                 │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           VPC (10.0.0.0/16)                          │    │
│  │  ┌───────────────────────────────────────────────────────────────┐ │    │
│  │  │                    Public Subnets                               │ │    │
│  │  │  10.0.1.0/24 (us-east-1a)  10.0.2.0/24 (us-east-1b)           │ │    │
│  │  │  - ALB                  - ALB                                 │ │    │
│  │  │  - NAT Gateway          - NAT Gateway                          │ │    │
│  │  └───────────────────────────────────────────────────────────────┘ │    │
│  │  ┌───────────────────────────────────────────────────────────────┐ │    │
│  │  │                    Private Subnets                              │ │    │
│  │  │  10.0.10.0/24 (us-east-1a)  10.0.20.0/24 (us-east-1b)       │ │    │
│  │  │                                                                   │ │    │
│  │  │  ┌─────────────────────────────────────────────────────────┐  │ │    │
│  │  │  │                    EKS Cluster                             │  │ │    │
│  │  │  │  Node Group: m6i.xlarge (3-20 nodes)                      │  │ │    │
│  │  │  │                                                             │  │ │    │
│  │  │  │  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐             │  │ │    │
│  │  │  │  │Backend│  │Frontend│ │Worker │  │Monitoring│          │  │ │    │
│  │  │  │  └───────┘  └───────┘  └───────┘  └───────┘             │  │ │    │
│  │  │  └─────────────────────────────────────────────────────────┘  │ │    │
│  │  │                                                                   │ │    │
│  │  │  ┌─────────────────────────────────────────────────────────┐  │ │    │
│  │  │  │                    RDS PostgreSQL                         │  │ │    │
│  │  │  │  db.r6g.xlarge (Primary) + 2 Read Replicas              │  │ │    │
│  │  │  │  Multi-AZ, Encrypted, Automated Backups                  │  │ │    │
│  │  │  └─────────────────────────────────────────────────────────┘  │ │    │
│  │  │                                                                   │ │    │
│  │  │  ┌─────────────────────────────────────────────────────────┐  │ │    │
│  │  │  │                    ElastiCache Redis                      │  │ │    │
│  │  │  │  cache.r6g.large (3 nodes, cluster mode)                │  │ │    │
│  │  │  │  Multi-AZ, Encryption at rest                           │  │ │    │
│  │  │  └─────────────────────────────────────────────────────────┘  │ │    │
│  │  └───────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    S3 Buckets                                        │    │
│  │  - researchos-artifacts-{account} (Object storage)                  │    │
│  │  - researchos-backups-{account} (Database backups)                 │    │
│  │  - researchos-wal-{account} (WAL archival)                          │    │
│  │  Versioning, Encryption, Cross-region replication                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Monitoring                                         │    │
│  │  - CloudWatch (Metrics, Alarms, Logs)                                │    │
│  │  - Prometheus (on EKS, remote write to CloudWatch)                 │    │
│  │  - Grafana (on EKS)                                                  │    │
│  │  - AWS X-Ray (Tracing)                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Security                                          │    │
│  │  - IAM Roles for Service Accounts (IRSA)                             │    │
│  │  - Secrets Manager                                                    │    │
│  │  - AWS KMS (Encryption)                                              │    │
│  │  - VPC Flow Logs                                                      │    │
│  │  - AWS Shield (DDoS protection)                                     │    │
│  │  - AWS WAF (Web Application Firewall)                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Infrastructure as Code (Terraform)

### VPC

```hcl
# infra/terraform/vpc.tf

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "researchos-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.10.0/24", "10.0.20.0/24", "10.0.30.0/24"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = true

  enable_vpn_gateway = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }

  tags = local.common_tags
}
```

### EKS Cluster

```hcl
# infra/terraform/eks.tf

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.0.0"

  cluster_name    = "researchos"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  # Managed Node Groups
  eks_managed_node_group_defaults = {
    ami_type       = "AL2_x86_64"
    instance_types = ["m6i.xlarge"]
    capacity_type  = "ON_DEMAND"

    attach_cluster_primary_security_group = true
  }

  eks_managed_node_groups = {
    frontend = {
      name = "frontend"
      
      min_size     = 2
      max_size     = 10
      desired_size = 2

      instance_types = ["c6i.large"]
      capacity_type  = "ON_DEMAND"

      labels = {
        role = "frontend"
      }
    }

    backend = {
      name = "backend"
      
      min_size     = 3
      max_size     = 20
      desired_size = 3

      instance_types = ["m6i.xlarge", "m5.xlarge"]
      capacity_type  = "MIXED"
      
      mixed_instances_policy = {
        instances = ["m6i.xlarge", "m5.xlarge", "m5a.xlarge"]
        on_demand_base_capacity                  = 3
        on_demand_percentage_above_base_capacity = 50
        spot_instance_pools                      = 3
      }

      labels = {
        role = "backend"
      }

      taints = []
    }

    workers = {
      name = "workers"
      
      min_size     = 2
      max_size     = 10
      desired_size = 2

      instance_types = ["c6i.2xlarge"]
      capacity_type  = "SPOT"

      labels = {
        role = "worker"
      }
    }
  }

  # IRSA for S3 access
  manage_aws_auth_configmap = true

  aws_auth_roles = [
    {
      rolearn  = module.eks.eks_managed_node_groups["backend"].iam_role_arn
      username = "system:node:{{EC2PrivateDNSName}}"
      groups   = ["system:bootstrappers", "system:nodes"]
    }
  ]

  tags = local.common_tags
}

# IRSA for pods
module "irsa_s3" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.0.0"

  role_name = "researchos-s3"

  attach_s3_policy = true
  s3_policy_arns    = [aws_iam_policy.s3.arn]

  oidc_provider_arn          = module.eks.oidc_provider_arn
  oidc_provider_fqdn         = replace(module.eks.oidc_provider, "https://", "")

  tags = local.common_tags
}

# Service Account for backend
resource "kubernetes_service_account" "backend" {
  depends_on = [module.irsa_s3]

  metadata {
    name      = "backend"
    namespace = "researchos"

    annotations = {
      "eks.amazonaws.com/role-arn" = module.irsa_s3.iam_role_arn
    }
  }
}
```

### RDS PostgreSQL

```hcl
# infra/terraform/rds.tf

resource "aws_db_parameter_group" "researchos" {
  name   = "researchos-postgres16"
  family = "postgres16"

  parameter {
    name  = "pgvector Preview"
    value = "1"
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pgvector"
  }

  parameter {
    name  = "max_connections"
    value = "200"
  }

  parameter {
    name  = "work_mem"
    value = "65536"
  }

  parameter {
    name  = "maintenance_work_mem"
    value = "262144"
  }

  tags = local.common_tags
}

module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "6.0.0"

  identifier = "researchos"

  engine               = "postgres"
  engine_version       = "16.2"
  major_engine_version = "16"
  family               = "postgres16"

  instance_class = "db.r6g.xlarge"

  allocated_storage     = 1000
  max_allocated_storage = 2000

  db_name  = "researchos"
  username = "researchos"
  port     = "5432"

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [module.security_group.security_group_id]

  maintenance_window              = "Sun:02:00-Sun:03:00"
  backup_window                   = "03:00-04:00"
  backup_retention_period         = 30
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  deletion_protection             = true
  skip_final_snapshot             = false
  final_snapshot_identifier       = "researchos-final-snapshot"

  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  monitoring_interval          = 60
  monitoring_role_arn         = module.rds_monitoring.iam_role_arn
  monitoring_role_name        = "rd-monitoring"
  create_monitoring_role     = true

  parameter_group_name = aws_db_parameter_group.researchos.name

  # Read replicas
  read_replica_count = 2
  replica_auto_scaling_enabled = true
  replica_auto_scaling_min_capacity = 1
  replica_auto_scaling_max_capacity = 3
  replica_auto_scaling_target_connections = 100

  # Storage
  storage_encrypted = true
  kms_key_arn       = aws_kms_key.rds.arn

  tags = local.common_tags
}

# S3 bucket for WAL archiving
resource "aws_s3_bucket" "wal_archive" {
  bucket = "researchos-wal-${data.aws_caller_identity.current.account_id}"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    enabled = true

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 2555  # 7 years
    }
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "aws:kms"
        kms_master_key_id = aws_kms_key.s3.key_id
      }
    }
  }

  tags = local.common_tags
}
```

### ElastiCache Redis

```hcl
# infra/terraform/elasticache.tf

module "elasticache" {
  source  = "terraform-aws-modules/elasticache/aws"
  version = "1.0.0"

  cluster_enabled = true

  engine               = "redis"
  engine_version       = "7.2"
  parameter_group_name = "default.redis7.cluster"

  num_node_groups       = 3
  replicas_per_node_group = 2

  node_type            = "cache.r6g.large"
  maintenance_window   = "sun:02:00-sun:03:00"

  subnet_group_name    = "researchos"
  subnet_ids           = module.vpc.private_subnets
  security_group_ids   = [module.security_group.security_group_id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis.result

  tags = local.common_tags
}

resource "aws_secretsmanager_secret" "redis" {
  name = "researchos/redis"
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "redis" {
  secret_id = aws_secretsmanager_secret.redis.id
  secret_string = jsonencode({
    url         = "rediss://:${random_password.redis.result}@${module.elasticache.cluster_address}:6379/0"
    host        = module.elasticache.cluster_address
    port        = 6379
    auth_token  = random_password.redis.result
  })
}
```

### S3 Buckets

```hcl
# infra/terraform/s3.tf

resource "aws_s3_bucket" "artifacts" {
  bucket = "researchos-artifacts-${data.aws_caller_identity.current.account_id}"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    id      = "transition-to-ia"
    enabled = true

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }

    expiration {
      days = 2555
    }
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "aws:kms"
        kms_master_key_id = aws_kms_key.s3.key_id
      }
    }
  }

  tags = local.common_tags
}

# Cross-region replication
resource "aws_s3_bucket_replication_configuration" "artifacts" {
  role   = aws_iam_role.replication.arn
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "replicate-to-eu-west-1"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.artifacts_eu.arn
      storage_class = "STANDARD"
      
      encryption_configuration {
        replica_kms_key_id = aws_kms_key.s3_eu.key_id
      }
    }

    source_selection_criteria {
      sse_kms_encrypted_objects {
        status = "Enabled"
      }
    }
  }
}
```

---

## Deployment Commands

```bash
# Initialize Terraform
cd infra/terraform
terraform init

# Plan
terraform plan -var-file=production.tfvars

# Apply
terraform apply -var-file=production.tfvars

# Get kubeconfig
aws eks update-kubeconfig --name researchos --region us-east-1

# Install controllers
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.0/deploy/static/provider/aws/deploy.yaml

# Install cert-manager
helm repo add jetstack https://charts.jetstream.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Install ResearchOS
helm install researchos ../helm/researchos \
  --namespace researchos \
  --create-namespace \
  --values values-production.yaml \
  --set ingress.hosts[0].host=researchos.yourdomain.com
```

---

## Backup Strategy

```hcl
# infra/terraform/backup.tf

resource "aws_backup_plan" "researchos" {
  name = "researchos-backup-plan"

  rule {
    rule_name         = "daily-backup"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 2 * * ? *)"

    lifecycle {
      delete_after = 30
    }

    recovery_point_tags = local.common_tags
  }

  rule {
    rule_name         = "weekly-backup"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 2 ? * SUN *)"

    lifecycle {
      delete_after = 90
    }
  }

  rule {
    rule_name         = "monthly-backup"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 2 1 * ? *)"

    lifecycle {
      cold_storage_after = 30
      delete_after       = 365
    }
  }
}

resource "aws_backup_selection" "researchos" {
  name         = "researchos-backup-selection"
  plan_id      = aws_backup_plan.researchos.id
  iam_role_arn = aws_iam_role.backup.arn

  resources = [
    module.rds.db_instance_arn,
    aws_s3_bucket.artifacts.arn
  ]
}
```

---

## Cost Estimation

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| EKS | 1 cluster, 5 nodes | $500 |
| EC2 | 5x m6i.xlarge | $600 |
| RDS | db.r6g.xlarge + 2 replicas | $800 |
| ElastiCache | 3x cache.r6g.large | $400 |
| S3 | 500GB storage + 1TB transfer | $50 |
| ALB + CloudFront | - | $100 |
| CloudWatch | Logs + Metrics | $100 |
| **Total** | | **~$2,550/mo** |

---

## Next Steps

- Monitoring setup → [15-monitoring.md](./15-monitoring.md)
