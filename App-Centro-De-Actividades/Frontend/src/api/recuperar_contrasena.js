import { endpoints } from '../services/api'
import { http } from './http'

export async function solicitarRecuperacion(email) {
  const { data } = await http.post(endpoints.recuperarContrasena, { email })
  return data
}
