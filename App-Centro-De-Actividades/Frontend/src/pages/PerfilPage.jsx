import { useNavigate } from 'react-router-dom'
import '../App.css'
import './PerfilPage.css'
import PerfilInfo from '../components/perfil/PerfilInfo'

function PerfilPage() {
  const navigate = useNavigate()

  return (
    <main className="dashboard-shell profile-shell">
      <section className="dashboard-frame profile-frame">
        <header className="dashboard-header profile-header">
          <h1>Mi perfil</h1>
          
        </header>

        <div className="profile-grid">
          <section className="profile-summary-card">
            <div className="profile-picture-card">
              <div className="profile-picture-placeholder">Foto de perfil</div>
              <button type="button" className="primary-action profile-update-button">
                Actualizar perfil
              </button>
            </div>

            <div className="profile-details">
              <h2>Datos personales</h2>
              <PerfilInfo hideRole />
            </div>
          </section>

          <section className="profile-actions-card">
            <h2>Accesos rápidos</h2>
            <div className="profile-actions">
              <button
                type="button"
                className="secondary-action"
                onClick={() => navigate('/mispagos')}
              >
                Mis pagos
              </button>
              <button type="button" className="secondary-action">Mis clases</button>
            </div>
          </section>
        </div>

        <section className="profile-description-card">
          <div className="section-heading">
            <h2>Descripción</h2>
          </div>
          <p className="profile-description-text">
            Lorem ipsum dolor sit, amet consectetur adipisicing elit. Minima, iste.
            Lorem ipsum, dolor sit amet consectetur adipisicing elit. Esse, ullam?
          </p>
        </section>
      </section>
    </main>
  )
}

export default PerfilPage;