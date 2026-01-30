import { Check, Zap, Crown, Rocket, ArrowRight } from 'lucide-react'
import { cn } from '../lib/utils'

const TIERS = [
  {
    id: 'starter',
    name: 'Starter',
    price: 29,
    icon: Zap,
    color: 'purple',
    description: 'Perfect for beginners',
    features: [
      '5 concurrent tasks',
      '2 active monitors',
      '20 tasks per day',
      'Basic Shopify support',
      'Email support',
      'Quick task creation'
    ],
    limitations: [
      'No proxy support',
      'No auto-tasks',
      'No API access'
    ]
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 79,
    icon: Crown,
    color: 'cyan',
    description: 'For serious resellers',
    popular: true,
    features: [
      '50 concurrent tasks',
      '10 active monitors',
      '200 tasks per day',
      'All site modules',
      'Proxy support',
      'Quick tasks',
      'Restock predictions',
      'Profit analysis',
      'Priority support'
    ],
    limitations: []
  },
  {
    id: 'elite',
    name: 'Elite',
    price: 199,
    icon: Rocket,
    color: 'green',
    description: 'Maximum performance',
    features: [
      'Unlimited tasks',
      'Unlimited monitors',
      'No daily limits',
      'All Pro features',
      'Auto-task creation',
      'API access',
      'Early restock alerts (24h)',
      'Custom integrations',
      'Dedicated support',
      'Success guarantee'
    ],
    limitations: []
  }
]

export function Pricing() {
  const handleSelectTier = async (tierId: string, _price: number) => {
    // TODO: Integrate with Stripe checkout
    const email = prompt('Enter your email:')
    if (!email) return

    try {
      const response = await fetch('/api/auth/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: tierId, email })
      })

      const data = await response.json()
      if (data.checkout_url) {
        window.location.href = data.checkout_url
      }
    } catch (e) {
      alert('Checkout failed. Please try again.')
    }
  }

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <div className="max-w-6xl mx-auto text-center mb-12">
        <h1 className="text-5xl font-bold text-white mb-4">
          Choose Your <span className="text-gradient">Phantom</span> Plan
        </h1>
        <p className="text-xl text-gray-400">
          Start botting smarter with AI-powered automation
        </p>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
        {TIERS.map((tier) => {
          const Icon = tier.icon
          const colors = {
            purple: 'from-purple-500/20 to-violet-500/10 border-purple-500/30',
            cyan: 'from-cyan-500/20 to-blue-500/10 border-cyan-500/30',
            green: 'from-green-500/20 to-emerald-500/10 border-green-500/30'
          }

          return (
            <div
              key={tier.id}
              className={cn(
                "relative rounded-2xl border p-8 transition-all hover:scale-105",
                tier.popular 
                  ? "bg-gradient-to-br from-cyan-500/20 to-blue-500/10 border-cyan-500 shadow-2xl shadow-cyan-500/50 scale-105" 
                  : `bg-gradient-to-br ${colors[tier.color as keyof typeof colors]}`
              )}
            >
              {tier.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-cyan-500 text-white text-sm font-bold rounded-full">
                  MOST POPULAR
                </div>
              )}

              <div className="flex items-center gap-3 mb-4">
                <div className={cn(
                  "w-12 h-12 rounded-xl flex items-center justify-center",
                  tier.popular ? "bg-cyan-500/30" : "bg-white/10"
                )}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white">{tier.name}</h3>
                  <p className="text-sm text-gray-400">{tier.description}</p>
                </div>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-bold text-white">${tier.price}</span>
                  <span className="text-gray-400">/month</span>
                </div>
              </div>

              <button
                onClick={() => handleSelectTier(tier.id, tier.price)}
                className={cn(
                  "w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all mb-6",
                  tier.popular
                    ? "bg-cyan-600 text-white hover:bg-cyan-500"
                    : "bg-white/10 text-white hover:bg-white/20"
                )}
              >
                Get {tier.name}
                <ArrowRight className="w-5 h-5" />
              </button>

              <div className="space-y-3">
                {tier.features.map((feature, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-gray-300">{feature}</span>
                  </div>
                ))}
              </div>

              {tier.limitations.length > 0 && (
                <div className="mt-6 pt-6 border-t border-white/10">
                  <p className="text-xs text-gray-500 mb-2">Not included:</p>
                  {tier.limitations.map((limitation, i) => (
                    <p key={i} className="text-xs text-gray-600 line-through">
                      {limitation}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* FAQ */}
      <div className="max-w-3xl mx-auto">
        <h2 className="text-2xl font-bold text-white text-center mb-8">Frequently Asked Questions</h2>
        <div className="space-y-4">
          <div className="p-6 rounded-xl bg-[#0f0f18] border border-[#1a1a2e]">
            <h3 className="font-semibold text-white mb-2">Can I cancel anytime?</h3>
            <p className="text-sm text-gray-400">Yes, cancel anytime. Your license remains active until the end of your billing period.</p>
          </div>
          <div className="p-6 rounded-xl bg-[#0f0f18] border border-[#1a1a2e]">
            <h3 className="font-semibold text-white mb-2">Do you offer refunds?</h3>
            <p className="text-sm text-gray-400">7-day money-back guarantee if you're not satisfied.</p>
          </div>
          <div className="p-6 rounded-xl bg-[#0f0f18] border border-[#1a1a2e]">
            <h3 className="font-semibold text-white mb-2">Can I upgrade/downgrade?</h3>
            <p className="text-sm text-gray-400">Yes, change your plan anytime. Upgrades are prorated.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
