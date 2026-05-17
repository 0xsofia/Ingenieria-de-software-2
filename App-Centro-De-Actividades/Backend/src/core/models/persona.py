from src.core.database import db


class Persona(db.Model):
    __tablename__ = "persona"

    persona_id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    apellido = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(32), nullable=False)
    calle = db.Column(db.String(120), nullable=False)
    numero_puerta = db.Column(db.String(20), nullable=False)
    codigo_postal = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.String(50), nullable=False, server_default="activo")
    intereses = db.Column(db.String(255), nullable=False, server_default="")
    creado_en = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    empleado = db.relationship(
        "Empleado",
        back_populates="persona",
        uselist=False,
        cascade="all, delete-orphan",
    )
    socio = db.relationship(
        "Socio",
        back_populates="persona",
        uselist=False,
        cascade="all, delete-orphan",
    )
    persona_roles = db.relationship(
        "PersonaRolPuente",
        back_populates="persona",
        cascade="all, delete-orphan",
    )

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}".strip()

    @property
    def roles(self):
        return [assignment.rol for assignment in self.persona_roles]


class Empleado(db.Model):
    __tablename__ = "empleado"

    persona_id = db.Column(
        db.Integer,
        db.ForeignKey("persona.persona_id", ondelete="CASCADE"),
        primary_key=True,
    )

    persona = db.relationship("Persona", back_populates="empleado")


class Socio(db.Model):
    __tablename__ = "socio"

    persona_id = db.Column(
        db.Integer,
        db.ForeignKey("persona.persona_id", ondelete="CASCADE"),
        primary_key=True,
    )

    persona = db.relationship("Persona", back_populates="socio")


class Rol(db.Model):
    __tablename__ = "rol"

    rol_id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False, index=True)
    descripcion = db.Column(db.String(255), nullable=False)

    persona_assignments = db.relationship(
        "PersonaRolPuente",
        back_populates="rol",
        cascade="all, delete-orphan",
    )
    rol_permissions = db.relationship(
        "RolPermisoPuente",
        back_populates="rol",
        cascade="all, delete-orphan",
    )

    @property
    def permisos(self):
        return [assignment.permiso for assignment in self.rol_permissions]

    @property
    def permission_codes(self):
        return sorted({permiso.codigo for permiso in self.permisos})


class Permiso(db.Model):
    __tablename__ = "permiso"

    permiso_id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(120), unique=True, nullable=False, index=True)
    descripcion = db.Column(db.String(255), nullable=False)

    rol_assignments = db.relationship(
        "RolPermisoPuente",
        back_populates="permiso",
        cascade="all, delete-orphan",
    )


class PersonaRolPuente(db.Model):
    __tablename__ = "persona_rol_puente"

    persona_id = db.Column(
        db.Integer,
        db.ForeignKey("persona.persona_id", ondelete="CASCADE"),
        primary_key=True,
    )
    rol_id = db.Column(
        db.Integer,
        db.ForeignKey("rol.rol_id", ondelete="CASCADE"),
        primary_key=True,
    )
    asignado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    persona = db.relationship("Persona", back_populates="persona_roles")
    rol = db.relationship("Rol", back_populates="persona_assignments")


class RolPermisoPuente(db.Model):
    __tablename__ = "rol_permiso_puente"

    rol_id = db.Column(
        db.Integer,
        db.ForeignKey("rol.rol_id", ondelete="CASCADE"),
        primary_key=True,
    )
    permiso_id = db.Column(
        db.Integer,
        db.ForeignKey("permiso.permiso_id", ondelete="CASCADE"),
        primary_key=True,
    )

    rol = db.relationship("Rol", back_populates="rol_permissions")
    permiso = db.relationship("Permiso", back_populates="rol_assignments")
