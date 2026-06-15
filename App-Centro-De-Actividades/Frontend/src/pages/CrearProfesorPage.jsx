import { useState, useMemo, useEffect } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import DynamicForm2 from '../components/forms/DynamicForm2'
import { crearProfesor } from '../api/profesor'
import { useAuth } from '../hooks/useAuth'
import { getPhoneValidationMessage, PHONE_HINT } from '../utils/phoneValidation'
import { redirectTo } from '../services/redirectTo'
import './ActividadPage.css'

export default function CrearProfesorPage() {
  const navigate = useNavigate()
  const { isAuthenticated, isBootstrapping, session } = useAuth()
  const [serverErrors, setServerErrors] = useState({})
  const [generalError, setGeneralError] = useState('')
  const [errorCycle, setErrorCycle] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!isBootstrapping && !isAuthenticated) {
      redirectTo(navigate, '/login')
    }
  }, [isAuthenticated, isBootstrapping, navigate])

  const crearProfesorSchema = useMemo(
    () =>
      z.object({
        nombre: z.string().trim().min(1, 'El nombre es obligatorio.'),
        dni: z
          .string()
          .trim()
          .min(1, 'El DNI es obligatorio.')
          .regex(/^[0-9]+$/, 'Ingresá el DNI solo con números.'),
        telefono: z
          .string()
          .trim()
          .min(1, 'El teléfono es obligatorio.')
          .superRefine((value, ctx) => {
            const validationMessage = getPhoneValidationMessage(value)
            if (validationMessage) {
              ctx.addIssue({ code: 'custom', message: validationMessage })
            }
          }),
      }),
    []
  )

  const fields = useMemo(
    () => [
      {
        name: 'nombre',
        label: 'Nombre',
        type: 'text',
        required: true,
        placeholder: 'Ingrese el nombre',
      },
      {
        name: 'dni',
        label: 'DNI',
        type: 'text',
        required: true,
        placeholder: 'Ingrese el DNI',
      },
      {
        name: 'telefono',
        label: 'Teléfono',
        type: 'tel',
        required: true,
        inputMode: 'numeric',
        pattern: '[0-9]*',
        digitsOnly: true,
        placeholder: '2214446633',
        hint: PHONE_HINT,
      },
    ],
    []
  )

  const initialValues = useMemo(
    () => ({
      nombre: '',
      dni: '',
      telefono: '',
    }),
    []
  )

  async function handleSubmit(values) {
    setErrorCycle((currentCycle) => currentCycle + 1)
    setServerErrors({})
    setGeneralError('')
    setIsSubmitting(true)

    try {
      const result = await crearProfesor(values)
      redirectTo(navigate, '/profesores', {
        flashMessage: result.message || 'El profesor fue cargado correctamente.',
      })
    } catch (error) {
      if (error?.data?.status === 'validation_error' && error.data.errors) {
        setServerErrors(error.data.errors)
      } else {
        setGeneralError(error?.data?.message || 'No se pudo crear el profesor.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isBootstrapping) {
    return (
      <main className="auth-shell">
        <section className="auth-frame auth-frame--compact">
          <header className="auth-header">
            <p className="auth-subtitle">Crear profesor</p>
            <h1>Centro de actividades deportivas</h1>
          </header>
          <p className="dashboard-copy">Cargando datos del usuario...</p>
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
          <p className="auth-subtitle">Crear profesor</p>
          <h1>Nuevo profesor</h1>
        </header>

        <DynamicForm2
          fields={fields}
          initialValues={initialValues}
          schema={crearProfesorSchema}
          onSubmit={handleSubmit}
          submitLabel="Crear profesor"
          isSubmitting={isSubmitting}
          serverErrors={serverErrors}
          generalError={generalError}
          errorCycle={errorCycle}
        />
      </section>
    </section>
  )
}
