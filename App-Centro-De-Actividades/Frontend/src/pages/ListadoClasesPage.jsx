import { useEffect, useState } from 'react'
import { listarClases } from '../api/clase'
import ClaseCard from '../components/ClaseCard'
import { ActividadFilter } from '../components/ActividadFilter'
import { ACTIVIDADES } from '../constants/actividades'
import './ListadoClasesPage.css'

export default function ListadoClasesPage() {
  const [clases, setClases] = useState([])
  const [actividad, setActividad] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchClases = async () => {
      try {
        setLoading(true)
        const result = await listarClases(actividad)
        setClases(result)
        setError('')
      } catch (err) {
        console.error(err)
        setError('No se pudieron cargar las clases.')
      } finally {
        setLoading(false)
      }
    }

    fetchClases()
  }, [actividad])

  const handleViewClass = (clase) => {
    console.log('Ver clase:', clase)
  }

  const handleReserveClass = (clase) => {
    console.log('Reservar clase:', clase)
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame">
        <div className="listado-clases__header-row">
          <div>
            <h1>Clases disponibles</h1>
            <p className="dashboard-copy">Selecciona una actividad para filtrar las clases en el backend.</p>
          </div>
        </div>

        {loading ? (
          <p>Cargando clases...</p>
        ) : error ? (
          <p style={{ color: 'red' }}>{error}</p>
        ) : (
          <div className="listado-clases__controls">
            <ActividadFilter
              value={actividad}
              options={ACTIVIDADES}
              onChange={setActividad}
            />

            <div className="listado-clases__status-row">
              <p className="dashboard-copy">{clases.length} clase(s) encontradas</p>
            </div>

            {clases.length === 0 ? (
              <div className="listado-clases__empty">No hay clases que coincidan con la actividad seleccionada.</div>
            ) : (
              <div className="listado-clases__cards">
                {clases.map((clase) => (
                  <ClaseCard
                    key={clase.clase_id}
                    clase={clase}
                    onView={handleViewClass}
                    onReserve={handleReserveClass}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </section>
    </section>
  )
}
