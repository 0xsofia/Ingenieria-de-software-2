import { endpoints } from '../services/api'
import { http } from './http'

export async function registrarEmpleado(payload) {
  const { data } = await http.post(endpoints.registerEmployee, payload)
  return data
}
