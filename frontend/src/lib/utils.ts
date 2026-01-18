import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPrice(price: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(price)
}

export function formatProfit(profit: number): string {
  const sign = profit >= 0 ? '+' : ''
  return `${sign}${formatPrice(profit)}`
}

export function getProfitClass(profit: number): string {
  if (profit >= 100) return 'profit-high'
  if (profit >= 30) return 'profit-medium'
  return 'profit-low'
}

export function formatRelativeTime(date: Date | string): string {
  const now = new Date()
  const then = new Date(date)
  const diff = now.getTime() - then.getTime()
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (seconds < 60) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return then.toLocaleDateString()
}

export function playSound(type: 'success' | 'alert' | 'notification') {
  const sounds: Record<string, string> = {
    success: '/sounds/success.mp3',
    alert: '/sounds/alert.mp3',
    notification: '/sounds/notification.mp3',
  }
  
  try {
    const audio = new Audio(sounds[type])
    audio.volume = 0.5
    audio.play().catch(() => {})
  } catch {}
}
