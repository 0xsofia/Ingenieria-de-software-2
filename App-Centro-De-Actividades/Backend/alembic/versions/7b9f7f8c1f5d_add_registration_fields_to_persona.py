"""add registration fields to persona

Revision ID: 7b9f7f8c1f5d
Revises: e3a8f9f8cb79
Create Date: 2026-05-12 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b9f7f8c1f5d"
down_revision: Union[str, Sequence[str], None] = "e3a8f9f8cb79"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("persona", sa.Column("dni", sa.String(length=32), nullable=True))
    op.add_column("persona", sa.Column("telefono", sa.String(length=32), nullable=True))
    op.add_column("persona", sa.Column("calle", sa.String(length=120), nullable=True))
    op.add_column(
        "persona", sa.Column("numero_puerta", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "persona", sa.Column("codigo_postal", sa.String(length=20), nullable=True)
    )

    op.execute(
        """
        UPDATE persona
        SET dni = LPAD(persona_id::text, 8, '0')
        WHERE dni IS NULL
        """
    )
    op.execute(
        """
        UPDATE persona
        SET telefono = CONCAT('01115', LPAD(persona_id::text, 8, '0')),
            calle = CONCAT('Calle ', persona_id),
            numero_puerta = persona_id::text,
            codigo_postal = '1900'
        WHERE telefono IS NULL
           OR calle IS NULL
           OR numero_puerta IS NULL
           OR codigo_postal IS NULL
        """
    )

    op.alter_column("persona", "dni", existing_type=sa.String(length=32), nullable=False)
    op.alter_column(
        "persona", "telefono", existing_type=sa.String(length=32), nullable=False
    )
    op.alter_column("persona", "calle", existing_type=sa.String(length=120), nullable=False)
    op.alter_column(
        "persona", "numero_puerta", existing_type=sa.String(length=20), nullable=False
    )
    op.alter_column(
        "persona", "codigo_postal", existing_type=sa.String(length=20), nullable=False
    )

    op.create_unique_constraint("uq_persona_dni", "persona", ["dni"])
    op.create_index(op.f("ix_persona_dni"), "persona", ["dni"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_persona_dni"), table_name="persona")
    op.drop_constraint("uq_persona_dni", "persona", type_="unique")
    op.drop_column("persona", "codigo_postal")
    op.drop_column("persona", "numero_puerta")
    op.drop_column("persona", "calle")
    op.drop_column("persona", "telefono")
    op.drop_column("persona", "dni")
