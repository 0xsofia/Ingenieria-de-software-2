"""add reservas tables

Revision ID: 4f2c1a9e8d70
Revises: e3a8f9f8cb79
Create Date: 2026-05-13 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f2c1a9e8d70"
down_revision: Union[str, Sequence[str], None] = "50cd64e1a3eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "abono_mensual",
        sa.Column("abono_mensual_id", sa.Integer(), nullable=False),
        sa.Column("socio_id", sa.Integer(), nullable=False),
        sa.Column("actividad_id", sa.Integer(), nullable=False),
        sa.Column("abono_anterior_id", sa.Integer(), nullable=True),
        sa.Column("periodo_inicio", sa.Date(), nullable=False),
        sa.Column("periodo_fin", sa.Date(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("dia_semana", sa.String(length=20), nullable=False),
        sa.Column("descuento_aplicado_pct", sa.Numeric(5, 2), server_default="0", nullable=False),
        sa.Column("prioridad_renovacion", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("fecha_limite_renovacion", sa.Date(), nullable=True),
        sa.Column("estado", sa.String(length=50), server_default="activo", nullable=False),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actividad_id"], ["actividad.actividad_id"]),
        sa.ForeignKeyConstraint(["socio_id"], ["socio.persona_id"]),
        sa.PrimaryKeyConstraint("abono_mensual_id"),
    )
    op.create_index(op.f("ix_abono_mensual_socio_id"), "abono_mensual", ["socio_id"], unique=False)
    op.create_index(op.f("ix_abono_mensual_actividad_id"), "abono_mensual", ["actividad_id"], unique=False)
    op.create_index(op.f("ix_abono_mensual_abono_anterior_id"), "abono_mensual", ["abono_anterior_id"], unique=False)

    op.create_table(
        "lista_espera",
        sa.Column("lista_espera_id", sa.Integer(), nullable=False),
        sa.Column("clase_id", sa.Integer(), nullable=False),
        sa.Column("socio_id", sa.Integer(), nullable=False),
        sa.Column("posicion", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=50), server_default="pendiente", nullable=False),
        sa.Column(
            "creada_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("notificado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vence_confirmacion_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmada_en", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["clase_id"], ["clase.clase_id"]),
        sa.ForeignKeyConstraint(["socio_id"], ["socio.persona_id"]),
        sa.PrimaryKeyConstraint("lista_espera_id"),
    )
    op.create_index(op.f("ix_lista_espera_clase_id"), "lista_espera", ["clase_id"], unique=False)
    op.create_index(op.f("ix_lista_espera_socio_id"), "lista_espera", ["socio_id"], unique=False)

    op.create_table(
        "reserva",
        sa.Column("reserva_id", sa.Integer(), nullable=False),
        sa.Column("clase_id", sa.Integer(), nullable=False),
        sa.Column("socio_id", sa.Integer(), nullable=False),
        sa.Column("abono_mensual_id", sa.Integer(), nullable=True),
        sa.Column("lista_espera_origen_id", sa.Integer(), nullable=True),
        sa.Column("tipo_reserva", sa.String(length=50), nullable=False),
        sa.Column("estado", sa.String(length=50), server_default="pendiente", nullable=False),
        sa.Column(
            "creada_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("confirmada_en", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["abono_mensual_id"], ["abono_mensual.abono_mensual_id"]),
        sa.ForeignKeyConstraint(["clase_id"], ["clase.clase_id"]),
        sa.ForeignKeyConstraint(["lista_espera_origen_id"], ["lista_espera.lista_espera_id"]),
        sa.ForeignKeyConstraint(["socio_id"], ["socio.persona_id"]),
        sa.PrimaryKeyConstraint("reserva_id"),
    )
    op.create_index(op.f("ix_reserva_clase_id"), "reserva", ["clase_id"], unique=False)
    op.create_index(op.f("ix_reserva_socio_id"), "reserva", ["socio_id"], unique=False)
    op.create_index(op.f("ix_reserva_abono_mensual_id"), "reserva", ["abono_mensual_id"], unique=False)
    op.create_index(op.f("ix_reserva_lista_espera_origen_id"), "reserva", ["lista_espera_origen_id"], unique=False)

    op.create_table(
        "pago",
        sa.Column("pago_id", sa.Integer(), nullable=False),
        sa.Column("socio_id", sa.Integer(), nullable=False),
        sa.Column("reserva_id", sa.Integer(), nullable=True),
        sa.Column("abono_mensual_id", sa.Integer(), nullable=True),
        sa.Column("proveedor", sa.String(length=50), server_default="mercadopago", nullable=False),
        sa.Column("external_ref", sa.String(length=255), nullable=True),
        sa.Column("monto_bruto", sa.Numeric(10, 2), nullable=False),
        sa.Column("descuento_pct", sa.Numeric(5, 2), server_default="0", nullable=False),
        sa.Column("monto_pagado", sa.Numeric(10, 2), nullable=True),
        sa.Column("estado", sa.String(length=50), server_default="pendiente", nullable=False),
        sa.Column("fecha_pago", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["abono_mensual_id"], ["abono_mensual.abono_mensual_id"]),
        sa.ForeignKeyConstraint(["reserva_id"], ["reserva.reserva_id"]),
        sa.ForeignKeyConstraint(["socio_id"], ["socio.persona_id"]),
        sa.PrimaryKeyConstraint("pago_id"),
    )
    op.create_index(op.f("ix_pago_socio_id"), "pago", ["socio_id"], unique=False)
    op.create_index(op.f("ix_pago_reserva_id"), "pago", ["reserva_id"], unique=False)
    op.create_index(op.f("ix_pago_abono_mensual_id"), "pago", ["abono_mensual_id"], unique=False)
    op.create_index(op.f("ix_pago_external_ref"), "pago", ["external_ref"], unique=False)

    op.create_table(
        "credito",
        sa.Column("credito_id", sa.Integer(), nullable=False),
        sa.Column("socio_id", sa.Integer(), nullable=False),
        sa.Column("cancelacion_reserva_origen_id", sa.Integer(), nullable=True),
        sa.Column("clase_cancelada_origen_id", sa.Integer(), nullable=True),
        sa.Column("reserva_que_consume_id", sa.Integer(), nullable=True),
        sa.Column(
            "otorgado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("consumido_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(length=50), server_default="disponible", nullable=False),
        sa.ForeignKeyConstraint(["reserva_que_consume_id"], ["reserva.reserva_id"]),
        sa.ForeignKeyConstraint(["socio_id"], ["socio.persona_id"]),
        sa.PrimaryKeyConstraint("credito_id"),
        sa.UniqueConstraint("reserva_que_consume_id"),
    )
    op.create_index(op.f("ix_credito_socio_id"), "credito", ["socio_id"], unique=False)
    op.create_index(op.f("ix_credito_cancelacion_reserva_origen_id"), "credito", ["cancelacion_reserva_origen_id"], unique=False)
    op.create_index(op.f("ix_credito_clase_cancelada_origen_id"), "credito", ["clase_cancelada_origen_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_credito_clase_cancelada_origen_id"), table_name="credito")
    op.drop_index(op.f("ix_credito_cancelacion_reserva_origen_id"), table_name="credito")
    op.drop_index(op.f("ix_credito_socio_id"), table_name="credito")
    op.drop_table("credito")

    op.drop_index(op.f("ix_pago_external_ref"), table_name="pago")
    op.drop_index(op.f("ix_pago_abono_mensual_id"), table_name="pago")
    op.drop_index(op.f("ix_pago_reserva_id"), table_name="pago")
    op.drop_index(op.f("ix_pago_socio_id"), table_name="pago")
    op.drop_table("pago")

    op.drop_index(op.f("ix_reserva_lista_espera_origen_id"), table_name="reserva")
    op.drop_index(op.f("ix_reserva_abono_mensual_id"), table_name="reserva")
    op.drop_index(op.f("ix_reserva_socio_id"), table_name="reserva")
    op.drop_index(op.f("ix_reserva_clase_id"), table_name="reserva")
    op.drop_table("reserva")

    op.drop_index(op.f("ix_lista_espera_socio_id"), table_name="lista_espera")
    op.drop_index(op.f("ix_lista_espera_clase_id"), table_name="lista_espera")
    op.drop_table("lista_espera")

    op.drop_index(op.f("ix_abono_mensual_abono_anterior_id"), table_name="abono_mensual")
    op.drop_index(op.f("ix_abono_mensual_actividad_id"), table_name="abono_mensual")
    op.drop_index(op.f("ix_abono_mensual_socio_id"), table_name="abono_mensual")
    op.drop_table("abono_mensual")
