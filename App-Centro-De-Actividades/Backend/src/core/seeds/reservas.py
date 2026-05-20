from datetime import datetime, date, time
from src.core.database import db
from src.core.models.reserva import Reserva
from src.core.models.clase import Clase
from src.core.models.persona import Persona, Socio
from src.core.models.profesor import Profesor 
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum

# ===========================================================================
# MAPEADORES DE STRINGS A ENUMS REALES (Evita errores en Postgres)
# ===========================================================================
def obtener_actividad_enum(nombre_str):
    mapping = {
        "voley": ActividadEnum.VOLEY if hasattr(ActividadEnum, 'VOLEY') else ActividadEnum.FUTBOL,
        "futbol": ActividadEnum.FUTBOL,
        "padel": ActividadEnum.PADEL if hasattr(ActividadEnum, 'PADEL') else ActividadEnum.FUTBOL,
        "basquet": ActividadEnum.BASQUET if hasattr(ActividadEnum, 'BASQUET') else ActividadEnum.FUTBOL,
        "crossfit": ActividadEnum.CROSSFIT if hasattr(ActividadEnum, 'CROSSFIT') else ActividadEnum.FUTBOL,
    }
    return mapping.get(nombre_str.lower().strip(), ActividadEnum.FUTBOL)

def obtener_nivel_enum(nivel_str):
    mapping = {
        "principiante": NivelEnum.PRINCIPIANTE,
        "intermedio": NivelEnum.INTERMEDIO if hasattr(NivelEnum, 'INTERMEDIO') else NivelEnum.PRINCIPIANTE,
        "avanzado": NivelEnum.AVANZADO if hasattr(NivelEnum, 'AVANZADO') else NivelEnum.PRINCIPIANTE,
    }
    return mapping.get(nivel_str.lower().strip(), NivelEnum.PRINCIPIANTE)


# ===========================================================================
# DATO SEMILLA DE PROFESORES REALES
# ===========================================================================
PROFESORES_TO_SEED = [
    {"nombre": "Juan García", "dni": "12345678", "telefono": "1234567890"},
    {"nombre": "María López", "dni": "87654321", "telefono": "0987654321"},
    {"nombre": "Carlos Martínez", "dni": "11223344", "telefono": "5555555555"},
    {"nombre": "Ana Rodríguez", "dni": "44332211", "telefono": "6666666666"},
]

# ===========================================================================
# DATO SEMILLA DE RESERVAS Y CLASES
# ===========================================================================
RESERVAS_TO_SEED = [
    {
        "reserva_id": 2001,
        "socio_dni": "44444444",
        "socio_nombre": "David",
        "socio_apellido": "Matias",
        "socio_email": "david.matias@carpintech.com",
        "tipo_reserva": "estandar",
        "estado": "confirmada",  # Éxito Verde en QR
        "fecha_str": "2026-06-01",
        "actividad_str": "Futbol",
        "horario_inicio_str": "18:00",
        "cancha": "Cancha B",
        "nivel_str": "Intermedio",
        "cupos": 10,
        "profesor_dni": "87654321"  # María López
    },
    {
        "reserva_id": 2002,
        "socio_dni": "55555555",
        "socio_nombre": "Juan",
        "socio_apellido": "Pérez",
        "socio_email": "juan.perez@carpintech.com",
        "tipo_reserva": "estandar",
        "estado": "asistio",  # Error 409 (Ya escaneado)
        "fecha_str": "2026-06-01",
        "actividad_str": "Voley",
        "horario_inicio_str": "08:00",
        "cancha": "Voley",
        "nivel_str": "Principiante",
        "cupos": 8,
        "profesor_dni": "12345678"  # Juan García
    },
    {
        "reserva_id": 2003,
        "socio_dni": "66666666",
        "socio_nombre": "Lautaro",
        "socio_apellido": "Gómez",
        "socio_email": "lau.gomez@carpintech.com",
        "tipo_reserva": "pase_libre",
        "estado": "pendiente_pago",  # Pasa el unique constraint condicional
        "fecha_str": "2026-06-01",
        "actividad_str": "Futbol",
        "horario_inicio_str": "18:00",
        "cancha": "Cancha B",
        "nivel_str": "Intermedio",
        "cupos": 10,
        "profesor_dni": "87654321"
    },
    {
        "reserva_id": 2004,
        "socio_dni": "44444444",
        "socio_nombre": "David",
        "socio_apellido": "Matias",
        "socio_email": "david.matias@carpintech.com",
        "tipo_reserva": "estandar",
        "estado": "confirmada",
        "fecha_str": "2026-06-12",
        "actividad_str": "Basquet",
        "horario_inicio_str": "18:00",
        "cancha": "Cancha D",
        "nivel_str": "Intermedio",
        "cupos": 12,
        "profesor_dni": "44332211"  # Ana Rodríguez
    }
]


# ===========================================================================
# FUNCIÓN PRINCIPAL EJECUTABLE
# ===========================================================================
def seed_reservas():
    print("🌱 [SEED] Iniciando base de datos unificada de Carpintech...")
    
    # 1. Creamos / actualizamos los profesores
    for prof_data in PROFESORES_TO_SEED:
        _ensure_profesor_exists(prof_data)
        
    # 2. Procesamos socios, clases y reservas
    for r_data in RESERVAS_TO_SEED:
        socio_id = _ensure_socio_exists(r_data)
        clase_id = _ensure_clase_exists(r_data)
        
        reserva = Reserva.query.get(r_data["reserva_id"])
        if reserva is None:
            reserva = Reserva(
                reserva_id=r_data["reserva_id"],
                clase_id=clase_id,
                socio_id=socio_id, # Asigna la FK limpia a la tabla Socio
                tipo_reserva=r_data["tipo_reserva"],
                estado=r_data["estado"],
                creada_en=datetime.now()
            )
            if r_data["estado"] in ["confirmada", "asistio"]:
                reserva.confirmada_en = datetime.now()
            db.session.add(reserva)
        else:
            reserva.clase_id = clase_id
            reserva.socio_id = socio_id
            reserva.tipo_reserva = r_data["tipo_reserva"]
            reserva.estado = r_data["estado"]
            
        db.session.flush()

    db.session.commit()
    print("🚀 [SEED] ¡Profesores, Socios, Clases y Reservas sincronizados con éxito!")


# ===========================================================================
# HELPERS DE INSERCIÓN SEGUROS
# ===========================================================================
def _ensure_profesor_exists(data):
    """Busca o inserta al Profesor usando directamente sus columnas propias."""
    profesor = Profesor.query.filter_by(dni=data["dni"]).first()
    
    if profesor is None:
        profesor = Profesor(
            nombre=data["nombre"],
            dni=data["dni"],
            telefono=data["telefono"]
        )
        db.session.add(profesor)
    else:
        profesor.nombre = data["nombre"]
        profesor.telefono = data["telefono"]
        
    db.session.flush()
    return profesor.profesor_id


def _ensure_socio_exists(data):
    """Busca/Inserta Persona, garantiza existencia en tabla Socio y retorna su ID."""
    dni = data["socio_dni"].strip()
    persona = Persona.query.filter_by(dni=dni).first()
    
    if persona is None:
        persona = Persona(
            dni=dni,
            email=data["socio_email"],
            password_hash="scrypt:32768:8:1$hashsocio$123",
            nombre=data["socio_nombre"],
            apellido=data["socio_apellido"],
            telefono="2214445555",
            calle="Avenida 1",
            numero_puerta="100",
            codigo_postal="1900",
            estado="activo"
        )
        db.session.add(persona)
        db.session.flush()

    # Buscamos el Socio usando la PK compartida o la columna persona_id correspondientemente
    socio = Socio.query.filter_by(persona_id=persona.persona_id).first() if hasattr(Socio, 'persona_id') else Socio.query.get(persona.persona_id)
    
    if socio is None:
        socio = Socio()
        if hasattr(socio, 'persona'):
            socio.persona = persona
        else:
            socio.persona_id = persona.persona_id
        db.session.add(socio)
        db.session.flush()
        
    # Retorna el ID que va a ir a parar a Reserva.socio_id (vinculado a socio.persona_id)
    return socio.persona_id if hasattr(socio, 'persona_id') else persona.persona_id


def _ensure_clase_exists(data):
    """Garantiza la existencia de la clase semilla con su Profesor real."""
    fecha_str = (data.get("fecha_str") or "").strip()
    fecha_clase = date.fromisoformat(fecha_str) if fecha_str else date.today()
    hora_partes = [int(p) for p in data["horario_inicio_str"].split(":")]
    h_inicio = time(hora_partes[0], hora_partes[1])
    h_fin = time((hora_partes[0] + 1) % 24, hora_partes[1])
    
    actividad_enum = obtener_actividad_enum(data["actividad_str"])
    nivel_enum = obtener_nivel_enum(data["nivel_str"])

    clase = Clase.query.filter_by(
        actividad=actividad_enum, 
        fecha=fecha_clase, 
        horario_inicio=h_inicio
    ).first()

    if clase is None:
        prof = Profesor.query.filter_by(dni=data["profesor_dni"]).first()
        prof_id = prof.profesor_id if prof else 1

        clase = Clase(
            actividad=actividad_enum,
            fecha=fecha_clase,
            horario_inicio=h_inicio,
            horario_fin=h_fin,
            cancha=data["cancha"],
            nivel=nivel_enum,
            cupos=data["cupos"],
            tipo_clase=(
                TipoClaseEnum.PARTICULAR if int(data["cupos"]) == 1 else TipoClaseEnum.GRUPAL
            ),
            profesor_id=prof_id
        )
        db.session.add(clase)
        db.session.flush()

    return clase.clase_id
