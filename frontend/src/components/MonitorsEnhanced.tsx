import { useState } from 'react'
import { 
  Radio, 
  Play, 
  Pause, 
  Plus,
  Check,
  RefreshCw,
  Store,
  Globe,
  Filter,
  Zap,
  TrendingUp,
  DollarSign,
  Search,
  X,
  Sparkles,
  Target
} from 'lucide-react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import { cn, formatRelativeTime } from '../lib/utils'

const MONITOR_PRESETS = [
  {
    id: 'dunks',
    name: 'Nike Dunks',
    icon: Sparkles,
    color: 'purple',
    keywords: ['dunk', 'nike dunk', 'sb dunk'],
    minPrice: 100,
    maxPrice: 200,
    sizes: ['8', '8.5', '9', '9.5', '10', '10.5', '11'],
    stores: ['DTLR', 'Shoe Palace', 'Jimmy Jazz', 'Hibbett']
  },
  {
    id: 'jordans',
    name: 'Air Jordans',
    icon: TrendingUp,
    color: 'red',
    keywords: ['jordan', 'air jordan', 'retro'],
    minPrice: 150,
    maxPrice: 250,
    sizes: ['9', '9.5', '10', '10.5', '11', '11.5', '12'],
    stores: ['DTLR', 'Shoe Palace', 'Hibbett', 'Foot Locker']
  },
  {
    id: 'yeezys',
    name: 'Yeezys',
    icon: Zap,
    color: 'cyan',
    keywords: ['yeezy', 'adidas yeezy', 'yzy'],
    minPrice: 200,
    maxPrice: 350,
    sizes: ['8', '9', '10', '11', '12'],
    stores: ['Social Status', 'Undefeated', 'Concepts']
  },
  {
    id: 'new-balance',
    name: 'New Balance',
    icon: Target,
    color: 'green',
    keywords: ['new balance', '550', '990', '2002r'],
    minPrice: 120,
    maxPrice: 200,
    sizes: ['9', '9.5', '10', '10.5', '11'],
    stores: ['Concepts', 'Bodega', 'Social Status']
  }
]

const DEFAULT_STORES = [
  { name: "DTLR", url: "https://www.dtlr.com", enabled: true },
  { name: "Shoe Palace", url: "https://www.shoepalace.com", enabled: true },
  { name: "Jimmy Jazz", url: "https://www.jimmyjazz.com", enabled: true },
  { name: "Hibbett", url: "https://www.hibbett.com", enabled: true },
  { name: "Social Status", url: "https://www.socialstatuspgh.com", enabled: false },
  { name: "Undefeated", url: "https://undefeated.com", enabled: false },
  { name: "Concepts", url: "https://cncpts.com", enabled: false },
  { name: "Bodega", url: "https://bdgastore.com", enabled: false },
  { name: "Kith", url: "https://kith.com", enabled: false },
  { name: "Extra Butter", url: "https://extrabutterny.com", enabled: false },
]

const FOOTSITES = [
  { id: "footlocker", name: "Foot Locker", enabled: true },
  { id: "champs", name: "Champs Sports", enabled: true },
  { id: "eastbay", name: "Eastbay", enabled: true },
  { id: "footaction", name: "Footaction", enabled: false },
  { id: "kidsfootlocker", name: "Kids Foot Locker", enabled: false },
]

function PresetCard({ preset, onApply, isActive }: { preset: typeof MONITOR_PRESETS[0], onApply: () => void, isActive: boolean }) {
  const Icon = preset.icon
  const colors = {
    purple: 'from-purple-500/20 to-violet-500/10 border-purple-500/30 text-purple-400',
    red: 'from-red-500/20 to-rose-500/10 border-red-500/30 text-red-400',
    cyan: 'from-cyan-500/20 to-blue-500/10 border-cyan-500/30 text-cyan-400',
    green: 'from-green-500/20 to-emerald-500/10 border-green-500/30 text-green-400',
  }
  
  return (
    <div className={cn(
      "p-4 rounded-xl border bg-gradient-to-br transition-all cursor-pointer hover:scale-105",
      colors[preset.color as keyof typeof colors],
      isActive && "ring-2 ring-offset-2 ring-offset-[#0a0a0f]"
    )}
    onClick={onApply}>
      <div className="flex items-center justify-between mb-3">
        <Icon className="w-6 h-6" />
        {isActive && <Check className="w-5 h-5 text-white" />}
      </div>
      <h3 className="font-bold text-white mb-1">{preset.name}</h3>
      <p className="text-xs opacity-80 mb-2">{preset.keywords.length} keywords</p>
      <div className="flex items-center gap-2 text-xs opacity-70">
        <DollarSign className="w-3 h-3" />
        <span>${preset.minPrice}-${preset.maxPrice}</span>
      </div>
    </div>
  )
}

function StoreCard({ 
  name, 
  url, 
  enabled,
  stats,
  onToggle 
}: { 
  name: string
  url: string
  enabled: boolean
  stats?: { successCount: number; errorCount: number; productsFound: number; lastCheck: string | null }
  onToggle: () => void
}) {
  return (
    <div className={cn(
      "p-4 rounded-xl border transition-all",
      enabled 
        ? "bg-[#0f0f18] border-purple-500/30" 
        : "bg-[#0a0a0f] border-[#1a1a2e] opacity-60"
    )}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center",
            enabled ? "bg-purple-500/20" : "bg-[#1a1a24]"
          )}>
            <Store className={cn("w-5 h-5", enabled ? "text-purple-400" : "text-gray-600")} />
          </div>
          <div>
            <h3 className="font-medium text-white">{name}</h3>
            <p className="text-xs text-gray-500 truncate max-w-[150px]">{url}</p>
          </div>
        </div>
        
        <button
          onClick={onToggle}
          role="switch"
          aria-checked={enabled ? "true" : "false"}
          aria-label={`Toggle ${name} monitoring`}
          className={cn(
            "w-12 h-6 rounded-full transition-colors relative",
            enabled ? "bg-purple-600" : "bg-[#2a2a3a]"
          )}
        >
          <div className={cn(
            "absolute w-5 h-5 rounded-full bg-white top-0.5 transition-all",
            enabled ? "left-6" : "left-0.5"
          )} />
        </button>
      </div>
      
      {enabled && stats && (
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-2 rounded-lg bg-[#1a1a24]">
            <p className="text-lg font-bold text-white">{stats.productsFound}</p>
            <p className="text-xs text-gray-500">Found</p>
          </div>
          <div className="p-2 rounded-lg bg-[#1a1a24]">
            <p className="text-lg font-bold text-green-400">{stats.successCount}</p>
            <p className="text-xs text-gray-500">Success</p>
          </div>
          <div className="p-2 rounded-lg bg-[#1a1a24]">
            <p className={cn("text-lg font-bold", stats.errorCount > 0 ? "text-red-400" : "text-gray-400")}>
              {stats.errorCount}
            </p>
            <p className="text-xs text-gray-500">Errors</p>
          </div>
        </div>
      )}
      
      {enabled && stats?.lastCheck && (
        <p className="text-xs text-gray-500 mt-2 text-center">
          Last check: {formatRelativeTime(stats.lastCheck)}
        </p>
      )}
    </div>
  )
}

export function MonitorsEnhanced() {
  const { monitorsRunning, setMonitorsRunning, shopifyStores } = useStore()
  const [loading, setLoading] = useState(false)
  const [stores, setStores] = useState(DEFAULT_STORES)
  const [footsites, setFootsites] = useState(FOOTSITES)
  const [targetSizes, setTargetSizes] = useState('10, 10.5, 11, 11.5, 12')
  const [keywords, setKeywords] = useState('')
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [showAddStore, setShowAddStore] = useState(false)
  const [newStore, setNewStore] = useState({ name: '', url: '' })
  const [activePreset, setActivePreset] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  
  const toggleStore = (index: number) => {
    setStores(s => s.map((store, i) => 
      i === index ? { ...store, enabled: !store.enabled } : store
    ))
  }
  
  const toggleFootsite = (index: number) => {
    setFootsites(f => f.map((site, i) => 
      i === index ? { ...site, enabled: !site.enabled } : site
    ))
  }
  
  const applyPreset = (preset: typeof MONITOR_PRESETS[0]) => {
    setActivePreset(preset.id)
    setKeywords(preset.keywords.join(', '))
    setTargetSizes(preset.sizes.join(', '))
    setMinPrice(preset.minPrice.toString())
    setMaxPrice(preset.maxPrice.toString())
    
    // Enable preset stores
    setStores(stores.map(store => ({
      ...store,
      enabled: preset.stores.includes(store.name)
    })))
  }
  
  const clearFilters = () => {
    setActivePreset(null)
    setKeywords('')
    setMinPrice('')
    setMaxPrice('')
  }
  
  const handleStartMonitors = async () => {
    setLoading(true)
    try {
      const sizes = targetSizes.split(',').map(s => s.trim()).filter(Boolean)
      const keywordList = keywords.split(',').map(k => k.trim()).filter(Boolean)
      
      // Setup Shopify with enabled stores
      await api.setupShopify(sizes)
      
      // Add custom stores
      for (const store of stores.filter(s => s.enabled)) {
        try {
          await api.addShopifyStore(store.name, store.url, 3000, sizes)
        } catch {}
      }
      
      // Setup Footsites with keywords
      const enabledFootsites = footsites.filter(f => f.enabled).map(f => f.id)
      if (enabledFootsites.length > 0) {
        await api.setupFootsites(enabledFootsites, keywordList.length > 0 ? keywordList : undefined, sizes)
      }
      
      // Start monitors
      await api.startMonitors()
      setMonitorsRunning(true)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }
  
  const handleStopMonitors = async () => {
    setLoading(true)
    try {
      await api.stopMonitors()
      setMonitorsRunning(false)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }
  
  const addCustomStore = () => {
    if (newStore.name && newStore.url) {
      setStores([...stores, { ...newStore, enabled: true }])
      setNewStore({ name: '', url: '' })
      setShowAddStore(false)
    }
  }
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Radio className="w-7 h-7 text-cyan-400" />
            Advanced Monitor Setup
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Configure intelligent monitoring with presets and filters
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all border",
              showFilters 
                ? "bg-purple-500/20 text-purple-400 border-purple-500/30"
                : "bg-[#1a1a24] text-gray-400 border-[#2a2a3a] hover:border-purple-500/30"
            )}
          >
            <Filter className="w-4 h-4" />
            Filters
          </button>
          <button
            onClick={monitorsRunning ? handleStopMonitors : handleStartMonitors}
            disabled={loading}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-all",
              monitorsRunning
                ? "bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30"
                : "bg-cyan-600 text-white hover:bg-cyan-500"
            )}
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : monitorsRunning ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {monitorsRunning ? 'Stop All Monitors' : 'Start All Monitors'}
          </button>
        </div>
      </div>
      
      {/* Quick Presets */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-purple-400" />
          Quick Presets
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {MONITOR_PRESETS.map(preset => (
            <PresetCard
              key={preset.id}
              preset={preset}
              onApply={() => applyPreset(preset)}
              isActive={activePreset === preset.id}
            />
          ))}
        </div>
      </div>
      
      {/* Advanced Filters */}
      {showFilters && (
        <div className="mb-6 p-5 rounded-xl bg-[#0f0f18] border border-purple-500/30">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Filter className="w-5 h-5 text-purple-400" />
              Advanced Filters
            </h3>
            {(keywords || minPrice || maxPrice) && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 text-sm text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
                Clear
              </button>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                <Search className="w-4 h-4 inline mr-1" />
                Keywords (comma separated)
              </label>
              <input
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                className="w-full px-4 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="dunk, jordan, yeezy"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                <DollarSign className="w-4 h-4 inline mr-1" />
                Min Price
              </label>
              <input
                type="number"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                className="w-full px-4 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="100"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                <DollarSign className="w-4 h-4 inline mr-1" />
                Max Price
              </label>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                className="w-full px-4 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="250"
              />
            </div>
          </div>
        </div>
      )}
      
      {/* Target Sizes */}
      <div className="mb-6 p-4 rounded-xl bg-[#0f0f18] border border-[#1a1a2e]">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Target Sizes (comma separated)
        </label>
        <input
          type="text"
          value={targetSizes}
          onChange={(e) => setTargetSizes(e.target.value)}
          className="w-full px-4 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
          placeholder="10, 10.5, 11, 11.5, 12"
        />
      </div>
      
      {/* Shopify Stores */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Store className="w-5 h-5 text-purple-400" />
            Shopify Stores
          </h2>
          <button
            onClick={() => setShowAddStore(true)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Store
          </button>
        </div>
        
        {showAddStore && (
          <div className="mb-4 p-4 rounded-xl bg-[#0f0f18] border border-purple-500/30">
            <div className="grid grid-cols-2 gap-4 mb-3">
              <input
                type="text"
                value={newStore.name}
                onChange={(e) => setNewStore({ ...newStore, name: e.target.value })}
                className="px-3 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="Store Name"
              />
              <input
                type="text"
                value={newStore.url}
                onChange={(e) => setNewStore({ ...newStore, url: e.target.value })}
                className="px-3 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="https://store.com"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowAddStore(false)}
                className="px-3 py-1.5 text-sm text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={addCustomStore}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-500 transition-colors"
              >
                <Check className="w-4 h-4" />
                Add
              </button>
            </div>
          </div>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {stores.map((store, i) => (
            <StoreCard
              key={i}
              name={store.name}
              url={store.url}
              enabled={store.enabled}
              stats={shopifyStores[store.name.toLowerCase().replace(' ', '_')]}
              onToggle={() => toggleStore(i)}
            />
          ))}
        </div>
      </div>
      
      {/* Footsites */}
      <div>
        <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
          <Globe className="w-5 h-5 text-cyan-400" />
          Footsites
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {footsites.map((site, i) => (
            <div
              key={site.id}
              onClick={() => toggleFootsite(i)}
              className={cn(
                "p-4 rounded-xl border cursor-pointer transition-all",
                site.enabled
                  ? "bg-[#0f0f18] border-cyan-500/30"
                  : "bg-[#0a0a0f] border-[#1a1a2e] opacity-60"
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center",
                    site.enabled ? "bg-cyan-500/20" : "bg-[#1a1a24]"
                  )}>
                    <Globe className={cn("w-4 h-4", site.enabled ? "text-cyan-400" : "text-gray-600")} />
                  </div>
                  <span className="font-medium text-white">{site.name}</span>
                </div>
                <div className={cn(
                  "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors",
                  site.enabled ? "border-cyan-500 bg-cyan-500" : "border-gray-600"
                )}>
                  {site.enabled && <Check className="w-3 h-3 text-white" />}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
