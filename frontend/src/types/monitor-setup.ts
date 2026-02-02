export type MonitorSetup = {
  id: string
  name: string
  description?: string
  pinned: boolean
  createdAt: number
  updatedAt: number
  version: 1

  filters: {
    enabled?: boolean | "all"
    sources?: string[]
    tags?: string[]
    keyword?: string
    negativeKeyword?: string
    status?: ("healthy" | "degraded" | "error")[]
    lastHitRange?: { from?: number; to?: number }
  }

  sort: { 
    by: "lastHit" | "hitCount" | "createdAt" | "name"
    dir: "asc" | "desc" 
  }

  columns?: {
    visible: string[]
    widths?: Record<string, number>
  }

  ui?: {
    grouping?: "none" | "source" | "tag"
    density?: "comfortable" | "compact"
  }
}

export type MonitorHealth = "healthy" | "degraded" | "error"

export type Monitor = {
  id: string
  name: string
  source: string
  query: string
  keywords: string[]
  enabled: boolean
  tags: string[]
  status: MonitorHealth
  lastHit?: number
  hitCount: number
  latency: number
  errorCount: number
  createdAt: number
}
