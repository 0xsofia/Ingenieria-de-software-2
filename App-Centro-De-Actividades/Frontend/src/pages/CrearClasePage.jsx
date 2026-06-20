import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import DynamicForm2 from '../components/forms/DynamicForm2'
import { crearClase, obtenerProfesores } from '../api/clase'
import { useAuth } from '../hooks/useAuth'
import { redirectTo } from '../services/redirectTo'
import { ACTIVIDADES } from '../constants/actividades'
import './ActividadPage.css'

const NIVELES = ['Principiante', 'Intermedio', 'Avanzado']
const DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
const HORARIOS = Array.from({ length: 24 }, (_, hora) => ({
  label: `${String(hora).padStart(2, '0')}:00`,
  value: hora,
}))
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

export default function ClasePage() {
  const navigate = useNavigate()
  const { isAuthenticated, isBootstrapping, session } = useAuth()
  const [serverErrors, setServerErrors] = useState({})
  const [generalError, setGeneralError] = useState('')
  const [errorCycle, setErrorCycle] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [profesores, setProfesores] = useState([])
  const [loadingProfesores, setLoadingProfesores] = useState(true)

  useEffect(() => {
    if (!isBootstrapping && !isAuthenticated) {
      redirectTo(navigate, '/login')
    }
  }, [isAuthenticated, isBootstrapping, navigate])

  useEffect(() => {
    const cargarProfesores = async () => {
      try {
        const data = await obtenerProfesores()
        setProfesores(data)
      } catch (err) {
        console.error('Error al cargar profesores:', err)
        setGeneralError('No se pudieron cargar los profesores')
      } finally {
        setLoadingProfesores(false)
      }
    }

    cargarProfesores()
  }, [])

  const crearClaseSchema = useMemo(
    () =>
      z.object({
        actividad: z
          .string()
          .trim()
          .min(1, 'La actividad es obligatoria.')
          .refine(
            (value) => ACTIVIDADES.includes(value),
            'La actividad seleccionada no es válida.'
          ),
        dia_semana: z
          .string()
          .trim()
          .min(1, 'El día de la semana es obligatorio.')
          .refine(
            (value) => DIAS_SEMANA.includes(value),
            'El día de la semana seleccionado no es válido.'
          ),
        mes: z.coerce
          .number()
          .int()
          .min(1, 'El mes es obligatorio.')
          .max(12, 'El mes seleccionado no es válido.'),
        horario_inicio: z.coerce
          .number()
          .int()
          .min(0, 'El horario de inicio es obligatorio.')
          .max(23),
        cancha: z
          .string()
          .trim()
          .min(1, 'La cancha es obligatoria.')
          .max(100, 'La cancha no puede exceder 100 caracteres.'),
        nivel: z
          .string()
          .trim()
          .min(1, 'El nivel es obligatorio.')
          .refine(
            (value) => NIVELES.includes(value),
            'El nivel seleccionado no es válido.'
          ),
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
      }),
    []
  )

  const fields = useMemo(
    () => [
      {
        name: 'actividad',
        label: 'Actividad',
        type: 'select',
        required: true,
        options: ACTIVIDADES.map((act) => ({
          label: act,
          value: act,
        })),
      },
      {
        name: 'dia_semana',
        label: 'Día de la semana',
        type: 'select',
        required: true,
        options: DIAS_SEMANA.map((dia) => ({
          label: dia,
          value: dia,
        })),
      },
      {
        name: 'mes',
        label: 'Mes',
        type: 'select',
        required: true,
        options: MESES,
      },
      {
        name: 'horario_inicio',
        label: 'Horario de inicio',
        type: 'select',
        required: true,
        options: HORARIOS,
      },
      {
        name: 'cancha',
        label: 'Cancha',
        type: 'text',
        required: true,
        placeholder: 'Ingrese la cancha',
      },
      {
        name: 'nivel',
        label: 'Nivel',
        type: 'select',
        required: true,
        options: NIVELES.map((nivel) => ({
          label: nivel,
          value: nivel,
        })),
      },
      {
        name: 'cupos',
        label: 'Cupos',
        type: 'number',
        required: true,
        min: '1',
      },
      {
        name: 'precio',
        label: 'Precio',
        type: 'number',
        required: true,
        min: '0.01',
        step: '0.01',
        placeholder: 'Ingrese el precio en pesos',
      },
      {
        name: 'profesor_id',
        label: 'Profesor',
        type: 'select',
        required: true,
        options: profesores.map((prof) => ({
          label: prof.nombre,
          value: prof.id,
        })),
      },
    ],
    [profesores]
  )

  const initialValues = useMemo(
    () => ({
      actividad: '',
      dia_semana: '',
      mes: '',
      horario_inicio: '',
      cancha: '',
      nivel: '',
      cupos: 1,
      precio: 1,
      profesor_id: '',
    }),
    []
  )

  async function handleSubmit(values) {
    setErrorCycle((currentCycle) => currentCycle + 1)
    setServerErrors({})
    setGeneralError('')
    setIsSubmitting(true)

    try {
      const result = await crearClase({
        ...values,
        mes: Number(values.mes),
        horario_inicio: Number(values.horario_inicio),
        cupos: Number(values.cupos),
        precio: Number(values.precio),
        profesor_id: Number(values.profesor_id),
      })

      redirectTo(navigate, result.redirect_to || '/clases', {
        flashMessage: result.message || 'La clase fue creada correctamente.',
      })
    } catch (error) {
      if (error?.data?.status === 'validation_error' && error.data.errors) {
        setServerErrors(error.data.errors)
      } else {
        setGeneralError(error?.data?.message || 'No se pudo crear la clase.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isBootstrapping || loadingProfesores) {
    return (
      <main className="auth-shell">
        <section className="auth-frame auth-frame--compact">
          <header className="auth-header">
            <p className="auth-subtitle">Crear clase</p>
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
          <p className="auth-subtitle">Crear clase</p>
          <h1>Nueva clase</h1>
        </header>

        <DynamicForm2
          fields={fields}
          initialValues={initialValues}
          schema={crearClaseSchema}
          onSubmit={handleSubmit}
          submitLabel="Crear clase"
          isSubmitting={isSubmitting}
          serverErrors={serverErrors}
          generalError={generalError}
          errorCycle={errorCycle}
        />
      </section>
    </section>
  )
}
