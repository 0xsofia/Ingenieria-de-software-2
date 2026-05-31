import './FilterForm.css'

function normalizeValues(values, fields) {
  return fields.reduce((accumulator, field) => {
    const value = values[field.name]
    accumulator[field.name] = typeof value === 'string' ? value.trim() : value ?? ''
    return accumulator
  }, {})
}

function getOptionValue(option) {
  return typeof option === 'string' ? option : option.value
}

function getOptionLabel(option) {
  return typeof option === 'string' ? option : option.label
}

export default function FilterForm({
  title,
  description = '',
  fields,
  initialValues,
  onSubmit,
  submitLabel = 'Filtrar',
  isSubmitting = false,
}) {
  const formKey = JSON.stringify([fields.map(({ name }) => name), initialValues])

  function handleSubmit(event) {
    event.preventDefault()

    const formData = new FormData(event.currentTarget)
    const values = fields.reduce((accumulator, field) => {
      accumulator[field.name] = formData.get(field.name) ?? ''
      return accumulator
    }, {})

    onSubmit(normalizeValues(values, fields))
  }

  return (
    <section className="filter-form-card">
      <div className="filter-form-card__title">
        <p className="auth-subtitle">Filtros</p>
        <h2>{title}</h2>
        {description ? <p className="dashboard-copy">{description}</p> : null}
      </div>

      <form key={formKey} className="filter-form" onSubmit={handleSubmit}>
        <div className="filter-form__grid">
          {fields.map((field) => {
            const commonProps = {
              id: field.name,
              name: field.name,
              defaultValue: initialValues[field.name] ?? '',
              disabled: isSubmitting,
            }

            return (
              <label key={field.name} className="field">
                <span>{field.label}</span>

                {field.type === 'select' ? (
                  <select className="filter-form__control" {...commonProps}>
                    <option value="">{field.placeholder || 'Todos'}</option>
                    {field.options.map((option) => (
                      <option key={getOptionValue(option)} value={getOptionValue(option)}>
                        {getOptionLabel(option)}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    className="filter-form__control"
                    type={field.type || 'text'}
                    placeholder={field.placeholder || ''}
                    autoComplete={field.autoComplete || 'off'}
                    inputMode={field.inputMode}
                    {...commonProps}
                  />
                )}
              </label>
            )
          })}
        </div>

        <div className="filter-form__actions">
          <button type="submit" className="primary-action" disabled={isSubmitting}>
            {isSubmitting ? 'Buscando...' : submitLabel}
          </button>
        </div>
      </form>
    </section>
  )
}
