/**
 * Phantom Bot API Client
 * Type-safe API layer with error handling, timeouts, and request cancellation
 */

import type {
  ApiError,
  EngineStatus,
  MonitorStatus,
  MonitorEventsResponse,
  CheckoutAnalytics,
  RateLimitStats,
  TasksResponse,
  ProfilesResponse,
  CuratedProductsResponse,
} from './types'

// ============ Configuration ============

const API_BASE = import.meta.env.VITE_API_URL || '/api'
const DEFAULT_TIMEOUT = 10000 // 10 seconds

// ============ Error Handling ============

export class ApiRequestError extends Error {
  code: string
  details?: Record<string, unknown>
  retryable: boolean
  status?: number

  constructor(error: ApiError, status?: number) {
    super(error.message)
    this.name = 'ApiRequestError'
    this.code = error.code
    this.details = error.details
    this.retryable = error.retryable
    this.status = status
  }
}

function normalizeError(error: unknown, status?: number): ApiRequestError {
  if (error instanceof ApiRequestError) {
    return error
  }

  if (error instanceof Error) {
    // Network or timeout errors are retryable
    const isNetworkError = error.message.includes('fetch') ||
      error.message.includes('network') ||
      error.name === 'AbortError'

    return new ApiRequestError({
      code: isNetworkError ? 'NETWORK_ERROR' : 'UNKNOWN_ERROR',
      message: error.message,
      retryable: isNetworkError,
    }, status)
  }

  return new ApiRequestError({
    code: 'UNKNOWN_ERROR',
    message: String(error),
    retryable: false,
  }, status)
}

// ============ Request Function ============

interface RequestOptions extends Omit<RequestInit, 'signal'> {
  timeout?: number
  signal?: AbortSignal
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { timeout = DEFAULT_TIMEOUT, signal: externalSignal, ...fetchOptions } = options

  // Create timeout controller
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  // Combine with external signal if provided
  if (externalSignal) {
    externalSignal.addEventListener('abort', () => controller.abort())
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers,
      },
      signal: controller.signal,
      ...fetchOptions,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      let errorData: ApiError
      try {
        const json = await response.json()
        errorData = {
          code: `HTTP_${response.status}`,
          message: json.detail || json.message || response.statusText,
          details: json,
          retryable: response.status >= 500 || response.status === 429,
        }
      } catch {
        errorData = {
          code: `HTTP_${response.status}`,
          message: response.statusText,
          retryable: response.status >= 500,
        }
      }
      throw new ApiRequestError(errorData, response.status)
    }

    return response.json()
  } catch (error) {
    clearTimeout(timeoutId)

    if (error instanceof ApiRequestError) {
      throw error
    }

    // Handle abort/timeout
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiRequestError({
        code: 'TIMEOUT',
        message: 'Request timed out',
        retryable: true,
      })
    }

    throw normalizeError(error)
  }
}

// ============ API Methods ============

export const api = {
  // ============ Auth ============
  validateLicense: (licenseKey: string) =>
    request<{ valid: boolean; user: { license_key: string; tier: string; expires_at: string } }>(
      '/auth/validate',
      { method: 'POST', body: JSON.stringify({ license_key: licenseKey }) }
    ),

  createCheckoutSession: (tier: string, email: string) =>
    request<{ session_id: string; url: string }>(
      '/auth/checkout',
      { method: 'POST', body: JSON.stringify({ tier, email }) }
    ),

  // ============ Engine ============
  getStatus: (signal?: AbortSignal) =>
    request<EngineStatus>('/status', { signal }),

  startEngine: () =>
    request<{ message: string }>('/start', { method: 'POST' }),

  stopEngine: () =>
    request<{ message: string }>('/stop', { method: 'POST' }),

  // ============ Monitors ============
  getMonitorStatus: (signal?: AbortSignal) =>
    request<MonitorStatus>('/monitors/status', { signal }),

  startMonitors: () =>
    request<{ message: string }>('/monitors/start', { method: 'POST' }),

  stopMonitors: () =>
    request<{ message: string }>('/monitors/stop', { method: 'POST' }),

  setupShopify: (sizes?: string[]) =>
    request<{ message: string; stores: number }>('/monitors/shopify/setup', {
      method: 'POST',
      body: JSON.stringify({ target_sizes: sizes, use_defaults: true }),
    }),

  addShopifyStore: (name: string, url: string, delay?: number, sizes?: string[]) =>
    request<{ message: string }>('/monitors/shopify/add-store', {
      method: 'POST',
      body: JSON.stringify({ name, url, delay_ms: delay || 3000, target_sizes: sizes }),
    }),

  setupFootsites: (sites?: string[], keywords?: string[], sizes?: string[]) =>
    request<{ message: string }>('/monitors/footsites/setup', {
      method: 'POST',
      body: JSON.stringify({ sites, keywords, target_sizes: sizes, delay_ms: 5000 }),
    }),

  getMonitorEvents: (limit = 50, signal?: AbortSignal) =>
    request<MonitorEventsResponse>(`/monitors/events?limit=${limit}`, { signal }),

  getHighPriorityEvents: (limit = 20, signal?: AbortSignal) =>
    request<MonitorEventsResponse>(`/monitors/events/high-priority?limit=${limit}`, { signal }),

  configureAutoTasks: (enabled: boolean, minConfidence = 0.7, minPriority = 'medium') =>
    request<{ message: string; enabled: boolean }>('/monitors/auto-tasks', {
      method: 'POST',
      body: JSON.stringify({ enabled, min_confidence: minConfidence, min_priority: minPriority }),
    }),

  saveMonitorConfig: () =>
    request<{ message: string; count: number }>('/monitors/config/save', { method: 'POST' }),

  loadMonitorConfig: () =>
    request<{ stores: unknown[]; count: number }>('/monitors/config/load'),

  restoreMonitorConfig: () =>
    request<{ message: string; count: number }>('/monitors/config/restore', { method: 'POST' }),

  // ============ Analytics ============
  getCheckoutAnalytics: (signal?: AbortSignal) =>
    request<CheckoutAnalytics>('/analytics/checkout', { signal }),

  getRateLimits: (signal?: AbortSignal) =>
    request<RateLimitStats>('/monitors/rate-limits', { signal }),

  // ============ Curated Products ============
  getCuratedProducts: (signal?: AbortSignal) =>
    request<CuratedProductsResponse>('/products/curated', { signal }),

  getHighPriorityProducts: (signal?: AbortSignal) =>
    request<{ products: CuratedProductsResponse['products'] }>('/products/curated/high-priority', { signal }),

  getProfitableProducts: (minProfit = 50, signal?: AbortSignal) =>
    request<{ products: CuratedProductsResponse['products'] }>(
      `/products/curated/profitable?min_profit=${minProfit}`,
      { signal }
    ),

  loadProductsJson: (path: string) =>
    request<{ message: string; count: number }>('/products/load-json', {
      method: 'POST',
      body: JSON.stringify({ path }),
    }),

  // ============ Tasks ============
  getTasks: (signal?: AbortSignal) =>
    request<TasksResponse>('/tasks', { signal }),

  createTask: (task: {
    site_type?: string
    site_name: string
    site_url: string
    monitor_input: string
    sizes?: string[]
    mode?: string
    profile_id?: string
    proxy_group_id?: string
    monitor_delay?: number
    retry_delay?: number
  }) =>
    request<{ id: string; message: string }>('/tasks', {
      method: 'POST',
      body: JSON.stringify(task),
    }),

  startTask: (id: string) =>
    request<{ message: string }>(`/tasks/${id}/start`, { method: 'POST' }),

  stopTask: (id: string) =>
    request<{ message: string }>(`/tasks/${id}/stop`, { method: 'POST' }),

  deleteTask: (id: string) =>
    request<{ message: string }>(`/tasks/${id}`, { method: 'DELETE' }),

  startAllTasks: () =>
    request<{ message: string }>('/tasks/start-all', { method: 'POST' }),

  stopAllTasks: () =>
    request<{ message: string }>('/tasks/stop-all', { method: 'POST' }),

  // ============ Profiles ============
  getProfiles: (signal?: AbortSignal) =>
    request<ProfilesResponse>('/profiles', { signal }),

  createProfile: (profile: {
    name: string
    email: string
    phone?: string
    shipping_first_name: string
    shipping_last_name: string
    shipping_address1: string
    shipping_address2?: string
    shipping_city: string
    shipping_state: string
    shipping_zip: string
    shipping_country?: string
    billing_same_as_shipping?: boolean
    card_holder: string
    card_number: string
    card_expiry: string
    card_cvv: string
  }) =>
    request<{ id: string; message: string }>('/profiles', {
      method: 'POST',
      body: JSON.stringify(profile),
    }),

  deleteProfile: (id: string) =>
    request<{ message: string }>(`/profiles/${id}`, { method: 'DELETE' }),

  importProfiles: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE}/profiles/import`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new ApiRequestError({
        code: `HTTP_${response.status}`,
        message: 'Import failed',
        retryable: false,
      }, response.status)
    }

    return response.json() as Promise<{ message: string; count: number }>
  },

  // ============ Proxies ============
  getProxies: (signal?: AbortSignal) =>
    request<{ stats: unknown; groups: string[] }>('/proxies', { signal }),

  createProxyGroup: (name: string, proxies: string) =>
    request<{ group: string; count: number }>('/proxies/groups', {
      method: 'POST',
      body: JSON.stringify({ name, proxies }),
    }),

  testProxies: (groupId?: string) =>
    request<unknown>('/proxies/test', {
      method: 'POST',
      body: JSON.stringify({ group_id: groupId }),
    }),

  // ============ Intelligence ============
  getTrending: (signal?: AbortSignal) =>
    request<{ trending: unknown[] }>('/intelligence/trending', { signal }),

  researchProduct: (name: string, sku: string, retailPrice: number) =>
    request<{
      name: string
      sku: string
      keywords: string[]
      sites: string[]
      hype_score: number
      profit: number | null
    }>(`/intelligence/research?name=${encodeURIComponent(name)}&sku=${encodeURIComponent(sku)}&retail_price=${retailPrice}`, {
      method: 'POST',
    }),

  // ============ Captcha ============
  getCaptchaBalances: (signal?: AbortSignal) =>
    request<Record<string, number>>('/captcha/balances', { signal }),

  // ============ Quick Tasks ============
  createQuickTask: (data: {
    url: string
    sizes?: string[]
    quantity?: number
    mode?: string
    profile_id?: string
    proxy_group_id?: string
    auto_start?: boolean
  }) =>
    request<{ id: string; message: string }>('/tasks/quick', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  createQuickTasksBatch: (urls: string[], sizes?: string[], mode?: string, autoStart?: boolean) =>
    request<{ ids: string[]; message: string }>('/tasks/quick-batch', {
      method: 'POST',
      body: JSON.stringify({ urls, sizes, mode, auto_start: autoStart }),
    }),

  // ============ Shopify Stores ============
  getShopifyStores: (signal?: AbortSignal) =>
    request<{ stores: unknown[] }>('/monitors/shopify/stores', { signal }),

  updateShopifyStore: (storeId: string, updates: Record<string, unknown>) =>
    request<{ message: string }>(`/monitors/shopify/stores/${storeId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }),

  deleteShopifyStore: (storeId: string) =>
    request<{ message: string }>(`/monitors/shopify/stores/${storeId}`, { method: 'DELETE' }),

  // ============ Restock History ============
  getRestockHistory: (hours: number = 24, limit: number = 50, signal?: AbortSignal) =>
    request<{ history: unknown[] }>(`/monitors/restock-history?hours=${hours}&limit=${limit}`, { signal }),

  getRestockStats: (signal?: AbortSignal) =>
    request<{ stats: unknown }>('/monitors/restock-stats', { signal }),

  getRestockPatterns: (days: number = 7, signal?: AbortSignal) =>
    request<{ patterns: unknown[] }>(`/monitors/restock-patterns?days=${days}`, { signal }),

  // ============ Generic ============
  get: <T = unknown>(endpoint: string, signal?: AbortSignal) =>
    request<T>(endpoint, { signal }),

  post: <T = unknown>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),
}

// ============ WebSocket ============

export class EventWebSocket {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private listeners: Map<string, Set<(data: unknown) => void>> = new Map()
  private lastMessageTime: number = 0

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  get lastUpdate(): number {
    return this.lastMessageTime
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/events`

    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('[WebSocket] Connected')
      this.reconnectAttempts = 0
      this.lastMessageTime = Date.now()
    }

    this.ws.onmessage = (event) => {
      this.lastMessageTime = Date.now()

      try {
        const data = JSON.parse(event.data)
        if (data.type === 'heartbeat') return

        const listeners = this.listeners.get(data.type) || new Set()
        listeners.forEach(callback => callback(data.data))

        // Notify 'all' listeners
        const allListeners = this.listeners.get('all') || new Set()
        allListeners.forEach(callback => callback(data))
      } catch (e) {
        console.error('[WebSocket] Parse error:', e)
      }
    }

    this.ws.onclose = () => {
      console.log('[WebSocket] Disconnected')

      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000)
        this.reconnectAttempts++
        setTimeout(() => this.connect(), delay)
      }
    }

    this.ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error)
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  on(eventType: string, callback: (data: unknown) => void) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set())
    }
    this.listeners.get(eventType)!.add(callback)
    return () => this.off(eventType, callback)
  }

  off(eventType: string, callback: (data: unknown) => void) {
    this.listeners.get(eventType)?.delete(callback)
  }

  ping() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send('ping')
    }
  }
}

export const eventWs = new EventWebSocket()
