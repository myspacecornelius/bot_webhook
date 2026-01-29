// Use environment variable or default to relative path for local dev
const API_BASE = import.meta.env.VITE_API_URL || '/api'

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }
  
  return response.json()
}

export const api = {
  // Status
  getStatus: () => request<any>('/status'),
  startEngine: () => request<any>('/start', { method: 'POST' }),
  stopEngine: () => request<any>('/stop', { method: 'POST' }),
  
  // Monitors
  getMonitorStatus: () => request<any>('/monitors/status'),
  startMonitors: () => request<any>('/monitors/start', { method: 'POST' }),
  stopMonitors: () => request<any>('/monitors/stop', { method: 'POST' }),
  setupShopify: (sizes?: string[]) => request<any>('/monitors/shopify/setup', {
    method: 'POST',
    body: JSON.stringify({ target_sizes: sizes, use_defaults: true }),
  }),
  addShopifyStore: (name: string, url: string, delay?: number, sizes?: string[]) => 
    request<any>('/monitors/shopify/add-store', {
      method: 'POST',
      body: JSON.stringify({ name, url, delay_ms: delay || 3000, target_sizes: sizes }),
    }),
  setupFootsites: (sites?: string[], keywords?: string[], sizes?: string[]) =>
    request<any>('/monitors/footsites/setup', {
      method: 'POST',
      body: JSON.stringify({ sites, keywords, target_sizes: sizes, delay_ms: 5000 }),
    }),
  getMonitorEvents: (limit = 50) => request<any>(`/monitors/events?limit=${limit}`),
  getHighPriorityEvents: (limit = 20) => request<any>(`/monitors/events/high-priority?limit=${limit}`),
  configureAutoTasks: (enabled: boolean, minConfidence = 0.7, minPriority = 'medium') =>
    request<any>('/monitors/auto-tasks', {
      method: 'POST',
      body: JSON.stringify({ enabled, min_confidence: minConfidence, min_priority: minPriority }),
    }),
  
  // Curated Products
  getCuratedProducts: () => request<any>('/products/curated'),
  getHighPriorityProducts: () => request<any>('/products/curated/high-priority'),
  getProfitableProducts: (minProfit = 50) => request<any>(`/products/curated/profitable?min_profit=${minProfit}`),
  loadProductsJson: (path: string) => request<any>('/products/load-json', {
    method: 'POST',
    body: JSON.stringify({ path }),
  }),
  
  // Tasks
  getTasks: () => request<any>('/tasks'),
  createTask: (task: any) => request<any>('/tasks', {
    method: 'POST',
    body: JSON.stringify(task),
  }),
  startTask: (id: string) => request<any>(`/tasks/${id}/start`, { method: 'POST' }),
  stopTask: (id: string) => request<any>(`/tasks/${id}/stop`, { method: 'POST' }),
  deleteTask: (id: string) => request<any>(`/tasks/${id}`, { method: 'DELETE' }),
  startAllTasks: () => request<any>('/tasks/start-all', { method: 'POST' }),
  stopAllTasks: () => request<any>('/tasks/stop-all', { method: 'POST' }),
  
  // Quick Tasks
  createQuickTask: (data: {
    url: string
    sizes?: string[]
    quantity?: number
    mode?: string
    profile_id?: string
    proxy_group_id?: string
    auto_start?: boolean
  }) => request<any>('/tasks/quick', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  createQuickTasksBatch: (urls: string[], sizes?: string[], mode?: string, autoStart?: boolean) =>
    request<any>('/tasks/quick-batch', {
      method: 'POST',
      body: JSON.stringify({ urls, sizes, mode, auto_start: autoStart }),
    }),
  
  // Profiles
  getProfiles: () => request<any>('/profiles'),
  createProfile: (profile: any) => request<any>('/profiles', {
    method: 'POST',
    body: JSON.stringify(profile),
  }),
  deleteProfile: (id: string) => request<any>(`/profiles/${id}`, { method: 'DELETE' }),
  
  // Proxies
  getProxies: () => request<any>('/proxies'),
  createProxyGroup: (name: string, proxies: string) => request<any>('/proxies/groups', {
    method: 'POST',
    body: JSON.stringify({ name, proxies }),
  }),
  testProxies: (groupId?: string) => request<any>('/proxies/test', {
    method: 'POST',
    body: JSON.stringify({ group_id: groupId }),
  }),
  
  // Intelligence
  getTrending: () => request<any>('/intelligence/trending'),
  researchProduct: (name: string, sku: string, retailPrice: number) =>
    request<any>(`/intelligence/research?name=${encodeURIComponent(name)}&sku=${encodeURIComponent(sku)}&retail_price=${retailPrice}`, {
      method: 'POST',
    }),
  
  // Captcha
  getCaptchaBalances: () => request<any>('/captcha/balances'),
  
  // Monitor Config Persistence
  saveMonitorConfig: () => request<any>('/monitors/config/save', { method: 'POST' }),
  loadMonitorConfig: () => request<any>('/monitors/config/load'),
  restoreMonitorConfig: () => request<any>('/monitors/config/restore', { method: 'POST' }),
  
  // Rate Limits
  getRateLimits: () => request<any>('/monitors/rate-limits'),
  
  // Analytics
  getCheckoutAnalytics: () => request<any>('/analytics/checkout'),
  
  // Profile Import
  importProfiles: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch(`${API_BASE}/profiles/import`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) throw new Error(`Import failed: ${response.status}`)
    return response.json()
  },
  
  // Shopify Stores
  getShopifyStores: () => request<any>('/monitors/shopify/stores'),
  updateShopifyStore: (storeId: string, updates: any) =>
    request<any>(`/monitors/shopify/stores/${storeId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }),
  deleteShopifyStore: (storeId: string) =>
    request<any>(`/monitors/shopify/stores/${storeId}`, { method: 'DELETE' }),
  
  // Restock tracking
  getRestockHistory: (hours = 24, limit = 50) =>
    request<any>(`/monitors/restocks/history?hours=${hours}&limit=${limit}`),
  getRestockStats: () => request<any>('/monitors/restocks/stats'),
  getRestockPatterns: (minOccurrences = 2) =>
    request<any>(`/monitors/restocks/patterns?min_occurrences=${minOccurrences}`),
}

// WebSocket connection for real-time events
export class EventWebSocket {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private listeners: Map<string, Set<(data: any) => void>> = new Map()
  
  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/events`
    
    this.ws = new WebSocket(wsUrl)
    
    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'heartbeat') return
        
        const listeners = this.listeners.get(data.type) || new Set()
        listeners.forEach(callback => callback(data.data))
        
        // Also notify 'all' listeners
        const allListeners = this.listeners.get('all') || new Set()
        allListeners.forEach(callback => callback(data))
      } catch (e) {
        console.error('WebSocket message parse error:', e)
      }
    }
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++
        setTimeout(() => this.connect(), 2000 * this.reconnectAttempts)
      }
    }
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
  
  on(eventType: string, callback: (data: any) => void) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set())
    }
    this.listeners.get(eventType)!.add(callback)
    return () => this.off(eventType, callback)
  }
  
  off(eventType: string, callback: (data: any) => void) {
    this.listeners.get(eventType)?.delete(callback)
  }
  
  ping() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send('ping')
    }
  }
}

export const eventWs = new EventWebSocket()
