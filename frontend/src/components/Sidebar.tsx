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
  Sparkles
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
  const { selectedTab, setSelectedTab, isRunning, monitorsRunning, events, stats } = useStore()
  
  const highPriorityCount = events.filter(e => e.priority === 'high').length
  
  return (
    <aside className="w-[260px] h-screen flex flex-col" style={{ background: 'var(--surface)', borderRight: '1px solid var(--border)' }}>
      {/* Logo */}
      <div className="p-5" style={{ borderBottom: '1px solid var(--border)' }}>
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'var(--primary)', boxShadow: 'var(--shadow-sm)' }}>
              <Zap className="w-5 h-5" style={{ color: '#FFF8ED' }} />
            </div>
            <div className="absolute -top-0.5 -right-0.5 w-3 h-3 rounded-full border-2" style={{ background: '#2F6F4E', borderColor: 'var(--surface)' }} />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight" style={{ color: 'var(--text)' }}>
              PHANTOM
            </h1>
            <p className="text-[10px] uppercase tracking-widest" style={{ color: 'var(--muted)' }}>Bot Suite v1.0</p>
          </div>
        </div>
      </div>
      
      {/* Status Cards */}
      <div className="p-3 space-y-2">
        <div className="p-3 rounded-lg border transition-all duration-300" style={{
          background: isRunning ? 'rgba(47,111,78,0.08)' : 'var(--surface2)',
          borderColor: isRunning ? 'rgba(47,111,78,0.25)' : 'var(--border)'
        }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={cn(
                "status-dot",
                isRunning ? "online pulsing" : "offline"
              )} />
              <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>Engine</span>
            </div>
            <span className="text-xs font-semibold" style={{ color: isRunning ? '#2F6F4E' : 'var(--muted)' }}>
              {isRunning ? "Running" : "Stopped"}
            </span>
          </div>
        </div>
        
        <div className="p-3 rounded-lg border transition-all duration-300" style={{
          background: monitorsRunning ? 'rgba(106,123,78,0.08)' : 'var(--surface2)',
          borderColor: monitorsRunning ? 'rgba(106,123,78,0.25)' : 'var(--border)'
        }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={cn(
                "status-dot",
                monitorsRunning ? "online pulsing" : "offline"
              )} style={{ background: monitorsRunning ? 'var(--info)' : undefined }} />
              <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>Monitors</span>
            </div>
            <span className="text-xs font-semibold" style={{ color: monitorsRunning ? 'var(--primary)' : 'var(--muted)' }}>
              {monitorsRunning ? "Active" : "Idle"}
            </span>
          </div>
          {monitorsRunning && stats.totalProductsFound > 0 && (
            <div className="mt-2 pt-2" style={{ borderTop: '1px solid rgba(106,123,78,0.15)' }}>
              <p className="text-[10px]" style={{ color: 'var(--muted)' }}>
                <span className="font-semibold" style={{ color: 'var(--primary)' }}>{stats.totalProductsFound.toLocaleString()}</span> products found
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto">
        <p className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Navigation</p>
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = selectedTab === item.id
          const showBadge = item.id === 'feed' && highPriorityCount > 0
          
          return (
            <button
              key={item.id}
              onClick={() => setSelectedTab(item.id)}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 border"
              style={{
                background: isActive ? 'rgba(106,123,78,0.12)' : 'transparent',
                borderColor: isActive ? 'rgba(106,123,78,0.25)' : 'transparent',
                color: isActive ? 'var(--primary)' : 'var(--muted)'
              }}
              onMouseEnter={(e) => !isActive && (e.currentTarget.style.background = 'rgba(196,138,44,0.08)')}
              onMouseLeave={(e) => !isActive && (e.currentTarget.style.background = 'transparent')}
            >
              <Icon className="w-4 h-4" style={{ color: isActive ? 'var(--primary)' : 'inherit' }} />
              <span className="flex-1 text-left">{item.label}</span>
              {showBadge && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold bg-rose-500 text-[var(--text)] rounded-md animate-pulse">
                  {highPriorityCount}
                </span>
              )}
            </button>
          )
        })}
      </nav>
      
      {/* Pro Badge */}
      <div className="p-3" style={{ borderTop: '1px solid var(--border)' }}>
        <div className="p-3 rounded-xl" style={{ background: 'rgba(106,123,78,0.08)', border: '1px solid rgba(106,123,78,0.2)' }}>
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4" style={{ color: 'var(--primary)' }} />
            <span className="text-xs font-semibold" style={{ color: 'var(--text)' }}>Phantom Pro</span>
          </div>
          <p className="text-[10px] mt-1" style={{ color: 'var(--muted)' }}>Advanced automation suite</p>
        </div>
      </div>
    </aside>
  )
}
