import { useEffect, useState, startTransition } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import './PerfilPage.css'
import PerfilInfo from '../components/perfil/PerfilInfo'
import { useAuth } from '../hooks/useAuth'

function PerfilPage() {
  const { session } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [successMessage, setSuccessMessage] = useState(location.state?.flashMessage || '')

  useEffect(() => {
    const flashMessage = location.state?.flashMessage
    if (!flashMessage) {
      return
    }

    startTransition(() => {
      navigate(location.pathname, { replace: true, state: null })
    })
  }, [location.pathname, location.state, navigate])
  
  return (
    <main className="dashboard-shell profile-shell">
      <section className="dashboard-frame profile-frame">
        <header className="dashboard-header profile-header">
          <h1>Mi perfil</h1>
        </header>

        {successMessage ? (
          <div className="banner banner--success" role="status" style={{ marginBottom: '1.5rem' }}>
            {successMessage}
          <button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>
        ) : null}

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
              <Link className="secondary-action" to="/perfil/cambiar-contrasena" style={{ marginTop: '0.5rem' }}>
                Cambiar contraseña
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
