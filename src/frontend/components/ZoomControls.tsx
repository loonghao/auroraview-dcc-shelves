/**
 * ZoomControls - Compact zoom control component for the shelf UI
 *
 * Provides zoom in/out buttons and current zoom level display.
 * Supports keyboard shortcuts and auto-zoom toggle.
 */

import { useEffect } from 'react'
import { ZoomIn, ZoomOut, RotateCcw, Monitor } from 'lucide-react'
import { useZoom } from '../hooks/useZoom'
import { cn } from '../lib/utils'

interface ZoomControlsProps {
  /** Additional CSS classes */
  className?: string
  /** Show as compact inline buttons */
  compact?: boolean
  /** Show screen info tooltip */
  showScreenInfo?: boolean
}

export function ZoomControls({
  className,
  compact = true,
  showScreenInfo = false,
}: ZoomControlsProps) {
  const [{ zoom, autoZoomEnabled, screenInfo }, controls] = useZoom()

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + Plus: Zoom in
      if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '=')) {
        e.preventDefault()
        controls.zoomIn()
      }
      // Ctrl/Cmd + Minus: Zoom out
      if ((e.ctrlKey || e.metaKey) && e.key === '-') {
        e.preventDefault()
        controls.zoomOut()
      }
      // Ctrl/Cmd + 0: Reset zoom
      if ((e.ctrlKey || e.metaKey) && e.key === '0') {
        e.preventDefault()
        controls.resetZoom()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [controls])

  const zoomPercent = Math.round(zoom * 100)

  const buttonClass = cn(
    'p-1 rounded hover:bg-white/10 transition-colors',
    'focus:outline-none focus:ring-1 focus:ring-white/30',
    'disabled:opacity-50 disabled:cursor-not-allowed'
  )

  if (compact) {
    return (
      <div
        className={cn(
          'flex items-center gap-1 text-xs text-white/70',
          className
        )}
      >
        <button
          onClick={() => controls.zoomOut()}
          disabled={zoom <= 0.5}
          className={buttonClass}
          title="Zoom Out (Ctrl+-)"
        >
          <ZoomOut className="w-3.5 h-3.5" />
        </button>

        <span
          className="min-w-[3rem] text-center cursor-pointer hover:text-white/90"
          onClick={() => controls.resetZoom()}
          title="Click to reset (Ctrl+0)"
        >
          {zoomPercent}%
        </span>

        <button
          onClick={() => controls.zoomIn()}
          disabled={zoom >= 2.0}
          className={buttonClass}
          title="Zoom In (Ctrl++)"
        >
          <ZoomIn className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={() => controls.autoZoom()}
          className={cn(buttonClass, autoZoomEnabled && 'text-blue-400')}
          title={`Auto Zoom ${autoZoomEnabled ? '(On)' : '(Off)'} - ${screenInfo?.screenType || 'unknown'}`}
        >
          <Monitor className="w-3.5 h-3.5" />
        </button>
      </div>
    )
  }

  // Full controls (for settings panel)
  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Display Zoom</span>
        <span className="text-sm text-white/60">{zoomPercent}%</span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => controls.zoomOut()}
          disabled={zoom <= 0.5}
          className={cn(buttonClass, 'p-2')}
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>

        <input
          type="range"
          min="50"
          max="200"
          step="5"
          value={zoomPercent}
          onChange={(e) => controls.setZoom(Number(e.target.value) / 100)}
          className="flex-1 h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
        />

        <button
          onClick={() => controls.zoomIn()}
          disabled={zoom >= 2.0}
          className={cn(buttonClass, 'p-2')}
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => controls.resetZoom()}
          className={cn(buttonClass, 'flex items-center gap-1 px-2 py-1')}
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span className="text-xs">Reset</span>
        </button>

        <button
          onClick={() => controls.toggleAutoZoom()}
          className={cn(
            buttonClass,
            'flex items-center gap-1 px-2 py-1',
            autoZoomEnabled && 'bg-blue-500/20 text-blue-400'
          )}
        >
          <Monitor className="w-3.5 h-3.5" />
          <span className="text-xs">Auto</span>
        </button>
      </div>

      {showScreenInfo && screenInfo && (
        <div className="text-xs text-white/40 mt-2">
          Screen: {screenInfo.width}x{screenInfo.height} ({screenInfo.screenType})
          {screenInfo.devicePixelRatio > 1 && ` @${screenInfo.devicePixelRatio}x`}
        </div>
      )}
    </div>
  )
}

export default ZoomControls

