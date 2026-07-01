import './ClaseCard.css'

const currencyFormatter = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
  minimumFractionDigits: 2,
})

export default function ClaseCard({
  clase,
  onView,
  onScanQR,
  onReserve,
  onCancel,
  viewLabel = 'Ver',
  reserveLabel = 'Inscribirme',
  cancelLabel = 'Cancelar clase',
  viewScanLabel = 'Escanear QR',
  onExtend,
  extendLabel = 'Crear siguientes clases', // Prop configurable para mantener consistencia

}) {
  return (
    <article className="clase-card">
      <div className="clase-card__header">
        <div>
          <h2 className="clase-card__title">{clase.actividad}</h2>
          <p className="clase-card__subtitle">{clase.tipo_clase} · {clase.nivel}</p>
        </div>
        <span className="clase-card__badge">{clase.cupos}/{Math.max(0, clase.cupos - (clase.cupos_ocupados || 0))} cupos</span>
      </div>

      <div className="clase-card__meta-grid">
        <div className="clase-card__meta-item">
          <span className="clase-card__label">Fecha</span>
          <span className="clase-card__value">{clase.fecha ? clase.fecha.split('-').reverse().join('/') : ''}</span>
        </div>
        <div className="clase-card__meta-item">
          <span className="clase-card__label">Horario</span>
          <span className="clase-card__value">{clase.horario_inicio} - {clase.horario_fin}</span>
        </div>
        <div className="clase-card__meta-item">
          <span className="clase-card__label">Precio</span>
          <span className="clase-card__value">
            {clase.precio !== undefined && clase.precio !== null
              ? currencyFormatter.format(Number(clase.precio))
              : 'Sin precio'}
          </span>
        </div>
        <div className="clase-card__meta-item">
          <span className="clase-card__label">Cancha</span>
          <span className="clase-card__value">{clase.cancha}</span>
        </div>
        <div className="clase-card__meta-item">
          <span className="clase-card__label">Profesor</span>
          <span className="clase-card__value">{clase.profesor_nombre || clase.profesor_id}</span>
        </div>
      </div>

      <div className="clase-card__footer">
        <div className="clase-card__note">ID: {clase.clase_id}</div>
        <div className="clase-card__actions">
          {onScanQR && (
              <button type="button" className="secondary-action scan-qr-action" onClick={() => onScanQR(clase)}>
                {viewScanLabel}
              </button>
            )}
          <button type="button" className="secondary-action" onClick={() => onView(clase)}>
            {viewLabel}
          </button>
          {onReserve && (
            <button type="button" className="primary-action" onClick={() => onReserve(clase)}>
              {reserveLabel}
            </button>
          )}
          {onCancel && (
            <button type="button" className="danger-action" onClick={() => onCancel(clase)}>
              {cancelLabel}
            </button>
          )}
         {/* Mismo estilo secundario que "Ver detalle", controlado externamente */}
          {onExtend && (
            <button type="button" className="secondary-action" onClick={() => onExtend(clase)}>
              {extendLabel}
            </button>
          )}


        </div>
      </div>
    </article>
  )
}
