import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { listarClases } from '../api/clase'
import ClaseCard from '../components/ClaseCard'
import { ActividadFilter } from '../components/ActividadFilter'
import { ACTIVIDADES } from '../constants/actividades'
import { useAuth } from '../hooks/useAuth'
import './ListadoClasesPage.css'

export default function ListadoClasesPage() {
  const navigate = useNavigate()
  const { session } = useAuth()
  const [clases, setClases] = useState([])
  const [actividad, setActividad] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const canManageClasses = session?.role === 'empleado'

  useEffect(() => {
    if (!canManageClasses) {
      return
    }

    const fetchClases = async () => {
      try {
        setLoading(true)
        const result = await listarClases(actividad)
        setClases(result)
        setError('')
      } catch {
        setError('No se pudieron cargar las clases.')
      } finally {
        setLoading(false)
      }
    }

    fetchClases()
  }, [actividad, canManageClasses])

  if (!canManageClasses) {
    return <Navigate to="/inicio" replace />
  }

  function handleViewClass(clase) {
    navigate(`/clases/${clase.clase_id}/modificar`, { state: { clase } })
  }

  function handleEditClass(clase) {
    navigate(`/clases/${clase.clase_id}/modificar`, { state: { clase } })
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame">
        <div className="listado-clases__header-row">
          <div>
            <p className="auth-subtitle">Gestión de clases</p>
            <h1>Ver clases</h1>
            <p className="dashboard-copy">
              Revisá las clases creadas, filtrá por actividad y avanzá al flujo de modificación.
            </p>
          </div>

          <Link className="primary-action" to="/clases/crear">
            Crear clase
          </Link>
        </div>

        {loading ? (
          <p>Cargando clases...</p>
        ) : error ? (
          <p className="banner banner--error" role="alert">{error}</p>
        ) : (
          <div className="listado-clases__controls">
            <ActividadFilter value={actividad} options={ACTIVIDADES} onChange={setActividad} />

            <div className="listado-clases__status-row">
              <p className="dashboard-copy">{clases.length} clase(s) encontradas</p>
            </div>

            {clases.length === 0 ? (
              <div className="listado-clases__empty">
                No hay clases que coincidan con la actividad seleccionada.
              </div>
            ) : (
              <div className="listado-clases__cards">
                {clases.map((clase) => (
                  <ClaseCard
                    key={clase.clase_id}
                    clase={clase}
                    onView={handleViewClass}
                    onReserve={handleEditClass}
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
