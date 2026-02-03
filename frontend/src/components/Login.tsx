/**
 * Premium Login Page
 * Dark glassmorphism design with animated gradient and micro-interactions
 */

import { useState, useEffect } from 'react'
import { Shield, Key, ArrowRight, Sparkles, Zap, Brain, TrendingUp, Lock, CheckCircle2 } from 'lucide-react'
import { api } from '../api/client'

interface LoginProps {
  onLogin: (licenseKey: string) => void
}

export function Login({ onLogin }: LoginProps) {
  const [licenseKey, setLicenseKey] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [error, setError] = useState('')
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })

  // Track mouse for gradient effect
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY })
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsValidating(true)

    try {
      const data = await api.validateLicense(licenseKey)
      localStorage.setItem('phantom_license', licenseKey)
      localStorage.setItem('phantom_user', JSON.stringify(data.user))
      onLogin(licenseKey)
    } catch (err: any) {
      setError(err.message || 'Invalid license key')
    } finally {
      setIsValidating(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f1a 100%)'
      }}>

      {/* Animated gradient orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute w-[600px] h-[600px] rounded-full opacity-30 blur-[120px] transition-all duration-1000 ease-out"
          style={{
            background: 'radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, transparent 70%)',
            left: mousePos.x * 0.05,
            top: mousePos.y * 0.05,
          }}
        />
        <div
          className="absolute w-[500px] h-[500px] rounded-full opacity-25 blur-[100px] animate-pulse"
          style={{
            background: 'radial-gradient(circle, rgba(59, 130, 246, 0.4) 0%, transparent 70%)',
            right: '10%',
            bottom: '20%',
          }}
        />
        <div
          className="absolute w-[400px] h-[400px] rounded-full opacity-20 blur-[80px]"
          style={{
            background: 'radial-gradient(circle, rgba(16, 185, 129, 0.4) 0%, transparent 70%)',
            left: '5%',
            bottom: '10%',
            animation: 'float 8s ease-in-out infinite',
          }}
        />
      </div>

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                           linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="relative inline-block">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-2xl shadow-violet-500/25 mb-6 mx-auto transform hover:scale-105 transition-transform duration-300">
              <Zap className="w-10 h-10 text-white" strokeWidth={2.5} />
            </div>
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-400 rounded-full animate-pulse" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">
            PHANTOM
          </h1>
          <p className="text-zinc-400 text-sm">Next-Gen Automation Suite</p>
        </div>

        {/* Glass Card */}
        <div className="relative">
          {/* Gradient border */}
          <div className="absolute -inset-[1px] bg-gradient-to-r from-violet-500/50 via-purple-500/50 to-blue-500/50 rounded-2xl blur-sm opacity-75" />

          <div className="relative bg-zinc-900/80 backdrop-blur-xl rounded-2xl border border-white/10 p-8 shadow-2xl">
            <div className="flex items-center gap-4 mb-8">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 flex items-center justify-center border border-violet-500/30">
                <Shield className="w-6 h-6 text-violet-400" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">Activate License</h2>
                <p className="text-sm text-zinc-500">Enter your key to unlock</p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-zinc-300 mb-3">
                  <Key className="w-4 h-4 text-zinc-500" />
                  License Key
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={licenseKey}
                    onChange={(e) => setLicenseKey(e.target.value.toUpperCase())}
                    className="w-full px-4 py-3.5 bg-zinc-800/50 border border-zinc-700/50 rounded-xl text-white placeholder-zinc-600 font-mono text-sm tracking-wider focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/50 transition-all"
                    placeholder="XXXX-XXXX-XXXX-XXXX"
                    required
                  />
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <Lock className="w-4 h-4 text-zinc-600" />
                  </div>
                </div>
                <p className="flex items-center gap-1.5 text-xs text-zinc-600 mt-2">
                  <CheckCircle2 className="w-3 h-3" />
                  256-bit encrypted • Privacy protected
                </p>
              </div>

              {error && (
                <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm animate-shake">
                  <div className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isValidating || licenseKey.length < 4}
                className="w-full relative group overflow-hidden rounded-xl font-semibold text-white py-4 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                }}
              >
                {/* Shine effect */}
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/20 to-transparent" />

                <span className="relative flex items-center justify-center gap-2">
                  {isValidating ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Validating...
                    </>
                  ) : (
                    <>
                      Activate License
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </span>
              </button>
            </form>

            <div className="mt-8 pt-6 border-t border-zinc-800 text-center">
              <p className="text-zinc-500 text-sm mb-2">Don't have a license?</p>
              <a
                href="#"
                className="inline-flex items-center gap-2 text-violet-400 hover:text-violet-300 font-medium text-sm transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                Get Phantom Pro
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="mt-10 grid grid-cols-3 gap-4">
          <FeatureChip icon={Zap} label="Lightning Fast" color="violet" />
          <FeatureChip icon={Brain} label="AI Powered" color="blue" />
          <FeatureChip icon={TrendingUp} label="Profit Tracking" color="emerald" />
        </div>

        {/* Stats */}
        <div className="mt-8 flex items-center justify-center gap-8 text-center">
          <div>
            <p className="text-2xl font-bold text-white">50K+</p>
            <p className="text-xs text-zinc-500">Active Users</p>
          </div>
          <div className="w-px h-8 bg-zinc-800" />
          <div>
            <p className="text-2xl font-bold text-white">$2M+</p>
            <p className="text-xs text-zinc-500">Profit Generated</p>
          </div>
          <div className="w-px h-8 bg-zinc-800" />
          <div>
            <p className="text-2xl font-bold text-white">99.9%</p>
            <p className="text-xs text-zinc-500">Uptime</p>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          75% { transform: translateX(5px); }
        }
        .animate-shake {
          animation: shake 0.3s ease-in-out;
        }
      `}</style>
    </div>
  )
}

function FeatureChip({ icon: Icon, label, color }: { icon: any; label: string; color: 'violet' | 'blue' | 'emerald' }) {
  const colors = {
    violet: 'from-violet-500/10 to-purple-500/10 border-violet-500/20 text-violet-400',
    blue: 'from-blue-500/10 to-cyan-500/10 border-blue-500/20 text-blue-400',
    emerald: 'from-emerald-500/10 to-teal-500/10 border-emerald-500/20 text-emerald-400',
  }

  return (
    <div className={`flex flex-col items-center gap-2 p-4 rounded-xl bg-gradient-to-br ${colors[color]} border backdrop-blur-sm hover:scale-105 transition-transform duration-300 cursor-default`}>
      <Icon className="w-5 h-5" />
      <p className="text-xs font-medium text-zinc-400">{label}</p>
    </div>
  )
}
