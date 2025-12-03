import { defineConfig, Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

/**
 * Vite plugin to fix HTML files for file:// protocol loading in DCC mode.
 *
 * Problem: All HTML files are loaded via Qt's load_file() in DCC mode,
 * but their asset URLs use auroraview.localhost protocol which requires
 * special handling. Using relative paths is more reliable and universal.
 *
 * Solution: Replace absolute protocol URLs with relative paths in all HTML files.
 */
function relativePathPlugin(): Plugin {
  return {
    name: 'relative-path-fix',
    enforce: 'post',
    generateBundle(_, bundle) {
      for (const fileName of Object.keys(bundle)) {
        // Process all HTML files
        if (fileName.endsWith('.html')) {
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
    relativePathPlugin(),
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

