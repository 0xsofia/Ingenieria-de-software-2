import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate, useParams } from 'react-router-dom'
import { z } from 'zod'

import DynamicForm2 from '../components/forms/DynamicForm2'
import { actualizarClase, obtenerDetalleClase, obtenerProfesores, cancelarClase } from '../api/clase'
import { useAuth } from '../hooks/useAuth'
import { redirectTo } from '../services/redirectTo'
import { ACTIVIDADES } from '../constants/actividades'
const NIVELES = ['Principiante', 'Intermedio', 'Avanzado']
import './ActividadPage.css'

const HORARIOS = Array.from({ length: 24 }, (_, hour) => ({
  value: String(hour),
  label: `${String(hour).padStart(2, '0')}:00`,
}))

export default function ModificarClasePage() {
  const { session, isAuthenticated, isBootstrapping } = useAuth()
  const navigate = useNavigate()
  const { claseId } = useParams()
  const location = useLocation()
  const claseState = location.state?.clase
  const returnTo = getReturnTo(location)

  const [clase, setClase] = useState(claseState || null)
  const [profesores, setProfesores] = useState([])
  const [loading, setLoading] = useState(!claseState)
  const [loadingProfesores, setLoadingProfesores] = useState(true)
  const [initialValues, setInitialValues] = useState({
    actividad: '',
    fecha: '',
    horario_inicio: '',
    cancha: '',
    nivel: '',
    cupos: 1,
    precio: 1,
    profesor_id: '',
  })
  const [serverErrors, setServerErrors] = useState({})
  const [generalError, setGeneralError] = useState('')
  const [errorCycle, setErrorCycle] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!isBootstrapping && !isAuthenticated) {
      redirectTo(navigate, '/login')
    }
  }, [isAuthenticated, isBootstrapping, navigate])

  useEffect(() => {
    const cargarDatos = async () => {
      if (claseState) {
        setClase(claseState)
        setLoading(false)
      }

      try {
        const [detalle, listaProfesores] = await Promise.all([
          obtenerDetalleClase(claseId),
          obtenerProfesores(),
        ])

        setClase(detalle)
        setProfesores(listaProfesores)
        setInitialValues({
          actividad: detalle.actividad || '',
          fecha: detalle.fecha || '',
          // extraer la hora (ej. "11:00" -> "11") para que coincida con los valores de `HORARIOS`
          horario_inicio: detalle.horario_inicio
            ? String(Number(String(detalle.horario_inicio).split(':')[0]))
            : '',
          cancha: detalle.cancha || '',
          nivel: detalle.nivel || '',
          cupos: detalle.cupos || 1,
          precio: detalle.precio ?? 1,
          profesor_id: String(detalle.profesor_id || ''),
        })
        setGeneralError('')
      } catch (error) {
        console.error('Error al cargar la clase para modificar:', error)
        setGeneralError(error?.data?.message || 'No se pudo cargar la clase.')
      } finally {
        setLoading(false)
        setLoadingProfesores(false)
      }
    }

    if (isAuthenticated) {
      cargarDatos()
    }
  }, [claseId, claseState, isAuthenticated])

  useEffect(() => {
    if (clase) {
      setInitialValues({
        actividad: clase.actividad || '',
        fecha: clase.fecha || '',
        // extraer la hora para preseleccionar correctamente en el selector
        horario_inicio: clase.horario_inicio
          ? String(Number(String(clase.horario_inicio).split(':')[0]))
          : '',
        cancha: clase.cancha || '',
        nivel: clase.nivel || '',
        cupos: clase.cupos || 1,
        precio: clase.precio ?? 1,
        profesor_id: String(clase.profesor_id || ''),
      })
    }
  }, [clase])

  const modificarClaseSchema = useMemo(
    () => {
      if (clase?.cupos_ocupados > 0) {
        return z.object({
          cupos: z
            .coerce.number()
            .int('Los cupos deben ser un número entero.')
            .min(1, 'Los cupos deben ser al menos 1.'),
        })
      }
      const base = z.object({
        actividad: z
          .string()
          .trim()
          .min(1, 'La actividad es obligatoria.')
          .refine((v) => ACTIVIDADES.includes(v), 'La actividad seleccionada no es válida.'),
        fecha: z
          .string()
          .trim()
          .min(1, 'La fecha es obligatoria.')
          .refine((value) => {
            try {
              const hoy = new Date().toISOString().split('T')[0]
              const fecha = new Date(value)
              const hoyDate = new Date(hoy)
              return fecha >= hoyDate
            } catch {
              return false
            }
          }, 'La fecha no puede ser en el pasado.'),
        horario_inicio: z
          .string()
          .trim()
          .min(1, 'El horario de inicio es obligatorio.')
          .regex(/^(?:[01]?\d|2[0-3])$/, 'El horario de inicio debe estar entre 00:00 y 23:00.'),
        cancha: z
          .string()
          .trim()
          .min(1, 'La cancha es obligatoria.')
          .max(100, 'La cancha no puede exceder 100 caracteres.'),
        nivel: z
          .string()
          .trim()
          .min(1, 'El nivel es obligatorio.')
          .refine((v) => NIVELES.includes(v), 'El nivel seleccionado no es válido.'),
        cupos: z
          .coerce.number()
          .int('Los cupos deben ser un número entero.')
          .min(1, 'Los cupos deben ser al menos 1.'),
        precio: z
          .coerce.number()
          .positive('El precio debe ser mayor a 0.')
          .refine((value) => !Number.isNaN(value), 'El precio debe ser un número válido.'),
        profesor_id: z
          .coerce.number()
          .min(1, 'El profesor es obligatorio.'),
      })

      return base.partial()
    },
    [clase?.cupos_ocupados]
  )

  const fields = useMemo(() => {
    if (clase?.cupos_ocupados > 0) {
      return [
        {
          name: 'cupos',
          label: 'Cupos',
          type: 'number',
          required: true,
          min: '1',
        },
      ]
    }
    return [
      {
        name: 'actividad',
        label: 'Actividad',
        type: 'select',
        required: false,
        options: ACTIVIDADES.map((act) => ({ label: act, value: act })),
      },
      {
        name: 'fecha',
        label: 'Fecha',
        type: 'date',
        required: false,
        min: new Date().toISOString().split('T')[0],
      },
      {
        name: 'horario_inicio',
        label: 'Horario de inicio',
        type: 'select',
        required: false,
        options: HORARIOS,
      },
      {
        name: 'cancha',
        label: 'Cancha',
        type: 'text',
        required: false,
      },
      {
        name: 'nivel',
        label: 'Nivel',
        type: 'select',
        required: false,
        options: NIVELES.map((nivel) => ({ label: nivel, value: nivel })),
      },
      {
        name: 'cupos',
        label: 'Cupos',
        type: 'number',
        required: false,
        min: '1',
      },
      {
        name: 'precio',
        label: 'Precio',
        type: 'number',
        required: false,
        min: '0.01',
        step: '0.01',
      },
      {
        name: 'profesor_id',
        label: 'Profesor',
        type: 'select',
        required: false,
        options: profesores.map((prof) => ({ label: prof.nombre, value: prof.id })),
      },
    ]
  }, [clase?.cupos_ocupados, profesores])

  async function handleSubmit(values) {
    setErrorCycle((currentCycle) => currentCycle + 1)
    setServerErrors({})
    setGeneralError('')
    setIsSubmitting(true)

    try {
      const actividad = values.actividad && values.actividad !== '' ? values.actividad : clase.actividad
      const fecha = values.fecha && values.fecha !== '' ? values.fecha : clase.fecha
      const horario_inicio = clase?.cupos_ocupados > 0
        ? Number(clase.horario_inicio.split(':')[0])
        : (values.horario_inicio !== undefined && values.horario_inicio !== '' ? Number(values.horario_inicio) : Number(clase.horario_inicio.split(':')[0]))
      const cancha = values.cancha && values.cancha !== '' ? values.cancha : clase.cancha
      const nivel = values.nivel && values.nivel !== '' ? values.nivel : clase.nivel
      const cupos = values.cupos !== undefined && values.cupos !== '' ? Number(values.cupos) : clase.cupos
      const precio = values.precio !== undefined && values.precio !== '' ? Number(values.precio) : clase.precio
      const profesor_id = clase?.cupos_ocupados > 0 ? clase.profesor_id : (values.profesor_id ? Number(values.profesor_id) : clase.profesor_id)

      const payload = {
        actividad,
        fecha,
        horario_inicio,
        cancha,
        nivel,
        cupos,
        precio,
        profesor_id,
      }

      const result = await actualizarClase(claseId, payload)
      redirectTo(navigate, result.redirect_to || '/clases', {
        flashMessage: result.message || 'La clase fue actualizada correctamente.',
      })
    } catch (error) {
      if (error?.data?.status === 'validation_error' && error.data.errors) {
        setServerErrors(error.data.errors)
      } else {
        setGeneralError(error?.data?.message || 'No se pudo actualizar la clase.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isBootstrapping || loading || loadingProfesores) {
    return (
      <main className="auth-shell">
        <section className="auth-frame auth-frame--compact">
          <header className="auth-header">
            <p className="auth-subtitle">Modificar clase</p>
            <h1>Centro de actividades deportivas</h1>
          </header>
          <p className="dashboard-copy">Cargando datos de la clase.</p>
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
          <Link className="secondary-action" to={returnTo}>
            Volver
          </Link>
        </div>

        <header className="dashboard-header">
          <h1>Modificar clase </h1>
          <p className="dashboard-copy">
            {clase?.cupos_ocupados > 0
              ? 'Esta clase tiene reservas activas. Solo se puede modificar la cantidad de cupos.'
              : 'Actualizá el horario, profesor o cupos según corresponda.'}
          </p>
        </header>

        <div className="actividad-placeholder-page__card">
          {clase?.cupos_ocupados > 0 && (
            <>
              <h2>Resumen de clase</h2>
              
              <dl className="actividad-placeholder-page__details">
                <div>
                  <dt>Actividad</dt>
                  <dd>{clase.actividad}</dd>
                </div>
                <div>
                  <dt>Fecha</dt>
                  <dd>{clase.fecha}</dd>
                </div>
                <div>
                  <dt>Horario actual</dt>
                  <dd>{clase.horario_inicio} - {clase.horario_fin}</dd>
                </div>
                <div>
                  <dt>Cancha</dt>
                  <dd>{clase.cancha}</dd>
                </div>
                <div>
                  <dt>Nivel</dt>
                  <dd>{clase.nivel}</dd>
                </div>
                <div>
                  <dt>Profesor</dt>
                  <dd>{clase.profesor_nombre || 'A confirmar'}</dd>
                </div>
                <div>
                  <dt>Cupos ocupados</dt>
                  <dd>{clase.cupos_ocupados}</dd>
                </div>
              </dl>
            </>
          )}
          <DynamicForm2
            key={clase?.clase_id ?? 'modificar-clase'}
            fields={fields}
            initialValues={initialValues}
            schema={modificarClaseSchema}
            onSubmit={handleSubmit}
            submitLabel="Actualizar clase"
            isSubmitting={isSubmitting}
            serverErrors={serverErrors}
            generalError={generalError}
            errorCycle={errorCycle}
            disableIfUnchanged={true}
          />
        </div>
      </section>
    </section>
  )
}

function getReturnTo(location) {
  const params = new URLSearchParams(location.search)
  const returnTo = params.get('returnTo') || location.state?.from || location.state?.returnTo

  if (typeof returnTo === 'string' && returnTo.startsWith('/')) {
    return returnTo
  }

  return '/clases'
}

function canNavigateBack(returnTo) {
  return returnTo === '/clases' && window.history.state?.idx > 0
}
