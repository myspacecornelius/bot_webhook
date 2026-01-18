import { useEffect } from 'react'
import { useStore } from './store/useStore'
import { api } from './api/client'
import { Sidebar } from './components/Sidebar'
import { Dashboard } from './components/Dashboard'
import { ProductFeed } from './components/ProductFeed'
import { Monitors } from './components/Monitors'

function App() {
  const { selectedTab, setRunning, setMonitorsRunning, setStats } = useStore()
  
  // Initial status fetch
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await api.getStatus()
        if (status.running !== undefined) {
          setRunning(status.running)
        }
        
        const monitorStatus = await api.getMonitorStatus()
        if (monitorStatus.running !== undefined) {
          setMonitorsRunning(monitorStatus.running)
        }
        if (monitorStatus.total_products_found !== undefined) {
          setStats({
            totalProductsFound: monitorStatus.total_products_found,
            highPriorityFound: monitorStatus.high_priority_found || 0,
          })
        }
      } catch (e) {
        console.log('API not available yet')
      }
    }
    
    fetchStatus()
  }, [])
  
  const renderContent = () => {
    switch (selectedTab) {
      case 'dashboard':
        return <Dashboard />
      case 'feed':
        return <ProductFeed />
      case 'monitors':
        return <Monitors />
      case 'tasks':
        return <ComingSoon title="Tasks" description="Manage checkout tasks" />
      case 'profiles':
        return <ComingSoon title="Profiles" description="Payment and shipping profiles" />
      case 'proxies':
        return <ComingSoon title="Proxies" description="Proxy management" />
      case 'analytics':
        return <ComingSoon title="Analytics" description="Performance analytics" />
      case 'intelligence':
        return <ComingSoon title="Intelligence" description="Market research" />
      case 'settings':
        return <ComingSoon title="Settings" description="Bot configuration" />
      default:
        return <Dashboard />
    }
  }
  
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {renderContent()}
      </main>
    </div>
  )
}

function ComingSoon({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-2">{title}</h1>
        <p className="text-gray-500">{description}</p>
        <div className="mt-6 px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg text-sm">
          Coming Soon
        </div>
      </div>
    </div>
  )
}

export default App
