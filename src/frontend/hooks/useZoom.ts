/**
 * useZoom - Smart zoom control hook for adaptive display support
 *
 * Supports 4K, 2K, and laptop screens with intelligent auto-detection
 * and manual zoom controls.
 */

import { useState, useEffect, useCallback, useMemo } from 'react'

export interface ZoomState {
  /** Current zoom level (1.0 = 100%) */
  zoom: number
  /** Whether auto-zoom is enabled */
  autoZoomEnabled: boolean
  /** Screen info for debugging */
  screenInfo: ScreenInfo | null
}

export interface ScreenInfo {
  width: number
  height: number
  devicePixelRatio: number
  screenType: 'mobile' | 'laptop' | 'desktop' | '2k' | '4k' | 'unknown'
}

export interface ZoomControls {
  /** Set zoom to specific level */
  setZoom: (level: number) => void
  /** Increase zoom by step (default 10%) */
  zoomIn: (step?: number) => void
  /** Decrease zoom by step (default 10%) */
  zoomOut: (step?: number) => void
  /** Reset zoom to 100% */
  resetZoom: () => void
  /** Auto-detect and apply optimal zoom */
  autoZoom: () => void
  /** Toggle auto-zoom feature */
  toggleAutoZoom: () => void
}

const ZOOM_MIN = 0.5
const ZOOM_MAX = 2.0
const ZOOM_STEP = 0.1
const STORAGE_KEY = 'auroraview-zoom-settings'

/**
 * Detect screen type based on resolution
 */
function detectScreenType(width: number, height: number): ScreenInfo['screenType'] {
  const maxDimension = Math.max(width, height)

  if (maxDimension >= 3840) return '4k'
  if (maxDimension >= 2560) return '2k'
  if (maxDimension >= 1920) return 'desktop'
  if (maxDimension >= 1366) return 'laptop'
  if (maxDimension < 768) return 'mobile'
  return 'unknown'
}

/**
 * Calculate optimal zoom based on screen characteristics
 */
function calculateOptimalZoom(screenInfo: ScreenInfo): number {
  const { screenType, devicePixelRatio } = screenInfo

  // Base zoom adjustments by screen type
  let baseZoom: number
  switch (screenType) {
    case '4k':
      baseZoom = 1.25 // 125% for 4K
      break
    case '2k':
      baseZoom = 1.1 // 110% for 2K/QHD
      break
    case 'desktop':
      baseZoom = 1.0 // 100% for Full HD
      break
    case 'laptop':
      baseZoom = 0.95 // 95% for laptops
      break
    case 'mobile':
      baseZoom = 0.85 // 85% for mobile
      break
    default:
      baseZoom = 1.0
  }

  // Adjust for HiDPI (devicePixelRatio > 1 means OS is already scaling)
  if (devicePixelRatio >= 2) {
    // Retina/HiDPI - OS handles scaling, use smaller zoom
    baseZoom *= 0.9
  } else if (devicePixelRatio >= 1.5) {
    baseZoom *= 0.95
  }

  // Clamp to valid range
  return Math.round(Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, baseZoom)) * 100) / 100
}

/**
 * Get current screen info
 */
function getScreenInfo(): ScreenInfo {
  const width = window.screen.width
  const height = window.screen.height
  const devicePixelRatio = window.devicePixelRatio || 1

  return {
    width,
    height,
    devicePixelRatio,
    screenType: detectScreenType(width, height),
  }
}

/**
 * Load saved zoom settings from localStorage
 */
function loadSavedSettings(): { zoom: number; autoZoomEnabled: boolean } | null {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch {
    // Ignore errors
  }
  return null
}

/**
 * Save zoom settings to localStorage
 */
function saveSettings(zoom: number, autoZoomEnabled: boolean): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ zoom, autoZoomEnabled }))
  } catch {
    // Ignore errors
  }
}

/**
 * Apply zoom level to the document
 */
function applyZoom(zoom: number): void {
  document.body.style.zoom = String(zoom)

  // Also notify Python backend if available
  if (window.auroraview?.api?.set_zoom) {
    window.auroraview.api.set_zoom(zoom).catch(() => {
      // Ignore errors - CSS zoom is already applied
    })
  }
}

/**
 * Hook for smart zoom control with screen adaptation
 */
export function useZoom(): [ZoomState, ZoomControls] {
  const [zoom, setZoomState] = useState<number>(1.0)
  const [autoZoomEnabled, setAutoZoomEnabled] = useState<boolean>(true)
  const [screenInfo, setScreenInfo] = useState<ScreenInfo | null>(null)

  // Initialize on mount
  useEffect(() => {
    const info = getScreenInfo()
    setScreenInfo(info)

    const saved = loadSavedSettings()
    if (saved) {
      setZoomState(saved.zoom)
      setAutoZoomEnabled(saved.autoZoomEnabled)
      applyZoom(saved.zoom)
    } else if (autoZoomEnabled) {
      // First time - auto-detect optimal zoom
      const optimalZoom = calculateOptimalZoom(info)
      setZoomState(optimalZoom)
      applyZoom(optimalZoom)
      saveSettings(optimalZoom, true)
    }
  }, [])

  // Handle window resize (screen change)
  useEffect(() => {
    const handleResize = () => {
      const info = getScreenInfo()
      setScreenInfo(info)

      if (autoZoomEnabled) {
        const optimalZoom = calculateOptimalZoom(info)
        setZoomState(optimalZoom)
        applyZoom(optimalZoom)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [autoZoomEnabled])

  // Controls
  const setZoom = useCallback((level: number) => {
    const clamped = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, level))
    const rounded = Math.round(clamped * 100) / 100
    setZoomState(rounded)
    applyZoom(rounded)
    saveSettings(rounded, autoZoomEnabled)
  }, [autoZoomEnabled])

  const zoomIn = useCallback((step: number = ZOOM_STEP) => {
    setZoom(zoom + step)
  }, [zoom, setZoom])

  const zoomOut = useCallback((step: number = ZOOM_STEP) => {
    setZoom(zoom - step)
  }, [zoom, setZoom])

  const resetZoom = useCallback(() => {
    setZoom(1.0)
  }, [setZoom])

  const autoZoom = useCallback(() => {
    if (screenInfo) {
      const optimalZoom = calculateOptimalZoom(screenInfo)
      setZoom(optimalZoom)
    }
  }, [screenInfo, setZoom])

  const toggleAutoZoom = useCallback(() => {
    const newValue = !autoZoomEnabled
    setAutoZoomEnabled(newValue)
    saveSettings(zoom, newValue)

    if (newValue && screenInfo) {
      // Re-apply auto zoom when enabled
      const optimalZoom = calculateOptimalZoom(screenInfo)
      setZoom(optimalZoom)
    }
  }, [autoZoomEnabled, zoom, screenInfo, setZoom])

  const state: ZoomState = useMemo(() => ({
    zoom,
    autoZoomEnabled,
    screenInfo,
  }), [zoom, autoZoomEnabled, screenInfo])

  const controls: ZoomControls = useMemo(() => ({
    setZoom,
    zoomIn,
    zoomOut,
    resetZoom,
    autoZoom,
    toggleAutoZoom,
  }), [setZoom, zoomIn, zoomOut, resetZoom, autoZoom, toggleAutoZoom])

  return [state, controls]
}

export default useZoom

