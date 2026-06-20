import random
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
from src.core.database import db
from src.core.models import Persona, Socio, Empleado, Clase, Reserva, ListaEspera, Pago, Asistencia
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum

def seed_metricas():
    print("🚀 Iniciando la carga de datos de prueba para el año 2026...")

    # 1. Crear Roles y Permisos básicos en caso de no existir o usar IDs fijos.
    # Asumimos un profesor de ID fijo para simplificar el ForeignKey de Clase
    profesor_id_test = 1 

    # 2. Crear un pool de Socios (Personas)
    socios_creados = []
    print("👥 Creando socios de prueba...")
    for i in range(1, 16):  # 15 socios para generar volumen y listas de espera
        dni = f"45000{i:03d}"
        email = f"socio{i}@centro.test"
        
        persona = Persona.query.filter_by(email=email).first()
        if not persona:
            persona = Persona(
                dni=dni,
                email=email,
                password_hash="pbkdf2:sha256:default_hash_for_testing_123456",
                nombre=f"SocioNombre{i}",
                apellido=f"Apellido{i}",
                telefono=f"11234567{i:02d}",
                calle="Av. Siempreviva",
                numero_puerta=str(742 + i),
                codigo_postal="1900",
                estado="activo"
            )
            db.session.add(persona)
            db.session.flush()  # Para obtener el persona_id

            socio = Socio(persona_id=persona.persona_id)
            db.session.add(socio)
            socios_creados.append(socio)
        else:
            socio = Socio.query.get(persona.persona_id)
            if socio:
                socios_creados.append(socio)

    db.session.commit()

    # 3. Generación de Clases Semanales a lo largo del 2026
    print("📅 Generando cronograma de clases, reservas y pagos para el 2026...")
    
    # Configuramos deportes a evaluar sacados de tu ActividadEnum
    actividades = list(ActividadEnum) if list(ActividadEnum) else ["VOLEY", "FUTBOL", "BASQUET"]
    proveedores_pago = ["mercadopago", "efectivo", "stripe"]
    
    fecha_actual = date(2026, 1, 1)
    fecha_fin_anio = date(2026, 12, 31)
    
    total_clases = 0
    total_pagos = 0

    while fecha_actual <= fecha_fin_anio:
        # Generamos unas 3 clases en días particulares (ej: Lunes, Miércoles, Viernes)
        if fecha_actual.weekday() in [0, 2, 4]:
            for idx, actividad in enumerate(actividades):
                # Variar horarios para tener diversidad micro-operativa
                if idx % 3 == 0:
                    h_inicio, h_fin = time(16, 0), time(17, 32)
                elif idx % 3 == 1:
                    h_inicio, h_fin = time(19, 0), time(20, 30)
                else:
                    h_inicio, h_fin = time(8, 0), time(9, 30)

                # Definimos cupo bajo para forzar Listas de Espera en Voley
                es_voley = "voley" in str(actividad).lower()
                cupos_clase = 5 if es_voley else 12

                nueva_clase = Clase(
                    actividad=actividad,
                    fecha=fecha_actual,
                    horario_inicio=h_inicio,
                    horario_fin=h_fin,
                    cancha=f"Cancha de {str(actividad).split('.')[-1].capitalize()}",
                    nivel=random.choice(list(NivelEnum)),
                    cupos=cupos_clase,
                    precio=Decimal("1500.00"),
                    tipo_clase=random.choice(list(TipoClaseEnum)),
                    profesor_id=profesor_id_test
                )
                db.session.add(nueva_clase)
                db.session.flush()
                total_clases += 1

                # 4. Simulación de Socios anotándose (Reservas e Inscripciones)
                # Mezclamos el pool de socios de forma aleatoria
                random.shuffle(socios_creados)
                
                # Determinamos cuántos quieren asistir (Voley tendrá sobrepoblación intencional)
                cantidad_interesados = random.randint(7, 12) if es_voley else random.randint(2, 8)
                
                posicion_lista_espera = 1

                for j in range(min(cantidad_interesados, len(socios_creados))):
                    socio_actual = socios_creados[j]
                    
                    if j < cupos_clase:
                        # ENTRA DIRECTO A RESERVA
                        # 70% de probabilidad de que asista realmente a clases pasadas
                        # Las clases que caigan a futuro de la fecha real de hoy se quedan en "confirmada"
                        fecha_clase_completa = datetime.combine(fecha_actual, h_inicio).replace(tzinfo=timezone.utc)
                        es_pasada = fecha_clase_completa < datetime.now(timezone.utc)

                        estado_reserva = "confirmada"
                        if es_pasada:
                            estado_reserva = "asistio" if random.random() < 0.75 else "confirmada"

                        nueva_reserva = Reserva(
                            clase_id=nueva_clase.clase_id,
                            socio_id=socio_actual.persona_id,
                            tipo_reserva="regular",
                            estado=estado_reserva,
                            creada_en=fecha_clase_completa - timedelta(days=2)
                        )
                        db.session.add(nueva_reserva)
                        db.session.flush()

                        # Si asistió, creamos el registro físico en Asistencia para la métrica B
                        if estado_reserva == "asistio":
                            nueva_asistencia = Asistencia(
                                reserva_id=nueva_reserva.reserva_id,
                                fecha_hora=fecha_clase_completa + timedelta(minutes=10),
                                medio_registro="QR"
                            )
                            db.session.add(nueva_asistencia)

                        # Generamos flujo de Caja (Pagos aprobados para la métrica A)
                        monto = Decimal("1500.00")
                        nuevo_pago = Pago(
                            socio_id=socio_actual.persona_id,
                            reserva_id=nueva_reserva.reserva_id,
                            proveedor=random.choice(proveedores_pago),
                            monto_bruto=monto,
                            descuento_pct=Decimal("0.00"),
                            monto_pagado=monto,
                            estado="approved",
                            fecha_pago=fecha_clase_completa - timedelta(days=1)
                        )
                        db.session.add(nuevo_pago)
                        total_pagos += 1

                    else:
                        # SUPERA EL CUPO: SE VA A LISTA DE ESPERA (Métrica C)
                        # Hacemos que queden registros de lista de espera guardados como históricos
                        nueva_espera = ListaEspera(
                            clase_id=nueva_clase.clase_id,
                            socio_id=socio_actual.persona_id,
                            posicion=posicion_lista_espera,
                            estado="pendiente",
                            creada_en=datetime.combine(fecha_actual, h_inicio).replace(tzinfo=timezone.utc) - timedelta(days=1)
                        )
                        db.session.add(nueva_espera)
                        posicion_lista_espera += 1

        # Avanzar el bucle de días
        fecha_actual += timedelta(days=1)
        
        # Guardado en baches cada mes para no saturar memoria RAM
        if fecha_actual.day == 1:
            db.session.commit()

    db.session.commit()
    print(f"✅ Seeding finalizado con éxito.")
    print(f"📊 Resumen cargado: {total_clases} Clases, {total_pagos} Pagos registrados con sus asistencias mapeadas para el 2026.")