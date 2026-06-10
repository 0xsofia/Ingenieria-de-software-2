"""merge migration heads

Revision ID: fe28e5f18be4
Revises: 3101e9c2b5f4, 9eef1ad4feda
Create Date: 2026-06-10 18:54:42.793993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe28e5f18be4'
down_revision: Union[str, Sequence[str], None] = ('3101e9c2b5f4', '9eef1ad4feda')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
