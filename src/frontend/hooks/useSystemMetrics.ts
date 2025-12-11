/**
 * Hook for fetching system metrics from AuroraView backend.
 * Falls back to simulated data in development mode.
 */

import { useState, useEffect, useCallback } from 'react'
import type { SystemMetrics } from './useShelfIPC'

export type { SystemMetrics }

// Check if AuroraView API is available
const hasAuroraView = () => !!window.auroraview?.api

export function useSystemMetrics(intervalMs: number = 3000) {
  const [metrics, setMetrics] = useState<SystemMetrics>({ cpu: 0, memory: 0 })
  const [isLoading, setIsLoading] = useState(true)

  const fetchMetrics = useCallback(async () => {
    // Try to get real metrics from AuroraView backend
    if (hasAuroraView() && window.auroraview?.api?.get_system_metrics) {
      try {
        const data = await window.auroraview.api.get_system_metrics()
        setMetrics(data)
        setIsLoading(false)
        return
      } catch (err) {
        console.debug('[SystemMetrics] Failed to fetch from backend:', err)
      }
    }

    // Fallback: Use browser Performance API for memory estimate
    const memory = (performance as Performance & {
      memory?: { usedJSHeapSize: number; jsHeapSizeLimit: number }
    }).memory

    const memoryUsage = memory
      ? Math.round((memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100)
      : Math.round(30 + Math.random() * 20)

    // Simulated CPU and disk (no reliable browser API for these)
    setMetrics({
      cpu: Math.round(15 + Math.random() * 35),
      memory: memoryUsage,
      disk: Math.round(40 + Math.random() * 25),
    })
    setIsLoading(false)
  }, [])

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, intervalMs)
    return () => clearInterval(interval)
  }, [fetchMetrics, intervalMs])

  return { metrics, isLoading, refetch: fetchMetrics }
}
