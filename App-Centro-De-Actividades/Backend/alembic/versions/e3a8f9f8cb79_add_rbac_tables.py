"""add rbac tables

Revision ID: e3a8f9f8cb79
Revises: 6c1c4b98918d
Create Date: 2026-05-10 18:05:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e3a8f9f8cb79"
down_revision: Union[str, Sequence[str], None] = "6c1c4b98918d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rol",
        sa.Column("rol_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("rol_id"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_index(op.f("ix_rol_nombre"), "rol", ["nombre"], unique=False)

    op.create_table(
        "permiso",
        sa.Column("permiso_id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("permiso_id"),
        sa.UniqueConstraint("codigo"),
    )
    op.create_index(op.f("ix_permiso_codigo"), "permiso", ["codigo"], unique=False)

    op.create_table(
        "persona_rol_puente",
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.Column("rol_id", sa.Integer(), nullable=False),
        sa.Column(
            "asignado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["persona_id"], ["persona.persona_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rol_id"], ["rol.rol_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("persona_id", "rol_id"),
    )

    op.create_table(
        "rol_permiso_puente",
        sa.Column("rol_id", sa.Integer(), nullable=False),
        sa.Column("permiso_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permiso_id"], ["permiso.permiso_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rol_id"], ["rol.rol_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("rol_id", "permiso_id"),
    )


def downgrade() -> None:
    op.drop_table("rol_permiso_puente")
    op.drop_table("persona_rol_puente")
    op.drop_index(op.f("ix_permiso_codigo"), table_name="permiso")
    op.drop_table("permiso")
    op.drop_index(op.f("ix_rol_nombre"), table_name="rol")
    op.drop_table("rol")
