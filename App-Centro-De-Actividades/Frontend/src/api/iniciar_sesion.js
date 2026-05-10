import { endpoints } from '../services/api'
import { http } from './http'

export async function iniciarSesion(payload) {
  const { data } = await http.post(endpoints.login, payload)
  return data
}

export async function seleccionarRolDeSesion(payload) {
  const { data } = await http.post(endpoints.selectLoginRole, payload)
  return data
}

export async function obtenerSesionActual() {
  const { data } = await http.get(endpoints.currentSession)
  return data
}

export async function autorizarPermiso(payload) {
  const { data } = await http.post(endpoints.authorizePermission, payload)
  return data
}

export async function cerrarSesion() {
  const { data } = await http.post(endpoints.logout)
  return data
}
