"""add_rag_fields_to_responses

Revision ID: 64a3f874b15f
Revises: 6357e7414752
Create Date: 2025-05-28 17:31:48.440919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64a3f874b15f'
down_revision: Union[str, None] = '6357e7414752'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with RAG fields."""
    op.add_column('responses', sa.Column('sources', sa.JSON(), nullable=True))
    op.add_column('responses', sa.Column('excerpts', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema by removing RAG fields."""
    op.drop_column('responses', 'excerpts')
    op.drop_column('responses', 'sources')
