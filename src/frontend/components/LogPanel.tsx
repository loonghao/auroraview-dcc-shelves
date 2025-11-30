import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Terminal, ChevronUp, ChevronDown, Filter, X, Send, AlertCircle, Info, AlertTriangle, Bug, Cpu, HardDrive, Activity } from 'lucide-react'
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

interface LogPanelProps {
  isExpanded: boolean
  onToggle: () => void
  onExecuteCommand?: (command: string) => void
}

const LOG_LEVEL_STYLES: Record<LogLevel, { icon: React.ReactNode; color: string }> = {
  info: { icon: <Info size={12} />, color: 'text-blue-400' },
  warn: { icon: <AlertTriangle size={12} />, color: 'text-amber-400' },
  error: { icon: <AlertCircle size={12} />, color: 'text-red-400' },
  debug: { icon: <Bug size={12} />, color: 'text-purple-400' },
  log: { icon: <Terminal size={12} />, color: 'text-white/60' },
}

// Get color based on usage percentage
const getUsageColor = (value: number): string => {
  if (value >= 90) return 'text-red-400'
  if (value >= 70) return 'text-amber-400'
  if (value >= 50) return 'text-yellow-400'
  return 'text-emerald-400'
}

export const LogPanel: React.FC<LogPanelProps> = ({ isExpanded, onToggle, onExecuteCommand }) => {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filter, setFilter] = useState<LogLevel | 'all'>('all')
  const [command, setCommand] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Get system metrics from AuroraView backend (or fallback to simulation)
  const { metrics } = useSystemMetrics(3000)

  // Intercept console methods
  useEffect(() => {
    const originalConsole = {
      log: console.log,
      info: console.info,
      warn: console.warn,
      error: console.error,
      debug: console.debug,
    }

    const createInterceptor = (level: LogLevel) => (...args: unknown[]) => {
      originalConsole[level](...args)
      const message = args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
      ).join(' ')
      
      addLog({ level, source: 'console', message })
    }

    console.log = createInterceptor('log')
    console.info = createInterceptor('info')
    console.warn = createInterceptor('warn')
    console.error = createInterceptor('error')
    console.debug = createInterceptor('debug')

    return () => {
      console.log = originalConsole.log
      console.info = originalConsole.info
      console.warn = originalConsole.warn
      console.error = originalConsole.error
      console.debug = originalConsole.debug
    }
  }, [])

  const addLog = useCallback((entry: Omit<LogEntry, 'id' | 'timestamp'>) => {
    setLogs(prev => [...prev.slice(-200), {
      ...entry,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    }])
  }, [])


  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (isExpanded && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, isExpanded])

  // Focus input when expanded
  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isExpanded])

  const handleExecuteCommand = () => {
    if (!command.trim()) return
    addLog({ level: 'info', source: 'system', message: `> ${command}` })
    onExecuteCommand?.(command)
    setCommand('')
  }

  const filteredLogs = logs.filter(log => {
    if (filter !== 'all' && log.level !== filter) return false
    return true
  })

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  const errorCount = logs.filter(l => l.level === 'error').length
  const warnCount = logs.filter(l => l.level === 'warn').length

  return (
    <div className="shrink-0 flex flex-col glass border-t border-white/10">
      {/* VSCode-style Header Bar - Always visible, clickable to toggle */}
      <button
        onClick={onToggle}
        className="shrink-0 flex items-center justify-between px-3 py-1.5
          hover:bg-white/5 transition-colors select-none"
      >
        <div className="flex items-center gap-2">
          {/* Collapse/Expand indicator */}
          <span className="text-white/40">
            {isExpanded ? <ChevronDown size={10} /> : <ChevronUp size={10} />}
          </span>
          {/* Title like VSCode "OUTLINE" */}
          <span className="text-[10px] font-semibold text-white/50 uppercase tracking-wider">
            Console
          </span>
          {/* Status badges */}
          {errorCount > 0 && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded text-[9px]">
              <AlertCircle size={9} />
              {errorCount}
            </span>
          )}
          {warnCount > 0 && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 bg-amber-500/20 text-amber-400 rounded text-[9px]">
              <AlertTriangle size={9} />
              {warnCount}
            </span>
          )}
        </div>
        {/* Right side - System metrics and actions */}
        <div className="flex items-center gap-3">
          {/* System Performance Metrics */}
          <div className="flex items-center gap-2 text-[9px] font-mono">
            {/* CPU */}
            <span className={`flex items-center gap-1 ${getUsageColor(metrics.cpu)}`} title="CPU Usage">
              <Cpu size={9} />
              <span>{metrics.cpu}%</span>
            </span>
            {/* Memory */}
            <span className={`flex items-center gap-1 ${getUsageColor(metrics.memory)}`} title="Memory Usage">
              <Activity size={9} />
              <span>{metrics.memory}%</span>
            </span>
            {/* Disk */}
            {metrics.disk !== undefined && (
              <span className={`flex items-center gap-1 ${getUsageColor(metrics.disk)}`} title="Disk Usage">
                <HardDrive size={9} />
                <span>{metrics.disk}%</span>
              </span>
            )}
          </div>

          {/* Divider */}
          <div className="w-px h-3 bg-white/10" />

          {/* Actions */}
          {isExpanded && (
            <>
              <span
                onClick={(e) => { e.stopPropagation(); setShowFilters(!showFilters) }}
                className={`p-1 rounded transition-colors cursor-pointer
                  ${showFilters ? 'bg-white/10 text-white/70' : 'text-white/40 hover:text-white/60'}`}
              >
                <Filter size={10} />
              </span>
              <span
                onClick={(e) => { e.stopPropagation(); setLogs([]) }}
                className="p-1 text-white/40 hover:text-white/60 rounded transition-colors cursor-pointer"
              >
                <X size={10} />
              </span>
            </>
          )}
        </div>
      </button>

      {/* Filter bar - only when expanded and filters shown */}
      {isExpanded && showFilters && (
        <div className="shrink-0 flex items-center gap-1 px-3 py-1.5 border-t border-white/5 animate-fade-in">
          {(['all', 'info', 'warn', 'error', 'debug'] as const).map(level => (
            <button
              key={level}
              onClick={() => setFilter(level)}
              className={`px-2 py-0.5 rounded text-[9px] transition-colors
                ${filter === level ? 'bg-white/15 text-white/90' : 'text-white/40 hover:text-white/60'}`}
            >
              {level}
            </button>
          ))}
        </div>
      )}

      {/* Expandable Content - Logs and Command Input */}
      {isExpanded && (
        <div
          className="flex flex-col overflow-hidden animate-slide-up"
          style={{ height: '200px' }}
        >
          {/* Logs List */}
          <div className="flex-1 overflow-y-auto custom-scrollbar px-3 py-2 font-mono text-[11px]">
            {filteredLogs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-white/30 text-[10px]">
                No logs to display
              </div>
            ) : (
              filteredLogs.map(log => (
                <div
                  key={log.id}
                  className="flex items-start gap-2 py-1 hover:bg-white/5 rounded px-1 -mx-1"
                >
                  <span className="text-white/30 shrink-0">{formatTime(log.timestamp)}</span>
                  <span className={`shrink-0 ${LOG_LEVEL_STYLES[log.level].color}`}>
                    {LOG_LEVEL_STYLES[log.level].icon}
                  </span>
                  <span className={`text-white/80 break-all ${log.level === 'error' ? 'text-red-300' : ''}`}>
                    {log.message}
                  </span>
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>

          {/* Command Input */}
          <div className="shrink-0 flex items-center gap-2 px-3 py-2 border-t border-white/5">
            <span className="text-white/40 text-[11px]">&gt;</span>
            <input
              ref={inputRef}
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleExecuteCommand()}
              placeholder="Enter command..."
              className="flex-1 bg-transparent text-white/90 text-[11px] font-mono
                placeholder:text-white/30 focus:outline-none"
            />
            <button
              onClick={handleExecuteCommand}
              disabled={!command.trim()}
              className="p-1 text-white/40 hover:text-white/70 disabled:opacity-30 transition-colors"
            >
              <Send size={12} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
