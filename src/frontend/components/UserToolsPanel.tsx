/**
 * Panel for managing user-created tools.
 * Provides UI for creating, editing, and importing/exporting tools.
 */

import React, { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Plus,
  Download,
  Upload,
  Trash2,
  User,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from 'lucide-react'
import { IconMapper } from './IconMapper'
import { CreateToolDialog } from './CreateToolDialog'
import { useUserTools } from '../hooks/useUserTools'

interface UserToolsPanelProps {
  isExpanded: boolean
  onToggle: () => void
}

export const UserToolsPanel: React.FC<UserToolsPanelProps> = ({
  isExpanded,
  onToggle,
}) => {
  const { t } = useTranslation()
  const {
    userTools,
    isLoading,
    error,
    addTool,
    deleteTool,
    downloadToolsAsFile,
    triggerImportFile,
  } = useUserTools()

  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  const handleCreateTool = useCallback(async (tool: Parameters<typeof addTool>[0]) => {
    await addTool(tool)
  }, [addTool])

  const handleDeleteTool = useCallback(async (id: string) => {
    await deleteTool(id)
    setDeleteConfirmId(null)
  }, [deleteTool])

  return (
    <div className="border-t border-white/5">
      {/* Header - Toggle Button */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-2">
          <User size={12} className="text-cyan-400" />
          <span className="text-[10px] font-medium text-white/70">
            {t('userTools.title')}
          </span>
          <span className="px-1.5 py-0.5 bg-cyan-500/20 rounded text-[9px] text-cyan-300">
            {userTools.length}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp size={12} className="text-white/40" />
        ) : (
          <ChevronDown size={12} className="text-white/40" />
        )}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-3 pb-3 space-y-3 animate-fade-in">
          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCreateDialog(true)}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 hover:from-cyan-500/30 hover:to-blue-500/30 border border-cyan-500/30 rounded-lg text-[10px] font-medium text-cyan-200 transition-all"
            >
              <Plus size={12} />
              {t('userTools.create')}
            </button>
            <button
              onClick={triggerImportFile}
              className="flex items-center justify-center gap-1.5 px-3 py-1.5 glass-subtle border border-white/10 hover:border-cyan-500/30 rounded-lg text-[10px] font-medium text-white/60 hover:text-cyan-300 transition-all"
              title={t('userTools.import')}
            >
              <Upload size={12} />
            </button>
            <button
              onClick={downloadToolsAsFile}
              disabled={userTools.length === 0}
              className="flex items-center justify-center gap-1.5 px-3 py-1.5 glass-subtle border border-white/10 hover:border-cyan-500/30 rounded-lg text-[10px] font-medium text-white/60 hover:text-cyan-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              title={t('userTools.export')}
            >
              <Download size={12} />
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 px-2 py-1.5 bg-red-500/20 border border-red-500/30 rounded-lg text-[10px] text-red-200">
              <AlertCircle size={12} />
              {error}
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="text-center py-4 text-[10px] text-white/40">
              {t('common.loading')}
            </div>
          )}

          {/* Empty State */}
          {!isLoading && userTools.length === 0 && (
            <div className="text-center py-4 space-y-2">
              <User size={20} className="mx-auto text-white/20" />
              <p className="text-[10px] text-white/40">
                {t('userTools.empty')}
              </p>
              <p className="text-[9px] text-white/30">
                {t('userTools.emptyHint')}
              </p>
            </div>
          )}

          {/* User Tools List */}
          {userTools.length > 0 && (
            <div className="space-y-1.5 max-h-40 overflow-y-auto custom-scrollbar">
              {userTools.map((tool) => (
                <div
                  key={tool.id}
                  className="flex items-center justify-between px-2 py-1.5 glass-subtle rounded-lg group hover:border-cyan-500/20 border border-transparent transition-all"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <IconMapper name={tool.icon} size={14} className="text-cyan-300 shrink-0" />
                    <span className="text-[10px] text-white/70 truncate">
                      {tool.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {deleteConfirmId === tool.id ? (
                      <>
                        <button
                          onClick={() => handleDeleteTool(tool.id)}
                          className="p-1 bg-red-500/30 hover:bg-red-500/50 rounded text-red-300 transition-colors"
                          title={t('common.confirm')}
                        >
                          <Trash2 size={10} />
                        </button>
                        <button
                          onClick={() => setDeleteConfirmId(null)}
                          className="p-1 hover:bg-white/10 rounded text-white/40 transition-colors"
                          title={t('common.cancel')}
                        >
                          ×
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirmId(tool.id)}
                        className="p-1 hover:bg-white/10 rounded text-white/40 hover:text-red-400 transition-colors"
                        title={t('common.delete')}
                      >
                        <Trash2 size={10} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create Tool Dialog */}
      <CreateToolDialog
        isOpen={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onSave={handleCreateTool}
      />
    </div>
  )
}

