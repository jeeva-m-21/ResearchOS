"""add_compute_provider_to_notebooks

Revision ID: 3a6b83a39681
Revises: 27b3f6581036
Create Date: 2026-07-06 14:01:43.301315

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a6b83a39681'
down_revision = '27b3f6581036'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notebooks",
        sa.Column(
            "compute_provider",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'in_app'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("notebooks", "compute_provider")