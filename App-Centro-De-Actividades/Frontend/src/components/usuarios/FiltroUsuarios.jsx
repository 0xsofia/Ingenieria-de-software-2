import FilterForm from '../listing/FilterForm'

const USER_FILTER_FIELDS = [
  {
    name: 'dni',
    label: 'DNI',
    type: 'text',
    inputMode: 'numeric',
    placeholder: '44000000',
  },
  {
    name: 'email',
    label: 'Email',
    type: 'email',
    autoComplete: 'email',
    placeholder: 'usuario@dominio.com',
  },
  {
    name: 'nombre',
    label: 'Nombre',
    type: 'text',
    placeholder: 'Nombre o apellido',
  },
]

export default function FiltroUsuarios({ initialValues, onSubmit, isSubmitting }) {
  return (
    <FilterForm
      title="Filtrar usuarios"
      description=""
      fields={USER_FILTER_FIELDS}
      initialValues={initialValues}
      onSubmit={onSubmit}
      submitLabel="Filtrar usuarios"
      isSubmitting={isSubmitting}
    />
  )
}
