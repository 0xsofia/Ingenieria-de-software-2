import { startTransition, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { autorizarPermiso, obtenerSesionActual } from '../api/iniciar_sesion'
import '../App.css'

const FRONTEND_OPTIONS = [
  {
    permission: 'usuarios:gestionar',
    title: 'Gestión de usuarios',
    description: 'Alta, edición y bloqueo de usuarios del sistema.',
  },
  {
    permission: 'usuarios:ver',
    title: 'Consulta de usuarios',
    description: 'Listado y visualización de información operativa de personas.',
  },
  {
    permission: 'metricas:ver',
    title: 'Métricas',
    description: 'Acceso a indicadores globales del centro.',
  },
  {
    permission: 'clases:ver',
    title: 'Clases',
    description: 'Visualización de clases y horarios disponibles.',
  },
  {
    permission: 'reservas:crear',
    title: 'Reservas',
    description: 'Creación de reservas y operaciones del socio.',
  },
  {
    permission: 'pagos:ver_propios',
    title: 'Pagos propios',
    description: 'Seguimiento de pagos vinculados a la cuenta actual.',
  },
]

const BACKEND_ACTIONS = [
  {
    permission: 'usuarios:gestionar',
    title: 'Administrar usuarios',
  },
  {
    permission: 'metricas:ver',
    title: 'Consultar métricas institucionales',
  },
  {
    permission: 'reservas:crear',
    title: 'Crear una reserva desde backend',
  },
]

function InicioPage() {
  const navigate = useNavigate()
  const [sessionData, setSessionData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')
  const [authorizationError, setAuthorizationError] = useState('')
  const [authorizationMap, setAuthorizationMap] = useState({})

  useEffect(() => {
    let ignore = false

    async function cargarSesion() {
      try {
        const result = await obtenerSesionActual()
        if (ignore) {
          return
        }

        if (!result.authenticated) {
          startTransition(() => {
            navigate('/', { replace: true })
          })
          return
        }

        setSessionData(result.session)
      } catch {
        if (!ignore) {
          setErrorMessage('No se pudo cargar la sesión actual.')
        }
      } finally {
        if (!ignore) {
          setIsLoading(false)
        }
      }
    }

    cargarSesion()

    return () => {
      ignore = true
    }
  }, [navigate])

  useEffect(() => {
    if (!sessionData) {
      return undefined
    }

    const actionsToValidate = BACKEND_ACTIONS.filter((action) =>
      sessionData.permissions.includes(action.permission),
    )

    if (actionsToValidate.length === 0) {
      return undefined
    }

    let ignore = false

    Promise.all(
      actionsToValidate.map(async (action) => {
        const result = await autorizarPermiso({ permission: action.permission })
        return [action.permission, result.authorized]
      }),
    )
      .then((entries) => {
        if (!ignore) {
          setAuthorizationError('')
          setAuthorizationMap(Object.fromEntries(entries))
        }
      })
      .catch(() => {
        if (!ignore) {
          setAuthorizationError('No se pudo validar los permisos de backend para esta sesión.')
        }
      })

    return () => {
      ignore = true
    }
  }, [sessionData])

  if (isLoading) {
    return (
      <main className="dashboard-shell">
        <section className="dashboard-frame dashboard-frame--compact">
          <p className="auth-subtitle">Cargando sesión</p>
          <h1>Preparando tu inicio</h1>
          <p className="dashboard-copy">Estamos verificando tu sesión activa.</p>
        </section>
      </main>
    )
  }

  if (errorMessage) {
    return (
      <main className="dashboard-shell">
        <section className="dashboard-frame dashboard-frame--compact">
          <p className="auth-subtitle">Error de sesión</p>
          <h1>No pudimos abrir el inicio</h1>
          <p className="banner banner--error">{errorMessage}</p>
        </section>
      </main>
    )
  }

  if (!sessionData) {
    return null
  }

  const visibleOptions = FRONTEND_OPTIONS.filter((option) =>
    sessionData.permissions.includes(option.permission),
  )

  return (
    <main className="dashboard-shell">
      <section className="dashboard-frame">
        <header className="dashboard-header">
          <p className="auth-subtitle">Sesión activa</p>
          <h1>Bienvenido al sistema</h1>
          <p className="dashboard-copy">
            Los permisos del rol activo determinan qué módulos se muestran en el
            frontend y qué acciones sensibles quedan autorizadas desde backend.
          </p>
        </header>

        <dl className="session-summary" aria-label="Resumen de sesión actual">
          <div>
            <dt>Nombre</dt>
            <dd>{sessionData.display_name}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{sessionData.email}</dd>
          </div>
          <div>
            <dt>Rol activo</dt>
            <dd>{sessionData.role_label}</dd>
          </div>
        </dl>

        <section className="dashboard-section">
          <div className="section-heading">
            <h2>Opciones visibles por permisos</h2>
            <p>Chequeo local en frontend sobre los permisos del rol actual.</p>
          </div>

          <div className="permission-grid">
            {visibleOptions.map((option) => (
              <article key={option.permission} className="permission-card">
                <span className="permission-code">{option.permission}</span>
                <h3>{option.title}</h3>
                <p>{option.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="dashboard-section">
          <div className="section-heading">
            <h2>Validación backend de acciones</h2>
            <p>
              Antes de una operación sensible, el frontend consulta al backend si el
              rol activo conserva el permiso requerido.
            </p>
          </div>

          {authorizationError ? (
            <p className="banner banner--error">{authorizationError}</p>
          ) : null}

          <div className="backend-grid">
            {BACKEND_ACTIONS.map((action) => {
              const hasPermissionInRole = sessionData.permissions.includes(action.permission)
              const isAuthorized = authorizationMap[action.permission]

              return (
                <article key={action.permission} className="backend-card">
                  <span className="permission-code">{action.permission}</span>
                  <h3>{action.title}</h3>
                  <p>
                    {hasPermissionInRole
                      ? isAuthorized === undefined
                        ? 'Validando acceso real contra backend...'
                        : isAuthorized
                          ? 'Backend confirmó el permiso para ejecutar esta acción.'
                          : 'El backend no autorizó esta acción para la sesión actual.'
                      : 'El rol actual no expone este permiso en frontend.'}
                  </p>
                </article>
              )
            })}
          </div>
        </section>
      </section>
    </main>
  )
}

export default InicioPage
