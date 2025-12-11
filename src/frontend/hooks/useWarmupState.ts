/**
 * Hook for tracking WebView2 warmup state.
 *
 * This hook receives warmup progress events from the Python backend
 * and provides warmup state for UI display.
 */

import { useState, useEffect, useCallback } from 'react';

export interface WarmupStatus {
  initiated: boolean;
  complete: boolean;
  progress: number;
  stage: string;
  durationMs: number;
  error: string | null;
}

interface WarmupStateResult {
  /** Whether warmup has been initiated */
  isWarmingUp: boolean;
  /** Whether warmup is complete */
  isComplete: boolean;
  /** Warmup progress (0-100) */
  progress: number;
  /** Current warmup stage description */
  stage: string;
  /** Duration in milliseconds */
  durationMs: number;
  /** Error message if warmup failed */
  error: string | null;
}

/**
 * Hook to track WebView2 warmup state.
 *
 * @returns Warmup state object
 *
 * @example
 * ```tsx
 * const { isWarmingUp, progress, stage } = useWarmupState();
 *
 * if (isWarmingUp) {
 *   return <div>Initializing: {stage} ({progress}%)</div>;
 * }
 * ```
 */
export function useWarmupState(): WarmupStateResult {
  const [state, setState] = useState<WarmupStateResult>({
    isWarmingUp: false,
    isComplete: false,
    progress: 0,
    stage: '',
    durationMs: 0,
    error: null,
  });

  const handleWarmupEvent = useCallback((event: CustomEvent<WarmupStatus>) => {
    const data = event.detail;
    setState({
      isWarmingUp: data.initiated && !data.complete,
      isComplete: data.complete,
      progress: data.progress,
      stage: data.stage,
      durationMs: data.durationMs,
      error: data.error,
    });
  }, []);

  useEffect(() => {
    // Listen for warmup_state events from Python backend
    const handleEvent = (event: Event) => {
      handleWarmupEvent(event as CustomEvent<WarmupStatus>);
    };

    window.addEventListener('warmup_state', handleEvent);

    // Also check if auroraview API provides warmup status
    const checkAuroraViewStatus = () => {
      if (window.auroraview?.on) {
        window.auroraview.on('warmup_state', (data: unknown) => {
          const warmupData = data as WarmupStatus
          setState({
            isWarmingUp: warmupData.initiated && !warmupData.complete,
            isComplete: warmupData.complete,
            progress: warmupData.progress,
            stage: warmupData.stage,
            durationMs: warmupData.durationMs,
            error: warmupData.error,
          });
        });
      }
    };

    // Try immediately and also after a short delay
    checkAuroraViewStatus();
    const timer = setTimeout(checkAuroraViewStatus, 100);

    return () => {
      window.removeEventListener('warmup_state', handleEvent);
      clearTimeout(timer);
    };
  }, [handleWarmupEvent]);

  return state;
}

export default useWarmupState;
