import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { listarClases } from '../api/clase'
import FilterForm from '../components/listing/FilterForm'
import SectionedTableList from '../components/listing/SectionedTableList'
import { ACTIVIDADES } from '../constants/actividades'
import { useAuth } from '../hooks/useAuth'
import './ActividadesPage.css'

const INITIAL_FILTERS = Object.freeze({
  actividad: '',
  fecha: '',
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

export default function ActividadesPage() {
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
          setError('No se pudieron cargar las clases disponibles para reservar.')
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

  const clasesDisponibles = useMemo(
    () => clases.filter((clase) => isClaseDisponible(clase, currentTime)),
    [clases, currentTime]
  )

  const horarioOptions = useMemo(
    () => Array.from(new Set(clasesDisponibles.map((clase) => clase.horario_inicio))).sort(),
    [clasesDisponibles]
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
        name: 'fecha',
        label: 'Fecha',
        type: 'date',
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
    [horarioOptions]
  )

  const filteredClases = useMemo(() => {
    return clasesDisponibles.filter((clase) => {
      if (submittedFilters.actividad && clase.actividad !== submittedFilters.actividad) {
        return false
      }

      if (submittedFilters.fecha && clase.fecha !== submittedFilters.fecha) {
        return false
      }

      if (submittedFilters.horario && clase.horario_inicio !== submittedFilters.horario) {
        return false
      }

      return true
    })
  }, [clasesDisponibles, submittedFilters])

  const hasActiveFilters = Object.values(submittedFilters).some(Boolean)
  const canReserve = session?.role === 'socio'

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame actividades-page">
        <div className="actividades-page__header">
          <div>
            <p className="auth-subtitle">Reservas</p>
            <h1>Actividades y horarios</h1>
          </div>
        </div>

        <div className="actividades-page__content">
          <FilterForm
            title="Reserva tu próxima clase"
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
            <p className="dashboard-copy">Cargando actividades disponibles...</p>
          ) : (
            <>
              <div className="actividades-page__status-row">
                <p className="dashboard-copy">{filteredClases.length} clase(s) disponibles</p>
              </div>

              <SectionedTableList
                sections={[
                  {
                    key: 'actividades',
                    title: 'Clases para reservar',
                    items: filteredClases,
                    emptyMessage: hasActiveFilters
                      ? 'No hay horarios para el filtro aplicado.'
                      : 'Aún no hay clases disponibles para reservar.',
                  },
                ]}
                columns={[
                  {
                    key: 'actividad',
                    header: 'Actividad',
                    render: (clase) => (
                      <div className="sectioned-table-list__primary-cell">
                        <strong>{clase.actividad}</strong>
                        <span>{clase.nivel}</span>
                      </div>
                    ),
                  },
                  {
                    key: 'fecha',
                    header: 'Fecha',
                    render: (clase) => clase.fecha ? clase.fecha.split('-').reverse().join('/') : '',
                  },
                  {
                    key: 'horario',
                    header: 'Horario',
                    render: (clase) => `${clase.horario_inicio} - ${clase.horario_fin}`,
                  },
                  {
                    key: 'profesor_nombre',
                    header: 'Profesor',
                    render: (clase) => clase.profesor_nombre || 'A confirmar',
                  },
                  {
                    key: 'cupos',
                    header: 'Cupos',
                    render: (clase) => `${clase.cupos_ocupados || 0}/${clase.cupos}`,
                  },
                ]}
                getRowKey={(clase) => clase.clase_id}
                emptyMessage={
                  hasActiveFilters
                    ? 'No hay horarios para el filtro aplicado.'
                    : 'Aún no hay clases disponibles para reservar.'
                }
                renderActions={
                  canReserve
                    ? (clase) => (
                        <div className="sectioned-table-list__actions">
                          <Link
                            className="primary-action"
                            to={`/actividad/${getSlug(clase.actividad)}`}
                            state={{ clase }}
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

function getSlug(nombre) {
  return String(nombre)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
}

function isClaseDisponible(clase, currentTime) {
  if (!clase?.fecha || !clase?.horario_inicio) {
    return true
  }

  const currentDateTimeKey = getArgentinaDateTimeKey(currentTime)
  if (!currentDateTimeKey) {
    return true
  }

  return `${clase.fecha}T${clase.horario_inicio}:00` > currentDateTimeKey
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
