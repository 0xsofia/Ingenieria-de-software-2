"""merge migration heads

Revision ID: 37f585e3fa47
Revises: 097404523ad4, e2a3d9a942fb
Create Date: 2026-06-20 18:33:56.991313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37f585e3fa47'
down_revision: Union[str, Sequence[str], None] = ('097404523ad4', 'e2a3d9a942fb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
