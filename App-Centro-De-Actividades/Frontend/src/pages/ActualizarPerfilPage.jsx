import { Link } from 'react-router-dom'

import './PerfilPage.css'
import PerfilUpdateForm from '../components/perfil/PerfilUpdateForm'

function ActualizarPerfilPage() {
  return (
    <main className="dashboard-shell profile-shell">
      <section className="dashboard-frame profile-frame">
        <header className="dashboard-header profile-header profile-header-row">
          <h1>Actualizar perfil</h1>
          <Link className="secondary-action" to="/verperfil">
            Volver al perfil
          </Link>
        </header>

        <section className="profile-update-card">
          <PerfilUpdateForm />
        </section>
      </section>
    </main>
  )
}

export default ActualizarPerfilPage
