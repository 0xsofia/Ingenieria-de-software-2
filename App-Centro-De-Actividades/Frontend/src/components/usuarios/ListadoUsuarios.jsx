import { Link } from 'react-router-dom'

import SectionedTableList from '../listing/SectionedTableList'

const USER_COLUMNS = [
  {
    key: 'nombre_completo',
    header: 'Usuario',
    render: (user) => (
      <div className="sectioned-table-list__primary-cell">
        <strong>{user.nombre_completo}</strong>
        <span>{user.estado}</span>
      </div>
    ),
  },
  {
    key: 'dni',
    header: 'DNI',
  },
  {
    key: 'email',
    header: 'Email',
  },
  {
    key: 'telefono',
    header: 'Teléfono',
  },
  {
    key: 'roles',
    header: 'Roles',
    render: (user) => (
      <div className="sectioned-table-list__role-badges">
        {user.roles.map((role) => (
          <span key={`${user.persona_id}-${role}`} className="sectioned-table-list__badge">
            {formatRoleLabel(role)}
          </span>
        ))}
      </div>
    ),
  },
]

export default function ListadoUsuarios({ users, emptyMessage, canManageUsers }) {
  const sections = [
    {
      key: 'empleados',
      title: 'Empleados',
      emptyMessage: 'No hay empleados para mostrar.',
      items: users.filter((user) => user.roles.includes('empleado')),
    },
    {
      key: 'socios',
      title: 'Socios',
      emptyMessage: 'No hay socios para mostrar.',
      items: users.filter((user) => user.roles.includes('socio')),
    },
  ]

  return (
    <SectionedTableList
      sections={sections}
      columns={USER_COLUMNS}
      getRowKey={(user, sectionKey) => `${sectionKey}-${user.persona_id}`}
      emptyMessage={emptyMessage}
      renderActions={
        canManageUsers
          ? (user) => (
              <div className="sectioned-table-list__actions">
                <Link
                  className="secondary-action"
                  to={`/usuarios/${user.persona_id}/modificar?returnTo=/usuarios`}
                >
                  Modificar
                </Link>
              </div>
            )
          : undefined
      }
    />
  )
}

function formatRoleLabel(role) {
  if (role === 'empleado') {
    return 'Empleado'
  }

  if (role === 'socio') {
    return 'Socio'
  }

  return role
}
