import { useAuth } from '../hooks/useAuth'
import './InicioPage.css'

function InicioPage() {
  const { session } = useAuth()

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame">
        <header className="dashboard-header">
          <p className="auth-subtitle">Sesión activa</p>
          <h1>Bienvenido</h1>
          <p className="dashboard-copy">
            Esta página es un scaffold inicial para la vista `/inicio`.
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
            <h2>Home</h2>
            <p className="inicio-placeholder">Contenido pendiente de implementación.</p>
          </div>
        </section>
      </section>
    </section>
  )
}

export default InicioPage
