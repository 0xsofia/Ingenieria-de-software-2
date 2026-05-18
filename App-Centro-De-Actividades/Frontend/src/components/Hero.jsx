import { NavLink } from 'react-router-dom'

import './Hero.css'

function Hero({ role, onLogout, isLoggingOut = false }) {
  const navigationItems = [
    { to: '/actividades', label: 'Actividades' },
    { to: '/verperfil', label: 'Ver Perfil' },
  ]

  if (role === 'administrador') {
    navigationItems.splice(1, 0, { to: '/usuarios', label: 'Usuarios' })
  }

  if (role === 'empleado') {
    navigationItems.splice(1, 0, { to: '/clases', label: 'Ver Clases' })
  }

  return (
    <header className="site-hero">
      <div className="site-hero__branding">
        <p className="auth-subtitle">Centro de actividades deportivas</p>
        <h1>CAD</h1>
      </div>

      <nav className="site-hero__nav" aria-label="Navegación principal">
        {navigationItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              isActive ? 'hero-link hero-link--active' : 'hero-link'
            }
          >
            {item.label}
          </NavLink>
        ))}

        <button
          type="button"
          className="site-hero__action"
          onClick={onLogout}
          disabled={isLoggingOut}
        >
          {isLoggingOut ? 'Cerrando sesión...' : 'Cerrar Sesión'}
        </button>
      </nav>
    </header>
  )
}

export default Hero
