"""add unique active reservation index

Revision ID: 8b7d0a2f2b1a
Revises: 4f2c1a9e8d70
Create Date: 2026-05-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b7d0a2f2b1a"
down_revision: Union[str, Sequence[str], None] = "4f2c1a9e8d70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEX_NAME = "uq_reserva_clase_socio_activa"


def upgrade() -> None:
    # Prevent a socio from reserving the same clase more than once
    # while the reservation is still active (i.e. it occupies a spot).
    op.create_index(
        INDEX_NAME,
        "reserva",
        ["clase_id", "socio_id"],
        unique=True,
        postgresql_where=sa.text("estado IN ('pendiente_pago', 'confirmada')"),
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="reserva")
