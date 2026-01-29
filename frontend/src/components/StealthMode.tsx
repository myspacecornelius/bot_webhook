import { useEffect, useState } from 'react'
import { Eye, EyeOff, Shield } from 'lucide-react'
import { cn } from '../lib/utils'

export function StealthMode() {
  const [isStealthActive, setIsStealthActive] = useState(false)
  
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Escape key toggles stealth mode
      if (e.key === 'Escape') {
        setIsStealthActive(prev => !prev)
      }
    }
    
    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [])
  
  useEffect(() => {
    // Apply blur to sensitive elements when stealth is active
    if (isStealthActive) {
      document.body.classList.add('stealth-mode-active')
    } else {
      document.body.classList.remove('stealth-mode-active')
    }
  }, [isStealthActive])
  
  return (
    <>
      {/* Stealth Mode Indicator */}
      <button
        onClick={() => setIsStealthActive(!isStealthActive)}
        className={cn(
          "fixed bottom-6 right-6 z-50 p-4 rounded-full shadow-2xl transition-all duration-300",
          isStealthActive
            ? "bg-purple-600 hover:bg-purple-500 animate-pulse"
            : "bg-[#1a1a24] hover:bg-[#2a2a3a] border border-[#2a2a3a]"
        )}
        title={isStealthActive ? "Stealth Mode Active (Press ESC)" : "Activate Stealth Mode (Press ESC)"}
      >
        {isStealthActive ? (
          <EyeOff className="w-6 h-6 text-white" />
        ) : (
          <Eye className="w-6 h-6 text-gray-400" />
        )}
      </button>
      
      {/* Stealth Mode Overlay */}
      {isStealthActive && (
        <div className="fixed inset-0 z-40 pointer-events-none">
          <div className="absolute top-4 left-1/2 -translate-x-1/2 px-6 py-3 bg-purple-600 text-white rounded-full shadow-2xl flex items-center gap-3 animate-fade-in">
            <Shield className="w-5 h-5" />
            <span className="font-semibold">Stealth Mode Active</span>
            <kbd className="px-2 py-1 bg-purple-700 rounded text-xs">ESC</kbd>
          </div>
        </div>
      )}
      
      {/* Global Styles */}
      <style>{`
        .stealth-mode-active .sensitive-blur {
          filter: blur(8px);
          transition: filter 0.3s ease;
        }
        
        .stealth-mode-active .sensitive-blur:hover {
          filter: blur(4px);
        }
      `}</style>
    </>
  )
}
