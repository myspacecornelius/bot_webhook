import { useEffect, useState } from 'react'
import { CheckCircle, DollarSign, TrendingUp, X } from 'lucide-react'
import { cn, formatPrice } from '../lib/utils'

interface SuccessNotification {
  id: string
  productName: string
  productImage?: string
  size: string
  price: number
  estimatedProfit: number
  store: string
  timestamp: number
}

export function SuccessTheater() {
  const [notifications, setNotifications] = useState<SuccessNotification[]>([])
  
  useEffect(() => {
    // Listen for success events from WebSocket or store
    const handleSuccess = (event: CustomEvent<SuccessNotification>) => {
      const notification = { ...event.detail, id: Date.now().toString() }
      setNotifications(prev => [notification, ...prev].slice(0, 3)) // Keep max 3
      
      // Play success sound
      playSuccessSound()
      
      // Auto-remove after 10 seconds
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== notification.id))
      }, 10000)
    }
    
    window.addEventListener('checkout-success' as any, handleSuccess)
    return () => window.removeEventListener('checkout-success' as any, handleSuccess)
  }, [])
  
  const playSuccessSound = () => {
    // Check if sound is enabled in localStorage
    const soundEnabled = localStorage.getItem('successSoundEnabled') !== 'false'
    if (!soundEnabled) return
    
    const audio = new Audio('/sounds/success.mp3')
    audio.volume = parseFloat(localStorage.getItem('successSoundVolume') || '0.5')
    audio.play().catch(() => {}) // Ignore errors if sound file missing
  }
  
  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }
  
  return (
    <div className="fixed top-20 right-6 z-50 space-y-3 pointer-events-none">
      {notifications.map((notif, index) => (
        <div
          key={notif.id}
          className={cn(
            "pointer-events-auto w-96 rounded-xl border-2 border-green-500 bg-gradient-to-br from-green-500/20 to-emerald-500/10 backdrop-blur-xl shadow-2xl shadow-green-500/50 animate-slide-in-right",
            "transform transition-all duration-500"
          )}
          style={{
            animationDelay: `${index * 100}ms`,
            marginTop: index > 0 ? '12px' : '0'
          }}
        >
          {/* Success Header */}
          <div className="flex items-center gap-3 p-4 pb-3 border-b border-green-500/30">
            <div className="w-12 h-12 rounded-full bg-green-500 flex items-center justify-center animate-bounce-once">
              <CheckCircle className="w-7 h-7 text-white fill-current" />
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-white text-lg flex items-center gap-2">
                🎉 CHECKOUT SUCCESS!
              </h3>
              <p className="text-xs text-green-300">{notif.store}</p>
            </div>
            <button
              onClick={() => removeNotification(notif.id)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* Product Details */}
          <div className="p-4 flex gap-4">
            {/* Product Image */}
            <div className="w-20 h-20 rounded-lg bg-[#1a1a24] flex items-center justify-center overflow-hidden flex-shrink-0">
              {notif.productImage ? (
                <img 
                  src={notif.productImage} 
                  alt={notif.productName}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-4xl">👟</div>
              )}
            </div>
            
            {/* Details */}
            <div className="flex-1 min-w-0">
              <h4 className="font-semibold text-white text-sm mb-1 line-clamp-2">
                {notif.productName}
              </h4>
              <div className="flex items-center gap-3 text-xs text-gray-300 mb-2">
                <span className="px-2 py-0.5 bg-white/10 rounded">Size {notif.size}</span>
                <span>{formatPrice(notif.price)}</span>
              </div>
              
              {/* Profit Display */}
              <div className="flex items-center gap-2 p-2 rounded-lg bg-green-500/20 border border-green-500/30">
                <TrendingUp className="w-4 h-4 text-green-400" />
                <div className="flex-1">
                  <p className="text-xs text-green-300">Est. Profit</p>
                  <p className="text-lg font-bold text-green-400">
                    +{formatPrice(notif.estimatedProfit)}
                  </p>
                </div>
                <DollarSign className="w-6 h-6 text-green-400 animate-pulse" />
              </div>
            </div>
          </div>
          
          {/* Animated Progress Bar */}
          <div className="h-1 bg-green-500/20 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-green-500 to-emerald-400 animate-progress-bar"
              style={{ animationDuration: '10s' }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

// Helper function to trigger success notification
export function triggerSuccessTheater(data: Omit<SuccessNotification, 'id' | 'timestamp'>) {
  const event = new CustomEvent('checkout-success', {
    detail: { ...data, timestamp: Date.now() }
  })
  window.dispatchEvent(event)
}
