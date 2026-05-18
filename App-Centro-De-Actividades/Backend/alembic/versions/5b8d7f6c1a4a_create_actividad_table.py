"""create actividad table

Revision ID: 5b8d7f6c1a4a
Revises: 24928d013e22
Create Date: 2026-05-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '5b8d7f6c1a4a'
down_revision = '24928d013e22'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'actividad',
        sa.Column('actividad_id', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(length=120), nullable=False, unique=True),
    )


def downgrade() -> None:
    op.drop_table('actividad')
