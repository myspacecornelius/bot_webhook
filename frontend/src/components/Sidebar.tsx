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
  Bell
} from 'lucide-react'
import { useStore } from '../store/useStore'
import { cn } from '../lib/utils'

const navItems = [
  { id: 'dashboard', label: 'Command Center', icon: LayoutDashboard },
  { id: 'monitors', label: 'Monitors', icon: Radio },
  { id: 'feed', label: 'Product Feed', icon: Zap },
  { id: 'tasks', label: 'Tasks', icon: ShoppingCart },
  { id: 'profiles', label: 'Profiles', icon: Users },
  { id: 'proxies', label: 'Proxies', icon: Globe },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'intelligence', label: 'Intelligence', icon: TrendingUp },
  { id: 'settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const { selectedTab, setSelectedTab, isRunning, monitorsRunning, events } = useStore()
  
  const highPriorityCount = events.filter(e => e.priority === 'high').length
  
  return (
    <aside className="w-64 h-screen bg-[#0a0a0f] border-r border-[#1a1a2e] flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-[#1a1a2e]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-violet-400 bg-clip-text text-transparent">
              PHANTOM
            </h1>
            <p className="text-xs text-gray-500">v1.0.0</p>
          </div>
        </div>
      </div>
      
      {/* Status Indicators */}
      <div className="px-4 py-3 border-b border-[#1a1a2e]">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <div className={cn(
              "w-2 h-2 rounded-full",
              isRunning ? "bg-green-500 animate-pulse" : "bg-gray-600"
            )} />
            <span className="text-gray-400">Engine</span>
          </div>
          <span className={isRunning ? "text-green-400" : "text-gray-500"}>
            {isRunning ? "Running" : "Stopped"}
          </span>
        </div>
        <div className="flex items-center justify-between text-xs mt-2">
          <div className="flex items-center gap-2">
            <div className={cn(
              "w-2 h-2 rounded-full",
              monitorsRunning ? "bg-cyan-500 animate-pulse" : "bg-gray-600"
            )} />
            <span className="text-gray-400">Monitors</span>
          </div>
          <span className={monitorsRunning ? "text-cyan-400" : "text-gray-500"}>
            {monitorsRunning ? "Active" : "Idle"}
          </span>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = selectedTab === item.id
          const showBadge = item.id === 'feed' && highPriorityCount > 0
          
          return (
            <button
              key={item.id}
              onClick={() => setSelectedTab(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
                isActive 
                  ? "bg-purple-500/20 text-purple-400 border border-purple-500/30" 
                  : "text-gray-400 hover:text-white hover:bg-white/5"
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="flex-1 text-left">{item.label}</span>
              {showBadge && (
                <span className="px-2 py-0.5 text-xs bg-red-500 text-white rounded-full animate-pulse">
                  {highPriorityCount}
                </span>
              )}
            </button>
          )
        })}
      </nav>
      
      {/* Quick Actions */}
      <div className="p-4 border-t border-[#1a1a2e]">
        <div className="flex gap-2">
          <button className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium rounded-lg transition-colors">
            <Bell className="w-4 h-4" />
            Alerts
          </button>
        </div>
      </div>
    </aside>
  )
}
