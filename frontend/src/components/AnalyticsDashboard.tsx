/**
 * Analytics Dashboard
 * Combines checkout analytics stats with CopCalendar heatmap.
 * All data from live API — no hardcoded arrays.
 */

import { useState } from "react";
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  ShoppingBag,
  Calendar,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { cn } from "../lib/utils";
import { useCheckoutAnalytics, useRestockHistory } from "../hooks/useQueries";
import { CopCalendar } from "./CopCalendar";

// ============ Stat Card ============

function AnalyticStat({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{
    className?: string;
    style?: React.CSSProperties;
  }>;
  color: string;
}) {
  return (
    <div className="card-elevated rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span
          className="text-sm font-medium"
          style={{ color: "var(--text-secondary)" }}
        >
          {title}
        </span>
        <div className="p-2 rounded-lg" style={{ background: `${color}20` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
      </div>
      <p className="text-3xl font-bold text-white tracking-tight">
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
      {subtitle && (
        <p className="text-xs mt-1" style={{ color: "var(--muted)" }}>
          {subtitle}
        </p>
      )}
    </div>
  );
}

// ============ Site Breakdown Table ============

function SiteBreakdown({
  bySite,
}: {
  bySite: Record<string, { success: number; failed: number; total: number }>;
}) {
  const entries = Object.entries(bySite);
  if (entries.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          No site data yet
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--border)]">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[var(--surface2)]">
            <th
              className="text-left px-4 py-3 font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              Site
            </th>
            <th
              className="text-right px-4 py-3 font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              Success
            </th>
            <th
              className="text-right px-4 py-3 font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              Failed
            </th>
            <th
              className="text-right px-4 py-3 font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              Rate
            </th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([site, data]) => {
            const rate =
              data.total > 0
                ? ((data.success / data.total) * 100).toFixed(1)
                : "0.0";
            return (
              <tr
                key={site}
                className="border-t border-[var(--border)] hover:bg-[var(--surface2)] transition-colors"
              >
                <td className="px-4 py-3 font-medium text-white">{site}</td>
                <td
                  className="px-4 py-3 text-right"
                  style={{ color: "var(--success)" }}
                >
                  {data.success}
                </td>
                <td
                  className="px-4 py-3 text-right"
                  style={{ color: "var(--danger)" }}
                >
                  {data.failed}
                </td>
                <td className="px-4 py-3 text-right font-semibold text-white">
                  {rate}%
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ============ Main Component ============

export function AnalyticsDashboard() {
  const [activeTab, setActiveTab] = useState<"overview" | "calendar">(
    "overview",
  );

  const {
    data: checkout,
    isLoading: checkoutLoading,
    error: checkoutError,
    refetch: refetchCheckout,
  } = useCheckoutAnalytics();
  const { data: restockData, isLoading: restockLoading } = useRestockHistory();

  const tabs = [
    { id: "overview" as const, label: "Overview", icon: BarChart3 },
    { id: "calendar" as const, label: "Cop Calendar", icon: Calendar },
  ];

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            Analytics
          </h1>
          <p style={{ color: "var(--text-secondary)" }}>
            Performance metrics and checkout history
          </p>
        </div>

        <div className="flex items-center gap-2 bg-[var(--surface2)] p-1 rounded-xl border border-[var(--border)]">
          {tabs.map((tab) => {
            const TabIcon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                  activeTab === tab.id
                    ? "bg-[var(--primary)] text-white shadow-md"
                    : "text-[var(--muted)] hover:text-white",
                )}
              >
                <TabIcon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {activeTab === "overview" ? (
        <>
          {/* Stats Grid */}
          {checkoutLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 skeleton rounded-xl" />
              ))}
            </div>
          ) : checkoutError ? (
            <div className="card-elevated rounded-xl p-8 text-center">
              <p className="text-sm" style={{ color: "var(--danger)" }}>
                Failed to load analytics
              </p>
              <button
                onClick={refetchCheckout}
                className="mt-3 flex items-center gap-2 mx-auto px-4 py-2 rounded-lg bg-[var(--surface2)] text-sm hover:bg-[var(--surface3)] transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Retry
              </button>
            </div>
          ) : checkout ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                <AnalyticStat
                  title="Total Tasks"
                  value={checkout.total_tasks}
                  subtitle="All checkout attempts"
                  icon={ShoppingBag}
                  color="hsl(260 65% 62%)"
                />
                <AnalyticStat
                  title="Successful"
                  value={checkout.success}
                  subtitle={`${checkout.success_rate.toFixed(1)}% success rate`}
                  icon={TrendingUp}
                  color="hsl(160 60% 45%)"
                />
                <AnalyticStat
                  title="Failed"
                  value={checkout.failed}
                  subtitle="Declined or errored"
                  icon={DollarSign}
                  color="hsl(0 72% 56%)"
                />
                <AnalyticStat
                  title="Pending"
                  value={checkout.pending}
                  subtitle="In progress"
                  icon={Loader2}
                  color="hsl(38 92% 60%)"
                />
              </div>

              {/* Site Breakdown */}
              <div>
                <h2 className="text-lg font-semibold text-white mb-4">
                  Performance by Site
                </h2>
                <SiteBreakdown bySite={checkout.by_site} />
              </div>
            </>
          ) : null}
        </>
      ) : (
        /* Calendar Tab */
        <CopCalendar
          restockData={restockData?.history}
          isLoading={restockLoading}
        />
      )}
    </div>
  );
}
