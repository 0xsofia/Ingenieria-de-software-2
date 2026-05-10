function Hero({ onLogout, isLoggingOut = false }) {
  return (
    <header className="site-hero">
      <div>
        <p className="auth-subtitle">Centro de actividades deportivas</p>
      </div>

      <button
        type="button"
        className="hero-action"
        onClick={onLogout}
        disabled={isLoggingOut}
      >
        {isLoggingOut ? 'Cerrando sesión...' : 'Cerrar Sesión'}
      </button>
    </header>
  )
}

export default Hero
