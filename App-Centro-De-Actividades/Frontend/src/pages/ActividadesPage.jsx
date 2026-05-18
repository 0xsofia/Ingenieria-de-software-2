import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { obtenerActividades } from '../api/actividad'

function ActividadesPage() {
  const [actividades, setActividades] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    async function loadActividades() {
      try {
        const data = await obtenerActividades()
        if (!cancelled) {
          setActividades(data.actividades || [])
        }
      } catch (err) {
        if (!cancelled) {
          setError('No se pudieron cargar las actividades. Intente de nuevo.')
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadActividades()

    return () => {
      cancelled = true
    }
  }, [])

  function getSlug(nombre) {
    return String(nombre)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '')
  }

  return (
    <main className="dashboard-shell profile-shell">
      <section className="dashboard-frame profile-frame">
        <header className="dashboard-header profile-header">
          <h1>Actividades</h1>
        </header>

        {isLoading ? (
          <p>Cargando actividades...</p>
        ) : error ? (
          <p>{error}</p>
        ) : (
          <div className="profile-grid">
            {actividades.map((actividad) => {
              const slug = getSlug(actividad.nombre)
              return (
                <article key={actividad.actividad_id} className="profile-summary-card">
                  <h2>{actividad.nombre}</h2>
                  <Link className="primary-action" to={`/actividad/:${slug}`}state={{ id: actividad.actividad_id }}>
                    Ver actividad
                  </Link>
                </article>
              )
            })}
          </div>
        )}
      </section>
    </main>
  )
}

export default ActividadesPage
