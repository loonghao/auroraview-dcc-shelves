import React, { Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './style.css'

// Initialize i18n before rendering
import './i18n'

// Debug: Log startup info
console.log('[DCC-Shelves] Starting application...')
console.log('[DCC-Shelves] Location:', window.location.href)
console.log('[DCC-Shelves] AuroraView available:', !!window.auroraview)

const rootElement = document.getElementById('root')
if (!rootElement) {
  console.error('[DCC-Shelves] Could not find root element!')
  throw new Error('Could not find root element to mount to')
}

console.log('[DCC-Shelves] Root element found, mounting React...')

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-screen bg-[#0d0d0d] text-white/50">
    <span className="text-sm">Loading...</span>
  </div>
)

try {
  const root = ReactDOM.createRoot(rootElement)
  root.render(
    <React.StrictMode>
      <Suspense fallback={<LoadingFallback />}>
        <App />
      </Suspense>
    </React.StrictMode>
  )
  console.log('[DCC-Shelves] React mounted successfully!')
} catch (error) {
  console.error('[DCC-Shelves] Failed to mount React:', error)
}

