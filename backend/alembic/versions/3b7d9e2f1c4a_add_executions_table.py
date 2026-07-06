"""add executions table

Revision ID: 3b7d9e2f1c4a
Revises: 2a8f9c1e3d5b
Create Date: 2026-07-06 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '3b7d9e2f1c4a'
down_revision = '2a8f9c1e3d5b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'executions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('block_content_id', UUID(as_uuid=True), sa.ForeignKey('block_contents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('block_id', UUID(as_uuid=True), sa.ForeignKey('blocks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('notebook_id', UUID(as_uuid=True), sa.ForeignKey('notebooks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('ended_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
    )
    op.create_index(op.f('ix_executions_block_id'), 'executions', ['block_id'])
    op.create_index(op.f('ix_executions_notebook_id'), 'executions', ['notebook_id'])
    op.create_index(op.f('ix_executions_organization_id'), 'executions', ['organization_id'])
    op.create_index(op.f('ix_executions_status'), 'executions', ['status'])


def downgrade() -> None:
    op.drop_table('executions')
