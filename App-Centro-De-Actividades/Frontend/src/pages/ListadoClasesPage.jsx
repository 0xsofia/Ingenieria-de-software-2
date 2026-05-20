import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { listarClases } from '../api/clase'
import ClaseCard from '../components/ClaseCard'
import FilterForm from '../components/listing/FilterForm'
import { ACTIVIDADES } from '../constants/actividades'
import { useAuth } from '../hooks/useAuth'
import './ListadoClasesPage.css'

export default function ListadoClasesPage() {
  const navigate = useNavigate()
  const { session } = useAuth()
  const [clases, setClases] = useState([])
  const [filters, setFilters] = useState({
    actividad: '',
    fecha: '',
    horario: '',
  })
  const [submittedFilters, setSubmittedFilters] = useState({
    actividad: '',
    fecha: '',
    horario: '',
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const canManageClasses = session?.role === 'empleado'
  const hasActiveFilter = Object.values(submittedFilters).some(Boolean)

  const horarioOptions = useMemo(
    () => {
      const horas = []
      for (let i = 8; i <= 24; i++) {
        horas.push(`${String(i).padStart(2, '0')}:00`)
      }
      return horas
    },
    []
  )

  const filterFields = useMemo(
    () => [
      {
        name: 'actividad',
        label: 'Actividad',
        type: 'select',
        options: ACTIVIDADES,
        placeholder: 'Todas las actividades',
      },
      {
        name: 'fecha',
        label: 'Fecha',
        type: 'date',
        placeholder: 'Seleccionar fecha',
      },
      {
        name: 'horario',
        label: 'Horario',
        type: 'select',
        options: horarioOptions.map((horario) => ({
          value: horario,
          label: horario,
        })),
        placeholder: 'Todos los horarios',
      },
    ],
    [horarioOptions]
  )

  useEffect(() => {
    if (!canManageClasses) {
      return
    }

    const fetchClases = async () => {
      try {
        setLoading(true)
        const result = await listarClases(submittedFilters)
        setClases(result)
        setError('')
      } catch {
        setError('No se pudieron cargar las clases.')
      } finally {
        setLoading(false)
      }
    }

    fetchClases()
  }, [submittedFilters, canManageClasses])

  if (!canManageClasses) {
    return <Navigate to="/inicio" replace />
  }

  function handleViewClass(clase) {
    navigate(`/clases/${clase.clase_id}/modificar`, { state: { clase } })
  }

  function handleEditClass(clase) {
    navigate(`/clases/${clase.clase_id}/modificar`, { state: { clase } })
  }

  function handleScanQR(clase) {
    navigate(`/clases/${clase.clase_id}/qr`, { state: { clase } })
  }

  function handleFilterSubmit(values) {
    setFilters(values)
    setSubmittedFilters(values)
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame">
        <div className="listado-clases__header-row">
          <div>
            <p className="auth-subtitle">Gestión de clases</p>
            <h1>Ver clases</h1>
            {/* <p className="dashboard-copy">
              Revisá las clases creadas, filtrá por actividad y avanzá al flujo de modificación.
            </p> */}
          </div>

          <div className="listado-clases__actions">
            <Link className="primary-action" to="/clases/crear">
              Crear clase
            </Link>
            <Link className="secondary-action" to="/profesor/crear">
              Crear profesor
            </Link>
          </div>
        </div>

        {loading ? (
          <p>Cargando clases...</p>
        ) : error ? (
          <p className="banner banner--error" role="alert">{error}</p>
        ) : (
          <div className="listado-clases__controls">
            <FilterForm
              title="Buscar clases"
              description=""
              fields={filterFields}
              initialValues={filters}
              onSubmit={handleFilterSubmit}
              submitLabel="Filtrar"
            />

            <div className="listado-clases__status-row">
              <p className="dashboard-copy">{clases.length} clase(s) encontradas</p>
            </div>

            {clases.length === 0 ? (
              <div className="listado-clases__empty">
                {hasActiveFilter
                  ? 'Sin resultados para los filtros aplicados.'
                  : 'No se encontraron clases registradas.'}
              </div>
            ) : (
              <div className="listado-clases__cards">
                {clases.map((clase) => (
                  <ClaseCard
                    key={clase.clase_id}
                    clase={clase}
                    onView={handleViewClass}
                    onReserve={handleEditClass}
                    onScanQR={handleScanQR}
                    viewScanLabel="Escanear QR"
                    viewLabel="Ver detalle"
                    reserveLabel="Modificar"
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </section>
    </section>
  )
}
