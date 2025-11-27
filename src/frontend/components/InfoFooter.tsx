import React from 'react'
import type { ButtonConfig } from '../types'
import { BookOpen, FolderOpen, Database, User, Tag } from 'lucide-react'

interface InfoFooterProps {
  button: ButtonConfig | null
}

export const InfoFooter: React.FC<InfoFooterProps> = ({ button }) => {
  if (!button) {
    return (
      <div className="h-16 shrink-0 bg-[#151515] border-t border-[#2a2a2a] flex items-center px-6 text-xs text-gray-600 select-none">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-gray-700" />
          <span>Ready</span>
        </div>
      </div>
    )
  }

  return (
    <div className="shrink-0 bg-[#151515] border-t border-[#2a2a2a] px-6 py-3 animate-fade-in shadow-[0_-4px_20px_rgba(0,0,0,0.2)] z-20">
      {/* Row 1: Tool Info, Developer, Links */}
      <div className="flex items-center justify-between mb-2">
        {/* Left: Name, Version, Category */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-gray-100 font-bold text-sm tracking-wide">{button.name}</span>
            {button.version && (
              <span className="text-[10px] font-mono bg-[#252525] px-1.5 py-0.5 rounded text-brand-500 border border-brand-500/20">
                v{button.version}
              </span>
            )}
          </div>

          <div className="h-4 w-px bg-[#333]" />

          <div className="flex items-center space-x-1.5 text-xs text-gray-500">
            <Tag size={10} />
            <span className="uppercase tracking-wider">{button.category}</span>
          </div>

          {button.maintainer && (
            <>
              <div className="h-4 w-px bg-[#333]" />
              <div className="flex items-center space-x-1.5 text-xs text-gray-500" title="Maintainer">
                <User size={12} />
                <span className="hover:text-gray-300 transition-colors cursor-default">
                  {button.maintainer}
                </span>
              </div>
            </>
          )}
        </div>

        {/* Right: Links */}
        <div className="flex items-center space-x-1">
          <FooterLink icon={BookOpen} label="Wiki" />
          <FooterLink icon={FolderOpen} label="Docs" />
          <FooterLink icon={Database} label="Source" />
        </div>
      </div>

      {/* Row 2: Full Description */}
      <p className="text-gray-400 text-xs leading-relaxed">
        {button.description}
      </p>
    </div>
  )
}

interface FooterLinkProps {
  icon: React.ElementType
  label: string
  url?: string
}

const FooterLink: React.FC<FooterLinkProps> = ({ icon: Icon, label, url }) => {
  const hasUrl = !!url

  return (
    <a
      href={url || '#'}
      onClick={(e) => !hasUrl && e.preventDefault()}
      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded transition-all border border-transparent
        ${hasUrl
          ? 'hover:bg-[#222] text-gray-500 hover:text-brand-400 hover:border-[#333] cursor-pointer'
          : 'text-gray-700 cursor-not-allowed opacity-50'
        }`}
      title={hasUrl ? `Open ${label}` : 'Not available'}
    >
      <Icon size={12} />
      <span className="text-[10px] font-medium uppercase tracking-wider hidden sm:inline-block">
        {label}
      </span>
    </a>
  )
}

