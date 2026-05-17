"""merge migration heads

Revision ID: 50cd64e1a3eb
Revises: 4f6dd9f39e9b, 5b8d7f6c1a4a
Create Date: 2026-05-17 17:10:11.806817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50cd64e1a3eb'
down_revision: Union[str, Sequence[str], None] = ('4f6dd9f39e9b', '5b8d7f6c1a4a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
