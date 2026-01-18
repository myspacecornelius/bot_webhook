const API_BASE = '/api'

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
}
