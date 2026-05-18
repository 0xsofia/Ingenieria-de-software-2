import { useEffect, useState } from 'react'
import { listarUsuarios } from '../api/usuarios'
import UsuarioCard from '../components/UsuarioCard'
import './ListadoUsuariosPage.css' // Importamos el CSS que creamos arriba

export default function ListadoUsuariosPage() {
  const [usuarios, setUsuarios] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Estados de los 3 filtros
  const [nombre, setNombre] = useState('')
  const [dni, setDni] = useState('')
  const [mail, setMail] = useState('')

  useEffect(() => {
    const fetchUsuarios = async () => {
      try {
        setLoading(true)
        const result = await listarUsuarios(nombre, dni, mail)
        setUsuarios(result)
        setError('')
      } catch (err) {
        console.error(err)
        setError('No se pudieron cargar los usuarios.')
      } finally {
        setLoading(false)
      }
    }

    fetchUsuarios()
  }, [nombre, dni, mail])

  const handleEditUser = (usuario) => {
    console.log('Editar usuario:', usuario)
  }

  const handleToggleStatus = (usuario) => {
    console.log('Dar de baja/alta:', usuario)
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame">
        
        {/* Encabezado */}
        <div className="listado-usuarios__header-row">
          <h1>Control de Usuarios</h1>
          <p className="dashboard-copy">Filtrá el padrón por cualquiera de los siguientes campos en tiempo real.</p>
        </div>

        {loading && usuarios.length === 0 ? (
          <p>Cargando lista de usuarios...</p>
        ) : error ? (
          <p style={{ color: 'red' }}>{error}</p>
        ) : (
          <div className="listado-usuarios__controls">
            
            {/* Fila con los 3 Inputs estilizados */}
            <div className="listado-usuarios__filters-row">
              <div className="listado-usuarios__filter-group">
                <label htmlFor="input-nombre">Nombre o Apellido</label>
                <input
                  id="input-nombre"
                  type="text"
                  placeholder="Ej: Juan Carlos"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  className="listado-usuarios__input"
                />
              </div>

              <div className="listado-usuarios__filter-group">
                <label htmlFor="input-dni">Documento (DNI)</label>
                <input
                  id="input-dni"
                  type="text"
                  placeholder="Ej: 38234123"
                  value={dni}
                  onChange={(e) => setDni(e.target.value)}
                  className="listado-usuarios__input"
                />
              </div>

              <div className="listado-usuarios__filter-group">
                <label htmlFor="input-mail">Correo Electrónico</label>
                <input
                  id="input-mail"
                  type="text"
                  placeholder="Ej: socio@gmail.com"
                  value={mail}
                  onChange={(e) => setMail(e.target.value)}
                  className="listado-usuarios__input"
                />
              </div>
            </div>

            {/* Contador de registros */}
            <div className="listado-usuarios__status-row">
              <p className="dashboard-copy">{usuarios.length} usuario(s) encontrado(s)</p>
            </div>

            {/* Listado de tarjetas o mensaje vacío */}
            {usuarios.length === 0 ? (
              <div className="listado-usuarios__empty">
                No se encontraron usuarios que coincidan con los filtros ingresados.
              </div>
            ) : (
              <div className="listado-usuarios__cards">
                {usuarios.map((usuario) => (
                  <UsuarioCard
                    key={usuario.id}
                    usuario={usuario}
                    onEdit={handleEditUser}
                    onToggleStatus={handleToggleStatus}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </section>
    </section>
  )
}