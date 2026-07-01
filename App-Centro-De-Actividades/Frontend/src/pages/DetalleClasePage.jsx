import { useEffect, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'

import { obtenerDetalleClase } from '../api/clase'
import { registrarAsistenciaManual } from '../api/asistencias'
import { useAuth } from '../hooks/useAuth'
import './DetalleClasePage.css'

export default function DetalleClasePage() {
  const navigate = useNavigate()
  const { claseId } = useParams()
  const { session } = useAuth()
  const [clase, setClase] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [registrandoAsistencia, setRegistrandoAsistencia] = useState(null)
  const [dniFilter, setDniFilter] = useState('')
  const [submittedDniFilter, setSubmittedDniFilter] = useState('')

  const canManageClasses = session?.role === 'empleado'
  const hasActiveFilter = Boolean(submittedDniFilter)

  const fetchDetalle = async (dni = '') => {
    try {
      setLoading(true)
      setError('')
      const result = await obtenerDetalleClase(claseId, dni)
      setClase(result)
    } catch (err) {
      setError(err.data?.message || 'No se pudo cargar el detalle de la clase.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!canManageClasses) {
      return
    }

    fetchDetalle()
  }, [claseId, canManageClasses])

  if (!canManageClasses) {
    return <Navigate to="/inicio" replace />
  }

  async function handleRegistrarAsistencia(socio, reservaId) {
    try {
      setRegistrandoAsistencia(reservaId)
      setSuccess('')
      setError('')

      await registrarAsistenciaManual(reservaId)

      setSuccess(`Asistencia registrada.`)
      setClase((prevClase) => ({
        ...prevClase,
        socios: prevClase.socios.map((s) =>
          s.reserva_id === reservaId
            ? { ...s, asistencia_registrada: true, estado_reserva: 'asistio' }
            : s
        ),
      }))
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(err.data?.message || 'Error al registrar asistencia.')
    } finally {
      setRegistrandoAsistencia(null)
    }
  }

  async function handleBuscarPorDNI(event) {
    event.preventDefault()
    const dniValue = dniFilter.trim()
    setSubmittedDniFilter(dniValue)
    await fetchDetalle(dniValue)
  }


  function handleVolver() {
    navigate('/clases')
  }

  const emptyMessage = hasActiveFilter
    ? 'Sin resultados para el filtro aplicado.'
    : 'Aún no hay socios registrados para la clase.'

  if (loading) {
    return (
      <section className="dashboard-shell">
        <section className="dashboard-frame">
          <p>Cargando detalle de la clase...</p>
        </section>
      </section>
    )
  }

  if (!clase) {
    return (
      <section className="dashboard-shell">
        <section className="dashboard-frame">
          <div className="banner banner--error">No se encontró la clase.<button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>
          <button onClick={handleVolver} className="secondary-action">
            Volver
          </button>
        </section>
      </section>
    )
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame detalle-clase-frame">
        <div className="detalle-clase__header">
          <button onClick={handleVolver} className="back-button">
            ← Volver
          </button>
          <div>
            <p className="auth-subtitle">Listado de asistencias</p>
            <h1>{clase.actividad}</h1>
          </div>
        </div>

        {error && <div className="banner banner--error" role="alert">{error}<button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>}
        {success && <div className="banner banner--success" role="alert">{success}<button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>}

        <div className="detalle-clase__info">
          <div className="detalle-clase__info-grid">
            <div className="info-item">
              <label>Fecha</label>
              <p>{clase.fecha}</p>
            </div>
            <div className="info-item">
              <label>Horario</label>
              <p>
                {clase.horario_inicio} - {clase.horario_fin}
              </p>
            </div>
            <div className="info-item">
              <label>Cancha</label>
              <p>{clase.cancha}</p>
            </div>
            <div className="info-item">
              <label>Nivel</label>
              <p>{clase.nivel}</p>
            </div>
            <div className="info-item">
              <label>Profesor</label>
              <p>{clase.profesor_nombre}</p>
            </div>
            <div className="info-item">
              <label>Cupos</label>
              <p>
                {clase.cupos_ocupados} / {clase.cupos}
              </p>
            </div>
            <div className="info-item">
              <label>Precio</label>
              <p>
                {clase.precio
                  ? new Intl.NumberFormat('es-AR', {
                      style: 'currency',
                      currency: 'ARS',
                    }).format(clase.precio)
                  : 'N/A'}
              </p>
            </div>
          </div>
        </div>

        <section className="detalle-clase__controls">
          <form className="detalle-clase__filter-form" onSubmit={handleBuscarPorDNI}>
            <div className="filter-field">
              <label htmlFor="dni">Filtrar por DNI</label>
              <input
                id="dni"
                value={dniFilter}
                onChange={(event) => setDniFilter(event.target.value)}
                placeholder="Ingrese DNI"
              />
            </div>
            <div className="filter-actions">
              <button type="submit" className="primary-action" disabled={loading}>
                Filtrar
              </button>
            </div>
          </form>
        </section>

        <div className="detalle-clase__socios">
          <h2>Listado de asistencias</h2>

          {clase.socios.length === 0 ? (
            <p className="detalle-clase__empty">{emptyMessage}</p>
          ) : (
            <div className="detalle-clase__table-wrapper">
              <table className="detalle-clase__table">
                <thead>
                  <tr>
                    <th>Nombre y apellido</th>
                    <th>DNI</th>
                    <th>Email</th>
                    <th>Teléfono</th>
                    <th>Estado reserva</th>
                    <th>Asistencia</th>
                  </tr>
                </thead>
                <tbody>
                  {clase.socios.map((socio) => (
                    <tr key={socio.reserva_id}>
                      <td>{socio.nombre_completo}</td>
                      <td>{socio.dni}</td>
                      <td>{socio.email}</td>
                      <td>{socio.telefono}</td>
                      <td>{socio.estado_reserva}</td>
                      <td>
                        <button
                          type="button"
                          className="btn-registrar-asistencia"
                          onClick={() => handleRegistrarAsistencia(socio, socio.reserva_id)}
                          disabled={socio.asistencia_registrada || registrandoAsistencia === socio.reserva_id}
                        >
                          {socio.asistencia_registrada
                            ? 'Asistencia registrada'
                            : registrandoAsistencia === socio.reserva_id
                            ? 'Registrando...'
                            : 'Registrar asistencia'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </section>
  )
}
