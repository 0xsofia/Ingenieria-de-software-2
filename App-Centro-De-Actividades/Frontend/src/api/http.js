import axios from 'axios'

const baseURL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export const http = axios.create({
  baseURL,
  timeout: 20000,
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
