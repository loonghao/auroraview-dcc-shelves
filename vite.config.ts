import { defineConfig, Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

/**
 * Vite plugin to fix child window HTML files for file:// protocol loading.
 *
 * Problem: Child windows (like settings) are loaded via Qt's load_file(),
 * but their asset URLs use auroraview.localhost protocol which won't work.
 *
 * Solution: Replace absolute protocol URLs with relative paths in child HTML files.
 */
function childWindowPlugin(): Plugin {
  // List of HTML files that are opened as child windows
  const childWindows = ['settings.html']

  return {
    name: 'child-window-fix',
    enforce: 'post',
    generateBundle(_, bundle) {
      for (const fileName of Object.keys(bundle)) {
        if (childWindows.includes(fileName)) {
          const chunk = bundle[fileName]
          if (chunk.type === 'asset' && typeof chunk.source === 'string') {
            // Replace auroraview protocol URLs with relative paths
            chunk.source = chunk.source
              .replace(/https:\/\/auroraview\.localhost\//g, './')
              .replace(/auroraview:\/\//g, './')
          }
        }
      }
    },
  }
}

export default defineConfig({
  plugins: [
    react(),
    childWindowPlugin(),
  ],
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

