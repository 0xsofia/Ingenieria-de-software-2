import { useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'

import { renovarAbonoMensual } from '../api/reservas'
import { useAuth } from '../hooks/useAuth'
import { calcularPrecioAbonoConDescuento } from '../utils/abonos'
import './ActividadPage.css'
import './ActividadesPage.css'

const currencyFormatter = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
  minimumFractionDigits: 2,
})

export default function RealizarRenovacionAbonoPage() {
  const { session } = useAuth()
  const { actividadName } = useParams()
  const location = useLocation()
  
  const abono = location.state?.abono
  const abonoId = abono ? Number(abono.abono_mensual_id) : null
  const actividadTitle = formatActividadTitle(actividadName || abono?.actividad)
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [requestError, setRequestError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  // 🛠️ SOLUCIÓN AL "A CONFIRMAR": 
  // Evaluamos todas las formas posibles en que el backend expone el precio en las listas de abonos.
  // Agregamos fallbacks matemáticos basados en el precio base si el backend devuelve el precio unitario.
  // 🛠️ Buscamos el precio real de la clase o calculamos el pack mensual en base a tus valores ($4000 por clase)
const precioClaseConfigurada = abono?.clase_base?.precio ?? 
                abono?.clase?.precio ?? 
                abono?.horario?.precio ?? 
                abono?.actividad_info?.precio ??
                abono?.precio_clase ?? 
                abono?.precio; // Si viene directo como propiedad

// Si encontramos el precio unitario de la clase configurada, lo multiplicamos por 4 clases del mes.
// Si el backend ya mandó el total calculado del abono, usamos ese directamente.
const precioTotal = abono?.precio_total || abono?.monto || abono?.precio_abono 
? Number(abono.precio_total || abono.monto || abono.precio_abono)
: precioClaseConfigurada 
? Number(precioClaseConfigurada) * 4 
: null; // Volvemos a null si realmente no hay rastro de configuración

const tienePrecioValido = precioTotal !== null && !isNaN(precioTotal) && precioTotal > 0;
  // Fecha límite de renovación como pivote
  const fechaReferenciaDescuento = abono?.fecha_limite_renovacion || new Date().toISOString().split('T')[0];

  async function handleRenovacionAbono() {
    if (!Number.isFinite(abonoId)) {
      setRequestError('Necesitás seleccionar un abono mensual válido para renovar.')
      return
    }

    setIsSubmitting(true)
    setRequestError('')
    setSuccessMessage('')

    try {
      const result = await renovarAbonoMensual({ abono_mensual_id: abonoId })

      if (result.status === 'payment_required' && result.payment_url) {
        window.location.assign(result.payment_url)
        return
      }
      
      if (result.init_point) {
        window.location.assign(result.init_point)
        return
      }

      if (result.status === 'reserved' || result.status === 'ok') {
        setSuccessMessage(result.message || 'Abono mensual renovado con éxito.')
        return
      }

      setSuccessMessage(result.message || 'Renovación procesada con éxito.')
    } catch (error) {
      const apiMessage = error?.response?.data?.message || error?.data?.message
      setRequestError(apiMessage || 'No se pudo realizar la renovación mensual por un error de pago.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="dashboard-shell">
      <section className="dashboard-frame actividad-placeholder-page">
        <div className="actividad-placeholder-page__top-link">
          <Link className="secondary-action" to="/mis-clases">
            Volver a mis clases
          </Link>
        </div>

        <header className="dashboard-header actividad-placeholder-page__header">
          <p className="auth-subtitle">Renovación de abono</p>
          <h1>{actividadTitle}</h1>
          <p className="dashboard-copy">
            Confirmá la renovación de tu abono mensual para el próximo mes.
          </p>
        </header>

        <div className="actividad-placeholder-page__card">
          <h2>Detalles del abono a renovar</h2>
          {abono ? (
            <dl className="actividad-placeholder-page__details">
              <div>
                <dt>Actividad</dt>
                <dd>{abono.actividad || '-'}</dd>
              </div>
              <div>
                <dt>Día de la semana</dt>
                <dd>{abono.dia_semana ? `Los ${abono.dia_semana}s` : '-'}</dd>
              </div>
              <div>
                <dt>Horario fijo</dt>
                <dd>{abono.hora_inicio || '--:--'} hs</dd>
              </div>
              <div>
                <dt>Fecha Límite Renovación</dt>
                <dd style={{ color: 'var(--primary-color, #e63946)', fontWeight: 'bold' }}>
                  {abono.fecha_limite_renovacion ? abono.fecha_limite_renovacion.split('-').reverse().join('/') : '-'}
                </dd>
              </div>
            <div>
                <dt>Total a pagar</dt>
                <dd>
                    {tienePrecioValido ? (
                    <PrecioAbono
                        precioTotal={precioTotal}
                        fechaClase={fechaReferenciaDescuento}
                        session={session}
                    />
                    ) : (
                    'A confirmar'
                    )}
                </dd>
            </div>
            </dl>
          ) : (
            <p className="dashboard-copy">No se ha seleccionado ningún abono para renovar.</p>
          )}

          {requestError ? (
            <div className="banner banner--error" role="alert">
              {requestError}
            <button type="button" className="banner__close" onClick={(e) => e.target.closest('.banner').style.display = 'none'}>×</button></div>
          ) : null}

          {successMessage ? (
            <p className="dashboard-copy" role="status">
              {successMessage}
            </p>
          ) : null}

          <div className="actividad-placeholder-page__actions">
            <button
              type="button"
              className="primary-action"
              onClick={handleRenovacionAbono}
              disabled={isSubmitting || !abono}
            >
              {isSubmitting ? 'Redirigiendo a Mercado Pago...' : 'Renovar abono mensual'}
            </button>
          </div>
        </div>
      </section>
    </section>
  )
}

function PrecioAbono({ precioTotal, fechaClase, session }) {
  // Manejo defensivo dentro de la ejecución para evitar que rompa el árbol de renderizado
  const precio = calcularPrecioAbonoConDescuento(precioTotal, session, fechaClase) || {
    aplicaDescuento: false,
    precioOriginal: precioTotal,
    precioFinal: precioTotal
  };

  if (!precio.aplicaDescuento) {
    return currencyFormatter.format(precio.precioOriginal)
  }

  return (
    <div className="abono-price">
      <span className="abono-price__original">
        {currencyFormatter.format(precio.precioOriginal)}
      </span>
      <span className="abono-price__discounted">
        {currencyFormatter.format(precio.precioFinal)}
      </span>
      <span className="abono-price__tag">20% de descuento por renovación</span>
    </div>
  )
}

function formatActividadTitle(slug) {
  return String(slug || 'actividad')
    .replace(/-/g, ' ')
    .split(' ')
    .filter(Boolean)
    .map((word) => word[0]?.toUpperCase() + word.slice(1))
    .join(' ')
}