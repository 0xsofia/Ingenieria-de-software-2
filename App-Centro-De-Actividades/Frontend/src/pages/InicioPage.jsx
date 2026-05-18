import { useEffect, useState } from 'react'

import { listarClases } from '../api/clase'
import { entrarListaEspera, reservarEspontanea } from '../api/reservas'
import '../App.css'
import { useAuth } from '../hooks/useAuth'
import './InicioPage.css'

function InicioPage() {
  const { session } = useAuth()
  const [clases, setClases] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [requestError, setRequestError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [pendingWaitlistClaseId, setPendingWaitlistClaseId] = useState(null)
  const [weekStart, setWeekStart] = useState(() => startOfWeekMonday(new Date()))

  const calendarModel = buildCalendarModel(clases, weekStart)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setIsLoading(true)
      setRequestError('')

      try {
        const items = await listarClases()
        if (cancelled) return
        setClases(items)

        const firstDate = items
          .map((item) => parseIsoDate(item.fecha))
          .filter(Boolean)
          .sort((a, b) => a.getTime() - b.getTime())[0]

        if (firstDate) {
          setWeekStart(startOfWeekMonday(firstDate))
        }
      } catch (error) {
        if (cancelled) return
        setRequestError(
          error?.data?.message || 'No pudimos cargar las clases disponibles.',
        )
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    load()

    return () => {
      cancelled = true
    }
  }, [])

  async function handleReservar(claseOrEvent) {
    const claseId = Number(
      typeof claseOrEvent === 'object' && claseOrEvent
        ? claseOrEvent.clase_id
        : claseOrEvent,
    )

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

      if (result.status === 'reserved') {
        setSuccessMessage(result.message)
        return
      }

      if (result.status === 'already_reserved') {
        setSuccessMessage(result.message)
        return
      }

      setSuccessMessage(result.message || 'Reserva procesada.')
    } catch (error) {
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
        error?.data?.message || 'No se pudo ingresar a la lista de espera.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleCancelarListaEspera() {
    setPendingWaitlistClaseId(null)
  }

  function handlePrevWeek() {
    setWeekStart((current) => addDays(current, -7))
  }

  function handleNextWeek() {
    setWeekStart((current) => addDays(current, 7))
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame">
        <header className="dashboard-header">
          <p className="auth-subtitle">Sesión activa</p>
          <h1>Bienvenido</h1>
          <p className="dashboard-copy">
            Consultá las clases disponibles y reservá desde el calendario.
          </p>
        </header>

        <dl className="session-summary" aria-label="Resumen de sesión actual">
          <div>
            <dt>Nombre</dt>
            <dd>{session.display_name}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{session.email}</dd>
          </div>
          <div>
            <dt>Rol activo</dt>
            <dd>{session.role_label}</dd>
          </div>
        </dl>

        <section className="dashboard-section">
          <div className="section-heading">
            <h2>Reservas espontáneas</h2>
            <p>Seleccioná una clase y presioná “reservar”.</p>

            <div className="calendar-nav" aria-label="Navegación de semanas">
              <button
                type="button"
                className="hero-action"
                onClick={handlePrevWeek}
                disabled={isLoading || isSubmitting}
                aria-label="Semana anterior"
              >
                ‹
              </button>
              <p className="calendar-nav__label">
                Semana {calendarModel.weekStartIso} – {calendarModel.weekEndIso}
              </p>
              <button
                type="button"
                className="hero-action"
                onClick={handleNextWeek}
                disabled={isLoading || isSubmitting}
                aria-label="Semana siguiente"
              >
                ›
              </button>
            </div>
          </div>

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
                  No hay más cupo en la clase seleccionada.
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

          {isLoading ? (
            <p className="dashboard-copy">Cargando clases...</p>
          ) : (
            <section className="calendar-wrapper" aria-label="Calendario de clases">
              {clases.length === 0 ? (
                <article className="backend-card">
                  <h3>Sin clases</h3>
                  <p>No hay clases cargadas aún.</p>
                </article>
              ) : (
                <>
                  {calendarModel.events.length === 0 ? (
                    <p className="dashboard-copy" role="status">
                      No hay clases en esta semana. Usá las flechas para cambiar de semana.
                    </p>
                  ) : null}
                  <div className="calendar-header" role="row">
                    <div className="calendar-header__time" aria-hidden="true" />
                    {calendarModel.days.map((day) => (
                      <div key={day.iso} className="calendar-header__day" role="columnheader">
                        <p className="auth-subtitle">{day.label}</p>
                        <p className="calendar-header__date">{day.iso}</p>
                      </div>
                    ))}
                  </div>

                  <div className="calendar-body">
                    <div className="calendar-time-column" aria-hidden="true">
                      {calendarModel.hours.map((hour) => (
                        <div key={hour} className="calendar-time-slot">
                          {String(hour).padStart(2, '0')}:00
                        </div>
                      ))}
                    </div>

                    <div className="calendar-days" role="rowgroup">
                      {calendarModel.days.map((day) => (
                        <div
                          key={day.iso}
                          className="calendar-day-column"
                          data-day={day.iso}
                        >
                          <div
                            className="calendar-day-grid"
                            style={{ height: calendarModel.totalHeight }}
                          >
                            {calendarModel.events
                              .filter((event) => event.dayIso === day.iso)
                              .map((event) => (
                                <button
                                  key={event.clase_id}
                                  type="button"
                                  className="calendar-event"
                                  style={{ top: event.top, height: event.height }}
                                  onClick={() => handleReservar(event)}
                                  disabled={isSubmitting}
                                >
                                  <strong className="calendar-event__title">
                                    {event.actividad || 'Clase'}
                                  </strong>
                                  <span className="calendar-event__meta">
                                    {event.horario_inicio} - {event.horario_fin}
                                  </span>
                                  <span className="calendar-event__meta">
                                    Cupos disponibles: {event.cupos}
                                  </span>
                                </button>
                              ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </section>
          )}
        </section>
      </section>
    </section>
  )
}

function buildCalendarModel(clases, weekStart) {
  const safeWeekStart = weekStart instanceof Date ? weekStart : startOfWeekMonday(new Date())
  const normalizedWeekStart = startOfWeekMonday(safeWeekStart)
  const weekEnd = addDays(normalizedWeekStart, 6)

  const days = buildWeekDaysFromStart(normalizedWeekStart)
  const daySet = new Set(days.map((day) => day.iso))

  const rawEvents = (Array.isArray(clases) ? clases : [])
    .map((item) => {
      const date = parseIsoDate(item.fecha)
      if (!date) return null

      const dayIso = formatIso(date)
      const start = parseTimeToMinutes(item.horario_inicio)
      const end = parseTimeToMinutes(item.horario_fin)

      if (!daySet.has(dayIso)) return null
      if (!Number.isFinite(start) || !Number.isFinite(end)) return null

      return {
        ...item,
        dayIso,
        _startMinutes: start,
        _endMinutes: end,
      }
    })
    .filter(Boolean)

  const startMinutes = rawEvents.map((event) => event._startMinutes)
  const endMinutes = rawEvents.map((event) => event._endMinutes)

  const earliest = startMinutes.length ? Math.min(...startMinutes) : 8 * 60
  const latest = endMinutes.length ? Math.max(...endMinutes) : 20 * 60

  const startHour = clamp(Math.floor(earliest / 60) - 1, 6, 20)
  const endHour = clamp(Math.ceil(latest / 60) + 1, startHour + 2, 23)

  const hours = []
  for (let hour = startHour; hour <= endHour; hour += 1) {
    hours.push(hour)
  }

  const hourHeight = 64
  const pxPerMinute = hourHeight / 60
  const totalHeight = (endHour - startHour + 1) * hourHeight

  const events = rawEvents
    .map((event) => {
      const top = (event._startMinutes - startHour * 60) * pxPerMinute
      const height = Math.max((event._endMinutes - event._startMinutes) * pxPerMinute, 28)

      return {
        ...event,
        top,
        height,
      }
    })
    .sort((a, b) => {
      if (a.dayIso !== b.dayIso) return a.dayIso.localeCompare(b.dayIso)
      return a._startMinutes - b._startMinutes
    })

  return {
    days,
    hours,
    events,
    totalHeight,
    weekStartIso: formatIso(normalizedWeekStart),
    weekEndIso: formatIso(weekEnd),
  }
}

function buildWeekDaysFromStart(weekStart) {
  const labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

  return labels.map((label, index) => {
    const date = addDays(weekStart, index)
    return {
      label,
      iso: formatIso(date),
    }
  })
}

function startOfWeekMonday(date) {
  const base = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()))
  const day = base.getUTCDay() // 0=Dom
  const diff = day === 0 ? -6 : 1 - day
  base.setUTCDate(base.getUTCDate() + diff)
  return base
}

function addDays(date, days) {
  const next = new Date(date)
  next.setUTCDate(next.getUTCDate() + days)
  return next
}

function parseIsoDate(value) {
  if (!value) return null
  if (typeof value !== 'string') return null

  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (!match) return null

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])

  if (!Number.isFinite(year) || !Number.isFinite(month) || !Number.isFinite(day)) {
    return null
  }

  const parsed = new Date(Date.UTC(year, month - 1, day))
  if (Number.isNaN(parsed.getTime())) return null
  return parsed
}

function formatIso(date) {
  return date.toISOString().slice(0, 10)
}

function parseTimeToMinutes(value) {
  if (!value || typeof value !== 'string') return NaN
  const [hours, minutes] = value.split(':').map((chunk) => Number(chunk))
  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) return NaN
  return hours * 60 + minutes
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

export default InicioPage
