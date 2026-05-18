import { endpoints } from '../services/api'
import { http } from './http'

export async function registrarEmpleado(payload) {
  const { data } = await http.post(endpoints.registerEmployee, payload)
  return data
}

export async function listarUsuarios(filters) {
  const params = Object.fromEntries(
    Object.entries(filters || {}).filter(([, value]) => value !== '' && value !== null && value !== undefined)
  )
  const { data } = await http.get(endpoints.users, { params })
  return data
}

export async function obtenerUsuarioModificable(personaId) {
  const { data } = await http.get(`${endpoints.users}/${personaId}`)
  return data
}

export async function modificarUsuario(personaId, payload) {
  const { data } = await http.put(`${endpoints.users}/${personaId}`, payload)
  return data
}

// export async function listarUsuarios(nombre = '', dni = '', mail = '') {
//   const { data } = await http.get(endpoints.users, {
//     params: {
//       nombre: nombre,
//       dni: dni,
//       mail: mail
//     }
//   })
//   return data
// }
