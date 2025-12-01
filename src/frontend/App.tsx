import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Search, X, Settings, LayoutGrid, Box, Filter, Minus, CheckCircle, XCircle } from 'lucide-react'
import type { ButtonConfig, ContextMenuState, LaunchResult, TabItem } from './types'
import { ALL_TOOLS_CATEGORY } from './types'

/** Generate a safe ID for DOM elements from category name */
const categoryToId = (category: string): string => {
  return `category-${category.replace(/\s+/g, '-').toLowerCase()}`
}
import { ToolButton } from './components/ToolButton'
import { ContextMenu } from './components/ContextMenu'
import { Banner } from './components/Banner'
import { BottomPanel, type BottomPanelTab } from './components/BottomPanel'
import { LanguageSwitcher } from './components/LanguageSwitcher'
import { useShelfIPC } from './hooks/useShelfIPC'

// Toast notification component
interface ToastProps {
  result: LaunchResult
  onClose: () => void
}

const Toast: React.FC<ToastProps> = ({ result, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000)
    return () => clearTimeout(timer)
  }, [onClose])

  return (
    <div
      className={`fixed bottom-20 right-3 z-50 flex items-center gap-2 px-3 py-2 rounded-xl shadow-2xl animate-slide-in backdrop-blur-xl ${
        result.success
          ? 'bg-emerald-500/20 border border-emerald-400/30 text-emerald-100'
          : 'bg-red-500/20 border border-red-400/30 text-red-100'
      }`}
    >
      {result.success ? (
        <CheckCircle size={14} className="text-emerald-400 shrink-0" />
      ) : (
        <XCircle size={14} className="text-red-400 shrink-0" />
      )}
      <span className="text-[11px] max-w-[200px] truncate font-medium">{result.message}</span>
      <button
        onClick={onClose}
        className="ml-1 p-1 hover:bg-white/10 rounded-lg transition-colors"
      >
        <X size={10} />
      </button>
    </div>
  )
}

export default function App() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<string>(ALL_TOOLS_CATEGORY)
  const [searchQuery, setSearchQuery] = useState('')
  const [toast, setToast] = useState<LaunchResult | null>(null)
  const [bottomPanelExpanded, setBottomPanelExpanded] = useState(true)
  const [bottomPanelTab, setBottomPanelTab] = useState<BottomPanelTab>('detail')

  // Ref for scroll container
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // Use IPC hook for Python communication
  const { tools, banner, currentHost, launchResult, launchTool, clearLaunchResult, isConnected } = useShelfIPC()

  // Interaction State
  const [hoveredTool, setHoveredTool] = useState<ButtonConfig | null>(null)
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    visible: false,
    x: 0,
    y: 0,
    button: null,
  })

  // Handle launch result from Python
  useEffect(() => {
    if (launchResult) {
      setToast(launchResult)
      clearLaunchResult()
    }
  }, [launchResult, clearLaunchResult])

  // Close toast
  const handleCloseToast = useCallback(() => {
    setToast(null)
  }, [])


  // Generate dynamic tabs from tool categories (preserve order from data)
  const { tabs, categoryOrder } = useMemo(() => {
    const orderedCategories: string[] = []
    const seen = new Set<string>()
    for (const tool of tools) {
      if (tool.category && !seen.has(tool.category)) {
        seen.add(tool.category)
        orderedCategories.push(tool.category)
      }
    }
    const dynamicTabs: TabItem[] = [{ id: ALL_TOOLS_CATEGORY, label: t('tools.allTools') }]
    for (const category of orderedCategories) {
      dynamicTabs.push({ id: category, label: category })
    }
    return { tabs: dynamicTabs, categoryOrder: orderedCategories }
  }, [tools, t])

  // Filter tools by search query only (waterfall shows all categories)
  const filteredTools = useMemo(() => {
    if (!searchQuery) return tools
    return tools.filter((tool) => {
      const matchesSearch =
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (tool.description?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false)
      return matchesSearch
    })
  }, [searchQuery, tools])

  // Group tools by category (always show all categories in waterfall)
  const groupedTools = useMemo<Record<string, ButtonConfig[]>>(() => {
    const groups: Record<string, ButtonConfig[]> = {}
    filteredTools.forEach((tool) => {
      const category = tool.category || 'Other'
      if (!groups[category]) groups[category] = []
      groups[category].push(tool)
    })
    return groups
  }, [filteredTools])

  // Handle tab click - scroll to category section
  const handleTabClick = useCallback((tabId: string) => {
    setActiveTab(tabId)
    if (tabId === ALL_TOOLS_CATEGORY) {
      // Scroll to top
      scrollContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      // Scroll to specific category
      const element = document.getElementById(categoryToId(tabId))
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
  }, [])

  // Update active tab based on scroll position
  const handleScroll = useCallback(() => {
    const container = scrollContainerRef.current
    if (!container || categoryOrder.length === 0) return

    const scrollTop = container.scrollTop
    const containerTop = container.getBoundingClientRect().top

    // Find the category section that's currently at the top of the viewport
    let currentCategory = ALL_TOOLS_CATEGORY
    for (const category of categoryOrder) {
      const element = document.getElementById(categoryToId(category))
      if (element) {
        const rect = element.getBoundingClientRect()
        // If the element's top is above or near the container top, it's the current section
        if (rect.top <= containerTop + 50) {
          currentCategory = category
        }
      }
    }

    // Only update if at the very top
    if (scrollTop < 10) {
      currentCategory = ALL_TOOLS_CATEGORY
    }

    setActiveTab(currentCategory)
  }, [categoryOrder])

  const handleToolLaunch = useCallback((tool: ButtonConfig) => {
    console.log(`Launching ${tool.name} (${tool.id})...`)
    launchTool(tool.id)
  }, [launchTool])

  const handleContextMenu = (e: React.MouseEvent, tool: ButtonConfig) => {
    e.preventDefault()
    setContextMenu({
      visible: true,
      x: e.clientX,
      y: e.clientY,
      button: tool,
    })
  }

  const handleContextMenuAction = (action: string, tool: ButtonConfig) => {
    setContextMenu({ ...contextMenu, visible: false })
    console.log(`Context menu action: ${action} on ${tool.name}`)
  }


  const handleExecuteCommand = useCallback((command: string) => {
    // Execute command through IPC or evaluate locally
    console.info(`Executing command: ${command}`)
    try {
      // eslint-disable-next-line no-eval
      const result = eval(command)
      if (result !== undefined) {
        console.log('Result:', result)
      }
    } catch (err) {
      console.error(`Command error: ${err}`)
    }
  }, [])

  return (
    <div className="flex flex-col h-screen apple-bg text-[#f5f5f7] font-sans selection:bg-blue-500/30 overflow-hidden w-full min-w-[280px] max-w-[480px]">
      {/* 1. TOP TITLE BAR (Window Controls) - Apple style, z-50 to keep above banner */}
      <div className="shrink-0 h-9 flex items-center justify-between px-3 glass select-none border-b border-white/5 relative z-50">
        <div className="flex items-center space-x-2 text-white/90">
          <Box size={13} className="text-blue-400" />
          <span className="font-semibold tracking-wide text-[11px]">{t('app.title')}</span>
        </div>
        <div className="flex items-center space-x-2 text-white/40">
          <LanguageSwitcher />
          <button className="hover:text-white/80 transition-colors p-1 rounded hover:bg-white/5"><Settings size={12} /></button>
          <button className="hover:text-white/80 transition-colors p-1 rounded hover:bg-white/5"><Minus size={12} /></button>
          <button className="hover:text-red-400 transition-colors p-1 rounded hover:bg-white/5"><X size={12} /></button>
        </div>
      </div>

      {/* 2. PROJECT BANNER - Enhanced with mesh pattern */}
      <Banner banner={banner} />

      {/* 3. MAIN CONTENT AREA */}
      <div
        className="flex-1 flex flex-col min-w-0 px-2.5 relative w-full overflow-hidden"
        onClick={() => setContextMenu({ ...contextMenu, visible: false })}
      >
        {/* HEADER CONTROLS */}
        <div className="shrink-0 pt-2 pb-2.5 space-y-2 z-10">
          {/* Search Bar Row - Apple style */}
          <div className="flex items-center space-x-2">
            <div className="relative flex-1 group">
              <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none">
                <Search className="h-3.5 w-3.5 text-white/30 group-focus-within:text-blue-400 transition-colors" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('tools.searchPlaceholder')}
                className="block w-full pl-8 pr-7 py-1.5 glass-subtle border border-white/10 rounded-lg text-[11px] text-white/90 placeholder-white/30 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all apple-inset"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute inset-y-0 right-0 pr-2 flex items-center text-white/30 hover:text-white/60 transition-colors"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
            <button className="p-1.5 glass-subtle border border-white/10 rounded-lg hover:border-white/20 text-white/40 hover:text-white/70 transition-all apple-btn">
              <Filter size={13} />
            </button>
          </div>

          {/* Filter Tabs (Apple Pill Style) - Click to scroll to category */}
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabClick(tab.id)}
                  className={`px-2.5 py-1 text-[10px] font-medium rounded-full transition-all duration-200 whitespace-nowrap flex items-center apple-btn ${
                    isActive
                      ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/25'
                      : 'bg-white/5 text-white/50 hover:bg-white/10 hover:text-white/70'
                  }`}
                >
                  {tab.label}
                </button>
              )
            })}
          </div>
        </div>


        {/* TOOL GRID - Waterfall layout */}
        <div
          ref={scrollContainerRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto pb-2 -mr-0.5 pr-0.5 custom-scrollbar"
        >
          {filteredTools.length === 0 && (
            <div className="flex flex-col items-center justify-center h-28 text-white/20">
              <LayoutGrid size={24} className="mb-2 opacity-40" />
              <p className="text-[11px]">{t('tools.noTools')}</p>
            </div>
          )}

          {/* Render categories in order */}
          {categoryOrder.map((category) => {
            const categoryTools = groupedTools[category]
            if (!categoryTools || categoryTools.length === 0) return null
            return (
              <div
                key={category}
                id={categoryToId(category)}
                className="mb-3 animate-fade-in scroll-mt-2"
              >
                <h2 className="text-[10px] font-semibold text-white/40 mb-2 pl-0.5 uppercase tracking-wider sticky top-0 bg-[#1a1a1f]/90 backdrop-blur-sm py-1 -mx-0.5 px-0.5 z-10">
                  {category}
                </h2>

                {/* Responsive grid: 5 cols default */}
                <div className="grid grid-cols-5 gap-2">
                  {categoryTools.map((tool) => (
                    <ToolButton
                      key={tool.id}
                      button={tool}
                      onLaunch={handleToolLaunch}
                      onHover={setHoveredTool}
                      onLeave={() => setHoveredTool(null)}
                      onContextMenu={handleContextMenu}
                    />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 4. BOTTOM PANEL - Combined Detail and Console tabs */}
      <BottomPanel
        isExpanded={bottomPanelExpanded}
        onToggle={() => setBottomPanelExpanded(!bottomPanelExpanded)}
        activeTab={bottomPanelTab}
        onTabChange={setBottomPanelTab}
        hoveredTool={hoveredTool}
        currentHost={currentHost}
        onExecuteCommand={handleExecuteCommand}
      />


      {/* Context Menu */}
      <ContextMenu
        state={contextMenu}
        onClose={() => setContextMenu({ ...contextMenu, visible: false })}
        onAction={handleContextMenuAction}
      />

      {/* Toast Notification */}
      {toast && <Toast result={toast} onClose={handleCloseToast} />}

      {/* Connection Status Indicator (dev mode only) */}
      {!isConnected && (
        <div className="fixed top-10 left-1/2 -translate-x-1/2 z-50 px-3 py-1 glass border border-amber-500/30 rounded-full text-[10px] text-amber-200/80">
          {t('app.devMode')}
        </div>
      )}
    </div>
  )
}
