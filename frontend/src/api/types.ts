/**
 * API Types for Phantom Bot
 * All TypeScript interfaces for backend responses
 */

// ============ Error Types ============

export interface ApiError {
    code: string
    message: string
    details?: Record<string, unknown>
    retryable: boolean
}

// ============ Engine Types ============

export interface EngineStatus {
    running: boolean
    tasks: {
        total: number
        running: number
        idle: number
        success: number
        failed: number
    }
    proxies: {
        total: number
        good: number
        slow: number
        bad: number
        banned: number
        untested: number
        avg_response_time: number
        total_requests: number
        success_rate?: number
    }
    profiles?: {
        total: number
    }
}

// ============ Monitor Types ============

export interface ShopifyStoreStats {
    name: string
    url: string
    products_found: number
    requests_made: number
    errors: number
    last_check: string | null
    rate_limited: boolean
}

export interface MonitorStatus {
    running: boolean
    total_products_found: number
    high_priority_found: number
    tasks_created: number
    events_stored: number
    curated_products: {
        total: number
        enabled: number
        high_priority: number
        avg_profit: number
    }
    shopify?: {
        running: boolean
        store_count: number
        total_products_found: number
        stores: Record<string, ShopifyStoreStats>
    }
    footsites?: {
        running: boolean
        sites: string[]
        keywords: string[]
    }
}

export interface MonitorEvent {
    id?: string
    type: 'new_product' | 'restock' | 'price_drop'
    source: 'shopify' | 'footsite' | 'snkrs'
    store: string
    product: string
    url: string
    sizes: string[]
    price: number
    matched: string | null
    confidence: number
    priority: 'high' | 'medium' | 'low'
    profit?: number | null
    timestamp: string
    imageUrl?: string
}

export interface MonitorEventsResponse {
    count: number
    events: MonitorEvent[]
}

// ============ Analytics Types ============

export interface CheckoutAnalytics {
    total_tasks: number
    success: number
    failed: number
    pending: number
    success_rate: number
    by_site: Record<string, {
        success: number
        failed: number
        total: number
    }>
}

export interface RateLimitStats {
    stores: Record<string, {
        url: string
        delay_ms: number
        request_count: number
        rate_limited: boolean
        last_request: string | null
    }>
}

// ============ Task Types ============

export interface Task {
    id: string
    status: string
    status_message: string
    site_name: string
    site_url: string
    product_name?: string
    product_url?: string
    size?: string
    is_running: boolean
    created_at: string
    result?: {
        success: boolean
        message: string
        order_number?: string
        checkout_time?: number
    }
}

export interface TasksResponse {
    tasks: Task[]
    stats: {
        total: number
        running: number
        idle: number
        success: number
        failed: number
    }
}

// ============ Profile Types ============

export interface Profile {
    id: string
    name: string
    email: string
    phone?: string
    shipping_first_name: string
    shipping_last_name: string
    shipping_address1: string
    shipping_city: string
    shipping_state: string
    shipping_zip: string
    shipping_country: string
    billing_same_as_shipping: boolean
}

export interface ProfilesResponse {
    profiles: Profile[]
    groups: Array<{
        id: string
        name: string
        color: string
    }>
}

// ============ Product Types ============

export interface CuratedProduct {
    id: string
    name: string
    sku: string
    style_code?: string
    brand?: string
    retail_price: number
    current_price: number
    profit_dollar: number
    profit_ratio: number
    priority: 'high' | 'medium' | 'low'
    enabled: boolean
    positive_keywords: string[]
    negative_keywords: string[]
    sizes?: string[]
    search_string?: string
}

export interface CuratedProductsResponse {
    stats: {
        total: number
        enabled: number
        high_priority: number
        avg_profit: number
    }
    products: CuratedProduct[]
}

// ============ WebSocket Types ============

export type WebSocketMessageType =
    | 'monitor_event'
    | 'task_update'
    | 'status_update'
    | 'heartbeat'

export interface WebSocketMessage<T = unknown> {
    type: WebSocketMessageType
    data?: T
}

export interface StatusUpdateData {
    monitorsRunning?: boolean
    engineRunning?: boolean
    stats?: {
        totalProductsFound?: number
        highPriorityFound?: number
        checkouts?: number
        declines?: number
    }
    shopifyStores?: Record<string, ShopifyStoreStats>
}
