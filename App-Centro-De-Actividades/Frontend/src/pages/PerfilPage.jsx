import { Link } from 'react-router-dom'
import './PerfilPage.css'
import PerfilInfo from '../components/perfil/PerfilInfo'
import { useAuth } from '../hooks/useAuth'
function PerfilPage() {
  const { session } = useAuth()
  
  return (
    <main className="dashboard-shell profile-shell">
      <section className="dashboard-frame profile-frame">
        <header className="dashboard-header profile-header">
          <h1>Mi perfil</h1>
        </header>

        <div className="profile-grid">
          <section className="profile-summary-card">
            <div className="profile-details">
              <h2>Datos personales</h2>
              <PerfilInfo />
            </div>
          </section>

          <section className="profile-actions-card">
            <div className="profile-actions-card__header">
              <h2>Accesos rápidos</h2>
              <Link className="secondary-action" to="/perfil/actualizar">
                Actualizar perfil
              </Link>
            </div>

            <div className="profile-actions">
              {session?.role === 'socio' && (
                <>
                  <Link className="secondary-action" to="/mis-pagos">
                    Mis pagos
                  </Link>
                  <Link className="secondary-action" to="/mis-clases">
                    Mis clases
                  </Link>
                </>
              )}
            </div>
          </section>
        </div>
      </section>
    </main>
  )
}

export default PerfilPage
