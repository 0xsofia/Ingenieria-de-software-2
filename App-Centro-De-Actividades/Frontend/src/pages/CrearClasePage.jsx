import { useEffect, useMemo, useState } from 'react'
import { z } from 'zod'
import DynamicForm2 from '../components/forms/DynamicForm2'
import { crearClase, obtenerProfesores } from '../api/clase'
import { useAuth } from '../hooks/useAuth'
import { redirectTo } from '../services/redirectTo'
import { useNavigate } from 'react-router-dom'
import { ACTIVIDADES } from '../constants/actividades'

const NIVELES = ['Principiante', 'Intermedio', 'Avanzado']

const hoy = new Date().toISOString().split('T')[0]

export default function ClasePage() {
  const navigate = useNavigate()
  const { isAuthenticated, isBootstrapping } = useAuth()
  const [serverErrors, setServerErrors] = useState({})
  const [generalError, setGeneralError] = useState('')
  const [errorCycle, setErrorCycle] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [profesores, setProfesores] = useState([])
  const [loadingProfesores, setLoadingProfesores] = useState(true)

  useEffect(() => {
    if (isAuthenticated) {
      redirectTo(navigate, '/inicio')
    }
  }, [isAuthenticated, navigate])

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
        fecha: z
          .string()
          .trim()
          .min(1, 'La fecha es obligatoria.')
          .refine(
            (value) => {
              try {
                const fecha = new Date(value)
                const hoyDate = new Date(hoy)
                return fecha >= hoyDate
              } catch {
                return false
              }
            },
            'La fecha no puede ser en el pasado.'
          ),
        horario_inicio: z.coerce
          .number()
          .int()
          .min(1, 'El horario de inicio es obligatorio.')
          .max(24),
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
        name: 'fecha',
        label: 'Fecha',
        type: 'date',
        required: true,
        min: hoy,
      },
      {
        name: 'horario_inicio',
        label: 'Horario de inicio',
        type: 'number',
        required: true,
        min:1,
        max:24,
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
      fecha: '',
      horario_inicio: 1,
      cancha: '',
      nivel: '',
      cupos: 1,
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
        horario_inicio: Number(values.horario_inicio),
        cupos: Number(values.cupos),
        profesor_id: Number(values.profesor_id),
      })

      redirectTo(navigate, '/inicio', {
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

  return (
    <main className="auth-shell">
      <section className="auth-frame">
        <header className="auth-header">
          <p className="auth-subtitle">Crear clase</p>
          <h1>Centro de actividades deportivas</h1>
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
    </main>
  )
}
