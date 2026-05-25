import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

import { obtenerConfirmacion, confirmarDesdeToken } from '../api/confirmaciones'
import './ActividadPage.css'

export default function ConfirmarTurnoPage() {
  const { token } = useParams()
  const navigate = useNavigate()
  const [oferta, setOferta] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isConfirming, setIsConfirming] = useState(false)

  useEffect(() => {
    cargarOferta()
  }, [token])

  async function cargarOferta() {
    setIsLoading(true)
    setError('')

    try {
      const data = await obtenerConfirmacion(token)
      if (data.status === 'ok') {
        setOferta(data)
      } else {
        setError(data.message || 'No se pudo cargar la oferta.')
      }
    } catch (err) {
      setError(err.data?.message || 'Error al cargar la oferta.')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleConfirmar() {
    if (!oferta) return

    setIsConfirming(true)
    setError('')

    try {
      const result = await confirmarDesdeToken(token)

      if (result.status === 'error') {
        setError(result.message || 'No se pudo confirmar el turno.')
      } else if (result.status === 'conflict') {
        setError(result.message || 'Ya posee una inscripción en ese horario.')
      } else if (result.status === 'confirmed') {
        // Redirigir a la página de actividad para completar la reserva
        const actividadSlug = getSlug(result.actividad)
        navigate(`/actividad/${actividadSlug}`, {
          state: {
            clase: {
              clase_id: result.clase_id,
              actividad: result.actividad,
              fecha: result.fecha,
              horario_inicio: result.horario_inicio,
              horario_fin: result.horario_fin,
              cancha: result.cancha,
            },
          },
        })
      }
    } catch (err) {
      setError(err.data?.message || 'Error al confirmar el turno.')
    } finally {
      setIsConfirming(false)
    }
  }

  function getSlug(text) {
    return String(text || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '')
  }

  if (isLoading) {
    return (
      <section className="dashboard-shell">
        <section className="dashboard-frame actividad-placeholder-page">
          <p className="dashboard-copy">Cargando oferta...</p>
        </section>
      </section>
    )
  }

  if (!oferta || error) {
    return (
      <section className="dashboard-shell">
        <section className="dashboard-frame actividad-placeholder-page">
          <header className="dashboard-header actividad-placeholder-page__header">
            <p className="auth-subtitle">Oferta de Turno</p>
            <h1>No disponible</h1>
          </header>

          {error && (
            <p className="banner banner--error" role="alert">
              {error}
            </p>
          )}

          <div className="actividad-placeholder-page__actions">
            <button
              type="button"
              className="secondary-action"
              onClick={() => navigate('/mis-clases')}
            >
              Volver a Mis Clases
            </button>
          </div>
        </section>
      </section>
    )
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame actividad-placeholder-page">
        <header className="dashboard-header actividad-placeholder-page__header">
          <p className="auth-subtitle">Oferta de Turno</p>
          <h1>{oferta.actividad}</h1>
          <p className="dashboard-copy">
            Tenés 15 minutos para confirmar. ¡No dejes pasar esta oportunidad!
          </p>
        </header>

        <div className="actividad-placeholder-page__card">
          <h2>Detalles de la clase</h2>
          {oferta ? (
            <dl className="actividad-placeholder-page__details">
              <div>
                <dt>Fecha</dt>
                <dd>{oferta.fecha}</dd>
              </div>
              <div>
                <dt>Horario</dt>
                <dd>{oferta.horario_inicio} - {oferta.horario_fin}</dd>
              </div>
              <div>
                <dt>Cancha</dt>
                <dd>{oferta.cancha || '-'}</dd>
              </div>
            </dl>
          ) : null}

          {error ? (
            <p className="banner banner--error" role="alert">
              {error}
            </p>
          ) : null}

          <div className="actividad-placeholder-page__actions">
            <button
              type="button"
              className="primary-action"
              onClick={handleConfirmar}
              disabled={isConfirming}
            >
              {isConfirming ? 'Confirmando...' : 'Confirmar Turno'}
            </button>
            <button
              type="button"
              className="secondary-action"
              onClick={() => navigate('/mis-clases')}
              disabled={isConfirming}
            >
              Cancelar
            </button>
          </div>
        </div>
      </section>
    </section>
  )
}
