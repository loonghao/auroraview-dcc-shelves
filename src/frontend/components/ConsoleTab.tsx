import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Terminal, Filter, X, Send, AlertCircle, Info, AlertTriangle, Bug, Cpu, HardDrive, Activity } from 'lucide-react'
import { useSystemMetrics } from '../hooks/useSystemMetrics'

export type LogLevel = 'info' | 'warn' | 'error' | 'debug' | 'log'
export type LogSource = 'console' | 'backend' | 'system'

export interface LogEntry {
  id: string
  timestamp: Date
  level: LogLevel
  source: LogSource
  message: string
  details?: string
}

export interface CommandDefinition {
  name: string
  description: string
  usage?: string
}

interface ConsoleTabProps {
  onExecuteCommand?: (command: string) => void
  /** Available commands for autocomplete */
  availableCommands?: CommandDefinition[]
}

const LOG_LEVEL_STYLES: Record<LogLevel, { icon: React.ReactNode; color: string }> = {
  info: { icon: <Info size={10} />, color: 'text-blue-400' },
  warn: { icon: <AlertTriangle size={10} />, color: 'text-amber-400' },
  error: { icon: <AlertCircle size={10} />, color: 'text-red-400' },
  debug: { icon: <Bug size={10} />, color: 'text-purple-400' },
  log: { icon: <Terminal size={10} />, color: 'text-white/60' },
}

const getUsageColor = (value: number): string => {
  if (value >= 90) return 'text-red-400'
  if (value >= 70) return 'text-amber-400'
  if (value >= 50) return 'text-yellow-400'
  return 'text-emerald-400'
}

// Default built-in commands
const DEFAULT_COMMANDS: CommandDefinition[] = [
  { name: 'clear', description: 'Clear console logs', usage: 'clear' },
  { name: 'help', description: 'Show available commands', usage: 'help' },
  { name: 'reload', description: 'Reload the application', usage: 'reload' },
  { name: 'version', description: 'Show version info', usage: 'version' },
]

export const ConsoleTab: React.FC<ConsoleTabProps> = ({
  onExecuteCommand,
  availableCommands = DEFAULT_COMMANDS
}) => {
  const { t } = useTranslation()
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filter, setFilter] = useState<LogLevel | 'all'>('all')
  const [command, setCommand] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const autocompleteRef = useRef<HTMLDivElement>(null)
  const { metrics } = useSystemMetrics(3000)

  // Filter commands based on input
  const filteredCommands = useMemo(() => {
    if (!command.trim()) return availableCommands
    const lowerCmd = command.toLowerCase()
    return availableCommands.filter(cmd =>
      cmd.name.toLowerCase().startsWith(lowerCmd) ||
      cmd.description.toLowerCase().includes(lowerCmd)
    )
  }, [command, availableCommands])

  useEffect(() => {
    const originalConsole = { log: console.log, info: console.info, warn: console.warn, error: console.error, debug: console.debug }
    const createInterceptor = (level: LogLevel) => (...args: unknown[]) => {
      originalConsole[level](...args)
      const message = args.map(arg => typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)).join(' ')
      addLog({ level, source: 'console', message })
    }
    console.log = createInterceptor('log')
    console.info = createInterceptor('info')
    console.warn = createInterceptor('warn')
    console.error = createInterceptor('error')
    console.debug = createInterceptor('debug')
    return () => { Object.assign(console, originalConsole) }
  }, [])

  const addLog = useCallback((entry: Omit<LogEntry, 'id' | 'timestamp'>) => {
    setLogs(prev => [...prev.slice(-200), { ...entry, id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, timestamp: new Date() }])
  }, [])

  useEffect(() => { logsEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [logs])
  useEffect(() => { inputRef.current?.focus() }, [])

  // Reset selected index when filtered commands change
  useEffect(() => { setSelectedIndex(0) }, [filteredCommands])

  // Close autocomplete when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (autocompleteRef.current && !autocompleteRef.current.contains(e.target as Node)) {
        setShowAutocomplete(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleExecuteCommand = useCallback(() => {
    if (!command.trim()) return

    // Handle built-in commands
    const cmd = command.trim().toLowerCase()
    if (cmd === 'clear') {
      setLogs([])
      setCommand('')
      setShowAutocomplete(false)
      return
    }
    if (cmd === 'help') {
      addLog({ level: 'info', source: 'system', message: '📋 Available commands:' })
      availableCommands.forEach(c => {
        addLog({ level: 'log', source: 'system', message: `  ${c.name} - ${c.description}` })
      })
      setCommand('')
      setShowAutocomplete(false)
      return
    }

    addLog({ level: 'info', source: 'system', message: `> ${command}` })
    onExecuteCommand?.(command)
    setCommand('')
    setShowAutocomplete(false)
  }, [command, addLog, onExecuteCommand, availableCommands])

  const handleSelectCommand = useCallback((cmd: CommandDefinition) => {
    setCommand(cmd.name)
    setShowAutocomplete(false)
    inputRef.current?.focus()
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!showAutocomplete) {
      if (e.key === 'Enter') handleExecuteCommand()
      else if (e.key === 'ArrowDown' || e.key === 'Tab') {
        e.preventDefault()
        setShowAutocomplete(true)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(i => Math.min(i + 1, filteredCommands.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(i => Math.max(i - 1, 0))
        break
      case 'Enter':
      case 'Tab':
        e.preventDefault()
        if (filteredCommands[selectedIndex]) {
          handleSelectCommand(filteredCommands[selectedIndex])
        }
        break
      case 'Escape':
        setShowAutocomplete(false)
        break
    }
  }, [showAutocomplete, handleExecuteCommand, filteredCommands, selectedIndex, handleSelectCommand])

  const filteredLogs = logs.filter(log => filter === 'all' || log.level === filter)
  const formatTime = (date: Date) => date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const errorCount = logs.filter(l => l.level === 'error').length
  const warnCount = logs.filter(l => l.level === 'warn').length

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Compact Toolbar */}
      <div className="shrink-0 flex items-center justify-between px-2 py-1 border-b border-white/[0.04]">
        <div className="flex items-center gap-1.5">
          {errorCount > 0 && <span className="flex items-center gap-0.5 px-1 py-px bg-red-500/15 text-red-400 rounded text-[8px]"><AlertCircle size={8} />{errorCount}</span>}
          {warnCount > 0 && <span className="flex items-center gap-0.5 px-1 py-px bg-amber-500/15 text-amber-400 rounded text-[8px]"><AlertTriangle size={8} />{warnCount}</span>}
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-[8px] font-mono">
            <span className={`flex items-center gap-0.5 ${getUsageColor(metrics.cpu)}`} title={t('console.metrics.cpu')}><Cpu size={8} /><span>{metrics.cpu}%</span></span>
            <span className={`flex items-center gap-0.5 ${getUsageColor(metrics.memory)}`} title={t('console.metrics.memory')}><Activity size={8} /><span>{metrics.memory}%</span></span>
            {metrics.disk !== undefined && <span className={`flex items-center gap-0.5 ${getUsageColor(metrics.disk)}`} title={t('console.metrics.disk')}><HardDrive size={8} /><span>{metrics.disk}%</span></span>}
          </div>
          <div className="w-px h-2.5 bg-white/[0.06]" />
          <button onClick={() => setShowFilters(!showFilters)} className={`p-0.5 rounded transition-colors ${showFilters ? 'bg-white/[0.08] text-white/60' : 'text-white/30 hover:text-white/50'}`}><Filter size={9} /></button>
          <button onClick={() => setLogs([])} className="p-0.5 text-white/30 hover:text-white/50 rounded transition-colors"><X size={9} /></button>
        </div>
      </div>

      {/* Filter bar - More compact */}
      {showFilters && (
        <div className="shrink-0 flex items-center gap-0.5 px-2 py-1 border-b border-white/[0.04] animate-fade-in">
          {(['all', 'info', 'warn', 'error', 'debug'] as const).map(level => (
            <button key={level} onClick={() => setFilter(level)} className={`px-1.5 py-px rounded text-[8px] transition-colors ${filter === level ? 'bg-white/[0.1] text-white/80' : 'text-white/35 hover:text-white/50'}`}>{t(`console.filters.${level}`)}</button>
          ))}
        </div>
      )}

      {/* Logs List - Compact */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-2 py-1 font-mono text-[9px]">
        {filteredLogs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-white/25 text-[9px]">{t('console.noLogs')}</div>
        ) : (
          filteredLogs.map(log => (
            <div key={log.id} className="flex items-start gap-1.5 py-0.5 hover:bg-white/[0.03] rounded px-1 -mx-1">
              <span className="text-white/25 shrink-0">{formatTime(log.timestamp)}</span>
              <span className={`shrink-0 ${LOG_LEVEL_STYLES[log.level].color}`}>{LOG_LEVEL_STYLES[log.level].icon}</span>
              <span className={`text-white/70 break-all ${log.level === 'error' ? 'text-red-300' : ''}`}>{log.message}</span>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>

      {/* Command Input with Autocomplete - Compact */}
      <div className="shrink-0 relative border-t border-white/[0.04]" ref={autocompleteRef}>
        {/* Autocomplete Dropdown */}
        {showAutocomplete && filteredCommands.length > 0 && (
          <div className="absolute bottom-full left-0 right-0 mb-0 max-h-[100px] overflow-y-auto bg-[#151518] border border-white/[0.08] rounded-t shadow-xl z-50">
            {filteredCommands.map((cmd, index) => (
              <button
                key={cmd.name}
                onClick={() => handleSelectCommand(cmd)}
                className={`w-full px-2 py-1 flex items-center justify-between text-left transition-colors ${
                  index === selectedIndex ? 'bg-emerald-500/15 text-white' : 'hover:bg-white/[0.04] text-white/60'
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span className="font-mono text-[9px] text-emerald-400/80">{cmd.name}</span>
                  <span className="text-[8px] text-white/35">{cmd.description}</span>
                </div>
                {cmd.usage && (
                  <span className="text-[8px] text-white/25 font-mono">{cmd.usage}</span>
                )}
              </button>
            ))}
          </div>
        )}

        {/* Input Row - Compact */}
        <div className="flex items-center gap-1.5 px-2 py-1">
          <span className="text-white/30 text-[9px]">&gt;</span>
          <input
            ref={inputRef}
            type="text"
            value={command}
            onChange={(e) => { setCommand(e.target.value); setShowAutocomplete(true) }}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowAutocomplete(true)}
            placeholder={t('console.enterCommand')}
            className="flex-1 bg-transparent text-white/80 text-[9px] font-mono placeholder:text-white/25 focus:outline-none"
          />
          <span className="text-[7px] text-white/15">Tab</span>
          <button onClick={handleExecuteCommand} disabled={!command.trim()} className="p-0.5 text-white/30 hover:text-white/60 disabled:opacity-30 transition-colors"><Send size={10} /></button>
        </div>
      </div>
    </div>
  )
}
