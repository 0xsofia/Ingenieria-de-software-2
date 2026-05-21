import { Link } from 'react-router-dom'

import logoCad from '../assets/Logo CAD.png'
import { useAuth } from '../hooks/useAuth'
import './InicioPage.css'

function InicioPage() {
  const { session } = useAuth()
  const canReserve = session?.role === 'socio'

  return (
    <section className="dashboard-shell home-landing-shell">
      <section className="dashboard-frame home-landing-frame">
        <div className="home-landing-grid">
          <div className="home-landing-copy">
            <p className="auth-subtitle">Centro de actividades deportivas</p>
            <h1>Probando el cicd</h1>
            <p className="home-landing-lead">
              Reserva tu clase hoy, encontrá horarios disponibles y seguí de cerca las
              actividades del centro en un solo lugar.
            </p>

            {canReserve ? (
              <div className="home-landing-actions">
                <Link className="primary-action" to="/actividades">
                  Reservar clase
                </Link>
              </div>
            ) : null}

            <p className="home-landing-footnote">
              CAD © {new Date().getFullYear()} · Reserva tu clase hoy y mantené tu rutina en movimiento.
            </p>
          </div>

          <div className="home-landing-brand-panel" aria-hidden="true">
            <img className="home-landing-logo" src={logoCad} alt="" />
          </div>
        </div>
      </section>
    </section>
  )
}

export default InicioPage
