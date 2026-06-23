"""merge migration heads

Revision ID: 73405aaeef6c
Revises: 32ce44659eaf, e2a3d9a942fb
Create Date: 2026-06-21 12:38:36.927652

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73405aaeef6c'
down_revision: Union[str, Sequence[str], None] = ('32ce44659eaf', 'e2a3d9a942fb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
