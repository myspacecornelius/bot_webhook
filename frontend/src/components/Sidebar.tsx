/**
 * Sidebar Navigation
 * Premium dark theme with real-time status
 */

import {
  LayoutDashboard,
  Radio,
  ShoppingCart,
  Users,
  Globe,
  BarChart3,
  Settings,
  Zap,
  TrendingUp,
  Sparkles,
  Wifi,
  WifiOff,
  AlertCircle,
  BookOpen
} from 'lucide-react'
import { useStore } from '../store/useStore'
import { cn } from '../lib/utils'
import { useEngineStatus, useMonitorStatus, useTimeAgo } from '../hooks/useQueries'

const navItems = [
  { id: 'dashboard', label: 'Command Center', icon: LayoutDashboard },
  { id: 'monitors', label: 'Monitors', icon: Radio },
  { id: 'feed', label: 'Product Feed', icon: Zap },
  { id: 'tasks', label: 'Tasks', icon: ShoppingCart },
  { id: 'profiles', label: 'Profiles', icon: Users },
  { id: 'proxies', label: 'Proxies', icon: Globe },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'intelligence', label: 'Intelligence', icon: TrendingUp },
  { id: 'learn', label: 'Learn', icon: BookOpen },
  { id: 'settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const { selectedTab, setSelectedTab, isRunning, monitorsRunning, events, stats, isConnected } = useStore()

  const { data: engineStatus, lastUpdated: engineLastUpdated, error: engineError } = useEngineStatus()
  const { data: monitorStatus, lastUpdated: monitorLastUpdated } = useMonitorStatus(isRunning)

  const engineTimeAgo = useTimeAgo(engineLastUpdated)
  const monitorTimeAgo = useTimeAgo(monitorLastUpdated)

  const highPriorityCount = events.filter(e => e.priority === 'high').length

  const engineRunning = engineStatus?.running ?? isRunning
  const engineDegraded = engineError !== null
  const monitorsActive = monitorStatus?.running ?? monitorsRunning
  const monitorDegraded = monitorStatus?.shopify?.stores
    ? Object.values(monitorStatus.shopify.stores).some(s => s.errors > 0)
    : false

  return (
    <aside className="w-[280px] h-screen flex flex-col bg-zinc-900 border-r border-zinc-800">
      {/* Logo */}
      <div className="p-6 border-b border-zinc-800">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
              <Zap className="w-6 h-6 text-white" strokeWidth={2.5} />
            </div>
            <div
              className={cn(
                "absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-zinc-900",
                isConnected ? "bg-emerald-400" : engineDegraded ? "bg-amber-400" : "bg-zinc-500"
              )}
            />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">PHANTOM</h1>
            <p className="text-[11px] uppercase tracking-widest text-zinc-500">Bot Suite v1.0</p>
          </div>
        </div>
      </div>

      {/* Status Cards */}
      <div className="p-4 space-y-3">
        {/* Engine Status */}
        <div className={cn(
          "p-4 rounded-xl border transition-all duration-300",
          engineRunning
            ? "bg-emerald-500/10 border-emerald-500/30"
            : engineDegraded
              ? "bg-amber-500/10 border-amber-500/30"
              : "bg-zinc-800/50 border-zinc-700/50"
        )}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2.5">
              <div className={cn(
                "status-dot",
                engineRunning ? "online pulsing" : engineDegraded ? "warning" : "offline"
              )} />
              <span className="text-xs font-medium text-zinc-400">Engine</span>
            </div>
            <span className={cn(
              "text-xs font-bold",
              engineRunning ? "text-emerald-400" : engineDegraded ? "text-amber-400" : "text-zinc-500"
            )}>
              {engineRunning ? 'Running' : engineDegraded ? 'Degraded' : 'Stopped'}
            </span>
          </div>
          {engineLastUpdated && (
            <p className="text-[10px] text-zinc-600">Updated {engineTimeAgo}</p>
          )}
        </div>

        {/* Monitors Status */}
        <div className={cn(
          "p-4 rounded-xl border transition-all duration-300",
          monitorsActive
            ? "bg-blue-500/10 border-blue-500/30"
            : monitorDegraded
              ? "bg-amber-500/10 border-amber-500/30"
              : "bg-zinc-800/50 border-zinc-700/50"
        )}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2.5">
              <div className={cn(
                "status-dot",
                monitorsActive ? "online pulsing" : monitorDegraded ? "warning" : "offline"
              )}
                style={{ background: monitorsActive ? '#3b82f6' : undefined }}
              />
              <span className="text-xs font-medium text-zinc-400">Monitors</span>
            </div>
            <div className="flex items-center gap-1.5">
              {monitorDegraded && <AlertCircle className="w-3 h-3 text-amber-400" />}
              <span className={cn(
                "text-xs font-bold",
                monitorsActive ? "text-blue-400" : monitorDegraded ? "text-amber-400" : "text-zinc-500"
              )}>
                {monitorsActive ? 'Active' : monitorDegraded ? 'Errors' : 'Idle'}
              </span>
            </div>
          </div>

          {monitorsActive && stats.totalProductsFound > 0 && (
            <div className="mt-2 pt-2 border-t border-blue-500/20">
              <p className="text-[10px] text-zinc-500">
                <span className="font-bold text-blue-400">
                  {stats.totalProductsFound.toLocaleString()}
                </span> products found
              </p>
            </div>
          )}

          {monitorLastUpdated && (
            <p className="text-[10px] text-zinc-600 mt-1">Updated {monitorTimeAgo}</p>
          )}
        </div>

        {/* Connection Status */}
        <div className={cn(
          "flex items-center gap-2.5 px-4 py-3 rounded-xl text-xs font-medium border",
          isConnected
            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
            : "bg-amber-500/10 text-amber-400 border-amber-500/30"
        )}>
          {isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
          {isConnected ? 'WebSocket Connected' : 'Reconnecting...'}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-3 space-y-1 overflow-y-auto">
        <p className="px-3 py-2 text-[10px] font-semibold uppercase tracking-widest text-zinc-600">Navigation</p>
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = selectedTab === item.id
          const showBadge = item.id === 'feed' && highPriorityCount > 0

          return (
            <button
              key={item.id}
              onClick={() => setSelectedTab(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-violet-500/20 text-violet-400 border border-violet-500/30"
                  : "text-zinc-400 hover:text-white hover:bg-zinc-800/50 border border-transparent"
              )}
            >
              <Icon className={cn("w-5 h-5", isActive && "text-violet-400")} />
              <span className="flex-1 text-left">{item.label}</span>
              {showBadge && (
                <span className="px-2 py-0.5 text-[10px] font-bold bg-rose-500 text-white rounded-full animate-pulse">
                  {highPriorityCount}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Pro Badge */}
      <div className="p-4 border-t border-zinc-800">
        <div className="p-4 rounded-xl bg-gradient-to-r from-violet-500/20 to-purple-500/20 border border-violet-500/30">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-violet-400" />
            <span className="text-sm font-semibold text-white">Phantom Pro</span>
          </div>
          <p className="text-[11px] text-zinc-400 mt-1.5">Advanced automation suite</p>
        </div>
      </div>
    </aside>
  )
}
