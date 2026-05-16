"""merge migration heads

Revision ID: 24928d013e22
Revises: 7b9f7f8c1f5d, c6146a5ee162
Create Date: 2026-05-16 00:16:41.440204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24928d013e22'
down_revision: Union[str, Sequence[str], None] = ('7b9f7f8c1f5d', 'c6146a5ee162')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
