"""add_papers_tables

Revision ID: b3bfeb7339c4
Revises: 61f55875cb77
Create Date: 2026-07-07 03:45:09.089737

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b3bfeb7339c4'
down_revision = '61f55875cb77'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create paper_status enum idempotently
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paper_status AS ENUM (
                'draft',
                'in_review',
                'published',
                'archived'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Papers table
    op.create_table('papers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('authors', postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('doi', sa.String(length=255), nullable=True),
        sa.Column('arxiv_id', sa.String(length=50), nullable=True),
        sa.Column('tags', postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_papers_organization', 'papers', ['organization_id'])
    op.create_index('idx_papers_project', 'papers', ['project_id'])
    op.create_index('idx_papers_status', 'papers', ['status'])

    # Citations table
    op.create_table('citations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('citation_key', sa.String(length=255), nullable=False),
        sa.Column('cited_paper_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cited_doi', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('authors', postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('venue', sa.String(length=255), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('citation_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cited_paper_id'], ['papers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('paper_id', 'citation_key')
    )
    op.create_index('idx_citations_paper', 'citations', ['paper_id'])
    op.create_index('idx_citations_organization', 'citations', ['organization_id'])

    # References table (inline citation usage)
    op.create_table('references',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('citation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['citation_id'], ['citations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['blocks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_references_paper', 'references', ['paper_id'])
    op.create_index('idx_references_citation', 'references', ['citation_id'])


def downgrade() -> None:
    op.drop_index('idx_references_citation', table_name='references')
    op.drop_index('idx_references_paper', table_name='references')
    op.drop_table('references')
    op.drop_index('idx_citations_organization', table_name='citations')
    op.drop_index('idx_citations_paper', table_name='citations')
    op.drop_table('citations')
    op.drop_index('idx_papers_status', table_name='papers')
    op.drop_index('idx_papers_project', table_name='papers')
    op.drop_index('idx_papers_organization', table_name='papers')
    op.drop_table('papers')
    op.execute("DROP TYPE IF EXISTS paper_status")
