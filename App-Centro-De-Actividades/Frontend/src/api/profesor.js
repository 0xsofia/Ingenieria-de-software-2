import { endpoints } from '../services/api'
import { http } from './http'

export async function crearProfesor(payload) {
  const { data } = await http.post(endpoints.crearProfesor, payload)
  return data
}

export async function obtenerProfesores() {
  const { data } = await http.get(endpoints.obtenerProfesores)
  return data
}

export async function eliminarProfesor(profesorId) {
  const { data } = await http.delete(endpoints.eliminarProfesor(profesorId))
  return data
}
