/**
 * IPC hook for communication with Python backend via AuroraView.
 * Falls back to mock data in development mode when AuroraView is not available.
 *
 * Communication patterns:
 * 1. API Mode (DCC/QtWebView): window.auroraview.api.method_name(args)
 * 2. Event Mode (Standalone): window.auroraview.send_event(event, data)
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import type { LaunchResult, ButtonConfig, ShelfConfig, BannerConfig } from '../types'
import { TOOLS_DATA } from '../data/mockData'

// Check if we're in development mode
const isDev = import.meta.env.DEV

// Debug logging helper
const debugLog = (message: string, ...args: unknown[]) => {
  console.log(`[ShelfIPC] ${message}`, ...args)
}

// System metrics interface
export interface SystemMetrics {
  cpu: number
  memory: number
  disk?: number
}

// Window creation result
export interface CreateWindowResult {
  success: boolean
  message?: string
  label: string
}

// Type declarations for AuroraView
declare global {
  interface Window {
    auroraview?: {
      // Event-based API (standalone mode)
      send_event?: (event: string, data?: Record<string, unknown>) => void
      on?: (event: string, handler: (data: unknown) => void) => void
      off?: (event: string, handler: (data: unknown) => void) => void
      // Direct API (DCC/QtWebView mode)
      // Note: AuroraView passes params as a single positional argument to Python
      // Python methods receive: def method(self, params=None)
      api?: {
        get_config: (params?: unknown) => Promise<ConfigResponse>
        launch_tool: (params: { button_id: string }) => Promise<LaunchResult>
        get_tool_path: (params: { button_id: string }) => Promise<{ buttonId: string; path: string }>
        get_system_metrics?: () => Promise<SystemMetrics>
        // Window management APIs
        create_window?: (params: {
          label: string
          url: string
          title: string
          width: number
          height: number
        }) => Promise<CreateWindowResult>
        close_window?: (params: { label: string }) => Promise<{ success: boolean; message?: string }>
        // Window drag API (for frameless window mode)
        start_drag?: (params?: Record<string, unknown>) => Promise<{ success: boolean; message?: string }>
        // Zoom APIs for adaptive display support
        set_zoom?: (scale_factor: number) => Promise<boolean>
        get_zoom?: () => Promise<number>
        zoom_in?: (step?: number) => Promise<boolean>
        zoom_out?: (step?: number) => Promise<boolean>
        reset_zoom?: () => Promise<boolean>
        auto_zoom?: () => Promise<number>
        // User tools management APIs
        get_user_tools?: (params?: unknown) => Promise<{ success: boolean; tools: Record<string, unknown>[]; message?: string }>
        save_user_tool?: (params: Record<string, unknown>) => Promise<{ success: boolean; tool: Record<string, unknown>; message?: string }>
        delete_user_tool?: (params: { id: string }) => Promise<{ success: boolean; message?: string }>
        export_user_tools?: (params?: unknown) => Promise<{ success: boolean; config: string; message?: string }>
        import_user_tools?: (params: { config: string; merge?: boolean }) => Promise<{ success: boolean; count: number; message?: string }>
      }
    }
  }
}

// Interface for config response from Python
interface ConfigResponse {
  shelves: ShelfConfig[]
  banner?: BannerConfig
  currentHost?: string
}

// Check which mode is available
// hasApiMode checks that get_config method is available (not just api namespace)
const hasApiMode = () => typeof window.auroraview?.api?.get_config === 'function'
const hasEventMode = () => typeof window.auroraview?.send_event === 'function'

// Default banner config
const DEFAULT_BANNER: BannerConfig = {
  title: 'Toolbox',
  subtitle: 'Production Tools & Scripts',
}

export function useShelfIPC() {
  const [isConnected, setIsConnected] = useState(false)
  const [tools, setTools] = useState<ButtonConfig[]>([])
  const [banner, setBanner] = useState<BannerConfig>(DEFAULT_BANNER)
  const [currentHost, setCurrentHost] = useState<string>('standalone')
  const [launchResult, setLaunchResult] = useState<LaunchResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<'api' | 'event' | 'mock'>('mock')

  // Use refs for event handlers to avoid re-registration on every render
  const handlersRef = useRef<{
    configResponse?: (data: unknown) => void
    launchResult?: (data: unknown) => void
    configUpdated?: (data: unknown) => void
  }>({})

  /**
   * Send an event to Python backend (event mode only).
   */
  const sendEvent = useCallback((event: string, data?: Record<string, unknown>): void => {
    if (window.auroraview?.send_event) {
      console.log(`[IPC] Sending event: ${event}`, data)
      window.auroraview.send_event(event, data)
    } else if (isDev) {
      console.log(`[Mock] Would send event: ${event}`, data)
    }
  }, [])

  /**
   * Register a callback for Python events (event mode only).
   */
  const onPythonEvent = useCallback((event: string, handler: (data: unknown) => void): void => {
    if (window.auroraview?.on) {
      window.auroraview.on(event, handler)
    }
  }, [])

  /**
   * Remove a callback for Python events (event mode only).
   */
  const offPythonEvent = useCallback((event: string, handler: (data: unknown) => void): void => {
    if (window.auroraview?.off) {
      window.auroraview.off(event, handler)
    }
  }, [])

  /**
   * Convert shelf config response to flat tools array.
   * Includes i18n fields (name_zh, description_zh, category_zh).
   */
  const parseConfigToTools = useCallback((config: ConfigResponse): ButtonConfig[] => {
    const allTools: ButtonConfig[] = []
    for (const shelf of config.shelves) {
      for (const button of shelf.buttons) {
        allTools.push({
          ...button,
          category: shelf.name,
          // Include i18n fields from shelf for category
          category_zh: shelf.name_zh || '',
        })
      }
    }
    return allTools
  }, [])

  /**
   * Request tools configuration from Python (event mode).
   */
  const requestConfig = useCallback((): void => {
    sendEvent('get_config', {})
  }, [sendEvent])

  /**
   * Load config using API mode.
   * AuroraView API binding: api.method_name() returns a Promise<T>
   */
  const loadConfigViaApi = useCallback(async (): Promise<void> => {
    debugLog('loadConfigViaApi called')
    debugLog('window.auroraview:', window.auroraview)
    debugLog('window.auroraview?.api:', window.auroraview?.api)

    if (!window.auroraview?.api) {
      debugLog('API not available yet, skipping')
      return
    }

    debugLog('Available API methods:', Object.keys(window.auroraview.api))

    const getConfigMethod = window.auroraview.api.get_config
    debugLog('get_config method:', getConfigMethod, 'type:', typeof getConfigMethod)

    if (typeof getConfigMethod !== 'function') {
      debugLog('get_config is not a function!')
      setError('get_config method not available')
      return
    }

    try {
      debugLog('Calling get_config()...')
      const config = await getConfigMethod()
      debugLog('Received config via API:', config)
      debugLog('Config type:', typeof config)
      debugLog('Config shelves:', config?.shelves)

      if (config && config.shelves) {
        const parsedTools = parseConfigToTools(config)
        debugLog('Parsed tools count:', parsedTools.length)
        setTools(parsedTools)

        // Update banner if provided
        if (config.banner) {
          debugLog('Setting banner config:', config.banner)
          setBanner({ ...DEFAULT_BANNER, ...config.banner })
        }

        // Update current host
        if (config.currentHost) {
          debugLog('Setting current host:', config.currentHost)
          setCurrentHost(config.currentHost)
        }
      } else {
        debugLog('Invalid config structure:', config)
        setError('Invalid config structure received')
      }
    } catch (err) {
      debugLog('Error loading config via API:', err)
      setError(String(err))
    }
  }, [parseConfigToTools])

  /**
   * Launch a tool by button ID.
   * For API mode: passes { button_id: buttonId } as params to Python
   *
   * Tool execution varies by type:
   * - PYTHON: exec() in DCC mode, subprocess in standalone
   * - EXECUTABLE: subprocess.Popen
   * - MEL: maya.mel.eval() (Maya only)
   * - JAVASCRIPT: eval() in WebView
   */
  const launchTool = useCallback(async (buttonId: string): Promise<void> => {
    // API mode (DCC/QtWebView)
    if (window.auroraview?.api) {
      debugLog(`Launching tool via API: ${buttonId}`)
      try {
        // Pass params as dict with button_id key
        const result = await window.auroraview.api.launch_tool({ button_id: buttonId })
        debugLog('Launch result:', result)

        // Handle JavaScript tools - execute in WebView
        if (result.success && result.javascript) {
          debugLog('Executing JavaScript tool in WebView')
          try {
            // eslint-disable-next-line no-eval
            eval(result.javascript)
            debugLog('JavaScript executed successfully')
          } catch (jsErr) {
            debugLog('JavaScript execution error:', jsErr)
            setLaunchResult({
              success: false,
              message: `JavaScript error: ${String(jsErr)}`,
              buttonId,
            })
            return
          }
        }

        setLaunchResult(result)
      } catch (err) {
        debugLog('Launch error:', err)
        setLaunchResult({
          success: false,
          message: String(err),
          buttonId,
        })
      }
      return
    }

    // Event mode (standalone)
    if (window.auroraview?.send_event) {
      debugLog(`Launching tool via event: ${buttonId}`)
      sendEvent('launch_tool', { buttonId })
      return
    }

    // Mock mode (development)
    if (isDev) {
      console.log(`[Mock] Launching tool: ${buttonId}`)
      setLaunchResult({
        success: true,
        message: `[Mock] Tool ${buttonId} launched successfully`,
        buttonId,
      })
    }
  }, [sendEvent])

  /**
   * Clear the launch result.
   */
  const clearLaunchResult = useCallback((): void => {
    setLaunchResult(null)
  }, [])

  /**
   * Initialize connection and set up event handlers.
   */
  useEffect(() => {
    debugLog('Initializing IPC connection...')
    debugLog('window.auroraview available:', !!window.auroraview)
    debugLog('API mode available:', hasApiMode())
    debugLog('Event mode available:', hasEventMode())
    debugLog('isDev:', isDev)

    // Determine which mode to use
    if (hasApiMode()) {
      // API mode (DCC/QtWebView) - preferred
      debugLog('Using API mode (DCC/QtWebView)')
      setMode('api')
      setIsConnected(true)

      // Load config via API
      loadConfigViaApi()
    } else if (hasEventMode()) {
      // Event mode (standalone WebView)
      debugLog('Using Event mode (standalone)')
      setMode('event')
      setIsConnected(true)

      // Handle config response from Python
      handlersRef.current.configResponse = (data: unknown) => {
        debugLog('Received config_response:', data)
        const config = data as ConfigResponse
        const parsedTools = parseConfigToTools(config)
        debugLog('Parsed tools count:', parsedTools.length)
        setTools(parsedTools)
        if (config.banner) {
          setBanner({ ...DEFAULT_BANNER, ...config.banner })
        }
        if (config.currentHost) {
          setCurrentHost(config.currentHost)
        }
      }

      // Handle launch result from Python
      handlersRef.current.launchResult = (data: unknown) => {
        debugLog('Received launch_result:', data)
        setLaunchResult(data as LaunchResult)
      }

      // Handle config updates from Python
      handlersRef.current.configUpdated = (data: unknown) => {
        debugLog('Received config_updated:', data)
        const config = data as ConfigResponse
        const parsedTools = parseConfigToTools(config)
        setTools(parsedTools)
        if (config.banner) {
          setBanner({ ...DEFAULT_BANNER, ...config.banner })
        }
        if (config.currentHost) {
          setCurrentHost(config.currentHost)
        }
      }

      // Register event handlers
      debugLog('Registering event handlers...')
      onPythonEvent('config_response', handlersRef.current.configResponse)
      onPythonEvent('launch_result', handlersRef.current.launchResult)
      onPythonEvent('config_updated', handlersRef.current.configUpdated)

      // Request initial config with a small delay to ensure handlers are ready
      debugLog('Requesting initial config...')
      setTimeout(() => {
        requestConfig()
      }, 100)
    } else if (isDev) {
      // Mock mode (development without AuroraView)
      debugLog('Using Mock mode - AuroraView not available')
      setMode('mock')
      setIsConnected(false)
      setTools(TOOLS_DATA)
    } else {
      // Production but no AuroraView - poll for it
      // Different DCCs have different WebView init speeds
      debugLog('Production mode but AuroraView not available yet, polling...')

      let attempts = 0
      const maxAttempts = 50 // 5 seconds max wait
      const pollInterval = 100 // 100ms between checks

      const pollForAuroraView = setInterval(() => {
        attempts++
        debugLog(`Polling for AuroraView (attempt ${attempts}/${maxAttempts})...`)

        if (hasApiMode()) {
          debugLog('AuroraView API now available!')
          clearInterval(pollForAuroraView)
          setMode('api')
          setIsConnected(true)
          loadConfigViaApi()
        } else if (hasEventMode()) {
          debugLog('AuroraView Event mode now available!')
          clearInterval(pollForAuroraView)
          setMode('event')
          setIsConnected(true)
          // Set up event handlers and request config
          handlersRef.current.configResponse = (data: unknown) => {
            const config = data as ConfigResponse
            const parsedTools = parseConfigToTools(config)
            setTools(parsedTools)
            if (config.banner) setBanner({ ...DEFAULT_BANNER, ...config.banner })
            if (config.currentHost) setCurrentHost(config.currentHost)
          }
          onPythonEvent('config_response', handlersRef.current.configResponse)
          setTimeout(() => requestConfig(), 50)
        } else if (attempts >= maxAttempts) {
          debugLog('Max attempts reached, AuroraView not available')
          clearInterval(pollForAuroraView)
          setError('AuroraView not available after timeout')
        }
      }, pollInterval)

      return () => clearInterval(pollForAuroraView)
    }

    setError(null)

    // Listen for API ready event from Python (after API injection)
    const handleApiReady = () => {
      debugLog('Received auroraview-api-ready event')
      if (hasApiMode()) {
        debugLog('API now available, reloading config...')
        loadConfigViaApi()
      }
    }
    window.addEventListener('auroraview-api-ready', handleApiReady)

    // Expose reload function for Python to call
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(window as any).__reloadShelfConfig = () => {
      debugLog('__reloadShelfConfig called from Python')
      loadConfigViaApi()
    }

    // Cleanup event handlers
    return () => {
      window.removeEventListener('auroraview-api-ready', handleApiReady)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (window as any).__reloadShelfConfig

      if (handlersRef.current.configResponse) {
        offPythonEvent('config_response', handlersRef.current.configResponse)
      }
      if (handlersRef.current.launchResult) {
        offPythonEvent('launch_result', handlersRef.current.launchResult)
      }
      if (handlersRef.current.configUpdated) {
        offPythonEvent('config_updated', handlersRef.current.configUpdated)
      }
    }
  }, [onPythonEvent, offPythonEvent, parseConfigToTools, requestConfig, loadConfigViaApi])

  return {
    isConnected,
    tools,
    banner,
    currentHost,
    launchResult,
    error,
    mode,
    launchTool,
    clearLaunchResult,
    requestConfig,
    sendEvent,
    onPythonEvent,
    offPythonEvent,
  }
}
