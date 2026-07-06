"""add_artifacts_tables

Revision ID: 27b3f6581036
Revises: 3b7d9e2f1c4a
Create Date: 2026-07-06 13:30:13.050870

"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "27b3f6581036"
down_revision = "3b7d9e2f1c4a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artifacts",
        sa.Column(
            "id", UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "organization_id", UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("artifact_type", sa.String(50), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("hash_sha256", sa.String(64), nullable=False),
        sa.Column(
            "current_version", sa.Integer(),
            nullable=False, server_default=sa.text("1"),
        ),
        sa.Column(
            "experiment_id", UUID(as_uuid=True),
            sa.ForeignKey("experiments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "run_id", UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "notebook_id", UUID(as_uuid=True),
            sa.ForeignKey("notebooks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by", UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        op.f("ix_artifacts_organization_id"),
        "artifacts", ["organization_id"],
    )
    op.create_index(
        op.f("ix_artifacts_experiment_id"),
        "artifacts", ["experiment_id"],
    )
    op.create_index(
        op.f("ix_artifacts_run_id"),
        "artifacts", ["run_id"],
    )
    op.create_index(
        op.f("ix_artifacts_artifact_type"),
        "artifacts", ["artifact_type"],
    )

    op.create_table(
        "artifact_versions",
        sa.Column(
            "id", UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "artifact_id", UUID(as_uuid=True),
            sa.ForeignKey("artifacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id", UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("hash_sha256", sa.String(64), nullable=False),
        sa.Column(
            "metadata_", sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column(
            "created_by", UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "artifact_id", "version",
            name="uq_artifact_version",
        ),
    )
    op.create_index(
        op.f("ix_artifact_versions_artifact_id"),
        "artifact_versions", ["artifact_id"],
    )
    op.create_index(
        op.f("ix_artifact_versions_organization_id"),
        "artifact_versions", ["organization_id"],
    )


def downgrade() -> None:
    op.drop_table("artifact_versions")
    op.drop_table("artifacts")
