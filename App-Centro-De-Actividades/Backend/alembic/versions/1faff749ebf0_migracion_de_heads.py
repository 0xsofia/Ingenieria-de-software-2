"""migracion de heads

Revision ID: 1faff749ebf0
Revises: c676bb98c307, fe28e5f18be4
Create Date: 2026-06-15 17:39:37.837960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1faff749ebf0'
down_revision: Union[str, Sequence[str], None] = ('c676bb98c307', 'fe28e5f18be4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
