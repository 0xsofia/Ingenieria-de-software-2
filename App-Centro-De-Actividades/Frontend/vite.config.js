import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const proxyTarget =
    env.VITE_PROXY_TARGET || env.VITE_API_URL || 'http://localhost:5000'

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      allowedHosts: ['inge2-front2.ngrok.app', 'localhost', '127.0.0.1'],
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})
