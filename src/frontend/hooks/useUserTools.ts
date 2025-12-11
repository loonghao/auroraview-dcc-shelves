/**
 * Hook for managing user-created tools.
 * Uses Python backend API for persistent storage (saves to local YAML file).
 */

import { useState, useEffect, useCallback } from 'react'
import type { ButtonConfig, UserButtonConfig } from '../types'
import { ToolSource, ToolType } from '../types'

// Default user tools category
export const USER_TOOLS_CATEGORY = 'My Tools'
export const USER_TOOLS_CATEGORY_ZH = '我的工具'

/**
 * Call Python API method via auroraview bridge.
 * Uses the api object pattern from useShelfIPC.
 */
const callApi = async <T>(method: string, params?: Record<string, unknown>): Promise<T> => {
  const api = window.auroraview?.api as Record<string, ((params?: unknown) => Promise<unknown>) | undefined> | undefined
  if (!api) {
    throw new Error('AuroraView API not available')
  }
  const fn = api[method]
  if (!fn) {
    throw new Error(`API method not found: ${method}`)
  }
  const result = await fn(params)
  return result as T
}

/**
 * Convert API tool to ButtonConfig format.
 */
const toButtonConfig = (tool: Record<string, unknown>): ButtonConfig => {
  const rawToolType = (tool.toolType as string) || (tool.tool_type as string) || 'python'
  // Map string to ToolType enum
  const toolType = rawToolType === 'executable' ? ToolType.EXECUTABLE : ToolType.PYTHON

  return {
    id: tool.id as string,
    name: tool.name as string,
    name_zh: tool.name_zh as string | undefined,
    toolType,
    toolPath: (tool.toolPath as string) || (tool.tool_path as string) || '',
    icon: (tool.icon as string) || 'Wrench',
    args: (tool.args as string[]) || [],
    description: (tool.description as string) || '',
    description_zh: tool.description_zh as string | undefined,
    category: USER_TOOLS_CATEGORY,
    category_zh: USER_TOOLS_CATEGORY_ZH,
    hosts: tool.hosts as string[] | undefined,
    source: ToolSource.USER,
  }
}

export interface UseUserToolsReturn {
  /** All user-created tools */
  userTools: ButtonConfig[]
  /** Loading state */
  isLoading: boolean
  /** Error message if any */
  error: string | null
  /** Add a new user tool */
  addTool: (tool: Omit<UserButtonConfig, 'id'>) => Promise<ButtonConfig>
  /** Update an existing user tool */
  updateTool: (id: string, updates: Partial<UserButtonConfig>) => Promise<void>
  /** Delete a user tool */
  deleteTool: (id: string) => Promise<void>
  /** Export all user tools to JSON */
  exportTools: () => Promise<string>
  /** Import tools from JSON config */
  importTools: (jsonConfig: string, merge?: boolean) => Promise<number>
  /** Download tools as JSON file */
  downloadToolsAsFile: () => void
  /** Trigger file input for importing */
  triggerImportFile: () => void
}

export function useUserTools(): UseUserToolsReturn {
  const [userTools, setUserTools] = useState<ButtonConfig[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load user tools from Python backend
  useEffect(() => {
    let retryCount = 0
    const maxRetries = 50 // 5 seconds total (50 * 100ms)
    let isLoaded = false

    const loadTools = async () => {
      if (isLoaded) return // Prevent duplicate loads

      try {
        // Wait for auroraview API and specific method to be ready
        const api = window.auroraview?.api as Record<string, unknown> | undefined
        if (!api || typeof api.get_user_tools !== 'function') {
          retryCount++
          if (retryCount < maxRetries) {
            // Retry after a short delay
            setTimeout(loadTools, 100)
            return
          }
          // Give up after max retries
          console.warn('[UserTools] API not available after max retries')
          setIsLoading(false)
          return
        }

        const result = await callApi<{ success: boolean; tools: Record<string, unknown>[]; message?: string }>(
          'get_user_tools'
        )

        if (result.success) {
          isLoaded = true
          const tools = result.tools.map(toButtonConfig)
          setUserTools(tools)
          console.log(`[UserTools] Loaded ${tools.length} tools from backend`)
        } else {
          console.warn('[UserTools] Failed to load:', result.message)
          setError(result.message || 'Failed to load tools')
        }
      } catch (err) {
        console.error('[UserTools] Error loading tools:', err)
        setError(String(err))
      } finally {
        setIsLoading(false)
      }
    }

    // Listen for API ready event from Python backend
    const handleApiReady = () => {
      console.log('[UserTools] Received auroraview-api-ready event')
      loadTools()
    }
    window.addEventListener('auroraview-api-ready', handleApiReady)

    // Start initial load attempt
    loadTools()

    return () => {
      window.removeEventListener('auroraview-api-ready', handleApiReady)
    }
  }, [])

  /**
   * Add a new user tool via Python API.
   */
  const addTool = useCallback(async (tool: Omit<UserButtonConfig, 'id'>): Promise<ButtonConfig> => {
    try {
      const result = await callApi<{ success: boolean; tool: Record<string, unknown>; message?: string }>(
        'save_user_tool',
        {
          name: tool.name,
          toolType: tool.toolType,
          toolPath: tool.toolPath,
          icon: tool.icon || 'Wrench',
          name_zh: tool.name_zh || '',
          description: tool.description || '',
          description_zh: tool.description_zh || '',
          args: tool.args || [],
          hosts: tool.hosts || [],
        }
      )

      if (!result.success) {
        throw new Error(result.message || 'Failed to save tool')
      }

      const buttonConfig = toButtonConfig(result.tool)
      setUserTools((prev) => [...prev, buttonConfig])
      console.log(`[UserTools] Added tool: ${buttonConfig.name}`)
      return buttonConfig
    } catch (err) {
      console.error('[UserTools] Failed to add tool:', err)
      throw err
    }
  }, [])

  /**
   * Update an existing user tool via Python API.
   */
  const updateTool = useCallback(async (id: string, updates: Partial<UserButtonConfig>): Promise<void> => {
    try {
      // Find existing tool to merge updates
      const existingTool = userTools.find((t) => t.id === id)
      if (!existingTool) {
        throw new Error('Tool not found')
      }

      const result = await callApi<{ success: boolean; tool: Record<string, unknown>; message?: string }>(
        'save_user_tool',
        {
          id,
          name: updates.name ?? existingTool.name,
          toolType: updates.toolType ?? existingTool.toolType,
          toolPath: updates.toolPath ?? existingTool.toolPath,
          icon: updates.icon ?? existingTool.icon,
          name_zh: updates.name_zh ?? existingTool.name_zh ?? '',
          description: updates.description ?? existingTool.description ?? '',
          description_zh: updates.description_zh ?? existingTool.description_zh ?? '',
          args: updates.args ?? existingTool.args ?? [],
          hosts: updates.hosts ?? existingTool.hosts ?? [],
        }
      )

      if (!result.success) {
        throw new Error(result.message || 'Failed to update tool')
      }

      const updatedConfig = toButtonConfig(result.tool)
      setUserTools((prev) => prev.map((t) => (t.id === id ? updatedConfig : t)))
      console.log(`[UserTools] Updated tool: ${updatedConfig.name}`)
    } catch (err) {
      console.error('[UserTools] Failed to update tool:', err)
      throw err
    }
  }, [userTools])

  /**
   * Delete a user tool via Python API.
   */
  const deleteTool = useCallback(async (id: string): Promise<void> => {
    try {
      const result = await callApi<{ success: boolean; message?: string }>('delete_user_tool', { id })

      if (!result.success) {
        throw new Error(result.message || 'Failed to delete tool')
      }

      setUserTools((prev) => prev.filter((t) => t.id !== id))
      console.log(`[UserTools] Deleted tool: ${id}`)
    } catch (err) {
      console.error('[UserTools] Failed to delete tool:', err)
      throw err
    }
  }, [])

  /**
   * Export all user tools to JSON string via Python API.
   */
  const exportTools = useCallback(async (): Promise<string> => {
    try {
      const result = await callApi<{ success: boolean; config: string; message?: string }>('export_user_tools')

      if (!result.success) {
        throw new Error(result.message || 'Failed to export tools')
      }

      return result.config
    } catch (err) {
      console.error('[UserTools] Failed to export tools:', err)
      throw err
    }
  }, [])

  /**
   * Import tools from JSON config string via Python API.
   * @param merge If true, merge with existing tools. If false, replace all.
   * @returns Number of tools imported
   */
  const importTools = useCallback(async (jsonConfig: string, merge = true): Promise<number> => {
    try {
      const result = await callApi<{ success: boolean; count: number; message?: string }>(
        'import_user_tools',
        { config: jsonConfig, merge }
      )

      if (!result.success) {
        throw new Error(result.message || 'Failed to import tools')
      }

      // Reload tools from backend
      const reloadResult = await callApi<{ success: boolean; tools: Record<string, unknown>[] }>('get_user_tools')
      if (reloadResult.success) {
        setUserTools(reloadResult.tools.map(toButtonConfig))
      }

      console.log(`[UserTools] Imported ${result.count} tools`)
      return result.count
    } catch (err) {
      console.error('[UserTools] Failed to import tools:', err)
      throw err
    }
  }, [])

  /**
   * Download user tools as a JSON file.
   */
  const downloadToolsAsFile = useCallback(() => {
    exportTools().then((json) => {
      const blob = new Blob([json], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `dcc-shelves-user-tools-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    })
  }, [exportTools])

  /**
   * Trigger file input for importing tools.
   */
  const triggerImportFile = useCallback(() => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.json'
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return

      try {
        const text = await file.text()
        const count = await importTools(text, true)
        console.log(`[UserTools] Imported ${count} tools`)
      } catch (err) {
        console.error('[UserTools] Import failed:', err)
        setError(String(err))
      }
    }
    input.click()
  }, [importTools])

  return {
    userTools,
    isLoading,
    error,
    addTool,
    updateTool,
    deleteTool,
    exportTools,
    importTools,
    downloadToolsAsFile,
    triggerImportFile,
  }
}

