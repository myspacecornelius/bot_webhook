import { useState } from 'react'
import { 
  BarChart3, 
  TrendingUp,
  DollarSign,
  ShoppingBag,
  Target,
  Calendar,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react'
import { cn, formatPrice } from '../lib/utils'

function StatCard({ title, value, change, icon: Icon, prefix = '', color = 'moss' }: {
  title: string
  value: number
  change?: number
  icon: any
  prefix?: string
  color?: 'moss' | 'green' | 'red' | 'moss'
}) {
  const colors = {
    moss: 'from-moss-500/20 to-moss-500/10 border-moss-500/30 text-moss-400',
    green: 'from-green-500/20 to-[var(--primary)]/10 border-green-500/30 text-green-400',
    red: 'from-red-500/20 to-rose-500/10 border-red-500/30 text-red-400',
    moss: 'from-[var(--info)]/20 to-blue-500/10 border-[var(--info)]/30 text-[var(--info)]',
  }
  
  return (
    <div className={cn("p-5 rounded-xl border bg-gradient-to-br", colors[color])}>
      <div className="flex items-start justify-between mb-3">
        <Icon className="w-6 h-6" />
        {change !== undefined && (
          <div className={cn(
            "flex items-center gap-1 text-xs font-medium",
            change >= 0 ? "text-green-400" : "text-red-400"
          )}>
            {change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <p className="text-3xl font-bold text-[var(--text)]">{prefix}{value.toLocaleString()}</p>
      <p className="text-sm text-[var(--muted)] mt-1">{title}</p>
    </div>
  )
}

function MiniChart({ data, color = '#6A7B4E' }: { data: number[]; color?: string }) {
  const max = Math.max(...data, 1)
  const min = Math.min(...data, 0)
  const range = max - min || 1
  
  return (
    <div className="flex items-end gap-1 h-16">
      {data.map((value, i) => (
        <div
          key={i}
          className="flex-1 rounded-t transition-all hover:opacity-80"
          style={{
            height: `${((value - min) / range) * 100}%`,
            backgroundColor: color,
            minHeight: '4px',
          }}
        />
      ))}
    </div>
  )
}

function SitePerformance({ sites }: { sites: { name: string; checkouts: number; declines: number; successRate: number }[] }) {
  return (
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5">
      <h3 className="font-semibold text-[var(--text)] mb-4 flex items-center gap-2">
        <Target className="w-5 h-5 text-moss-400" />
        Site Performance
      </h3>
      
      <div className="space-y-3">
        {sites.map((site, i) => (
          <div key={i} className="flex items-center gap-4">
            <div className="w-32 text-sm text-[var(--text)] font-medium truncate">{site.name}</div>
            <div className="flex-1">
              <div className="h-2 bg-[var(--surface2)] rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-500 to-moss-400 rounded-full transition-all"
                  style={{ width: `${site.successRate}%` }}
                />
              </div>
            </div>
            <div className="w-20 text-right">
              <span className="text-sm font-medium text-green-400">{site.successRate}%</span>
            </div>
            <div className="w-24 text-right text-sm text-[var(--muted)]">
              {site.checkouts}/{site.checkouts + site.declines}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function RecentActivity({ activity }: { activity: { type: string; product: string; site: string; time: string; profit?: number }[] }) {
  return (
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5">
      <h3 className="font-semibold text-[var(--text)] mb-4 flex items-center gap-2">
        <Calendar className="w-5 h-5 text-[var(--info)]" />
        Recent Activity
      </h3>
      
      <div className="space-y-3">
        {activity.map((item, i) => (
          <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-[var(--surface2)]">
            <div className={cn(
              "w-2 h-2 rounded-full",
              item.type === 'checkout' ? "bg-green-500" : "bg-red-500"
            )} />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-[var(--text)] truncate">{item.product}</p>
              <p className="text-xs text-[var(--muted)]">{item.site} • {item.time}</p>
            </div>
            {item.profit && (
              <span className="text-sm font-medium text-green-400">+{formatPrice(item.profit)}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export function Analytics() {
  const [timeRange, setTimeRange] = useState<'today' | 'week' | 'month' | 'all'>('week')
  const [stats] = useState({
    totalCheckouts: 47,
    totalDeclines: 23,
    totalRevenue: 14250,
    totalProfit: 4830,
    successRate: 67,
  })
  
  const [dailyData] = useState<number[]>([3, 7, 5, 12, 8, 15, 10])
  
  const [sitePerformance] = useState([
    { name: 'DTLR', checkouts: 18, declines: 5, successRate: 78 },
    { name: 'Shoe Palace', checkouts: 12, declines: 8, successRate: 60 },
    { name: 'Jimmy Jazz', checkouts: 9, declines: 4, successRate: 69 },
    { name: 'Hibbett', checkouts: 5, declines: 3, successRate: 63 },
    { name: 'Kith', checkouts: 3, declines: 3, successRate: 50 },
  ])
  
  const [recentActivity] = useState([
    { type: 'checkout', product: 'Jordan 4 Black Cat', site: 'DTLR', time: '2 min ago', profit: 150 },
    { type: 'decline', product: 'Dunk Low Panda', site: 'Shoe Palace', time: '5 min ago' },
    { type: 'checkout', product: 'Jordan 1 Chicago', site: 'Jimmy Jazz', time: '12 min ago', profit: 180 },
    { type: 'checkout', product: 'Yeezy 350 Onyx', site: 'DTLR', time: '18 min ago', profit: 50 },
    { type: 'decline', product: 'NB 550 White', site: 'Hibbett', time: '25 min ago' },
  ])
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)] flex items-center gap-3">
            <BarChart3 className="w-7 h-7 text-moss-400" />
            Analytics
          </h1>
          <p className="text-[var(--muted)] text-sm mt-1">
            Track your performance and profits
          </p>
        </div>
        
        <div className="flex items-center gap-1 p-1 bg-[var(--surface)] rounded-lg border border-[var(--border)]">
          {(['today', 'week', 'month', 'all'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={cn(
                "px-4 py-1.5 text-sm font-medium rounded-md transition-colors capitalize",
                timeRange === range
                  ? "bg-moss-500/20 text-moss-400"
                  : "text-[var(--muted)] hover:text-[var(--text)]"
              )}
            >
              {range === 'all' ? 'All Time' : range}
            </button>
          ))}
        </div>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Total Checkouts"
          value={stats.totalCheckouts}
          change={12}
          icon={ShoppingBag}
          color="green"
        />
        <StatCard
          title="Success Rate"
          value={stats.successRate}
          change={5}
          icon={Target}
          prefix=""
          color="moss"
        />
        <StatCard
          title="Total Revenue"
          value={stats.totalRevenue}
          change={18}
          icon={DollarSign}
          prefix="$"
          color="moss"
        />
        <StatCard
          title="Total Profit"
          value={stats.totalProfit}
          change={23}
          icon={TrendingUp}
          prefix="$"
          color="green"
        />
      </div>
      
      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Checkout Chart */}
        <div className="lg:col-span-2 bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-[var(--text)]">Checkouts Over Time</h3>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-green-500" />
                <span className="text-[var(--muted)]">Success</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-red-500" />
                <span className="text-[var(--muted)]">Declined</span>
              </div>
            </div>
          </div>
          <MiniChart data={dailyData} color="var(--primary)" />
          <div className="flex justify-between mt-2 text-xs text-[var(--muted)]">
            <span>Mon</span>
            <span>Tue</span>
            <span>Wed</span>
            <span>Thu</span>
            <span>Fri</span>
            <span>Sat</span>
            <span>Sun</span>
          </div>
        </div>
        
        {/* Profit Breakdown */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5">
          <h3 className="font-semibold text-[var(--text)] mb-4">Profit Breakdown</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-[var(--muted)]">Jordan</span>
                <span className="text-[var(--text)] font-medium">$2,450</span>
              </div>
              <div className="h-2 bg-[var(--surface2)] rounded-full overflow-hidden">
                <div className="h-full w-[65%] bg-moss-500 rounded-full" />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-[var(--muted)]">Nike</span>
                <span className="text-[var(--text)] font-medium">$1,280</span>
              </div>
              <div className="h-2 bg-[var(--surface2)] rounded-full overflow-hidden">
                <div className="h-full w-[35%] bg-[var(--info)] rounded-full" />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-[var(--muted)]">Yeezy</span>
                <span className="text-[var(--text)] font-medium">$680</span>
              </div>
              <div className="h-2 bg-[var(--surface2)] rounded-full overflow-hidden">
                <div className="h-full w-[18%] bg-yellow-500 rounded-full" />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-[var(--muted)]">New Balance</span>
                <span className="text-[var(--text)] font-medium">$420</span>
              </div>
              <div className="h-2 bg-[var(--surface2)] rounded-full overflow-hidden">
                <div className="h-full w-[12%] bg-green-500 rounded-full" />
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SitePerformance sites={sitePerformance} />
        <RecentActivity activity={recentActivity} />
      </div>
    </div>
  )
}
