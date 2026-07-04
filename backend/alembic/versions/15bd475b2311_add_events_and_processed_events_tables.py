"""Add events and processed_events tables

Revision ID: 15bd475b2311
Revises: 002_authentication
Create Date: 2026-07-04 15:30:23.776867

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '15bd475b2311'
down_revision = '002_authentication'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # CREATE EVENTS TABLE (append-only event store)
    # ============================================
    op.create_table('events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=255), nullable=False),
        sa.Column('aggregate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aggregate_type', sa.String(length=50), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),

        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )

    op.create_index('idx_events_organization', 'events', ['organization_id'])
    op.create_index('idx_events_event_type', 'events', ['event_type'])
    op.create_index('idx_events_aggregate', 'events', ['aggregate_id', 'aggregate_type'])
    op.create_index('idx_events_created_at', 'events', [sa.text('created_at DESC')])
    op.create_index('idx_events_event_id', 'events', ['event_id'], unique=True)

    # ============================================
    # CREATE PROCESSED EVENTS TABLE (idempotency)
    # ============================================
    op.create_table('processed_events',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('consumer_group', sa.String(length=255), nullable=False),
        sa.Column('processed_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),

        sa.PrimaryKeyConstraint('event_id', 'consumer_group')
    )

    op.create_index('idx_processed_events_time', 'processed_events', [sa.text('processed_at DESC')])


def downgrade() -> None:
    op.drop_table('processed_events')
    op.drop_table('events')
