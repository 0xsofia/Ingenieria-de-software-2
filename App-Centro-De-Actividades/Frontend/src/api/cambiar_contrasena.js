import { endpoints } from '../services/api'
import { http } from './http'

export async function cambiarContrasena(payload) {
  const { data } = await http.post(endpoints.cambiarContrasena, payload)
  return data
}

export async function validarToken(token) {
  const { data } = await http.get(`${endpoints.cambiarContrasena}/${token}`)
  return data
}
