import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,            // listen on 0.0.0.0 so tunnels can reach it
    allowedHosts: true,    // accept any Host header (ngrok/cloudflare/localtunnel)
    proxy: {
      // Same-origin API: browser calls /api/*, Vite forwards to the backend.
      // This means only ONE port needs to be tunneled and there are no CORS issues.
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
