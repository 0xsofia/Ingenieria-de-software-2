import { startTransition, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { obtenerSesionActual } from '../api/iniciar_sesion'
import '../App.css'

function InicioPage() {
  const navigate = useNavigate()
  const [sessionData, setSessionData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    let ignore = false

    async function cargarSesion() {
      try {
        const result = await obtenerSesionActual()
        if (ignore) {
          return
        }

        if (!result.authenticated) {
          startTransition(() => {
            navigate('/', { replace: true })
          })
          return
        }

        setSessionData(result.session)
      } catch {
        if (!ignore) {
          setErrorMessage('No se pudo cargar la sesión actual.')
        }
      } finally {
        if (!ignore) {
          setIsLoading(false)
        }
      }
    }

    cargarSesion()

    return () => {
      ignore = true
    }
  }, [navigate])

  if (isLoading) {
    return (
      <main className="dashboard-shell">
        <section className="dashboard-frame dashboard-frame--compact">
          <p className="auth-subtitle">Cargando sesión</p>
          <h1>Preparando tu inicio</h1>
          <p className="dashboard-copy">Estamos verificando tu sesión activa.</p>
        </section>
      </main>
    )
  }

  if (errorMessage) {
    return (
      <main className="dashboard-shell">
        <section className="dashboard-frame dashboard-frame--compact">
          <p className="auth-subtitle">Error de sesión</p>
          <h1>No pudimos abrir el inicio</h1>
          <p className="banner banner--error">{errorMessage}</p>
        </section>
      </main>
    )
  }

  if (!sessionData) {
    return null
  }

  return (
    <main className="dashboard-shell">
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
            <dd>{sessionData.display_name}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{sessionData.email}</dd>
          </div>
          <div>
            <dt>Rol activo</dt>
            <dd>{sessionData.role_label}</dd>
          </div>
        </dl>

        <section className="dashboard-section">
          <div className="section-heading">
            <h2>Home</h2>
            <p>Contenido pendiente de implementación.</p>
          </div>
        </section>
      </section>
    </main>
  )
}

export default InicioPage
