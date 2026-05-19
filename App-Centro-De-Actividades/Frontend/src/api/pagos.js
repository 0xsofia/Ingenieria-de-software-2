import { endpoints } from '../services/api'
import { http } from './http'

export async function obtenerPagos(filters = {}) {
  const { data } = await http.get(endpoints.misPagos, {
    params: filters,
  })

  return data
}
