"""create auth tables for login

Revision ID: 6c1c4b98918d
Revises: bd5d9591d758
Create Date: 2026-05-10 16:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6c1c4b98918d"
down_revision: Union[str, Sequence[str], None] = "bd5d9591d758"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "persona",
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("apellido", sa.String(length=120), nullable=False),
        sa.Column("estado", sa.String(length=50), server_default="activo", nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("persona_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_persona_email"), "persona", ["email"], unique=False)

    op.create_table(
        "empleado",
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["persona_id"], ["persona.persona_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("persona_id"),
    )

    op.create_table(
        "socio",
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["persona_id"], ["persona.persona_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("persona_id"),
    )


def downgrade() -> None:
    op.drop_table("socio")
    op.drop_table("empleado")
    op.drop_index(op.f("ix_persona_email"), table_name="persona")
    op.drop_table("persona")
