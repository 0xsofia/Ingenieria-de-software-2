import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { cambiarContrasena, validarToken } from '../api/cambiar_contrasena'
import './LoginPage.css' // Reusing auth styles

function CambiarContrasenaPage() {
  const { token } = useParams()
  const navigate = useNavigate()
  
  const [form, setForm] = useState({
    current_password: '',
    new_password: '',
    repeat_password: ''
  })
  
  const [fieldErrors, setFieldErrors] = useState({})
  const [requestError, setRequestError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isValidatingToken, setIsValidatingToken] = useState(!!token)

  useEffect(() => {
    if (token) {
      validarToken(token)
        .then(() => {
          setIsValidatingToken(false)
        })
        .catch((error) => {
          const errorMessage = error?.data?.message || 'Token inválido'
          navigate('/login', { state: { flashMessage: errorMessage, flashType: 'error' } })
        })
    }
  }, [token, navigate])

  function handleChange(event) {
    const { name, value } = event.target
    setForm(prev => ({ ...prev, [name]: value }))
    
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const next = { ...prev }
        delete next[name]
        return next
      })
    }
    if (requestError) setRequestError('')
    if (successMessage) setSuccessMessage('')
  }

  async function handleSubmit(event) {
    event.preventDefault()

    const errors = {}
    if (!token && !form.current_password) {
      errors.current_password = 'La contraseña actual es obligatoria.'
    }
    if (!form.new_password) {
      errors.new_password = 'La nueva contraseña es obligatoria.'
    } else if (form.new_password.length < 6 || form.new_password.length > 12) {
      errors.new_password = 'La contraseña debe tener entre 6 a 12 caracteres.'
    }
    
    if (!form.repeat_password) {
      errors.repeat_password = 'Repetir la contraseña es obligatorio.'
    }
    
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors)
      return
    }

    if (form.new_password !== form.repeat_password) {
      setFieldErrors({ repeat_password: 'La contraseña ingresada no coincide con la ingresada en Contraseña nueva' })
      return
    }

    setIsSubmitting(true)
    setRequestError('')
    setSuccessMessage('')

    try {
      const payload = {
        new_password: form.new_password,
        repeat_password: form.repeat_password
      }
      
      if (token) {
        payload.token = token
      } else {
        payload.current_password = form.current_password
      }

      const result = await cambiarContrasena(payload)
      
      if (token) {
        navigate('/login', { state: { flashMessage: result.message || 'Su contraseña ha sido cambiada exitosamente' } })
      } else {
        navigate('/verperfil', { state: { flashMessage: result.message || 'Su contraseña ha sido cambiada exitosamente' } })
      }
      
    } catch (error) {
      if (error?.data?.status === 'validation_error' && error.data.errors) {
        setFieldErrors(error.data.errors)
      } else {
        const errorMessage = error?.data?.message || 'Error al cambiar la contraseña.'
        if (token && errorMessage === 'Este email de recuperacion ya ha sido utilizado, recupere su contraseña nuevamente') {
          navigate('/login', { state: { flashMessage: errorMessage, flashType: 'error' } })
        } else {
          setRequestError(errorMessage)
        }
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isValidatingToken) {
    return (
      <main className="auth-shell">
        <section className="auth-frame auth-frame--compact">
          <header className="auth-header">
            <p className="auth-subtitle">Seguridad</p>
            <h1>Cambiar contraseña</h1>
          </header>
          <p className="dashboard-copy">Validando enlace de recuperación...</p>
        </section>
      </main>
    )
  }

  return (
    <main className="auth-shell">
      <section className="auth-frame">
        <header className="auth-header">
          <p className="auth-subtitle">Seguridad</p>
          <h1>Cambiar contraseña</h1>
        </header>

        <div className="auth-form-shell">
          {successMessage ? (
            <div className="banner banner--success" role="status">
              {successMessage}
            <button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>
          ) : null}

          {requestError ? (
            <div className="banner banner--error" role="alert">
              {requestError}
            <button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>
          ) : null}

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            {!token && (
              <label className="field">
                <span>Contraseña actual</span>
                <input
                  name="current_password"
                  type="password"
                  value={form.current_password}
                  onChange={handleChange}
                  aria-invalid={fieldErrors.current_password ? 'true' : 'false'}
                />
                {fieldErrors.current_password ? <small>{fieldErrors.current_password}</small> : null}
              </label>
            )}

            <label className="field">
              <span>Contraseña nueva</span>
              <input
                name="new_password"
                type="password"
                value={form.new_password}
                onChange={handleChange}
                aria-invalid={fieldErrors.new_password ? 'true' : 'false'}
              />
              {fieldErrors.new_password ? <small>{fieldErrors.new_password}</small> : null}
            </label>

            <label className="field">
              <span>Repetir contraseña</span>
              <input
                name="repeat_password"
                type="password"
                value={form.repeat_password}
                onChange={handleChange}
                aria-invalid={fieldErrors.repeat_password ? 'true' : 'false'}
              />
              {fieldErrors.repeat_password ? <small>{fieldErrors.repeat_password}</small> : null}
            </label>

            <button className="primary-action" type="submit" disabled={isSubmitting || !!successMessage}>
              {isSubmitting ? 'Cambiando...' : 'Cambiar contraseña'}
            </button>
            
            {!token && (
              <button 
                type="button" 
                className="secondary-action" 
                onClick={() => navigate(-1)}
                style={{ marginTop: '1rem', background: 'transparent', border: '1px solid #ccc', padding: '0.75rem', borderRadius: '4px', cursor: 'pointer' }}
              >
                Cancelar
              </button>
            )}
          </form>
        </div>
      </section>
    </main>
  )
}

export default CambiarContrasenaPage
