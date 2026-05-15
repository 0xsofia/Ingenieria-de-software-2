import { endpoints } from '../services/api'
import { http } from './http'

export async function registrarAsistencia(payload) {
  const { data } = await http.post(endpoints.registrarAsistencia, payload)
  return data
}
