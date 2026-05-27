import axios from 'axios'

const envURL = import.meta.env.VITE_API_URL;
const baseURL = (envURL && envURL.trim() !== '' ? envURL : 'https://inge2-back2.ngrok.app').replace(/\/$/, '')

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