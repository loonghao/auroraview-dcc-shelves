import React from 'react'
import { useTranslation } from 'react-i18next'
import { Info, Terminal, ChevronUp, ChevronDown } from 'lucide-react'
import type { ButtonConfig } from '../types'
import { DetailTab } from './DetailTab'
import { ConsoleTab } from './ConsoleTab'

export type BottomPanelTab = 'detail' | 'console'

interface BottomPanelProps {
  isExpanded: boolean
  onToggle: () => void
  activeTab: BottomPanelTab
  onTabChange: (tab: BottomPanelTab) => void
  // Detail tab props - hoveredTool persists until next hover (no clear on leave)
  hoveredTool: ButtonConfig | null
  currentHost?: string
  // Console tab props
  onExecuteCommand?: (command: string) => void
}

export const BottomPanel: React.FC<BottomPanelProps> = ({
  isExpanded,
  onToggle,
  activeTab,
  onTabChange,
  hoveredTool,
  currentHost = 'standalone',
  onExecuteCommand,
}) => {
  const { t } = useTranslation()

  const tabs = [
    { id: 'detail' as const, label: t('bottomPanel.detail'), icon: <Info size={12} /> },
    { id: 'console' as const, label: t('bottomPanel.console'), icon: <Terminal size={12} /> },
  ]

  return (
    <div className="shrink-0 flex flex-col glass border-t border-white/10">
      {/* Tab Header Bar */}
      <div className="shrink-0 flex items-center justify-between px-2 py-1 border-b border-white/5">
        {/* Left: Tabs */}
        <div className="flex items-center gap-0.5">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-t-md text-[10px] font-medium
                transition-all duration-200 select-none
                ${activeTab === tab.id
                  ? 'bg-white/10 text-white/90 border-b-2 border-blue-400'
                  : 'text-white/40 hover:text-white/60 hover:bg-white/5'
                }
              `}
            >
              <span className={activeTab === tab.id ? 'text-blue-400' : ''}>{tab.icon}</span>
              <span className="uppercase tracking-wider">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Right: Collapse/Expand toggle */}
        <button
          onClick={onToggle}
          className="p-1.5 text-white/40 hover:text-white/60 hover:bg-white/5 rounded transition-colors"
          title={isExpanded ? t('common.collapse') : t('common.expand')}
        >
          {isExpanded ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
        </button>
      </div>

      {/* Tab Content */}
      {isExpanded && (
        <div className="flex flex-col overflow-hidden animate-slide-up" style={{ height: '200px' }}>
          {activeTab === 'detail' && (
            <DetailTab button={hoveredTool} currentHost={currentHost} />
          )}
          {activeTab === 'console' && (
            <ConsoleTab onExecuteCommand={onExecuteCommand} />
          )}
        </div>
      )}
    </div>
  )
}
