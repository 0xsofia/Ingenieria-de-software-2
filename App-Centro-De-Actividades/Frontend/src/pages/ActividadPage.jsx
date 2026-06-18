import { useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'

import { entrarListaEspera, reservarAbonada, reservarEspontanea } from '../api/reservas'
import './ActividadPage.css'

export default function ActividadPage() {
  const { actividadName } = useParams()
  const location = useLocation()
  const clase = location.state?.clase
  const claseId = clase ? Number(clase.clase_id) : null
  const actividadTitle = formatActividadTitle(actividadName)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [abonadaSubmitting, setAbonadaSubmitting] = useState(false)
  const [requestError, setRequestError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [pendingWaitlistClaseId, setPendingWaitlistClaseId] = useState(null)

  async function handleReservar() {
    if (!clase || !Number.isFinite(claseId)) {
      setRequestError('Necesitás seleccionar una clase válida para reservar.')
      return
    }

    if (clase.ya_reservado) {
      setRequestError('')
      setSuccessMessage('Ya estás reservado en esta clase.')
      setPendingWaitlistClaseId(null)
      return
    }

    setIsSubmitting(true)
    setRequestError('')
    setSuccessMessage('')
    setPendingWaitlistClaseId(null)

    try {
      const result = await reservarEspontanea({ clase_id: claseId })

      if (result.status === 'no_cupo') {
        setSuccessMessage(result.message)
        setPendingWaitlistClaseId(claseId)
        return
      }

      if (result.status === 'payment_required' && result.payment_url) {
        window.location.assign(result.payment_url)
        return
      }

      if (result.status === 'reserved' || result.status === 'already_reserved') {
        setSuccessMessage(result.message)
        return
      }

      setSuccessMessage(result.message || 'Reserva procesada.')
      }  catch (error) {
        if (error?.data?.status === 'no_cupo') {
          setSuccessMessage(error?.data?.message)
          setPendingWaitlistClaseId(claseId)
          return
        }

        if (error?.data?.status === 'already_reserved') {
          setSuccessMessage(error?.data?.message)
          return
        }

        setRequestError(error?.data?.message || 'No se pudo realizar la reserva.')
      } finally {
        setIsSubmitting(false)
      }
  }

  async function handleReservarAbonada() {
    if (!clase || !Number.isFinite(claseId)) {
      setRequestError('Necesitás seleccionar una clase válida para reservar.')
      return
    }

    setAbonadaSubmitting(true)
    setRequestError('')
    setSuccessMessage('')
    setPendingWaitlistClaseId(null)

    try {
      const result = await reservarAbonada({ clase_id: claseId })

      if (result.status === 'payment_required' && result.payment_url) {
        window.location.assign(result.payment_url)
        return
      }

      if (result.status === 'reserved') {
        setSuccessMessage(result.message)
        return
      }

      setSuccessMessage(result.message || 'Reserva abonada procesada.')
    } catch (error) {
      setRequestError(error?.data?.message || 'No se pudo realizar la reserva abonada.')
    } finally {
      setAbonadaSubmitting(false)
    }
  }

  async function handleEntrarListaEspera() {
    if (!pendingWaitlistClaseId) return

    setIsSubmitting(true)
    setRequestError('')
    setSuccessMessage('')

    try {
      const result = await entrarListaEspera({ clase_id: pendingWaitlistClaseId })
      setSuccessMessage(result.message)
      setPendingWaitlistClaseId(null)
    } catch (error) {
      setRequestError(
        error?.data?.message || 'No se pudo ingresar a la lista de espera.'
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleCancelarListaEspera() {
    setPendingWaitlistClaseId(null)
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame actividad-placeholder-page">
        <div className="actividad-placeholder-page__top-link">
          <Link className="secondary-action" to="/actividades">
            Volver a actividades
          </Link>
        </div>

        <header className="dashboard-header actividad-placeholder-page__header">
          <p className="auth-subtitle">Reserva</p>
          <h1>{actividadTitle}</h1>
          <p className="dashboard-copy">
            Confirmá la clase seleccionada y avanzá con la reserva.
          </p>
        </header>

        <div className="actividad-placeholder-page__card">
          <h2>Clase seleccionada</h2>
          {clase ? (
            <dl className="actividad-placeholder-page__details">
              <div>
                <dt>Fecha</dt>
                <dd>{clase.fecha ? clase.fecha.split('-').reverse().join('/') : ''}</dd>
              </div>
              <div>
                <dt>Horario</dt>
                <dd>{clase.horario_inicio} - {clase.horario_fin}</dd>
              </div>
              <div>
                <dt>Profesor</dt>
                <dd>{clase.profesor_nombre || 'A confirmar'}</dd>
              </div>
              <div>
                <dt>Cupos</dt>
                <dd>{clase.cupos}</dd>
              </div>
              {clase.precio !== undefined && clase.precio !== null ? (
                <div>
                  <dt>Precio</dt>
                  <dd>$ {clase.precio}</dd>
                </div>
              ) : null}
            </dl>
          ) : (
            <p className="dashboard-copy">Todavía no hay una clase seleccionada para esta actividad.</p>
          )}

          {requestError ? (
            <p className="banner banner--error" role="alert">
              {requestError}
            </p>
          ) : null}

          {successMessage ? (
            <p className="dashboard-copy" role="status">
              {successMessage}
            </p>
          ) : null}

          {pendingWaitlistClaseId ? (
            <section className="test-credentials-card" aria-label="Sin cupo">
              <div className="section-heading">
                <h3>Sin cupo</h3>
                <p>
                  La clase se encuentra llena.
                  ¿Querés entrar a la lista de espera?
                </p>
              </div>

              <div className="role-grid">
                <button
                  type="button"
                  className="primary-action"
                  onClick={handleEntrarListaEspera}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Procesando...' : 'Entrar a lista de espera'}
                </button>
                <button
                  type="button"
                  className="hero-action"
                  onClick={handleCancelarListaEspera}
                  disabled={isSubmitting}
                >
                  Cancelar
                </button>
              </div>
            </section>
          ) : null}

          <div className="actividad-placeholder-page__actions">
            <button
              type="button"
              className="primary-action"
              onClick={handleReservar}
              disabled={isSubmitting || abonadaSubmitting || !clase}
            >
              {isSubmitting ? 'Procesando...' : 'Confirmar reserva'}
            </button>
            <button
              type="button"
              className="secondary-action"
              onClick={handleReservarAbonada}
              disabled={isSubmitting || abonadaSubmitting || !clase}
            >
              {abonadaSubmitting ? 'Procesando...' : 'Abonar reserva de 4 clases'}
            </button>
          </div>
        </div>
      </section>
    </section>
  )
}

function formatActividadTitle(slug) {
  return String(slug || 'actividad')
    .replace(/-/g, ' ')
    .split(' ')
    .filter(Boolean)
    .map((word) => word[0]?.toUpperCase() + word.slice(1))
    .join(' ')
}
