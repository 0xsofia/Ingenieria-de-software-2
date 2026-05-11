import { createContext, useEffect, useState } from 'react'

import { obtenerSesionActual } from '../api/iniciar_sesion'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null)
  const [pendingRoles, setPendingRoles] = useState([])
  const [pendingIdentity, setPendingIdentity] = useState(null)
  const [isBootstrapping, setIsBootstrapping] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function bootstrapAuth() {
      try {
        const result = await obtenerSesionActual()
        if (cancelled) {
          return
        }

        if (result.authenticated && result.session) {
          setAuthenticatedSession(result.session)
          return
        }

        if (result.pending_role_selection) {
          setPendingRoleSelection(result)
          return
        }

        clearAuthState()
      } catch {
        if (!cancelled) {
          clearAuthState()
        }
      } finally {
        if (!cancelled) {
          setIsBootstrapping(false)
        }
      }
    }

    bootstrapAuth()

    return () => {
      cancelled = true
    }
  }, [])

  function setAuthenticatedSession(nextSession) {
    setSession(nextSession)
    setPendingRoles([])
    setPendingIdentity(null)
  }

  function setPendingRoleSelection(result) {
    setSession(null)
    setPendingRoles(result.available_roles || [])
    setPendingIdentity(result.identity || null)
  }

  function clearAuthState() {
    setSession(null)
    setPendingRoles([])
    setPendingIdentity(null)
  }

  function hasPermission(permissionCode) {
    return Boolean(session?.permissions?.includes(permissionCode))
  }

  const value = {
    clearAuth: clearAuthState,
    hasPendingRoleSelection: pendingRoles.length > 0,
    hasPermission,
    isAuthenticated: Boolean(session),
    isBootstrapping,
    pendingIdentity,
    pendingRoles,
    session,
    setAuthenticatedSession,
    setPendingRoleSelection,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export { AuthContext }
