import { Link } from 'react-router-dom'
import './PerfilPage.css'
import PerfilInfo from '../components/perfil/PerfilInfo'

function PerfilPage() {
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
            <h2>Accesos rápidos</h2>
            <div className="profile-actions">
              <Link className="secondary-action" to="/perfil/actualizar">
                Actualizar perfil
              </Link>
              <Link className="secondary-action" to="/mis-pagos">
                Mis pagos
              </Link>
              <button type="button" className="secondary-action">Mis clases</button>
            </div>
          </section>
        </div>
      </section>
    </main>
  )
}

export default PerfilPage
