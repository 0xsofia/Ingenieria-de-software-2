import { useState } from 'react'
import { createPortal } from 'react-dom'
import './BloquearUsuarioModal.css'

export default function BloquearUsuarioModal({
  user,
  onClose,
  onConfirm,
  isSubmitting,
  error
}) {
  const [motivo, setMotivo] = useState('')
  const [devolverDinero, setDevolverDinero] = useState(false)

  if (!user) return null

  return createPortal(
    <div className="bloquear-usuario-modal" role="presentation">
      <div className="bloquear-usuario-modal__backdrop" onClick={onClose} />
      <section 
        className="bloquear-usuario-modal__dialog" 
        role="dialog" 
        aria-modal="true"
        aria-labelledby="bloquear-usuario-title"
      >
        <h2 id="bloquear-usuario-title">Bloquear a {user.nombre_completo}</h2>
        
        {error ? (
          <div className="banner banner--error" role="alert" style={{ marginBottom: '1rem' }}>
            {error}
          <button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>
        ) : null}

        <div className="bloquear-usuario-modal__body">
          <div className="form-group">
            <label htmlFor="motivo">Motivo de bloqueo</label>
            <input
              id="motivo"
              type="text"
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              placeholder="Ej: Socio problemático"
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={devolverDinero}
                onChange={(e) => setDevolverDinero(e.target.checked)}
                disabled={isSubmitting}
              />
              ¿Devolución del dinero de reservas activas?
            </label>
          </div>
        </div>

        <div className="bloquear-usuario-modal__actions">
          <button
            type="button"
            className="secondary-action"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancelar
          </button>
          <button
            type="button"
            className="primary-action danger"
            onClick={() => onConfirm({ motivo, devolver_dinero: devolverDinero })}
            disabled={isSubmitting || !motivo.trim()}
          >
            Bloquear Usuario
          </button>
        </div>
      </section>
    </div>,
    document.body
  )
}
