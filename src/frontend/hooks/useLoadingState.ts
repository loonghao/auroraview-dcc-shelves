/**
 * Hook for tracking WebView loading state from Python backend.
 *
 * This hook listens for loading state events from the AuroraView backend,
 * providing real-time loading progress information to the UI.
 *
 * Features:
 * - is_loading: Whether the page is currently loading
 * - progress: Loading progress (0-100)
 * - Automatic event subscription/cleanup
 */

import { useState, useEffect, useCallback } from 'react'

// Loading state interface from Python backend
export interface LoadingState {
  isLoading: boolean
  progress: number
}

// Debug logging helper
const debugLog = (message: string, ...args: unknown[]) => {
  console.log(`[LoadingState] ${message}`, ...args)
}

/**
 * Hook for tracking WebView loading state.
 *
 * @returns Loading state object with isLoading and progress
 *
 * @example
 * ```tsx
 * function App() {
 *   const { isLoading, progress } = useLoadingState()
 *
 *   return (
 *     <div>
 *       {isLoading && <ProgressBar value={progress} />}
 *       <MainContent />
 *     </div>
 *   )
 * }
 * ```
 */
export function useLoadingState() {
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)

  // Handle loading state event from Python
  const handleLoadingState = useCallback((data: unknown) => {
    const state = data as LoadingState
    debugLog('Received loading state:', state)
    setIsLoading(state.isLoading)
    setProgress(state.progress)
  }, [])

  useEffect(() => {
    // Register event listener for loading_state events
    if (window.auroraview?.on) {
      debugLog('Registering loading_state listener')
      window.auroraview.on('loading_state', handleLoadingState)
    }

    // Cleanup on unmount
    return () => {
      if (window.auroraview?.off) {
        debugLog('Unregistering loading_state listener')
        window.auroraview.off('loading_state', handleLoadingState)
      }
    }
  }, [handleLoadingState])

  return {
    isLoading,
    progress,
  }
}

export default useLoadingState

