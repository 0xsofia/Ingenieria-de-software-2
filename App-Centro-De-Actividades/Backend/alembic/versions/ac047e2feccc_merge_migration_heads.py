"""merge migration heads

Revision ID: ac047e2feccc
Revises: 37f585e3fa47, 73405aaeef6c
Create Date: 2026-06-22 11:40:17.367415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac047e2feccc'
down_revision: Union[str, Sequence[str], None] = ('37f585e3fa47', '73405aaeef6c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
