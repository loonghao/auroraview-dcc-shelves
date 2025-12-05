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
      <div className="flex-1 flex items-center justify-center text-white/25 text-[10px]">
        {t('bottomPanel.noToolSelected')}
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar px-3 py-2">
      {/* Compact Tool Header - Single Row Layout */}
      <div className="flex items-center gap-2.5">
        {/* Tool Icon - Smaller */}
        <div className="w-9 h-9 rounded-md bg-white/[0.04] flex items-center justify-center shrink-0 overflow-hidden text-white/60">
          <IconMapper name={button.icon || 'Box'} size={20} />
        </div>

        {/* Tool Name, Version & Description */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <h3 className="text-white/90 font-medium text-[11px]">{localized.name}</h3>
            {button.version && (
              <span className="text-[8px] font-mono bg-emerald-500/15 px-1 py-px rounded text-emerald-400/80">
                v{button.version}
              </span>
            )}
          </div>
          <p className="text-white/40 text-[9px] truncate mt-0.5">{localized.description}</p>
        </div>

        {/* Quick Links - Inline */}
        {(button.wiki || button.docs || button.assets) && (
          <div className="flex items-center gap-1 shrink-0">
            {button.wiki && (
              <a href={button.wiki} target="_blank" rel="noopener noreferrer"
                className="p-1 rounded hover:bg-white/[0.06] transition-colors text-white/30 hover:text-white/60"
                title="Wiki">
                <ExternalLink size={11} />
              </a>
            )}
            {button.docs && (
              <a href={button.docs} target="_blank" rel="noopener noreferrer"
                className="p-1 rounded hover:bg-white/[0.06] transition-colors text-white/30 hover:text-white/60"
                title={t('bottomPanel.docs')}>
                <FileText size={11} />
              </a>
            )}
            {button.assets && (
              <a href={button.assets} target="_blank" rel="noopener noreferrer"
                className="p-1 rounded hover:bg-white/[0.06] transition-colors text-white/30 hover:text-white/60"
                title={t('bottomPanel.assets')}>
                <Folder size={11} />
              </a>
            )}
          </div>
        )}
      </div>

      {/* Compact Info Row */}
      <div className="flex items-center gap-3 mt-2 pt-2 border-t border-white/[0.04] text-[9px]">
        {/* Maintainer */}
        {button.maintainer && (
          <div className="flex items-center gap-1 text-white/35">
            <User size={9} />
            <span>{button.maintainer}</span>
          </div>
        )}

        {/* Category */}
        <div className="flex items-center gap-1 text-white/35">
          <Tag size={9} />
          <span>{localized.category}</span>
        </div>

        {/* Host */}
        <div className="flex items-center gap-1 text-white/35">
          <Monitor size={9} />
          <span>{formatHostName(currentHost)}</span>
        </div>
      </div>
    </div>
  )
}
