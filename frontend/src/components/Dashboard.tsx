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
  Clock
} from 'lucide-react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import { cn, formatPrice, formatRelativeTime } from '../lib/utils'

function StatCard({ 
  title, 
  value, 
  subtitle, 
  icon: Icon, 
  trend,
  color = 'purple'
}: { 
  title: string
  value: string | number
  subtitle?: string
  icon: any
  trend?: number
  color?: 'purple' | 'green' | 'yellow' | 'red' | 'cyan'
}) {
  const colorClasses = {
    purple: 'from-purple-500/20 to-violet-500/10 border-purple-500/30',
    green: 'from-green-500/20 to-emerald-500/10 border-green-500/30',
    yellow: 'from-yellow-500/20 to-amber-500/10 border-yellow-500/30',
    red: 'from-red-500/20 to-rose-500/10 border-red-500/30',
    cyan: 'from-cyan-500/20 to-blue-500/10 border-cyan-500/30',
  }
  
  const iconColors = {
    purple: 'text-purple-400',
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
    cyan: 'text-cyan-400',
  }
  
  return (
    <div className={cn(
      "relative p-5 rounded-xl border bg-gradient-to-br overflow-hidden",
      colorClasses[color]
    )}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400 mb-1">{title}</p>
          <p className="text-3xl font-bold text-white animate-count-up">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={cn("p-3 rounded-lg bg-black/30", iconColors[color])}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      {trend !== undefined && (
        <div className={cn(
          "flex items-center gap-1 mt-3 text-xs",
          trend >= 0 ? "text-green-400" : "text-red-400"
        )}>
          <TrendingUp className={cn("w-3 h-3", trend < 0 && "rotate-180")} />
          <span>{Math.abs(trend)}% from last hour</span>
        </div>
      )}
    </div>
  )
}

function LiveFeed() {
  const { events } = useStore()
  const recentEvents = events.slice(0, 5)
  
  return (
    <div className="bg-[#0f0f18] rounded-xl border border-[#1a1a2e] p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-cyan-400" />
          Live Product Feed
        </h3>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-xs text-gray-400">Live</span>
        </div>
      </div>
      
      <div className="space-y-3">
        {recentEvents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Zap className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No products detected yet</p>
            <p className="text-xs">Start monitors to see live updates</p>
          </div>
        ) : (
          recentEvents.map((event, i) => (
            <div 
              key={event.id || i}
              className={cn(
                "p-3 rounded-lg border transition-all animate-slide-in",
                event.priority === 'high' 
                  ? "bg-green-500/10 border-green-500/30" 
                  : "bg-[#1a1a24] border-[#2a2a3a]"
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={cn(
                      "px-2 py-0.5 text-xs rounded font-medium",
                      event.priority === 'high' 
                        ? "bg-green-500/20 text-green-400" 
                        : "bg-purple-500/20 text-purple-400"
                    )}>
                      {event.store}
                    </span>
                    {event.matched && (
                      <span className="px-2 py-0.5 text-xs bg-yellow-500/20 text-yellow-400 rounded">
                        Matched
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-white font-medium truncate">{event.product}</p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                    <span>{formatPrice(event.price)}</span>
                    <span>•</span>
                    <span>{event.sizes.slice(0, 3).join(', ')}{event.sizes.length > 3 ? '...' : ''}</span>
                    <span>•</span>
                    <span>{formatRelativeTime(event.timestamp)}</span>
                  </div>
                </div>
                {event.profit && (
                  <div className="text-right">
                    <p className={cn(
                      "text-sm font-bold",
                      event.profit >= 100 ? "text-green-400" : event.profit >= 30 ? "text-yellow-400" : "text-gray-400"
                    )}>
                      +{formatPrice(event.profit)}
                    </p>
                    <p className="text-xs text-gray-500">profit</p>
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
  const stores = Object.entries(shopifyStores).slice(0, 6)
  
  return (
    <div className="bg-[#0f0f18] rounded-xl border border-[#1a1a2e] p-5">
      <h3 className="font-semibold text-white flex items-center gap-2 mb-4">
        <Target className="w-5 h-5 text-purple-400" />
        Store Health
      </h3>
      
      <div className="space-y-3">
        {stores.length === 0 ? (
          <div className="text-center py-6 text-gray-500">
            <p className="text-sm">No stores configured</p>
          </div>
        ) : (
          stores.map(([id, store]) => (
            <div key={id} className="flex items-center justify-between p-2 rounded-lg bg-[#1a1a24]">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  store.errorCount === 0 ? "bg-green-500" : store.errorCount < 3 ? "bg-yellow-500" : "bg-red-500"
                )} />
                <span className="text-sm text-white">{store.name}</span>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>{store.productsFound} found</span>
                <span>{store.lastCheck ? formatRelativeTime(store.lastCheck) : 'Never'}</span>
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
    addEvent
  } = useStore()
  
  const [loading, setLoading] = useState(false)
  
  const toggleEngine = async () => {
    setLoading(true)
    try {
      if (isRunning) {
        await api.stopEngine()
        setRunning(false)
      } else {
        await api.startEngine()
        setRunning(true)
      }
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }
  
  const toggleMonitors = async () => {
    setLoading(true)
    try {
      if (monitorsRunning) {
        await api.stopMonitors()
        setMonitorsRunning(false)
      } else {
        await api.setupShopify()
        await api.startMonitors()
        setMonitorsRunning(true)
      }
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }
  
  // Poll for updates
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
    const interval = setInterval(pollStatus, 5000)
    return () => clearInterval(interval)
  }, [])
  
  // Poll for events
  useEffect(() => {
    const pollEvents = async () => {
      try {
        const data = await api.getMonitorEvents(10)
        if (data.events) {
          data.events.forEach((e: any, i: number) => {
            addEvent({ ...e, id: `${e.timestamp}-${i}` })
          })
        }
      } catch {}
    }
    
    const interval = setInterval(pollEvents, 3000)
    return () => clearInterval(interval)
  }, [])
  
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Command Center</h1>
          <p className="text-gray-500 text-sm">Real-time monitoring and control</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={toggleMonitors}
            disabled={loading}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all",
              monitorsRunning
                ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/30"
                : "bg-[#1a1a24] text-gray-400 border border-[#2a2a3a] hover:border-cyan-500/50"
            )}
          >
            {monitorsRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {monitorsRunning ? 'Stop Monitors' : 'Start Monitors'}
          </button>
          
          <button
            onClick={toggleEngine}
            disabled={loading}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all",
              isRunning
                ? "bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30"
                : "bg-purple-600 text-white hover:bg-purple-500"
            )}
          >
            {isRunning ? <Pause className="w-4 h-4" /> : <Zap className="w-4 h-4" />}
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
          color="purple"
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
          color="cyan"
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
