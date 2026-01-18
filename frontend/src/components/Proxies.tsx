import { useState, useEffect } from 'react'
import { 
  Globe, 
  Plus,
  Trash2,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Wifi,
  WifiOff,
  Upload,
  Download
} from 'lucide-react'
import { api } from '../api/client'
import { cn } from '../lib/utils'

interface ProxyGroup {
  id: string
  name: string
  proxies: Proxy[]
  createdAt: string
}

interface Proxy {
  url: string
  status: 'untested' | 'working' | 'slow' | 'dead'
  speed?: number
  location?: string
  lastTested?: string
}

function ProxyGroupCard({ group, onTest, onDelete }: {
  group: ProxyGroup
  onTest: () => void
  onDelete: () => void
}) {
  const workingCount = group.proxies.filter(p => p.status === 'working').length
  const deadCount = group.proxies.filter(p => p.status === 'dead').length
  
  return (
    <div className="bg-[#0f0f18] border border-[#1a1a2e] rounded-xl p-5 hover:border-purple-500/30 transition-all">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
            <Globe className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white">{group.name}</h3>
            <p className="text-sm text-gray-500">{group.proxies.length} proxies</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={onTest}
            className="p-2 rounded-lg bg-[#1a1a24] text-gray-400 hover:text-cyan-400 transition-colors"
            title="Test Proxies"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={onDelete}
            className="p-2 rounded-lg bg-[#1a1a24] text-gray-400 hover:text-red-400 transition-colors"
            title="Delete Group"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-3 gap-2">
        <div className="p-3 rounded-lg bg-[#1a1a24] text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span className="text-lg font-bold text-green-400">{workingCount}</span>
          </div>
          <p className="text-xs text-gray-500">Working</p>
        </div>
        <div className="p-3 rounded-lg bg-[#1a1a24] text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <Clock className="w-4 h-4 text-yellow-400" />
            <span className="text-lg font-bold text-yellow-400">
              {group.proxies.filter(p => p.status === 'slow').length}
            </span>
          </div>
          <p className="text-xs text-gray-500">Slow</p>
        </div>
        <div className="p-3 rounded-lg bg-[#1a1a24] text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <XCircle className="w-4 h-4 text-red-400" />
            <span className="text-lg font-bold text-red-400">{deadCount}</span>
          </div>
          <p className="text-xs text-gray-500">Dead</p>
        </div>
      </div>
      
      {/* Proxy List Preview */}
      <div className="mt-4 max-h-32 overflow-y-auto">
        {group.proxies.slice(0, 5).map((proxy, i) => (
          <div key={i} className="flex items-center justify-between py-1.5 border-b border-[#1a1a2e] last:border-0">
            <div className="flex items-center gap-2">
              {proxy.status === 'working' ? (
                <Wifi className="w-3 h-3 text-green-400" />
              ) : proxy.status === 'dead' ? (
                <WifiOff className="w-3 h-3 text-red-400" />
              ) : (
                <Clock className="w-3 h-3 text-gray-400" />
              )}
              <span className="text-xs text-gray-400 font-mono truncate max-w-[200px]">
                {proxy.url.replace(/:[^:]+@/, ':***@')}
              </span>
            </div>
            {proxy.speed && (
              <span className="text-xs text-gray-500">{proxy.speed}ms</span>
            )}
          </div>
        ))}
        {group.proxies.length > 5 && (
          <p className="text-xs text-gray-500 text-center pt-2">
            +{group.proxies.length - 5} more
          </p>
        )}
      </div>
    </div>
  )
}

function AddProxyModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState('')
  const [proxies, setProxies] = useState('')
  const [loading, setLoading] = useState(false)
  
  const handleSubmit = async () => {
    if (!name || !proxies) return
    setLoading(true)
    try {
      await api.createProxyGroup(name, proxies)
      onCreated()
      onClose()
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }
  
  const proxyCount = proxies.split('\n').filter(p => p.trim()).length
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onClose}>
      <div className="w-full max-w-lg bg-[#0f0f18] border border-[#1a1a2e] rounded-2xl p-6" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-white mb-6">Add Proxy Group</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Group Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
              placeholder="ISP Proxies"
            />
          </div>
          
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-gray-400">Proxies (one per line)</label>
              <span className="text-xs text-gray-500">{proxyCount} proxies</span>
            </div>
            <textarea
              value={proxies}
              onChange={(e) => setProxies(e.target.value)}
              className="w-full h-48 px-4 py-3 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 font-mono text-sm resize-none"
              placeholder="ip:port:user:pass&#10;ip:port:user:pass&#10;http://user:pass@ip:port"
            />
          </div>
        </div>
        
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !name || proxyCount === 0}
            className="flex items-center gap-2 px-5 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add {proxyCount} Proxies
          </button>
        </div>
      </div>
    </div>
  )
}

export function Proxies() {
  const [groups, setGroups] = useState<ProxyGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [testing, setTesting] = useState(false)
  
  const fetchGroups = async () => {
    try {
      const data = await api.getProxies()
      setGroups(data.groups || [])
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }
  
  useEffect(() => {
    fetchGroups()
  }, [])
  
  const handleTestAll = async () => {
    setTesting(true)
    try {
      await api.testProxies()
      await fetchGroups()
    } catch (e) {
      console.error(e)
    }
    setTesting(false)
  }
  
  const totalProxies = groups.reduce((acc, g) => acc + g.proxies.length, 0)
  const workingProxies = groups.reduce((acc, g) => acc + g.proxies.filter(p => p.status === 'working').length, 0)
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Globe className="w-7 h-7 text-cyan-400" />
            Proxies
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            {groups.length} groups • {totalProxies} total • {workingProxies} working
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={handleTestAll}
            disabled={testing}
            className="flex items-center gap-2 px-4 py-2 bg-[#1a1a24] text-gray-300 border border-[#2a2a3a] rounded-lg hover:border-cyan-500/50 transition-colors"
          >
            <RefreshCw className={cn("w-4 h-4", testing && "animate-spin")} />
            Test All
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-5 py-2 bg-purple-600 hover:bg-purple-500 text-white font-medium rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Group
          </button>
        </div>
      </div>
      
      {/* Groups Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : groups.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-gray-500">
          <Globe className="w-16 h-16 mb-4 opacity-30" />
          <p className="text-lg font-medium">No proxy groups</p>
          <p className="text-sm mb-4">Add proxies to improve success rates</p>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-medium rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Proxy Group
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups.map(group => (
            <ProxyGroupCard
              key={group.id}
              group={group}
              onTest={() => api.testProxies(group.id).then(fetchGroups)}
              onDelete={() => {/* TODO */}}
            />
          ))}
        </div>
      )}
      
      {/* Modal */}
      {showModal && (
        <AddProxyModal
          onClose={() => setShowModal(false)}
          onCreated={fetchGroups}
        />
      )}
    </div>
  )
}
