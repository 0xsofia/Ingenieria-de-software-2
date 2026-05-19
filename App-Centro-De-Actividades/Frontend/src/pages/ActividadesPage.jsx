import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { listarClases } from '../api/clase'
import FilterForm from '../components/listing/FilterForm'
import SectionedTableList from '../components/listing/SectionedTableList'
import { ACTIVIDADES } from '../constants/actividades'
import './ActividadesPage.css'

const INITIAL_FILTERS = Object.freeze({
  actividad: '',
  dia: '',
  horario: '',
})

const WEEKDAY_FORMATTER = new Intl.DateTimeFormat('es-AR', {
  weekday: 'long',
})

export default function ActividadesPage() {
  const [clases, setClases] = useState([])
  const [submittedFilters, setSubmittedFilters] = useState(INITIAL_FILTERS)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

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

  const horarioOptions = useMemo(
    () => Array.from(new Set(clases.map((clase) => clase.horario_inicio))).sort(),
    [clases]
  )

  const diaOptions = useMemo(
    () =>
      Array.from(new Set(clases.map((clase) => clase.fecha)))
        .sort()
        .map((fecha) => ({
          value: fecha,
          label: formatClaseDate(fecha),
        })),
    [clases]
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
        name: 'dia',
        label: 'Día',
        type: 'select',
        placeholder: 'Todos los días',
        options: diaOptions,
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
    [diaOptions, horarioOptions]
  )

  const filteredClases = useMemo(() => {
    return clases.filter((clase) => {
      if (submittedFilters.actividad && clase.actividad !== submittedFilters.actividad) {
        return false
      }

      if (submittedFilters.dia && clase.fecha !== submittedFilters.dia) {
        return false
      }

      if (submittedFilters.horario && clase.horario_inicio !== submittedFilters.horario) {
        return false
      }

      return true
    })
  }, [clases, submittedFilters])

  const hasActiveFilters = Object.values(submittedFilters).some(Boolean)

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
            description="Usá estos filtros para encontrar la clase que querés reservar."
            fields={filterFields}
            initialValues={submittedFilters}
            onSubmit={setSubmittedFilters}
            submitLabel="Aplicar filtros"
            resetLabel="Limpiar"
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
                      ? 'No hay clases para el filtro aplicado.'
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
                    render: (clase) => formatClaseDate(clase.fecha),
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
                  },
                ]}
                getRowKey={(clase) => clase.clase_id}
                emptyMessage={
                  hasActiveFilters
                    ? 'No hay clases para el filtro aplicado.'
                    : 'Aún no hay clases disponibles para reservar.'
                }
                renderActions={(clase) => (
                  <div className="sectioned-table-list__actions">
                    <Link
                      className="primary-action"
                      to={`/actividad/${getSlug(clase.actividad)}`}
                      state={{ clase }}
                    >
                      Reservar
                    </Link>
                  </div>
                )}
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

function formatClaseDate(value) {
  const [year, month, day] = String(value)
    .split('-')
    .map((part) => Number(part))

  const date = new Date(year, month - 1, day)
  const weekday = WEEKDAY_FORMATTER.format(date)

  return `${capitalize(weekday)} ${day}`
}

function capitalize(value) {
  return value.charAt(0).toUpperCase() + value.slice(1)
}
