import './UsuarioCard.css'

export default function UsuarioCard({ usuario, onEdit, onToggleStatus }) {
  return (
    <article className="usuario-card">
      
      {/* Cabecera de la tarjeta */}
      <div className="usuario-card__header">
        <div>
          <h2 className="usuario-card__title">{usuario.nombre}</h2>
          <p className="usuario-card__subtitle">DNI: {usuario.dni}</p>
        </div>
        {/* Un badge para el rol (Alumno, Profesor, Admin) */}
        <span className="usuario-card__badge">{usuario.rol}</span>
      </div>

      {/* Cuerpo con la metadata del usuario */}
      <div className="usuario-card__meta-grid">
        <div className="usuario-card__meta-item">
          <span className="usuario-card__label">Email</span>
          <span className="usuario-card__value">{usuario.mail}</span>
        </div>
      </div>

      {/* Acciones de la tarjeta */}
      <div className="usuario-card__footer">
        <div className="usuario-card__note">ID: {usuario.id}</div>
        <div className="usuario-card__actions">
          <button type="button" className="secondary-action" onClick={() => onEdit(usuario)}>
            Editar
          </button>
          <button type="button" className="primary-action" onClick={() => onToggleStatus(usuario)}>
            Dar de Baja
          </button>
        </div>
      </div>

    </article>
  )
}