import { endpoints } from '../services/api'
import { http } from './http'

export async function crearClase(payload) {
  const { data } = await http.post(endpoints.crearClase, payload)
  return data
}

export async function obtenerProfesores() {
  const response = await http.get(endpoints.obtenerProfesores)

  return await response.data
}