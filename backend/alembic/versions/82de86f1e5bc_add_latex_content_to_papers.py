"""add_latex_content_to_papers

Revision ID: 82de86f1e5bc
Revises: b3bfeb7339c4
Create Date: 2026-07-07 09:06:33.963011

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82de86f1e5bc'
down_revision: Union[str, None] = 'b3bfeb7339c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('papers', sa.Column('latex_content', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('papers', 'latex_content')
