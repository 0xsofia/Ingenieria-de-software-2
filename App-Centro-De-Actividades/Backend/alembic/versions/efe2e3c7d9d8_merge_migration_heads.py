"""merge migration heads

Revision ID: efe2e3c7d9d8
Revises: 926c4f5cbcef, f3a9b1c2d4e5
Create Date: 2026-05-25 14:33:57.160248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efe2e3c7d9d8'
down_revision: Union[str, Sequence[str], None] = ('926c4f5cbcef', 'f3a9b1c2d4e5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
