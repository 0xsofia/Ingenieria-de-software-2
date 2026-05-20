import { useEffect, useState } from 'react'

import { obtenerPagos } from '../api/pagos'
import './MisPagosPage.css'

function MisPagosPage() {
  const [payments, setPayments] = useState([])
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchPayments()
  }, [])

  async function fetchPayments(params = {}) {
    setIsLoading(true)
    setError(null)

    try {
      const data = await obtenerPagos(params)
      setPayments(data.payments || [])
    } catch (err) {
      setError(err.data?.message || 'No fue posible cargar los pagos. Intentalo nuevamente.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setFilters((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    const today = new Date()
    const startDate = filters.start_date ? new Date(filters.start_date) : null
    const endDate = filters.end_date ? new Date(filters.end_date) : null

    if ((startDate && startDate > today) || (endDate && endDate > today)) {
      setError('Las fechas no pueden ser mayores a hoy.')
      return
    }

    await fetchPayments(filters)
  }

  const formattedAmount = (value) => {
    if (!value) {
      return '-'
    }

    return Number(value).toLocaleString('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 2,
    })
  }

  return (
    <main className="dashboard-shell payments-shell">
      <section className="dashboard-frame payments-frame">
        <header className="dashboard-header payments-header">
          <h1>Mis pagos</h1>
        </header>

        <section className="payments-filter-card">
          <h2>Filtrar por fecha</h2>
          <form className="payments-filter-form" onSubmit={handleSubmit}>
            <div className="payments-filter-field">
              <label htmlFor="start_date">Desde</label>
              <input
                id="start_date"
                name="start_date"
                type="date"
                max={new Date().toISOString().split('T')[0]}
                value={filters.start_date}
                onChange={handleChange}
              />
            </div>

            <div className="payments-filter-field">
              <label htmlFor="end_date">Hasta</label>
              <input
                id="end_date"
                name="end_date"
                type="date"
                max={new Date().toISOString().split('T')[0]}
                value={filters.end_date}
                onChange={handleChange}
              />
            </div>

            <div className="payments-filter-actions">
              <button type="submit" className="primary-action">
                Filtrar
              </button>
            </div>
          </form>
        </section>

        <section className="payments-list-card">
          <h2>Listado de pagos</h2>

          {error ? <p className="payments-error">{error}</p> : null}

          {isLoading ? (
            <p className="dashboard-copy">Cargando pagos...</p>
          ) : payments.length === 0 ? (
            <p className="dashboard-copy">
              {filters.start_date || filters.end_date
                ? 'No hay pagos en el rango de fechas seleccionado.'
                : 'Aún no tienes pagos registrados.'}
            </p>
          ) : (
            <div className="payments-table-wrapper">
              <table className="payments-table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Monto bruto</th>
                    <th>Descuento</th>
                    <th>Monto pagado</th>
                    <th>Estado</th>
                    <th>Proveedor</th>
                    <th>Ref.</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.map((payment) => (
                    <tr key={payment.pago_id}>
                      <td>
                        {payment.fecha_pago
                          ? new Date(payment.fecha_pago).toLocaleDateString('es-AR', {
                              day: '2-digit',
                              month: '2-digit',
                              year: 'numeric',
                            })
                          : 'Pendiente'}
                      </td>
                      <td>{formattedAmount(payment.monto_bruto)}</td>
                      <td>{payment.descuento_pct}%</td>
                      <td>{payment.monto_pagado ? formattedAmount(payment.monto_pagado) : '-'}</td>
                      <td>{payment.estado}</td>
                      <td>{payment.proveedor}</td>
                      <td>{payment.external_ref || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </section>
    </main>
  )
}

export default MisPagosPage
