import React from 'react'
import { useTranslation } from 'react-i18next'
import type { ButtonConfig } from '../types'
import { ToolType } from '../types'
import { Tag, Monitor, ChevronUp, ChevronDown } from 'lucide-react'
import { useLocalizedTool } from '../hooks/useLocalizedTool'

interface InfoFooterProps {
  button: ButtonConfig | null
  currentHost?: string
  isExpanded?: boolean
  onToggle?: () => void
}

export const InfoFooter: React.FC<InfoFooterProps> = ({
  button,
  currentHost = 'standalone',
  isExpanded = false,
  onToggle
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
  // If no button is hovered, hide completely (drawer style - default hidden)
  if (!button) {
    return null
  }


  // Drawer-style info footer that slides up when a tool is hovered
  return (
    <div 
      className={`
        fixed bottom-0 left-0 right-0 z-30
        transform transition-transform duration-300 ease-out
        ${button ? 'translate-y-0' : 'translate-y-full'}
      `}
    >
      <div className="glass border-t border-white/10 px-3 py-2.5 animate-slide-up">
        {/* Toggle handle (optional) */}
        {onToggle && (
          <button
            onClick={onToggle}
            className="absolute -top-5 left-1/2 -translate-x-1/2 
              px-3 py-1 glass border border-white/10 border-b-0 rounded-t-lg
              text-white/40 hover:text-white/60 transition-colors"
          >
            {isExpanded ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
          </button>
        )}

        {/* Tool Info Row */}
        <div className="flex items-center justify-between gap-3">
          {/* Left: Name, Version, Description */}
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <span className="text-white/95 font-semibold text-[11px] shrink-0">
              {localized.name}
            </span>
            {button.version && (
              <span className="text-[9px] font-mono bg-blue-500/20 px-1.5 py-0.5 rounded-md text-blue-300 shrink-0">
                v{button.version}
              </span>
            )}
            <span className="text-white/40 text-[10px] truncate">
              {localized.description}
            </span>
          </div>

          {/* Right: Host & Category */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="flex items-center gap-1 text-[9px] text-white/30">
              <Monitor size={10} />
              <span className="uppercase">{formatHostName(currentHost)}</span>
            </div>
            <div className="flex items-center gap-1 text-[9px] text-white/30">
              <Tag size={9} />
              <span className="uppercase">{localized.category}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
