import { useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'

import { reservarAbonada } from '../api/reservas'
import { useAuth } from '../hooks/useAuth'
import { calcularPrecioAbonoConDescuento } from '../utils/abonos'
import './ActividadPage.css'
import './ActividadesPage.css'

const currencyFormatter = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
  minimumFractionDigits: 2,
})

export default function RealizarReservaAbonadaPage() {
  const { session } = useAuth()
  const { actividadName } = useParams()
  const location = useLocation()
  const abono = location.state?.abono
  const clase = location.state?.clase || abono?.primera_clase
  const claseId = clase ? Number(clase.clase_id) : null
  const actividadTitle = formatActividadTitle(actividadName)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [requestError, setRequestError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const precioTotal = abono?.precio_total !== undefined
    ? Number(abono.precio_total)
    : clase?.precio !== undefined && clase?.precio !== null
    ? Number(clase.precio) * 4
    : null

  async function handleReservarAbonada() {
    if (!clase || !Number.isFinite(claseId)) {
      setRequestError('Necesitás seleccionar un abono válido para reservar.')
      return
    }

    setIsSubmitting(true)
    setRequestError('')
    setSuccessMessage('')

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
      setIsSubmitting(false)
    }
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame actividad-placeholder-page">
        <div className="actividad-placeholder-page__top-link">
          <Link className="secondary-action" to="/abonos">
            Volver a abonos
          </Link>
        </div>

        <header className="dashboard-header actividad-placeholder-page__header">
          <p className="auth-subtitle">Realizar reserva abonada</p>
          <h1>{actividadTitle}</h1>
          <p className="dashboard-copy">
            Confirmá el abono mensual de 4 clases consecutivas y avanzá con el pago.
          </p>
        </header>

        <div className="actividad-placeholder-page__card">
          <h2>Abono seleccionado</h2>
          {clase ? (
            <dl className="actividad-placeholder-page__details">
              <div>
                <dt>Día y mes</dt>
                <dd>{formatDiaMesLabel(clase.fecha)}</dd>
              </div>
              <div>
                <dt>Fechas</dt>
                <dd>{abono?.fechas?.length ? abono.fechas.map(formatDisplayDate).join(' · ') : formatDisplayDate(clase.fecha)}</dd>
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
                <dd>
                  {abono?.cupo_minimo_disponible !== undefined
                    ? `${abono.cupo_minimo_disponible} disponibles`
                    : clase.cupos}
                </dd>
              </div>
              <div>
                <dt>Total</dt>
                <dd>
                  {precioTotal !== null ? (
                    <PrecioAbono
                      precioTotal={precioTotal}
                      fechaClase={clase.fecha}
                      session={session}
                    />
                  ) : (
                    'A confirmar'
                  )}
                </dd>
              </div>
            </dl>
          ) : (
            <p className="dashboard-copy">Todavía no hay un abono seleccionado.</p>
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

          <div className="actividad-placeholder-page__actions">
            <button
              type="button"
              className="primary-action"
              onClick={handleReservarAbonada}
              disabled={isSubmitting || !clase}
            >
              {isSubmitting ? 'Procesando...' : 'Confirmar reserva abonada'}
            </button>
          </div>
        </div>
      </section>
    </section>
  )
}

function PrecioAbono({ precioTotal, fechaClase, session }) {
  const precio = calcularPrecioAbonoConDescuento(precioTotal, session, fechaClase)

  if (!precio.aplicaDescuento) {
    return currencyFormatter.format(precio.precioOriginal)
  }

  return (
    <div className="abono-price">
      <span className="abono-price__original">
        {currencyFormatter.format(precio.precioOriginal)}
      </span>
      <span className="abono-price__discounted">
        {currencyFormatter.format(precio.precioFinal)}
      </span>
      <span className="abono-price__tag">20% de descuento</span>
    </div>
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

function formatDiaMesLabel(dateKey) {
  const [year, month, day] = String(dateKey || '').split('-').map(Number)
  const date = new Date(year, month - 1, day)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('es-AR', {
      weekday: 'long',
      month: 'long',
      year: 'numeric',
    })
      .formatToParts(date)
      .filter((part) => part.type !== 'literal')
      .map((part) => [part.type, part.value])
  )

  return `los ${pluralizeWeekday(parts.weekday)} de ${parts.month}, ${parts.year}`
}

function pluralizeWeekday(weekday) {
  if (weekday === 'sábado') {
    return 'sábados'
  }

  if (weekday === 'domingo') {
    return 'domingos'
  }

  return weekday
}

function formatDisplayDate(dateKey) {
  const [year, month, day] = String(dateKey || '').split('-').map(Number)
  const date = new Date(year, month - 1, day)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  return new Intl.DateTimeFormat('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}
