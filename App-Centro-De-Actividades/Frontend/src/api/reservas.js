import { endpoints } from '../services/api'
import { http } from './http'

export async function reservarEspontanea(payload) {
  const { data } = await http.post(endpoints.reservaEspontanea, payload)
  return data
}

export async function entrarListaEspera(payload) {
  const { data } = await http.post(endpoints.reservaEspontaneaListaEspera, payload)
  return data
}

export async function confirmarPagoRetorno(payload) {
  const { data } = await http.post(endpoints.reservaEspontaneaPagoRetorno, payload)
  return data
}

export async function listarMisClases() {
  const { data } = await http.get(endpoints.misClases)
  return data
}

export async function cancelarReservaEspontanea(payload) {
  const { data } = await http.post(endpoints.reservaEspontaneaCancelar, payload)
  return data
}
