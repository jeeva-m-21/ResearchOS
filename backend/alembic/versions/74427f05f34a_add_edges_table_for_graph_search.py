"""add_edges_table_for_graph_search

Revision ID: 74427f05f34a
Revises: 3c2b1d550efb
Create Date: 2026-07-11 13:47:37.172887

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "74427f05f34a"
down_revision = "3c2b1d550efb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create edge_type enum (safe — IF NOT EXISTS handles re-runs)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'edge_type') THEN
                CREATE TYPE edge_type AS ENUM (
                    'derives_from', 'tests', 'supports', 'contradicts',
                    'references', 'uses', 'generates', 'contains',
                    'belongs_to', 'authored_by', 'cites', 'based_on',
                    'extends', 'replaces', 'version_of', 'fork_of',
                    'merged_from'
                );
            END IF;
        END
        $$;
    """)

    # Create edges table
    op.create_table(
        "edges",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("edge_type",
                  postgresql.ENUM("edge_type", name="edge_type", create_type=False),
                  nullable=False),
        sa.Column("properties", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("weight", sa.Float(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_id"], ["nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "source_id", "target_id", "edge_type", "version",
                            name="uq_edge_org_source_target_type_version"),
    )

    # Indexes for graph traversal
    op.create_index("idx_edges_organization", "edges", ["organization_id"])
    op.create_index("idx_edges_source", "edges", ["source_id"])
    op.create_index("idx_edges_target", "edges", ["target_id"])
    op.create_index("idx_edges_type", "edges", ["edge_type"])
    op.create_index("idx_edges_source_type", "edges", ["source_id", "edge_type"])
    op.create_index("idx_edges_target_type", "edges", ["target_id", "edge_type"])

    # RLS policy for edges
    op.execute("""
        CREATE POLICY edge_isolation ON edges
            USING (organization_id IN (
                SELECT organization_id FROM organization_members
                WHERE user_id = current_setting('app.current_user_id')::uuid
            ))
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS edge_isolation ON edges")
    op.drop_table("edges")
    op.execute("DROP TYPE IF EXISTS edge_type")
