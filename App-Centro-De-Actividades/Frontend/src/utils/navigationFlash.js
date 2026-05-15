const FLASH_MESSAGE_STORAGE_KEY = 'cad.navigation.flash'

export function storeFlashMessage(message) {
  if (!message) {
    return
  }

  window.sessionStorage.setItem(FLASH_MESSAGE_STORAGE_KEY, message)
}

export function consumeFlashMessage() {
  const message = window.sessionStorage.getItem(FLASH_MESSAGE_STORAGE_KEY) || ''

  if (message) {
    window.sessionStorage.removeItem(FLASH_MESSAGE_STORAGE_KEY)
  }

  return message
}
