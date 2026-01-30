import { useState } from 'react'
import { Shield, Key, ArrowRight, Sparkles } from 'lucide-react'
import { cn } from '../lib/utils'

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
      const response = await fetch('/api/auth/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: licenseKey })
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Invalid license key')
      }

      const data = await response.json()
      
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
    <div className="min-h-screen flex items-center justify-center p-6">
      {/* Background Effects */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-transparent to-cyan-500/10" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-500 to-cyan-500 mb-4 shadow-2xl shadow-purple-500/50">
            <span className="text-4xl">👻</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <span>PHANTOM</span>
            <Sparkles className="w-8 h-8 text-purple-400" />
          </h1>
          <p className="text-gray-400">Advanced Sneaker Automation Suite</p>
        </div>

        {/* Login Card */}
        <div className="bg-[#0f0f18] border border-[#1a1a2e] rounded-2xl p-8 shadow-2xl">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
              <Shield className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Activate License</h2>
              <p className="text-sm text-gray-500">Enter your license key to continue</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                <Key className="w-4 h-4 inline mr-1" />
                License Key
              </label>
              <input
                type="text"
                value={licenseKey}
                onChange={(e) => setLicenseKey(e.target.value)}
                className="w-full px-4 py-3 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 font-mono text-sm"
                placeholder="XXXX-XXXX-XXXX-XXXX"
                required
              />
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isValidating || !licenseKey}
              className={cn(
                "w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all",
                "bg-gradient-to-r from-purple-600 to-cyan-600 text-white hover:from-purple-500 hover:to-cyan-500",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
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
          <div className="mt-6 pt-6 border-t border-[#1a1a2e] text-center">
            <p className="text-sm text-gray-500 mb-2">Don't have a license?</p>
            <a
              href="https://phantom-bot.com/pricing"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300 font-medium text-sm transition-colors"
            >
              Get Phantom Pro →
            </a>
          </div>
        </div>

        {/* Features */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl mb-1">⚡</div>
            <p className="text-xs text-gray-500">Lightning Fast</p>
          </div>
          <div>
            <div className="text-2xl mb-1">🧠</div>
            <p className="text-xs text-gray-500">AI Powered</p>
          </div>
          <div>
            <div className="text-2xl mb-1">💰</div>
            <p className="text-xs text-gray-500">Profit Tracking</p>
          </div>
        </div>
      </div>
    </div>
  )
}
