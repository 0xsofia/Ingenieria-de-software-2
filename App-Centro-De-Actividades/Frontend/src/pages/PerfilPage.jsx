import './PerfilPage.css'
import PerfilInfo from '../components/perfil/PerfilInfo'
import PerfilUpdateForm from '../components/perfil/PerfilUpdateForm'

function PerfilPage() {
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
            </div>
            <div className="profile-details">
              <h2>Datos del perfil</h2>
              <PerfilInfo />
            </div>
          </section>

          <section className="profile-update-card">
            <PerfilUpdateForm />
          </section>
        </div>

        <section className="profile-actions-card">
          <h2>Accesos rápidos</h2>
          <div className="profile-actions">
            <button type="button" className="secondary-action">Mis pagos</button>
            <button type="button" className="secondary-action">Mis clases</button>
          </div>
        </section>
      </section>
    </main>
  )
}

export default PerfilPage
