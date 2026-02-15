/**
 * Command Center Dashboard
 * Premium dark theme with real-time data and glassmorphism
 */

import { useState, useMemo, useCallback, useEffect } from "react";
import { Responsive, WidthProvider } from "react-grid-layout/legacy";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";

import {
  Play,
  Pause,
  Zap,
  TrendingUp,
  ShoppingBag,
  AlertTriangle,
  Activity,
  DollarSign,
  Target,
  Loader2,
  Wifi,
  WifiOff,
  RefreshCw,
  ExternalLink,
  Clock,
  Sparkles,
  Lock,
  Unlock,
  RotateCcw,
} from "lucide-react";
import { useStore } from "../store/useStore";
import { api } from "../api/client";
import { cn, formatPrice, formatRelativeTime } from "../lib/utils";
import { toast } from "./ui/Toast";
import { ConfirmModal } from "./ui/ConfirmModal";
import { ProductDetailsDrawer } from "./ui/ProductDetailsDrawer";
import { useWebSocket } from "../hooks/useWebSocket";
import {
  useEngineStatus,
  useMonitorStatus,
  useCheckoutAnalytics,
  useTimeAgo,
} from "../hooks/useQueries";

const ResponsiveGridLayout = WidthProvider(Responsive);

// Default Layouts
const defaultLayouts = {
  lg: [
    { i: "stat-products", x: 0, y: 0, w: 3, h: 4 },
    { i: "stat-high-priority", x: 3, y: 0, w: 3, h: 4 },
    { i: "stat-checkouts", x: 6, y: 0, w: 3, h: 4 },
    { i: "stat-declines", x: 9, y: 0, w: 3, h: 4 },
    { i: "live-feed", x: 0, y: 4, w: 6, h: 10 },
    { i: "store-health", x: 6, y: 4, w: 6, h: 10 },
  ],
  md: [
    { i: "stat-products", x: 0, y: 0, w: 5, h: 4 },
    { i: "stat-high-priority", x: 5, y: 0, w: 5, h: 4 },
    { i: "stat-checkouts", x: 0, y: 4, w: 5, h: 4 },
    { i: "stat-declines", x: 5, y: 4, w: 5, h: 4 },
    { i: "live-feed", x: 0, y: 8, w: 10, h: 10 },
    { i: "store-health", x: 0, y: 18, w: 10, h: 10 },
  ],
  sm: [
    { i: "stat-products", x: 0, y: 0, w: 6, h: 4 },
    { i: "stat-high-priority", x: 0, y: 4, w: 6, h: 4 },
    { i: "stat-checkouts", x: 0, y: 8, w: 6, h: 4 },
    { i: "stat-declines", x: 0, y: 12, w: 6, h: 4 },
    { i: "live-feed", x: 0, y: 16, w: 6, h: 10 },
    { i: "store-health", x: 0, y: 26, w: 6, h: 10 },
  ],
};

// ============ Stat Card Component ============

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  tooltip?: string;
  icon: React.ComponentType<{ className?: string }>;
  trend?: number;
  gradient: "purple" | "blue" | "green" | "red";
  loading?: boolean;
  error?: boolean;
  onRetry?: () => void;
  dragHandleProps?: any;
}

function StatCard({
  title,
  value,
  subtitle,
  tooltip,
  icon: Icon,
  trend,
  gradient,
  loading = false,
  error = false,
  onRetry,
  dragHandleProps,
  ...props
}: StatCardProps & React.HTMLAttributes<HTMLDivElement>) {
  const accentColors = {
    purple: {
      bg: "hsl(260 65% 62% / 0.12)",
      border: "hsl(260 65% 62% / 0.25)",
      icon: "hsl(260 65% 70%)",
      glow: "hsl(260 65% 62% / 0.15)",
    },
    blue: {
      bg: "hsl(215 85% 58% / 0.12)",
      border: "hsl(215 85% 58% / 0.25)",
      icon: "hsl(215 85% 68%)",
      glow: "hsl(215 85% 58% / 0.15)",
    },
    green: {
      bg: "hsl(160 60% 45% / 0.12)",
      border: "hsl(160 60% 45% / 0.25)",
      icon: "hsl(160 60% 55%)",
      glow: "hsl(160 60% 45% / 0.15)",
    },
    red: {
      bg: "hsl(0 72% 56% / 0.12)",
      border: "hsl(0 72% 56% / 0.25)",
      icon: "hsl(0 72% 66%)",
      glow: "hsl(0 72% 56% / 0.15)",
    },
  };

  const colors = accentColors[gradient];

  return (
    <div
      {...props}
      className={cn(
        "group relative p-6 rounded-2xl card-elevated overflow-hidden h-full flex flex-col",
        props.className,
      )}
      title={tooltip}
      style={{
        background: `linear-gradient(135deg, ${colors.bg}, transparent)`,
        borderColor: colors.border,
        ...props.style,
      }}
    >
      {/* Drag Handle Overlay (optional, creates draggable area) */}
      {dragHandleProps && (
        <div
          {...dragHandleProps}
          className="absolute top-2 right-2 p-1 opacity-0 group-hover:opacity-50 cursor-grab active:cursor-grabbing"
        >
          {/* Draggable Icon could go here, but entire card is draggable by default in RGL unless specified */}
        </div>
      )}

      {/* Subtle glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

      <div className="relative flex items-start justify-between flex-1">
        <div className="space-y-1.5 flex-1">
          <p
            className="text-sm font-medium"
            style={{ color: "var(--text-secondary)" }}
          >
            {title}
          </p>

          {error ? (
            <div className="flex items-center gap-2 mt-2">
              <span className="text-sm" style={{ color: "var(--danger)" }}>
                Failed to load
              </span>
              {onRetry && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRetry();
                  }}
                  className="p-1.5 rounded-lg hover:bg-rose-500/20 text-rose-400 transition-colors"
                  aria-label="Retry"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ) : loading ? (
            <div className="h-10 w-24 skeleton mt-1" />
          ) : (
            <p className="text-4xl font-bold text-white tracking-tight">
              {typeof value === "number" ? value.toLocaleString() : value}
            </p>
          )}

          {subtitle && !error && (
            <p className="text-xs mt-1" style={{ color: "var(--muted)" }}>
              {subtitle}
            </p>
          )}
        </div>

        <div
          className="p-3.5 rounded-xl bg-white/5 border border-white/10 transition-all duration-300 group-hover:bg-white/10 group-hover:scale-110"
          style={{ color: colors.icon }}
        >
          <Icon className="w-5 h-5" />
        </div>
      </div>

      {trend !== undefined && !loading && !error && (
        <div
          className="flex items-center gap-1.5 mt-auto text-xs font-medium pt-4"
          style={{ color: trend >= 0 ? "var(--success)" : "var(--danger)" }}
        >
          <TrendingUp
            className={cn("w-3.5 h-3.5", trend < 0 && "rotate-180")}
          />
          <span>
            {trend >= 0 ? "+" : ""}
            {trend}% from last hour
          </span>
        </div>
      )}
    </div>
  );
}

// ============ Live Feed Component ============

interface MonitorEvent {
  id?: string;
  type: "new_product" | "restock" | "price_drop";
  source: "shopify" | "footsite" | "snkrs";
  store: string;
  product: string;
  url: string;
  sizes: string[];
  price: number;
  matched: string | null;
  confidence: number;
  priority: "high" | "medium" | "low";
  profit?: number | null;
  timestamp: string;
  imageUrl?: string;
}

function LiveFeed({
  onSelectEvent,
  ...props
}: {
  onSelectEvent: (event: MonitorEvent) => void;
} & React.HTMLAttributes<HTMLDivElement>) {
  const { events, isConnected } = useStore();
  const recentEvents = useMemo(() => events.slice(0, 8), [events]);

  return (
    <div
      {...props}
      className={cn(
        "card-elevated rounded-2xl overflow-hidden h-full flex flex-col",
        props.className,
      )}
    >
      <div className="flex items-center justify-between p-5 border-b border-[var(--border)] shrink-0 drag-handle cursor-grab active:cursor-grabbing">
        <h3 className="font-semibold text-white flex items-center gap-2.5">
          <div
            className="p-2 rounded-lg"
            style={{ background: "hsl(var(--accent-hue) 42% 48% / 0.15)" }}
          >
            <Activity className="w-4 h-4" style={{ color: "var(--primary)" }} />
          </div>
          Live Product Feed
        </h3>
        <div
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium",
            isConnected
              ? "bg-emerald-500/20 text-emerald-400"
              : "bg-amber-500/20 text-amber-400",
          )}
        >
          <div
            className={cn(
              "w-2 h-2 rounded-full",
              isConnected ? "bg-emerald-400 animate-pulse" : "bg-amber-400",
            )}
          />
          {isConnected ? "Live" : "Reconnecting..."}
        </div>
      </div>

      <div className="p-4 space-y-3 overflow-y-auto flex-1 custom-scrollbar">
        {recentEvents.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-zinc-800/50 flex items-center justify-center">
              <Zap className="w-8 h-8 text-zinc-600" />
            </div>
            <p className="text-sm font-medium text-zinc-400">
              No products detected yet
            </p>
            <p className="text-xs text-zinc-600 mt-1.5">
              Start monitors to see live updates
            </p>
          </div>
        ) : (
          recentEvents.map((event, i) => (
            <button
              key={event.id || `event-${i}`}
              onClick={() => onSelectEvent(event as MonitorEvent)}
              className={cn(
                "w-full text-left p-4 rounded-xl border transition-all duration-200 cursor-pointer block",
                event.priority === "high"
                  ? "bg-emerald-500/10 border-emerald-500/30 hover:border-emerald-500/50"
                  : "bg-zinc-800/50 border-zinc-700/50 hover:border-zinc-600",
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className="badge badge-purple text-[10px]">
                      {event.store}
                    </span>
                    {event.matched && (
                      <span className="badge badge-yellow text-[10px]">
                        Matched
                      </span>
                    )}
                    {event.priority === "high" && (
                      <span className="badge badge-green text-[10px]">
                        <Sparkles className="w-3 h-3 mr-1" />
                        High Priority
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-white font-medium truncate">
                    {event.product}
                  </p>
                  <div className="flex items-center gap-2.5 mt-2 text-xs text-zinc-500">
                    <span className="font-semibold text-white">
                      {formatPrice(event.price)}
                    </span>
                    <span className="text-zinc-600">•</span>
                    <span>
                      {event.sizes?.slice(0, 3).join(", ")}
                      {(event.sizes?.length ?? 0) > 3 ? "..." : ""}
                    </span>
                    <span className="text-zinc-600">•</span>
                    <span>{formatRelativeTime(event.timestamp)}</span>
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2.5 shrink-0">
                  {event.profit && event.profit > 0 && (
                    <div className="text-right">
                      <p
                        className={cn(
                          "text-sm font-bold",
                          event.profit >= 100
                            ? "text-emerald-400"
                            : event.profit >= 30
                              ? "text-amber-400"
                              : "text-zinc-400",
                        )}
                      >
                        +{formatPrice(event.profit)}
                      </p>
                      <p className="text-[10px] text-zinc-600">profit</p>
                    </div>
                  )}

                  {event.url && (
                    <a
                      href={event.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-lg bg-[var(--surface2)] hover:bg-[var(--primary)]/20 text-[var(--muted)] hover:text-[var(--primary)] transition-colors"
                      aria-label="View product"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

// ============ Store Health Component ============

function StoreHealth(props: React.HTMLAttributes<HTMLDivElement>) {
  const { data: monitorStatus, isLoading } = useMonitorStatus(true);

  const stores = useMemo(() => {
    if (!monitorStatus?.shopify?.stores) return [];
    return Object.entries(monitorStatus.shopify.stores).slice(0, 8);
  }, [monitorStatus]);

  return (
    <div
      {...props}
      className={cn(
        "card-elevated rounded-2xl overflow-hidden h-full flex flex-col",
        props.className,
      )}
    >
      <div className="flex items-center justify-between p-5 border-b border-[var(--border)] shrink-0 drag-handle cursor-grab active:cursor-grabbing">
        <h3 className="font-semibold text-white flex items-center gap-2.5">
          <div
            className="p-2 rounded-lg"
            style={{ background: "hsl(160 60% 45% / 0.15)" }}
          >
            <Target className="w-4 h-4" style={{ color: "var(--success)" }} />
          </div>
          Store Health
        </h3>
        <span className="text-xs text-zinc-500">
          {isLoading ? "..." : `${stores.length} stores`}
        </span>
      </div>

      <div className="p-4 space-y-3 overflow-y-auto flex-1 custom-scrollbar">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 skeleton" />
            ))}
          </div>
        ) : stores.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-zinc-800/50 flex items-center justify-center">
              <Target className="w-8 h-8 text-zinc-600" />
            </div>
            <p className="text-sm font-medium text-zinc-400">
              No stores configured
            </p>
            <p className="text-xs text-zinc-600 mt-1.5">
              Add stores in the Monitors tab
            </p>
          </div>
        ) : (
          stores.map(([id, store]) => (
            <div
              key={id}
              className="flex items-center justify-between p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50 hover:border-zinc-600 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "status-dot",
                    store.errors === 0
                      ? "online pulsing"
                      : store.errors < 3
                        ? "warning"
                        : "offline",
                  )}
                />
                <div>
                  <span className="text-sm font-medium text-white">
                    {store.name}
                  </span>
                  <p className="text-xs text-zinc-500">
                    {store.last_check
                      ? formatRelativeTime(store.last_check)
                      : "Not checked"}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-bold text-white">
                  {store.products_found?.toLocaleString() ?? 0}
                </p>
                <p className="text-xs text-zinc-500">products</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ============ Main Dashboard Component ============

export function Dashboard() {
  const {
    isRunning,
    setRunning,
    monitorsRunning,
    setMonitorsRunning,
    setStats,
    setShopifyStores,
    isConnected,
  } = useStore();

  useWebSocket();

  // Layout State
  const [layouts, setLayouts] = useState(() => {
    const saved = localStorage.getItem("dashboard-layout");
    return saved ? JSON.parse(saved) : defaultLayouts;
  });
  const [isDraggable, setIsDraggable] = useState(false);

  const handleLayoutChange = useCallback((_layout: any, allLayouts: any) => {
    setLayouts(allLayouts);
    localStorage.setItem("dashboard-layout", JSON.stringify(allLayouts));
  }, []);

  const resetLayout = useCallback(() => {
    setLayouts(defaultLayouts);
    localStorage.removeItem("dashboard-layout");
    toast.success("Layout Reset", "Dashboard layout restored to default");
  }, []);

  const {
    data: engineStatus,
    lastUpdated: engineLastUpdated,
    refetch: refetchEngine,
  } = useEngineStatus();

  const {
    data: monitorStatus,
    error: monitorError,
    isLoading: monitorLoading,
    refetch: refetchMonitors,
  } = useMonitorStatus();

  const {
    data: checkoutData,
    error: checkoutError,
    isLoading: checkoutLoading,
    refetch: refetchCheckouts,
  } = useCheckoutAnalytics();

  const lastUpdatedText = useTimeAgo(engineLastUpdated);

  const [showStopEngineModal, setShowStopEngineModal] = useState(false);
  const [engineActionLoading, setEngineActionLoading] = useState(false);
  const [monitorActionLoading, setMonitorActionLoading] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<MonitorEvent | null>(null);

  // Sync engine status
  useEffect(() => {
    if (engineStatus && engineStatus.running !== isRunning) {
      setRunning(engineStatus.running);
    }
  }, [engineStatus, isRunning, setRunning]);

  // Sync monitor status
  useEffect(() => {
    if (monitorStatus) {
      if (monitorStatus.running !== monitorsRunning) {
        setMonitorsRunning(monitorStatus.running);
      }
      setStats({
        totalProductsFound: monitorStatus.total_products_found,
        highPriorityFound: monitorStatus.high_priority_found,
        tasksCreated: monitorStatus.tasks_created,
      });
      if (monitorStatus.shopify?.stores) {
        const storeData: Record<string, any> = {};
        for (const [key, store] of Object.entries(
          monitorStatus.shopify.stores,
        )) {
          storeData[key] = {
            name: store.name,
            url: store.url,
            productsFound: store.products_found,
            errorCount: store.errors,
            lastCheck: store.last_check,
          };
        }
        setShopifyStores(storeData);
      }
    }
  }, [
    monitorStatus,
    monitorsRunning,
    setMonitorsRunning,
    setStats,
    setShopifyStores,
  ]);

  // Sync checkout stats
  useEffect(() => {
    if (checkoutData) {
      setStats({
        checkouts: checkoutData.success,
        declines: checkoutData.failed,
      });
    }
  }, [checkoutData, setStats]);

  const handleEngineToggle = async () => {
    if (isRunning) {
      setShowStopEngineModal(true);
    } else {
      setEngineActionLoading(true);
      try {
        await api.startEngine();
        setRunning(true);
        toast.success("Engine Started", "Bot engine is now running");
        refetchEngine();
      } catch (e) {
        console.error(e);
        toast.error("Error", "Failed to start engine");
      }
      setEngineActionLoading(false);
    }
  };

  const confirmStopEngine = async () => {
    setEngineActionLoading(true);
    try {
      await api.stopEngine();
      setRunning(false);
      setShowStopEngineModal(false);
      toast.info("Engine Stopped", "Bot engine has been stopped");
      refetchEngine();
    } catch (e) {
      console.error(e);
      toast.error("Error", "Failed to stop engine");
    }
    setEngineActionLoading(false);
  };

  const handleMonitorsToggle = async () => {
    setMonitorActionLoading(true);
    try {
      if (monitorsRunning) {
        await api.stopMonitors();
        setMonitorsRunning(false);
        toast.info("Monitors Stopped", "Product monitoring has been stopped");
      } else {
        await api.setupShopify();
        await api.startMonitors();
        setMonitorsRunning(true);
        toast.success("Monitors Started", "Now monitoring for products");
      }
      refetchMonitors();
    } catch (e) {
      console.error(e);
      toast.error("Error", "Failed to toggle monitors");
    }
    setMonitorActionLoading(false);
  };

  const totalProducts = monitorStatus?.total_products_found ?? 0;
  const highPriority = monitorStatus?.high_priority_found ?? 0;
  const checkouts = checkoutData?.success ?? 0;
  const declines = checkoutData?.failed ?? 0;

  return (
    <div className="p-8 space-y-8 animate-fade-in pb-20">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-4">
            Command Center
            <div
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-full",
                isConnected
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "bg-amber-500/20 text-amber-400",
              )}
            >
              {isConnected ? (
                <Wifi className="w-3.5 h-3.5" />
              ) : (
                <WifiOff className="w-3.5 h-3.5" />
              )}
              {isConnected ? "Live" : "Connecting..."}
            </div>
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <p className="text-zinc-400">Real-time monitoring and control</p>
            {engineLastUpdated && (
              <span className="flex items-center gap-1.5 text-xs text-zinc-500 px-2 py-1 rounded-full bg-zinc-800/50">
                <Clock className="w-3 h-3" />
                {lastUpdatedText}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Layout Controls */}
          <div className="flex items-center gap-2 mr-4 bg-[var(--surface2)] p-1 rounded-xl border border-[var(--border)]">
            <button
              onClick={() => setIsDraggable(!isDraggable)}
              className={cn(
                "p-2 rounded-lg transition-colors hover:bg-[var(--surface3)]",
                isDraggable
                  ? "text-[var(--primary)] bg-[var(--surface3)]"
                  : "text-[var(--muted)]",
              )}
              title={isDraggable ? "Lock Layout" : "Unlock Layout"}
            >
              {isDraggable ? (
                <Unlock className="w-4 h-4" />
              ) : (
                <Lock className="w-4 h-4" />
              )}
            </button>
            <button
              onClick={resetLayout}
              className="p-2 rounded-lg text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface3)] transition-colors"
              title="Reset Layout"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={handleMonitorsToggle}
            disabled={monitorActionLoading || !isRunning}
            title={!isRunning ? "Start engine first" : undefined}
            className={cn(
              "flex items-center gap-2 px-5 py-3 rounded-xl font-semibold transition-all duration-300",
              !isRunning && "opacity-40 cursor-not-allowed",
              monitorsRunning
                ? "bg-blue-500/20 text-blue-400 border border-blue-500/30 hover:bg-blue-500/30"
                : "bg-zinc-800 text-zinc-300 border border-zinc-700 hover:border-blue-500/50 hover:text-blue-400",
            )}
          >
            {monitorActionLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : monitorsRunning ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            {monitorsRunning ? "Stop Monitors" : "Start Monitors"}
          </button>

          <button
            onClick={handleEngineToggle}
            disabled={engineActionLoading}
            className={cn(
              "flex items-center gap-2 px-5 py-3 rounded-xl font-semibold transition-all duration-300",
              isRunning
                ? "bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:bg-rose-500/30"
                : "bg-gradient-to-r from-[hsl(var(--accent-hue)_42%_48%)] to-[hsl(var(--accent-hue)_50%_38%)] text-white shadow-lg shadow-[var(--primary-glow)] hover:shadow-[var(--primary-glow)] hover:-translate-y-0.5",
            )}
          >
            {engineActionLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : isRunning ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Zap className="w-5 h-5" />
            )}
            {isRunning ? "Stop Engine" : "Start Engine"}
          </button>
        </div>
      </div>

      {/* Draggable Dashboard Grid */}
      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={30}
        onLayoutChange={handleLayoutChange}
        isDraggable={isDraggable}
        isResizable={isDraggable}
        margin={[20, 20]}
        containerPadding={[0, 0]}
        draggableHandle=".drag-handle"
      >
        <div key="stat-products">
          <StatCard
            title="Products Found"
            value={totalProducts}
            subtitle="Total detections"
            tooltip="Total number of products detected by monitors since the last reset"
            icon={ShoppingBag}
            gradient="purple"
            loading={monitorLoading}
            error={!!monitorError}
            onRetry={refetchMonitors}
            className="cursor-move drag-handle" // Make entire stat card draggable
          />
        </div>
        <div key="stat-high-priority">
          <StatCard
            title="High Priority"
            value={highPriority}
            subtitle="Profitable items"
            tooltip="Products that match your keywords and exceed profit thresholds"
            icon={TrendingUp}
            gradient="green"
            loading={monitorLoading}
            error={!!monitorError}
            onRetry={refetchMonitors}
            className="cursor-move drag-handle"
          />
        </div>
        <div key="stat-checkouts">
          <StatCard
            title="Checkouts"
            value={checkouts}
            subtitle="Successful orders"
            tooltip="Completed checkout attempts - orders placed successfully"
            icon={DollarSign}
            gradient="blue"
            loading={checkoutLoading}
            error={!!checkoutError}
            onRetry={refetchCheckouts}
            className="cursor-move drag-handle"
          />
        </div>
        <div key="stat-declines">
          <StatCard
            title="Declines"
            value={declines}
            subtitle="Failed attempts"
            tooltip="Failed checkout attempts due to out-of-stock, payment issues, or anti-bot detection"
            icon={AlertTriangle}
            gradient="red"
            loading={checkoutLoading}
            error={!!checkoutError}
            onRetry={refetchCheckouts}
            className="cursor-move drag-handle"
          />
        </div>

        <div key="live-feed">
          <LiveFeed onSelectEvent={setSelectedEvent} />
        </div>

        <div key="store-health">
          <StoreHealth />
        </div>
      </ResponsiveGridLayout>

      {/* Stop Engine Modal */}
      <ConfirmModal
        isOpen={showStopEngineModal}
        onClose={() => setShowStopEngineModal(false)}
        onConfirm={confirmStopEngine}
        title="Stop Engine?"
        message="This will stop all running tasks and monitors. Any in-progress checkouts may be interrupted."
        confirmText="Stop Engine"
        cancelText="Keep Running"
        variant="danger"
        isLoading={engineActionLoading}
      />

      {/* Product Details Drawer */}
      <ProductDetailsDrawer
        isOpen={selectedEvent !== null}
        onClose={() => setSelectedEvent(null)}
        event={selectedEvent}
      />
    </div>
  );
}
