import React, { useState, useCallback, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  X,
  Settings,
  FolderSearch,
  Variable,
  Plus,
  Trash2,
  Save,
  RefreshCw,
  ChevronRight,
  AlertCircle,
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

interface SettingsPanelProps {
  isOpen: boolean
  onClose: () => void
  onSave: (context: ConfigContext, data: SettingsData) => void
  onRefresh: () => void
  initialData?: Partial<Record<ConfigContext, SettingsData>>
}

/** Tab button component */
const TabButton: React.FC<{
  active: boolean
  onClick: () => void
  children: React.ReactNode
}> = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`px-3 py-1.5 text-[11px] font-medium transition-all border-b-2 ${
      active
        ? 'text-blue-400 border-blue-400'
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
    className={`flex items-center gap-2 px-3 py-2 text-[11px] font-medium rounded-lg transition-all w-full text-left ${
      active
        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
        : 'text-white/60 hover:bg-white/5 hover:text-white/80'
    }`}
  >
    {icon}
    <span>{label}</span>
    <ChevronRight size={12} className={`ml-auto transition-transform ${active ? 'rotate-90' : ''}`} />
  </button>
)

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  isOpen,
  onClose,
  onSave,
  onRefresh,
  initialData,
}) => {
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
    if (initialData?.[activeContext]) {
      setSearchPaths(initialData[activeContext]!.searchPaths || [])
      setEnvVars(initialData[activeContext]!.envVars || [])
    } else {
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
    }
    setHasChanges(false)
  }, [activeContext, initialData])

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
    onSave(activeContext, { searchPaths, envVars })
    setHasChanges(false)
  }, [activeContext, searchPaths, envVars, onSave])

  const handleRefresh = useCallback(() => {
    onRefresh()
  }, [onRefresh])

  if (!isOpen) return null

  const contexts: { id: ConfigContext; label: string }[] = [
    { id: 'default', label: t('settings.contexts.default') },
    { id: 'system', label: t('settings.contexts.system') },
    { id: 'project', label: t('settings.contexts.project') },
    { id: 'user', label: t('settings.contexts.user') },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-[420px] max-h-[85vh] bg-[#1a1a1f] border border-white/10 rounded-xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Settings size={16} className="text-blue-400" />
            <span className="text-[13px] font-semibold text-white/90">{t('settings.title')}</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-white/40 hover:text-white/80"
          >
            <X size={14} />
          </button>
        </div>

        {/* Context Tabs */}
        <div className="flex border-b border-white/10 px-2">
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
          <div className="w-32 border-r border-white/10 p-2 space-y-1 bg-black/20">
            <SectionTab
              active={activeSection === 'paths'}
              onClick={() => setActiveSection('paths')}
              icon={<FolderSearch size={14} />}
              label={t('settings.searchPaths')}
            />
            <SectionTab
              active={activeSection === 'env'}
              onClick={() => setActiveSection('env')}
              icon={<Variable size={14} />}
              label={t('settings.envVars')}
            />
          </div>

          {/* Section Content */}
          <div className="flex-1 p-3 overflow-y-auto custom-scrollbar">
            {activeSection === 'paths' && (
              <div className="space-y-3">
                {/* Info banner */}
                <div className="flex items-start gap-2 px-2.5 py-2 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <AlertCircle size={14} className="text-blue-400 mt-0.5 shrink-0" />
                  <p className="text-[10px] text-blue-200/80">{t('settings.searchPathsInfo')}</p>
                </div>

                {/* Path list */}
                <div className="space-y-1.5">
                  {searchPaths.map((entry, index) => (
                    <div
                      key={index}
                      className={`flex items-center gap-2 px-2.5 py-2 rounded-lg border ${
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
                        className="w-3 h-3 rounded accent-blue-500"
                      />
                      <span className="flex-1 text-[10px] truncate font-mono">{entry.path}</span>
                      {entry.source === 'env' && (
                        <span className="text-[9px] px-1.5 py-0.5 bg-white/5 rounded text-white/30">ENV</span>
                      )}
                      {entry.source === 'manual' && (
                        <button
                          onClick={() => handleRemovePath(index)}
                          className="p-1 hover:bg-red-500/20 rounded text-white/40 hover:text-red-400 transition-colors"
                        >
                          <Trash2 size={12} />
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
                    className="flex-1 px-2.5 py-1.5 text-[10px] bg-white/5 border border-white/10 rounded-lg text-white/80 placeholder-white/30 focus:outline-none focus:border-blue-500/50"
                  />
                  <button
                    onClick={handleAddPath}
                    disabled={!newPath.trim()}
                    className="px-2.5 py-1.5 bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-400 hover:bg-blue-500/30 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <Plus size={14} />
                  </button>
                </div>
              </div>
            )}

            {activeSection === 'env' && (
              <div className="space-y-3">
                {/* Info banner */}
                <div className="flex items-start gap-2 px-2.5 py-2 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                  <AlertCircle size={14} className="text-amber-400 mt-0.5 shrink-0" />
                  <p className="text-[10px] text-amber-200/80">{t('settings.envVarsInfo')}</p>
                </div>

                {/* Env var list */}
                <div className="space-y-1.5">
                  {envVars.map((entry, index) => (
                    <div
                      key={index}
                      className={`flex flex-col gap-1 px-2.5 py-2 rounded-lg border ${
                        entry.source === 'system'
                          ? 'bg-white/[0.02] border-white/5'
                          : 'bg-white/5 border-white/10'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-mono font-medium ${
                          entry.source === 'system' ? 'text-white/40' : 'text-blue-400'
                        }`}>
                          {entry.key}
                        </span>
                        {entry.source === 'system' && (
                          <span className="text-[9px] px-1.5 py-0.5 bg-white/5 rounded text-white/30">SYS</span>
                        )}
                        {entry.source === 'override' && (
                          <button
                            onClick={() => handleRemoveEnvVar(index)}
                            className="ml-auto p-1 hover:bg-red-500/20 rounded text-white/40 hover:text-red-400 transition-colors"
                          >
                            <Trash2 size={12} />
                          </button>
                        )}
                      </div>
                      {entry.source === 'system' ? (
                        <p className="text-[9px] text-white/30 font-mono truncate">{entry.value}</p>
                      ) : (
                        <input
                          type="text"
                          value={entry.value}
                          onChange={e => handleUpdateEnvVar(index, e.target.value)}
                          className="px-2 py-1 text-[9px] bg-white/5 border border-white/10 rounded text-white/80 font-mono focus:outline-none focus:border-blue-500/50"
                        />
                      )}
                    </div>
                  ))}
                </div>

                {/* Add new env var */}
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newEnvKey}
                      onChange={e => setNewEnvKey(e.target.value)}
                      placeholder={t('settings.envKeyPlaceholder')}
                      className="w-28 px-2.5 py-1.5 text-[10px] bg-white/5 border border-white/10 rounded-lg text-white/80 placeholder-white/30 focus:outline-none focus:border-blue-500/50 font-mono"
                    />
                    <input
                      type="text"
                      value={newEnvValue}
                      onChange={e => setNewEnvValue(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handleAddEnvVar()}
                      placeholder={t('settings.envValuePlaceholder')}
                      className="flex-1 px-2.5 py-1.5 text-[10px] bg-white/5 border border-white/10 rounded-lg text-white/80 placeholder-white/30 focus:outline-none focus:border-blue-500/50 font-mono"
                    />
                    <button
                      onClick={handleAddEnvVar}
                      disabled={!newEnvKey.trim()}
                      className="px-2.5 py-1.5 bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-400 hover:bg-blue-500/30 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <Plus size={14} />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-white/10 bg-black/20">
          <button
            onClick={handleRefresh}
            className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] text-white/60 hover:text-white/80 hover:bg-white/5 rounded-lg transition-colors"
          >
            <RefreshCw size={12} />
            {t('settings.refresh')}
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-[11px] text-white/60 hover:text-white/80 hover:bg-white/5 rounded-lg transition-colors"
            >
              {t('common.cancel')}
            </button>
            <button
              onClick={handleSave}
              disabled={!hasChanges}
              className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Save size={12} />
              {t('common.save')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
