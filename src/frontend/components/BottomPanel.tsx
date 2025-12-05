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
    { id: 'detail' as const, label: t('bottomPanel.detail'), icon: <Info size={10} /> },
    { id: 'console' as const, label: t('bottomPanel.console'), icon: <Terminal size={10} /> },
  ]

  return (
    <div className="shrink-0 flex flex-col bg-black/40 border-t border-white/[0.06]">
      {/* Tab Header Bar - More compact, differentiated from top */}
      <div className="shrink-0 flex items-center justify-between px-1.5 h-6 bg-gradient-to-r from-white/[0.02] to-transparent">
        {/* Left: Tabs - Smaller, more subtle */}
        <div className="flex items-center gap-px">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`
                flex items-center gap-1 px-2 py-0.5 text-[9px] font-medium
                transition-all duration-150 select-none rounded-sm
                ${activeTab === tab.id
                  ? 'bg-white/[0.08] text-white/80'
                  : 'text-white/30 hover:text-white/50 hover:bg-white/[0.04]'
                }
              `}
            >
              <span className={activeTab === tab.id ? 'text-emerald-400/80' : 'opacity-60'}>{tab.icon}</span>
              <span className="uppercase tracking-wide">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Right: Collapse/Expand toggle */}
        <button
          onClick={onToggle}
          className="p-0.5 text-white/30 hover:text-white/50 hover:bg-white/[0.04] rounded-sm transition-colors"
          title={isExpanded ? t('common.collapse') : t('common.expand')}
        >
          {isExpanded ? <ChevronDown size={10} /> : <ChevronUp size={10} />}
        </button>
      </div>

      {/* Tab Content - Reduced height */}
      {isExpanded && (
        <div className="flex flex-col overflow-hidden animate-slide-up" style={{ height: '120px' }}>
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
