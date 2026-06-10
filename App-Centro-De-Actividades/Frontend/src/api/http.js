import axios from 'axios'

const envURL = import.meta.env.VITE_API_URL;
const fallbackURL = import.meta.env.DEV ? 'http://localhost:5000' : 'https://ingenieria-de-software-2.onrender.com'
const baseURL = (envURL && envURL.trim() !== '' ? envURL : fallbackURL).replace(/\/$/, '')

console.log('📡 [AXIOS] Conectando a la API en URL:', baseURL);

export const http = axios.create({
  baseURL,
  timeout: 20000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    // 'ngrok-skip-browser-warning': '1',
  },
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    error.data = error.response?.data
    return Promise.reject(error)
  },
)
