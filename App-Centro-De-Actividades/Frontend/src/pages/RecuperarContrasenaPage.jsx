import { useState } from 'react'
import { Link } from 'react-router-dom'
import { solicitarRecuperacion } from '../api/recuperar_contrasena'
import './LoginPage.css' // Reusing login styles for consistency

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function RecuperarContrasenaPage() {
  const [email, setEmail] = useState('')
  const [fieldError, setFieldError] = useState('')
  const [requestError, setRequestError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  function handleChange(event) {
    setEmail(event.target.value)
    if (fieldError) setFieldError('')
    if (requestError) setRequestError('')
    if (successMessage) setSuccessMessage('')
  }

  async function handleSubmit(event) {
    event.preventDefault()

    const trimmedEmail = email.trim().toLowerCase()
    
    if (!trimmedEmail) {
      setFieldError('El email es obligatorio.')
      return
    } else if (!EMAIL_PATTERN.test(trimmedEmail)) {
      setFieldError('Ingresá un email válido.')
      return
    }

    setIsSubmitting(true)
    setRequestError('')
    setSuccessMessage('')

    try {
      const result = await solicitarRecuperacion(trimmedEmail)
      setSuccessMessage(result.message || 'Se ha enviado un email con las instrucciones para recuperar su contraseña')
      setEmail('')
    } catch (error) {
      if (error?.data?.status === 'validation_error' && error.data.errors?.email) {
        setFieldError(error.data.errors.email)
      } else {
        setRequestError(error?.data?.message || 'El email ingresado no se encuentra registrado.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-frame">
        <header className="auth-header">
          <p className="auth-subtitle">Recuperar contraseña</p>
          <h1>Centro de actividades deportivas</h1>
        </header>

        <div className="auth-form-shell">
          {successMessage ? (
            <p className="banner banner--success" role="status">
              {successMessage}
            </p>
          ) : null}

          {requestError ? (
            <p className="banner banner--error" role="alert">
              {requestError}
            </p>
          ) : null}

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <p className="dashboard-copy" style={{ marginBottom: '1rem' }}>
              Ingresá tu email y te enviaremos las instrucciones para recuperar tu contraseña.
            </p>

            <label className="field">
              <span>Email</span>
              <input
                autoComplete="email"
                name="email"
                type="email"
                value={email}
                onChange={handleChange}
                aria-invalid={fieldError ? 'true' : 'false'}
              />
              {fieldError ? <small>{fieldError}</small> : null}
            </label>

            <button className="primary-action" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Enviando...' : 'Recuperar contraseña'}
            </button>

            <p className="login-register-copy">
              <Link className="login-register-link" to="/login">
                Volver al inicio de sesión
              </Link>
            </p>
          </form>
        </div>
      </section>
    </main>
  )
}

export default RecuperarContrasenaPage
