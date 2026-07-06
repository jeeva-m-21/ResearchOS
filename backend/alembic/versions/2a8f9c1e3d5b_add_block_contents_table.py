"""add block_contents table

Revision ID: 2a8f9c1e3d5b
Revises: 06776428afc7
Create Date: 2026-07-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '2a8f9c1e3d5b'
down_revision = '06776428afc7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'block_contents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('block_id', UUID(as_uuid=True), sa.ForeignKey('blocks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('language', sa.String(50), nullable=True),
        sa.Column('metadata', sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('block_id', 'version', name='uq_block_contents_block_id_version'),
    )
    op.create_index(op.f('ix_block_contents_block_id'), 'block_contents', ['block_id'])


def downgrade() -> None:
    op.drop_table('block_contents')
