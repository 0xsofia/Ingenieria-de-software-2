import { startTransition, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { registrarEmpleado } from '../api/usuarios'
import DynamicForm from '../components/forms/DynamicForm.jsx'
import { useAuth } from '../hooks/useAuth'
import { getPhoneValidationMessage } from '../utils/phoneValidation'
import './RegistrarsePage.css'
import './RegistrarEmpleadoPage.css'

const EMPLOYEE_FIELDS = [
  {
    name: 'dni',
    label: 'DNI',
    type: 'text',
    autoComplete: 'off',
    inputMode: 'numeric',
    placeholder: 'Solo números',
  },
  {
    name: 'email',
    label: 'Email',
    type: 'email',
    autoComplete: 'email',
    placeholder: 'nombre@dominio.com',
  },
  {
    name: 'nombre',
    label: 'Nombre',
    type: 'text',
    autoComplete: 'given-name',
    placeholder: 'Nombre',
  },
  {
    name: 'apellido',
    label: 'Apellido',
    type: 'text',
    autoComplete: 'family-name',
    placeholder: 'Apellido',
  },
  {
    name: 'telefono',
    label: 'Teléfono',
    type: 'text',
    autoComplete: 'tel',
    inputMode: 'tel',
    placeholder: '2214446633',
    hint: 'Ingresá un teléfono de 10 dígitos. Ejemplo: 2214446633.',
    fullWidth: true,
  },
  {
    name: 'calle',
    label: 'Calle',
    type: 'text',
    autoComplete: 'address-line1',
    placeholder: 'Calle',
  },
  {
    name: 'numero_puerta',
    label: 'Número de puerta',
    type: 'text',
    autoComplete: 'address-line2',
    placeholder: 'Número',
  },
  {
    name: 'codigo_postal',
    label: 'Código postal',
    type: 'text',
    autoComplete: 'postal-code',
    placeholder: '1900',
  },
]

const INITIAL_VALUES = Object.freeze(
  EMPLOYEE_FIELDS.reduce((accumulator, field) => {
    accumulator[field.name] = ''
    return accumulator
  }, {})
)

function RegistrarEmpleadoPage() {
  const navigate = useNavigate()
  const { session } = useAuth()
  const [serverErrors, setServerErrors] = useState({})
  const [generalError, setGeneralError] = useState('')
  const [errorCycle, setErrorCycle] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const employeeSchema = useMemo(
    () =>
      z.object({
        dni: z
          .string()
          .trim()
          .min(1, 'El DNI es obligatorio.')
          .regex(/^\d+$/, 'Ingresá el DNI solo con números.'),
        email: z
          .string()
          .trim()
          .min(1, 'El email es obligatorio.')
          .email('Ingresá un email válido.')
          .transform((value) => value.toLowerCase()),
        nombre: z.string().trim().min(1, 'El nombre es obligatorio.'),
        apellido: z.string().trim().min(1, 'El apellido es obligatorio.'),
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
        calle: z.string().trim().min(1, 'La calle es obligatoria.'),
        numero_puerta: z.string().trim().min(1, 'El número de puerta es obligatorio.'),
        codigo_postal: z.string().trim().min(1, 'El código postal es obligatorio.'),
      }),
    []
  )

  if (session?.role !== 'administrador') {
    return <Navigate to="/inicio" replace />
  }

  async function handleSubmit(values) {
    setErrorCycle((currentCycle) => currentCycle + 1)
    setServerErrors({})
    setGeneralError('')
    setIsSubmitting(true)

    try {
      const result = await registrarEmpleado(values)
      startTransition(() => {
        navigate(result.redirect_to || '/inicio', {
          replace: true,
          state: {
            flashMessage:
              result.message ||
              'El empleado fue registrado correctamente con la contraseña temporal de esta fase.',
          },
        })
      })
    } catch (error) {
      if (error?.data?.status === 'validation_error' && error.data.errors) {
        setServerErrors(error.data.errors)
      } else {
        setGeneralError(error?.data?.message || 'No se pudo registrar el empleado.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-frame">
        <div className="register-top-link">
          <Link className="secondary-action" to="/inicio">
            Volver al inicio
          </Link>
        </div>

        <header className="auth-header">
          <p className="auth-subtitle">Administración</p>
          <h1>Registrar empleado</h1>
        </header>

        <div className="auth-form-shell">
          <DynamicForm
            fields={EMPLOYEE_FIELDS}
            initialValues={INITIAL_VALUES}
            schema={employeeSchema}
            onSubmit={handleSubmit}
            submitLabel="Registrar empleado"
            isSubmitting={isSubmitting}
            serverErrors={serverErrors}
            generalError={generalError}
            errorCycle={errorCycle}
          />
        </div>
      </section>
    </main>
  )
}

export default RegistrarEmpleadoPage
