import SectionedTableList from '../listing/SectionedTableList'

const PAYMENT_COLUMNS = [
  {
    key: 'pago_id',
    header: 'ID Pago',
  },
  {
    key: 'socio_id',
    header: 'Socio',
  },
  {
    key: 'monto_pagado',
    header: 'Monto Pagado',
    render: (pago) => (
      <div className="sectioned-table-list__primary-cell">
        <strong>{pago.monto_pagado || pago.monto_bruto}</strong>
      </div>
    ),
  },
  {
    key: 'estado',
    header: 'Estado',
  },
  {
    key: 'fecha_pago',
    header: 'Fecha',
    render: (pago) =>
      pago.fecha_pago
        ? new Date(pago.fecha_pago).toLocaleDateString()
        : '-',
  },
  {
    key: 'proveedor',
    header: 'Proveedor',
  },
]

export default function ListadoPagos({ pagos, emptyMessage }) {
  const sections = [
    {
      key: 'pagos',
      title: 'Pagos registrados',
      emptyMessage,
      items: pagos,
    },
  ]

  return (
    <SectionedTableList
      sections={sections}
      columns={PAYMENT_COLUMNS}
      getRowKey={(pago) => pago.pago_id}
      emptyMessage={emptyMessage}
    />
  )
}
