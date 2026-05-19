import { endpoints } from '../services/api'
import { http } from './http'

export async function crearProfesor(payload) {
  const { data } = await http.post(endpoints.crearProfesor, payload)
  return data
}
