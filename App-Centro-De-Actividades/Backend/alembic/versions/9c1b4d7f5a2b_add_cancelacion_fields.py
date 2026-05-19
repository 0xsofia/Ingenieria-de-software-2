"""add cancelada_en and descuento bloqueado

Revision ID: 9c1b4d7f5a2b
Revises: 8b7d0a2f2b1a
Create Date: 2026-05-18 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c1b4d7f5a2b"
down_revision: Union[str, Sequence[str], None] = "8b7d0a2f2b1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reserva", sa.Column("cancelada_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("socio", sa.Column("descuento_bloqueado_hasta", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("socio", "descuento_bloqueado_hasta")
    op.drop_column("reserva", "cancelada_en")
