import { defineConfig,loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:5000'

const getHostname = (value) => {
  if (!value) return null

  try {
    return new URL(value).hostname
  } catch {
    return value
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const frontendHost = getHostname(env.VITE_FRONTEND_HOST)
  
  return {
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: [
      frontendHost,
      'inge2-front2.ngrok.app',
      'localhost',
      '127.0.0.1',
    ],
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
}
}
);




/*import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

const getHostname = (value) => {
  if (!value) return null

  try {
    return new URL(value).hostname
  } catch {
    return value
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://localhost:5000'
  const frontendHost = getHostname(env.VITE_FRONTEND_HOST)

  console.log(`Frontend host: ${frontendHost || 'no configurado'}`)

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      allowedHosts: [
        frontendHost,
        'inge2-front2.ngrok.app',
        'localhost',
        '127.0.0.1',
      ].filter(Boolean),
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
 */