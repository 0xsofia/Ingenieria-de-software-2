import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { listarClases } from '../api/clase'
import FilterForm from '../components/listing/FilterForm'
import SectionedTableList from '../components/listing/SectionedTableList'
import { ACTIVIDADES } from '../constants/actividades'
import { useAuth } from '../hooks/useAuth'
import { calcularPrecioAbonoConDescuento } from '../utils/abonos'
import './ActividadesPage.css'

const INITIAL_FILTERS = Object.freeze({
  actividad: '',
  mes: '',
  horario: '',
})

const ARGENTINA_TIMEZONE = 'America/Argentina/Buenos_Aires'
const argentinaDateTimeFormatter = new Intl.DateTimeFormat('sv-SE', {
  timeZone: ARGENTINA_TIMEZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
})

const monthFormatter = new Intl.DateTimeFormat('es-AR', {
  month: 'long',
  year: 'numeric',
})

const currencyFormatter = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
  minimumFractionDigits: 2,
})

export default function AbonosPage() {
  const { session } = useAuth()
  const [clases, setClases] = useState([])
  const [submittedFilters, setSubmittedFilters] = useState(INITIAL_FILTERS)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [currentTime, setCurrentTime] = useState(() => Date.now())

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setCurrentTime(Date.now())
    }, 60_000)

    return () => {
      window.clearInterval(intervalId)
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadClases() {
      setIsLoading(true)
      setError('')

      try {
        const result = await listarClases()
        if (!cancelled) {
          setClases(Array.isArray(result) ? result : [])
        }
      } catch {
        if (!cancelled) {
          setError('No se pudieron cargar las reservas abonadas disponibles.')
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadClases()

    return () => {
      cancelled = true
    }
  }, [])

  const abonosDisponibles = useMemo(
    () => buildAbonosMensuales(clases, currentTime),
    [clases, currentTime]
  )

  const horarioOptions = useMemo(
    () => Array.from(new Set(abonosDisponibles.map((abono) => abono.horario_inicio))).sort(),
    [abonosDisponibles]
  )

  const mesOptions = useMemo(
    () => Array.from(new Map(
      abonosDisponibles.map((abono) => [
        abono.mes,
        {
          value: abono.mes,
          label: formatMonthLabel(abono.mes),
        },
      ])
    ).values()),
    [abonosDisponibles]
  )

  const filterFields = useMemo(
    () => [
      {
        name: 'actividad',
        label: 'Actividad',
        type: 'select',
        placeholder: 'Todas las actividades',
        options: ACTIVIDADES,
      },
      {
        name: 'mes',
        label: 'Mes',
        type: 'select',
        placeholder: 'Todos los meses',
        options: mesOptions,
      },
      {
        name: 'horario',
        label: 'Horario',
        type: 'select',
        placeholder: 'Todos los horarios',
        options: horarioOptions.map((horario) => ({
          value: horario,
          label: horario,
        })),
      },
    ],
    [horarioOptions, mesOptions]
  )

  const filteredAbonos = useMemo(() => {
    return abonosDisponibles.filter((abono) => {
      if (submittedFilters.actividad && abono.actividad !== submittedFilters.actividad) {
        return false
      }

      if (submittedFilters.mes && abono.mes !== submittedFilters.mes) {
        return false
      }

      if (submittedFilters.horario && abono.horario_inicio !== submittedFilters.horario) {
        return false
      }

      return true
    })
  }, [abonosDisponibles, submittedFilters])

  const hasActiveFilters = Object.values(submittedFilters).some(Boolean)
  const canReserve = session?.role === 'socio'

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame actividades-page">
        <div className="actividades-page__header">
          <div>
            <p className="auth-subtitle">Reservas abonadas</p>
            <h1>Abonos mensuales</h1>
          </div>
        </div>

        <div className="actividades-page__content">
          <FilterForm
            title="Buscar abonos disponibles"
            description=""
            fields={filterFields}
            initialValues={submittedFilters}
            onSubmit={setSubmittedFilters}
            submitLabel="Filtrar"
            isSubmitting={isLoading}
          />

          {error ? (
            <p className="banner banner--error" role="alert">
              {error}
            </p>
          ) : null}

          {isLoading ? (
            <p className="dashboard-copy">Cargando abonos disponibles...</p>
          ) : (
            <>
              <div className="actividades-page__status-row">
                <p className="dashboard-copy">{filteredAbonos.length} abono(s) disponible(s)</p>
              </div>

              <SectionedTableList
                sections={[
                  {
                    key: 'abonos',
                    title: 'Clases mensuales para reservar',
                    items: filteredAbonos,
                    emptyMessage: hasActiveFilters
                      ? 'No hay abonos para el filtro aplicado.'
                      : 'Aún no hay abonos disponibles para reservar.',
                  },
                ]}
                columns={[
                  {
                    key: 'actividad',
                    header: 'Actividad',
                    render: (abono) => (
                      <div className="sectioned-table-list__primary-cell">
                        <strong>{abono.actividad}</strong>
                        <span>{abono.nivel}</span>
                      </div>
                    ),
                  },
                  {
                    key: 'mes',
                    header: 'Mes',
                    render: (abono) => formatMonthLabel(abono.mes),
                  },
                  {
                    key: 'dia_mes',
                    header: 'Día y mes',
                    render: (abono) => formatDiaMesLabel(abono.fechas[0]),
                  },
                  {
                    key: 'horario',
                    header: 'Horario',
                    render: (abono) => `${abono.horario_inicio} - ${abono.horario_fin}`,
                  },
                  {
                    key: 'profesor_nombre',
                    header: 'Profesor',
                    render: (abono) => abono.profesor_nombre || 'A confirmar',
                  },
                  {
                    key: 'cupos',
                    header: 'Cupos',
                    render: (abono) => `${abono.cupo_minimo_disponible} disponibles`,
                  },
                  {
                    key: 'precio_total',
                    header: 'Total',
                    render: (abono) => (
                      <PrecioAbono
                        precioTotal={abono.precio_total}
                        fechaClase={abono.fechas[0]}
                        session={session}
                      />
                    ),
                  },
                ]}
                getRowKey={(abono) => abono.key}
                emptyMessage={
                  hasActiveFilters
                    ? 'No hay abonos para el filtro aplicado.'
                    : 'Aún no hay abonos disponibles para reservar.'
                }
                renderActions={
                  canReserve
                    ? (abono) => (
                        <div className="sectioned-table-list__actions">
                          <Link
                            className="primary-action"
                            to={`/abonos/${getSlug(abono.actividad)}/reservar`}
                            state={{ abono, clase: abono.primera_clase }}
                          >
                            Reservar
                          </Link>
                        </div>
                      )
                    : undefined
                }
              />
            </>
          )}
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

function buildAbonosMensuales(clases, currentTime) {
  const currentDateTimeKey = getArgentinaDateTimeKey(currentTime)
  const clasesDisponibles = clases
    .filter((clase) => isClaseDisponible(clase, currentDateTimeKey))
    .filter((clase) => cuposDisponibles(clase) > 0)

  const grouped = new Map()

  for (const clase of clasesDisponibles) {
    const mes = getMonthKey(clase.fecha)
    const key = [
      mes,
      clase.actividad,
      clase.horario_inicio,
      clase.horario_fin,
      getWeekday(clase.fecha),
      clase.cancha,
      clase.nivel,
      clase.profesor_id,
    ].join('|')

    if (!grouped.has(key)) {
      grouped.set(key, [])
    }

    grouped.get(key).push(clase)
  }

  return Array.from(grouped.entries())
    .map(([key, group]) => buildAbonoFromGroup(key, group))
    .filter(Boolean)
    .sort((a, b) => {
      if (a.fechas[0] !== b.fechas[0]) {
        return a.fechas[0].localeCompare(b.fechas[0])
      }

      return a.horario_inicio.localeCompare(b.horario_inicio)
    })
}

function buildAbonoFromGroup(key, group) {
  const sortedGroup = [...group].sort((a, b) => a.fecha.localeCompare(b.fecha))
  const fechas = sortedGroup.map((clase) => clase.fecha)
  const windowStart = findConsecutiveMonthlyWindowStart(fechas)

  if (windowStart < 0) {
    return null
  }

  const clasesAbono = sortedGroup.slice(windowStart, windowStart + 4)

  return {
    key,
    actividad: clasesAbono[0].actividad,
    mes: getMonthKey(clasesAbono[0].fecha),
    fechas: clasesAbono.map((clase) => clase.fecha),
    horario_inicio: clasesAbono[0].horario_inicio,
    horario_fin: clasesAbono[0].horario_fin,
    cancha: clasesAbono[0].cancha,
    nivel: clasesAbono[0].nivel,
    profesor_nombre: clasesAbono[0].profesor_nombre,
    primera_clase: clasesAbono[0],
    cupo_minimo_disponible: Math.min(...clasesAbono.map(cuposDisponibles)),
    precio_total: clasesAbono.reduce((total, clase) => total + Number(clase.precio || 0), 0),
  }
}

function findConsecutiveMonthlyWindowStart(fechas) {
  for (let index = 0; index <= fechas.length - 4; index += 1) {
    const windowDates = fechas.slice(index, index + 4)
    const monthKey = getMonthKey(windowDates[0])
    const isSameMonth = windowDates.every((fecha) => getMonthKey(fecha) === monthKey)
    const isWeekly = windowDates.every((fecha, dateIndex) => {
      if (dateIndex === 0) {
        return true
      }

      return daysBetween(windowDates[dateIndex - 1], fecha) === 7
    })

    if (isSameMonth && isWeekly) {
      return index
    }
  }

  return -1
}

function isClaseDisponible(clase, currentDateTimeKey) {
  if (!clase?.fecha || !clase?.horario_inicio || !currentDateTimeKey) {
    return true
  }

  return `${clase.fecha}T${clase.horario_inicio}:00` > currentDateTimeKey
}

function cuposDisponibles(clase) {
  return Math.max(Number(clase.cupos || 0) - Number(clase.cupos_ocupados || 0), 0)
}

function daysBetween(previousDate, nextDate) {
  return Math.round((parseDateKey(nextDate) - parseDateKey(previousDate)) / 86_400_000)
}

function parseDateKey(dateKey) {
  const [year, month, day] = String(dateKey).split('-').map(Number)
  return new Date(year, month - 1, day)
}

function getMonthKey(dateKey) {
  return String(dateKey || '').slice(0, 7)
}

function getWeekday(dateKey) {
  return parseDateKey(dateKey).getDay()
}

function formatMonthLabel(monthKey) {
  const [year, month] = String(monthKey).split('-').map(Number)
  if (!year || !month) {
    return ''
  }

  return monthFormatter.format(new Date(year, month - 1, 1))
}

function formatDiaMesLabel(dateKey) {
  const date = parseDateKey(dateKey)
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

function getSlug(nombre) {
  return String(nombre)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
}

function getArgentinaDateTimeKey(currentTime) {
  const date = new Date(currentTime)
  if (Number.isNaN(date.getTime())) {
    return null
  }

  const parts = Object.fromEntries(
    argentinaDateTimeFormatter
      .formatToParts(date)
      .filter((part) => part.type !== 'literal')
      .map((part) => [part.type, part.value])
  )

  if (!parts.year || !parts.month || !parts.day || !parts.hour || !parts.minute || !parts.second) {
    return null
  }

  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:${parts.second}`
}
