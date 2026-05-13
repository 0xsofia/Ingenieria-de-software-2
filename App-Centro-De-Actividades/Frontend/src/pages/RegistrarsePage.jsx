import { startTransition, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { registrarse } from '../api/registrarse'
import DynamicForm from '../components/forms/DynamicForm.jsx'
import { useAuth } from '../hooks/useAuth'
import './RegistrarsePage.css'

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
    inputMode: 'tel',
    placeholder: '22112345678',
    hint: 'Ingresá tu celular sin 0 ni 15. Ejemplo: 22112345678.',
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
    placeholder: 'Mínimo 4 caracteres',
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
            .refine(
              (value) => normalizeArgentinaPhone(value) !== null,
              'Ingresá un celular válido sin 0 ni 15. Ejemplo: 22112345678.'
            )
            .transform((value) => normalizeArgentinaPhone(value)),
          calle: z.string().trim().min(1, 'La calle es obligatoria.'),
          numero_puerta: z.string().trim().min(1, 'El número de puerta es obligatorio.'),
          codigo_postal: z.string().trim().min(1, 'El código postal es obligatorio.'),
          password: z
            .string()
            .min(1, 'La contraseña es obligatoria.')
            .min(4, 'La contraseña debe tener al menos 4 caracteres.')
            .max(128, 'La contraseña debe tener como máximo 128 caracteres.'),
          repeat_password: z.string().min(1, 'Repetir contraseña es obligatorio.'),
        })
        .refine((data) => data.password === data.repeat_password, {
          message: 'Repetir contraseña debe coincidir con la contraseña.',
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
         <h1>Creá tu cuenta</h1>
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
          />
        </div>
      </section>
    </main>
  )
}

function normalizeArgentinaPhone(value) {
  let digits = value.replace(/\D/g, '')

  if (digits.startsWith('54')) {
    digits = digits.slice(2)
  }

  if (digits.startsWith('0')) {
    digits = digits.slice(1)
  }

  const normalizedLocalPhone = normalizeLocalMobileDigits(digits)
  if (normalizedLocalPhone === null) {
    return null
  }

  return `+54${normalizedLocalPhone}`
}

function normalizeLocalMobileDigits(digits) {
  for (let areaLength = 2; areaLength <= 4; areaLength += 1) {
    const localWithoutMobilePrefix = validateLocalPhoneDigits(digits, areaLength)
    if (localWithoutMobilePrefix !== null) {
      return localWithoutMobilePrefix
    }

    const localWithLegacyMobilePrefix = validateLegacyMobileDigits(digits, areaLength)
    if (localWithLegacyMobilePrefix !== null) {
      return localWithLegacyMobilePrefix
    }
  }

  return null
}

function validateLocalPhoneDigits(digits, areaLength) {
  const subscriber = digits.slice(areaLength)
  if (subscriber.length < 6 || subscriber.length > 8) {
    return null
  }

  return areaLength + subscriber.length >= 10 && areaLength + subscriber.length <= 11
    ? digits
    : null
}

function validateLegacyMobileDigits(digits, areaLength) {
  if (digits.slice(areaLength, areaLength + 2) !== '15') {
    return null
  }

  const subscriber = digits.slice(areaLength + 2)
  if (subscriber.length < 6 || subscriber.length > 8) {
    return null
  }

  const localDigits = `${digits.slice(0, areaLength)}${subscriber}`
  return localDigits.length >= 10 && localDigits.length <= 11 ? localDigits : null
}

function redirectTo(navigate, path, state) {
  startTransition(() => {
    navigate(path, { replace: true, state })
  })
}

export default RegistrarsePage
