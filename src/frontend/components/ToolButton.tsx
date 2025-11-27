import React from 'react'
import type { ButtonConfig } from '../types'
import { ToolStatus } from '../types'
import { IconMapper } from './IconMapper'
import { DownloadCloud, Star } from 'lucide-react'

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
  const getStatusIndicator = () => {
    switch (button.status) {
      case ToolStatus.RUNNING:
        return (
          <div className="absolute top-2 right-2 flex items-center justify-center z-10 pointer-events-none">
            <div className="w-1.5 h-1.5 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.8)] animate-pulse" />
          </div>
        )
      case ToolStatus.UPDATE_AVAILABLE:
        return (
          <div className="absolute top-2 right-2 z-10 pointer-events-none">
            <DownloadCloud size={10} className="text-brand-400" />
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
        group relative flex flex-col items-center p-4 rounded-xl
        transition-all duration-150 cursor-pointer
        bg-[#1e1e1e] hover:bg-[#2a2a2a] hover:ring-1 hover:ring-brand-500/30
        hover:shadow-lg hover:-translate-y-0.5
      `}
    >
      {getStatusIndicator()}

      {/* Icon Area */}
      <div className={`
        mb-3 transition-transform duration-200 group-hover:scale-110 text-gray-400 group-hover:text-gray-100
      `}>
        <IconMapper name={button.icon || 'Box'} size={36} />
      </div>

      {/* Tool Name & Star */}
      <div className="w-full flex items-center justify-center space-x-1">
        <span className={`
            text-[11px] font-medium text-center truncate leading-tight max-w-[85%]
            text-gray-400 group-hover:text-brand-400 transition-colors
        `}>
          {button.name}
        </span>
        {button.isFavorite && (
          <Star size={8} className="text-yellow-600 group-hover:text-yellow-400 fill-current shrink-0 transition-colors" />
        )}
      </div>
    </div>
  )
}

