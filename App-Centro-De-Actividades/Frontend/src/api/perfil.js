import { endpoints } from '../services/api'
import { http } from './http'

export async function obtenerPerfil() {
  const { data } = await http.get(endpoints.profileMe)
  return data
}

export async function actualizarPerfil(payload) {
  const { data } = await http.put(endpoints.profileMe, payload)
  return data
}
