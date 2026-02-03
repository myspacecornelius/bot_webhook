/**
 * Query Hooks for Phantom Bot
 * Smart polling with visibility awareness and cleanup
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { api, ApiRequestError } from '../api/client'
import type { EngineStatus, MonitorStatus, CheckoutAnalytics, MonitorEventsResponse } from '../api/types'

// ============ Polling Configuration ============

interface PollingConfig {
    /** Interval when page is visible (ms) */
    activeInterval: number
    /** Interval when page is hidden (ms) */
    hiddenInterval: number
    /** Stop polling when engine is stopped */
    stopWhenEngineOff?: boolean
}

// ============ Generic Polling Hook ============

interface UsePollingResult<T> {
    data: T | null
    error: ApiRequestError | null
    isLoading: boolean
    lastUpdated: number | null
    refetch: () => Promise<void>
}

function usePolling<T>(
    fetcher: (signal: AbortSignal) => Promise<T>,
    config: PollingConfig,
    enabled: boolean = true
): UsePollingResult<T> {
    const [data, setData] = useState<T | null>(null)
    const [error, setError] = useState<ApiRequestError | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [lastUpdated, setLastUpdated] = useState<number | null>(null)

    const abortControllerRef = useRef<AbortController | null>(null)
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

    const fetch = useCallback(async () => {
        // Cancel previous request
        abortControllerRef.current?.abort()
        abortControllerRef.current = new AbortController()

        try {
            const result = await fetcher(abortControllerRef.current.signal)
            setData(result)
            setError(null)
            setLastUpdated(Date.now())
        } catch (e) {
            if (e instanceof Error && e.name === 'AbortError') {
                return // Ignore abort errors
            }
            setError(e instanceof ApiRequestError ? e : new ApiRequestError({
                code: 'UNKNOWN',
                message: e instanceof Error ? e.message : 'Unknown error',
                retryable: true,
            }))
        } finally {
            setIsLoading(false)
        }
    }, [fetcher])

    // Setup polling with visibility awareness
    useEffect(() => {
        if (!enabled) {
            setIsLoading(false)
            return
        }

        const scheduleInterval = () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }

            const interval = document.hidden
                ? config.hiddenInterval
                : config.activeInterval

            intervalRef.current = setInterval(fetch, interval)
        }

        const handleVisibilityChange = () => {
            scheduleInterval()
            // Immediately fetch when becoming visible
            if (!document.hidden) {
                fetch()
            }
        }

        // Initial fetch
        fetch()
        scheduleInterval()

        document.addEventListener('visibilitychange', handleVisibilityChange)

        return () => {
            abortControllerRef.current?.abort()
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
            document.removeEventListener('visibilitychange', handleVisibilityChange)
        }
    }, [fetch, enabled, config.activeInterval, config.hiddenInterval])

    return {
        data,
        error,
        isLoading,
        lastUpdated,
        refetch: fetch,
    }
}

// ============ Specific Hooks ============

/**
 * Engine status polling hook
 * Polls every 5s when visible, 15s when hidden
 */
export function useEngineStatus() {
    return usePolling<EngineStatus>(
        (signal) => api.getStatus(signal),
        { activeInterval: 5000, hiddenInterval: 15000 }
    )
}

/**
 * Monitor status polling hook
 * Polls every 3s when visible, 10s when hidden
 * Stops when engine is off
 */
export function useMonitorStatus(engineRunning: boolean = true) {
    return usePolling<MonitorStatus>(
        (signal) => api.getMonitorStatus(signal),
        { activeInterval: 3000, hiddenInterval: 10000 },
        engineRunning
    )
}

/**
 * Checkout analytics polling hook
 * Polls every 10s when visible, 30s when hidden
 */
export function useCheckoutAnalytics(enabled: boolean = true) {
    return usePolling<CheckoutAnalytics>(
        (signal) => api.getCheckoutAnalytics(signal),
        { activeInterval: 10000, hiddenInterval: 30000 },
        enabled
    )
}

/**
 * Monitor events polling hook (fallback when WebSocket disconnected)
 * Polls every 2s when visible
 */
export function useMonitorEvents(enabled: boolean = true, limit: number = 50) {
    return usePolling<MonitorEventsResponse>(
        (signal) => api.getMonitorEvents(limit, signal),
        { activeInterval: 2000, hiddenInterval: 10000 },
        enabled
    )
}

// ============ Action Hooks ============

interface UseActionResult<T> {
    execute: () => Promise<T | null>
    isLoading: boolean
    error: ApiRequestError | null
    reset: () => void
}

export function useAction<T>(
    action: () => Promise<T>
): UseActionResult<T> {
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<ApiRequestError | null>(null)

    const execute = useCallback(async () => {
        setIsLoading(true)
        setError(null)

        try {
            const result = await action()
            return result
        } catch (e) {
            const apiError = e instanceof ApiRequestError
                ? e
                : new ApiRequestError({
                    code: 'UNKNOWN',
                    message: e instanceof Error ? e.message : 'Unknown error',
                    retryable: false,
                })
            setError(apiError)
            return null
        } finally {
            setIsLoading(false)
        }
    }, [action])

    const reset = useCallback(() => {
        setError(null)
    }, [])

    return { execute, isLoading, error, reset }
}

// ============ Convenience Hooks ============

export function useStartEngine() {
    return useAction(() => api.startEngine())
}

export function useStopEngine() {
    return useAction(() => api.stopEngine())
}

export function useStartMonitors() {
    return useAction(async () => {
        await api.setupShopify()
        return api.startMonitors()
    })
}

export function useStopMonitors() {
    return useAction(() => api.stopMonitors())
}

// ============ Time Formatting ============

export function formatTimeAgo(timestamp: number | null): string {
    if (!timestamp) return 'Never'

    const seconds = Math.floor((Date.now() - timestamp) / 1000)

    if (seconds < 5) return 'Just now'
    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
}

/**
 * Hook to get live "Updated Xs ago" string
 */
export function useTimeAgo(timestamp: number | null): string {
    const [timeAgo, setTimeAgo] = useState(() => formatTimeAgo(timestamp))

    useEffect(() => {
        if (!timestamp) return

        const update = () => setTimeAgo(formatTimeAgo(timestamp))
        update()

        const interval = setInterval(update, 1000)
        return () => clearInterval(interval)
    }, [timestamp])

    return timeAgo
}
