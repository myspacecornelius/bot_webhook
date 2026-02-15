export function RadarScanner() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      {/* Radar Animation */}
      <div className="relative w-32 h-32 mb-6">
        {/* Outer rings */}
        <div className="absolute inset-0 rounded-full border-2 border-[var(--info)]/30 animate-ping" />
        <div
          className="absolute inset-2 rounded-full border-2 border-[var(--info)]/30 animate-ping"
          style={{ animationDelay: "0.5s" }}
        />
        <div
          className="absolute inset-4 rounded-full border-2 border-[var(--info)]/30 animate-ping"
          style={{ animationDelay: "1s" }}
        />

        {/* Center dot */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-4 h-4 rounded-full bg-[var(--info)] animate-pulse" />
        </div>

        {/* Scanning line */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="absolute w-16 h-0.5 bg-gradient-to-r from-transparent via-moss-500 to-transparent animate-radar-sweep origin-center" />
        </div>
      </div>

      {/* Scanning Text */}
      <div className="text-center">
        <h3 className="text-xl font-semibold text-[var(--text)] mb-2 flex items-center gap-2 justify-center">
          <span className="inline-block animate-pulse">👻</span>
          Phantom Scanner Active
        </h3>
        <p className="text-[var(--muted)] mb-4">
          Monitoring stores for products...
        </p>

        {/* Scanning Code Effect */}
        <div className="font-mono text-xs text-[var(--info)]/60 space-y-1">
          <div className="animate-fade-in-out" style={{ animationDelay: "0s" }}>
            &gt; Scanning DTLR.com...
          </div>
          <div className="animate-fade-in-out" style={{ animationDelay: "1s" }}>
            &gt; Scanning ShopPalace.com...
          </div>
          <div className="animate-fade-in-out" style={{ animationDelay: "2s" }}>
            &gt; Scanning JimmyJazz.com...
          </div>
        </div>
      </div>
    </div>
  );
}
