import React from 'react'
import type { ShelfConfig, ButtonConfig } from '../types'
import { ToolButton } from './ToolButton'

interface ShelfGroupProps {
  shelf: ShelfConfig
  onLaunch: (button: ButtonConfig) => void
  onHover: (button: ButtonConfig) => void
  onContextMenu: (e: React.MouseEvent, button: ButtonConfig) => void
}

export const ShelfGroup: React.FC<ShelfGroupProps> = ({
  shelf,
  onLaunch,
  onHover,
  onContextMenu,
}) => {
  return (
    <div className="mb-6 animate-fade-in">
      {/* Shelf title */}
      <h2 className="text-xs font-bold text-gray-400 mb-3 pl-1 uppercase tracking-wider opacity-80">
        {shelf.name}
      </h2>

      {/* Button grid */}
      <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 gap-3">
        {shelf.buttons.map((button) => (
          <ToolButton
            key={button.id}
            button={button}
            onLaunch={onLaunch}
            onHover={onHover}
            onContextMenu={onContextMenu}
          />
        ))}
      </div>
    </div>
  )
}
