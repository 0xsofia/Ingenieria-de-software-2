import { endpoints } from '../services/api'
import { http } from './http'

export async function registrarse(payload) {
  const { data } = await http.post(endpoints.registrarse, payload)
  return data
}
