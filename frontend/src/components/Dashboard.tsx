import { useEffect, useState } from 'react'
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
  WifiOff
} from 'lucide-react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import { cn, formatPrice, formatRelativeTime } from '../lib/utils'
import { toast } from './ui/Toast'
import { useWebSocket } from '../hooks/useWebSocket'

function StatCard({ 
  title, 
  value, 
  subtitle, 
  icon: Icon, 
  trend,
  color = 'moss',
  loading = false
}: { 
  title: string
  value: string | number
  subtitle?: string
  icon: any
  trend?: number
  color?: 'moss' | 'green' | 'yellow' | 'red' | 'moss'
  loading?: boolean
}) {
  const colorClasses = {
    moss: 'group-hover:shadow-moss-500/20',
    green: 'group-hover:shadow-moss-500/20',
    yellow: 'group-hover:shadow-amber-500/20',
    red: 'group-hover:shadow-rose-500/20',
    moss: 'group-hover:shadow-[var(--info)]/20',
  }
  
  const iconBgColors = {
    moss: 'bg-moss-500/10 text-moss-400 group-hover:bg-moss-500/20',
    green: 'bg-[var(--primary)]/10 text-[var(--primary)] group-hover:bg-[var(--primary)]/10',
    yellow: 'bg-amber-500/10 text-amber-400 group-hover:bg-amber-500/20',
    red: 'bg-rose-500/10 text-rose-400 group-hover:bg-rose-500/20',
    moss: 'bg-[var(--info)]/10 text-[var(--info)] group-hover:bg-[var(--info)]/10',
  }

  const accentColors = {
    moss: 'bg-moss-500',
    green: 'bg-[var(--primary)]',
    yellow: 'bg-amber-500',
    red: 'bg-rose-500',
    moss: 'bg-[var(--info)]',
  }
  
  return (
    <div className={cn(
      "group relative p-5 rounded-xl bg-[var(--surface2)] border border-[var(--border)] overflow-hidden",
      "transition-all duration-300 hover:border-[var(--border)] hover:shadow-xl",
      colorClasses[color]
    )}>
      <div className={cn("absolute top-0 left-0 w-full h-0.5", accentColors[color], "opacity-50")} />
      
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-[var(--muted)]">{title}</p>
          {loading ? (
            <div className="h-9 w-20 skeleton" />
          ) : (
            <p className="text-3xl font-bold text-[var(--text)] tracking-tight">{value.toLocaleString()}</p>
          )}
          {subtitle && <p className="text-xs text-[var(--muted)]">{subtitle}</p>}
        </div>
        <div className={cn(
          "p-3 rounded-xl transition-colors duration-300",
          iconBgColors[color]
        )}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      
      {trend !== undefined && (
        <div className={cn(
          "flex items-center gap-1.5 mt-4 text-xs font-medium",
          trend >= 0 ? "text-[var(--primary)]" : "text-rose-400"
        )}>
          <TrendingUp className={cn("w-3.5 h-3.5", trend < 0 && "rotate-180")} />
          <span>{trend >= 0 ? '+' : ''}{trend}% from last hour</span>
        </div>
      )}
    </div>
  )
}

function LiveFeed() {
  const { events } = useStore()
  const recentEvents = events.slice(0, 6)
  
  return (
    <div className="bg-[var(--surface2)] rounded-xl border border-[var(--border)] overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
        <h3 className="font-semibold text-[var(--text)] flex items-center gap-2">
          <Activity className="w-4 h-4 text-[var(--info)]" />
          Live Product Feed
        </h3>
        <div className="flex items-center gap-2 px-2 py-1 bg-[var(--primary)]/10 rounded-full">
          <div className="w-1.5 h-1.5 bg-moss-400 rounded-full animate-pulse" />
          <span className="text-xs font-medium text-[var(--primary)]">Live</span>
        </div>
      </div>
      
      <div className="p-4 space-y-2 max-h-[400px] overflow-y-auto">
        {recentEvents.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-[var(--surface2)] flex items-center justify-center">
              <Zap className="w-6 h-6 text-[var(--muted)]" />
            </div>
            <p className="text-sm font-medium text-[var(--muted)]">No products detected yet</p>
            <p className="text-xs text-[var(--muted)] mt-1">Start monitors to see live updates</p>
          </div>
        ) : (
          recentEvents.map((event, i) => (
            <div 
              key={event.id || i}
              className={cn(
                "p-3 rounded-lg border transition-all duration-200 animate-fade-in-up hover:bg-[var(--surface2)]",
                event.priority === 'high' 
                  ? "bg-[var(--primary)]/10 border-moss-500/20" 
                  : "bg-[var(--surface2)] border-[var(--border)]"
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className={cn(
                      "badge",
                      event.priority === 'high' ? "badge-green" : "badge-moss"
                    )}>
                      {event.store}
                    </span>
                    {event.matched && (
                      <span className="badge badge-yellow">Matched</span>
                    )}
                  </div>
                  <p className="text-sm text-[var(--text)] font-medium truncate">{event.product}</p>
                  <div className="flex items-center gap-2 mt-1.5 text-xs text-[var(--muted)]">
                    <span className="font-medium text-[var(--muted)]">{formatPrice(event.price)}</span>
                    <span className="text-[var(--muted)]">•</span>
                    <span>{event.sizes?.slice(0, 3).join(', ')}{event.sizes?.length > 3 ? '...' : ''}</span>
                    <span className="text-[var(--muted)]">•</span>
                    <span>{formatRelativeTime(event.timestamp)}</span>
                  </div>
                </div>
                {event.profit && (
                  <div className="text-right shrink-0">
                    <p className={cn(
                      "text-sm font-bold",
                      event.profit >= 100 ? "text-[var(--primary)]" : event.profit >= 30 ? "text-amber-400" : "text-[var(--muted)]"
                    )}>
                      +{formatPrice(event.profit)}
                    </p>
                    <p className="text-xs text-[var(--muted)]">profit</p>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function StoreHealth() {
  const { shopifyStores } = useStore()
  const stores = Object.entries(shopifyStores).slice(0, 8)
  
  return (
    <div className="bg-[var(--surface2)] rounded-xl border border-[var(--border)] overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
        <h3 className="font-semibold text-[var(--text)] flex items-center gap-2">
          <Target className="w-4 h-4 text-moss-400" />
          Store Health
        </h3>
        <span className="text-xs text-[var(--muted)]">{stores.length} stores</span>
      </div>
      
      <div className="p-4 space-y-2 max-h-[400px] overflow-y-auto">
        {stores.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-[var(--surface2)] flex items-center justify-center">
              <Target className="w-6 h-6 text-[var(--muted)]" />
            </div>
            <p className="text-sm font-medium text-[var(--muted)]">No stores configured</p>
            <p className="text-xs text-[var(--muted)] mt-1">Add stores in the Monitors tab</p>
          </div>
        ) : (
          stores.map(([id, store]) => (
            <div 
              key={id} 
              className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface2)] border border-[var(--border)] hover:border-[var(--border)] transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className={cn(
                  "status-dot",
                  (store.errorCount ?? 0) === 0 ? "online" : (store.errorCount ?? 0) < 3 ? "warning" : "offline"
                )} />
                <div>
                  <span className="text-sm font-medium text-[var(--text)]">{store.name}</span>
                  <p className="text-xs text-[var(--muted)]">
                    {store.lastCheck ? formatRelativeTime(store.lastCheck) : 'Not checked'}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-[var(--text)]">{(store.productsFound ?? 0).toLocaleString()}</p>
                <p className="text-xs text-[var(--muted)]">products</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export function Dashboard() {
  const { 
    isRunning, 
    setRunning, 
    monitorsRunning, 
    setMonitorsRunning,
    stats,
    setStats,
    setShopifyStores,
    isConnected
  } = useStore()
  
  // Initialize WebSocket connection for real-time updates
  useWebSocket()
  
  const [loading, setLoading] = useState(false)
  
  const toggleEngine = async () => {
    setLoading(true)
    try {
      if (isRunning) {
        await api.stopEngine()
        setRunning(false)
        toast.info('Engine Stopped', 'Bot engine has been stopped')
      } else {
        await api.startEngine()
        setRunning(true)
        toast.success('Engine Started', 'Bot engine is now running')
      }
    } catch (e) {
      console.error(e)
      toast.error('Error', 'Failed to toggle engine')
    }
    setLoading(false)
  }
  
  const toggleMonitors = async () => {
    setLoading(true)
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
    } catch (e) {
      console.error(e)
      toast.error('Error', 'Failed to toggle monitors')
    }
    setLoading(false)
  }
  
  // Poll for status only (events come via WebSocket now)
  // Reduced frequency since WebSocket handles real-time updates
  useEffect(() => {
    const pollStatus = async () => {
      try {
        const status = await api.getMonitorStatus()
        if (status.running !== undefined) {
          setMonitorsRunning(status.running)
        }
        if (status.total_products_found !== undefined) {
          setStats({ totalProductsFound: status.total_products_found })
        }
        if (status.high_priority_found !== undefined) {
          setStats({ highPriorityFound: status.high_priority_found })
        }
        if (status.shopify?.stores) {
          setShopifyStores(status.shopify.stores)
        }
      } catch {}
    }
    
    pollStatus()
    // Poll less frequently - WebSocket handles real-time events
    const interval = setInterval(pollStatus, 15000)
    return () => clearInterval(interval)
  }, [])
  
  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)] tracking-tight flex items-center gap-3">
            Command Center
            {isConnected ? (
              <span className="flex items-center gap-1.5 px-2 py-1 text-xs bg-[var(--primary)]/10 text-[var(--primary)] rounded-full">
                <Wifi className="w-3 h-3" />
                Live
              </span>
            ) : (
              <span className="flex items-center gap-1.5 px-2 py-1 text-xs bg-amber-500/10 text-amber-400 rounded-full">
                <WifiOff className="w-3 h-3" />
                Connecting...
              </span>
            )}
          </h1>
          <p className="text-[var(--muted)] text-sm mt-1">Real-time monitoring and control</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={toggleMonitors}
            disabled={loading}
            aria-label={monitorsRunning ? 'Stop Monitors' : 'Start Monitors'}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-all duration-200",
              monitorsRunning
                ? "bg-[var(--info)]/10 text-[var(--info)] border border-[var(--info)]/30 hover:bg-[var(--info)]/10"
                : "bg-[var(--surface2)] text-[var(--muted)] border border-[var(--border)] hover:border-[var(--info)]/30 hover:text-[var(--info)]"
            )}
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : monitorsRunning ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {monitorsRunning ? 'Stop Monitors' : 'Start Monitors'}
          </button>
          
          <button
            onClick={toggleEngine}
            disabled={loading}
            aria-label={isRunning ? 'Stop Engine' : 'Start Engine'}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-all duration-200",
              isRunning
                ? "bg-[var(--primary)]/10 text-[var(--primary)] border border-moss-500/30 hover:bg-[var(--primary)]/10"
                : "btn-primary"
            )}
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : isRunning ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            {isRunning ? 'Stop Engine' : 'Start Engine'}
          </button>
        </div>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Products Found"
          value={stats.totalProductsFound}
          subtitle="Total detections"
          icon={ShoppingBag}
          color="moss"
        />
        <StatCard
          title="High Priority"
          value={stats.highPriorityFound}
          subtitle="Profitable items"
          icon={TrendingUp}
          color="green"
        />
        <StatCard
          title="Checkouts"
          value={stats.checkouts}
          subtitle="Successful orders"
          icon={DollarSign}
          color="moss"
        />
        <StatCard
          title="Declines"
          value={stats.declines}
          subtitle="Failed attempts"
          icon={AlertTriangle}
          color="red"
        />
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LiveFeed />
        <StoreHealth />
      </div>
    </div>
  )
}
