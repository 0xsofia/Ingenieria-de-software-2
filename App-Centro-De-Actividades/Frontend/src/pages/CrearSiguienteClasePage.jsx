import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { extenderClasesSiguienteMes } from '../api/clase'
import { useAuth } from '../hooks/useAuth'
import { redirectTo } from '../services/redirectTo'
import './ActividadPage.css'

const MESES = [
  { label: 'Enero', value: 1 },
  { label: 'Febrero', value: 2 },
  { label: 'Marzo', value: 3 },
  { label: 'Abril', value: 4 },
  { label: 'Mayo', value: 5 },
  { label: 'Junio', value: 6 },
  { label: 'Julio', value: 7 },
  { label: 'Agosto', value: 8 },
  { label: 'Septiembre', value: 9 },
  { label: 'Octubre', value: 10 },
  { label: 'Noviembre', value: 11 },
  { label: 'Diciembre', value: 12 },
]

export default function ExtenderClasesPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated, isBootstrapping, session } = useAuth()
  const [generalError, setGeneralError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Extraemos la clase enviada desde la tarjeta
  const { clase } = location.state || {}

  // Calculamos mes de origen y de destino
  const mesesCalculados = useMemo(() => {
    if (!clase?.fecha) return { origen: '', destino: '' }
    const partes = clase.fecha.split('-')
    if (partes.length < 2) return { origen: '', destino: '' }
    
    const origenNum = Number(partes[1])
    const destinoNum = (origenNum % 12) + 1 // Si es 12 (Diciembre), pasa a 1 (Enero)
    
    const origenLabel = MESES.find(m => m.value === origenNum)?.label || ''
    const destinoLabel = MESES.find(m => m.value === destinoNum)?.label || ''
    
    return { origen: origenLabel, destino: destinoLabel, destinoNum }
  }, [clase])

  useEffect(() => {
    if (!isBootstrapping && !isAuthenticated) {
      redirectTo(navigate, '/login')
    }
  }, [isAuthenticated, isBootstrapping, navigate])

  // Redirección de seguridad si no hay datos de clase
  if (!clase && !isBootstrapping && isAuthenticated) {
    return <Navigate to="/clases" replace />
  }

  async function handleConfirmExtend() {
    setGeneralError('')
    setIsSubmitting(true)

    try {
      const result = await extenderClasesSiguienteMes({
        clase_id: clase.clase_id,
        mes: mesesCalculados.destinoNum, // Enviamos directamente el número del nuevo mes
      })

      redirectTo(navigate, result.redirect_to || '/clases', {
        flashMessage: result.message || `La clase fue extendida a ${mesesCalculados.destino} con éxito.`,
      })
    } catch (error) {
      setGeneralError(error?.data?.message || 'No se pudo extender la clase.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isBootstrapping) {
    return (
      <main className="auth-shell">
        <section className="auth-frame auth-frame--compact">
          <header className="auth-header">
            <p className="auth-subtitle">Extender Agenda</p>
            <h1>Centro de actividades deportivas</h1>
          </header>
          <p className="dashboard-copy">Estamos cargando los datos.</p>
        </section>
      </main>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (session?.role !== 'empleado') {
    return <Navigate to="/inicio" replace />
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame dashboard-frame--compact">
        <div className="actividad-placeholder-page__top-link">
          <Link className="secondary-action" to="/clases">
            Volver a clases
          </Link>
        </div>

        <header className="dashboard-header">
          <p className="auth-subtitle">Clonación de planificación</p>
          <h1>Confirmar extensión de clase</h1>
        </header>

        {/* Bloque Destacado del nuevo mes */}
        <div style={{
          backgroundColor: 'var(--primary-light, #eef2ff)', 
          borderLeft: '4px solid var(--primary-color, #4f46e5)',
          padding: '1.25rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          textAlign: 'center'
        }}>
          <p style={{ margin: 0, fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#555' }}>
            Nueva planificación para
          </p>
          <h2 style={{ margin: '0.25rem 0 0 0', fontSize: '2rem', color: 'var(--primary-color, #4f46e5)', fontWeight: 'bold' }}>
            {mesesCalculados.destino}
          </h2>
        </div>

        {/* Ficha técnica de la clase origen de donde se copian los datos */}
        <div style={{
          backgroundColor: '#f9fafb',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '1.25rem',
          marginBottom: '1.5rem'
        }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem' }}>
            Datos base de la clase
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.95rem' }}>
            <div>
              <strong style={{ color: '#666' }}>Actividad:</strong>
              <p style={{ margin: '0.25rem 0 0 0', fontWeight: '500' }}>{clase?.actividad}</p>
            </div>
            <div>
              <strong style={{ color: '#666' }}>Tipo / Nivel:</strong>
              <p style={{ margin: '0.25rem 0 0 0', fontWeight: '500' }}>{clase?.tipo_clase} · {clase?.nivel}</p>
            </div>
            <div>
              <strong style={{ color: '#666' }}>Horario habitual:</strong>
              <p style={{ margin: '0.25rem 0 0 0', fontWeight: '500' }}>{clase?.horario_inicio} a {clase?.horario_fin} hs</p>
            </div>
            <div>
              <strong style={{ color: '#666' }}>Profesor:</strong>
              <p style={{ margin: '0.25rem 0 0 0', fontWeight: '500' }}>{clase?.profesor_nombre || 'Asignado'}</p>
            </div>
            <div>
              <strong style={{ color: '#666' }}>Cancha:</strong>
              <p style={{ margin: '0.25rem 0 0 0', fontWeight: '500' }}>{clase?.cancha}</p>
            </div>
            <div>
              <strong style={{ color: '#666' }}>Mes de origen:</strong>
              <p style={{ margin: '0.25rem 0 0 0', fontWeight: '500' }}>{mesesCalculados.origen} ({clase?.fecha?.split('-').reverse().join('/')})</p>
            </div>
          </div>
        </div>

        <p style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: '1.5rem' }}>
          Al continuar, se replicará este espacio en todos los días correspondientes del mes de {mesesCalculados.destino} y se migrarán las configuraciones de alumnos inscritos si corresponde.
        </p>

        {/* Sección de errores generales del backend */}
        {generalError && (
          <div className="error-message" style={{ marginBottom: '1rem', color: '#dc2626' }}>
            {generalError}
          </div>
        )}

        {/* Botonera con el mismo estilo del kit */}
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>

          <button
            type="button"
            className="primary-action"
            onClick={handleConfirmExtend}
            disabled={isSubmitting}
            style={{ minWidth: '200px' }}
          >
            {isSubmitting ? 'Procesando...' : 'Crear clases'}
          </button>
        </div>
      </section>
    </section>
  )
}