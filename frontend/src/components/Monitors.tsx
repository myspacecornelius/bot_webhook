import { useState, useEffect } from 'react'
import { 
  Radio, 
  Play, 
  Pause, 
  Plus,
  Settings,
  Check,
  X,
  RefreshCw,
  Store,
  Globe
} from 'lucide-react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import { cn, formatRelativeTime } from '../lib/utils'

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
  const health = stats 
    ? stats.errorCount === 0 ? 'good' : stats.errorCount < 3 ? 'warning' : 'error'
    : 'unknown'
  
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

export function Monitors() {
  const { monitorsRunning, setMonitorsRunning, shopifyStores } = useStore()
  const [loading, setLoading] = useState(false)
  const [stores, setStores] = useState(DEFAULT_STORES)
  const [footsites, setFootsites] = useState(FOOTSITES)
  const [targetSizes, setTargetSizes] = useState('10, 10.5, 11, 11.5, 12')
  const [showAddStore, setShowAddStore] = useState(false)
  const [newStore, setNewStore] = useState({ name: '', url: '' })
  
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
  
  const handleStartMonitors = async () => {
    setLoading(true)
    try {
      const sizes = targetSizes.split(',').map(s => s.trim()).filter(Boolean)
      
      // Setup Shopify with enabled stores
      await api.setupShopify(sizes)
      
      // Add custom stores
      for (const store of stores.filter(s => s.enabled)) {
        try {
          await api.addShopifyStore(store.name, store.url, 3000, sizes)
        } catch {}
      }
      
      // Setup Footsites
      const enabledFootsites = footsites.filter(f => f.enabled).map(f => f.id)
      if (enabledFootsites.length > 0) {
        await api.setupFootsites(enabledFootsites, undefined, sizes)
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
            Monitor Configuration
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Configure stores and sites to monitor for products
          </p>
        </div>
        
        <div className="flex items-center gap-3">
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
