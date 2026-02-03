/**
 * SmartTooltip Component
 * Displays contextual help from the settings metadata registry.
 */

import { useState, useRef, useEffect } from 'react'
import { HelpCircle, ExternalLink, AlertTriangle, Lightbulb } from 'lucide-react'
import { getSettingMetadata, type SettingMetadata } from '../lib/settingsMetadata'
import { cn } from '../lib/utils'

interface SmartTooltipProps {
  settingId: string
  children: React.ReactNode
  position?: 'top' | 'bottom' | 'left' | 'right'
  showIcon?: boolean
  className?: string
}

export function SmartTooltip({ 
  settingId, 
  children, 
  position = 'top',
  showIcon = true,
  className 
}: SmartTooltipProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const metadata = getSettingMetadata(settingId)

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => setIsOpen(true), 300)
  }

  const handleMouseLeave = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    if (!expanded) setIsOpen(false)
  }

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [])

  if (!metadata) {
    return <>{children}</>
  }

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2'
  }

  return (
    <div 
      className={cn("relative inline-flex items-center gap-1", className)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {showIcon && (
        <HelpCircle className="w-3.5 h-3.5 text-[var(--muted)] cursor-help hover:text-[var(--primary)]" />
      )}
      
      {isOpen && (
        <TooltipPanel 
          metadata={metadata} 
          position={position}
          positionClasses={positionClasses}
          expanded={expanded}
          onExpand={() => setExpanded(true)}
          onClose={() => { setIsOpen(false); setExpanded(false) }}
        />
      )}
    </div>
  )
}

interface TooltipPanelProps {
  metadata: SettingMetadata
  position: 'top' | 'bottom' | 'left' | 'right'
  positionClasses: Record<string, string>
  expanded: boolean
  onExpand: () => void
  onClose: () => void
}

function TooltipPanel({ metadata, position, positionClasses, expanded, onExpand, onClose }: TooltipPanelProps) {
  return (
    <div 
      className={cn(
        "absolute z-50 w-80 p-4 rounded-xl shadow-xl border",
        "bg-[var(--surface)] border-[var(--border)]",
        "animate-in fade-in-0 zoom-in-95 duration-200",
        positionClasses[position]
      )}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-semibold text-[var(--text)]">{metadata.label}</h4>
        <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--surface2)] text-[var(--muted)]">
          {metadata.category}
        </span>
      </div>

      {/* Short Help */}
      <p className="text-sm text-[var(--muted)] mb-3">{metadata.shortHelp}</p>

      {/* Expanded Content */}
      {expanded ? (
        <div className="space-y-3 text-sm">
          {/* Long Help */}
          <div>
            <p className="text-[var(--text)]">{metadata.longHelp}</p>
          </div>

          {/* When to Use */}
          <div className="p-2 rounded-lg bg-[var(--primary)]/10 border border-[var(--primary)]/20">
            <div className="flex items-center gap-2 mb-1">
              <Lightbulb className="w-4 h-4 text-[var(--primary)]" />
              <span className="font-medium text-[var(--primary)]">When to use</span>
            </div>
            <p className="text-[var(--text)] text-xs">{metadata.whenToUse}</p>
          </div>

          {/* Tradeoffs */}
          <div className="p-2 rounded-lg bg-[var(--warning)]/10 border border-[var(--warning)]/20">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-4 h-4 text-[var(--warning)]" />
              <span className="font-medium text-[var(--warning)]">Tradeoffs</span>
            </div>
            <p className="text-[var(--text)] text-xs">{metadata.tradeoffs}</p>
          </div>

          {/* Common Mistakes */}
          {metadata.commonMistakes.length > 0 && (
            <div>
              <span className="font-medium text-[var(--danger)] text-xs">Common mistakes:</span>
              <ul className="mt-1 space-y-1">
                {metadata.commonMistakes.map((mistake, i) => (
                  <li key={i} className="text-xs text-[var(--muted)] flex items-start gap-1">
                    <span className="text-[var(--danger)]">•</span>
                    {mistake}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Default */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-[var(--muted)]">Default:</span>
            <code className="px-2 py-0.5 bg-[var(--surface2)] rounded text-[var(--text)]">
              {metadata.defaults}
            </code>
          </div>

          {/* Learn More */}
          <a 
            href={metadata.learnMorePath}
            className="flex items-center gap-1 text-xs text-[var(--info)] hover:underline"
          >
            <ExternalLink className="w-3 h-3" />
            Learn more in docs
          </a>

          <button
            onClick={onClose}
            className="w-full mt-2 py-1.5 text-xs text-[var(--muted)] hover:text-[var(--text)] transition-colors"
          >
            Close
          </button>
        </div>
      ) : (
        <button
          onClick={onExpand}
          className="flex items-center gap-1 text-xs text-[var(--info)] hover:underline"
        >
          <ExternalLink className="w-3 h-3" />
          Show more details
        </button>
      )}
    </div>
  )
}

/**
 * Inline tooltip label - combines label with tooltip
 */
export function TooltipLabel({ 
  settingId, 
  children,
  className 
}: { 
  settingId: string
  children: React.ReactNode
  className?: string 
}) {
  return (
    <SmartTooltip settingId={settingId} className={className}>
      <span className="text-sm font-medium text-[var(--muted)]">{children}</span>
    </SmartTooltip>
  )
}
