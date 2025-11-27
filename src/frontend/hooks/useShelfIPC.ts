/**
 * IPC hook for communication with Python backend via AuroraView.
 * Falls back to mock data in development mode when AuroraView is not available.
 */

import { useState, useEffect, useCallback } from 'react'
import type { LaunchResult, ButtonConfig } from '../types'
import { TOOLS_DATA } from '../data/mockData'

// Check if we're in development mode
const isDev = import.meta.env.DEV

// Type declarations for AuroraView
declare global {
  interface Window {
    auroraview?: {
      call: <T>(method: string, params?: Record<string, unknown>) => Promise<T>
      on: (event: string, handler: (data: unknown) => void) => void
      off: (event: string, handler: (data: unknown) => void) => void
    }
  }
}

export function useShelfIPC() {
  const [isConnected, setIsConnected] = useState(false)
  const [tools, setTools] = useState<ButtonConfig[]>([])
  const [error, setError] = useState<string | null>(null)

  /**
   * Call a Python API method.
   */
  const callAPI = useCallback(async <T>(method: string, params?: Record<string, unknown>): Promise<T> => {
    if (!window.auroraview) {
      throw new Error('AuroraView not available')
    }
    return window.auroraview.call<T>(method, params)
  }, [])

  /**
   * Get the tools configuration from Python or mock data.
   */
  const getTools = useCallback(async (): Promise<ButtonConfig[]> => {
    if (window.auroraview) {
      return callAPI<ButtonConfig[]>('get_tools')
    }
    // Return mock data when AuroraView is not available
    return TOOLS_DATA
  }, [callAPI])

  /**
   * Launch a tool by button ID.
   */
  const launchTool = useCallback(async (buttonId: string): Promise<LaunchResult> => {
    if (window.auroraview) {
      return callAPI<LaunchResult>('launch_tool', { button_id: buttonId })
    }
    // Mock launch in development
    console.log(`[Mock] Launching tool: ${buttonId}`)
    return {
      success: true,
      message: `[Mock] Tool ${buttonId} launched successfully`,
      buttonId,
    }
  }, [callAPI])

  /**
   * Register a callback for Python events.
   */
  const onPythonEvent = useCallback((event: string, handler: (data: unknown) => void): void => {
    if (window.auroraview) {
      window.auroraview.on(event, handler)
    }
  }, [])

  /**
   * Remove a callback for Python events.
   */
  const offPythonEvent = useCallback((event: string, handler: (data: unknown) => void): void => {
    if (window.auroraview) {
      window.auroraview.off(event, handler)
    }
  }, [])

  /**
   * Initialize connection and load tools.
   */
  const initialize = useCallback(async (): Promise<void> => {
    try {
      const hasAuroraView = !!window.auroraview
      setIsConnected(hasAuroraView)

      // Load tools (from AuroraView or mock data)
      const loadedTools = await getTools()
      setTools(loadedTools)

      if (isDev && !hasAuroraView) {
        console.log('[Dev] Using mock data - AuroraView not available')
      }

      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to connect')
      console.error('Shelf IPC initialization error:', e)
    }
  }, [getTools])

  // Handle tools updates from Python
  useEffect(() => {
    const handleToolsUpdate = (data: unknown): void => {
      setTools(data as ButtonConfig[])
    }

    initialize()
    onPythonEvent('tools_updated', handleToolsUpdate)

    return () => {
      offPythonEvent('tools_updated', handleToolsUpdate)
    }
  }, [initialize, onPythonEvent, offPythonEvent])

  return {
    isConnected,
    tools,
    error,
    launchTool,
    getTools,
    callAPI,
    onPythonEvent,
    offPythonEvent,
    initialize,
  }
}

