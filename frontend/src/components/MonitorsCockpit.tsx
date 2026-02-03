/**
 * MonitorsCockpit - Comprehensive Monitor Console
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Radio, Play, Pause, RefreshCw, Store, AlertTriangle,
  Clock, Gauge, Activity
} from 'lucide-react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import { cn } from '../lib/utils'
import { TooltipLabel } from './SmartTooltip'

interface DomainMetrics {
  domain: string
  requests_per_minute: number
  success_rate: number
  avg_latency_ms: number
  rate_limit_hits: number
  throttle_state: string
  backoff_remaining_ms: number
  last_error: string
}

interface RateLimitEvent {
  domain: string
  timestamp: number
  reason: string
  suggested_remedy: string
}

const THROTTLE_PRESETS = {
  conservative: { label: 'Conservative', delay: 5000, desc: 'Safest' },
  balanced: { label: 'Balanced', delay: 3000, desc: 'Default' },
  aggressive: { label: 'Aggressive', delay: 1500, desc: 'Fastest' }
}

export function MonitorsCockpit() {
  const { monitorsRunning, setMonitorsRunning } = useStore()
  const [loading, setLoading] = useState(false)
  const [rateLimitHealth, setRateLimitHealth] = useState<any>(null)
  const [rateLimitEvents, setRateLimitEvents] = useState<RateLimitEvent[]>([])
  const [throttlePreset, setThrottlePreset] = useState<keyof typeof THROTTLE_PRESETS>('balanced')
  const [globalConcurrency, setGlobalConcurrency] = useState(20)
  const [targetSizes, setTargetSizes] = useState('10, 10.5, 11, 11.5, 12')

  const fetchHealth = useCallback(async () => {
    try {
      const [health, events] = await Promise.all([
        api.get('/api/rate-limit/health'),
        api.get('/api/rate-limit/events?limit=10')
      ]) as [any, any]
      setRateLimitHealth(health)
      setRateLimitEvents(events.events || [])
    } catch (e) { console.error(e) }
  }, [])

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 5000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  const handleStart = async () => {
    setLoading(true)
    try {
      await api.post('/api/monitors/start')
      setMonitorsRunning(true)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const handleStop = async () => {
    setLoading(true)
    try {
      await api.post('/api/monitors/stop')
      setMonitorsRunning(false)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)] flex items-center gap-3">
            <Radio className="w-7 h-7 text-[var(--primary)]" />
            Monitor Cockpit
          </h1>
          <p className="text-[var(--muted)] text-sm mt-1">
            Configuration • Status • Rate Limits • Performance
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={monitorsRunning ? handleStop : handleStart}
            disabled={loading}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-all",
              monitorsRunning
                ? "bg-[var(--danger)]/20 text-[var(--danger)] border border-[var(--danger)]/30"
                : "bg-[var(--primary)] text-white"
            )}
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> :
              monitorsRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {monitorsRunning ? 'Stop All' : 'Start All'}
          </button>
        </div>
      </div>

      {/* Global Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Throttle Preset */}
        <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
          <TooltipLabel settingId="throttle_preset">Throttle Preset</TooltipLabel>
          <div className="flex gap-2 mt-2">
            {Object.entries(THROTTLE_PRESETS).map(([key, preset]) => (
              <button
                key={key}
                onClick={() => setThrottlePreset(key as keyof typeof THROTTLE_PRESETS)}
                className={cn(
                  "flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all border",
                  throttlePreset === key
                    ? "bg-[var(--primary)]/20 border-[var(--primary)]/50 text-[var(--primary)]"
                    : "bg-[var(--surface2)] border-transparent text-[var(--muted)] hover:text-[var(--text)]"
                )}
              >
                {preset.label}
              </button>
            ))}
          </div>
          <p className="text-xs text-[var(--muted)] mt-2">
            {THROTTLE_PRESETS[throttlePreset].desc} • {THROTTLE_PRESETS[throttlePreset].delay}ms delay
          </p>
        </div>

        {/* Global Concurrency */}
        <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
          <TooltipLabel settingId="global_concurrency">Global Concurrency</TooltipLabel>
          <div className="flex items-center gap-3 mt-2">
            <input
              type="range"
              min="5"
              max="50"
              value={globalConcurrency}
              onChange={(e) => setGlobalConcurrency(parseInt(e.target.value))}
              className="flex-1 accent-[var(--primary)]"
            />
            <span className="w-12 text-center font-mono text-[var(--text)]">{globalConcurrency}</span>
          </div>
          <p className="text-xs text-[var(--muted)] mt-2">
            Max simultaneous requests across all monitors
          </p>
        </div>

        {/* Target Sizes */}
        <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
          <TooltipLabel settingId="target_sizes">Target Sizes</TooltipLabel>
          <input
            type="text"
            value={targetSizes}
            onChange={(e) => setTargetSizes(e.target.value)}
            className="w-full mt-2 px-3 py-2 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] text-sm"
            placeholder="10, 10.5, 11"
          />
        </div>
      </div>

      {/* Rate Limit Health Panel */}
      <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-[var(--text)] flex items-center gap-2">
            <Activity className="w-5 h-5 text-[var(--primary)]" />
            Rate Limit Health
          </h2>
          <button onClick={fetchHealth} className="text-[var(--muted)] hover:text-[var(--text)]">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {rateLimitHealth ? (
          <div className="space-y-4">
            {/* Summary Stats */}
            <div className="grid grid-cols-4 gap-4">
              <StatCard label="Domains" value={rateLimitHealth.total_domains} />
              <StatCard label="Total Requests" value={rateLimitHealth.total_requests} />
              <StatCard label="429 Hits" value={rateLimitHealth.total_rate_limit_hits} color="danger" />
              <StatCard label="Backing Off" value={rateLimitHealth.domains_backing_off} color="warning" />
            </div>

            {/* Top Offenders */}
            {rateLimitHealth.top_offenders?.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-[var(--muted)] mb-2">Top Offenders</h3>
                <div className="space-y-2">
                  {rateLimitHealth.top_offenders.slice(0, 3).map((d: DomainMetrics) => (
                    <DomainRow key={d.domain} metrics={d} />
                  ))}
                </div>
              </div>
            )}

            {/* Recent Events */}
            {rateLimitEvents.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-[var(--muted)] mb-2">Recent Rate Limit Events</h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {rateLimitEvents.map((e, i) => (
                    <EventRow key={i} event={e} />
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-[var(--muted)]">
            <Gauge className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No rate limit data yet</p>
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number; color?: 'danger' | 'warning' }) {
  const colorClasses = {
    danger: 'text-[var(--danger)]',
    warning: 'text-[var(--warning)]',
  }
  return (
    <div className="p-3 rounded-lg bg-[var(--surface2)]">
      <p className="text-xs text-[var(--muted)]">{label}</p>
      <p className={cn("text-2xl font-bold", color ? colorClasses[color] : "text-[var(--text)]")}>
        {value}
      </p>
    </div>
  )
}

function DomainRow({ metrics }: { metrics: DomainMetrics }) {
  const stateColors: Record<string, string> = {
    normal: 'bg-green-500/20 text-green-400',
    cautious: 'bg-yellow-500/20 text-yellow-400',
    backing_off: 'bg-orange-500/20 text-orange-400',
    cooling_down: 'bg-red-500/20 text-red-400'
  }

  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface2)]">
      <div className="flex items-center gap-3">
        <Store className="w-4 h-4 text-[var(--muted)]" />
        <span className="font-medium text-[var(--text)]">{metrics.domain}</span>
        <span className={cn("px-2 py-0.5 rounded-full text-xs", stateColors[metrics.throttle_state] || stateColors.normal)}>
          {metrics.throttle_state}
        </span>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <span className="text-[var(--muted)]">{metrics.requests_per_minute} r/m</span>
        <span className="text-[var(--muted)]">{metrics.success_rate}%</span>
        <span className="text-[var(--danger)]">{metrics.rate_limit_hits} 429s</span>
        {metrics.backoff_remaining_ms > 0 && (
          <span className="text-[var(--warning)]">
            <Clock className="w-3 h-3 inline mr-1" />
            {Math.ceil(metrics.backoff_remaining_ms / 1000)}s
          </span>
        )}
      </div>
    </div>
  )
}

function EventRow({ event }: { event: RateLimitEvent }) {
  const timeAgo = Math.round((Date.now() / 1000 - event.timestamp) / 60)

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-[var(--danger)]/5 border border-[var(--danger)]/20">
      <AlertTriangle className="w-4 h-4 text-[var(--danger)] mt-0.5 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className="font-medium text-[var(--text)]">{event.domain}</span>
          <span className="text-xs text-[var(--muted)]">{timeAgo}m ago</span>
        </div>
        <p className="text-sm text-[var(--muted)] truncate">{event.reason}</p>
        <p className="text-xs text-[var(--primary)] mt-1">{event.suggested_remedy}</p>
      </div>
    </div>
  )
}
