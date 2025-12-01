import React, { Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './style.css'

// Initialize i18n before rendering
import './i18n'

const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Could not find root element to mount to')
}

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-screen bg-[#0d0d0d] text-white/50">
    <span className="text-sm">Loading...</span>
  </div>
)

const root = ReactDOM.createRoot(rootElement)
root.render(
  <React.StrictMode>
    <Suspense fallback={<LoadingFallback />}>
      <App />
    </Suspense>
  </React.StrictMode>
)

