import { http } from './http'
import { endpoints } from '../services/api'

export async function obtenerConfirmacion(token) {
  const { data } = await http.get(endpoints.confirmacionTurno(token))
  console.log("Confirmacion del turno",data);
  
  return data
}

export async function confirmarDesdeToken(token) {
  const { data } = await http.post(endpoints.confirmarTurnoToken(token), {})
  return data
}
