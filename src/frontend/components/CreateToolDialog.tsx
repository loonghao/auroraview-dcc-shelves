/**
 * Dialog for creating a new user tool.
 *
 * Features:
 * - Drag & drop file path support
 * - Native file picker via auroraview.dialog plugin
 * - Drag & drop custom icon (image file)
 * - Icon picker with built-in icons
 */

import React, { useState, useCallback, useRef, DragEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { X, Plus, Folder, Code, Terminal, Upload, ImageIcon } from 'lucide-react'
import { ToolType } from '../types'
import type { UserButtonConfig } from '../types'
import { IconMapper } from './IconMapper'

// Common icons for selection
const ICON_OPTIONS = [
  'Box', 'Wrench', 'Code', 'Terminal', 'Folder', 'File', 'FileCode',
  'Settings', 'Zap', 'Package', 'Layers', 'Grid', 'Palette', 'Brush',
  'Scissors', 'Wand2', 'Sparkles', 'Lightbulb', 'Cpu', 'Database',
  'Globe', 'Image', 'Film', 'Music', 'Eye', 'Camera',
]

// Type for dialog plugin API
interface DialogPluginAPI {
  openFile: (options?: {
    title?: string
    defaultPath?: string
    filters?: Array<{ name: string; extensions: string[] }>
  }) => Promise<{ path: string | null; cancelled: boolean }>
}

// Helper to get dialog plugin
const getDialogPlugin = (): DialogPluginAPI | undefined => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const av = (window as any).auroraview
  return av?.dialog as DialogPluginAPI | undefined
}

interface CreateToolDialogProps {
  isOpen: boolean
  onClose: () => void
  onSave: (tool: Omit<UserButtonConfig, 'id'>) => Promise<void>
}

export const CreateToolDialog: React.FC<CreateToolDialogProps> = ({
  isOpen,
  onClose,
  onSave,
}) => {
  const { t } = useTranslation()
  const [name, setName] = useState('')
  const [nameZh, setNameZh] = useState('')
  const [toolType, setToolType] = useState<ToolType>(ToolType.PYTHON)
  const [toolPath, setToolPath] = useState('')
  const [icon, setIcon] = useState('Wrench')
  const [customIconPath, setCustomIconPath] = useState<string | null>(null)
  const [description, setDescription] = useState('')
  const [descriptionZh, setDescriptionZh] = useState('')
  const [showIconPicker, setShowIconPicker] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Drag states
  const [isPathDragOver, setIsPathDragOver] = useState(false)
  const [isIconDragOver, setIsIconDragOver] = useState(false)

  const pathInputRef = useRef<HTMLInputElement>(null)

  // Check if native dialog is available
  const dialogPlugin = getDialogPlugin()
  const hasNativeDialog = !!dialogPlugin?.openFile

  // Handle file picker button click
  const handleBrowseFile = useCallback(async () => {
    const dialog = getDialogPlugin()
    if (!dialog) {
      console.warn('[CreateToolDialog] Native dialog not available')
      return
    }

    try {
      const filters = toolType === ToolType.PYTHON
        ? [{ name: 'Python Files', extensions: ['py'] }, { name: 'All Files', extensions: ['*'] }]
        : [{ name: 'Executable Files', extensions: ['exe', 'bat', 'cmd', 'sh'] }, { name: 'All Files', extensions: ['*'] }]

      const result = await dialog.openFile({
        title: t('userTools.selectToolFile'),
        filters,
      })

      if (!result.cancelled && result.path) {
        setToolPath(result.path)
        setError(null)
      }
    } catch (err) {
      console.error('[CreateToolDialog] Failed to open file dialog:', err)
    }
  }, [toolType, t])

  // Handle browse icon file
  const handleBrowseIcon = useCallback(async () => {
    const dialog = getDialogPlugin()
    if (!dialog) return

    try {
      const result = await dialog.openFile({
        title: t('userTools.selectIconFile'),
        filters: [
          { name: 'Image Files', extensions: ['png', 'jpg', 'jpeg', 'svg', 'ico', 'gif'] },
          { name: 'All Files', extensions: ['*'] },
        ],
      })

      if (!result.cancelled && result.path) {
        setCustomIconPath(result.path)
        setIcon('custom') // Mark as custom icon
        setShowIconPicker(false)
      }
    } catch (err) {
      console.error('[CreateToolDialog] Failed to open icon dialog:', err)
    }
  }, [t])

  // Handle drag over for tool path
  const handlePathDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsPathDragOver(true)
  }, [])

  const handlePathDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsPathDragOver(false)
  }, [])

  // Handle drop for tool path
  const handlePathDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsPathDragOver(false)

    // Try to get file path from drag data
    const files = e.dataTransfer.files
    if (files.length > 0) {
      const file = files[0]
      // In WebView, we can access the file path
      const filePath = (file as File & { path?: string }).path
      if (filePath) {
        setToolPath(filePath)
        setError(null)
        return
      }
    }

    // Try to get text (might be a path dragged from file manager)
    const text = e.dataTransfer.getData('text/plain')
    if (text) {
      // Clean up the path (remove file:// prefix if present)
      let path = text.trim()
      if (path.startsWith('file://')) {
        path = path.slice(7)
        // On Windows, remove leading slash from /C:/path
        if (/^\/[A-Za-z]:/.test(path)) {
          path = path.slice(1)
        }
      }
      setToolPath(path)
      setError(null)
    }
  }, [])

  // Handle drag over for icon
  const handleIconDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsIconDragOver(true)
  }, [])

  const handleIconDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsIconDragOver(false)
  }, [])

  // Handle drop for icon
  const handleIconDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsIconDragOver(false)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      const file = files[0]
      // Check if it's an image file
      if (file.type.startsWith('image/') || /\.(png|jpg|jpeg|svg|ico|gif)$/i.test(file.name)) {
        const filePath = (file as File & { path?: string }).path
        if (filePath) {
          setCustomIconPath(filePath)
          setIcon('custom')
          setShowIconPicker(false)
          return
        }
      }
    }

    // Try text data
    const text = e.dataTransfer.getData('text/plain')
    if (text && /\.(png|jpg|jpeg|svg|ico|gif)$/i.test(text)) {
      let path = text.trim()
      if (path.startsWith('file://')) {
        path = path.slice(7)
        if (/^\/[A-Za-z]:/.test(path)) {
          path = path.slice(1)
        }
      }
      setCustomIconPath(path)
      setIcon('custom')
      setShowIconPicker(false)
    }
  }, [])

  // Clear custom icon
  const handleClearCustomIcon = useCallback(() => {
    setCustomIconPath(null)
    setIcon('Wrench')
  }, [])

  const handleSave = useCallback(async () => {
    // Validate required fields
    if (!name.trim()) {
      setError(t('userTools.errors.nameRequired'))
      return
    }
    if (!toolPath.trim()) {
      setError(t('userTools.errors.pathRequired'))
      return
    }

    setIsSaving(true)
    setError(null)

    try {
      await onSave({
        name: name.trim(),
        name_zh: nameZh.trim() || undefined,
        toolType,
        toolPath: toolPath.trim(),
        // If custom icon, store the path; otherwise store the icon name
        icon: customIconPath || icon,
        description: description.trim() || undefined,
        description_zh: descriptionZh.trim() || undefined,
      })

      // Reset form and close
      setName('')
      setNameZh('')
      setToolType(ToolType.PYTHON)
      setToolPath('')
      setIcon('Wrench')
      setCustomIconPath(null)
      setDescription('')
      setDescriptionZh('')
      onClose()
    } catch (err) {
      setError(String(err))
    } finally {
      setIsSaving(false)
    }
  }, [name, nameZh, toolType, toolPath, icon, customIconPath, description, descriptionZh, onSave, onClose, t])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="relative glass border border-white/10 rounded-2xl shadow-2xl w-[420px] max-h-[85vh] overflow-hidden animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-gradient-to-r from-cyan-500/10 to-blue-500/10">
          <div className="flex items-center gap-2">
            <Plus size={16} className="text-cyan-400" />
            <h2 className="text-sm font-semibold text-white/90">
              {t('userTools.createTool')}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X size={14} className="text-white/40" />
          </button>
        </div>

        {/* Form */}
        <div className="p-4 space-y-4 overflow-y-auto max-h-[calc(85vh-120px)] custom-scrollbar">
          {/* Error message */}
          {error && (
            <div className="px-3 py-2 bg-red-500/20 border border-red-500/30 rounded-lg text-xs text-red-200">
              {error}
            </div>
          )}

          {/* Tool Name */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-medium text-white/50 uppercase tracking-wider">
              {t('userTools.fields.name')} *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('userTools.placeholders.name')}
              className="w-full px-3 py-2 glass-subtle border border-white/10 rounded-lg text-xs text-white/90 placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20"
            />
          </div>

          {/* Tool Name (Chinese) */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-medium text-white/50 uppercase tracking-wider">
              {t('userTools.fields.nameZh')}
            </label>
            <input
              type="text"
              value={nameZh}
              onChange={(e) => setNameZh(e.target.value)}
              placeholder={t('userTools.placeholders.nameZh')}
              className="w-full px-3 py-2 glass-subtle border border-white/10 rounded-lg text-xs text-white/90 placeholder-white/30 focus:outline-none focus:border-cyan-500/50"
            />
          </div>

          {/* Tool Type */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-medium text-white/50 uppercase tracking-wider">
              {t('userTools.fields.toolType')}
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setToolType(ToolType.PYTHON)}
                className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  toolType === ToolType.PYTHON
                    ? 'bg-gradient-to-r from-cyan-500/30 to-blue-500/30 border border-cyan-500/50 text-cyan-200'
                    : 'glass-subtle border border-white/10 text-white/60 hover:text-white/80'
                }`}
              >
                <Code size={12} />
                Python
              </button>
              <button
                onClick={() => setToolType(ToolType.EXECUTABLE)}
                className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  toolType === ToolType.EXECUTABLE
                    ? 'bg-gradient-to-r from-cyan-500/30 to-blue-500/30 border border-cyan-500/50 text-cyan-200'
                    : 'glass-subtle border border-white/10 text-white/60 hover:text-white/80'
                }`}
              >
                <Terminal size={12} />
                Executable
              </button>
            </div>
          </div>

          {/* Tool Path - with drag & drop */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-medium text-white/50 uppercase tracking-wider">
              {t('userTools.fields.toolPath')} *
            </label>
            <div
              className={`flex gap-2 p-0.5 rounded-lg transition-all ${
                isPathDragOver
                  ? 'bg-cyan-500/20 border-2 border-dashed border-cyan-500/50'
                  : ''
              }`}
              onDragOver={handlePathDragOver}
              onDragLeave={handlePathDragLeave}
              onDrop={handlePathDrop}
            >
              <input
                ref={pathInputRef}
                type="text"
                value={toolPath}
                onChange={(e) => setToolPath(e.target.value)}
                placeholder={isPathDragOver ? t('userTools.dropFileHere') : t('userTools.placeholders.toolPath')}
                className="flex-1 px-3 py-2 glass-subtle border border-white/10 rounded-lg text-xs text-white/90 placeholder-white/30 focus:outline-none focus:border-cyan-500/50"
              />
              <button
                onClick={handleBrowseFile}
                disabled={!hasNativeDialog}
                className={`px-3 py-2 glass-subtle border border-white/10 rounded-lg transition-all ${
                  hasNativeDialog
                    ? 'text-white/40 hover:text-white/70 hover:border-white/20'
                    : 'text-white/20 cursor-not-allowed'
                }`}
                title={hasNativeDialog ? t('userTools.browseFile') : t('userTools.nativeDialogUnavailable')}
              >
                <Folder size={14} />
              </button>
            </div>
            {isPathDragOver && (
              <p className="text-[10px] text-cyan-400 flex items-center gap-1">
                <Upload size={10} />
                {t('userTools.dropToSetPath')}
              </p>
            )}
          </div>

          {/* Icon Picker - with drag & drop for custom icon */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-medium text-white/50 uppercase tracking-wider">
              {t('userTools.fields.icon')}
            </label>
            <div className="relative">
              {/* Icon display / drop zone */}
              <div
                className={`flex items-center gap-2 p-0.5 rounded-lg transition-all ${
                  isIconDragOver
                    ? 'bg-cyan-500/20 border-2 border-dashed border-cyan-500/50'
                    : ''
                }`}
                onDragOver={handleIconDragOver}
                onDragLeave={handleIconDragLeave}
                onDrop={handleIconDrop}
              >
                <button
                  onClick={() => setShowIconPicker(!showIconPicker)}
                  className="flex-1 flex items-center gap-2 px-3 py-2 glass-subtle border border-white/10 rounded-lg text-xs text-white/70 hover:border-white/20 transition-all"
                >
                  {customIconPath ? (
                    <>
                      <img
                        src={`https://auroraview.localhost/file/${customIconPath}`}
                        alt="Custom icon"
                        className="w-4 h-4 object-contain"
                        onError={(e) => {
                          // Fallback to default icon on error
                          e.currentTarget.style.display = 'none'
                        }}
                      />
                      <span className="truncate text-cyan-300">{customIconPath.split(/[/\\]/).pop()}</span>
                    </>
                  ) : (
                    <>
                      <IconMapper name={icon} size={16} />
                      <span>{icon}</span>
                    </>
                  )}
                </button>

                {/* Browse icon button */}
                <button
                  onClick={handleBrowseIcon}
                  disabled={!hasNativeDialog}
                  className={`px-3 py-2 glass-subtle border border-white/10 rounded-lg transition-all ${
                    hasNativeDialog
                      ? 'text-white/40 hover:text-white/70 hover:border-white/20'
                      : 'text-white/20 cursor-not-allowed'
                  }`}
                  title={t('userTools.browseIcon')}
                >
                  <ImageIcon size={14} />
                </button>

                {/* Clear custom icon button */}
                {customIconPath && (
                  <button
                    onClick={handleClearCustomIcon}
                    className="px-2 py-2 glass-subtle border border-white/10 rounded-lg text-white/40 hover:text-red-400 hover:border-red-500/30 transition-all"
                    title={t('userTools.clearCustomIcon')}
                  >
                    <X size={14} />
                  </button>
                )}
              </div>

              {isIconDragOver && (
                <p className="text-[10px] text-cyan-400 flex items-center gap-1 mt-1">
                  <Upload size={10} />
                  {t('userTools.dropIconHere')}
                </p>
              )}

              {/* Icon picker dropdown */}
              {showIconPicker && !customIconPath && (
                <div className="absolute top-full left-0 right-0 mt-1 p-2 glass border border-white/10 rounded-lg shadow-xl z-10 grid grid-cols-8 gap-1 max-h-32 overflow-y-auto custom-scrollbar">
                  {ICON_OPTIONS.map((iconName) => (
                    <button
                      key={iconName}
                      onClick={() => {
                        setIcon(iconName)
                        setShowIconPicker(false)
                      }}
                      className={`p-1.5 rounded-lg transition-all ${
                        icon === iconName
                          ? 'bg-cyan-500/30 text-cyan-200'
                          : 'hover:bg-white/10 text-white/50 hover:text-white/80'
                      }`}
                      title={iconName}
                    >
                      <IconMapper name={iconName} size={14} />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-medium text-white/50 uppercase tracking-wider">
              {t('userTools.fields.description')}
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('userTools.placeholders.description')}
              rows={2}
              className="w-full px-3 py-2 glass-subtle border border-white/10 rounded-lg text-xs text-white/90 placeholder-white/30 focus:outline-none focus:border-cyan-500/50 resize-none"
            />
          </div>

          {/* Description (Chinese) */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-medium text-white/50 uppercase tracking-wider">
              {t('userTools.fields.descriptionZh')}
            </label>
            <textarea
              value={descriptionZh}
              onChange={(e) => setDescriptionZh(e.target.value)}
              placeholder={t('userTools.placeholders.descriptionZh')}
              rows={2}
              className="w-full px-3 py-2 glass-subtle border border-white/10 rounded-lg text-xs text-white/90 placeholder-white/30 focus:outline-none focus:border-cyan-500/50 resize-none"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-white/10">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-white/60 hover:text-white/80 transition-colors"
          >
            {t('common.cancel')}
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-1.5 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {isSaving ? t('common.loading') : t('common.save')}
          </button>
        </div>
      </div>
    </div>
  )
}
