import { Link, Navigate, useLocation, useParams } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import './ActividadPage.css'

export default function ModificarClasePage() {
  const { session } = useAuth()
  const { claseId } = useParams()
  const location = useLocation()
  const clase = location.state?.clase

  if (session?.role !== 'empleado') {
    return <Navigate to="/inicio" replace />
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame actividad-placeholder-page">
        <div className="actividad-placeholder-page__top-link">
          <Link className="secondary-action" to="/clases">
            Volver a clases
          </Link>
        </div>

        <header className="dashboard-header actividad-placeholder-page__header">
          <p className="auth-subtitle">Gestión de clases</p>
          <h1>Modificar clase #{claseId}</h1>
          <p className="dashboard-copy">
            Esta vista queda conectada como placeholder para el flujo de modificación.
          </p>
        </header>

        <div className="actividad-placeholder-page__card">
          <h2>Resumen</h2>
          {clase ? (
            <dl className="actividad-placeholder-page__details">
              <div>
                <dt>Actividad</dt>
                <dd>{clase.actividad}</dd>
              </div>
              <div>
                <dt>Fecha</dt>
                <dd>{clase.fecha}</dd>
              </div>
              <div>
                <dt>Horario</dt>
                <dd>{clase.horario_inicio} - {clase.horario_fin}</dd>
              </div>
              <div>
                <dt>Profesor</dt>
                <dd>{clase.profesor_nombre || 'A confirmar'}</dd>
              </div>
            </dl>
          ) : (
            <p className="dashboard-copy">No hay datos precargados para esta clase todavía.</p>
          )}

          <div className="actividad-placeholder-page__actions">
            <button type="button" className="primary-action" disabled>
              Guardar cambios próximamente
            </button>
          </div>
        </div>
      </section>
    </section>
  )
}
