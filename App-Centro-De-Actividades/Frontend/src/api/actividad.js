import { endpoints } from '../services/api'
import { http } from './http'

export async function obtenerActividades() {
  const { data } = await http.get(endpoints.actividades)
  return data
}
