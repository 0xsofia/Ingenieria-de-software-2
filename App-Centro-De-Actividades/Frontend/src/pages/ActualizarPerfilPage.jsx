import './PerfilPage.css'
import PerfilUpdateForm from '../components/perfil/PerfilUpdateForm'

function ActualizarPerfilPage() {
  return (
    <main className="dashboard-shell profile-shell">
      <section className="dashboard-frame profile-frame">
        <header className="dashboard-header profile-header">
          <h1>Actualizar perfil</h1>
        </header>

        <section className="profile-update-card">
          <PerfilUpdateForm />
        </section>
      </section>
    </main>
  )
}

export default ActualizarPerfilPage
