/**
 * Settings Window Component
 * Standalone settings window that can run independently from the main app.
 */
import React, { useState, useCallback, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Settings,
  FolderSearch,
  Variable,
  Plus,
  Trash2,
  Save,
  RefreshCw,
  ChevronRight,
  AlertCircle,
  X,
} from 'lucide-react'

/** Configuration context levels */
export type ConfigContext = 'default' | 'system' | 'project' | 'user'

/** Search path entry */
export interface SearchPathEntry {
  path: string
  source: 'env' | 'manual'
  enabled: boolean
}

/** Environment variable entry */
export interface EnvVarEntry {
  key: string
  value: string
  source: 'system' | 'override'
  enabled: boolean
}

/** Settings data structure */
export interface SettingsData {
  searchPaths: SearchPathEntry[]
  envVars: EnvVarEntry[]
}

/** Tab button component */
const TabButton: React.FC<{
  active: boolean
  onClick: () => void
  children: React.ReactNode
}> = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 text-[12px] font-medium transition-all border-b-2 ${
      active
        ? 'text-[#14CF90] border-[#14CF90]'
        : 'text-white/50 border-transparent hover:text-white/70 hover:border-white/20'
    }`}
  >
    {children}
  </button>
)

/** Section tab button component */
const SectionTab: React.FC<{
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
}> = ({ active, onClick, icon, label }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-3 py-2.5 text-[12px] font-medium rounded-lg transition-all w-full text-left ${
      active
        ? 'bg-[#14CF90]/15 text-[#14CF90] border border-[#14CF90]/30'
        : 'text-white/60 hover:bg-white/5 hover:text-white/80'
    }`}
  >
    {icon}
    <span>{label}</span>
    <ChevronRight size={14} className={`ml-auto transition-transform ${active ? 'rotate-90' : ''}`} />
  </button>
)

export const SettingsWindow: React.FC = () => {
  const { t } = useTranslation()
  const [activeContext, setActiveContext] = useState<ConfigContext>('user')
  const [activeSection, setActiveSection] = useState<'paths' | 'env'>('paths')

  // Settings state for current context
  const [searchPaths, setSearchPaths] = useState<SearchPathEntry[]>([])
  const [envVars, setEnvVars] = useState<EnvVarEntry[]>([])
  const [newPath, setNewPath] = useState('')
  const [newEnvKey, setNewEnvKey] = useState('')
  const [newEnvValue, setNewEnvValue] = useState('')
  const [hasChanges, setHasChanges] = useState(false)

  // Load initial data when context changes
  useEffect(() => {
    // Default mock data for demonstration
    setSearchPaths([
      { path: 'C:/pipeline/shelves', source: 'env', enabled: true },
      { path: 'D:/projects/vfx/tools', source: 'env', enabled: true },
    ])
    setEnvVars([
      { key: 'DCC_SHELF_SEARCH_PATH', value: 'C:/pipeline/shelves;D:/projects/vfx/tools', source: 'system', enabled: true },
      { key: 'PYTHONPATH', value: 'C:/pipeline/python', source: 'system', enabled: true },
      { key: 'PATH', value: 'C:/Program Files/...', source: 'system', enabled: true },
    ])
    setHasChanges(false)
  }, [activeContext])

  const handleAddPath = useCallback(() => {
    if (newPath.trim()) {
      setSearchPaths(prev => [...prev, { path: newPath.trim(), source: 'manual', enabled: true }])
      setNewPath('')
      setHasChanges(true)
    }
  }, [newPath])

  const handleRemovePath = useCallback((index: number) => {
    setSearchPaths(prev => prev.filter((_, i) => i !== index))
    setHasChanges(true)
  }, [])

  const handleTogglePath = useCallback((index: number) => {
    setSearchPaths(prev => prev.map((p, i) => i === index ? { ...p, enabled: !p.enabled } : p))
    setHasChanges(true)
  }, [])

  const handleAddEnvVar = useCallback(() => {
    if (newEnvKey.trim()) {
      setEnvVars(prev => [...prev, { key: newEnvKey.trim(), value: newEnvValue, source: 'override', enabled: true }])
      setNewEnvKey('')
      setNewEnvValue('')
      setHasChanges(true)
    }
  }, [newEnvKey, newEnvValue])

  const handleRemoveEnvVar = useCallback((index: number) => {
    setEnvVars(prev => prev.filter((_, i) => i !== index))
    setHasChanges(true)
  }, [])

  const handleUpdateEnvVar = useCallback((index: number, value: string) => {
    setEnvVars(prev => prev.map((v, i) => i === index ? { ...v, value, source: 'override' as const } : v))
    setHasChanges(true)
  }, [])

  const handleSave = useCallback(() => {
    console.log('Saving settings:', { context: activeContext, searchPaths, envVars })
    // TODO: Send to backend via IPC
    setHasChanges(false)
  }, [activeContext, searchPaths, envVars])

  const handleRefresh = useCallback(() => {
    console.log('Refreshing shelves...')
    // TODO: Trigger shelf refresh via IPC
  }, [])

  const handleClose = useCallback(() => {
    window.close()
  }, [])

  const contexts: { id: ConfigContext; label: string }[] = [
    { id: 'default', label: t('settings.contexts.default') },
    { id: 'system', label: t('settings.contexts.system') },
    { id: 'project', label: t('settings.contexts.project') },
    { id: 'user', label: t('settings.contexts.user') },
  ]

  return (
    <div className="h-screen flex flex-col bg-gradient-to-b from-[#1d1d1f] to-[#0d0d0d]">
      {/* Title Bar (draggable area for native window) */}
      <div
        className="flex items-center justify-between px-4 py-3 border-b border-white/10 select-none"
        style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}
      >
        <div className="flex items-center gap-2">
          <Settings size={18} className="text-[#14CF90]" />
          <span className="text-[14px] font-semibold text-white/90">{t('settings.title')}</span>
        </div>
        <button
          onClick={handleClose}
          className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-white/40 hover:text-white/80"
          style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}
        >
          <X size={16} />
        </button>
      </div>

      {/* Context Tabs */}
      <div className="flex border-b border-white/10 px-3 bg-black/20">
        {contexts.map(ctx => (
          <TabButton
            key={ctx.id}
            active={activeContext === ctx.id}
            onClick={() => setActiveContext(ctx.id)}
          >
            {ctx.label}
          </TabButton>
        ))}
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Section Sidebar */}
        <div className="w-40 border-r border-white/10 p-3 space-y-1 bg-black/20">
          <SectionTab
            active={activeSection === 'paths'}
            onClick={() => setActiveSection('paths')}
            icon={<FolderSearch size={16} />}
            label={t('settings.searchPaths')}
          />
          <SectionTab
            active={activeSection === 'env'}
            onClick={() => setActiveSection('env')}
            icon={<Variable size={16} />}
            label={t('settings.envVars')}
          />
        </div>

        {/* Section Content */}
        <div className="flex-1 p-4 overflow-y-auto custom-scrollbar">
          {activeSection === 'paths' && (
            <div className="space-y-4">
              {/* Info banner */}
              <div className="flex items-start gap-2 px-3 py-2.5 bg-[#14CF90]/10 border border-[#14CF90]/20 rounded-lg">
                <AlertCircle size={16} className="text-[#14CF90] mt-0.5 shrink-0" />
                <p className="text-[11px] text-[#A1ECD3]">{t('settings.searchPathsInfo')}</p>
              </div>

              {/* Path list */}
              <div className="space-y-2">
                {searchPaths.map((entry, index) => (
                  <div
                    key={index}
                    className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border ${
                      entry.source === 'env'
                        ? 'bg-white/[0.02] border-white/5 text-white/40'
                        : 'bg-white/5 border-white/10 text-white/80'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={entry.enabled}
                      onChange={() => handleTogglePath(index)}
                      disabled={entry.source === 'env'}
                      className="w-4 h-4 rounded accent-[#14CF90]"
                    />
                    <span className="flex-1 text-[11px] truncate font-mono">{entry.path}</span>
                    {entry.source === 'env' && (
                      <span className="text-[10px] px-2 py-0.5 bg-white/5 rounded text-white/30">ENV</span>
                    )}
                    {entry.source === 'manual' && (
                      <button
                        onClick={() => handleRemovePath(index)}
                        className="p-1.5 hover:bg-red-500/20 rounded text-white/40 hover:text-red-400 transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {/* Add new path */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newPath}
                  onChange={e => setNewPath(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleAddPath()}
                  placeholder={t('settings.addPathPlaceholder')}
                  className="flex-1 px-3 py-2 text-[11px] bg-white/5 border border-white/10 rounded-lg text-white/80 placeholder-white/30 focus:outline-none focus:border-[#14CF90]/50"
                />
                <button
                  onClick={handleAddPath}
                  disabled={!newPath.trim()}
                  className="px-3 py-2 bg-[#14CF90]/20 border border-[#14CF90]/30 rounded-lg text-[#14CF90] hover:bg-[#14CF90]/30 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Plus size={16} />
                </button>
              </div>
            </div>
          )}

          {activeSection === 'env' && (
            <div className="space-y-4">
              {/* Info banner */}
              <div className="flex items-start gap-2 px-3 py-2.5 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <AlertCircle size={16} className="text-amber-400 mt-0.5 shrink-0" />
                <p className="text-[11px] text-amber-200/80">{t('settings.envVarsInfo')}</p>
              </div>

              {/* Env var list */}
              <div className="space-y-2">
                {envVars.map((entry, index) => (
                  <div
                    key={index}
                    className={`flex flex-col gap-1.5 px-3 py-2.5 rounded-lg border ${
                      entry.source === 'system'
                        ? 'bg-white/[0.02] border-white/5'
                        : 'bg-white/5 border-white/10'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`text-[11px] font-mono font-medium ${
                        entry.source === 'system' ? 'text-white/40' : 'text-[#14CF90]'
                      }`}>
                        {entry.key}
                      </span>
                      {entry.source === 'system' && (
                        <span className="text-[10px] px-2 py-0.5 bg-white/5 rounded text-white/30">SYS</span>
                      )}
                      {entry.source === 'override' && (
                        <button
                          onClick={() => handleRemoveEnvVar(index)}
                          className="ml-auto p-1.5 hover:bg-red-500/20 rounded text-white/40 hover:text-red-400 transition-colors"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                    {entry.source === 'system' ? (
                      <p className="text-[10px] text-white/30 font-mono truncate">{entry.value}</p>
                    ) : (
                      <input
                        type="text"
                        value={entry.value}
                        onChange={e => handleUpdateEnvVar(index, e.target.value)}
                        className="px-2 py-1.5 text-[10px] bg-white/5 border border-white/10 rounded text-white/80 font-mono focus:outline-none focus:border-[#14CF90]/50"
                      />
                    )}
                  </div>
                ))}
              </div>

              {/* Add new env var */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newEnvKey}
                  onChange={e => setNewEnvKey(e.target.value)}
                  placeholder={t('settings.envKeyPlaceholder')}
                  className="w-32 px-3 py-2 text-[11px] bg-white/5 border border-white/10 rounded-lg text-white/80 placeholder-white/30 focus:outline-none focus:border-[#14CF90]/50 font-mono"
                />
                <input
                  type="text"
                  value={newEnvValue}
                  onChange={e => setNewEnvValue(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleAddEnvVar()}
                  placeholder={t('settings.envValuePlaceholder')}
                  className="flex-1 px-3 py-2 text-[11px] bg-white/5 border border-white/10 rounded-lg text-white/80 placeholder-white/30 focus:outline-none focus:border-[#14CF90]/50 font-mono"
                />
                <button
                  onClick={handleAddEnvVar}
                  disabled={!newEnvKey.trim()}
                  className="px-3 py-2 bg-[#14CF90]/20 border border-[#14CF90]/30 rounded-lg text-[#14CF90] hover:bg-[#14CF90]/30 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Plus size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-white/10 bg-black/20">
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-3 py-2 text-[12px] text-white/60 hover:text-white/80 hover:bg-white/5 rounded-lg transition-colors"
        >
          <RefreshCw size={14} />
          {t('settings.refresh')}
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-[12px] text-white/60 hover:text-white/80 hover:bg-white/5 rounded-lg transition-colors"
          >
            {t('common.cancel')}
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges}
            className="flex items-center gap-2 px-4 py-2 text-[12px] bg-[#14CF90] text-[#04291D] font-medium rounded-lg hover:bg-[#10A673] active:bg-[#0C7C56] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Save size={14} />
            {t('common.save')}
          </button>
        </div>
      </div>
    </div>
  )
}

