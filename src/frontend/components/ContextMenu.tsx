import React, { useEffect, useRef } from 'react'
import type { ContextMenuState, ButtonConfig } from '../types'
import { FileCode, Folder, Info, Copy } from 'lucide-react'

interface ContextMenuProps {
  state: ContextMenuState
  onClose: () => void
  onAction: (action: string, button: ButtonConfig) => void
}

export const ContextMenu: React.FC<ContextMenuProps> = ({ state, onClose, onAction }) => {
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  if (!state.visible || !state.button) return null

  const handleAction = (action: string) => {
    if (state.button) {
      onAction(action, state.button)
    }
    onClose()
  }

  return (
    <div
      ref={menuRef}
      style={{ left: state.x, top: state.y }}
      className="fixed z-50"
    >
      {/* Backdrop */}
      <div className="fixed inset-0" onClick={onClose} />

      {/* Menu */}
      <div className="relative bg-[#2a2a2a] border border-[#444] rounded-lg shadow-xl
                      py-1 min-w-[160px] animate-fade-in">
        <div className="px-3 py-2 border-b border-[#444]">
          <div className="text-xs text-white font-medium truncate">{state.button.name}</div>
          <div className="text-[10px] text-gray-500">{state.button.toolType}</div>
        </div>

        <button
          onClick={() => handleAction('open_path')}
          className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-[#3a3a3a]
                     flex items-center gap-2 transition-colors"
        >
          <Folder size={14} />
          Open Location
        </button>

        <button
          onClick={() => handleAction('copy_path')}
          className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-[#3a3a3a]
                     flex items-center gap-2 transition-colors"
        >
          <Copy size={14} />
          Copy Path
        </button>

        <button
          onClick={() => handleAction('view_source')}
          className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-[#3a3a3a]
                     flex items-center gap-2 transition-colors"
        >
          <FileCode size={14} />
          View Source
        </button>

        <div className="border-t border-[#444] my-1" />

        <button
          onClick={() => handleAction('details')}
          className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-[#3a3a3a]
                     flex items-center gap-2 transition-colors"
        >
          <Info size={14} />
          Details
        </button>
      </div>
    </div>
  )
}

