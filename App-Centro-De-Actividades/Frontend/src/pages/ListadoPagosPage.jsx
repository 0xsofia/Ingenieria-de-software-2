import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'

import { listarPagos } from '../api/pagos'
import FiltroPagos from '../components/pagos/FiltroPagos'
import ListadoPagos from '../components/pagos/ListadoPagos'
import { useAuth } from '../hooks/useAuth'
import './ListadoPagosPage.css'

const INITIAL_PAYMENT_FILTERS = Object.freeze({
  dni: '',
  email: '',
  nombre: '',
  fecha_desde: '',
  fecha_hasta: '',
})

export default function ListadoPagosPage() {
  const { session } = useAuth()
  const [payments, setPayments] = useState([])
  const [submittedFilters, setSubmittedFilters] = useState(INITIAL_PAYMENT_FILTERS)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const canViewPayments = session?.role === 'administrador'

  useEffect(() => {
    if (!canViewPayments) return

    let cancelled = false

    async function loadInitialPayments() {
      setIsLoading(true)
      setError('')

      try {
        const result = await listarPagos(INITIAL_PAYMENT_FILTERS)
        if (!cancelled) {
          setPayments(result.pagos || [])
          setSubmittedFilters(INITIAL_PAYMENT_FILTERS)
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError?.response?.data?.message || 'No se encontraron pagos registrados.')
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadInitialPayments()
    return () => { cancelled = true }
  }, [canViewPayments])

  if (!canViewPayments) {
    return <Navigate to="/inicio" replace />
  }

  async function handleFilterSubmit(nextFilters) {
    if (nextFilters.fecha_desde && nextFilters.fecha_hasta) {
      if (nextFilters.fecha_desde > nextFilters.fecha_hasta) {
        setError('La fecha desde no puede ser mayor a la fecha hasta')
        return
      }
    }

    setIsLoading(true)
    setError('')

    try {
      const result = await listarPagos(nextFilters)
      setPayments(result.pagos || [])
      setSubmittedFilters(nextFilters)
    } catch (requestError) {
      setError(requestError?.response?.data?.message || 'No se pudo filtrar el listado de pagos.')
    } finally {
      setIsLoading(false)
    }
  }

  const emptyMessage = 'No hay pagos para mostrar.'

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame listado-pagos-page">
        <div className="listado-pagos-page__header-row">
          <div>
            <p className="auth-subtitle">Administración</p>
            <h1>Pagos de Clientes</h1>
          </div>

          <div className="listado-pagos-page__header-actions">
            <Link className="secondary-action" to="/inicio">
              Volver al inicio
            </Link>
          </div>
        </div>

        <div className="listado-pagos-page__content">
          <FiltroPagos
            initialValues={submittedFilters}
            onSubmit={handleFilterSubmit}
            isSubmitting={isLoading}
          />

          {error && (
            <div className="banner banner--error" role="alert">
              {error}
            <button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>
          )}

          {isLoading ? (
            <p className="dashboard-copy">Cargando pagos...</p>
          ) : (
            <>
              <div className="listado-pagos-page__status-row">
                <p className="dashboard-copy">{payments.length} pago(s) encontrados</p>
              </div>

              <ListadoPagos
                pagos={payments}
                emptyMessage={emptyMessage}
              />
            </>
          )}
        </div>
      </section>
    </section>
  )
}
