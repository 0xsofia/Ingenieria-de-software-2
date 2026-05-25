import { startTransition, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { registrarse } from '../api/registrarse'
import DynamicForm from '../components/forms/DynamicForm.jsx'
import { useAuth } from '../hooks/useAuth'
import { getPhoneValidationMessage, PHONE_HINT } from '../utils/phoneValidation'
import './RegistrarsePage.css'

const PASSWORD_LENGTH_MESSAGE = 'La contraseña debe tener entre 6 a 12 caracteres.'
const REPEAT_PASSWORD_MESSAGE = 'Repetir contraseña debe coincidir con la contraseña.'

const REGISTER_FIELDS = [
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
    inputMode: 'numeric',
    pattern: '[0-9]*',
    digitsOnly: true,
    placeholder: '2214446633',
    hint: PHONE_HINT,
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
  {
    name: 'password',
    label: 'Contraseña',
    type: 'password',
    autoComplete: 'new-password',
    placeholder: 'Entre 6 y 12 caracteres',
  },
  {
    name: 'repeat_password',
    label: 'Repetir contraseña',
    type: 'password',
    autoComplete: 'new-password',
    placeholder: 'Repetí la contraseña',
  },
]

const INITIAL_VALUES = Object.freeze(
  REGISTER_FIELDS.reduce((accumulator, field) => {
    accumulator[field.name] = ''
    return accumulator
  }, {})
)

function RegistrarsePage() {
  const navigate = useNavigate()
  const { isAuthenticated, isBootstrapping } = useAuth()
  const [serverErrors, setServerErrors] = useState({})
  const [generalError, setGeneralError] = useState('')
  const [errorCycle, setErrorCycle] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const registerSchema = useMemo(
    () =>
      z
        .object({
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
          password: z
            .string()
            .min(1, 'La contraseña es obligatoria.')
            .refine((value) => value.length >= 6 && value.length <= 12, PASSWORD_LENGTH_MESSAGE),
          repeat_password: z.string().min(1, 'Repetir contraseña es obligatorio.'),
        })
        .refine((data) => data.password === data.repeat_password, {
          message: REPEAT_PASSWORD_MESSAGE,
          path: ['repeat_password'],
        }),
    []
  )

  useEffect(() => {
    if (isAuthenticated) {
      redirectTo(navigate, '/inicio')
    }
  }, [isAuthenticated, navigate])

  async function handleSubmit(values) {
    setErrorCycle((currentCycle) => currentCycle + 1)
    setServerErrors({})
    setGeneralError('')
    setIsSubmitting(true)

    try {
      const result = await registrarse(values)
      redirectTo(navigate, '/login', {
        flashMessage: result.message || 'La cuenta fue creada correctamente.',
      })
    } catch (error) {
      if (error?.data?.status === 'validation_error' && error.data.errors) {
        setServerErrors(error.data.errors)
      } else {
        setGeneralError(error?.data?.message || 'No se pudo completar el registro.')
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
            <p className="auth-subtitle">Registro de socios</p>
            <h1>Centro de actividades deportivas</h1>
          </header>
          <p className="dashboard-copy">Estamos verificando tu sesión activa.</p>
        </section>
      </main>
    )
  }

  return (
    <main className="auth-shell">
      <section className="auth-frame">
        <div className="register-top-link">
          <Link className="secondary-action" to="/login">
            Volver al inicio de sesión
          </Link>
        </div>

        <header className="auth-header">
          <p className="auth-subtitle">Registro de socios</p>
          <h1>Creá tu cuenta</h1>
          <p className="register-copy">
            Cargá tus datos personales para registrarte como socio y continuar luego desde el
            inicio de sesión.
          </p>
        </header>

        <div className="auth-form-shell">
          <DynamicForm
            fields={REGISTER_FIELDS}
            initialValues={INITIAL_VALUES}
            schema={registerSchema}
            onSubmit={handleSubmit}
            submitLabel="Registrarse"
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

function redirectTo(navigate, path, state) {
  startTransition(() => {
    navigate(path, { replace: true, state })
  })
}

export default RegistrarsePage
