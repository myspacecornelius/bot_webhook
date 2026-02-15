import { useState } from "react";
import { ChevronLeft, ChevronRight, Calendar } from "lucide-react";
import { cn, formatPrice } from "../lib/utils";

interface CopData {
  date: string; // YYYY-MM-DD
  count: number;
  revenue: number;
  products: Array<{
    name: string;
    size: string;
    price: number;
    profit: number;
  }>;
}

interface CopCalendarProps {
  restockData?: unknown[];
  isLoading?: boolean;
}

// Transform raw restock API data into CopData format
function transformRestockData(raw: unknown[]): CopData[] {
  if (!raw || raw.length === 0) return [];

  // Group by date
  const byDate = new Map<string, CopData>();
  for (const item of raw) {
    const record = item as Record<string, unknown>;
    const timestamp =
      (record.timestamp as string) || (record.date as string) || "";
    const dateStr = timestamp.slice(0, 10); // YYYY-MM-DD
    if (!dateStr) continue;

    const existing = byDate.get(dateStr) || {
      date: dateStr,
      count: 0,
      revenue: 0,
      products: [],
    };
    existing.count += 1;
    const price = Number(record.price || record.retail_price || 0);
    const profit = Number(record.profit || record.estimated_profit || 0);
    existing.revenue += price;
    existing.products.push({
      name: String(record.product || record.name || "Unknown"),
      size: String(record.size || "N/A"),
      price,
      profit,
    });
    byDate.set(dateStr, existing);
  }

  return Array.from(byDate.values());
}

export function CopCalendar({
  restockData,
  isLoading: _isLoading = false,
}: CopCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [hoveredDate, setHoveredDate] = useState<string | null>(null);

  const copData = transformRestockData(restockData || []);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Get days in month
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startingDayOfWeek = firstDay.getDay();

  // Navigate months
  const previousMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  // Get cop data for a specific date
  const getCopDataForDate = (day: number): CopData | undefined => {
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    return copData.find((d) => d.date === dateStr);
  };

  // Get intensity class based on cop count
  const getIntensityClass = (count: number) => {
    if (count === 0) return "bg-[var(--surface2)] hover:bg-[var(--surface2)]";
    if (count === 1)
      return "bg-green-900/30 hover:bg-green-900/40 border-green-500/30";
    if (count === 2)
      return "bg-green-700/40 hover:bg-green-700/50 border-green-500/50";
    return "bg-green-500/60 hover:bg-green-500/70 border-green-400";
  };

  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  // Generate calendar grid
  const calendarDays = [];

  // Empty cells before first day
  for (let i = 0; i < startingDayOfWeek; i++) {
    calendarDays.push(<div key={`empty-${i}`} className="aspect-square" />);
  }

  // Days of month
  for (let day = 1; day <= daysInMonth; day++) {
    const copData = getCopDataForDate(day);
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const isToday =
      new Date().toDateString() === new Date(year, month, day).toDateString();

    calendarDays.push(
      <div
        key={day}
        className="relative"
        onMouseEnter={() => copData && setHoveredDate(dateStr)}
        onMouseLeave={() => setHoveredDate(null)}
      >
        <div
          className={cn(
            "aspect-square rounded-lg border transition-all cursor-pointer flex flex-col items-center justify-center",
            getIntensityClass(copData?.count || 0),
            isToday &&
              "ring-2 ring-moss-500 ring-offset-2 ring-offset-[#0a0a0f]",
          )}
        >
          <span
            className={cn(
              "text-sm font-medium",
              copData ? "text-[var(--text)]" : "text-[var(--muted)]",
            )}
          >
            {day}
          </span>
          {copData && (
            <span className="text-xs text-green-300 font-bold">
              {copData.count}
            </span>
          )}
        </div>

        {/* Hover Tooltip */}
        {hoveredDate === dateStr && copData && (
          <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-[var(--surface)] border border-green-500/30 rounded-lg shadow-2xl animate-fade-in">
            <div className="text-xs text-[var(--muted)] mb-2">{dateStr}</div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-[var(--text)]">
                {copData.count} Checkouts
              </span>
              <span className="text-sm font-bold text-green-400">
                {formatPrice(copData.revenue)}
              </span>
            </div>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {copData.products.map((product, i) => (
                <div
                  key={i}
                  className="text-xs text-[var(--muted)] flex items-center justify-between"
                >
                  <span className="truncate flex-1">{product.name}</span>
                  <span className="text-green-400 ml-2">
                    +{formatPrice(product.profit)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>,
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)] flex items-center gap-3">
            <Calendar className="w-7 h-7 text-green-400" />
            Cop Calendar
          </h1>
          <p className="text-[var(--muted)] text-sm mt-1">
            Track your successful checkouts over time
          </p>
        </div>

        {/* Month Navigation */}
        <div className="flex items-center gap-4">
          <button
            onClick={previousMonth}
            className="p-2 rounded-lg bg-[var(--surface2)] hover:bg-[var(--surface2)] transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-[var(--muted)]" />
          </button>
          <span className="text-lg font-semibold text-[var(--text)] min-w-[180px] text-center">
            {monthNames[month]} {year}
          </span>
          <button
            onClick={nextMonth}
            className="p-2 rounded-lg bg-[var(--surface2)] hover:bg-[var(--surface2)] transition-colors"
          >
            <ChevronRight className="w-5 h-5 text-[var(--muted)]" />
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mb-6 text-xs text-[var(--muted)]">
        <span>Less</span>
        <div className="flex gap-1">
          <div className="w-4 h-4 rounded bg-[var(--surface2)]" />
          <div className="w-4 h-4 rounded bg-green-900/30 border border-green-500/30" />
          <div className="w-4 h-4 rounded bg-green-700/40 border border-green-500/50" />
          <div className="w-4 h-4 rounded bg-green-500/60 border border-green-400" />
        </div>
        <span>More</span>
      </div>

      {/* Calendar Grid */}
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-6">
        {/* Day Headers */}
        <div className="grid grid-cols-7 gap-2 mb-2">
          {dayNames.map((day) => (
            <div
              key={day}
              className="text-center text-xs font-medium text-[var(--muted)] py-2"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Calendar Days */}
        <div className="grid grid-cols-7 gap-2">{calendarDays}</div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-3 gap-4 mt-6">
        <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
          <p className="text-sm text-[var(--muted)] mb-1">Total Checkouts</p>
          <p className="text-2xl font-bold text-[var(--text)]">
            {copData.reduce((sum: number, d: CopData) => sum + d.count, 0)}
          </p>
        </div>
        <div className="p-4 rounded-xl bg-[var(--surface)] border border-green-500/30">
          <p className="text-sm text-[var(--muted)] mb-1">Total Revenue</p>
          <p className="text-2xl font-bold text-green-400">
            {formatPrice(
              copData.reduce((sum: number, d: CopData) => sum + d.revenue, 0),
            )}
          </p>
        </div>
        <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
          <p className="text-sm text-[var(--muted)] mb-1">Avg Per Checkout</p>
          <p className="text-2xl font-bold text-[var(--text)]">
            {copData.length > 0
              ? formatPrice(
                  copData.reduce(
                    (sum: number, d: CopData) => sum + d.revenue,
                    0,
                  ) /
                    copData.reduce(
                      (sum: number, d: CopData) => sum + d.count,
                      0,
                    ),
                )
              : "$0"}
          </p>
        </div>
      </div>
    </div>
  );
}
