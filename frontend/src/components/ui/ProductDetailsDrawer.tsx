/**
 * Product Details Drawer
 * Slide-out panel showing detailed product information
 */

import { useEffect, useRef } from 'react'
import {
    X,
    ExternalLink,
    Copy,
    Check,
    Clock,
    Store,
    Tag,
    DollarSign,
    Sparkles,
    ChevronDown,
    ChevronUp
} from 'lucide-react'
import { cn, formatPrice, formatRelativeTime } from '../../lib/utils'
import { useState } from 'react'

interface ProductEvent {
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

interface ProductDetailsDrawerProps {
    isOpen: boolean
    onClose: () => void
    event: ProductEvent | null
}

export function ProductDetailsDrawer({ isOpen, onClose, event }: ProductDetailsDrawerProps) {
    const drawerRef = useRef<HTMLDivElement>(null)
    const [copiedField, setCopiedField] = useState<string | null>(null)
    const [showRawPayload, setShowRawPayload] = useState(false)

    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) {
                onClose()
            }
        }
        document.addEventListener('keydown', handleEscape)
        return () => document.removeEventListener('keydown', handleEscape)
    }, [isOpen, onClose])

    useEffect(() => {
        if (isOpen) {
            drawerRef.current?.focus()
        }
    }, [isOpen])

    const handleCopy = async (text: string, field: string) => {
        try {
            await navigator.clipboard.writeText(text)
            setCopiedField(field)
            setTimeout(() => setCopiedField(null), 2000)
        } catch (e) {
            console.error('Failed to copy:', e)
        }
    }

    if (!isOpen || !event) return null

    const priorityColors = {
        high: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
        medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
        low: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
    }

    const typeLabels = {
        new_product: 'New Product',
        restock: 'Restock',
        price_drop: 'Price Drop',
    }

    return (
        <div className="fixed inset-0 z-50 flex" role="dialog" aria-modal="true">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fade-in"
                onClick={onClose}
            />

            {/* Drawer */}
            <div
                ref={drawerRef}
                tabIndex={-1}
                className="absolute right-0 top-0 h-full w-full max-w-md bg-zinc-900 border-l border-zinc-800 shadow-2xl animate-slide-in-right overflow-y-auto"
            >
                {/* Header */}
                <div className="sticky top-0 z-10 flex items-center justify-between p-5 border-b border-zinc-800 bg-zinc-900/95 backdrop-blur-sm">
                    <h2 className="text-lg font-semibold text-white">Product Details</h2>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg text-zinc-500 hover:text-white hover:bg-zinc-800 transition-colors"
                        aria-label="Close"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-5 space-y-5">
                    {/* Product Title */}
                    <div>
                        <div className="flex items-start justify-between gap-3">
                            <h3 className="text-xl font-bold text-white leading-tight">{event.product}</h3>
                            <button
                                onClick={() => handleCopy(event.product, 'product')}
                                className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors shrink-0"
                                aria-label="Copy product name"
                            >
                                {copiedField === 'product' ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                            </button>
                        </div>

                        {/* Badges */}
                        <div className="flex flex-wrap items-center gap-2 mt-3">
                            <span className={cn("px-2.5 py-1 text-xs font-medium rounded-full border", priorityColors[event.priority])}>
                                {event.priority === 'high' && <Sparkles className="w-3 h-3 inline mr-1" />}
                                {event.priority.charAt(0).toUpperCase() + event.priority.slice(1)} Priority
                            </span>
                            <span className="badge badge-purple text-xs">{typeLabels[event.type]}</span>
                            <span className="badge badge-blue text-xs">{event.source}</span>
                        </div>
                    </div>

                    {/* Key Info Grid */}
                    <div className="grid grid-cols-2 gap-4">
                        {/* Store */}
                        <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
                            <div className="flex items-center gap-2 text-zinc-500 mb-1">
                                <Store className="w-4 h-4" />
                                <span className="text-xs font-medium">Store</span>
                            </div>
                            <p className="text-sm font-semibold text-white">{event.store}</p>
                        </div>

                        {/* Price */}
                        <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
                            <div className="flex items-center gap-2 text-zinc-500 mb-1">
                                <DollarSign className="w-4 h-4" />
                                <span className="text-xs font-medium">Price</span>
                            </div>
                            <p className="text-sm font-semibold text-white">{formatPrice(event.price)}</p>
                        </div>

                        {/* Detected */}
                        <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
                            <div className="flex items-center gap-2 text-zinc-500 mb-1">
                                <Clock className="w-4 h-4" />
                                <span className="text-xs font-medium">Detected</span>
                            </div>
                            <p className="text-sm font-semibold text-white">{formatRelativeTime(event.timestamp)}</p>
                        </div>

                        {/* Confidence */}
                        <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
                            <div className="flex items-center gap-2 text-zinc-500 mb-1">
                                <Tag className="w-4 h-4" />
                                <span className="text-xs font-medium">Match Confidence</span>
                            </div>
                            <p className="text-sm font-semibold text-white">{Math.round(event.confidence * 100)}%</p>
                        </div>
                    </div>

                    {/* Profit (if available) */}
                    {event.profit && event.profit > 0 && (
                        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-xs text-emerald-400 font-medium mb-1">Estimated Profit</p>
                                    <p className="text-2xl font-bold text-emerald-400">+{formatPrice(event.profit)}</p>
                                </div>
                                <div className="p-3 rounded-xl bg-emerald-500/20">
                                    <DollarSign className="w-6 h-6 text-emerald-400" />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Matched Product */}
                    {event.matched && (
                        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
                            <p className="text-xs text-amber-400 font-medium mb-1">Matched to Curated Product</p>
                            <p className="text-sm font-semibold text-white">{event.matched}</p>
                        </div>
                    )}

                    {/* Available Sizes */}
                    {event.sizes && event.sizes.length > 0 && (
                        <div>
                            <p className="text-xs font-medium text-zinc-500 mb-2">Available Sizes</p>
                            <div className="flex flex-wrap gap-2">
                                {event.sizes.map((size, i) => (
                                    <span
                                        key={i}
                                        className="px-3 py-1.5 text-sm font-medium bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                                    >
                                        {size}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Product URL */}
                    <div>
                        <p className="text-xs font-medium text-zinc-500 mb-2">Product URL</p>
                        <div className="flex items-center gap-2">
                            <div className="flex-1 p-3 rounded-lg bg-zinc-800 border border-zinc-700 overflow-hidden">
                                <p className="text-sm text-zinc-300 truncate">{event.url}</p>
                            </div>
                            <button
                                onClick={() => handleCopy(event.url, 'url')}
                                className="p-3 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors"
                                aria-label="Copy URL"
                            >
                                {copiedField === 'url' ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                            </button>
                            <a
                                href={event.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-3 rounded-lg bg-violet-500/20 hover:bg-violet-500/30 text-violet-400 transition-colors"
                                aria-label="Open in new tab"
                            >
                                <ExternalLink className="w-4 h-4" />
                            </a>
                        </div>
                    </div>

                    {/* Raw Payload (Collapsible) */}
                    <div className="border border-zinc-700 rounded-xl overflow-hidden">
                        <button
                            onClick={() => setShowRawPayload(!showRawPayload)}
                            className="w-full flex items-center justify-between p-4 bg-zinc-800/50 hover:bg-zinc-800 transition-colors"
                        >
                            <span className="text-sm font-medium text-zinc-400">Raw Payload</span>
                            {showRawPayload ? (
                                <ChevronUp className="w-4 h-4 text-zinc-500" />
                            ) : (
                                <ChevronDown className="w-4 h-4 text-zinc-500" />
                            )}
                        </button>
                        {showRawPayload && (
                            <div className="p-4 bg-zinc-900/50 border-t border-zinc-700">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs text-zinc-500">JSON</span>
                                    <button
                                        onClick={() => handleCopy(JSON.stringify(event, null, 2), 'json')}
                                        className="flex items-center gap-1 text-xs text-zinc-400 hover:text-white transition-colors"
                                    >
                                        {copiedField === 'json' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                                        Copy
                                    </button>
                                </div>
                                <pre className="text-xs text-zinc-400 overflow-x-auto whitespace-pre-wrap break-words font-mono">
                                    {JSON.stringify(event, null, 2)}
                                </pre>
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer Actions */}
                <div className="sticky bottom-0 p-5 border-t border-zinc-800 bg-zinc-900/95 backdrop-blur-sm">
                    <div className="flex gap-3">
                        <button
                            onClick={onClose}
                            className="flex-1 px-4 py-3 text-sm font-medium text-zinc-400 hover:text-white bg-zinc-800 border border-zinc-700 rounded-xl transition-colors"
                        >
                            Close
                        </button>
                        <a
                            href={event.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold text-white bg-gradient-to-r from-violet-500 to-purple-500 rounded-xl shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 transition-all"
                        >
                            <ExternalLink className="w-4 h-4" />
                            Open Product
                        </a>
                    </div>
                </div>
            </div>
        </div>
    )
}
