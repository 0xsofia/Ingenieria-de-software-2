import { startTransition, useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'

import { cerrarSesion } from '../api/iniciar_sesion'
import '../App.css'
import Hero from './Hero.jsx'

function AuthenticatedLayout() {
  const navigate = useNavigate()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  async function handleLogout() {
    setIsLoggingOut(true)

    try {
      const result = await cerrarSesion()
      startTransition(() => {
        navigate(result.redirect_to || '/login', { replace: true })
      })
    } catch {
      startTransition(() => {
        navigate('/login', { replace: true })
      })
    } finally {
      setIsLoggingOut(false)
    }
  }

  return (
    <div className="app-shell">
      <Hero onLogout={handleLogout} isLoggingOut={isLoggingOut} />
      <Outlet />
    </div>
  )
}

export default AuthenticatedLayout
