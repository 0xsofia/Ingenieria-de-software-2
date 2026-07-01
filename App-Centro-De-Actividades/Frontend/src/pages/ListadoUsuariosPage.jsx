import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { createPortal } from 'react-dom'

import { listarUsuarios, bloquearUsuario, desbloquearUsuario } from '../api/usuarios'
import FiltroUsuarios from '../components/usuarios/FiltroUsuarios'
import ListadoUsuarios from '../components/usuarios/ListadoUsuarios'
import BloquearUsuarioModal from '../components/usuarios/BloquearUsuarioModal'
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
  const [successMessages, setSuccessMessages] = useState([])
  
  const [userToBlock, setUserToBlock] = useState(null)
  const [isBlocking, setIsBlocking] = useState(false)
  const [blockError, setBlockError] = useState('')

  const [userToUnblock, setUserToUnblock] = useState(null)
  const [isUnblocking, setIsUnblocking] = useState(false)
  const [unblockError, setUnblockError] = useState('')

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
    setSuccessMessages([])

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

  async function handleUnblockUser(user) {
    setUserToUnblock(user)
  }

  async function handleConfirmUnblock() {
    setIsUnblocking(true)
    setUnblockError('')
    setSuccessMessages([])

    try {
      const unblockResult = await desbloquearUsuario(userToUnblock.persona_id)
      setSuccessMessages([unblockResult.message || `El usuario ${userToUnblock.nombre_completo} ha sido desbloqueado exitosamente.`])
      setUserToUnblock(null)
      // Refresh list
      const result = await listarUsuarios(submittedFilters)
      setUsers(result.users || [])
    } catch (requestError) {
      setUnblockError(requestError?.data?.message || 'Error al desbloquear el usuario.')
    } finally {
      setIsUnblocking(false)
    }
  }

  async function handleConfirmBlock({ motivo, devolver_dinero }) {
    setIsBlocking(true)
    setBlockError('')
    
    try {
      const result = await bloquearUsuario(userToBlock.persona_id, { motivo, devolver_dinero })
      setSuccessMessages(_normalizeSuccessMessages(result, `El usuario ${userToBlock.nombre_completo} ha sido bloqueado exitosamente.`))
      setUserToBlock(null)
      // Refresh list
      const listResult = await listarUsuarios(submittedFilters)
      setUsers(listResult.users || [])
    } catch (requestError) {
      setBlockError(requestError?.data?.message || 'Error al bloquear el usuario.')
    } finally {
      setIsBlocking(false)
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
            <div className="banner banner--error" role="alert">
              {error}
            <button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>
          ) : null}

          {successMessages.length ? (
            <div className="banner banner--success listado-usuarios-page__messages" role="status">
              {successMessages.map((message, index) => (
                <p key={`${message}-${index}`}>{message}</p>
              ))}
            <button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>
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
                onBlockUser={setUserToBlock}
                onUnblockUser={handleUnblockUser}
              />
            </>
          )}
        </div>
      </section>
      
      {userToBlock ? (
        <BloquearUsuarioModal
          user={userToBlock}
          onClose={() => {
            setUserToBlock(null)
            setBlockError('')
          }}
          onConfirm={handleConfirmBlock}
          isSubmitting={isBlocking}
          error={blockError}
        />
      ) : null}
      {userToUnblock ? (
        createPortal(
          <div className="bloquear-usuario-modal" role="presentation">
            <div className="bloquear-usuario-modal__backdrop" onClick={() => {
              if (!isUnblocking) setUserToUnblock(null)
            }} />
            <section
              className="bloquear-usuario-modal__dialog"
              role="dialog"
              aria-modal="true"
              aria-labelledby="desbloquear-usuario-title"
            >
              <h2 id="desbloquear-usuario-title">Confirmar desbloqueo</h2>
              <p style={{ textAlign: 'center', marginBottom: '24px', color: 'var(--text-soft)' }}>
                ¿Estás seguro de que deseas desbloquear a {userToUnblock.nombre_completo}?
              </p>
              
              {unblockError ? (
                <div className="banner banner--error" role="alert" style={{ marginBottom: '1rem' }}>
                  {unblockError}
                <button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>
              ) : null}

              <div className="bloquear-usuario-modal__actions">
                <button
                  type="button"
                  className="secondary-action"
                  onClick={() => setUserToUnblock(null)}
                  disabled={isUnblocking}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  className="primary-action"
                  onClick={handleConfirmUnblock}
                  disabled={isUnblocking}
                >
                  {isUnblocking ? 'Desbloqueando...' : 'Aceptar'}
                </button>
              </div>
            </section>
          </div>,
          document.body
        )
      ) : null}
    </section>
  )
}

function _normalizeSuccessMessages(result, fallbackMessage) {
  if (Array.isArray(result?.messages) && result.messages.length) {
    return result.messages
  }

  if (result?.message) {
    return String(result.message).split('\n').filter(Boolean)
  }

  return [fallbackMessage]
}
