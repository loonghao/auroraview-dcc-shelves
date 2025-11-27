/**
 * IPC composable for communication with Python backend via AuroraView.
 */

import { ref, onMounted, onUnmounted } from 'vue'
import type { ShelvesConfig, LaunchResult } from '../types'

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
  const isConnected = ref(false)
  const config = ref<ShelvesConfig | null>(null)
  const error = ref<string | null>(null)

  /**
   * Call a Python API method.
   */
  async function callAPI<T>(method: string, params?: Record<string, unknown>): Promise<T> {
    if (!window.auroraview) {
      throw new Error('AuroraView not available')
    }
    return window.auroraview.call<T>(method, params)
  }

  /**
   * Get the shelves configuration from Python.
   */
  async function getConfig(): Promise<ShelvesConfig> {
    return callAPI<ShelvesConfig>('get_config')
  }

  /**
   * Launch a tool by button ID.
   */
  async function launchTool(buttonId: string): Promise<LaunchResult> {
    return callAPI<LaunchResult>('launch_tool', { button_id: buttonId })
  }

  /**
   * Register a callback for Python events.
   */
  function onPythonEvent(event: string, handler: (data: unknown) => void): void {
    if (window.auroraview) {
      window.auroraview.on(event, handler)
    }
  }

  /**
   * Remove a callback for Python events.
   */
  function offPythonEvent(event: string, handler: (data: unknown) => void): void {
    if (window.auroraview) {
      window.auroraview.off(event, handler)
    }
  }

  /**
   * Initialize connection and load configuration.
   */
  async function initialize(): Promise<void> {
    try {
      isConnected.value = !!window.auroraview
      if (isConnected.value) {
        config.value = await getConfig()
      }
      error.value = null
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to connect'
      console.error('Shelf IPC initialization error:', e)
    }
  }

  // Handle config updates from Python
  function handleConfigUpdate(data: unknown): void {
    config.value = data as ShelvesConfig
  }

  onMounted(() => {
    initialize()
    onPythonEvent('config_updated', handleConfigUpdate)
  })

  onUnmounted(() => {
    offPythonEvent('config_updated', handleConfigUpdate)
  })

  return {
    isConnected,
    config,
    error,
    launchTool,
    getConfig,
    callAPI,
    onPythonEvent,
    offPythonEvent,
    initialize,
  }
}

