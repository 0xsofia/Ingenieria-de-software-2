import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { actualizarPerfil } from '../../api/perfil'
import { useAuth } from '../../hooks/useAuth'

function PerfilUpdateForm() {
  const navigate = useNavigate()
  const { session, setAuthenticatedSession, isBootstrapping } = useAuth()
  const [formValues, setFormValues] = useState({})
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState(null)
  const [isSaving, setIsSaving] = useState(false)

  if (isBootstrapping) {
    return <div>Cargando perfil...</div>
  }

  if (!session) {
    return <div>No hay sesión activa.</div>
  }

  const emailValue = formValues.email ?? session.email ?? ''
  const interesesValue = formValues.intereses ?? session.intereses ?? ''

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormValues((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsSaving(true)
    setMessage(null)
    setErrors({})

    let data

    try {
      data = await actualizarPerfil({
        email: emailValue,
        intereses: interesesValue,
      })
    } catch (error) {
      const responseErrors = error.data?.errors
      if (responseErrors) {
        setErrors(responseErrors)
      } else {
        console.error('Fallo la request de actualizar perfil', error)
        setMessage(
          error.data?.message || 'No fue posible actualizar el perfil. Intentalo nuevamente.',
        )
      }

      setIsSaving(false)
      return
    }

    try {
      const updatedProfile = data?.profile || {
        email: emailValue,
        intereses: interesesValue,
      }

      setAuthenticatedSession({ ...session, ...updatedProfile })
      navigate('/verperfil')
    } catch (error) {
      console.error('La API devolvio 200 pero fallo el frontend al aplicar el perfil', error)
      setMessage('El perfil se actualizo, pero hubo un problema al refrescar la pantalla.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="profile-update-form">

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
            value={emailValue}
            onChange={handleChange}
            placeholder="Ingrese un email"
          />
          {errors.email ? <span className="form-error">{errors.email}</span> : null}
        </div>

        <div className="profile-update-field">
          <label htmlFor="intereses">Intereses</label>
          <textarea
            id="intereses"
            name="intereses"
            value={interesesValue}
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
