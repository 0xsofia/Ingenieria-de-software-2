import SectionedTableList from '../listing/SectionedTableList'

const PAYMENT_COLUMNS = [
  { key: 'pago_id', header: 'Número de Pago' },
  {
    key: 'nombre_completo',
    header: 'Socio',
    render: (p) => (
      <div className="sectioned-table-list__primary-cell">
        <strong>{p.nombre_completo}</strong>
      </div>
    ),
  },
  {
    key: 'monto_pagado',
    header: 'Monto',
    render: (p) => <strong>{p.monto_pagado || p.monto_bruto}</strong>,
  },
  { key: 'estado', header: 'Estado' },
  {
    key: 'fecha_pago',
    header: 'Fecha',
    render: (p) =>
      p.fecha_pago ? new Date(p.fecha_pago).toLocaleDateString() : '-',
  },
  { key: 'proveedor', header: 'Proveedor' },
]

export default function ListadoPagos({ pagos, emptyMessage }) {
  const sections = [
    { key: 'pagos', title: 'Pagos registrados', emptyMessage, items: pagos },
  ]

  return (
    <SectionedTableList
      sections={sections}
      columns={PAYMENT_COLUMNS}
      getRowKey={(p) => p.pago_id}
      emptyMessage={emptyMessage}
    />
  )
}
