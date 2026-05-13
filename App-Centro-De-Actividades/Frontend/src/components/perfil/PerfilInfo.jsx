import { useAuth } from '../../hooks/useAuth'

function PerfilInfo({ hideRole = false }) {
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
          <strong>Nombre: </strong> {session.display_name}
        </li>
        <li>
          <strong>Email: </strong> {session.email}
        </li>
        {!hideRole ? (
          <li>
            <strong>Rol de usuario:</strong> {session.role_label}
          </li>
        ) : null}
      </ul>
    </div>
  )
}

export default PerfilInfo; 