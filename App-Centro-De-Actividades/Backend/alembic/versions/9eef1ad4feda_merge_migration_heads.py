"""merge migration heads

Revision ID: 9eef1ad4feda
Revises: e47c81f0639c, efe2e3c7d9d8
Create Date: 2026-06-10 11:58:02.651436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9eef1ad4feda'
down_revision: Union[str, Sequence[str], None] = ('e47c81f0639c', 'efe2e3c7d9d8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
