import { endpoints } from '../services/api'
import { http } from './http'

export async function escanearQR(payload) {

  const { data } = await http.post('/api/asistencia/escanearQR', payload);
  return data;
}

export async function generarQR(idReserva) {

  const { data } = await http.post(`/api/asistencia/generarQR/${idReserva}`)
  return data
}