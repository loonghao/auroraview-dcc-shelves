/**
 * Window Manager - Utilities for managing browser windows and native window API
 *
 * Provides functions for:
 * - Opening settings in native windows (DCC mode)
 * - Opening settings in browser popups (standalone mode)
 * - Detecting available window APIs
 */

export interface WindowOptions {
  width?: number
  height?: number
  title?: string
}

export interface WindowResult {
  success: boolean
  window?: Window | null
  error?: string
}

/**
 * Check if native AuroraView window API is available
 */
export function hasNativeWindowAPI(): boolean {
  return !!(
    window.auroraview?.api?.create_window &&
    typeof window.auroraview.api.create_window === 'function'
  )
}

/**
 * Check if browser can open popup windows
 */
export function canOpenPopups(): boolean {
  // Most browsers allow popups if triggered by user action
  return typeof window.open === 'function'
}

/**
 * Open settings using native AuroraView window API
 */
export async function openSettingsNative(options: WindowOptions = {}): Promise<WindowResult> {
  if (!hasNativeWindowAPI()) {
    return { success: false, error: 'Native window API not available' }
  }

  try {
    const { width = 520, height = 650, title = 'Settings' } = options
    const settingsUrl = '/settings.html'

    await window.auroraview!.api!.create_window!({
      label: 'settings',
      url: settingsUrl,
      title,
      width,
      height,
    })

    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to open native window',
    }
  }
}

/**
 * Open settings in a browser popup window
 */
export function openSettingsPopup(options: WindowOptions = {}): WindowResult {
  const { width = 520, height = 650, title = 'Settings' } = options

  // Calculate center position
  const left = Math.max(0, (window.screen.width - width) / 2)
  const top = Math.max(0, (window.screen.height - height) / 2)

  const features = [
    `width=${width}`,
    `height=${height}`,
    `left=${left}`,
    `top=${top}`,
    'menubar=no',
    'toolbar=no',
    'location=no',
    'status=no',
    'resizable=yes',
    'scrollbars=yes',
  ].join(',')

  try {
    const popup = window.open('/settings.html', title, features)

    if (!popup) {
      return { success: false, error: 'Popup blocked by browser' }
    }

    return { success: true, window: popup }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to open popup',
    }
  }
}

/**
 * Focus existing settings window or open a new one
 */
export function focusOrOpenSettingsWindow(
  existingWindow: Window | null,
  options: WindowOptions = {}
): WindowResult {
  // Try to focus existing window
  if (existingWindow && !existingWindow.closed) {
    try {
      existingWindow.focus()
      return { success: true, window: existingWindow }
    } catch {
      // Window might be from different origin, try to open new one
    }
  }

  // Open new window
  return openSettingsPopup(options)
}

/**
 * Smart settings opener - tries native API first, then popup, returns result
 */
export async function openSettingsSmart(options: WindowOptions = {}): Promise<WindowResult> {
  // 1. Try native API (DCC mode)
  if (hasNativeWindowAPI()) {
    const result = await openSettingsNative(options)
    if (result.success) {
      return result
    }
    console.warn('[WindowManager] Native window failed:', result.error)
  }

  // 2. Try browser popup
  if (canOpenPopups()) {
    const result = openSettingsPopup(options)
    if (result.success) {
      return result
    }
    console.warn('[WindowManager] Popup failed:', result.error)
  }

  // 3. Return failure - caller should fallback to modal
  return { success: false, error: 'No window method available' }
}
