import '../App.css'
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
            <div className="profile-picture-card">
              <div className="profile-picture-placeholder">Foto de perfil</div>
              <button type="button" className="primary-action profile-update-button">
                Actualizar perfil
              </button>
            </div>

            <div className="profile-details">
              <h2>Datos del perfil</h2>
              <PerfilInfo hideRole />
            </div>
          </section>

          <section className="profile-actions-card">
            <h2>Accesos rápidos</h2>
            <div className="profile-actions">
              <button type="button" className="secondary-action">Mis pagos</button>
              <button type="button" className="secondary-action">Mis clases</button>
            </div>
          </section>
        </div>

        <section className="profile-description-card">
          <div className="section-heading">
            <h2>Descripción</h2>
            <p>Un texto de presentación que el cliente podrá editar más adelante.</p>
          </div>
          <p className="profile-description-text">
            Me interesa mantenerme activo y aprovechar las actividades deportivas que ofrece el
            centro. Esta descripción es un texto de ejemplo que se verá en la vista de perfil.
          </p>
        </section>
      </section>
    </main>
  )
}

export default PerfilPage;