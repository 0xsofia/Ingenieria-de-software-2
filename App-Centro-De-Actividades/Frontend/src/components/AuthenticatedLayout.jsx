import { startTransition, useEffect, useState } from 'react'
import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { cerrarSesion } from '../api/iniciar_sesion'
import { useAuth } from '../hooks/useAuth'
import { consumeFlashMessage } from '../utils/navigationFlash'
import Hero from './Hero.jsx'

function AuthenticatedLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { clearAuth, isAuthenticated, isBootstrapping } = useAuth()
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const [flashMessage, setFlashMessage] = useState('')

  useEffect(() => {
    const nextFlashMessage = location.state?.flashMessage || consumeFlashMessage()
    setFlashMessage(nextFlashMessage || '')
  }, [location.key, location.state])

  async function handleLogout() {
    setIsLoggingOut(true)

    try {
      const result = await cerrarSesion()
      clearAuth()
      startTransition(() => {
        navigate(result.redirect_to || '/login', { replace: true })
      })
    } catch {
      clearAuth()
      startTransition(() => {
        navigate('/login', { replace: true })
      })
    } finally {
      setIsLoggingOut(false)
    }
  }

  if (isBootstrapping) {
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

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="app-shell">
      <Hero onLogout={handleLogout} isLoggingOut={isLoggingOut} />
      {flashMessage ? (
        <section className="dashboard-shell">
          <section className="dashboard-frame dashboard-frame--compact">
            <p className="banner banner--success" role="status">
              {flashMessage}
            </p>
          </section>
        </section>
      ) : null}
      <Outlet />
    </div>
  )
}

export default AuthenticatedLayout
