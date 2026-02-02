import { useState, useEffect } from 'react'
import { 
  Zap, 
  ExternalLink, 
  ShoppingCart, 
  TrendingUp,
  RefreshCw,
  Volume2,
  VolumeX,
  Star,
  Sparkles,
  DollarSign,
  Filter,
  X
} from 'lucide-react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import { cn, formatPrice, formatRelativeTime, getProfitClass, playSound } from '../lib/utils'
import { RadarScanner } from './RadarScanner'

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
  const [isCreatingTask, setIsCreatingTask] = useState(false)
  
  const handleQuickTask = async () => {
    setIsCreatingTask(true)
    try {
      await onQuickTask()
      playSound('success')
    } catch (e) {
      console.error(e)
    }
    setIsCreatingTask(false)
  }
  
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
          <div className="flex items-center gap-1 px-2 py-1 bg-green-500 text-[var(--text)] text-xs font-bold rounded-full shadow-lg shadow-green-500/50">
            <Star className="w-3 h-3 fill-current" />
            HIGH PROFIT
          </div>
        </div>
      )}
      
      <div className="relative p-4">
        {/* Header */}
        <div className="flex items-start gap-3 mb-3">
          {/* Product image */}
          <div className="w-20 h-20 rounded-lg bg-[var(--surface2)] flex items-center justify-center overflow-hidden flex-shrink-0">
            {event.imageUrl ? (
              <img src={event.imageUrl} alt={event.product} className="w-full h-full object-cover" />
            ) : (
              <ShoppingCart className="w-8 h-8 text-[var(--muted)]" />
            )}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="px-2 py-0.5 text-xs bg-moss-500/20 text-moss-400 rounded font-medium">
                {event.store}
              </span>
              <span className="px-2 py-0.5 text-xs bg-[var(--surface2)] text-[var(--muted)] rounded">
                {event.source}
              </span>
            </div>
            <h3 className="text-sm font-semibold text-[var(--text)] line-clamp-2 mb-1">{event.product}</h3>
            <p className="text-xs text-[var(--muted)]">{formatRelativeTime(event.timestamp)}</p>
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
            <p className="text-xs text-[var(--muted)] mb-1">Retail Price</p>
            <p className="text-lg font-bold text-[var(--text)]">{formatPrice(event.price)}</p>
          </div>
          
          {event.profit && (
            <div className="text-right">
              <p className="text-xs text-[var(--muted)] mb-1">Est. Profit</p>
              <p className={cn("text-lg font-bold", profitClass)}>
                +{formatPrice(event.profit)}
              </p>
            </div>
          )}
        </div>
        
        {/* Sizes */}
        {event.sizes && event.sizes.length > 0 && (
          <div className="mb-3">
            <p className="text-xs text-[var(--muted)] mb-2">Available Sizes</p>
            <div className="flex flex-wrap gap-1">
              {event.sizes.slice(0, 8).map((size, i) => (
                <span key={i} className="px-2 py-1 text-xs bg-[var(--surface2)] text-[var(--muted)] rounded">
                  {size}
                </span>
              ))}
              {event.sizes.length > 8 && (
                <span className="px-2 py-1 text-xs bg-[var(--surface2)] text-[var(--muted)] rounded">
                  +{event.sizes.length - 8}
                </span>
              )}
            </div>
          </div>
        )}
        
        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={handleQuickTask}
            disabled={isCreatingTask}
            className={cn(
              "flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-all",
              isHighPriority
                ? "bg-green-600 text-[var(--text)] hover:bg-green-500"
                : "bg-moss-600 text-[var(--text)] hover:bg-moss-500",
              isCreatingTask && "opacity-50 cursor-not-allowed"
            )}
          >
            {isCreatingTask ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Zap className="w-4 h-4" />
                Quick Task
              </>
            )}
          </button>
          
          <a
            href={event.url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 rounded-lg bg-[var(--surface2)] text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface2)] transition-colors flex items-center justify-center"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  )
}

export function ProductFeedEnhanced() {
  const { events } = useStore()
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [showFilters, setShowFilters] = useState(false)
  const [minProfit, setMinProfit] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [selectedStore, setSelectedStore] = useState<string>('')
  const [priorityFilter, setPriorityFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all')
  
  // Filter events
  const filteredEvents = events.filter(event => {
    if (priorityFilter !== 'all' && event.priority !== priorityFilter) return false
    if (minProfit && (!event.profit || event.profit < parseFloat(minProfit))) return false
    if (maxPrice && event.price > parseFloat(maxPrice)) return false
    if (selectedStore && event.store !== selectedStore) return false
    return true
  })
  
  // Get unique stores
  const stores = Array.from(new Set(events.map(e => e.store)))
  
  // Play sound for new high priority items
  useEffect(() => {
    if (soundEnabled && events.length > 0) {
      const latestEvent = events[0]
      if (latestEvent.priority === 'high') {
        playSound('alert')
      }
    }
  }, [events.length, soundEnabled])
  
  const handleQuickTask = async (event: ProductEvent) => {
    try {
      await api.createQuickTask({
        url: event.url,
        sizes: event.sizes,
        auto_start: true
      })
    } catch (e) {
      console.error('Failed to create quick task:', e)
    }
  }
  
  const clearFilters = () => {
    setMinProfit('')
    setMaxPrice('')
    setSelectedStore('')
    setPriorityFilter('all')
  }
  
  const hasActiveFilters = minProfit || maxPrice || selectedStore || priorityFilter !== 'all'
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)] flex items-center gap-3">
            <Sparkles className="w-7 h-7 text-[var(--info)]" />
            Live Product Feed
          </h1>
          <p className="text-[var(--muted)] text-sm mt-1">
            Real-time product detections with profit analysis
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            className={cn(
              "p-2 rounded-lg transition-colors",
              soundEnabled 
                ? "bg-moss-500/20 text-moss-400" 
                : "bg-[var(--surface2)] text-[var(--muted)]"
            )}
            aria-label={soundEnabled ? "Disable sound" : "Enable sound"}
          >
            {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
          </button>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all border",
              showFilters 
                ? "bg-moss-500/20 text-moss-400 border-moss-500/30"
                : "bg-[var(--surface2)] text-[var(--muted)] border-[var(--border)] hover:border-moss-500/30"
            )}
          >
            <Filter className="w-4 h-4" />
            Filters
            {hasActiveFilters && (
              <span className="px-1.5 py-0.5 bg-moss-600 text-[var(--text)] text-xs rounded-full">
                {[minProfit, maxPrice, selectedStore, priorityFilter !== 'all'].filter(Boolean).length}
              </span>
            )}
          </button>
        </div>
      </div>
      
      {/* Filters */}
      {showFilters && (
        <div className="mb-6 p-5 rounded-xl bg-[var(--surface)] border border-moss-500/30">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-[var(--text)] flex items-center gap-2">
              <Filter className="w-5 h-5 text-moss-400" />
              Filter Products
            </h3>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 text-sm text-[var(--muted)] hover:text-[var(--text)] transition-colors"
              >
                <X className="w-4 h-4" />
                Clear All
              </button>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-[var(--muted)] mb-2">
                Priority
              </label>
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value as any)}
                className="w-full px-4 py-2 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] focus:outline-none focus:border-moss-500"
              >
                <option value="all">All Priorities</option>
                <option value="high">High Only</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-[var(--muted)] mb-2">
                <DollarSign className="w-4 h-4 inline mr-1" />
                Min Profit
              </label>
              <input
                type="number"
                value={minProfit}
                onChange={(e) => setMinProfit(e.target.value)}
                className="w-full px-4 py-2 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] placeholder-gray-500 focus:outline-none focus:border-moss-500"
                placeholder="50"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-[var(--muted)] mb-2">
                <DollarSign className="w-4 h-4 inline mr-1" />
                Max Price
              </label>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                className="w-full px-4 py-2 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] placeholder-gray-500 focus:outline-none focus:border-moss-500"
                placeholder="250"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-[var(--muted)] mb-2">
                Store
              </label>
              <select
                value={selectedStore}
                onChange={(e) => setSelectedStore(e.target.value)}
                className="w-full px-4 py-2 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] focus:outline-none focus:border-moss-500"
              >
                <option value="">All Stores</option>
                {stores.map(store => (
                  <option key={store} value={store}>{store}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}
      
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
          <p className="text-sm text-[var(--muted)] mb-1">Total Products</p>
          <p className="text-2xl font-bold text-[var(--text)]">{filteredEvents.length}</p>
        </div>
        <div className="p-4 rounded-xl bg-[var(--surface)] border border-green-500/30">
          <p className="text-sm text-[var(--muted)] mb-1">High Priority</p>
          <p className="text-2xl font-bold text-green-400">
            {filteredEvents.filter(e => e.priority === 'high').length}
          </p>
        </div>
        <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
          <p className="text-sm text-[var(--muted)] mb-1">Avg Profit</p>
          <p className="text-2xl font-bold text-[var(--text)]">
            {formatPrice(
              filteredEvents.reduce((sum, e) => sum + (e.profit || 0), 0) / 
              (filteredEvents.filter(e => e.profit).length || 1)
            )}
          </p>
        </div>
        <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
          <p className="text-sm text-[var(--muted)] mb-1">Stores Active</p>
          <p className="text-2xl font-bold text-[var(--text)]">{stores.length}</p>
        </div>
      </div>
      
      {/* Product Grid */}
      {filteredEvents.length === 0 ? (
        hasActiveFilters ? (
          <div className="text-center py-20">
            <Sparkles className="w-16 h-16 text-[var(--muted)] mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-[var(--text)] mb-2">No Products Match</h3>
            <p className="text-[var(--muted)]">No products match your filters. Try adjusting them.</p>
          </div>
        ) : (
          <RadarScanner />
        )
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredEvents.map(event => (
            <ProductCard
              key={event.id}
              event={event}
              onQuickTask={() => handleQuickTask(event)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
