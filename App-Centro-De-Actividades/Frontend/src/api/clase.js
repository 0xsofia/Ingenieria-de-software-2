import { endpoints } from '../services/api'
import { http } from './http'

export async function crearClase(payload) {
  const { data } = await http.post(endpoints.crearClase, payload)
  return data
}

export async function listarClases(filters = {}) {
  const params = {}

  if (filters.actividad) {
    params.actividad = filters.actividad
  }

  if (filters.fecha) {
    params.fecha = filters.fecha
  }

  if (filters.horario) {
    params.horario = filters.horario
  }

  const { data } = await http.get(endpoints.listarClases, { params })
  return data
}

export async function obtenerProfesores() {
  const response = await http.get(endpoints.obtenerProfesores)

  return await response.data
}