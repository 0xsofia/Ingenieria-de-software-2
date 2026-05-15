export const PHONE_INVALID_CHARS_MESSAGE =
  'Ingrese un telefono valido sin caracteres especiales, letras o espacios. Ejemplo 2214446633'

export const PHONE_AREA_CODE_MESSAGE =
  'Debe ingresar un código de área válido en territorio argentino. Ejemplo: 221'

export const PHONE_TOTAL_DIGITS_MESSAGE =
  'El "Teléfono" debe alcanzar los 10 dígitos totales incluyendo el código de área. Ejemplo: 2214446633'

export function getPhoneValidationMessage(value) {
  if (!/^\d+$/.test(value)) {
    return PHONE_INVALID_CHARS_MESSAGE
  }

  if (value.length !== 10) {
    return PHONE_TOTAL_DIGITS_MESSAGE
  }

  if (!hasValidAreaCode(value)) {
    return PHONE_AREA_CODE_MESSAGE
  }

  return ''
}

function hasValidAreaCode(value) {
  if (value.startsWith('0')) {
    return false
  }

  if (value.startsWith('1') && !value.startsWith('11')) {
    return false
  }

  return [2, 3, 4].some((areaLength) => {
    const subscriberLength = value.length - areaLength
    return subscriberLength >= 6 && subscriberLength <= 8
  })
}
