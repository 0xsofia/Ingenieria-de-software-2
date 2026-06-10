import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { obtenerProfesores } from '../api/profesor'
import { useAuth } from '../hooks/useAuth'

export default function ListadoProfesoresPage() {
  const { session } = useAuth()
  const [profesores, setProfesores] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (session?.role !== 'empleado') {
      return
    }

    const fetchProfesores = async () => {
      try {
        setLoading(true)
        const result = await obtenerProfesores()
        setProfesores(result || [])
        setError('')
      } catch (err) {
        console.error(err)
        setError('No se pudieron cargar los profesores.')
      } finally {
        setLoading(false)
      }
    }

    fetchProfesores()
  }, [session])

  if (session?.role !== 'empleado') {
    return <Navigate to="/inicio" replace />
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame">
        <div className="listado-clases__header-row">
          <div>
            <h1>Listado de profesores</h1>

          </div>

          <div className="listado-clases__actions">
            <Link className="primary-action" to="/profesor/crear">
              Crear profesor
            </Link>
          </div>
        </div>

        {loading ? (
          <p>Cargando profesores...</p>
        ) : error ? (
          <p className="banner banner--error" role="alert">{error}</p>
        ) : (
          <div className="mis-clases-table-wrapper">
            <table className="mis-clases-table">
              <thead>
                <tr>
                  <th scope="col">Nombre</th>
                  <th scope="col">DNI</th>
                  <th scope="col">Teléfono</th>
                </tr>
              </thead>
              <tbody>
                {profesores.length === 0 ? (
                  <tr>
                    <td className="mis-clases-table__empty" colSpan={3}>
                      Aún no se registraron profesores.
                    </td>
                  </tr>
                ) : (
                  profesores.map((profesor) => (
                    <tr key={profesor.id}>
                      <td data-label="Nombre">{profesor.nombre}</td>
                      <td data-label="DNI">{profesor.dni}</td>
                      <td data-label="Teléfono">{profesor.telefono}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  )
}
