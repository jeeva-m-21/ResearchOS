"""add_connection_configs_table

Revision ID: 61f55875cb77
Revises: 3a6b83a39681
Create Date: 2026-07-06 16:49:21.018530

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '61f55875cb77'
down_revision = '3a6b83a39681'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('connection_configs',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('config', JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_connection_configs_org', 'connection_configs', ['organization_id'])
    op.create_index('idx_connection_configs_provider', 'connection_configs', ['provider'])


def downgrade() -> None:
    op.drop_index('idx_connection_configs_provider')
    op.drop_index('idx_connection_configs_org')
    op.drop_table('connection_configs')
