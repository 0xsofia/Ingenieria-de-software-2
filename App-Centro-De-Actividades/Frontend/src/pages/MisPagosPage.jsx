import { useState, useEffect } from 'react'
import '../App.css'
import './MisPagosPage.css'
import pagosData from '../data/pagos.json'

function MisPagosPage() {
  const [pagos, setPagos] = useState([])
  const [filteredPagos, setFilteredPagos] = useState([])
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [error, setError] = useState('')
  const [hasFiltered, setHasFiltered] = useState(false)

  useEffect(() => {
    setPagos(pagosData.pagos)
    setFilteredPagos(pagosData.pagos)
  }, [])

  function handleFilter(e) {
    e.preventDefault()
    setError('')
    setHasFiltered(true)

    if (!dateFrom || !dateTo) {
      //setError('Debe ingresar ambas fechas.')
      return
    }

    const from = new Date(dateFrom)
    const to = new Date(dateTo)

    if (from > to) {
      setError('La fecha desde no puede ser mayor a la hasta')
      setFilteredPagos([])
      return
    }

    const filtered = pagos.filter((pago) => {
      const pagoDate = new Date(pago.fecha)
      return pagoDate >= from && pagoDate <= to
    })

    setFilteredPagos(filtered)
  }

  function handleReset() {
    setDateFrom('')
    setDateTo('')
    setError('')
    setHasFiltered(false)
    setFilteredPagos(pagos)
  }

  function formatDate(dateString) {
    const date = new Date(dateString)
    return date.toLocaleDateString('es-AR', { year: 'numeric', month: '2-digit', day: '2-digit' })
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(amount)
  }

  return (
    <main className="dashboard-shell pagos-shell">
      <section className="dashboard-frame pagos-frame">
        <header className="dashboard-header pagos-header">
          <h1>Mis pagos</h1>
        </header>

        <section className="pagos-filter-card">
          <div className="section-heading">
            <h2>Filtrar pagos</h2>
          </div>

          <form className="pagos-filter-form" onSubmit={handleFilter}>
            <div className="filter-fields">
              <label className="field">
                <span>Desde</span>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  max={new Date().toISOString().split('T')[0]}
                />
              </label>

              <label className="field">
                <span>Hasta</span>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  max={new Date().toISOString().split('T')[0]}
                />
              </label>
            </div>

            {error && (
              <p className="banner banner--error" role="alert">
                {error}
              </p>
            )}

            <div className="filter-actions">
              <button type="submit" className="primary-action filter-button">
                Filtrar
              </button>
              <button type="button" className="secondary-action filter-reset" onClick={handleReset}>
                Limpiar
              </button>
            </div>
          </form>
        </section>

        <section className="pagos-list-card">
          <div className="section-heading">
            <h2>Resultados</h2>
            <p>
              {hasFiltered
                ? filteredPagos.length === 0
                  ? 'No hay pagos en el rango de fechas seleccionado.'
                  : ``
                : ``}
            </p>
          </div>

          {filteredPagos.length > 0 ? (
            <div className="pagos-table">
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Descripción</th>
                    <th>Monto</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPagos.map((pago) => (
                    <tr key={pago.id}>
                      <td>{formatDate(pago.fecha)}</td>
                      <td>{pago.descripcion}</td>
                      <td className="amount">{formatCurrency(pago.monto)}</td>
                      <td>
                        <span className={`status status--${pago.estado}`}>
                          {pago.estado === 'completado' ? 'Completado' : 'Pendiente'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <p>No hay pagos para mostrar.</p>
            </div>
          )}
        </section>
      </section>
    </main>
  )
}

export default MisPagosPage
