import { startTransition, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  iniciarSesion,
  obtenerSesionActual,
  seleccionarRolDeSesion,
} from './api/iniciar_sesion'
import './App.css'

const INITIAL_FORM = {
  email: '',
  password: '',
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const ROLE_CONTENT = {
  administrador: {
    title: 'Ingresar como administrador',
    description: 'Acceso exclusivo del dueño con permisos globales del sistema.',
  },
  empleado: {
    title: 'Ingresar como empleado',
    description: 'Accedé con los permisos operativos y administrativos de atención.',
  },
  socio: {
    title: 'Ingresar como socio',
    description: 'Continuá con la experiencia orientada a reservas, pagos y clases.',
  },
}

function App() {
  const navigate = useNavigate()
  const [form, setForm] = useState(INITIAL_FORM)
  const [fieldErrors, setFieldErrors] = useState({})
  const [requestError, setRequestError] = useState('')
  const [pendingRoles, setPendingRoles] = useState([])
  const [pendingIdentity, setPendingIdentity] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSelectingRole, setIsSelectingRole] = useState(false)

  useEffect(() => {
    let ignore = false

    async function cargarSesion() {
      try {
        const result = await obtenerSesionActual()

        if (ignore) {
          return
        }

        if (result.authenticated) {
          redirectToHome(navigate, result.session, '/inicio')
          return
        }

        if (result.pending_role_selection) {
          setPendingRoles(result.available_roles || [])
          setPendingIdentity(result.identity || null)
        }
      } catch {
        if (!ignore) {
          setPendingRoles([])
          setPendingIdentity(null)
        }
      }
    }

    cargarSesion()

    return () => {
      ignore = true
    }
  }, [navigate])

  function handleChange(event) {
    const { name, value } = event.target

    setForm((currentForm) => ({
      ...currentForm,
      [name]: value,
    }))

    if (fieldErrors[name]) {
      setFieldErrors((currentErrors) => {
        const nextErrors = { ...currentErrors }
        delete nextErrors[name]
        return nextErrors
      })
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()

    const clientErrors = validateForm(form)
    setFieldErrors(clientErrors)
    setRequestError('')

    if (Object.keys(clientErrors).length > 0) {
      return
    }

    setIsSubmitting(true)

    try {
      const result = await iniciarSesion({
        email: form.email.trim().toLowerCase(),
        password: form.password,
      })

      if (result.status === 'role_selection_required') {
        setPendingRoles(result.available_roles || [])
        setPendingIdentity(result.identity || null)
        setForm((currentForm) => ({ ...currentForm, password: '' }))
        setFieldErrors({})
        return
      }

      redirectToHome(navigate, result.session, result.redirect_to)
    } catch (error) {
      applyApiError(error, setFieldErrors, setRequestError)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleRoleSelection(role) {
    setRequestError('')
    setIsSelectingRole(true)

    try {
      const result = await seleccionarRolDeSesion({ role })
      redirectToHome(navigate, result.session, result.redirect_to)
    } catch (error) {
      applyApiError(error, setFieldErrors, setRequestError)
    } finally {
      setIsSelectingRole(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-frame">
        <header className="auth-header">
          <p className="auth-subtitle">Acceso al sistema</p>
          <h1>Centro de actividades deportivas</h1>
        </header>

        <div className="auth-form-shell">
          {requestError ? (
            <p className="banner banner--error" role="alert">
              {requestError}
            </p>
          ) : null}

          {pendingRoles.length > 0 ? (
            <section className="role-panel" aria-labelledby="role-selection-title">
              <div className="role-copy">
                <h2 id="role-selection-title">Elegí cómo querés ingresar</h2>
                <p>
                  La cuenta <strong>{pendingIdentity?.email}</strong> tiene más de un rol
                  disponible.
                </p>
              </div>

              <div className="role-grid">
                {pendingRoles.map((role) => {
                  const roleContent = ROLE_CONTENT[role] || {
                    title: `Ingresar como ${role}`,
                    description: 'Continuá con el rol seleccionado para esta cuenta.',
                  }

                  return (
                    <button
                      key={role}
                      type="button"
                      className="role-card"
                      disabled={isSelectingRole}
                      onClick={() => handleRoleSelection(role)}
                    >
                      <span className="role-card__label">{roleContent.title}</span>
                      <span className="role-card__description">
                        {roleContent.description}
                      </span>
                    </button>
                  )
                })}
              </div>
            </section>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit} noValidate>
              <label className="field">
                <span>Usuario</span>
                <input
                  autoComplete="email"
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={handleChange}
                  aria-invalid={fieldErrors.email ? 'true' : 'false'}
                />
                {fieldErrors.email ? <small>{fieldErrors.email}</small> : null}
              </label>

              <label className="field">
                <span>Contraseña</span>
                <input
                  autoComplete="current-password"
                  name="password"
                  type="password"
                  value={form.password}
                  onChange={handleChange}
                  aria-invalid={fieldErrors.password ? 'true' : 'false'}
                />
                {fieldErrors.password ? <small>{fieldErrors.password}</small> : null}
              </label>

              <button className="primary-action" type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Validando credenciales...' : 'Iniciar sesión'}
              </button>
            </form>
          )}
        </div>
      </section>
    </main>
  )
}

function validateForm(form) {
  const errors = {}
  const email = form.email.trim().toLowerCase()

  if (!email) {
    errors.email = 'El email es obligatorio.'
  } else if (!EMAIL_PATTERN.test(email)) {
    errors.email = 'Ingresá un email válido.'
  }

  if (!form.password) {
    errors.password = 'La contraseña es obligatoria.'
  } else if (form.password.length < 4) {
    errors.password = 'La contraseña debe tener al menos 4 caracteres.'
  } else if (form.password.length > 128) {
    errors.password = 'La contraseña debe tener como máximo 128 caracteres.'
  }

  return errors
}

function applyApiError(error, setFieldErrors, setRequestError) {
  if (error?.data?.status === 'validation_error' && error.data.errors) {
    setFieldErrors(error.data.errors)
    return
  }

  setRequestError(error?.data?.message || 'No se pudo iniciar la sesión.')
}

function redirectToHome(navigate, sessionData, redirectTo) {
  startTransition(() => {
    navigate(redirectTo || '/inicio', {
      replace: true,
      state: { session: sessionData },
    })
  })
}

export default App
