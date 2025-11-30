/**
 * Banner settings dialog with PS-style transform controls.
 */

import React, { useState, useRef, useCallback, useEffect } from 'react'
import { Settings, Upload, Link, X, RotateCcw, Move, Crop } from 'lucide-react'
import type { BannerSettings } from '../hooks/useIndexedDB'
import { DEFAULT_BANNER_SETTINGS, fileToBase64 } from '../hooks/useIndexedDB'

type DragMode = 'none' | 'move' | 'resize-nw' | 'resize-ne' | 'resize-sw' | 'resize-se' | 'resize-n' | 'resize-s' | 'resize-e' | 'resize-w'
type ToolMode = 'move' | 'crop'

interface BannerSettingsDialogProps {
  isOpen: boolean
  onClose: () => void
  settings: BannerSettings
  onSave: (settings: BannerSettings) => void
}

export const BannerSettingsDialog: React.FC<BannerSettingsDialogProps> = ({
  isOpen,
  onClose,
  settings,
  onSave,
}) => {
  const [localSettings, setLocalSettings] = useState<BannerSettings>(settings)
  const [urlInput, setUrlInput] = useState(settings.imageType === 'url' ? settings.imageUrl || '' : '')
  const [toolMode, setToolMode] = useState<ToolMode>('move')
  const [dragMode, setDragMode] = useState<DragMode>('none')
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [imageTransform, setImageTransform] = useState({ x: 0, y: 0, scale: 1 })
  const fileInputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen) {
      setLocalSettings(settings)
      setUrlInput(settings.imageType === 'url' ? settings.imageUrl || '' : '')
      // Parse existing position/scale
      const pos = parsePosition(settings.objectPosition)
      setImageTransform({ x: pos.x - 50, y: pos.y - 50, scale: settings.scale })
    }
  }, [isOpen, settings])

  const parsePosition = (pos: string): { x: number; y: number } => {
    if (pos.includes('%')) {
      const parts = pos.split(' ')
      return { x: parseFloat(parts[0]) || 50, y: parseFloat(parts[1]) || 50 }
    }
    const presets: Record<string, { x: number; y: number }> = {
      'top': { x: 50, y: 0 }, 'center': { x: 50, y: 50 }, 'bottom': { x: 50, y: 100 },
    }
    return presets[pos] || { x: 50, y: 50 }
  }

  // Update settings when transform changes
  useEffect(() => {
    const posX = 50 + imageTransform.x
    const posY = 50 + imageTransform.y
    setLocalSettings(prev => ({
      ...prev,
      objectPosition: `${posX.toFixed(1)}% ${posY.toFixed(1)}%`,
      scale: imageTransform.scale,
    }))
  }, [imageTransform])

  const handleMouseDown = useCallback((e: React.MouseEvent, mode: DragMode) => {
    e.preventDefault()
    e.stopPropagation()
    setDragMode(mode)
    setDragStart({ x: e.clientX, y: e.clientY })
  }, [])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (dragMode === 'none' || !containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const deltaX = ((e.clientX - dragStart.x) / rect.width) * 100
    const deltaY = ((e.clientY - dragStart.y) / rect.height) * 100

    if (dragMode === 'move') {
      setImageTransform(prev => ({
        ...prev,
        x: Math.max(-50, Math.min(50, prev.x - deltaX)),
        y: Math.max(-50, Math.min(50, prev.y - deltaY)),
      }))
    } else {
      // Resize modes
      const scaleDelta = (dragMode.includes('e') || dragMode.includes('s')) ? deltaX * 0.02 : -deltaX * 0.02
      setImageTransform(prev => ({ ...prev, scale: Math.max(0.5, Math.min(3, prev.scale + scaleDelta)) }))
    }
    setDragStart({ x: e.clientX, y: e.clientY })
  }, [dragMode, dragStart])

  const handleMouseUp = useCallback(() => setDragMode('none'), [])

  if (!isOpen) return null

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const base64 = await fileToBase64(file)
      setLocalSettings(prev => ({ ...prev, imageUrl: base64, imageType: 'local' }))
      setImageTransform({ x: 0, y: 0, scale: 1 })
    } catch (err) { console.error('Failed to load image:', err) }
  }

  const handleUrlApply = () => {
    if (urlInput.trim()) {
      setLocalSettings(prev => ({ ...prev, imageUrl: urlInput.trim(), imageType: 'url' }))
      setImageTransform({ x: 0, y: 0, scale: 1 })
    }
  }

  const handleSave = () => { onSave(localSettings); onClose() }
  const handleReset = () => {
    setLocalSettings(DEFAULT_BANNER_SETTINGS)
    setUrlInput('')
    setImageTransform({ x: 0, y: 0, scale: 1 })
  }

  // Control handle component
  const Handle: React.FC<{ position: string; mode: DragMode; cursor: string }> = ({ position, mode, cursor }) => (
    <div
      className={`absolute w-3 h-3 bg-white border-2 border-blue-500 rounded-sm shadow-lg ${position}`}
      style={{ cursor, transform: 'translate(-50%, -50%)' }}
      onMouseDown={(e) => handleMouseDown(e, mode)}
    />
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onMouseMove={handleMouseMove} onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}>
      <div className="bg-[#1a1a1a] border border-white/10 rounded-xl w-[520px] max-h-[90vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-white/10">
          <div className="flex items-center gap-2 text-white">
            <Settings className="w-5 h-5" />
            <span className="font-medium">Banner Settings</span>
          </div>
          <div className="flex items-center gap-2">
            {/* Tool buttons */}
            <div className="flex bg-black/30 rounded-lg p-0.5">
              <button onClick={() => setToolMode('move')}
                className={`p-1.5 rounded transition-colors ${toolMode === 'move' ? 'bg-blue-500/30 text-blue-400' : 'text-white/50 hover:text-white/80'}`}
                title="Move & Scale">
                <Move className="w-4 h-4" />
              </button>
              <button onClick={() => setToolMode('crop')}
                className={`p-1.5 rounded transition-colors ${toolMode === 'crop' ? 'bg-blue-500/30 text-blue-400' : 'text-white/50 hover:text-white/80'}`}
                title="Crop">
                <Crop className="w-4 h-4" />
              </button>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg transition-colors">
              <X className="w-5 h-5 text-white/60" />
            </button>
          </div>
        </div>

        {/* Canvas Area - Matches actual Banner display */}
        <div className="relative bg-[#0a0a0a] p-4"
          style={{ backgroundImage: 'linear-gradient(45deg, #1a1a1a 25%, transparent 25%), linear-gradient(-45deg, #1a1a1a 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #1a1a1a 75%), linear-gradient(-45deg, transparent 75%, #1a1a1a 75%)', backgroundSize: '16px 16px', backgroundPosition: '0 0, 0 8px, 8px -8px, -8px 0px' }}>

          {/* Preview frame - Same aspect ratio as actual banner (h-20 = 80px, typical width ~500px) */}
          <div ref={containerRef} className="relative h-20 w-full overflow-hidden rounded-sm">
            {localSettings.imageUrl && (
              <>
                {/* Image - Exact same styles as Banner.tsx */}
                <img src={localSettings.imageUrl} alt="Preview" draggable={false}
                  className="absolute inset-0 w-full h-full pointer-events-none select-none"
                  style={{
                    objectFit: localSettings.objectFit,
                    objectPosition: localSettings.objectPosition,
                    transform: `scale(${imageTransform.scale})`,
                    filter: `brightness(${localSettings.brightness}%)`,
                    transformOrigin: 'center',
                  }}
                />

                {/* Bottom fade - Same as Banner.tsx */}
                <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-t from-[#0d0d0d] to-transparent pointer-events-none" />

                {/* Transform frame overlay */}
                <div className="absolute inset-0 border-2 border-blue-500/60 border-dashed pointer-events-none" />

                {/* Center move handle */}
                <div className="absolute inset-0 cursor-move" onMouseDown={(e) => handleMouseDown(e, 'move')}>
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-7 h-7 border-2 border-blue-500 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <Move className="w-3.5 h-3.5 text-blue-400" />
                  </div>
                </div>

                {/* Corner handles */}
                <Handle position="top-0 left-0" mode="resize-nw" cursor="nw-resize" />
                <Handle position="top-0 right-0" mode="resize-ne" cursor="ne-resize" />
                <Handle position="bottom-0 left-0" mode="resize-sw" cursor="sw-resize" />
                <Handle position="bottom-0 right-0" mode="resize-se" cursor="se-resize" />

                {/* Edge handles */}
                <Handle position="top-0 left-1/2" mode="resize-n" cursor="n-resize" />
                <Handle position="bottom-0 left-1/2" mode="resize-s" cursor="s-resize" />
                <Handle position="top-1/2 left-0" mode="resize-w" cursor="w-resize" />
                <Handle position="top-1/2 right-0" mode="resize-e" cursor="e-resize" />
              </>
            )}
          </div>

          {/* Scale indicator */}
          <div className="absolute bottom-5 right-5 text-[10px] text-white/40 bg-black/40 px-1.5 py-0.5 rounded">
            {Math.round(imageTransform.scale * 100)}%
          </div>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Image Source */}
          <div className="flex gap-2">
            <button onClick={() => fileInputRef.current?.click()}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors text-white/80 text-sm">
              <Upload className="w-4 h-4" />
              <span>Upload</span>
            </button>
            <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileSelect} className="hidden" />
            <input type="text" value={urlInput} onChange={(e) => setUrlInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleUrlApply()} placeholder="Image URL..."
              className="flex-1 px-3 py-2 bg-black/30 border border-white/10 rounded-lg text-white text-sm placeholder-white/30 focus:outline-none focus:border-blue-500/50" />
            <button onClick={handleUrlApply} className="px-3 py-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 rounded-lg transition-colors text-blue-400">
              <Link className="w-4 h-4" />
            </button>
          </div>

          {/* Opacity slider */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-sm text-white/70">Opacity</label>
              <span className="text-sm text-white/50">{localSettings.brightness}%</span>
            </div>
            <input type="range" min="20" max="150" step="5" value={localSettings.brightness}
              onChange={(e) => setLocalSettings(prev => ({ ...prev, brightness: parseInt(e.target.value) }))}
              className="w-full accent-blue-500" />
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between px-4 py-3 border-t border-white/10 bg-black/20">
          <button onClick={handleReset} className="flex items-center gap-2 px-3 py-1.5 text-white/60 hover:text-white/80 transition-colors text-sm">
            <RotateCcw className="w-4 h-4" /><span>Reset</span>
          </button>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-4 py-1.5 text-white/60 hover:text-white/80 transition-colors text-sm">Cancel</button>
            <button onClick={handleSave} className="px-4 py-1.5 bg-blue-500 hover:bg-blue-600 rounded-lg text-white text-sm font-medium transition-colors">Save</button>
          </div>
        </div>
      </div>
    </div>
  )
}
