import { useState, useEffect } from 'react'
import './MisPagosPage.css'
import pagosData from '../data/pagos.json'

function PagosClientesPage() {
  const [pagos, setPagos] = useState([])
  const [filteredPagos, setFilteredPagos] = useState([])
  const [dni, setDni] = useState('')
  const [email, setEmail] = useState('')
  const [nombre, setNombre] = useState('')
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

    const hasDateRange = dateFrom && dateTo
    if (hasDateRange) {
      const from = new Date(dateFrom)
      const to = new Date(dateTo)

      if (from > to) {
        setError('La fecha desde no puede ser mayor a la fecha hasta')
        setFilteredPagos([])
        return
      }
    }

    const filtered = pagos.filter((pago) => {
      const matchesDni = dni
        ? pago.cliente_dni.toLowerCase().includes(dni.trim().toLowerCase())
        : true
      const matchesEmail = email
        ? pago.cliente_email.toLowerCase().includes(email.trim().toLowerCase())
        : true
      const matchesNombre = nombre
        ? pago.cliente_nombre.toLowerCase().includes(nombre.trim().toLowerCase())
        : true

      const matchesFecha = hasDateRange
        ? (() => {
            const from = new Date(dateFrom)
            const to = new Date(dateTo)
            const pagoDate = new Date(pago.fecha)
            return pagoDate >= from && pagoDate <= to
          })()
        : true

      return matchesDni && matchesEmail && matchesNombre && matchesFecha
    })

    setFilteredPagos(filtered)
  }

  function handleReset() {
    setDni('')
    setEmail('')
    setNombre('')
    setDateFrom('')
    setDateTo('')
    setError('')
    setHasFiltered(false)
    setFilteredPagos(pagos)
  }

  function formatDate(dateString) {
    const date = new Date(dateString)
    return date.toLocaleDateString('es-AR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
    }).format(amount)
  }

  return (
    <main className="dashboard-shell pagos-shell">
      <section className="dashboard-frame pagos-frame">
        <header className="dashboard-header pagos-header">
          <h1>Pagos de clientes</h1>
        </header>

        <section className="pagos-filter-card">
          <div className="section-heading">
            <h2>Filtrar pagos</h2>
          </div>

          <form className="pagos-filter-form" onSubmit={handleFilter}>
            <div className="filter-fields">
              <label className="field">
                <span>DNI</span>
                <input
                  type="text"
                  value={dni}
                  onChange={(e) => setDni(e.target.value)}
                  placeholder="DNI"
                />
              </label>

              <label className="field">
                <span>Mail</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="unCorreo@gmail.com"
                />
              </label>

              <label className="field">
                <span>Nombre</span>
                <input
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Nombre"
                />
              </label>

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
          

          {filteredPagos.length > 0 ? (
            <div className="pagos-table">
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Cliente</th>
                    <th>DNI</th>
                    <th>Mail</th>
                    <th>Descripción</th>
                    <th>Monto</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPagos.map((pago) => (
                    <tr key={pago.id}>
                      <td>{formatDate(pago.fecha)}</td>
                      <td>{pago.cliente_nombre}</td>
                      <td>{pago.cliente_dni}</td>
                      <td>{pago.cliente_email}</td>
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
              <p>No hay pagos para mostrar</p>
            </div>
          )}
        </section>
      </section>
    </main>
  )
}

export default PagosClientesPage
