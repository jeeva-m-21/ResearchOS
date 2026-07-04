"""Add authentication tables and updates

Revision ID: 002_authentication
Revises: 001_initial_schema
Create Date: 2024-01-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_authentication'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # ADD PASSWORD COLUMN TO USERS TABLE
    # ============================================
    op.add_column('users', 
        sa.Column('password_hash', sa.String(length=255), nullable=True)
    )
    
    # Update existing test user with a password
    op.execute("""
        UPDATE users 
        SET password_hash = crypt('test1234', gen_salt('bf'))
        WHERE email = 'test@example.com'
    """)
    
    # ============================================
    # CREATE API KEYS TABLE
    # ============================================
    op.create_table('api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_api_keys_organization', 'api_keys', ['organization_id'])
    op.create_index('idx_api_keys_user', 'api_keys', ['user_id'])
    
    # ============================================
    # CREATE REFRESH TOKENS TABLE
    # ============================================
    op.create_table('refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    
    op.create_index('idx_refresh_tokens_user', 'refresh_tokens', ['user_id'])
    
    # ============================================
    # ENABLE CRYPT EXTENSION FOR PASSWORD HASHING
    # ============================================
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    
    # ============================================
    # UPDATE RLS CURRENT_USER_ID FUNCTION
    # ============================================
    op.execute("""
        CREATE OR REPLACE FUNCTION current_user_id()
        RETURNS UUID
        LANGUAGE sql
        SECURITY DEFINER
        STABLE
        AS $$
            -- This will be set by the application middleware
            -- For now, return a placeholder
            SELECT NULL::UUID;
        $$;
    """)
    
    # ============================================
    # ADD RLS POLICIES FOR NEW TABLES
    # ============================================
    op.execute("ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY")
    
    op.execute("""
        CREATE POLICY api_keys_isolation ON api_keys
        FOR ALL USING (
            organization_id IN (
                SELECT organization_id 
                FROM organization_members 
                WHERE user_id = current_user_id()
            )
        );
    """)
    
    op.execute("""
        CREATE POLICY refresh_tokens_isolation ON refresh_tokens
        FOR ALL USING (user_id = current_user_id());
    """)
    
    # ============================================
    # CREATE TRIGGERS FOR NEW TABLES
    # ============================================
    op.execute("""
        CREATE TRIGGER update_api_keys_modtime
        BEFORE UPDATE ON api_keys
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    """)
    
    # ============================================
    # CREATE TEST API KEY
    # ============================================
    op.execute("""
        INSERT INTO api_keys (
            id, organization_id, user_id, name, key_hash
        ) VALUES (
            '00000000-0000-0000-0000-000000000002'::UUID,
            '00000000-0000-0000-0000-000000000001'::UUID,
            '00000000-0000-0000-0000-000000000001'::UUID,
            'Test API Key',
            crypt('test_api_key_12345', gen_salt('bf'))
        );
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_api_keys_modtime ON api_keys")
    
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS api_keys_isolation ON api_keys")
    op.execute("DROP POLICY IF EXISTS refresh_tokens_isolation ON refresh_tokens")
    
    # Disable RLS
    op.execute("ALTER TABLE api_keys DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE refresh_tokens DISABLE ROW LEVEL SECURITY")
    
    # Drop tables
    op.drop_table('refresh_tokens')
    op.drop_table('api_keys')
    
    # Drop column
    op.drop_column('users', 'password_hash')