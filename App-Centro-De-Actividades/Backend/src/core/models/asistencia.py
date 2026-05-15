from datetime import datetime

from src.core.database import db


class Profesor(db.Model):
    __tablename__ = "profesor"

    profesor_id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(32), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(120), nullable=False)

    clases = db.relationship(
        "Clase",
        back_populates="profesor",
        cascade="all, delete-orphan",
    )


class Actividad(db.Model):
    __tablename__ = "actividad"

    actividad_id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False, index=True)

    clases = db.relationship(
        "Clase",
        back_populates="actividad",
        cascade="all, delete-orphan",
    )
    abonos = db.relationship(
        "AbonoMensual",
        back_populates="actividad",
        cascade="all, delete-orphan",
    )


class Nivel(db.Model):
    __tablename__ = "nivel"

    nivel_id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False, index=True)

    clases = db.relationship(
        "Clase",
        back_populates="nivel",
        cascade="all, delete-orphan",
    )


class Cancha(db.Model):
    __tablename__ = "cancha"

    cancha_id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False, index=True)

    clases = db.relationship(
        "Clase",
        back_populates="cancha",
        cascade="all, delete-orphan",
    )


class Clase(db.Model):
    __tablename__ = "clase"

    clase_id = db.Column(db.Integer, primary_key=True)
    actividad_id = db.Column(
        db.Integer,
        db.ForeignKey("actividad.actividad_id", ondelete="RESTRICT"),
        nullable=False,
    )
    nivel_id = db.Column(
        db.Integer,
        db.ForeignKey("nivel.nivel_id", ondelete="RESTRICT"),
        nullable=False,
    )
    profesor_id = db.Column(
        db.Integer,
        db.ForeignKey("profesor.profesor_id", ondelete="RESTRICT"),
        nullable=False,
    )
    cancha_id = db.Column(
        db.Integer,
        db.ForeignKey("cancha.cancha_id", ondelete="RESTRICT"),
        nullable=False,
    )
    fecha_clase = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    cupo_total = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.String(50), nullable=False, server_default="activa")
    cancelada_en = db.Column(db.DateTime(timezone=True), nullable=True)

    actividad = db.relationship("Actividad", back_populates="clases")
    nivel = db.relationship("Nivel", back_populates="clases")
    profesor = db.relationship("Profesor", back_populates="clases")
    cancha = db.relationship("Cancha", back_populates="clases")
    reservas = db.relationship(
        "Reserva",
        back_populates="clase",
        cascade="all, delete-orphan",
    )
    lista_espera = db.relationship(
        "ListaEspera",
        back_populates="clase",
        cascade="all, delete-orphan",
    )


class ListaEspera(db.Model):
    __tablename__ = "lista_espera"

    lista_espera_id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(
        db.Integer,
        db.ForeignKey("clase.clase_id", ondelete="CASCADE"),
        nullable=False,
    )
    socio_id = db.Column(
        db.Integer,
        db.ForeignKey("socio.persona_id", ondelete="CASCADE"),
        nullable=False,
    )
    posicion = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(50), nullable=False, server_default="pendiente")
    creada_en = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    notificado_en = db.Column(db.DateTime(timezone=True), nullable=True)
    vence_confirmacion_en = db.Column(db.DateTime(timezone=True), nullable=True)
    confirmada_en = db.Column(db.DateTime(timezone=True), nullable=True)

    socio = db.relationship("Socio", back_populates="listas_espera")
    clase = db.relationship("Clase", back_populates="lista_espera")


class AbonoMensual(db.Model):
    __tablename__ = "abono_mensual"

    abono_mensual_id = db.Column(db.Integer, primary_key=True)
    socio_id = db.Column(
        db.Integer,
        db.ForeignKey("socio.persona_id", ondelete="CASCADE"),
        nullable=False,
    )
    actividad_id = db.Column(
        db.Integer,
        db.ForeignKey("actividad.actividad_id", ondelete="RESTRICT"),
        nullable=False,
    )
    abono_anterior_id = db.Column(db.Integer, db.ForeignKey("abono_mensual.abono_mensual_id"), nullable=True)
    periodo_inicio = db.Column(db.Date, nullable=False)
    periodo_fin = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    dia_semana = db.Column(db.String(30), nullable=False)
    descuento_aplicado_pct = db.Column(db.Numeric(5, 2), nullable=False, server_default="0.00")
    prioridad_renovacion = db.Column(db.Boolean, nullable=False, server_default="false")
    fecha_limite_renovacion = db.Column(db.Date, nullable=True)
    estado = db.Column(db.String(50), nullable=False, server_default="activo")
    creado_en = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    socio = db.relationship("Socio")
    actividad = db.relationship("Actividad", back_populates="abonos")
    reservas = db.relationship("Reserva", back_populates="abono_mensual")


class Reserva(db.Model):
    __tablename__ = "reserva"

    reserva_id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(
        db.Integer,
        db.ForeignKey("clase.clase_id", ondelete="CASCADE"),
        nullable=False,
    )
    socio_id = db.Column(
        db.Integer,
        db.ForeignKey("socio.persona_id", ondelete="CASCADE"),
        nullable=False,
    )
    abono_mensual_id = db.Column(
        db.Integer,
        db.ForeignKey("abono_mensual.abono_mensual_id", ondelete="SET NULL"),
        nullable=True,
    )
    lista_espera_origen_id = db.Column(
        db.Integer,
        db.ForeignKey("lista_espera.lista_espera_id", ondelete="SET NULL"),
        nullable=True,
    )
    tipo_reserva = db.Column(db.String(50), nullable=False, server_default="normal")
    estado = db.Column(db.String(50), nullable=False, server_default="pendiente")
    creada_en = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    confirmada_en = db.Column(db.DateTime(timezone=True), nullable=True)

    socio = db.relationship("Socio", back_populates="reservas")
    clase = db.relationship("Clase", back_populates="reservas")
    abono_mensual = db.relationship("AbonoMensual", back_populates="reservas")
    lista_espera_origen = db.relationship("ListaEspera", foreign_keys=[lista_espera_origen_id])
    qr_asistencias = db.relationship(
        "QrAsistencia",
        back_populates="reserva",
        cascade="all, delete-orphan",
    )
    asistencia = db.relationship(
        "Asistencia",
        back_populates="reserva",
        uselist=False,
        cascade="all, delete-orphan",
    )


class QrAsistencia(db.Model):
    __tablename__ = "qr_asistencia"

    qr_asistencia_id = db.Column(db.Integer, primary_key=True)
    reserva_id = db.Column(
        db.Integer,
        db.ForeignKey("reserva.reserva_id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash = db.Column(db.String(255), unique=True, nullable=False, index=True)
    generado_en = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    expira_en = db.Column(db.DateTime(timezone=True), nullable=False)
    escaneado_en = db.Column(db.DateTime(timezone=True), nullable=True)
    estado = db.Column(db.String(50), nullable=False, server_default="activo")

    reserva = db.relationship("Reserva", back_populates="qr_asistencias")
    asistencias = db.relationship(
        "Asistencia",
        back_populates="qr_asistencia",
        cascade="all, delete-orphan",
    )


class Asistencia(db.Model):
    __tablename__ = "asistencia"

    asistencia_id = db.Column(db.Integer, primary_key=True)
    reserva_id = db.Column(
        db.Integer,
        db.ForeignKey("reserva.reserva_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    qr_asistencia_id = db.Column(
        db.Integer,
        db.ForeignKey("qr_asistencia.qr_asistencia_id", ondelete="SET NULL"),
        nullable=True,
    )
    empleado_registro_id = db.Column(
        db.Integer,
        db.ForeignKey("empleado.persona_id", ondelete="SET NULL"),
        nullable=True,
    )
    fecha_hora = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    medio_registro = db.Column(db.String(120), nullable=False)

    reserva = db.relationship("Reserva", back_populates="asistencia")
    qr_asistencia = db.relationship("QrAsistencia", back_populates="asistencias")
    empleado_registro = db.relationship("Empleado", back_populates="asistencias_registradas")
