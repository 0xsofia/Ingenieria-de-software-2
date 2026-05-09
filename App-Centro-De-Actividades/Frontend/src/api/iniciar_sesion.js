import { endpoints } from '../services/api'

export async function iniciarSesion() {
  const response = await fetch(endpoints.login)

  if (!response.ok) {
    throw new Error(`Error al llamar login: ${response.status}`)
  }

  return response.text()
}
