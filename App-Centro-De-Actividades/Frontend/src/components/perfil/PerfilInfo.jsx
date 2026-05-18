import { useAuth } from '../../hooks/useAuth'

function PerfilInfo() {
  const { session, isBootstrapping } = useAuth()

  if (isBootstrapping) {
    return <div>Cargando sesión...</div>
  }

  if (!session) {
    return <div>No hay sesión activa.</div>
  }

  return (
    <div className="info-container">
      <ul>
        <li>
          <strong>Nombre:</strong> {session.nombre}
        </li>
        <li>
          <strong>Apellido:</strong> {session.apellido}
        </li>
        <li>
          <strong>DNI:</strong> {session.dni}
        </li>
        <li>
          <strong>Email:</strong> {session.email}
        </li>
       
      </ul>
      <div>
        <h2>Mis intereses</h2>
        <ul>
          <li>
            {session.intereses || 'No definidos'}
          </li>
        </ul>
      </div>
    </div>
  )
}

export default PerfilInfo
