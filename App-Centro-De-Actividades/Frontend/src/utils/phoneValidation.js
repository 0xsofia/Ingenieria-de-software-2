export const PHONE_INVALID_CHARS_MESSAGE =
  'Ingrese un telefono valido sin caracteres especiales, letras o espacios. Ejemplo 2214446633'

export const PHONE_START_DIGIT_MESSAGE =
  'Debe ingresar un telefono que comience con 1, 2 ó 3. Ejemplo: 2214446633'

export const PHONE_TOTAL_DIGITS_MESSAGE =
  'El teléfono debe alcanzar los 10 dígitos totales. Ejemplo: 2214446633'

export const PHONE_HINT =
  'Ingresá solo números en un teléfono de 10 dígitos que comience con 1, 2 o 3. Ejemplo: 2214446633.'

export function getPhoneValidationMessage(value) {
  if (!/^\d+$/.test(value)) {
    return PHONE_INVALID_CHARS_MESSAGE
  }

  if (value.length !== 10) {
    return PHONE_TOTAL_DIGITS_MESSAGE
  }

  if (!value.startsWith('1') && !value.startsWith('2') && !value.startsWith('3')) {
    return PHONE_START_DIGIT_MESSAGE
  }

  return ''
}
