"""add is_eliminated to profesor

Revision ID: 3101e9c2b5f4
Revises: 24928d013e22
Create Date: 2026-06-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3101e9c2b5f4'
down_revision = '24928d013e22'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'profesor',
        sa.Column('is_eliminated', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('profesor', 'is_eliminated')
