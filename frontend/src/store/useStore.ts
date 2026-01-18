import { create } from 'zustand'

interface MonitorEvent {
  id: string
  type: 'new_product' | 'restock'
  source: 'shopify' | 'footsite'
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

interface StoreStats {
  name: string
  url: string
  successCount: number
  errorCount: number
  productsFound: number
  lastCheck: string | null
}

interface Task {
  id: string
  status: string
  statusMessage: string
  siteName: string
  productName?: string
  size?: string
  isRunning: boolean
}

interface BotState {
  // Connection
  isConnected: boolean
  setConnected: (connected: boolean) => void
  
  // Engine
  isRunning: boolean
  setRunning: (running: boolean) => void
  
  // Monitors
  monitorsRunning: boolean
  setMonitorsRunning: (running: boolean) => void
  shopifyStores: Record<string, StoreStats>
  setShopifyStores: (stores: Record<string, StoreStats>) => void
  
  // Events
  events: MonitorEvent[]
  addEvent: (event: MonitorEvent) => void
  clearEvents: () => void
  
  // Tasks
  tasks: Task[]
  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  updateTask: (id: string, updates: Partial<Task>) => void
  
  // Stats
  stats: {
    totalProductsFound: number
    highPriorityFound: number
    tasksCreated: number
    checkouts: number
    declines: number
  }
  setStats: (stats: Partial<BotState['stats']>) => void
  
  // UI
  soundEnabled: boolean
  setSoundEnabled: (enabled: boolean) => void
  notifications: boolean
  setNotifications: (enabled: boolean) => void
  selectedTab: string
  setSelectedTab: (tab: string) => void
}

export const useStore = create<BotState>((set) => ({
  // Connection
  isConnected: false,
  setConnected: (connected) => set({ isConnected: connected }),
  
  // Engine
  isRunning: false,
  setRunning: (running) => set({ isRunning: running }),
  
  // Monitors
  monitorsRunning: false,
  setMonitorsRunning: (running) => set({ monitorsRunning: running }),
  shopifyStores: {},
  setShopifyStores: (stores) => set({ shopifyStores: stores }),
  
  // Events
  events: [],
  addEvent: (event) => set((state) => ({
    events: [event, ...state.events].slice(0, 200)
  })),
  clearEvents: () => set({ events: [] }),
  
  // Tasks
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((state) => ({
    tasks: [...state.tasks, task]
  })),
  updateTask: (id, updates) => set((state) => ({
    tasks: state.tasks.map(t => t.id === id ? { ...t, ...updates } : t)
  })),
  
  // Stats
  stats: {
    totalProductsFound: 0,
    highPriorityFound: 0,
    tasksCreated: 0,
    checkouts: 0,
    declines: 0,
  },
  setStats: (stats) => set((state) => ({
    stats: { ...state.stats, ...stats }
  })),
  
  // UI
  soundEnabled: true,
  setSoundEnabled: (enabled) => set({ soundEnabled: enabled }),
  notifications: true,
  setNotifications: (enabled) => set({ notifications: enabled }),
  selectedTab: 'dashboard',
  setSelectedTab: (tab) => set({ selectedTab: tab }),
}))
