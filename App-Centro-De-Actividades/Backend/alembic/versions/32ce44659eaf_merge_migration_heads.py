"""merge migration heads

Revision ID: 32ce44659eaf
Revises: 097404523ad4, 9711b175d365
Create Date: 2026-06-20 11:22:03.701230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32ce44659eaf'
down_revision: Union[str, Sequence[str], None] = ('097404523ad4', '9711b175d365')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
