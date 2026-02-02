import { useState } from 'react'
import { Shield, Key, ArrowRight, Sparkles } from 'lucide-react'
import { cn } from '../lib/utils'
import { api } from '../api/client'

interface LoginProps {
  onLogin: (licenseKey: string) => void
}

export function Login({ onLogin }: LoginProps) {
  const [licenseKey, setLicenseKey] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsValidating(true)

    try {
      const data = await api.validateLicense(licenseKey)
      
      // Store license key
      localStorage.setItem('phantom_license', licenseKey)
      localStorage.setItem('phantom_user', JSON.stringify(data.user))
      
      onLogin(licenseKey)
    } catch (err: any) {
      setError(err.message || 'Failed to validate license')
    } finally {
      setIsValidating(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ background: 'radial-gradient(1000px circle at 20% 10%, rgba(196,138,44,0.10), transparent 55%), #F6F1E7' }}>
      {/* Vanishing decorative elements */}
      <div className="fixed inset-0 -z-10 pointer-events-none">
        <div className="absolute top-20 left-10 w-32 h-32 opacity-30 transition-all duration-700" style={{ transform: `translateY(${typeof window !== 'undefined' ? window.scrollY * 0.3 : 0}px)`, opacity: typeof window !== 'undefined' ? Math.max(0, 1 - window.scrollY / 300) : 0.3 }}>
          <div className="text-6xl">👻</div>
        </div>
        <div className="absolute top-40 right-20 w-24 h-24 opacity-20 transition-all duration-700" style={{ transform: `translateY(${typeof window !== 'undefined' ? window.scrollY * 0.5 : 0}px)`, opacity: typeof window !== 'undefined' ? Math.max(0, 1 - window.scrollY / 300) : 0.2 }}>
          <div className="text-5xl">⚡</div>
        </div>
      </div>

      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-100 to-amber-50 mb-4 border border-amber-200/50" style={{ boxShadow: 'var(--shadow-md)' }}>
            <span className="text-4xl">👻</span>
          </div>
          <h1 className="text-4xl font-bold mb-2 flex items-center justify-center gap-3" style={{ color: 'var(--text)' }}>
            <span>PHANTOM</span>
          </h1>
          <p style={{ color: 'var(--muted)' }}>Advanced Sneaker Automation Suite</p>
        </div>

        {/* Paper Card */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-card)', boxShadow: 'var(--shadow-md)', padding: '32px' }}>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'rgba(106,123,78,0.12)' }}>
              <Shield className="w-6 h-6" style={{ color: 'var(--primary)' }} />
            </div>
            <div>
              <h2 className="text-xl font-bold" style={{ color: 'var(--text)' }}>Activate License</h2>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>Enter your license key to continue</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                <Key className="w-4 h-4 inline mr-1" />
                License Key
              </label>
              <input
                type="text"
                value={licenseKey}
                onChange={(e) => setLicenseKey(e.target.value)}
                style={{ 
                  width: '100%',
                  padding: '12px 16px',
                  background: 'var(--surface2)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-input)',
                  color: 'var(--text)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '14px'
                }}
                className="focus:outline-none"
                onFocus={(e) => e.target.style.boxShadow = 'var(--focus)'}
                onBlur={(e) => e.target.style.boxShadow = 'none'}
                placeholder="XXXX-XXXX-XXXX-XXXX"
                required
              />
              <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>🔒 Security & privacy protected</p>
            </div>

            {error && (
              <div className="p-3 rounded-lg text-sm" style={{ background: 'rgba(184,106,74,0.12)', border: '1px solid rgba(184,106,74,0.35)', color: 'var(--danger)' }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isValidating || !licenseKey}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '12px 24px',
                borderRadius: 'var(--radius-input)',
                fontWeight: '600',
                background: 'var(--primary)',
                color: '#FFF8ED',
                border: 'none',
                cursor: isValidating || !licenseKey ? 'not-allowed' : 'pointer',
                opacity: isValidating || !licenseKey ? 0.5 : 1,
                transition: 'all 0.2s',
                boxShadow: 'var(--shadow-sm)'
              }}
              onMouseEnter={(e) => !isValidating && licenseKey && (e.currentTarget.style.transform = 'translateY(-2px)', e.currentTarget.style.boxShadow = 'var(--shadow-md)')}
              onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)', e.currentTarget.style.boxShadow = 'var(--shadow-sm)')}
            >
              {isValidating ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Validating...
                </>
              ) : (
                <>
                  Activate License
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>

          {/* Get License Link */}
          <div className="mt-6 pt-6 text-center" style={{ borderTop: '1px solid var(--border)' }}>
            <p className="text-sm mb-2" style={{ color: 'var(--muted)' }}>Don't have a license?</p>
            <a
              href="https://phantom-bot.com/pricing"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-sm transition-colors"
              style={{ color: 'var(--primary)' }}
            >
              Get Phantom Pro →
            </a>
          </div>
        </div>

        {/* Features */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div style={{ padding: '12px', background: 'rgba(196,138,44,0.08)', borderRadius: '999px', border: '1px solid rgba(196,138,44,0.2)' }}>
            <div className="text-2xl mb-1">⚡</div>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>Lightning Fast</p>
          </div>
          <div style={{ padding: '12px', background: 'rgba(106,123,78,0.08)', borderRadius: '999px', border: '1px solid rgba(106,123,78,0.2)' }}>
            <div className="text-2xl mb-1">🧠</div>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>AI Powered</p>
          </div>
          <div style={{ padding: '12px', background: 'rgba(184,106,74,0.08)', borderRadius: '999px', border: '1px solid rgba(184,106,74,0.2)' }}>
            <div className="text-2xl mb-1">💰</div>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>Profit Tracking</p>
          </div>
        </div>
      </div>
    </div>
  )
}
