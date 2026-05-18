import { useState } from 'react'

import './DynamicForm.css'

function DynamicForm({
  fields,
  initialValues,
  schema,
  onSubmit,
  submitLabel,
  isSubmitting = false,
  serverErrors = {},
  generalError = '',
  errorCycle = 0,
}) {
  const [values, setValues] = useState(() => initialValues)
  const [clientErrors, setClientErrors] = useState({})
  const [dismissedErrorState, setDismissedErrorState] = useState({
    cycle: errorCycle,
    serverFields: {},
    general: false,
  })

  const hasFreshErrors = dismissedErrorState.cycle !== errorCycle
  const dismissedServerErrors = hasFreshErrors ? {} : dismissedErrorState.serverFields
  const dismissedGeneralError = hasFreshErrors ? false : dismissedErrorState.general

  function handleChange(event) {
    const { name, value } = event.target

    setValues((currentValues) => ({
      ...currentValues,
      [name]: value,
    }))

    if (clientErrors[name]) {
      setClientErrors((currentErrors) => {
        const nextErrors = { ...currentErrors }
        delete nextErrors[name]
        return nextErrors
      })
    }

    if (serverErrors[name]) {
      setDismissedErrorState((currentState) => ({
        ...currentState,
        cycle: errorCycle,
        serverFields: {
          ...currentState.serverFields,
          [name]: true,
        },
      }))
    }

    if (generalError) {
      setDismissedErrorState((currentState) => ({
        ...currentState,
        cycle: errorCycle,
        general: true,
      }))
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()

    const result = schema.safeParse(values)
    if (!result.success) {
      setClientErrors(mapZodErrors(result.error.issues))
      return
    }

    setClientErrors({})
    await onSubmit(result.data)
  }

  return (
    <form className="dynamic-form" onSubmit={handleSubmit} noValidate>
      {!dismissedGeneralError && generalError ? (
        <p className="banner banner--error" role="alert">
          {generalError}
        </p>
      ) : null}

      <div className="dynamic-form__grid">
        {fields.map((field) => {
          const fieldError =
            clientErrors[field.name] ||
            (!dismissedServerErrors[field.name] ? serverErrors[field.name] : '')
          const fieldClassName = field.fullWidth
            ? 'field dynamic-form__field--full'
            : 'field'

          return (
            <label key={field.name} className={fieldClassName}>
              <span>{field.label}</span>
              {field.type === 'textarea' ? (
                <textarea
                  name={field.name}
                  value={values[field.name] || ''}
                  onChange={handleChange}
                  autoComplete={field.autoComplete}
                  placeholder={field.placeholder}
                  rows={field.rows || 4}
                  disabled={field.disabled}
                  readOnly={field.readOnly}
                  aria-invalid={fieldError ? 'true' : 'false'}
                />
              ) : (
                <input
                  name={field.name}
                  type={field.type}
                  value={values[field.name] || ''}
                  onChange={handleChange}
                  autoComplete={field.autoComplete}
                  inputMode={field.inputMode}
                  placeholder={field.placeholder}
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  disabled={field.disabled}
                  readOnly={field.readOnly}
                  aria-invalid={fieldError ? 'true' : 'false'}
                />
              )}

              {fieldError ? <small>{fieldError}</small> : null}
              {!fieldError && field.hint ? <p className="field-hint">{field.hint}</p> : null}
            </label>
          )
        })}
      </div>

      <div className="dynamic-form__actions">
        <button className="primary-action" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Enviando...' : submitLabel}
        </button>
      </div>
    </form>
  )
}

function mapZodErrors(issues) {
  const errors = {}

  for (const issue of issues) {
    const fieldName = issue.path[0]
    if (!fieldName || errors[fieldName]) {
      continue
    }

    errors[fieldName] = issue.message
  }

  return errors
}

export default DynamicForm
