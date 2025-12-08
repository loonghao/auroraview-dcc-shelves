/**
 * useWindowDrag - Hook for handling frameless window dragging
 *
 * In frameless window mode, we need to implement custom window dragging
 * by calling the Python API to initiate native Win32 window drag.
 */

import { useCallback, useRef } from 'react'

// Note: Window.auroraview types are declared in useShelfIPC.ts

/**
 * Check if native window API is available (running in AuroraView/DCC mode)
 *
 * We check for window.auroraview.api existence, which indicates we're running
 * inside a DCC app with native Qt title bar. The specific start_drag method
 * is only needed for frameless windows.
 */
export function hasWindowDragAPI(): boolean {
  // Check if auroraview bridge exists - this means we're in DCC mode
  // Even if start_drag is not available, we should hide HTML title bar
  // because DCC mode has native Qt title bar
  return !!(window.auroraview?.api)
}

/**
 * Hook for window drag functionality
 */
export function useWindowDrag() {
  const isDragging = useRef(false)

  /**
   * Start window drag - call this on mousedown of the title bar
   */
  const startDrag = useCallback(async () => {
    if (!hasWindowDragAPI()) {
      console.debug('[useWindowDrag] Native drag API not available')
      return false
    }

    try {
      isDragging.current = true
      const result = await window.auroraview!.api!.start_drag!({})
      isDragging.current = false

      if (!result.success) {
        console.warn('[useWindowDrag] start_drag failed:', result.message)
        return false
      }

      console.debug('[useWindowDrag] Window drag started')
      return true
    } catch (err) {
      isDragging.current = false
      console.error('[useWindowDrag] Error starting drag:', err)
      return false
    }
  }, [])

  /**
   * Close main window
   */
  const closeWindow = useCallback(async () => {
    if (typeof window.auroraview?.api?.close_window !== 'function') {
      console.debug('[useWindowDrag] close_window API not available')
      return false
    }

    try {
      // Use 'main' as label to close the main window
      const result = await window.auroraview.api.close_window({ label: 'main' })
      return result.success
    } catch (err) {
      console.error('[useWindowDrag] Error closing window:', err)
      return false
    }
  }, [])

  /**
   * Get mouse event handlers for a draggable title bar element
   */
  const getDragHandlers = useCallback(() => ({
    onMouseDown: (e: React.MouseEvent) => {
      // Only handle left mouse button
      if (e.button !== 0) return

      // Don't drag if clicking on interactive elements
      const target = e.target as HTMLElement
      if (
        target.tagName === 'BUTTON' ||
        target.tagName === 'INPUT' ||
        target.tagName === 'A' ||
        target.closest('button') ||
        target.closest('a')
      ) {
        return
      }

      e.preventDefault()
      startDrag()
    },
  }), [startDrag])

  return {
    startDrag,
    closeWindow,
    getDragHandlers,
    hasNativeAPI: hasWindowDragAPI,
  }
}
