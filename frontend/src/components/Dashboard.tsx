/**
 * Command Center Dashboard
 * Premium dark theme with real-time data and glassmorphism
 */

import { useState, useMemo } from 'react'
import {
  Play,
  Pause,
  Zap,
  TrendingUp,
  ShoppingBag,
  AlertTriangle,
  Activity,
  DollarSign,
  Target,
  Loader2,
  Wifi,
  WifiOff,
  RefreshCw,
  ExternalLink,
  Clock,
  Sparkles
} from 'lucide-react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import { cn, formatPrice, formatRelativeTime } from '../lib/utils'
import { toast } from './ui/Toast'
import { ConfirmModal } from './ui/ConfirmModal'
import { ProductDetailsDrawer } from './ui/ProductDetailsDrawer'
import { useWebSocket } from '../hooks/useWebSocket'
import {
  useEngineStatus,
  useMonitorStatus,
  useCheckoutAnalytics,
  useTimeAgo
} from '../hooks/useQueries'

// ============ Stat Card Component ============

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  tooltip?: string
  icon: React.ComponentType<{ className?: string }>
  trend?: number
  gradient: 'purple' | 'blue' | 'green' | 'red'
  loading?: boolean
  error?: boolean
  onRetry?: () => void
}

function StatCard({
  title,
  value,
  subtitle,
  tooltip,
  icon: Icon,
  trend,
  gradient,
  loading = false,
  error = false,
  onRetry,
}: StatCardProps) {
  const gradients = {
    purple: 'from-violet-500/20 to-purple-500/20 border-violet-500/30 hover:border-violet-500/50',
    blue: 'from-blue-500/20 to-cyan-500/20 border-blue-500/30 hover:border-blue-500/50',
    green: 'from-emerald-500/20 to-teal-500/20 border-emerald-500/30 hover:border-emerald-500/50',
    red: 'from-rose-500/20 to-pink-500/20 border-rose-500/30 hover:border-rose-500/50',
  }

  const iconColors = {
    purple: 'text-violet-400',
    blue: 'text-blue-400',
    green: 'text-emerald-400',
    red: 'text-rose-400',
  }

  const glowColors = {
    purple: 'group-hover:shadow-violet-500/20',
    blue: 'group-hover:shadow-blue-500/20',
    green: 'group-hover:shadow-emerald-500/20',
    red: 'group-hover:shadow-rose-500/20',
  }

  return (
    <div
      className={cn(
        "group relative p-6 rounded-2xl bg-gradient-to-br border backdrop-blur-xl overflow-hidden transition-all duration-300",
        gradients[gradient],
        glowColors[gradient],
        "hover:shadow-2xl hover:-translate-y-1"
      )}
      title={tooltip}
    >
      {/* Subtle glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      <div className="relative flex items-start justify-between">
        <div className="space-y-1.5 flex-1">
          <p className="text-sm font-medium text-zinc-400">{title}</p>

          {error ? (
            <div className="flex items-center gap-2 mt-2">
              <span className="text-sm text-rose-400">Failed to load</span>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="p-1.5 rounded-lg hover:bg-rose-500/20 text-rose-400 transition-colors"
                  aria-label="Retry"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ) : loading ? (
            <div className="h-10 w-24 skeleton mt-1" />
          ) : (
            <p className="text-4xl font-bold text-white tracking-tight">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
          )}

          {subtitle && !error && (
            <p className="text-xs text-zinc-500 mt-1">{subtitle}</p>
          )}
        </div>

        <div className={cn(
          "p-3.5 rounded-xl bg-white/5 border border-white/10 transition-all duration-300",
          "group-hover:bg-white/10 group-hover:scale-110",
          iconColors[gradient]
        )}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      {trend !== undefined && !loading && !error && (
        <div className={cn(
          "flex items-center gap-1.5 mt-5 text-xs font-medium",
          trend >= 0 ? "text-emerald-400" : "text-rose-400"
        )}>
          <TrendingUp className={cn("w-3.5 h-3.5", trend < 0 && "rotate-180")} />
          <span>{trend >= 0 ? '+' : ''}{trend}% from last hour</span>
        </div>
      )}
    </div>
  )
}

// ============ Live Feed Component ============

interface MonitorEvent {
  id?: string
  type: 'new_product' | 'restock' | 'price_drop'
  source: 'shopify' | 'footsite' | 'snkrs'
  store: string
  product: string
  url: string
  sizes: string[]
  price: number
  matched: string | null
  confidence: number
  priority: 'high' | 'medium' | 'low'
  profit?: number | null
  timestamp: string
  imageUrl?: string
}

function LiveFeed({ onSelectEvent }: { onSelectEvent: (event: MonitorEvent) => void }) {
  const { events, isConnected } = useStore()
  const recentEvents = useMemo(() => events.slice(0, 8), [events])

  return (
    <div className="bg-zinc-900/50 backdrop-blur-xl rounded-2xl border border-zinc-800 overflow-hidden">
      <div className="flex items-center justify-between p-5 border-b border-zinc-800">
        <h3 className="font-semibold text-white flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-violet-500/20">
            <Activity className="w-4 h-4 text-violet-400" />
          </div>
          Live Product Feed
        </h3>
        <div className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium",
          isConnected
            ? "bg-emerald-500/20 text-emerald-400"
            : "bg-amber-500/20 text-amber-400"
        )}>
          <div className={cn(
            "w-2 h-2 rounded-full",
            isConnected
              ? "bg-emerald-400 animate-pulse"
              : "bg-amber-400"
          )} />
          {isConnected ? 'Live' : 'Reconnecting...'}
        </div>
      </div>

      <div className="p-4 space-y-3 max-h-[420px] overflow-y-auto">
        {recentEvents.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-zinc-800/50 flex items-center justify-center">
              <Zap className="w-8 h-8 text-zinc-600" />
            </div>
            <p className="text-sm font-medium text-zinc-400">No products detected yet</p>
            <p className="text-xs text-zinc-600 mt-1.5">Start monitors to see live updates</p>
          </div>
        ) : (
          recentEvents.map((event, i) => (
            <button
              key={event.id || `event-${i}`}
              onClick={() => onSelectEvent(event as MonitorEvent)}
              className={cn(
                "w-full text-left p-4 rounded-xl border transition-all duration-200 cursor-pointer",
                event.priority === 'high'
                  ? "bg-emerald-500/10 border-emerald-500/30 hover:border-emerald-500/50"
                  : "bg-zinc-800/50 border-zinc-700/50 hover:border-zinc-600"
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className="badge badge-purple text-[10px]">
                      {event.store}
                    </span>
                    {event.matched && (
                      <span className="badge badge-yellow text-[10px]">Matched</span>
                    )}
                    {event.priority === 'high' && (
                      <span className="badge badge-green text-[10px]">
                        <Sparkles className="w-3 h-3 mr-1" />
                        High Priority
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-white font-medium truncate">{event.product}</p>
                  <div className="flex items-center gap-2.5 mt-2 text-xs text-zinc-500">
                    <span className="font-semibold text-white">{formatPrice(event.price)}</span>
                    <span className="text-zinc-600">•</span>
                    <span>{event.sizes?.slice(0, 3).join(', ')}{(event.sizes?.length ?? 0) > 3 ? '...' : ''}</span>
                    <span className="text-zinc-600">•</span>
                    <span>{formatRelativeTime(event.timestamp)}</span>
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2.5 shrink-0">
                  {event.profit && event.profit > 0 && (
                    <div className="text-right">
                      <p className={cn(
                        "text-sm font-bold",
                        event.profit >= 100 ? "text-emerald-400" : event.profit >= 30 ? "text-amber-400" : "text-zinc-400"
                      )}>
                        +{formatPrice(event.profit)}
                      </p>
                      <p className="text-[10px] text-zinc-600">profit</p>
                    </div>
                  )}

                  {event.url && (
                    <a
                      href={event.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-lg bg-zinc-800 hover:bg-violet-500/20 text-zinc-400 hover:text-violet-400 transition-colors"
                      aria-label="View product"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  )
}

// ============ Store Health Component ============

function StoreHealth() {
  const { data: monitorStatus, isLoading } = useMonitorStatus(true)

  const stores = useMemo(() => {
    if (!monitorStatus?.shopify?.stores) return []
    return Object.entries(monitorStatus.shopify.stores).slice(0, 8)
  }, [monitorStatus])

  return (
    <div className="bg-zinc-900/50 backdrop-blur-xl rounded-2xl border border-zinc-800 overflow-hidden">
      <div className="flex items-center justify-between p-5 border-b border-zinc-800">
        <h3 className="font-semibold text-white flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-emerald-500/20">
            <Target className="w-4 h-4 text-emerald-400" />
          </div>
          Store Health
        </h3>
        <span className="text-xs text-zinc-500">
          {isLoading ? '...' : `${stores.length} stores`}
        </span>
      </div>

      <div className="p-4 space-y-3 max-h-[420px] overflow-y-auto">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 skeleton" />
            ))}
          </div>
        ) : stores.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-zinc-800/50 flex items-center justify-center">
              <Target className="w-8 h-8 text-zinc-600" />
            </div>
            <p className="text-sm font-medium text-zinc-400">No stores configured</p>
            <p className="text-xs text-zinc-600 mt-1.5">Add stores in the Monitors tab</p>
          </div>
        ) : (
          stores.map(([id, store]) => (
            <div
              key={id}
              className="flex items-center justify-between p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50 hover:border-zinc-600 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className={cn(
                  "status-dot",
                  store.errors === 0 ? "online pulsing" : store.errors < 3 ? "warning" : "offline"
                )} />
                <div>
                  <span className="text-sm font-medium text-white">{store.name}</span>
                  <p className="text-xs text-zinc-500">
                    {store.last_check ? formatRelativeTime(store.last_check) : 'Not checked'}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-bold text-white">
                  {store.products_found?.toLocaleString() ?? 0}
                </p>
                <p className="text-xs text-zinc-500">products</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

// ============ Main Dashboard Component ============

export function Dashboard() {
  const {
    isRunning,
    setRunning,
    monitorsRunning,
    setMonitorsRunning,
    setStats,
    setShopifyStores,
    isConnected
  } = useStore()

  useWebSocket()

  const {
    data: engineStatus,
    lastUpdated: engineLastUpdated,
    refetch: refetchEngine
  } = useEngineStatus()

  const {
    data: monitorStatus,
    error: monitorError,
    isLoading: monitorLoading,
    refetch: refetchMonitors
  } = useMonitorStatus(isRunning)

  const {
    data: checkoutData,
    error: checkoutError,
    isLoading: checkoutLoading,
    refetch: refetchCheckouts
  } = useCheckoutAnalytics(isRunning)

  const lastUpdatedText = useTimeAgo(engineLastUpdated)

  const [showStopEngineModal, setShowStopEngineModal] = useState(false)
  const [engineActionLoading, setEngineActionLoading] = useState(false)
  const [monitorActionLoading, setMonitorActionLoading] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<MonitorEvent | null>(null)

  // Sync states
  if (engineStatus && engineStatus.running !== isRunning) {
    setRunning(engineStatus.running)
  }

  if (monitorStatus) {
    if (monitorStatus.running !== monitorsRunning) {
      setMonitorsRunning(monitorStatus.running)
    }
    setStats({
      totalProductsFound: monitorStatus.total_products_found,
      highPriorityFound: monitorStatus.high_priority_found,
      tasksCreated: monitorStatus.tasks_created,
    })
    if (monitorStatus.shopify?.stores) {
      const storeData: Record<string, any> = {}
      for (const [key, store] of Object.entries(monitorStatus.shopify.stores)) {
        storeData[key] = {
          name: store.name,
          url: store.url,
          productsFound: store.products_found,
          errorCount: store.errors,
          lastCheck: store.last_check,
        }
      }
      setShopifyStores(storeData)
    }
  }

  if (checkoutData) {
    setStats({
      checkouts: checkoutData.success,
      declines: checkoutData.failed,
    })
  }

  const handleEngineToggle = async () => {
    if (isRunning) {
      setShowStopEngineModal(true)
    } else {
      setEngineActionLoading(true)
      try {
        await api.startEngine()
        setRunning(true)
        toast.success('Engine Started', 'Bot engine is now running')
        refetchEngine()
      } catch (e) {
        console.error(e)
        toast.error('Error', 'Failed to start engine')
      }
      setEngineActionLoading(false)
    }
  }

  const confirmStopEngine = async () => {
    setEngineActionLoading(true)
    try {
      await api.stopEngine()
      setRunning(false)
      setShowStopEngineModal(false)
      toast.info('Engine Stopped', 'Bot engine has been stopped')
      refetchEngine()
    } catch (e) {
      console.error(e)
      toast.error('Error', 'Failed to stop engine')
    }
    setEngineActionLoading(false)
  }

  const handleMonitorsToggle = async () => {
    setMonitorActionLoading(true)
    try {
      if (monitorsRunning) {
        await api.stopMonitors()
        setMonitorsRunning(false)
        toast.info('Monitors Stopped', 'Product monitoring has been stopped')
      } else {
        await api.setupShopify()
        await api.startMonitors()
        setMonitorsRunning(true)
        toast.success('Monitors Started', 'Now monitoring for products')
      }
      refetchMonitors()
    } catch (e) {
      console.error(e)
      toast.error('Error', 'Failed to toggle monitors')
    }
    setMonitorActionLoading(false)
  }

  const totalProducts = monitorStatus?.total_products_found ?? 0
  const highPriority = monitorStatus?.high_priority_found ?? 0
  const checkouts = checkoutData?.success ?? 0
  const declines = checkoutData?.failed ?? 0

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-4">
            Command Center
            <div className={cn(
              "flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-full",
              isConnected
                ? "bg-emerald-500/20 text-emerald-400"
                : "bg-amber-500/20 text-amber-400"
            )}>
              {isConnected ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
              {isConnected ? 'Live' : 'Connecting...'}
            </div>
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <p className="text-zinc-400">Real-time monitoring and control</p>
            {engineLastUpdated && (
              <span className="flex items-center gap-1.5 text-xs text-zinc-500 px-2 py-1 rounded-full bg-zinc-800/50">
                <Clock className="w-3 h-3" />
                {lastUpdatedText}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleMonitorsToggle}
            disabled={monitorActionLoading || !isRunning}
            title={!isRunning ? 'Start engine first' : undefined}
            className={cn(
              "flex items-center gap-2 px-5 py-3 rounded-xl font-semibold transition-all duration-300",
              !isRunning && "opacity-40 cursor-not-allowed",
              monitorsRunning
                ? "bg-blue-500/20 text-blue-400 border border-blue-500/30 hover:bg-blue-500/30"
                : "bg-zinc-800 text-zinc-300 border border-zinc-700 hover:border-blue-500/50 hover:text-blue-400"
            )}
          >
            {monitorActionLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : monitorsRunning ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            {monitorsRunning ? 'Stop Monitors' : 'Start Monitors'}
          </button>

          <button
            onClick={handleEngineToggle}
            disabled={engineActionLoading}
            className={cn(
              "flex items-center gap-2 px-5 py-3 rounded-xl font-semibold transition-all duration-300",
              isRunning
                ? "bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:bg-rose-500/30"
                : "bg-gradient-to-r from-violet-500 to-purple-500 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 hover:-translate-y-0.5"
            )}
          >
            {engineActionLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : isRunning ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Zap className="w-5 h-5" />
            )}
            {isRunning ? 'Stop Engine' : 'Start Engine'}
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Products Found"
          value={totalProducts}
          subtitle="Total detections"
          tooltip="Total number of products detected by monitors since the last reset"
          icon={ShoppingBag}
          gradient="purple"
          loading={monitorLoading}
          error={!!monitorError}
          onRetry={refetchMonitors}
        />
        <StatCard
          title="High Priority"
          value={highPriority}
          subtitle="Profitable items"
          tooltip="Products that match your keywords and exceed profit thresholds"
          icon={TrendingUp}
          gradient="green"
          loading={monitorLoading}
          error={!!monitorError}
          onRetry={refetchMonitors}
        />
        <StatCard
          title="Checkouts"
          value={checkouts}
          subtitle="Successful orders"
          tooltip="Completed checkout attempts - orders placed successfully"
          icon={DollarSign}
          gradient="blue"
          loading={checkoutLoading}
          error={!!checkoutError}
          onRetry={refetchCheckouts}
        />
        <StatCard
          title="Declines"
          value={declines}
          subtitle="Failed attempts"
          tooltip="Failed checkout attempts due to out-of-stock, payment issues, or anti-bot detection"
          icon={AlertTriangle}
          gradient="red"
          loading={checkoutLoading}
          error={!!checkoutError}
          onRetry={refetchCheckouts}
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LiveFeed onSelectEvent={setSelectedEvent} />
        <StoreHealth />
      </div>

      {/* Stop Engine Modal */}
      <ConfirmModal
        isOpen={showStopEngineModal}
        onClose={() => setShowStopEngineModal(false)}
        onConfirm={confirmStopEngine}
        title="Stop Engine?"
        message="This will stop all running tasks and monitors. Any in-progress checkouts may be interrupted."
        confirmText="Stop Engine"
        cancelText="Keep Running"
        variant="danger"
        isLoading={engineActionLoading}
      />

      {/* Product Details Drawer */}
      <ProductDetailsDrawer
        isOpen={selectedEvent !== null}
        onClose={() => setSelectedEvent(null)}
        event={selectedEvent}
      />
    </div>
  )
}
