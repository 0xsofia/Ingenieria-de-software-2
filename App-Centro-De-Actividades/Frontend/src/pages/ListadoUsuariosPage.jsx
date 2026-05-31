import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'

import { listarUsuarios } from '../api/usuarios'
import FiltroUsuarios from '../components/usuarios/FiltroUsuarios'
import ListadoUsuarios from '../components/usuarios/ListadoUsuarios'
import { useAuth } from '../hooks/useAuth'
import './ListadoUsuariosPage.css'

const INITIAL_USER_FILTERS = Object.freeze({
  dni: '',
  email: '',
  nombre: '',
})

export default function ListadoUsuariosPage() {
  const { session } = useAuth()
  const [users, setUsers] = useState([])
  const [submittedFilters, setSubmittedFilters] = useState(INITIAL_USER_FILTERS)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const canViewUsers = session?.role === 'administrador' || session?.role === 'empleado'
  const canManageUsers = session?.role === 'administrador'

  useEffect(() => {
    if (!canViewUsers) {
      return
    }

    let cancelled = false

    async function loadInitialUsers() {
      setIsLoading(true)
      setError('')

      try {
        const result = await listarUsuarios(INITIAL_USER_FILTERS)
        if (!cancelled) {
          setUsers(result.users || [])
          setSubmittedFilters(INITIAL_USER_FILTERS)
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError?.data?.message || "No se encontraron usuarios registrados.")
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadInitialUsers()

    return () => {
      cancelled = true
    }
  }, [canViewUsers])

  const hasActiveFilters = useMemo(
    () => Object.values(submittedFilters).some(Boolean),
    [submittedFilters]
  )

  if (!canViewUsers) {
    return <Navigate to="/inicio" replace />
  }

  async function handleFilterSubmit(nextFilters) {
    setIsLoading(true)
    setError('')

    try {
      const result = await listarUsuarios(nextFilters)
      setUsers(result.users || [])
      setSubmittedFilters(nextFilters)
    } catch (requestError) {
      setError(requestError?.data?.message || 'No se pudo filtrar el listado de usuarios.')
    } finally {
      setIsLoading(false)
    }
  }

  const emptyMessage = hasActiveFilters
    ? 'No se encontraron usuarios para el filtro aplicado.'
    : 'No se encontraron usuarios registrados.'

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame listado-usuarios-page">
        <div className="listado-usuarios-page__header-row">
          <div>
            <p className="auth-subtitle">Administración</p>
            <h1>Usuarios</h1>
            {/* <p className="dashboard-copy">
              Todos los usuarios se muestran en una sola tabla y el rol indica si es socio o empleado.
            </p> */}
          </div>

          <div className="listado-usuarios-page__header-actions">
            <Link className="secondary-action" to="/inicio">
              Volver al inicio
            </Link>
            {canManageUsers ? (
              <Link className="primary-action" to="/usuarios/registrar-empleado">
                Registrar empleado
              </Link>
            ) : null}
          </div>
        </div>

        <div className="listado-usuarios-page__content">
          <FiltroUsuarios
            initialValues={submittedFilters}
            onSubmit={handleFilterSubmit}
            isSubmitting={isLoading}
          />

          {error ? (
            <p className="banner banner--error" role="alert">
              {error}
            </p>
          ) : null}

          {isLoading ? (
            <p className="dashboard-copy">Cargando usuarios...</p>
          ) : (
            <>
              <div className="listado-usuarios-page__status-row">
                <p className="dashboard-copy">{users.length} usuario(s) encontrados</p>
              </div>

              <ListadoUsuarios
                users={users}
                emptyMessage={emptyMessage}
                canManageUsers={canManageUsers}
              />
            </>
          )}
        </div>
      </section>
    </section>
  )
}
