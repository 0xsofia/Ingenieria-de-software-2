import { useMemo } from 'react'
import { useParams, useLocation } from 'react-router-dom'

function ActividadPage() {
  const params = useParams()
  const location = useLocation();
  const actividadId = location.state?.id;
  const actividadSlug = params.actividadName || ''

  const actividadTitle = useMemo(() => {
    const normalized = actividadSlug
      .replace(/-/g, ' ')
      .split(' ')
      .filter(Boolean)
      .map((word) => word[0]?.toUpperCase() + word.slice(1))
      .join(' ')

    return normalized || 'Actividad'
  }, [actividadSlug])

  return (
    <main className="dashboard-shell profile-shell">
      <section className="dashboard-frame profile-frame">
        <header className="dashboard-header profile-header">
          <h1>Actividad {actividadId}{actividadTitle}</h1>
        </header>
      </section>
    </main>
  )
}

export default ActividadPage
