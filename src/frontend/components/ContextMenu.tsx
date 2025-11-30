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

      {/* Menu - Apple style glassmorphism */}
      <div className="relative glass border border-white/10 rounded-xl shadow-2xl shadow-black/50
                      py-1.5 min-w-[180px] animate-fade-in overflow-hidden">
        <div className="px-3 py-2 border-b border-white/5">
          <div className="text-[11px] text-white/90 font-semibold truncate">{state.button.name}</div>
          <div className="text-[10px] text-white/30">{state.button.toolType}</div>
        </div>

        <button
          onClick={() => handleAction('open_path')}
          className="w-full px-3 py-2 text-left text-[11px] text-white/70 hover:bg-white/10
                     flex items-center gap-2.5 transition-colors"
        >
          <Folder size={13} className="text-white/40" />
          Open Location
        </button>

        <button
          onClick={() => handleAction('copy_path')}
          className="w-full px-3 py-2 text-left text-[11px] text-white/70 hover:bg-white/10
                     flex items-center gap-2.5 transition-colors"
        >
          <Copy size={13} className="text-white/40" />
          Copy Path
        </button>

        <button
          onClick={() => handleAction('view_source')}
          className="w-full px-3 py-2 text-left text-[11px] text-white/70 hover:bg-white/10
                     flex items-center gap-2.5 transition-colors"
        >
          <FileCode size={13} className="text-white/40" />
          View Source
        </button>

        <div className="border-t border-white/5 my-1" />

        <button
          onClick={() => handleAction('details')}
          className="w-full px-3 py-2 text-left text-[11px] text-white/70 hover:bg-white/10
                     flex items-center gap-2.5 transition-colors"
        >
          <Info size={13} className="text-white/40" />
          Details
        </button>
      </div>
    </div>
  )
}

