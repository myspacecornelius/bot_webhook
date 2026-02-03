import { useState, useEffect } from 'react'
import { 
  Zap, 
  ExternalLink, 
  ShoppingCart, 
  TrendingUp,
  RefreshCw,
  Volume2,
  VolumeX,
  Star
} from 'lucide-react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import { cn, formatPrice, formatRelativeTime, getProfitClass, playSound } from '../lib/utils'

interface ProductEvent {
  id: string
  type: string
  source: string
  store: string
  product: string
  url: string
  sizes: string[]
  price: number
  matched: string | null
  confidence: number
  priority: 'high' | 'medium' | 'low'
  profit: number | null
  timestamp: string
  imageUrl?: string
}

function ProductCard({ event, onQuickTask }: { event: ProductEvent; onQuickTask: () => void }) {
  const isHighPriority = event.priority === 'high'
  const profitClass = event.profit ? getProfitClass(event.profit) : ''
  
  return (
    <div className={cn(
      "group relative rounded-xl border overflow-hidden transition-all hover:scale-[1.02] animate-fade-in-up",
      isHighPriority 
        ? "bg-gradient-to-br from-green-500/10 to-[var(--primary)]/5 border-green-500/30" 
        : "bg-[var(--surface)] border-[var(--border)] hover:border-moss-500/30"
    )}>
      {/* Glow effect for high priority */}
      {isHighPriority && (
        <div className="absolute inset-0 bg-green-500/5 animate-pulse" />
      )}
      
      {/* Priority badge */}
      {isHighPriority && (
        <div className="absolute top-3 right-3 z-10">
          <div className="flex items-center gap-1 px-2 py-1 bg-green-500 text-[var(--text)] text-xs font-bold rounded-full animate-pulse-glow">
            <Star className="w-3 h-3 fill-current" />
            HIGH PROFIT
          </div>
        </div>
      )}
      
      <div className="relative p-4">
        {/* Header */}
        <div className="flex items-start gap-3 mb-3">
          {/* Product image placeholder */}
          <div className="w-16 h-16 rounded-lg bg-[var(--surface2)] flex items-center justify-center overflow-hidden">
            {event.imageUrl ? (
              <img src={event.imageUrl} alt="" className="w-full h-full object-cover" />
            ) : (
              <ShoppingCart className="w-6 h-6 text-[var(--muted)]" />
            )}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 text-xs bg-moss-500/20 text-moss-400 rounded font-medium">
                {event.store}
              </span>
              <span className="px-2 py-0.5 text-xs bg-[var(--surface2)] text-[var(--muted)] rounded">
                {event.source}
              </span>
            </div>
            <h3 className="text-sm font-semibold text-[var(--text)] truncate">{event.product}</h3>
            <p className="text-xs text-[var(--muted)] mt-0.5">{formatRelativeTime(event.timestamp)}</p>
          </div>
        </div>
        
        {/* Matched product info */}
        {event.matched && (
          <div className="mb-3 p-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-yellow-400" />
                <span className="text-xs text-yellow-400 font-medium">Matched: {event.matched}</span>
              </div>
              <span className="text-xs text-[var(--muted)]">{Math.round(event.confidence * 100)}% match</span>
            </div>
          </div>
        )}
        
        {/* Price and profit */}
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-lg font-bold text-[var(--text)]">{formatPrice(event.price)}</p>
            <p className="text-xs text-[var(--muted)]">Retail</p>
          </div>
          {event.profit && (
            <div className="text-right">
              <p className={cn("text-lg font-bold", profitClass)}>
                +{formatPrice(event.profit)}
              </p>
              <p className="text-xs text-[var(--muted)]">Est. Profit</p>
            </div>
          )}
        </div>
        
        {/* Sizes */}
        <div className="mb-4">
          <p className="text-xs text-[var(--muted)] mb-2">Available Sizes</p>
          <div className="flex flex-wrap gap-1">
            {event.sizes.slice(0, 8).map((size, i) => (
              <span 
                key={i}
                className="px-2 py-1 text-xs bg-[var(--surface2)] text-[var(--muted)] rounded border border-[var(--border)]"
              >
                {size}
              </span>
            ))}
            {event.sizes.length > 8 && (
              <span className="px-2 py-1 text-xs text-[var(--muted)]">
                +{event.sizes.length - 8} more
              </span>
            )}
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={onQuickTask}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-moss-600 hover:bg-moss-500 text-[var(--text)] text-sm font-medium rounded-lg transition-colors"
          >
            <Zap className="w-4 h-4" />
            Quick Task
          </button>
          <a
            href={event.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center px-3 py-2 bg-[var(--surface2)] hover:bg-[#252532] text-[var(--muted)] rounded-lg transition-colors border border-[var(--border)]"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  )
}

export function ProductFeed() {
  const { events, soundEnabled, setSoundEnabled } = useStore()
  const [filter, setFilter] = useState<'all' | 'high' | 'matched'>('all')
  const [refreshing, setRefreshing] = useState(false)
  
  const filteredEvents = events.filter(e => {
    if (filter === 'high') return e.priority === 'high'
    if (filter === 'matched') return e.matched !== null
    return true
  })
  
  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await api.getMonitorEvents(50)
    } catch {}
    setTimeout(() => setRefreshing(false), 500)
  }
  
  const handleQuickTask = (event: ProductEvent) => {
    // Would create a task for this product
    console.log('Create quick task for:', event.product)
    if (soundEnabled) playSound('notification')
  }
  
  // Play sound on new high priority event
  useEffect(() => {
    const highPriorityEvents = events.filter(e => e.priority === 'high')
    if (highPriorityEvents.length > 0 && soundEnabled) {
      playSound('alert')
    }
  }, [events.filter(e => e.priority === 'high').length])
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)] flex items-center gap-3">
            <Zap className="w-7 h-7 text-moss-400" />
            Product Feed
          </h1>
          <p className="text-[var(--muted)] text-sm mt-1">
            {events.length} products detected • {events.filter(e => e.priority === 'high').length} high priority
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Sound toggle */}
          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            className={cn(
              "p-2 rounded-lg transition-colors",
              soundEnabled 
                ? "bg-moss-500/20 text-moss-400" 
                : "bg-[var(--surface2)] text-[var(--muted)]"
            )}
          >
            {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
          </button>
          
          {/* Refresh */}
          <button
            onClick={handleRefresh}
            className="p-2 rounded-lg bg-[var(--surface2)] text-[var(--muted)] hover:text-[var(--text)] transition-colors"
          >
            <RefreshCw className={cn("w-5 h-5", refreshing && "animate-spin")} />
          </button>
          
          {/* Filter */}
          <div className="flex items-center gap-1 p-1 bg-[var(--surface)] rounded-lg border border-[var(--border)]">
            {(['all', 'high', 'matched'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  "px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
                  filter === f
                    ? "bg-moss-500/20 text-moss-400"
                    : "text-[var(--muted)] hover:text-[var(--text)]"
                )}
              >
                {f === 'all' ? 'All' : f === 'high' ? 'High Profit' : 'Matched'}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Product Grid */}
      {filteredEvents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-[var(--muted)]">
          <ShoppingCart className="w-16 h-16 mb-4 opacity-30" />
          <p className="text-lg font-medium">No products found</p>
          <p className="text-sm">Products will appear here when monitors detect them</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredEvents.map((event, i) => (
            <ProductCard 
              key={event.id || i} 
              event={event} 
              onQuickTask={() => handleQuickTask(event)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
