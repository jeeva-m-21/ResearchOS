"""add_notebooks_blocks_tables

Revision ID: 06776428afc7
Revises: 4ad09203efc6
Create Date: 2026-07-04 16:38:36.019962

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '06776428afc7'
down_revision = '4ad09203efc6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'notebooks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('branch', sa.String(255), nullable=False, server_default='main'),
        sa.Column('parent_commit', sa.String(40), nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_notebooks_organization_id'), 'notebooks', ['organization_id'])
    op.create_index(op.f('ix_notebooks_project_id'), 'notebooks', ['project_id'])

    op.create_table(
        'blocks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('notebook_id', UUID(as_uuid=True), sa.ForeignKey('notebooks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('block_type', sa.String(50), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('current_version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint('notebook_id', 'position', name='uq_blocks_notebook_id_position'),
    )
    op.create_index(op.f('ix_blocks_notebook_id'), 'blocks', ['notebook_id'])


def downgrade() -> None:
    op.drop_table('blocks')
    op.drop_table('notebooks')
