import { useEffect, useState } from 'react'

import './FilterForm.css'

function buildFormValues(fields, initialValues = {}) {
  return fields.reduce((accumulator, field) => {
    accumulator[field.name] = initialValues[field.name] ?? ''
    return accumulator
  }, {})
}

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
  resetLabel = 'Limpiar',
  isSubmitting = false,
  submitOnReset = true,
}) {
  const [values, setValues] = useState(() => buildFormValues(fields, initialValues))

  useEffect(() => {
    setValues(buildFormValues(fields, initialValues))
  }, [fields, initialValues])

  function handleChange(fieldName, fieldValue) {
    setValues((currentValues) => ({
      ...currentValues,
      [fieldName]: fieldValue,
    }))
  }

  function handleSubmit(event) {
    event.preventDefault()
    onSubmit(normalizeValues(values, fields))
  }

  function handleReset() {
    const nextValues = buildFormValues(fields, {})
    setValues(nextValues)

    if (submitOnReset) {
      onSubmit(normalizeValues(nextValues, fields))
    }
  }

  return (
    <section className="filter-form-card">
      <div className="filter-form-card__title">
        <p className="auth-subtitle">Filtros</p>
        <h2>{title}</h2>
        {description ? <p className="dashboard-copy">{description}</p> : null}
      </div>

      <form className="filter-form" onSubmit={handleSubmit}>
        <div className="filter-form__grid">
          {fields.map((field) => {
            const commonProps = {
              id: field.name,
              name: field.name,
              value: values[field.name] ?? '',
              disabled: isSubmitting,
              onChange: (event) => handleChange(field.name, event.target.value),
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
          <button
            type="button"
            className="secondary-action"
            onClick={handleReset}
            disabled={isSubmitting}
          >
            {resetLabel}
          </button>
        </div>
      </form>
    </section>
  )
}
