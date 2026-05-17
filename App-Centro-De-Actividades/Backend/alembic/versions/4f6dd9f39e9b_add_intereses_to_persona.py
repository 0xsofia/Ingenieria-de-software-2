"""add intereses column to persona

Revision ID: 4f6dd9f39e9b
Revises: 24928d013e22
Create Date: 2026-05-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f6dd9f39e9b'
down_revision = '24928d013e22'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'persona',
        sa.Column('intereses', sa.String(length=255), nullable=False, server_default=''),
    )


def downgrade() -> None:
    op.drop_column('persona', 'intereses')
