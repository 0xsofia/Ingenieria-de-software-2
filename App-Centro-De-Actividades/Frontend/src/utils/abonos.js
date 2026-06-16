const DESCUENTO_ABONO_PCT = 20

export function calcularPrecioAbonoConDescuento(precioTotal, session, fechaClase, currentDate = new Date()) {
  const total = Number(precioTotal || 0)
  const aplicaDescuento = usuarioCalificaParaDescuentoAbono(session, fechaClase, currentDate)
  const precioConDescuento = aplicaDescuento
    ? roundCurrency(total * (1 - DESCUENTO_ABONO_PCT / 100))
    : total

  return {
    aplicaDescuento,
    descuentoPct: aplicaDescuento ? DESCUENTO_ABONO_PCT : 0,
    precioOriginal: roundCurrency(total),
    precioFinal: precioConDescuento,
  }
}

export function usuarioCalificaParaDescuentoAbono(session, fechaClase, currentDate = new Date()) {
  if (session?.role !== 'socio') {
    return false
  }

  const fechaLimite = getDiscountDeadline(fechaClase)
  if (!fechaLimite || formatDateKey(currentDate) > fechaLimite) {
    return false
  }

  const bloqueadoHasta = session?.descuento_bloqueado_hasta
  if (!bloqueadoHasta) {
    return true
  }

  return bloqueadoHasta < formatDateKey(currentDate)
}

function roundCurrency(value) {
  return Math.round(Number(value || 0) * 100) / 100
}

function formatDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getDiscountDeadline(fechaClase) {
  const [year, month] = String(fechaClase || '').split('-')
  if (!year || !month) {
    return null
  }

  return `${year}-${month}-10`
}
