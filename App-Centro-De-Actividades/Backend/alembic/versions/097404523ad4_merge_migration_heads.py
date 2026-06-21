"""merge migration heads

Revision ID: 097404523ad4
Revises: 588fff512ca9, 839a70a1bb65
Create Date: 2026-06-20 12:06:21.791006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '097404523ad4'
down_revision: Union[str, Sequence[str], None] = ('588fff512ca9', '839a70a1bb65')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
