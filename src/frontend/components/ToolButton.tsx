import React from 'react'
import type { ButtonConfig } from '../types'
import { ToolStatus } from '../types'
import { IconMapper } from './IconMapper'
import { DownloadCloud, Star } from 'lucide-react'
import { useLocalizedTool } from '../hooks/useLocalizedTool'

interface ToolButtonProps {
  button: ButtonConfig
  onLaunch: (button: ButtonConfig) => void
  onHover: (button: ButtonConfig) => void
  onLeave: () => void
  onContextMenu: (e: React.MouseEvent, button: ButtonConfig) => void
}

export const ToolButton: React.FC<ToolButtonProps> = ({
  button,
  onLaunch,
  onHover,
  onLeave,
  onContextMenu,
}) => {
  // Get localized tool name based on current language
  const { name: localizedName } = useLocalizedTool(button)
  const getStatusIndicator = () => {
    switch (button.status) {
      case ToolStatus.RUNNING:
        return (
          <div className="absolute top-1.5 right-1.5 flex items-center justify-center z-10 pointer-events-none">
            <div className="w-1.5 h-1.5 rounded-full bg-orange-500 shadow-[0_0_6px_rgba(249,115,22,0.8)] animate-pulse" />
          </div>
        )
      case ToolStatus.UPDATE_AVAILABLE:
        return (
          <div className="absolute top-1.5 right-1.5 z-10 pointer-events-none">
            <DownloadCloud size={9} className="text-brand-400" />
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div
      onClick={(e) => {
        e.stopPropagation()
        onLaunch(button)
      }}
      onMouseEnter={() => onHover(button)}
      onMouseLeave={onLeave}
      onContextMenu={(e) => {
        e.preventDefault()
        onContextMenu(e, button)
      }}
      className={`
        group relative flex flex-col items-center p-2 rounded-xl
        transition-all duration-200 cursor-pointer
        bg-white/[0.03] hover:bg-white/[0.08]
        border border-transparent hover:border-white/10
        hover:shadow-lg hover:shadow-black/20
        hover:-translate-y-0.5 active:scale-95
      `}
    >
      {getStatusIndicator()}

      {/* Icon Area */}
      <div className="mb-1.5 transition-all duration-200 group-hover:scale-110 text-white/50 group-hover:text-white/90">
        <IconMapper name={button.icon || 'Box'} size={22} />
      </div>

      {/* Tool Name & Star */}
      <div className="w-full flex items-center justify-center space-x-0.5">
        <span className="text-[9px] font-medium text-center truncate leading-tight max-w-[90%] text-white/40 group-hover:text-white/80 transition-colors">
          {localizedName}
        </span>
        {button.isFavorite && (
          <Star size={6} className="text-amber-500/60 group-hover:text-amber-400 fill-current shrink-0 transition-colors" />
        )}
      </div>
    </div>
  )
}

