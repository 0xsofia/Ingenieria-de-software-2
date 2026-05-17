import './ActividadFilter.css'

export function ActividadFilter({ value, options, onChange }) {
  return (
    <section className="actividad-filter">
      <div className="actividad-filter__title">
        <p className="auth-subtitle">Filtrar clases</p>
        <h2>Actividad</h2>
      </div>

      <label className="field">
        <span>Actividad</span>
        <select
          className="actividad-filter__select"
          value={value}
          onChange={(event) => onChange(event.target.value)}
        >
          <option value="">Todas las actividades</option>
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
    </section>
  )
}
