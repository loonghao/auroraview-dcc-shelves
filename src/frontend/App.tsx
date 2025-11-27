import React, { useState, useMemo } from 'react'
import { Search, X, Settings, LayoutGrid, Box, ArrowUp, Filter, ChevronDown, Minus } from 'lucide-react'
import type { ButtonConfig, ContextMenuState } from './types'
import { ToolCategory } from './types'
import { TOOLS_DATA, TABS } from './data/mockData'
import { ToolButton } from './components/ToolButton'
import { ContextMenu } from './components/ContextMenu'
import { InfoFooter } from './components/InfoFooter'

export default function App() {
  const [activeTab, setActiveTab] = useState<ToolCategory>(ToolCategory.ALL)
  const [searchQuery, setSearchQuery] = useState('')

  // Interaction State
  const [hoveredTool, setHoveredTool] = useState<ButtonConfig | null>(null)
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    visible: false,
    x: 0,
    y: 0,
    button: null,
  })

  // Mock Project Data
  const currentProject = {
    name: 'League of Legends: Wild Rift',
    banner: 'https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=2670&auto=format&fit=crop&ixlib=rb-4.0.3',
  }

  const filteredTools = useMemo(() => {
    return TOOLS_DATA.filter((tool) => {
      const matchesTab = activeTab === ToolCategory.ALL || tool.category === activeTab
      const matchesSearch =
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesTab && matchesSearch
    })
  }, [activeTab, searchQuery])

  const groupedTools = useMemo<Record<string, ButtonConfig[]>>(() => {
    if (activeTab !== ToolCategory.ALL) {
      return { [activeTab]: filteredTools }
    }
    const groups: Record<string, ButtonConfig[]> = {}
    filteredTools.forEach((tool) => {
      if (!groups[tool.category]) groups[tool.category] = []
      groups[tool.category].push(tool)
    })
    return groups
  }, [activeTab, filteredTools])

  const handleToolLaunch = (tool: ButtonConfig) => {
    console.log(`Launching ${tool.name}...`)
  }

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

  return (
    <div className="flex flex-col h-screen bg-[#121212] text-gray-200 font-sans selection:bg-brand-500/30 overflow-hidden">
      {/* 1. TOP TITLE BAR (Window Controls) */}
      <div className="shrink-0 h-10 flex items-center justify-between px-4 bg-[#1a1a1a] select-none border-b border-[#2a2a2a]">
        <div className="flex items-center space-x-2 text-white/90">
          <Box size={16} className="text-brand-500" />
          <span className="font-bold tracking-wider text-sm">LIGHTBOX</span>
        </div>
        <div className="flex items-center space-x-3 text-gray-400">
          <button className="hover:text-white transition-colors"><Settings size={14} /></button>
          <button className="hover:text-white transition-colors"><ArrowUp size={14} /></button>
          <button className="hover:text-white transition-colors"><Minus size={14} /></button>
          <button className="hover:text-red-500 transition-colors"><X size={14} /></button>
        </div>
      </div>

      {/* 2. PROJECT BANNER */}
      <div className="shrink-0 h-32 w-full relative group overflow-hidden">
        <img
          src={currentProject.banner}
          alt="Project Banner"
          className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity duration-500"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#121212] via-transparent to-transparent" />
      </div>

      {/* 3. MAIN CONTENT AREA */}
      <div
        className="flex-1 flex flex-col min-w-0 px-4 relative max-w-5xl mx-auto w-full overflow-hidden"
        onClick={() => setContextMenu({ ...contextMenu, visible: false })}
      >
        {/* HEADER CONTROLS */}
        <div className="shrink-0 pt-2 pb-4 space-y-3 z-10 bg-[#121212]">
          {/* Project Selector */}
          <div className="flex items-center text-gray-200 hover:text-white cursor-pointer transition-colors w-fit">
            <span className="text-sm font-medium mr-1">{currentProject.name}</span>
            <ChevronDown size={14} />
          </div>

          {/* Search Bar Row */}
          <div className="flex items-center space-x-2">
            <div className="relative flex-1 group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-gray-500 group-focus-within:text-brand-500 transition-colors" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search..."
                className="block w-full pl-9 pr-8 py-2 bg-[#1e1e1e] border border-[#333] rounded text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/50 transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-gray-500 hover:text-gray-300"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
            <button className="p-2 bg-[#1e1e1e] border border-[#333] rounded hover:border-gray-500 text-gray-400 hover:text-white transition-colors">
              <Filter size={16} />
            </button>
          </div>

          {/* Filter Tabs (Pill Style) */}
          <div className="flex items-center space-x-2 overflow-x-auto scrollbar-hide pt-1 pb-1">
            {TABS.map((tab) => {
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3 py-1 text-xs font-medium rounded-sm border transition-all duration-200 whitespace-nowrap flex items-center
                    ${isActive
                      ? 'bg-brand-600 border-brand-500 text-white shadow-[0_0_10px_rgba(16,185,129,0.3)]'
                      : 'bg-transparent border-transparent text-gray-500 hover:text-gray-300 hover:bg-[#1e1e1e]'
                    }`}
                >
                  {tab.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* TOOL GRID */}
        <div className="flex-1 overflow-y-auto pb-4 -mr-2 pr-2 custom-scrollbar">
          {filteredTools.length === 0 && (
            <div className="flex flex-col items-center justify-center h-48 text-gray-600">
              <LayoutGrid size={32} className="mb-3 opacity-20" />
              <p className="text-sm">No tools found</p>
            </div>
          )}

          {Object.entries(groupedTools).map(([category, tools]) => (
            <div key={category} className="mb-6 animate-fade-in">
              <h2 className="text-xs font-bold text-gray-400 mb-3 pl-1 uppercase tracking-wider opacity-80">
                {category}
              </h2>

              <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 gap-4">
                {tools.map((tool) => (
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
          ))}
        </div>
      </div>

      {/* 4. FOOTER INFO BAR */}
      <InfoFooter button={hoveredTool} />

      {/* Context Menu */}
      <ContextMenu
        state={contextMenu}
        onClose={() => setContextMenu({ ...contextMenu, visible: false })}
        onAction={handleContextMenuAction}
      />
    </div>
  )
}

