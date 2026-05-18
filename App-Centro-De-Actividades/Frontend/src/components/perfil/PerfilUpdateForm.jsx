import { useEffect, useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { actualizarPerfil } from '../../api/perfil'

function PerfilUpdateForm() {
  const { session, setAuthenticatedSession, isBootstrapping } = useAuth()
  const [formValues, setFormValues] = useState({ email: '', intereses: '' })
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState(null)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (!isBootstrapping && session) {
      setFormValues({
        email: session.email || '',
        intereses: session.intereses || '',
      })
    }
  }, [isBootstrapping, session])

  if (isBootstrapping) {
    return <div>Cargando perfil...</div>
  }

  if (!session) {
    return <div>No hay sesión activa.</div>
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormValues((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsSaving(true)
    setMessage(null)
    setErrors({})

    try {
      const data = await actualizarPerfil(formValues)
      const updatedProfile = data.profile
      setAuthenticatedSession({ ...session, ...updatedProfile })
    } catch (error) {
      const responseErrors = error.data?.errors
      if (responseErrors) {
        setErrors(responseErrors)
      } else {
        setMessage(
          error.data?.message ||
            'No fue posible actualizar el perfil. Intentalo nuevamente.',
        )
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="profile-update-form">
      <div className="form-header">
        <h2>Actualizar perfil</h2>
      </div>

      <form onSubmit={handleSubmit} className="profile-update-form__form">
        <div className="profile-update-field">
          <label htmlFor="nombre">Nombre</label>
          <input id="nombre" type="text" value={session.nombre || ''} disabled />
        </div>

        <div className="profile-update-field">
          <label htmlFor="apellido">Apellido</label>
          <input id="apellido" type="text" value={session.apellido || ''} disabled />
        </div>

        <div className="profile-update-field">
          <label htmlFor="dni">DNI</label>
          <input id="dni" type="text" value={session.dni || ''} disabled />
        </div>

        <div className="profile-update-field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            value={formValues.email}
            onChange={handleChange}
            placeholder="Ingrese un email"
          />
          {errors.email ? (
            <span className="form-error">{errors.email}</span>
          ) : null}
        </div>

        <div className="profile-update-field">
          <label htmlFor="intereses">Intereses</label>
          <textarea
            id="intereses"
            name="intereses"
            value={formValues.intereses}
            onChange={handleChange}
            placeholder="Ej: Me gusta jugar al padel"
            rows={4}
          />
        </div>

        <button type="submit" className="primary-action" disabled={isSaving}>
          {isSaving ? 'Guardando...' : 'Actualizar perfil'}
        </button>

        {message ? <div className="form-message">{message}</div> : null}
      </form>
    </section>
  )
}

export default PerfilUpdateForm
