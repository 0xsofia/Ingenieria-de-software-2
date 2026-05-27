import { endpoints } from '../services/api'
import { http } from './http'

export async function escanearQR(payload, idClase) {
  const bodyData = {
    dni: String(payload.dni).trim(),
    id_reserva: Number(payload.id_reserva),
    id_clase: idClase ? Number(idClase) : null
  };

  const { data } = await http.post('/api/asistencia/escanearQR', bodyData);
  return data;
}

export async function generarQR(idReserva) {

  const { data } = await http.post(`/api/asistencia/generarQR/${idReserva}`)
  return data
}

export async function registrarAsistenciaManual(reservaId) {
  const { data } = await http.post(`/api/asistencia/registrar-manual/${reservaId}`)
  return data
}