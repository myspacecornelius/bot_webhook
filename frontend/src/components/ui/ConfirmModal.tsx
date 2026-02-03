/**
 * Confirmation Modal Component
 * Premium dark theme with glassmorphism
 */

import { useEffect, useRef } from 'react'
import { AlertTriangle, X } from 'lucide-react'
import { cn } from '../../lib/utils'

interface ConfirmModalProps {
    isOpen: boolean
    onClose: () => void
    onConfirm: () => void
    title: string
    message: string
    confirmText?: string
    cancelText?: string
    variant?: 'danger' | 'warning' | 'info'
    isLoading?: boolean
}

export function ConfirmModal({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    variant = 'danger',
    isLoading = false,
}: ConfirmModalProps) {
    const modalRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen && !isLoading) {
                onClose()
            }
        }
        document.addEventListener('keydown', handleEscape)
        return () => document.removeEventListener('keydown', handleEscape)
    }, [isOpen, isLoading, onClose])

    useEffect(() => {
        if (isOpen) {
            modalRef.current?.focus()
        }
    }, [isOpen])

    if (!isOpen) return null

    const variantStyles = {
        danger: {
            icon: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
            button: 'bg-rose-500 hover:bg-rose-600 text-white shadow-lg shadow-rose-500/25',
            glow: 'from-rose-500/20',
        },
        warning: {
            icon: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
            button: 'bg-amber-500 hover:bg-amber-600 text-white shadow-lg shadow-amber-500/25',
            glow: 'from-amber-500/20',
        },
        info: {
            icon: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
            button: 'bg-violet-500 hover:bg-violet-600 text-white shadow-lg shadow-violet-500/25',
            glow: 'from-violet-500/20',
        },
    }

    const styles = variantStyles[variant]

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
        >
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
                onClick={!isLoading ? onClose : undefined}
            />

            {/* Modal */}
            <div
                ref={modalRef}
                tabIndex={-1}
                className="relative w-full max-w-md animate-scale-in"
            >
                {/* Gradient border glow */}
                <div className={cn(
                    "absolute -inset-[1px] bg-gradient-to-b to-transparent rounded-2xl blur-sm opacity-75",
                    styles.glow
                )} />

                <div className="relative bg-zinc-900 rounded-2xl border border-zinc-800 shadow-2xl overflow-hidden">
                    {/* Close button */}
                    <button
                        onClick={onClose}
                        disabled={isLoading}
                        className="absolute top-4 right-4 p-2 rounded-lg text-zinc-500 hover:text-white hover:bg-zinc-800 transition-colors disabled:opacity-50"
                        aria-label="Close"
                    >
                        <X className="w-4 h-4" />
                    </button>

                    {/* Content */}
                    <div className="p-6">
                        <div className="flex items-start gap-4">
                            <div className={cn("p-3 rounded-xl border shrink-0", styles.icon)}>
                                <AlertTriangle className="w-5 h-5" />
                            </div>

                            <div className="flex-1 pt-0.5">
                                <h2 id="modal-title" className="text-lg font-semibold text-white">
                                    {title}
                                </h2>
                                <p className="mt-2 text-sm text-zinc-400 leading-relaxed">
                                    {message}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-zinc-800 bg-zinc-900/50">
                        <button
                            onClick={onClose}
                            disabled={isLoading}
                            className="px-4 py-2.5 text-sm font-medium text-zinc-400 hover:text-white bg-zinc-800 border border-zinc-700 rounded-xl transition-colors disabled:opacity-50"
                        >
                            {cancelText}
                        </button>
                        <button
                            onClick={onConfirm}
                            disabled={isLoading}
                            className={cn(
                                "px-5 py-2.5 text-sm font-semibold rounded-xl transition-all duration-200 disabled:opacity-50 flex items-center gap-2",
                                styles.button
                            )}
                        >
                            {isLoading && (
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            )}
                            {confirmText}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
