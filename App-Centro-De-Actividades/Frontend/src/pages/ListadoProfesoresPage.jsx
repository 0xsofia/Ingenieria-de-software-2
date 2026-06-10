import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { obtenerProfesores, eliminarProfesor } from '../api/profesor'
import { useAuth } from '../hooks/useAuth'

export default function ListadoProfesoresPage() {
  const { session } = useAuth()
  const [profesores, setProfesores] = useState([])
  const [loading, setLoading] = useState(true)
  
  const [errorCarga, setErrorCarga] = useState('')
  const [errorAccion, setErrorAccion] = useState('')
  const [feedback, setFeedback] = useState('')
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    if (session?.role !== 'empleado') {
      return
    }

    const fetchProfesores = async () => {
      try {
        setLoading(true)
        const result = await obtenerProfesores()
        setProfesores(result || [])
        setErrorCarga('')
      } catch (err) {
        console.error(err)
        setErrorCarga('No se pudieron cargar los profesores.')
      } finally {
        setLoading(false)
      }
    }

    fetchProfesores()
  }, [session])

  if (session?.role !== 'empleado') {
    return <Navigate to="/inicio" replace />
  }

  async function handleEliminarProfesor(profesor) {
    setErrorAccion('')
    setFeedback('')
    setDeletingId(profesor.id)

    try {
      const result = await eliminarProfesor(profesor.id)
      if (result?.status === 'ok') {
        setFeedback(result.message || 'Profesor eliminado correctamente')
        const updated = await obtenerProfesores()
        setProfesores(updated || [])
      } else {
        //aca se guarda el mensaje del back El profesor tiene clases registradas, no se puede eliminar
        setErrorAccion(result?.message || 'No se pudo eliminar el profesor.')
      }
    } catch (err) {
      setErrorAccion(err.data?.message || 'No se pudo eliminar el profesor.')
    } finally {
      setDeletingId(null)
    }
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
        ) : errorCarga ? (
          <p className="banner banner--error" role="alert">{errorCarga}</p>
        ) : (
          <div>
            {feedback ? (
              <p className="banner banner--success" role="status">{feedback}</p>
            ) : null}

            {errorAccion ? (
              <p className="banner banner--error" role="alert">{errorAccion}</p>
            ) : null}

            <div className="mis-clases-table-wrapper">
              <table className="mis-clases-table">
                <thead>
                  <tr>
                    <th scope="col">Nombre</th>
                    <th scope="col">DNI</th>
                    <th scope="col">Teléfono</th>
                    <th scope="col">Accion</th>
                  </tr>
                </thead>
                <tbody>
                  {profesores.length === 0 ? (
                    <tr>
                      <td className="mis-clases-table__empty" colSpan={4}>
                        Aún no se registraron profesores.
                      </td>
                    </tr>
                  ) : (
                    profesores.map((profesor) => (
                      <tr key={profesor.id}>
                        <td data-label="Nombre">{profesor.nombre}</td>
                        <td data-label="DNI">{profesor.dni}</td>
                        <td data-label="Teléfono">{profesor.telefono}</td>
                        <td data-label="Accion">
                          <button
                            type="button"
                            className="secondary-action"
                            onClick={() => handleEliminarProfesor(profesor)}
                            disabled={deletingId === profesor.id}
                          >
                            {deletingId === profesor.id ? 'Eliminando...' : 'Eliminar'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </section>
  )
}