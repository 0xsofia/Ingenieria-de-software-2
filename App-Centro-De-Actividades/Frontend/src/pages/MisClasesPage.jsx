import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  cancelarReservaEspontanea,
  listarMisClases,
  obtenerOfertasActivas,
  confirmarTurno,
} from '../api/reservas'
import './MisClasesPage.css'

function MisClasesPage() {
  const navigate = useNavigate()
  const [reservas, setReservas] = useState([])
  const [listaEspera, setListaEspera] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [feedback, setFeedback] = useState('')
  const [cancelingId, setCancelingId] = useState(null)
  const [ofertas, setOfertas] = useState([])
  const [confirmingId, setConfirmingId] = useState(null)

  const currencyFormatter = useMemo(
    () =>
      new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: 'ARS',
        minimumFractionDigits: 2,
      }),
    [],
  )

  function handleAbandonarListaEspera(reserva) {
    if (!reserva?.reserva_id) return

    setError('')
    setFeedback('Funcionalidad de abandonar lista de espera todavía no está implementada.')
  }

  function handleGenerarQR(reserva) {
    if (!reserva?.reserva_id) return

    setError('')
    // Navega a la página que ya realiza la llamada al backend y renderiza el QR
    navigate(`/reservas/${reserva.reserva_id}/qr`)
  }

  useEffect(() => {
    fetchReservas()
    fetchOfertas()
  }, [])

  async function fetchReservas() {
    setIsLoading(true)
    setError('')

    try {
      const data = await listarMisClases()
      setReservas(data.reservas || [])
      setListaEspera(data.lista_espera || [])
    } catch (err) {
      setError(err.data?.message || 'No se pudieron cargar las reservas.')
    } finally {
      setIsLoading(false)
    }
  }

  async function fetchOfertas() {
    try {
      const result = await obtenerOfertasActivas()
      setOfertas(result.ofertas || [])
    } catch (err) {
      console.warn('No se pudieron cargar ofertas', err)
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

      console.log(result)

      let message = result.message || 'Reserva cancelada.'
      if (result.scenario_message) {
        message += ` ${result.scenario_message}`
      }
      if (result.reintegro?.estado === 'reintegrado') {
        message += ' Reintegro parcial iniciado.'
      } else if (result.reintegro?.estado === 'pendiente') {
        message += ' El reintegro quedo pendiente de configuracion.'
      }

      if (!result.scenario_message && result.sancion_aplicada) {
        message += ' Se aplico una sancion por cancelaciones repetidas.'
      }

      setFeedback(message)
      await fetchReservas()
      await fetchOfertas()
    } catch (err) {
      setError(err.data?.message || 'No se pudo cancelar la reserva.')
    } finally {
      setCancelingId(null)
    }
  }

  async function handleConfirmarTurno(oferta) {
    if (!oferta?.lista_espera_id) return

    setConfirmingId(oferta.lista_espera_id)
    setError('')
    setFeedback('')

    try {
      const result = await confirmarTurno({ lista_espera_id: oferta.lista_espera_id })

      if (result.status === 'expired') {
        setError(result.message || 'El tiempo de 15 minutos para confirmar el turno ha expirado, no puede acceder al cupo')
      } else if (result.status === 'conflict') {
        setError(result.message || 'No puede confirmar el turno, ya posee una inscripción en ese horario')
      } else if (result.status === 'confirmed') {
        setFeedback(result.message || 'Turno asegurado. Completá la reserva.')
        await fetchOfertas()
        const actividadSlug = getSlug(oferta.actividad || result.actividad || 'actividad')
        navigate(`/actividad/${actividadSlug}`, {
          state: {
            clase: {
              clase_id: result.clase_id || oferta.clase_id,
              actividad: result.actividad || oferta.actividad,
              fecha: result.fecha || oferta.fecha,
              horario_inicio: result.horario_inicio || oferta.horario_inicio,
              horario_fin: result.horario_fin || oferta.horario_fin,
              cancha: result.cancha || oferta.cancha,
            },
          },
        })
      } else {
        setError(result.message || 'No se pudo confirmar el turno.')
      }
    } catch (err) {
      setError(err.data?.message || 'No se pudo confirmar el turno.')
    } finally {
      setConfirmingId(null)
    }
  }

  const renderMonto = (value) => {
    if (!value) return '-'

    const numeric = Number(value)
    if (Number.isNaN(numeric)) return value

    return currencyFormatter.format(numeric)
  }

  function getSlug(text) {
    return String(text || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '')
  }

  return (
    <main className="dashboard-shell mis-clases-shell">
      <section className="dashboard-frame mis-clases-frame">
        <header className="dashboard-header mis-clases-header">
          <h1>Mis clases</h1>
          {/* <p className="dashboard-copy">
            Gestiona tus reservas y consulta si aplica reintegro.
          </p> */}
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
          <div>{/*
            {ofertas.length > 0 ? (
              <div className="ofertas-list">
                {ofertas.map((oferta) => {
                  const notificadoEn = oferta.notificado_en ? new Date(oferta.notificado_en) : null
                  const fechaHoraOferta = notificadoEn
                    ? `${notificadoEn.toLocaleDateString('es-AR')} a las ${notificadoEn.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}`
                    : '-'

                  return (
                    <div key={oferta.lista_espera_id} className="banner banner--info">
                      <div>
                        <strong>
                          Turno disponible para {oferta.actividad || 'Actividad'} el {oferta.fecha || '-'} de {oferta.horario_inicio || '--:--'} a {oferta.horario_fin || '--:--'}
                        </strong>
                        <div>Cancha: {oferta.cancha || '-'}</div>
                        <div>Ofertado el: {fechaHoraOferta}</div>
                      </div>
                      <div>
                        <button
                          type="button"
                          className="primary-action"
                          onClick={() => handleConfirmarTurno(oferta)}
                          disabled={confirmingId === oferta.lista_espera_id}
                        >
                          {confirmingId === oferta.lista_espera_id ? 'Confirmando...' : 'Confirmar turno'}
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : null}
             */}
           {/*
             <div className="mis-clases-table-wrapper">
                <h2> En lista de espera </h2>
                <table className="mis-clases-table">
                  <thead>
                    <tr>
                      <th scope="col">Actividad</th>
                      <th scope="col">Fecha</th>
                      <th scope="col">Horario</th>
                      <th scope="col">Cancha</th>
                      <th scope="col">Estado</th>
                      {/*<th scope="col">Posición</th>
                    </tr>
                  </thead>
                <tbody>
                  {listaEspera.length === 0 ? (
                    <tr>
                      <td className="mis-clases-table__empty" colSpan={8}>
                        Aún no hay clases en lista de espera.
                      </td>
                    </tr>   
                    ):(
                    listaEspera.map((item) => (
                      <tr key={`waitlist-${item.lista_espera_id}`}>
                        <td data-label="Actividad">{item.actividad || 'Actividad'}</td>
                        <td data-label="Fecha">{item.fecha || '-'}</td>
                        <td data-label="Horario">
                          {item.horario_inicio || '--:--'} - {item.horario_fin || '--:--'}
                        </td>
                        <td data-label="Cancha">{item.cancha || '-'}</td>
                        <td data-label="Estado">
                          <span className="badge badge--warning">
                            {item.estado === 'notificado' ? 'Turno disponible' : 'En espera'}
                          </span>
                        </td>
                        {/*<td data-label="Posición">{item.posicion ?? '-'}</td>
                      </tr>
                    ))
                  )} 
                </tbody>
              </table>
              </div>                
                   
            */}
            <div className="mis-clases-table-wrapper">
           {/* <h2>Reservadas</h2>  */}
            <table className="mis-clases-table">
              <thead>
                <tr>
                  <th scope="col">Actividad</th>
                  <th scope="col">Fecha</th>
                  <th scope="col">Horario</th>
                  <th scope="col">Cancha</th>
                  <th scope="col">Pago</th>
                  <th scope="col">Monto abonado</th>
                  <th scope="col">Reintegro estimado</th>
                  <th scope="col">Acciones</th>
                </tr>
              </thead>

              <tbody>
                {reservas.length === 0 ? (
                  <tr>
                    <td className="mis-clases-table__empty" colSpan={8}>
                      Aún no hay clases asociadas.
                    </td>
                  </tr>
                ) : (
                  reservas.map((reserva) => (
                    <tr key={reserva.reserva_id}>
                      <td data-label="Actividad">{reserva.actividad || 'Actividad'}</td>
                      <td data-label="Fecha">{reserva.fecha ? reserva.fecha.split('-').reverse().join('/') : ''}</td>
                      <td data-label="Horario" style={{ whiteSpace: 'nowrap' }}>
                        {reserva.horario_inicio || '--:--'} - {reserva.horario_fin || '--:--'}
                      </td>
                      <td data-label="Cancha">{reserva.cancha || '-'}</td>
                      <td data-label="Pago">{reserva.pago_estado || 'Sin pago'}</td>
                      <td data-label="Monto abonado">{renderMonto(reserva.monto_pagado)}</td>
                      <td data-label="Reintegro estimado">
                        {reserva.reintegro_aplica
                          ? renderMonto(reserva.reintegro_estimado)
                          : 'No aplica'}
                      </td>
                      <td data-label="Acciones">
                        <div className="mis-clases-table__actions">
                          {/*<button
                            type="button"
                            className="secondary-action"
                            onClick={() => handleAbandonarListaEspera(reserva)}
                          >
                            Abandonar lista de espera
                          </button>*/}

                          <button
                            type="button"
                            className="secondary-action"
                            onClick={() => handleGenerarQR(reserva)}
                          >
                            Generar QR
                          </button>

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
                  )
                )
              )}
              </tbody>
            </table>
            </div>
        </div>
        )}
      
      </section>
     </main>
     
  )
}

export default MisClasesPage
