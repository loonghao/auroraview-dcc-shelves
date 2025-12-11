/**
 * Dialog for creating a new user tool.
 */

import React, { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { X, Plus, Folder, Code, Terminal } from 'lucide-react'
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
  const [description, setDescription] = useState('')
  const [descriptionZh, setDescriptionZh] = useState('')
  const [showIconPicker, setShowIconPicker] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
        icon,
        description: description.trim() || undefined,
        description_zh: descriptionZh.trim() || undefined,
      })

      // Reset form and close
      setName('')
      setNameZh('')
      setToolType(ToolType.PYTHON)
      setToolPath('')
      setIcon('Wrench')
      setDescription('')
      setDescriptionZh('')
      onClose()
    } catch (err) {
      setError(String(err))
    } finally {
      setIsSaving(false)
    }
  }, [name, nameZh, toolType, toolPath, icon, description, descriptionZh, onSave, onClose, t])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="relative glass border border-white/10 rounded-2xl shadow-2xl w-[400px] max-h-[80vh] overflow-hidden animate-scale-in">
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
        <div className="p-4 space-y-4 overflow-y-auto max-h-[calc(80vh-120px)] custom-scrollbar">
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

          {/* Tool Path */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-medium text-white/50 uppercase tracking-wider">
              {t('userTools.fields.toolPath')} *
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={toolPath}
                onChange={(e) => setToolPath(e.target.value)}
                placeholder={t('userTools.placeholders.toolPath')}
                className="flex-1 px-3 py-2 glass-subtle border border-white/10 rounded-lg text-xs text-white/90 placeholder-white/30 focus:outline-none focus:border-cyan-500/50"
              />
              <button className="px-3 py-2 glass-subtle border border-white/10 rounded-lg text-white/40 hover:text-white/70 hover:border-white/20 transition-all">
                <Folder size={14} />
              </button>
            </div>
          </div>

          {/* Icon Picker */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-medium text-white/50 uppercase tracking-wider">
              {t('userTools.fields.icon')}
            </label>
            <div className="relative">
              <button
                onClick={() => setShowIconPicker(!showIconPicker)}
                className="w-full flex items-center gap-2 px-3 py-2 glass-subtle border border-white/10 rounded-lg text-xs text-white/70 hover:border-white/20 transition-all"
              >
                <IconMapper name={icon} size={16} />
                <span>{icon}</span>
              </button>

              {showIconPicker && (
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

