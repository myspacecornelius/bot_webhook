import { useEffect, useState } from 'react'
import { useStore } from './store/useStore'
import { api } from './api/client'
import { Sidebar } from './components/Sidebar'
import { Dashboard } from './components/Dashboard'
import { ProductFeedEnhanced as ProductFeed } from './components/ProductFeedEnhanced'
import { MonitorsEnhanced as Monitors } from './components/MonitorsEnhanced'
import { Tasks } from './components/Tasks'
import { Profiles } from './components/Profiles'
import { Proxies } from './components/Proxies'
import { CopCalendar } from './components/CopCalendar'
import { Intelligence } from './components/Intelligence'
import { Settings } from './components/Settings'
import { ToastContainer } from './components/ui/Toast'
import { SuccessTheater } from './components/SuccessTheater'
import { StealthMode } from './components/StealthMode'
import { Login } from './components/Login'

function App() {
  const { selectedTab, setRunning, setMonitorsRunning, setStats } = useStore()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  
  // Check for existing license on mount
  useEffect(() => {
    const checkAuth = async () => {
      const license = localStorage.getItem('phantom_license')
      if (license) {
        try {
          const response = await fetch('/api/auth/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ license_key: license })
          })
          
          if (response.ok) {
            setIsAuthenticated(true)
          } else {
            localStorage.removeItem('phantom_license')
            localStorage.removeItem('phantom_user')
          }
        } catch (e) {
          console.error('Auth check failed:', e)
        }
      }
      setIsCheckingAuth(false)
    }
    
    checkAuth()
  }, [])
  
  const handleLogin = (licenseKey: string) => {
    setIsAuthenticated(true)
  }
  
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
        return <Tasks />
      case 'profiles':
        return <Profiles />
      case 'proxies':
        return <Proxies />
      case 'analytics':
        return <CopCalendar />
      case 'intelligence':
        return <Intelligence />
      case 'settings':
        return <Settings />
      default:
        return <Dashboard />
    }
  }
  
  // Show loading while checking auth
  if (isCheckingAuth) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading Phantom...</p>
        </div>
      </div>
    )
  }
  
  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />
  }
  
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {renderContent()}
      </main>
      <ToastContainer />
      <SuccessTheater />
      <StealthMode />
    </div>
  )
}

export default App
