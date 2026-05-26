import axios from 'axios'

const baseURL = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  ''
).replace(/\/$/, '')

const timeoutMs = Number(
  import.meta.env.VITE_HTTP_TIMEOUT_MS ||
    import.meta.env.VITE_API_TIMEOUT_MS ||
    30000,
)

export const http = axios.create({
  baseURL,
  timeout: Number.isFinite(timeoutMs) && timeoutMs > 0 ? timeoutMs : 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': '1',
  },
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    error.data = error.response?.data
    return Promise.reject(error)
  },
)
