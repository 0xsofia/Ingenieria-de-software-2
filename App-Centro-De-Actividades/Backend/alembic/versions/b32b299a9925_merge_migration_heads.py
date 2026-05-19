"""merge migration heads

Revision ID: b32b299a9925
Revises: 380d8bba8e5d, 9c1b4d7f5a2b
Create Date: 2026-05-18 18:41:36.023555

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b32b299a9925'
down_revision: Union[str, Sequence[str], None] = ('380d8bba8e5d', '9c1b4d7f5a2b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
