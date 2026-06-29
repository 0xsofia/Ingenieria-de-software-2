import calendar
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user

from src.core.database import db
from src.core.models.clase import Clase
from src.core.models.reserva import Reserva
from src.core.services.clase_service import (
    validar_payload_clase,
    validar_payload_actualizar_clase,
    crear_clase_completa,
    obtener_clases,
    obtener_detalle_clase_con_socios,
    actualizar_clase,
    cancelar_clase,
)

clase_bp = Blueprint("clase", __name__, url_prefix="/api/clase")
ESTADOS_OCUPAN_CUPO = ("pendiente_pago", "confirmada")


@clase_bp.post("/crear")
def crear_clase():
    payload = request.get_json(silent=True) or {}
    normalized_payload, errors = validar_payload_clase(payload)

    if errors:
        return jsonify({"status": "validation_error", "errors": errors}), 400

    body, status_code = crear_clase_completa(normalized_payload)
    return jsonify(body), status_code


@clase_bp.get("/lista")
def listar_clases():
    actividad = (request.args.get("actividad") or "").strip()
    fecha = (request.args.get("fecha") or "").strip()
    horario = (request.args.get("horario") or "").strip()
    clases = obtener_clases(actividad, fecha, horario)
    cupos_ocupados = _obtener_cupos_ocupados(clases)
    clases_reservadas = _obtener_clases_reservadas_por_socio(clases)
    clases_data = [
        {
            "clase_id": clase.clase_id,
            "actividad": clase.actividad.value,
            "fecha": clase.fecha.strftime("%Y-%m-%d"),
            "horario_inicio": clase.horario_inicio.strftime("%H:%M"),
            "horario_fin": clase.horario_fin.strftime("%H:%M"),
            "cancha": clase.cancha,
            "nivel": clase.nivel.value,
            "cupos": clase.cupos,
            "cupos_ocupados": cupos_ocupados.get(clase.clase_id, 0),
            "precio": float(clase.precio) if clase.precio is not None else None,
            "tipo_clase": clase.tipo_clase.value,
            "profesor_id": clase.profesor_id,
            "profesor_nombre": clase.profesor.nombre if clase.profesor else None,
            "ya_reservado": clase.clase_id in clases_reservadas,
        }
        for clase in clases
    ]

    return jsonify(clases_data), 200


@clase_bp.put("/actualizar/<int:clase_id>")
def actualizar_clase_controller(clase_id):
    payload = request.get_json(silent=True) or {}
    
    normalized_payload, errors = validar_payload_actualizar_clase(payload)
    print("Payload recibido despues de validar:", normalized_payload, errors)   
    if errors:
        return jsonify({"status": "validation_error", "errors": errors}), 400

    body, status_code = actualizar_clase(clase_id, normalized_payload)
    return jsonify(body), status_code


def _obtener_cupos_ocupados(clases):
    clase_ids = [clase.clase_id for clase in clases]
    if not clase_ids:
        return {}

    rows = (
        db.session.query(Reserva.clase_id, db.func.count(Reserva.reserva_id))
        .filter(Reserva.clase_id.in_(clase_ids))
        .filter(Reserva.estado.in_(ESTADOS_OCUPAN_CUPO))
        .group_by(Reserva.clase_id)
        .all()
    )

    return {clase_id: int(total) for clase_id, total in rows}


def _obtener_clases_reservadas_por_socio(clases):
    if not current_user.is_authenticated or getattr(current_user, "role", None) != "socio":
        return set()

    clase_ids = [clase.clase_id for clase in clases]
    if not clase_ids:
        return set()

    rows = (
        db.session.query(Reserva.clase_id)
        .filter(Reserva.clase_id.in_(clase_ids))
        .filter(Reserva.socio_id == current_user.persona_id)
        .filter(Reserva.estado == "confirmada")
        .all()
    )

    return {clase_id for (clase_id,) in rows}


@clase_bp.get("/<int:clase_id>/detalle")
def obtener_detalle_clase(clase_id):
    """Obtiene el detalle de una clase con los socios registrados y su estado de asistencia."""
    dni = (request.args.get("dni") or "").strip()
    dni_filter = dni if dni else None
    clase_data, status_code = obtener_detalle_clase_con_socios(clase_id, dni_filter)

    if status_code == 404:
        return jsonify({"status": "error", "message": "La clase no fue encontrada."}), 404

    return jsonify(clase_data), status_code


@clase_bp.post('/cancelar/<int:clase_id>')
def cancelar_clase_controller(clase_id):
    body, status_code = cancelar_clase(clase_id)
    return jsonify(body), status_code

@clase_bp.route('/siguiente', methods=['POST'])
def extender_clase_por_id():
    data = request.get_json() or {}
    clase_id = data.get('clase_id')
    mes_destino = data.get('mes')

    if not clase_id or not mes_destino:
        return jsonify({
            "status": "error",
            "message": "El ID de la clase y el mes de destino son obligatorios."
        }), 400

    try:
        clase_base = db.session.get(Clase, clase_id) if hasattr(db.session, 'get') else Clase.query.get(clase_id)
        if not clase_base:
            return jsonify({
                "status": "error",
                "message": "No se encontró la clase original para extender."
            }), 404

        dias_espanol = {
            0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"
        }
        
        dia_semana_calculado = dias_espanol[clase_base.fecha.weekday()]

        if hasattr(clase_base.horario_inicio, 'strftime'):
            horario_str = clase_base.horario_inicio.strftime('%H:%M')
        else:
            horario_str = str(clase_base.horario_inicio)[:5]

        actividad_str = clase_base.actividad.value if hasattr(clase_base.actividad, 'value') else str(clase_base.actividad)
        nivel_str = clase_base.nivel.value if hasattr(clase_base.nivel, 'value') else str(clase_base.nivel)
        
        profesor_id_target = clase_base.profesor_id
        horario_inicio_target = clase_base.horario_inicio
        cancha_target = clase_base.cancha
        actividad_label = clase_base.actividad

        reservas_viejas_datos = [{"cliente_id": r.cliente_id} for r in Reserva.query.filter_by(clase_id=clase_id, estado="abonada").all()]

        payload_clase_nueva = {
            "actividad": actividad_str,
            "dia_semana": dia_semana_calculado,
            "mes": int(mes_destino),
            "horario_inicio": horario_str,
            "cancha": cancha_target,
            "nivel": nivel_str,
            "cupos": clase_base.cupos,
            "precio": float(clase_base.precio) if clase_base.precio is not None else None,
            "profesor_id": profesor_id_target,
        }

        # 1. Obtenemos la fecha real de hoy en el servidor
        hoy = datetime.now()
        
        # 2. Calculamos el año correspondiente
        # Si el mes destino es menor al mes actual, significa que saltamos al año siguiente (ej: de Dic a Ene)
        if int(mes_destino) < hoy.month:
            año_calculado = hoy.year + 1
        else:
            año_calculado = hoy.year

        # 3. Armamos la fecha simulada con el año correcto
        fecha_simulada = datetime(año_calculado, int(mes_destino), 1)
        
        resultado_creacion, status_code = crear_clase_completa(payload_clase_nueva, fecha_actual=fecha_simulada)

        if status_code != 201:
            # ---> ESTE PRINT TE VA A DECIR EN LA CONSOLA DE FLASK QUÉ RECHAZÓ TU SERVICIO <---
            print(f"\n[RECHAZO DE SERVICIO] Código {status_code}: {resultado_creacion}\n")
            return jsonify(resultado_creacion), status_code

        if reservas_viejas_datos:
            fecha_inicio_mes = datetime(año_calculado, int(mes_destino), 1).date()
            ultimo_dia = calendar.monthrange(año_calculado, int(mes_destino))[1]
            fecha_fin_mes = datetime(año_calculado, int(mes_destino), ultimo_dia).date()

            clases_nuevas_insertadas = Clase.query.filter(
                Clase.profesor_id == profesor_id_target,
                Clase.horario_inicio == horario_inicio_target,
                Clase.cancha == cancha_target,
                Clase.fecha >= fecha_inicio_mes,
                Clase.fecha <= fecha_fin_mes,
                Clase.is_eliminated == False
            ).all()

            for nueva_clase in clases_nuevas_insertadas:
                for res_datos in reservas_viejas_datos:
                    reserva_existe = Reserva.query.filter_by(
                        clase_id=nueva_clase.clase_id, 
                        cliente_id=res_datos['cliente_id']
                    ).first()
                    
                    if not reserva_existe:
                        nueva_reserva = Reserva(
                            clase_id=nueva_clase.clase_id,
                            cliente_id=res_datos['cliente_id'],
                            estado="abonada"
                        )
                        db.session.add(nueva_reserva)
            
            db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Las clases fueron registradas correctamente",
            "redirect_to": "/clases"
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error crítico al extender clase: {e}")
        return jsonify({"status": "error", "message": "Hubo un problema interno al procesar la extensión."}), 500