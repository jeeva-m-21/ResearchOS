"""create_nodes_table_for_search

Revision ID: 4ad09203efc6
Revises: 15bd475b2311
Create Date: 2026-07-04 15:43:18.540361

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "4ad09203efc6"
down_revision = "15bd475b2311"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create nodes table for hybrid search
    op.create_table(
        "nodes",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("organization_id", postgresql.UUID(), nullable=False),
        sa.Column(
            "node_type",
            postgresql.ENUM("node_type", name="node_type", create_type=False),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("properties", postgresql.JSONB(), server_default="{}"),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_by", postgresql.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
    )

    # Basic indexes
    op.create_index("idx_nodes_organization", "nodes", ["organization_id"])
    op.create_index("idx_nodes_type", "nodes", ["organization_id", "node_type"])

    # GIN index for full-text search
    op.create_index(
        "idx_nodes_search", "nodes", ["search_vector"], postgresql_using="gin"
    )

    # HNSW index for vector similarity search (pgvector)
    op.execute(
        "CREATE INDEX idx_nodes_embedding ON nodes "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    # Trigram index for fuzzy title matching
    op.execute(
        "CREATE INDEX idx_nodes_title_trgm ON nodes "
        "USING gin (title gin_trgm_ops)"
    )

    # Function and trigger for automatic search_vector updates
    op.execute("""
        CREATE OR REPLACE FUNCTION update_nodes_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER trigger_nodes_search_vector
        BEFORE INSERT OR UPDATE ON nodes
        FOR EACH ROW EXECUTE FUNCTION update_nodes_search_vector()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trigger_nodes_search_vector ON nodes")
    op.execute("DROP FUNCTION IF EXISTS update_nodes_search_vector()")
    op.execute("DROP INDEX IF EXISTS idx_nodes_embedding")
    op.execute("DROP INDEX IF EXISTS idx_nodes_title_trgm")
    op.execute("DROP INDEX IF EXISTS idx_nodes_search")
    op.execute("DROP INDEX IF EXISTS idx_nodes_type")
    op.execute("DROP INDEX IF EXISTS idx_nodes_organization")
    op.drop_table("nodes")
