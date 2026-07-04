# backend/alembic/versions/001_initial_schema.py
"""Initial schema creation

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # CREATE EXTENSIONS
    # ============================================
    # op.execute("CREATE EXTENSION IF NOT EXISTS pgvector")  # Phase 2 feature
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    # op.execute("CREATE EXTENSION IF NOT EXISTS pg_partman")  # Phase 2 feature
    
    # ============================================
    # CREATE ENUMS
    # ============================================
    
    # Node types for the research graph
    op.execute("""
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
        )
    """)
    
    # Edge types for graph relationships
    op.execute("""
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
        )
    """)
    
    # Status enums
    op.execute("""
        CREATE TYPE experiment_status AS ENUM (
            'created',
            'running',
            'paused',
            'completed', 
            'failed',
            'cancelled'
        )
    """)
    
    op.execute("""
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
        )
    """)
    
    # ============================================
    # CREATE ORGANIZATIONS (Tenants)
    # ============================================
    op.create_table('organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('plan', sa.String(length=50), server_default='free', nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    
    # ============================================
    # CREATE USERS
    # ============================================
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('auth_provider', sa.String(length=50), nullable=False),
        sa.Column('auth_provider_id', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # ============================================
    # CREATE ORGANIZATION MEMBERSHIPS
    # ============================================
    op.create_table('organization_members',
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='member', nullable=False),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('organization_id', 'user_id')
    )
    
    # ============================================
    # CREATE PROJECTS
    # ============================================
    op.create_table('projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('visibility', sa.String(length=50), server_default='private', nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ============================================
    # CREATE NODES (Research Graph Vertices)
    # ============================================
    op.create_table('nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_type', sa.Enum('idea', 'hypothesis', 'experiment', 'run', 'paper', 'dataset', 'model', 'notebook', 'block', 'citation', 'person', 'organization', 'project', 'task', 'insight', 'question', 'answer', 'metric', 'artifact', 'code', name='node_type'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        
        # Version history
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('parent_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Branching
        sa.Column('branch', sa.String(length=255), nullable=False, server_default='main'),
        sa.Column('is_fork', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('forked_from_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Embedding for search (1536-dim for OpenAI text-embedding-3-small) - Phase 2
        # sa.Column('embedding', postgresql.VECTOR(1536), nullable=True),

        # Full-text search
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        
        # Audit
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_version_id'], ['nodes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['forked_from_id'], ['nodes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'id', 'version', name='unique_node_version')
    )
    
    # Generate search_vector column
    op.execute("""
        CREATE OR REPLACE FUNCTION update_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector := 
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B');
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_nodes_search_vector
        BEFORE INSERT OR UPDATE ON nodes
        FOR EACH ROW EXECUTE FUNCTION update_search_vector();
    """)
    
    # ============================================
    # CREATE EDGES (Research Graph Edges)
    # ============================================
    op.create_table('edges',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('edge_type', sa.Enum('derives_from', 'tests', 'supports', 'contradicts', 'references', 'uses', 'generates', 'contains', 'belongs_to', 'authored_by', 'cites', 'based_on', 'extends', 'replaces', 'version_of', 'fork_of', 'merged_from', name='edge_type'), nullable=False),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        
        # Version
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        
        # Audit
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'source_id', 'target_id', 'edge_type', 'version', name='unique_edge')
    )
    
    # ============================================
    # CREATE EXPERIMENTS
    # ============================================
    op.create_table('experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hypothesis_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('created', 'running', 'paused', 'completed', 'failed', 'cancelled', name='experiment_status'), nullable=False, server_default='created'),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), server_default='{}', nullable=True),
        
        # Graph node reference
        sa.Column('node_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Audit
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['hypothesis_id'], ['nodes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ============================================
    # CREATE RUNS
    # ============================================
    op.create_table('runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('created', 'running', 'paused', 'completed', 'failed', 'cancelled', name='experiment_status'), nullable=False, server_default='created'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.BigInteger(), nullable=True),
        
        # Git context
        sa.Column('git_commit', sa.String(length=40), nullable=True),
        sa.Column('git_branch', sa.String(length=255), nullable=True),
        sa.Column('git_dirty', sa.Boolean(), server_default='false', nullable=True),
        
        # Parameters (snapshot at run time)
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        
        # Graph node reference
        sa.Column('node_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Audit
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('experiment_id', 'run_number', name='unique_run_number')
    )
    
    # ============================================
    # CREATE METRICS TABLE (Will be partitioned)
    # ============================================
    op.create_table('metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ============================================
    # CREATE PARAMETERS
    # ============================================
    op.create_table('parameters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('value_type', sa.String(length=50), nullable=False),
        
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id', 'key', name='unique_parameter')
    )
    
    # ============================================
    # CREATE INDEXES
    # ============================================
    
    # Organizations
    op.create_index('idx_organizations_slug', 'organizations', ['slug'])
    
    # Users
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Projects
    op.create_index('idx_projects_organization', 'projects', ['organization_id'])
    
    # Nodes
    op.create_index('idx_nodes_organization', 'nodes', ['organization_id'])
    op.create_index('idx_nodes_type', 'nodes', ['organization_id', 'node_type'])
    op.create_index('idx_nodes_branch', 'nodes', ['organization_id', 'branch'])
    op.create_index('idx_nodes_parent_version', 'nodes', ['parent_version_id'])
    op.create_index('idx_nodes_search', 'nodes', ['search_vector'], postgresql_using='gin')
    
    # Create HNSW index for vector similarity search - Phase 2 feature
    # op.execute("""
    #     CREATE INDEX idx_nodes_embedding ON nodes 
    #     USING hnsw (embedding vector_cosine_ops)
    #     WITH (m = 16, ef_construction = 64)
    # """)
    
    # Create trigram index for fuzzy search
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS pg_trgm
    """)
    
    op.execute("""
        CREATE INDEX idx_nodes_title_trgm ON nodes 
        USING gin (title gin_trgm_ops)
    """)
    
    # Edges
    op.create_index('idx_edges_organization', 'edges', ['organization_id'])
    op.create_index('idx_edges_source', 'edges', ['source_id'])
    op.create_index('idx_edges_target', 'edges', ['target_id'])
    op.create_index('idx_edges_type', 'edges', ['edge_type'])
    op.create_index('idx_edges_source_type', 'edges', ['source_id', 'edge_type'])
    op.create_index('idx_edges_target_type', 'edges', ['target_id', 'edge_type'])
    
    # Experiments
    op.create_index('idx_experiments_organization', 'experiments', ['organization_id'])
    op.create_index('idx_experiments_project', 'experiments', ['project_id'])
    op.create_index('idx_experiments_status', 'experiments', ['status'])
    op.create_index('idx_experiments_tags', 'experiments', ['tags'], postgresql_using='gin')
    
    # Runs
    op.create_index('idx_runs_experiment', 'runs', ['experiment_id'])
    op.create_index('idx_runs_status', 'runs', ['status'])
    op.create_index('idx_runs_time', 'runs', ['started_at'])
    
    # Metrics (will be partitioned, indexes inherited)
    op.create_index('idx_metrics_run_key', 'metrics', ['run_id', 'key', 'step'])
    op.create_index('idx_metrics_run_time', 'metrics', ['run_id', 'timestamp'])
    op.create_index('idx_metrics_key_value', 'metrics', ['organization_id', 'key', 'value'])
    
    # Parameters
    op.create_index('idx_parameters_run', 'parameters', ['run_id'])
    
    # ============================================
    # CONFIGURE METRICS PARTITIONING WITH PG_PARTMAN
    # ============================================
    op.execute("""
        -- Convert metrics table to partitioned table by timestamp
        ALTER TABLE metrics 
        DROP CONSTRAINT metrics_pkey,
        ADD PRIMARY KEY (id, timestamp);
        
        -- Create partition by month
        SELECT partman.create_parent(
            p_parent_table := 'public.metrics',
            p_control := 'timestamp',
            p_type := 'native',
            p_interval := '1 month',
            p_premake := 3
        );
        
        -- Configure partition retention (12 months)
        UPDATE partman.part_config 
        SET retention = '12 months',
            retention_keep_table = false
        WHERE parent_table = 'public.metrics';
    """)
    
    # ============================================
    # CREATE AUTOMATIC TIMESTAMP UPDATES
    # ============================================
    op.execute("""
        CREATE OR REPLACE FUNCTION update_modified_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply to tables with updated_at
    op.execute("""
        CREATE TRIGGER update_organizations_modtime
        BEFORE UPDATE ON organizations
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_users_modtime
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_projects_modtime
        BEFORE UPDATE ON projects
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_nodes_modtime
        BEFORE UPDATE ON nodes
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_experiments_modtime
        BEFORE UPDATE ON experiments
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    """)
    
    # ============================================
    # ENABLE ROW-LEVEL SECURITY
    # ============================================
    op.execute("""
        ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
        ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
        ALTER TABLE nodes ENABLE ROW LEVEL SECURITY;
        ALTER TABLE edges ENABLE ROW LEVEL SECURITY;
        ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
        ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
        ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;
        ALTER TABLE parameters ENABLE ROW LEVEL SECURITY;
    """)
    
    # ============================================
    # CREATE RLS POLICIES
    # ============================================
    
    # Helper function to get current user ID (simplified)
    op.execute("""
        CREATE OR REPLACE FUNCTION current_user_id()
        RETURNS UUID
        LANGUAGE sql
        SECURITY DEFINER
        STABLE
        AS $$
            -- Simplified for now - will be replaced with actual auth
            SELECT '00000000-0000-0000-0000-000000000000'::UUID;
        $$;
    """)
    
    # Example RLS policy for organizations
    op.execute("""
        CREATE POLICY organization_isolation ON organizations
        FOR ALL USING (
            id IN (
                SELECT organization_id 
                FROM organization_members 
                WHERE user_id = current_user_id()
            )
        );
    """)
    
    # Similar policies should be created for all tables
    # For simplicity in initial implementation, we'll set up basic policies
    
    op.execute("""
        CREATE POLICY project_isolation ON projects
        FOR ALL USING (
            organization_id IN (
                SELECT organization_id 
                FROM organization_members 
                WHERE user_id = current_user_id()
            )
        );
    """)
    
    op.execute("""
        CREATE POLICY node_isolation ON nodes
        FOR ALL USING (
            organization_id IN (
                SELECT organization_id 
                FROM organization_members 
                WHERE user_id = current_user_id()
            )
        );
    """)
    
    op.execute("""
        CREATE POLICY edge_isolation ON edges
        FOR ALL USING (
            organization_id IN (
                SELECT organization_id 
                FROM organization_members 
                WHERE user_id = current_user_id()
            )
        );
    """)
    
    op.execute("""
        CREATE POLICY experiment_isolation ON experiments
        FOR ALL USING (
            organization_id IN (
                SELECT organization_id 
                FROM organization_members 
                WHERE user_id = current_user_id()
            )
        );
    """)
    
    # ============================================
    # CREATE SAMPLE DATA FOR TESTING
    # ============================================
    op.execute("""
        -- Insert a test organization
        INSERT INTO organizations (id, name, slug) 
        VALUES (
            '00000000-0000-0000-0000-000000000001'::UUID,
            'Test Organization',
            'test-org'
        );
        
        -- Insert a test user
        INSERT INTO users (id, email, name, auth_provider) 
        VALUES (
            '00000000-0000-0000-0000-000000000001'::UUID,
            'test@example.com',
            'Test User',
            'email'
        );
        
        -- Add user to organization
        INSERT INTO organization_members (organization_id, user_id, role) 
        VALUES (
            '00000000-0000-0000-0000-000000000001'::UUID,
            '00000000-0000-0000-0000-000000000001'::UUID,
            'owner'
        );
        
        -- Create a test project
        INSERT INTO projects (id, organization_id, name, created_by)
        VALUES (
            '00000000-0000-0000-0000-000000000001'::UUID,
            '00000000-0000-0000-0000-000000000001'::UUID,
            'Test Project',
            '00000000-0000-0000-0000-000000000001'::UUID
        );
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS organization_isolation ON organizations")
    op.execute("DROP POLICY IF EXISTS project_isolation ON projects")
    op.execute("DROP POLICY IF EXISTS node_isolation ON nodes")
    op.execute("DROP POLICY IF EXISTS edge_isolation ON edges")
    op.execute("DROP POLICY IF EXISTS experiment_isolation ON experiments")
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_nodes_search_vector ON nodes")
    op.execute("DROP TRIGGER IF EXISTS update_organizations_modtime ON organizations")
    op.execute("DROP TRIGGER IF EXISTS update_users_modtime ON users")
    op.execute("DROP TRIGGER IF EXISTS update_projects_modtime ON projects")
    op.execute("DROP TRIGGER IF EXISTS update_nodes_modtime ON nodes")
    op.execute("DROP TRIGGER IF EXISTS update_experiments_modtime ON experiments")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS update_modified_column()")
    op.execute("DROP FUNCTION IF EXISTS current_user_id()")
    
    # Drop tables
    op.drop_table('parameters')
    op.drop_table('metrics')
    op.drop_table('runs')
    op.drop_table('experiments')
    op.drop_table('edges')
    op.drop_table('nodes')
    op.drop_table('organization_members')
    op.drop_table('projects')
    op.drop_table('users')
    op.drop_table('organizations')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS artifact_type")
    op.execute("DROP TYPE IF EXISTS experiment_status")
    op.execute("DROP TYPE IF EXISTS edge_type")
    op.execute("DROP TYPE IF EXISTS node_type")
    
    # Drop extensions
    op.execute("DROP EXTENSION IF EXISTS pg_partman")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS pgvector")