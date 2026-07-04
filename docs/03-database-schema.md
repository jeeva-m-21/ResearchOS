# ResearchOS - Database Schema Design

## Overview

ResearchOS uses a property graph model implemented in PostgreSQL with pgvector for semantic search. Every research object is a node with typed edges connecting them.

---

## Database Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Primary DB | PostgreSQL 16+ | Relational data, graph, search |
| Vector Extension | pgvector | Embeddings, similarity search |
| Trigram Extension | pg_trgm | Fuzzy text search |
| JSON Extension | Built-in JSONB | Flexible properties |
| Cache/Queue | Redis 7+ | Event streams, caching |

### Design Principles

1. **Graph-Centric**: Nodes and edges as first-class citizens
2. **Multi-Tenant**: `organization_id` on every table for RLS
3. **Versioning**: Immutable versions, mutable heads
4. **Soft Deletes**: `deleted_at` timestamp for audit trails
5. **Timestamps**: Automatic `created_at`, `updated_at` via triggers

---

## Core Enums

```sql
-- Node types for the research graph
CREATE TYPE node_type AS ENUM (
    'idea',
    'hypothesis',
    'experiment',
    'run',
    'paper',
    'dataset',
    'model',
    'notebook',
    'block',
    'citation',
    'person',
    'organization',
    'project',
    'task',
    'insight',
    'question',
    'answer',
    'metric',
    'artifact',
    'code'
);

-- Edge types for graph relationships
CREATE TYPE edge_type AS ENUM (
    'derives_from',
    'tests',
    'supports',
    'contradicts',
    'references',
    'uses',
    'generates',
    'contains',
    'belongs_to',
    'authored_by',
    'cites',
    'based_on',
    'extends',
    'replaces',
    'version_of',
    'fork_of',
    'merged_from'
);

-- Status enums
CREATE TYPE experiment_status AS ENUM (
    'created',
    'running',
    'paused',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE paper_status AS ENUM (
    'draft',
    'in_review',
    'published',
    'archived'
);

CREATE TYPE artifact_type AS ENUM (
    'model',
    'dataset',
    'image',
    'video',
    'audio',
    'text',
    'binary',
    'checkpoint',
    'log',
    'config'
);

CREATE TYPE block_type AS ENUM (
    'markdown',
    'python',
    'rust',
    'sql',
    'mermaid',
    'latex',
    'diagram',
    'experiment_card',
    'metric',
    'citation',
    'ai_summary'
);

CREATE TYPE execution_status AS ENUM (
    'pending',
    'running',
    'success',
    'failed',
    'timeout'
);
```

---

## Multi-Tenancy Tables

```sql
-- Organizations (tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_organizations_slug ON organizations(slug);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    avatar_url TEXT,
    auth_provider VARCHAR(50) NOT NULL,  -- 'email', 'google', 'github'
    auth_provider_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);

-- Organization memberships
CREATE TABLE organization_members (
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',  -- 'owner', 'admin', 'member', 'viewer'
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (organization_id, user_id)
);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    visibility VARCHAR(50) DEFAULT 'private',  -- 'private', 'public'
    metadata JSONB DEFAULT '{}',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_projects_organization ON projects(organization_id);
```

---

## Research Graph Tables

### Nodes

```sql
-- Core node table (property graph vertex)
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    node_type node_type NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    properties JSONB DEFAULT '{}',
    
    -- Version history (git-like DAG)
    version INT NOT NULL DEFAULT 1,
    parent_version_id UUID REFERENCES nodes(id),
    
    -- Branching
    branch VARCHAR(255) NOT NULL DEFAULT 'main',
    is_fork BOOLEAN NOT NULL DEFAULT FALSE,
    forked_from_id UUID REFERENCES nodes(id),
    
    -- Embedding for search (1536-dim for OpenAI text-embedding-3-small)
    embedding vector(1536),
    
    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B')
    ) STORED,
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT unique_node_version UNIQUE (organization_id, id, version)
);

-- Indexes
CREATE INDEX idx_nodes_organization ON nodes(organization_id);
CREATE INDEX idx_nodes_type ON nodes(organization_id, node_type);
CREATE INDEX idx_nodes_branch ON nodes(organization_id, branch);
CREATE INDEX idx_nodes_parent_version ON nodes(parent_version_id);
CREATE INDEX idx_nodes_search ON nodes USING GIN(search_vector);

-- HNSW index for vector similarity search
CREATE INDEX idx_nodes_embedding ON nodes USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Trigram index for fuzzy search
CREATE INDEX idx_nodes_title_trgm ON nodes USING gin(title gin_trgm_ops);
```

### Edges

```sql
-- Core edge table (property graph edge)
CREATE TABLE edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    edge_type edge_type NOT NULL,
    properties JSONB DEFAULT '{}',
    weight FLOAT NOT NULL DEFAULT 1.0 CHECK (weight >= 0 AND weight <= 1),
    
    -- Version
    version INT NOT NULL DEFAULT 1,
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT unique_edge UNIQUE (organization_id, source_id, target_id, edge_type, version)
);

-- Indexes
CREATE INDEX idx_edges_organization ON edges(organization_id);
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_edges_type ON edges(edge_type);

-- Graph traversal indexes
CREATE INDEX idx_edges_source_type ON edges(source_id, edge_type);
CREATE INDEX idx_edges_target_type ON edges(target_id, edge_type);
```

### Branches

```sql
-- Branches for versioning (git-like)
CREATE TABLE branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,  -- 'notebook', 'experiment', 'paper'
    entity_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_branch VARCHAR(255),
    head_commit_sha VARCHAR(40),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_merged BOOLEAN NOT NULL DEFAULT FALSE,
    merged_at TIMESTAMPTZ,
    merged_into VARCHAR(255),
    
    CONSTRAINT unique_branch UNIQUE (organization_id, entity_type, entity_id, name)
);

CREATE INDEX idx_branches_entity ON branches(entity_type, entity_id);
CREATE INDEX idx_branches_organization ON branches(organization_id);
```

### Commits

```sql
-- Commits for versioning
CREATE TABLE commits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    branch VARCHAR(255) NOT NULL,
    sha VARCHAR(40) UNIQUE NOT NULL,
    parent_sha VARCHAR(40),
    message TEXT,
    metadata JSONB DEFAULT '{}',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_commits_entity ON commits(entity_type, entity_id);
CREATE INDEX idx_commits_sha ON commits(sha);
CREATE INDEX idx_commits_branch ON commits(entity_type, entity_id, branch);
```

---

## Experiments Tables

```sql
-- Experiments
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    hypothesis_id UUID REFERENCES nodes(id),  -- Link to hypothesis node
    status experiment_status NOT NULL DEFAULT 'created',
    parameters JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    
    -- Graph node reference
    node_id UUID REFERENCES nodes(id),
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_experiments_organization ON experiments(organization_id);
CREATE INDEX idx_experiments_project ON experiments(project_id);
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_tags ON experiments USING GIN(tags);

-- Runs
CREATE TABLE runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    run_number INT NOT NULL,
    status experiment_status NOT NULL DEFAULT 'created',
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    duration_ms BIGINT,
    
    -- Git context
    git_commit VARCHAR(40),
    git_branch VARCHAR(255),
    git_dirty BOOLEAN DEFAULT FALSE,
    
    -- Parameters (snapshot at run time)
    parameters JSONB DEFAULT '{}',
    
    -- Graph node reference
    node_id UUID REFERENCES nodes(id),
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT unique_run_number UNIQUE (experiment_id, run_number)
);

CREATE INDEX idx_runs_experiment ON runs(experiment_id);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_runs_time ON runs(started_at DESC);

-- Metrics (time-series data) - PARTITIONED for scalability
-- CRITICAL: Partitioning is required for high-volume metrics (>1M rows/month)
-- Without partitioning: vacuum, index bloat, query degradation

CREATE EXTENSION IF NOT EXISTS pg_partman;

CREATE TABLE metrics (
    id UUID DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value FLOAT NOT NULL,
    step INT NOT NULL DEFAULT 0,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    PRIMARY KEY (run_id, key, step, timestamp)
) PARTITION BY RANGE (timestamp);

-- Automated partition management with pg_partman
-- Creates monthly partitions automatically
SELECT partman.create_parent(
    p_parent_table := 'public.metrics',
    p_control := 'timestamp',
    p_type := 'native',
    p_interval := '1 month',
    p_premake := 3,
    p_start_partition := CONCAT(to_char(DATE_TRUNC('month', NOW()), 'YYYY-MM-DD'), ' 00:00:00')
);

-- Indexes on parent table (applied to all partitions)
CREATE INDEX idx_metrics_run_key ON metrics(run_id, key, step);
CREATE INDEX idx_metrics_run_time ON metrics(run_id, timestamp DESC);
CREATE INDEX idx_metrics_key_value ON metrics(organization_id, key, value);

-- Partition retention: Auto-drop partitions older than 12 months
UPDATE partman.part_config 
SET retention = '12 months',
    retention_keep_table = false
WHERE parent_table = 'public.metrics';

-- Aggregation table for historical data
CREATE TABLE metric_rollups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    min_value FLOAT NOT NULL,
    max_value FLOAT NOT NULL,
    avg_value FLOAT NOT NULL,
    count INT NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    
    CONSTRAINT unique_metric_rollup UNIQUE (run_id, key, period_start)
);

CREATE INDEX idx_metric_rollups_run ON metric_rollups(run_id);
CREATE INDEX idx_metric_rollups_time ON metric_rollups(period_start DESC);

-- Parameters (alternative: could be in runs.parameters JSONB)
CREATE TABLE parameters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(50) NOT NULL,  -- 'string', 'int', 'float', 'bool', 'json'
    
    CONSTRAINT unique_parameter UNIQUE (run_id, key)
);

CREATE INDEX idx_parameters_run ON parameters(run_id);
```

---

## Notebooks Tables

```sql
-- Notebooks
CREATE TABLE notebooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    branch VARCHAR(255) NOT NULL DEFAULT 'main',
    parent_commit VARCHAR(40),
    
    -- Graph node reference
    node_id UUID REFERENCES nodes(id),
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_notebooks_organization ON notebooks(organization_id);
CREATE INDEX idx_notebooks_project ON notebooks(project_id);

-- Notebook blocks (ordered, versioned)
CREATE TABLE blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    block_type block_type NOT NULL,
    position INT NOT NULL,
    
    -- Current content version
    current_version INT NOT NULL DEFAULT 1,
    
    -- Execute settings
    auto_execute BOOLEAN DEFAULT FALSE,
    timeout_ms INT DEFAULT 30000,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT unique_block_position UNIQUE (notebook_id, position)
);

CREATE INDEX idx_blocks_notebook ON blocks(notebook_id);
CREATE INDEX idx_blocks_position ON blocks(notebook_id, position);

-- Block content (immutable versions)
CREATE TABLE block_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_id UUID NOT NULL REFERENCES blocks(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    version INT NOT NULL,
    content TEXT NOT NULL,
    language VARCHAR(50),  -- For code blocks: 'python', 'rust', 'sql'
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_block_content_version UNIQUE (block_id, version)
);

CREATE INDEX idx_block_contents_block ON block_contents(block_id);

-- Block executions
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_content_id UUID NOT NULL REFERENCES block_contents(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    notebook_id UUID NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    status execution_status NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_ms INT,
    output TEXT,
    error TEXT,
    
    -- Generated artifacts
    artifact_ids UUID[] DEFAULT '{}',
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id)
);

CREATE INDEX idx_executions_block_content ON executions(block_content_id);
CREATE INDEX idx_executions_notebook ON executions(notebook_id);
CREATE INDEX idx_executions_status ON executions(status);
```

---

## Papers Tables

```sql
-- Papers
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    abstract TEXT,
    status paper_status NOT NULL DEFAULT 'draft',
    version INT NOT NULL DEFAULT 1,
    doi VARCHAR(255),
    arxiv_id VARCHAR(50),
    
    -- Graph node reference
    node_id UUID REFERENCES nodes(id),
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_papers_organization ON papers(organization_id);
CREATE INDEX idx_papers_project ON papers(project_id);

-- Citations (bibliography entries)
CREATE TABLE citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    citation_key VARCHAR(255) NOT NULL,
    cited_paper_id UUID REFERENCES papers(id),  -- Internal reference
    cited_doi VARCHAR(255),  -- External reference
    title VARCHAR(500) NOT NULL,
    authors TEXT[] NOT NULL,
    year INT NOT NULL,
    venue VARCHAR(255),
    page_numbers VARCHAR(50),
    url TEXT,
    
    -- Full citation text
    citation_text TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_citation_key UNIQUE (paper_id, citation_key)
);

CREATE INDEX idx_citations_paper ON citations(paper_id);
CREATE INDEX idx_citations_cited_paper ON citations(cited_paper_id);

-- References (inline citation usage)
CREATE TABLE references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    citation_id UUID NOT NULL REFERENCES citations(id) ON DELETE CASCADE,
    block_id UUID REFERENCES blocks(id),
    context TEXT,  -- Surrounding text
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_references_paper ON references(paper_id);
CREATE INDEX idx_references_citation ON references(citation_id);
```

---

## Artifacts Tables

```sql
-- Artifacts
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    artifact_type artifact_type NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    hash_sha256 VARCHAR(64) NOT NULL,
    current_version INT NOT NULL DEFAULT 1,
    
    -- Lineage
    experiment_id UUID REFERENCES experiments(id) ON DELETE SET NULL,
    run_id UUID REFERENCES runs(id) ON DELETE SET NULL,
    notebook_id UUID REFERENCES notebooks(id) ON DELETE SET NULL,
    
    -- Graph node reference
    node_id UUID REFERENCES nodes(id),
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_artifacts_organization ON artifacts(organization_id);
CREATE INDEX idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX idx_artifacts_run ON artifacts(run_id);
CREATE INDEX idx_artifacts_experiment ON artifacts(experiment_id);

-- Artifact versions (immutable)
CREATE TABLE artifact_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    version INT NOT NULL,
    storage_path TEXT NOT NULL,  -- S3 path
    size_bytes BIGINT NOT NULL,
    hash_sha256 VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_artifact_version UNIQUE (artifact_id, version)
);

CREATE INDEX idx_artifact_versions_artifact ON artifact_versions(artifact_id);

-- Artifact lineage
CREATE TABLE artifact_lineage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_version_id UUID NOT NULL REFERENCES artifact_versions(id) ON DELETE CASCADE,
    parent_artifact_version_id UUID REFERENCES artifact_versions(id) ON DELETE CASCADE,
    transform_description TEXT,
    transform_code TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_artifact_lineage_version ON artifact_lineage(artifact_version_id);
CREATE INDEX idx_artifact_lineage_parent ON artifact_lineage(parent_artifact_version_id);
```

---

## AI Context Tables

```sql
-- AI agent sessions
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_types TEXT[] NOT NULL,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE INDEX idx_agent_sessions_organization ON agent_sessions(organization_id);
CREATE INDEX idx_agent_sessions_user ON agent_sessions(user_id);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'user', 'assistant', 'system', 'tool'
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_session ON messages(session_id);

-- Tool calls
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    arguments JSONB NOT NULL,
    result TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_tool_calls_message ON tool_calls(message_id);
CREATE INDEX idx_tool_calls_status ON tool_calls(status);
```

---

## Event Store Tables

```sql
-- Event store (append-only log)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL UNIQUE,  -- Client-generated for idempotency
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_type VARCHAR(255) NOT NULL,
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    version INT NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Processing status
    processed_at TIMESTAMPTZ,
    processing_error TEXT
);

-- Indexes
CREATE INDEX idx_events_organization ON events(organization_id);
CREATE INDEX idx_events_event_type ON events(event_type);
CREATE INDEX idx_events_aggregate ON events(aggregate_id, aggregate_type);
CREATE INDEX idx_events_created_at ON events(created_at DESC);
CREATE UNIQUE INDEX idx_events_event_id ON events(event_id);

-- Event projections (for CQRS read models)
CREATE TABLE event_projections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projection_name VARCHAR(255) NOT NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    last_event_id UUID NOT NULL,
    last_event_timestamp TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_projection UNIQUE (projection_name, organization_id)
);
```

---

## Row-Level Security

```sql
-- Enable RLS on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE notebooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;

-- RLS policy: user must be member of organization
CREATE POLICY organization_isolation ON organizations
    USING (id IN (
        SELECT organization_id FROM organization_members WHERE user_id = current_user_id()
    ));

CREATE POLICY project_isolation ON projects
    USING (organization_id IN (
        SELECT organization_id FROM organization_members WHERE user_id = current_user_id()
    ));

CREATE POLICY node_isolation ON nodes
    USING (organization_id IN (
        SELECT organization_id FROM organization_members WHERE user_id = current_user_id()
    ));

-- Similar policies for all other tables...
```

---

## Views

### Active Experiments View

```sql
CREATE VIEW active_experiments AS
SELECT 
    e.id,
    e.name,
    e.status,
    e.project_id,
    e.organization_id,
    COUNT(r.id) AS run_count,
    MAX(r.started_at) AS last_run_at
FROM experiments e
LEFT JOIN runs r ON e.id = r.experiment_id AND r.deleted_at IS NULL
WHERE e.deleted_at IS NULL
GROUP BY e.id;
```

### Metric Summary View

```sql
CREATE VIEW metric_summary AS
SELECT 
    m.key,
    m.run_id,
    r.experiment_id,
    MIN(m.value) AS min_value,
    MAX(m.value) AS max_value,
    AVG(m.value) AS avg_value,
    COUNT(m.id) AS count,
    MAX(m.timestamp) AS last_updated
FROM metrics m
JOIN runs r ON m.run_id = r.id
GROUP BY m.key, m.run_id, r.experiment_id;
```

### Graph Traversal View

```sql
-- Recursive CTE for graph traversal
CREATE VIEW graph_descendants AS
WITH RECURSIVE descendants AS (
    -- Base case: direct children
    SELECT 
        source_id,
        target_id,
        edge_type,
        1 AS depth,
        ARRAY[target_id] AS path
    FROM edges
    WHERE deleted_at IS NULL
    
    UNION ALL
    
    -- Recursive case: children of children
    SELECT 
        d.source_id,
        e.target_id,
        e.edge_type,
        d.depth + 1,
        d.path || e.target_id
    FROM descendants d
    JOIN edges e ON d.target_id = e.source_id
    WHERE e.deleted_at IS NULL
    AND d.depth < 10  -- Max depth
    AND e.target_id != ALL(d.path)  -- Prevent cycles
)
SELECT * FROM descendants;
```

---

## Functions & Triggers

### Automatic Timestamps

```sql
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all tables with updated_at
CREATE TRIGGER update_organizations_modtime
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Repeat for all tables...
```

### Search Vector Update

```sql
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$ language 'plpgsql';
```

---

## Indexing Strategy

### Primary Indexes
- `id` - all tables (PRIMARY KEY)
- `organization_id` - all tables (RLS, multi-tenancy)

### Secondary Indexes

| Table | Index | Purpose |
|-------|-------|---------|
| nodes | `(organization_id, node_type)` | Filter by type |
| nodes | `GIN(search_vector)` | Full-text search |
| nodes | `HNSW(embedding)` | Vector similarity |
| edges | `(source_id, edge_type)` | Graph traversal |
| metrics | `(run_id, key, step)` | Time-series queries |
| events | `(event_type)` | Event replay |

### Partial Indexes

```sql
-- Active experiments only
CREATE INDEX idx_experiments_active ON experiments(organization_id, status)
    WHERE deleted_at IS NULL AND status IN ('created', 'running');

-- Unprocessed events
CREATE INDEX idx_events_unprocessed ON events(created_at)
    WHERE processed_at IS NULL;
```

---

## Partitioning Strategy

### Metrics (Time-Series)

```sql
-- Partition metrics by month for large datasets
CREATE TABLE metrics_2024_01 PARTITION OF metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE metrics_2024_02 PARTITION OF metrics
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

### Events (Time-Series)

```sql
-- Partition events by month
CREATE TABLE events_2024_01 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

---

## Data Retention

### Metric Rollup

```sql
-- Aggregate old metrics (e.g., older than 90 days)
CREATE TABLE metric_rollups (
    run_id UUID NOT NULL REFERENCES runs(id),
    key VARCHAR(255) NOT NULL,
    min_value FLOAT,
    max_value FLOAT,
    avg_value FLOAT,
    count INT,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (run_id, key, period_start)
);
```

---

## Migration Strategy

All schema changes use Alembic migrations:

```
backend/
├── alembic/
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_branches.py
│   │   └── 003_add_embeddings.py
│   ├── env.py
│   └── alembic.ini
```

---

## Next Steps

- Python SDK design → [04-python-sdk.md](./04-python-sdk.md)
- Event architecture → [09-event-architecture.md](./09-event-architecture.md)
