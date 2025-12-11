import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  // Use auroraview:// protocol for AuroraView WebView compatibility
  // This avoids CORS issues with file:// protocol
  base: 'https://auroraview.localhost/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src/frontend'),
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'esbuild',
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
        settings: path.resolve(__dirname, 'settings.html'),
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    host: 'localhost',
  },
})

