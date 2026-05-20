import FilterForm from '../listing/FilterForm'

const PAYMENT_FILTER_FIELDS = [
  { name: 'dni', label: 'DNI', type: 'text', inputMode: 'numeric', placeholder: '44111111' },
  { name: 'email', label: 'Email', type: 'email', autoComplete: 'email', placeholder: 'cliente@dominio.com' },
  { name: 'nombre', label: 'Nombre', type: 'text', placeholder: 'Nombre o apellido' },
  { name: 'fecha_desde', label: 'Fecha desde', type: 'date' },
  { name: 'fecha_hasta', label: 'Fecha hasta', type: 'date' },
]

export default function FiltroPagos({ initialValues, onSubmit, isSubmitting }) {
  return (
    <FilterForm
      title="Filtrar pagos"
      description="Buscá por DNI, email, nombre o rango de fechas para encontrar pagos específicos."
      fields={PAYMENT_FILTER_FIELDS}
      initialValues={initialValues}
      onSubmit={onSubmit}
      submitLabel="Filtrar pagos"
      resetLabel="Limpiar filtros"
      isSubmitting={isSubmitting}
    />
  )
}
