// src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from 'react'
import { obtenerSesionActual } from '../api/iniciar_sesion'

const AuthContext = createContext()

export const AuthProvider = ({ children }) => {
  const [sessionData, setSessionData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const actualizarSesion = async () => {
    setIsLoading(true)
    try {
      const result = await obtenerSesionActual()
      setSessionData(result.authenticated ? result.session : null)
    } catch (error) {
      setSessionData(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    actualizarSesion()
  }, [])

  return (
    <AuthContext.Provider value={{ sessionData, isLoading, actualizarSesion }}>
      {children}
    </AuthContext.Provider>
  )
}

// Custom Hook para usar la sesión fácilmente
export const useAuth = () => useContext(AuthContext)