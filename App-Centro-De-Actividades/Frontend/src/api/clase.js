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

export async function obtenerDetalleClase(claseId, dni) {
  const params = {}
  if (dni) {
    params.dni = dni
  }

  const { data } = await http.get(`/api/clase/${claseId}/detalle`, { params })
  return data
}

export async function actualizarClase(claseId, payload) {
  console.log("llego a pasar por aca");
  
  const { data } = await http.put(endpoints.actualizarClase(claseId), payload)
  console.log(data);
  
  return data
}

export async function cancelarClase(claseId) {
  const { data } = await http.post(endpoints.cancelarClase(claseId), {})
  return data
}

export async function obtenerProfesores() {
  const response = await http.get(endpoints.obtenerProfesores)

  return await response.data
}

export async function extenderClasesSiguienteMes(payload) {
  console.log("Enviando solicitud para extender clase al siguiente mes con payload:", payload);
  const response = await http.post(endpoints.crearSiguienteClase, payload);
  console.log("Data de regreso:", response.data);
  return await response.data
}

