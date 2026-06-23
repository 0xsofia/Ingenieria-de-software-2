import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'

import {
  cancelarReservaAbonada,
  cancelarReservaEspontanea,
  listarMisClases,
  renovarAbonoMensual,
  obtenerOfertasActivas,
  confirmarTurno,
  abandonarListaEspera,
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
  const [renewingAbonoId, setRenewingAbonoId] = useState(null)
  const [pendingCancelReserva, setPendingCancelReserva] = useState(null)
  const [ofertas, setOfertas] = useState([])
  const [abonos, setAbonos] = useState([])
  const [confirmingId, setConfirmingId] = useState(null)
  const [abandoningId, setAbandoningId] = useState(null)
  const [currentDate] = useState(() => new Date())

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
    // espera: recibe un objeto de lista de espera
    if (!reserva?.lista_espera_id) return

    setError('')
    setFeedback('')

    setAbandoningId(reserva.lista_espera_id)

    abandonarListaEspera({ lista_espera_id: reserva.lista_espera_id })
      .then((result) => {
        if (result && result.status === 'ok') {
          setFeedback(result.message || 'Se abandono la lista de espera existosamente')
          fetchReservas()
        } else {
          setError(result?.message || 'No se pudo abandonar la lista de espera.')
        }
      })
      .catch((err) => {
        setError(err.data?.message || 'No se pudo abandonar la lista de espera.')
      })
      .finally(() => setAbandoningId(null))
  }

  function handleGenerarQR(reserva) {
    if (!reserva?.reserva_id) return

    setError('')
    navigate(`/reservas/${reserva.reserva_id}/qr`)
  }

  async function fetchReservas() {
    setIsLoading(true)
    setError('')

    try {
      const data = await listarMisClases()
      setReservas(data.reservas || [])
      setListaEspera(data.lista_espera || [])
      setAbonos(data.abonos || [])
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

  useEffect(() => {
    async function fetchAll() {
      await fetchReservas()
      await fetchOfertas()
    }

    fetchAll()
  }, [])

  async function handleCancelarReserva(reserva) {
    if (!reserva?.reserva_id) return

    setPendingCancelReserva(reserva)
  }

  function handleCloseCancelModal() {
    if (cancelingId) return

    setPendingCancelReserva(null)
  }

  async function handleConfirmCancelReserva() {
    if (!pendingCancelReserva?.reserva_id) return

    setCancelingId(pendingCancelReserva.reserva_id)
    setError('')
    setFeedback('')

    try {
      const cancelarReserva = pendingCancelReserva.tipo_reserva === 'abonada'
        ? cancelarReservaAbonada
        : cancelarReservaEspontanea

      const result = await cancelarReserva({
        reserva_id: pendingCancelReserva.reserva_id,
        confirmar_sancion: Boolean(pendingCancelReserva.requiereConfirmarSancion),
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
      if (result.credito?.aplica) {
        message += ' Se acredito una clase a favor.'
      } else if (result.credito && !result.credito.aplica) {
        message += ' No recibiras credito por esta cancelacion.'
      }

      if (!result.scenario_message && result.sancion_aplicada) {
        message += ' Se aplico una sancion por cancelaciones repetidas.'
      }

      setFeedback(message)
      setPendingCancelReserva(null)
      await fetchReservas()
      await fetchOfertas()
    } catch (err) {
      if (err.data?.status === 'requires_sanction_confirmation') {
        setPendingCancelReserva((current) => ({
          ...current,
          requiereConfirmarSancion: true,
          sancionMessage: err.data.message,
        }))
        setError('')
        return
      }

      setError(err.data?.message || 'No se pudo cancelar la reserva.')
    } finally {
      setCancelingId(null)
    }
  }

  async function handleRenovarAbono(abono) {
    if (!abono?.abono_mensual_id || !abono.renovable) {
      return
    }

    setError('')
    setFeedback('')
    setRenewingAbonoId(abono.abono_mensual_id)

    try {
      const result = await renovarAbonoMensual({ abono_mensual_id: abono.abono_mensual_id })
      setFeedback(result.message || 'Abono mensual renovado.')
      await fetchReservas()
    } catch (err) {
      setError(err.data?.message || 'No se pudo renovar el abono mensual.')
    } finally {
      setRenewingAbonoId(null)
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

  const isAbonoExpired = (abono) => {
    if (!abono?.fecha_limite_renovacion) return false

    const limite = new Date(`${abono.fecha_limite_renovacion}T23:59:59`)
    return currentDate > limite
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
          <div>
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

            <div className="mis-clases-table-wrapper">
              <h2>Abonos Mensuales</h2>
              <table className="mis-clases-table">
                <thead>
                  <tr>
                    <th scope="col">Actividad</th>
                    <th scope="col">Inicio y Fin</th>
                    <th scope="col">Hora</th>
                    <th scope="col">Día</th>
                    <th scope="col">Fecha Lim. Renovación</th>
                    <th scope="col">Renovación</th>
                  </tr>
                </thead>
                <tbody>
                  {abonos.length === 0 ? (
                    <tr>
                      <td className="mis-clases-table__empty" colSpan={6}>
                        Aún no hay abonos mensuales registrados.
                      </td>
                    </tr>
                  ) : (
                    abonos.map((abono) => (
                      <tr key={`abono-${abono.abono_mensual_id}`}>
                        <td data-label="Actividad">{abono.actividad || '-'}</td>
                        <td data-label="Inicio y Fin">
                          {abono.periodo_inicio ? abono.periodo_inicio.split('-').reverse().join('/') : '-'} - {abono.periodo_fin ? abono.periodo_fin.split('-').reverse().join('/') : '-'}
                        </td>
                        <td data-label="Hora">{abono.hora_inicio || '--:--'}</td>
                        <td data-label="Día">{abono.dia_semana || '-'}</td>
                        <td data-label="Fecha Lim. Renovación">
                          {abono.fecha_limite_renovacion ? abono.fecha_limite_renovacion.split('-').reverse().join('/') : '-'}
                        </td>
                        <td data-label="Acción">
                          <div className="mis-clases-table__actions">
                            <button
                              type="button"
                              className="primary-action"
                              onClick={() => handleRenovarAbono(abono)}
                              disabled={isAbonoExpired(abono) || !abono.renovable || renewingAbonoId === abono.abono_mensual_id}
                            >
                              {renewingAbonoId === abono.abono_mensual_id
                                ? 'Renovando...'
                                : isAbonoExpired(abono)
                                ? 'Expirado'
                                : 'Renovar'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="mis-clases-table-wrapper">
              <h2>En lista de espera</h2>
              <table className="mis-clases-table">
                <thead>
                  <tr>
                    <th scope="col">Actividad</th>
                    <th scope="col">Fecha</th>
                    <th scope="col">Horario</th>
                    <th scope="col">Cancha</th>
                    <th scope="col">Estado</th>
                    <th scope="col">Posición</th>
                    <th scope="col">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {listaEspera.length === 0 ? (
                    <tr>
                      <td className="mis-clases-table__empty" colSpan={7}>
                        Aún no hay clases en lista de espera.
                      </td>
                    </tr>   
                  ) : (
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
                        <td data-label="Posición">{item.posicion ?? '-'}</td>
                        <td data-label="Accion">
                          <button
                            type="button"
                            className="secondary-action"
                            onClick={() => handleAbandonarListaEspera(item)}
                            disabled={abandoningId === item.lista_espera_id}
                          >
                            {abandoningId === item.lista_espera_id ? 'Abandonando...' : 'Abandonar'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )} 
                </tbody>
              </table>
            </div>                
                   
            <div className="mis-clases-table-wrapper">
              <h2>Reservadas</h2>
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
                                : reserva.tipo_reserva === 'abonada'
                                  ? 'Cancelar reserva abonada'
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
          </div>
        )}

        {pendingCancelReserva
          ? createPortal(
              <div className="mis-clases-modal" role="presentation">
                <div className="mis-clases-modal__backdrop" onClick={handleCloseCancelModal} />
                <section
                  className="mis-clases-modal__dialog"
                  role="dialog"
                  aria-modal="true"
                  aria-labelledby="cancelar-reserva-title"
                >
                  <h2 id="cancelar-reserva-title">Confirmar cancelacion</h2>
                  {pendingCancelReserva.requiereConfirmarSancion ? (
                    <p>
                      {pendingCancelReserva.sancionMessage ||
                        'Esta cancelacion aplica una sancion y perderas el descuento del abono del mes siguiente.'}
                    </p>
                  ) : pendingCancelReserva.tipo_reserva === 'abonada' ? (
                    <p>
                      ¿Seguro que quiere cancelar la reserva abonada?
                    </p>
                  ) : (
                    <p>¿Seguro que quiere cancelar la reserva?</p>
                  )}
                  <div className="mis-clases-modal__actions">
                    <button
                      type="button"
                      className="secondary-action"
                      onClick={handleCloseCancelModal}
                      disabled={Boolean(cancelingId)}
                    >
                      Cancelar
                    </button>
                    <button
                      type="button"
                      className="primary-action"
                      onClick={handleConfirmCancelReserva}
                      disabled={Boolean(cancelingId)}
                    >
                      {cancelingId
                        ? 'Cancelando...'
                        : pendingCancelReserva.requiereConfirmarSancion
                          ? 'Confirmar sancion'
                          : 'Aceptar'}
                    </button>
                  </div>
                </section>
              </div>,
              document.body,
            )
          : null}
       
      </section>
    </main>
  )
}

export default MisClasesPage
