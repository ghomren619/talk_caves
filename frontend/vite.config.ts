import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      '/socket.io': {
        target: process.env.VITE_API_BASE || 'http://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})


