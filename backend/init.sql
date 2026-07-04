-- Initialize ResearchOS database with test data
-- This file runs when PostgreSQL container starts

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Create test user
INSERT INTO users (id, email, name, created_at, updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'test@example.com',
    'Test User',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;

-- 2. Create test organization
INSERT INTO organizations (id, name, slug, plan, created_at, updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Test Organization',
    'test-org',
    'free',
    NOW(),
    NOW()
)
ON CONFLICT (slug) DO NOTHING;

-- 3. Add user to organization as admin
INSERT INTO organization_members (organization_id, user_id, role, joined_at)
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    'admin',
    NOW()
)
ON CONFLICT (organization_id, user_id) DO NOTHING;

-- 4. Create test project
INSERT INTO projects (id, organization_id, name, description, created_by, created_at, updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Test Project',
    'Initial test project',
    '00000000-0000-0000-0000-000000000001'::UUID,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- 5. Create test experiment
INSERT INTO experiments (id, organization_id, project_id, name, description, status, created_by, updated_by, created_at, updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Test Experiment',
    'Initial test experiment',
    'created',
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- 6. Create test run
INSERT INTO runs (id, experiment_id, organization_id, run_number, status, created_by, created_at)
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    1,
    'completed',
    '00000000-0000-0000-0000-000000000001'::UUID,
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Set password for test user after migration runs
-- The migration will hash the password using pgcrypto
-- test1234 is the default password