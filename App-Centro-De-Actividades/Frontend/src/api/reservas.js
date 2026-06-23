import { endpoints } from '../services/api'
import { http } from './http'

export async function reservarEspontanea(payload) {
  const { data } = await http.post(endpoints.reservaEspontanea, payload)
  return data
}

export async function reservarAbonada(payload) {
  const { data } = await http.post(endpoints.reservaAbonada, payload)
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

export async function listarMisAbonos() {
  const { data } = await http.get(endpoints.misAbonos)
  return data
}

export async function renovarAbonoMensual(payload) {
  const { data } = await http.post(endpoints.renovarAbonoMensual, payload)
  return data
}

export async function cancelarAbonoMensual(payload) {
  const { data } = await http.post(endpoints.cancelarAbonoMensual, payload)
  return data
}

export async function cancelarReservaEspontanea(payload) {
  const { data } = await http.post(endpoints.reservaEspontaneaCancelar, payload)
  return data
}

export async function cancelarReservaAbonada(payload) {
  const { data } = await http.post(endpoints.reservaAbonadaCancelar, payload)
  return data
}

export async function abandonarListaEspera(payload) {
  const { data } = await http.post(endpoints.abandonarListaEspera, payload)
  return data
}

export async function obtenerOfertasActivas() {
  const { data } = await http.get(endpoints.ofertasActivas)
  console.log("obtenerofertas activas:", data);
  
  return data
}

export async function confirmarTurno(payload) {
  const { data } = await http.post(endpoints.confirmarTurno, payload)
  return data
}
