import { useState } from 'react'
import { NavLink } from 'react-router-dom'

import logoCad from '../assets/logo-cad.png'

function Hero({ role, onLogout, isLoggingOut = false }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const navigationItems = [
    { to: '/inicio', label: 'Inicio' },
    { to: '/actividades', label: 'Actividades' },
    { to: '/verperfil', label: 'Ver Perfil' },
  ]

  if (role === 'administrador') {
    navigationItems.splice(1, 0, { to: '/usuarios', label: 'Usuarios' })
    navigationItems.splice(2, 0, { to: '/pagos', label: 'Pagos' })  
  }

  if (role === 'empleado') {
    navigationItems.splice(1, 0, { to: '/clases', label: 'Ver Clases' })
    navigationItems.splice(2, 0, { to: '/profesores', label: 'Ver profesores' })
  }

  if (role === 'socio') {
    navigationItems.splice(2, 0, { to: '/abonos', label: 'Abonos' })
    navigationItems.splice(2, 0, { to: '/mis-clases', label: 'Mis clases' })
  }

  function closeMenu() {
    setIsMenuOpen(false)
  }

  function handleLogoutClick() {
    closeMenu()
    onLogout()
  }

  const navigationItemClassName = ({ isActive }) => {
    const baseClassName =
      'inline-flex min-h-[46px] items-center justify-center border border-white/20 px-4 py-3 text-sm font-semibold uppercase tracking-[0.18em] text-slate-50 transition duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-200/70'

    return isActive
      ? `${baseClassName} bg-white/18`
      : `${baseClassName} bg-white/6 hover:bg-white/12`
  }

  return (
    <header className="border-b border-slate-950/15 bg-[linear-gradient(125deg,#0f2236_0%,#14324f_42%,#1f5d91_100%)] text-slate-50 shadow-[0_24px_72px_-42px_rgba(2,8,23,0.95)]">
      <div className="flex w-full flex-col gap-4 px-3 py-2 sm:px-4 sm:py-3 lg:flex-row lg:items-center lg:justify-between lg:gap-6 lg:px-6 xl:px-8">
        <div className="flex w-full items-center justify-between gap-4 lg:w-auto lg:items-center lg:justify-start">
          <NavLink
            to="/inicio"
            className="inline-flex items-center justify-start transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-200/70"
            onClick={closeMenu}
            aria-label="Ir al inicio"
          >
            <img
              src={logoCad}
              alt="Centro de Actividades Deportivas"
              className="block h-[4.75rem] w-auto object-contain sm:h-[5.6rem] lg:h-[6.5rem]"
            />
          </NavLink>

          <button
            type="button"
            className="inline-flex h-11 w-11 shrink-0 self-center items-center justify-center border border-white/20 bg-white/8 text-slate-50 transition hover:bg-white/12 lg:hidden"
            aria-expanded={isMenuOpen}
            aria-controls="site-navigation"
            aria-label={isMenuOpen ? 'Cerrar menú principal' : 'Abrir menú principal'}
            onClick={() => setIsMenuOpen((currentState) => !currentState)}
          >
            <span className="sr-only">Menú principal</span>
            <span className="relative flex h-4 w-5 flex-col justify-between">
              <span
                className={`block h-px w-full bg-current transition duration-200 ${
                  isMenuOpen ? 'translate-y-[7px] rotate-45' : ''
                }`}
              />
              <span
                className={`block h-px w-full bg-current transition duration-200 ${
                  isMenuOpen ? 'opacity-0' : 'opacity-100'
                }`}
              />
              <span
                className={`block h-px w-full bg-current transition duration-200 ${
                  isMenuOpen ? '-translate-y-[7px] -rotate-45' : ''
                }`}
              />
            </span>
          </button>
        </div>

        <nav
          id="site-navigation"
          className={`${
            isMenuOpen ? 'grid' : 'hidden'
          } w-full gap-3 border-t border-white/12 pt-4 lg:ml-auto lg:flex lg:w-auto lg:flex-wrap lg:items-center lg:justify-end lg:border-t-0 lg:pt-0`}
          aria-label="Navegación principal"
        >
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={navigationItemClassName}
              onClick={closeMenu}
            >
              {item.label}
            </NavLink>
          ))}

          <button
            type="button"
            className="inline-flex min-h-[46px] items-center justify-center border border-sky-200/30 bg-slate-950/18 px-4 py-3 text-sm font-semibold uppercase tracking-[0.18em] text-slate-50 transition duration-200 hover:bg-slate-950/28 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-200/70"
            onClick={handleLogoutClick}
            disabled={isLoggingOut}
          >
            {isLoggingOut ? 'Cerrando sesión...' : 'Cerrar sesión'}
          </button>
        </nav>
      </div>
    </header>
  )
}

export default Hero
