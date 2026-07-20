import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'https://localhost',
        changeOrigin: true,
        secure: false,
        configure: (proxy) => {
          // Ensure long-lived connections (SSE) are not buffered/closed by proxy
          proxy.on('proxyReq', (proxyReq) => {
            proxyReq.setHeader('Connection', 'keep-alive');
            proxyReq.setHeader('X-Accel-Buffering', 'no');
          });
        }
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
});
