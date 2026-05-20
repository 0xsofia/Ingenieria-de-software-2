import { startTransition, useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate, useParams } from 'react-router-dom'
import { z } from 'zod'

import { modificarUsuario, obtenerUsuarioModificable } from '../api/usuarios'
import DynamicForm from '../components/forms/DynamicForm.jsx'
import { useAuth } from '../hooks/useAuth'
import { storeFlashMessage } from '../utils/navigationFlash'
import { getPhoneValidationMessage } from '../utils/phoneValidation'
import './RegistrarsePage.css'
import './ModificarUsuarioPage.css'

const EDITABLE_USER_FIELDS = [
  {
    name: 'dni',
    label: 'DNI',
    type: 'text',
    autoComplete: 'off',
    inputMode: 'numeric',
    placeholder: 'Solo números',
    hint: 'El DNI forma parte de la identidad del usuario y no puede modificarse.',
    disabled: true,
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

const EMPTY_VALUES = Object.freeze(
  EDITABLE_USER_FIELDS.reduce((accumulator, field) => {
    accumulator[field.name] = ''
    return accumulator
  }, {})
)

function ModificarUsuarioPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { id } = useParams()
  const { session } = useAuth()
  const [serverErrors, setServerErrors] = useState({})
  const [generalError, setGeneralError] = useState('')
  const [errorCycle, setErrorCycle] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [userRecord, setUserRecord] = useState(null)

  const userSchema = useMemo(
    () =>
      z.object({
        dni: z.string().trim().min(1, 'El DNI es obligatorio.'),
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

  const initialValues = useMemo(() => {
    if (userRecord === null) {
      return EMPTY_VALUES
    }

    return {
      dni: userRecord.dni || '',
      email: userRecord.email || '',
      nombre: userRecord.nombre || '',
      apellido: userRecord.apellido || '',
      telefono: userRecord.telefono || '',
      calle: userRecord.calle || '',
      numero_puerta: userRecord.numero_puerta || '',
      codigo_postal: userRecord.codigo_postal || '',
    }
  }, [userRecord])

  useEffect(() => {
    if (session?.role !== 'administrador') {
      return
    }

    let cancelled = false

    async function loadUser() {
      setIsLoading(true)
      setGeneralError('')

      try {
        const result = await obtenerUsuarioModificable(id)
        if (!cancelled) {
          setUserRecord(result.user)
        }
      } catch (error) {
        if (!cancelled) {
          setGeneralError(error?.data?.message || 'No se pudo cargar el usuario solicitado.')
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadUser()

    return () => {
      cancelled = true
    }
  }, [id, session?.role])

  if (session?.role !== 'administrador') {
    return <Navigate to="/inicio" replace />
  }

  async function handleSubmit(values) {
    setErrorCycle((currentCycle) => currentCycle + 1)
    setServerErrors({})
    setGeneralError('')
    setIsSubmitting(true)

    try {
      const result = await modificarUsuario(id, values)
      const successMessage = result.message || 'El usuario ha sido actualizado con éxito.'
      const returnTo = getReturnTo(location)

      if (canNavigateBack(returnTo)) {
        storeFlashMessage(successMessage)
        startTransition(() => {
          navigate(-1)
        })
      } else {
        startTransition(() => {
          navigate(returnTo, {
            replace: true,
            state: { flashMessage: successMessage },
          })
        })
      }
    } catch (error) {
      if (error?.data?.status === 'validation_error' && error.data.errors) {
        setServerErrors(error.data.errors)
      } else {
        setGeneralError(error?.data?.message || 'No se pudo actualizar el usuario.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const returnTo = getReturnTo(location)
  const roleSummary = formatRoleSummary(userRecord?.roles || [])

  if (isLoading) {
    return (
      <section className="dashboard-shell">
        <section className="dashboard-frame dashboard-frame--compact">
          <header className="dashboard-header">
            <p className="auth-subtitle">Administración</p>
            <h1>Cargando usuario</h1>
            <p className="dashboard-copy">Estamos preparando los datos para editar este perfil.</p>
          </header>
        </section>
      </section>
    )
  }

  if (generalError && userRecord === null) {
    return (
      <section className="dashboard-shell">
        <section className="dashboard-frame dashboard-frame--compact">
          <div className="register-top-link">
            <Link className="secondary-action" to={returnTo}>
              Volver
            </Link>
          </div>

          <p className="banner banner--error" role="alert">
            {generalError}
          </p>
        </section>
      </section>
    )
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame modify-user-frame">
        <div className="register-top-link">
          <Link className="secondary-action" to={returnTo}>
            Volver
          </Link>
        </div>

        <header className="dashboard-header modify-user-header">
          <p className="auth-subtitle">Administración</p>
          <h1>Modificar usuario</h1>
          {/* <p className="modify-user-copy">
            Editá los datos de {roleSummary} sin cambiar la contraseña ni el DNI registrado.
          </p> */}
        </header>

        <div className="auth-form-shell">
          <DynamicForm
            fields={EDITABLE_USER_FIELDS}
            initialValues={initialValues}
            schema={userSchema}
            onSubmit={handleSubmit}
            submitLabel="Modificar usuario"
            isSubmitting={isSubmitting}
            serverErrors={serverErrors}
            generalError={generalError}
            errorCycle={errorCycle}
          />
        </div>
      </section>
    </section>
  )
}

function formatRoleSummary(roles) {
  if (roles.length === 0) {
    return 'este usuario'
  }

  const labels = roles.map((role) => {
    if (role === 'empleado') {
      return 'empleado'
    }

    if (role === 'socio') {
      return 'socio'
    }

    return role
  })

  if (labels.length === 1) {
    return `un ${labels[0]}`
  }

  return `un ${labels.join(' y ')}`
}

function getReturnTo(location) {
  const params = new URLSearchParams(location.search)
  const returnTo = params.get('returnTo') || location.state?.from

  if (typeof returnTo === 'string' && returnTo.startsWith('/')) {
    return returnTo
  }

  return '/inicio'
}

function canNavigateBack(returnTo) {
  return returnTo === '/inicio' && window.history.state?.idx > 0
}

export default ModificarUsuarioPage
