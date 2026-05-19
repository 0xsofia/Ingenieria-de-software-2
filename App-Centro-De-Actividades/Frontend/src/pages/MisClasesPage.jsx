import { useEffect, useMemo, useState } from 'react'

import {
  cancelarReservaEspontanea,
  listarMisClases,
} from '../api/reservas'
import './MisClasesPage.css'

function MisClasesPage() {
  const [reservas, setReservas] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [feedback, setFeedback] = useState('')
  const [cancelingId, setCancelingId] = useState(null)

  const currencyFormatter = useMemo(
    () =>
      new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: 'ARS',
        minimumFractionDigits: 2,
      }),
    [],
  )

  useEffect(() => {
    fetchReservas()
  }, [])

  async function fetchReservas() {
    setIsLoading(true)
    setError('')

    try {
      const data = await listarMisClases()
      setReservas(data.reservas || [])
    } catch (err) {
      setError(err.data?.message || 'No se pudieron cargar las reservas.')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleCancelarReserva(reserva) {
    if (!reserva?.reserva_id) return

    const confirmCancel = window.confirm(
      'Vas a cancelar la reserva. El reintegro depende de las politicas de cancelacion. Queres continuar?',
    )

    if (!confirmCancel) return

    setCancelingId(reserva.reserva_id)
    setError('')
    setFeedback('')

    try {
      const result = await cancelarReservaEspontanea({
        reserva_id: reserva.reserva_id,
      })

      let message = result.message || 'Reserva cancelada.'
      if (result.reintegro?.estado === 'reintegrado') {
        message += ' Reintegro parcial iniciado.'
      } else if (result.reintegro?.estado === 'pendiente') {
        message += ' El reintegro quedo pendiente de configuracion.'
      }

      if (result.sancion_aplicada) {
        message += ' Se aplico una sancion por cancelaciones repetidas.'
      }

      setFeedback(message)
      await fetchReservas()
    } catch (err) {
      setError(err.data?.message || 'No se pudo cancelar la reserva.')
    } finally {
      setCancelingId(null)
    }
  }

  const renderEstado = (estado) => {
    const normalized = String(estado || '').toLowerCase()
    const labels = {
      confirmada: 'Confirmada',
      pendiente_pago: 'Pendiente de pago',
      cancelada: 'Cancelada',
    }

    return labels[normalized] || estado || 'Sin estado'
  }

  const renderMonto = (value) => {
    if (!value) return '-'

    const numeric = Number(value)
    if (Number.isNaN(numeric)) return value

    return currencyFormatter.format(numeric)
  }

  return (
    <main className="dashboard-shell mis-clases-shell">
      <section className="dashboard-frame mis-clases-frame">
        <header className="dashboard-header mis-clases-header">
          <h1>Mis clases</h1>
          <p className="dashboard-copy">
            Gestiona tus reservas y consulta si aplica reintegro.
          </p>
        </header>

        {error ? (
          <p className="banner banner--error" role="alert">
            {error}
          </p>
        ) : null}

        {feedback ? (
          <p className="banner banner--success" role="status">
            {feedback}
          </p>
        ) : null}

        {isLoading ? (
          <p className="dashboard-copy">Cargando reservas...</p>
        ) : (
          <div className="mis-clases-table-wrapper">
            <table className="mis-clases-table">
              <thead>
                <tr>
                  <th scope="col">Actividad</th>
                  <th scope="col">Fecha</th>
                  <th scope="col">Horario</th>
                  <th scope="col">Cancha</th>
                  <th scope="col">Estado</th>
                  <th scope="col">Pago</th>
                  <th scope="col">Monto abonado</th>
                  <th scope="col">Reintegro estimado</th>
                  <th scope="col">Acciones</th>
                </tr>
              </thead>

              <tbody>
                {reservas.length === 0 ? (
                  <tr>
                    <td className="mis-clases-table__empty" colSpan={9}>
                      No tenes reservas activas por el momento.
                    </td>
                  </tr>
                ) : (
                  reservas.map((reserva) => (
                    <tr key={reserva.reserva_id}>
                      <td data-label="Actividad">{reserva.actividad || 'Actividad'}</td>
                      <td data-label="Fecha">{reserva.fecha || '-'}</td>
                      <td data-label="Horario">
                        {reserva.horario_inicio || '--:--'} - {reserva.horario_fin || '--:--'}
                      </td>
                      <td data-label="Cancha">{reserva.cancha || '-'}</td>
                      <td data-label="Estado">
                        <span className="mis-clases-table__status">
                          {renderEstado(reserva.estado)}
                        </span>
                      </td>
                      <td data-label="Pago">{reserva.pago_estado || 'Sin pago'}</td>
                      <td data-label="Monto abonado">{renderMonto(reserva.monto_pagado)}</td>
                      <td data-label="Reintegro estimado">
                        {reserva.reintegro_aplica
                          ? renderMonto(reserva.reintegro_estimado)
                          : 'No aplica'}
                      </td>
                      <td data-label="Acciones">
                        <div className="mis-clases-table__actions">
                          <button
                            type="button"
                            className="primary-action"
                            onClick={() => handleCancelarReserva(reserva)}
                            disabled={!reserva.puede_cancelar || cancelingId === reserva.reserva_id}
                          >
                            {cancelingId === reserva.reserva_id
                              ? 'Cancelando...'
                              : 'Cancelar reserva'}
                          </button>

                          {!reserva.puede_cancelar ? (
                            <p className="mis-clases-table__hint">
                              Esta reserva ya no puede cancelarse.
                            </p>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  )
}

export default MisClasesPage
