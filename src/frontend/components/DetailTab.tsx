import React from 'react'
import { useTranslation } from 'react-i18next'
import type { ButtonConfig } from '../types'
import { ToolType } from '../types'
import { Tag, Monitor, User, FileText, Folder, ExternalLink } from 'lucide-react'
import { useLocalizedTool } from '../hooks/useLocalizedTool'
import { IconMapper } from './IconMapper'

interface DetailTabProps {
  button: ButtonConfig | null
  currentHost?: string
}

export const DetailTab: React.FC<DetailTabProps> = ({
  button,
  currentHost = 'standalone',
}) => {
  const { t } = useTranslation()

  // Get localized tool properties (safe default for null button)
  const localized = useLocalizedTool(button || {
    id: '', name: '', description: '', category: '',
    toolType: ToolType.PYTHON, toolPath: '', icon: '', args: []
  })

  // Format host name for display using i18n
  const formatHostName = (host: string): string => {
    const hostKey = host.toLowerCase() as 'maya' | 'houdini' | 'nuke' | 'standalone'
    return t(`hosts.${hostKey}`, host)
  }

  // Show empty state when no tool is selected
  if (!button) {
    return (
      <div className="flex-1 flex items-center justify-center text-white/30 text-[11px]">
        {t('bottomPanel.noToolSelected')}
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
      {/* Tool Header */}
      <div className="flex items-start gap-3 mb-4">
        {/* Tool Icon - use IconMapper to handle both Lucide icons and local images */}
        <div className="w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center shrink-0 overflow-hidden text-white/70">
          <IconMapper name={button.icon || 'Box'} size={28} />
        </div>

        {/* Tool Name & Version */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-white/95 font-semibold text-sm">{localized.name}</h3>
            {button.version && (
              <span className="text-[9px] font-mono bg-blue-500/20 px-1.5 py-0.5 rounded-md text-blue-300">
                v{button.version}
              </span>
            )}
          </div>
          <p className="text-white/50 text-[11px] line-clamp-2">{localized.description}</p>
        </div>

        {/* Quick Links */}
        {(button.wiki || button.docs || button.assets) && (
          <div className="flex items-center gap-2 shrink-0">
            {button.wiki && (
              <a href={button.wiki} target="_blank" rel="noopener noreferrer"
                className="flex flex-col items-center gap-0.5 p-1.5 rounded hover:bg-white/5 transition-colors text-white/40 hover:text-white/70">
                <ExternalLink size={14} />
                <span className="text-[8px]">WIKI</span>
              </a>
            )}
            {button.docs && (
              <a href={button.docs} target="_blank" rel="noopener noreferrer"
                className="flex flex-col items-center gap-0.5 p-1.5 rounded hover:bg-white/5 transition-colors text-white/40 hover:text-white/70">
                <FileText size={14} />
                <span className="text-[8px]">{t('bottomPanel.docs')}</span>
              </a>
            )}
            {button.assets && (
              <a href={button.assets} target="_blank" rel="noopener noreferrer"
                className="flex flex-col items-center gap-0.5 p-1.5 rounded hover:bg-white/5 transition-colors text-white/40 hover:text-white/70">
                <Folder size={14} />
                <span className="text-[8px]">{t('bottomPanel.assets')}</span>
              </a>
            )}
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="h-px bg-white/5 mb-3" />

      {/* Info Grid */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[10px]">
        {/* Maintainer */}
        {button.maintainer && (
          <div className="flex items-center gap-2">
            <User size={11} className="text-white/30" />
            <span className="text-white/40">{t('bottomPanel.maintainer')}:</span>
            <span className="text-white/70">{button.maintainer}</span>
          </div>
        )}

        {/* Category */}
        <div className="flex items-center gap-2">
          <Tag size={11} className="text-white/30" />
          <span className="text-white/40">{t('bottomPanel.category')}:</span>
          <span className="text-white/70">{localized.category}</span>
        </div>

        {/* Host */}
        <div className="flex items-center gap-2">
          <Monitor size={11} className="text-white/30" />
          <span className="text-white/40">{t('bottomPanel.host')}:</span>
          <span className="text-white/70">{formatHostName(currentHost)}</span>
        </div>
      </div>
    </div>
  )
}
