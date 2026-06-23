import { startTransition, useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { confirmarPagoRetorno } from '../api/reservas'

function PagoRetornoPage() {
  const location = useLocation()
  const navigate = useNavigate()

  const params = useMemo(() => new URLSearchParams(location.search), [location.search])
  const reservaIdParam = params.get('reserva_id')
  const statusParam =
    params.get('collection_status') ||
    params.get('payment_status') ||
    params.get('status_detail') ||
    params.get('status')
  const paymentIdParam = params.get('payment_id') || params.get('collection_id')
  const externalReferenceParam = params.get('external_reference')

  const [isSubmitting, setIsSubmitting] = useState(true)
  const [result, setResult] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    let cancelled = false

    async function run() {
      setIsSubmitting(true)
      setErrorMessage('')
      setResult(null)

      const reserva_id = Number(reservaIdParam)

      if (!reservaIdParam || Number.isNaN(reserva_id)) {
        setErrorMessage('No pudimos identificar la reserva asociada al pago.')
        setIsSubmitting(false)
        return
      }

      try {
        const response = await confirmarPagoRetorno({
          reserva_id,
          status: statusParam,
          payment_id: paymentIdParam,
          external_reference: externalReferenceParam,
        })

        if (cancelled) return

        setResult(response)
      } catch (error) {
        if (cancelled) return

        setErrorMessage(
          error?.data?.message ||
            'No pudimos confirmar el pago. Intentá nuevamente desde la reserva.',
        )
      } finally {
        if (!cancelled) {
          setIsSubmitting(false)
        }
      }
    }

    run()

    return () => {
      cancelled = true
    }
  }, [reservaIdParam, statusParam, paymentIdParam, externalReferenceParam])

  function handleBackHome() {
    startTransition(() => {
      navigate('/inicio', { replace: true })
    })
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame dashboard-frame--compact">
        <header className="dashboard-header">
          <p className="auth-subtitle">Pago</p>
          
        </header>

        {errorMessage ? (
          <p className="banner banner--error" role="alert">
            {errorMessage}
          </p>
        ) : null}

        {result ? (
          <section className="dashboard-section">
            <div className="section-heading">
              <h2>{result.message}</h2>
            </div>
          </section>
        ) : null}

        <button className="primary-action" type="button" onClick={handleBackHome} disabled={isSubmitting}>
          {isSubmitting ? 'Procesando...' : 'Volver al inicio'}
        </button>
      </section>
    </section>
  )
}

export default PagoRetornoPage
