"""merge migration heads

Revision ID: 9711b175d365
Revises: 588fff512ca9, 839a70a1bb65
Create Date: 2026-06-19 09:05:38.732060

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9711b175d365'
down_revision: Union[str, Sequence[str], None] = ('588fff512ca9', '839a70a1bb65')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
