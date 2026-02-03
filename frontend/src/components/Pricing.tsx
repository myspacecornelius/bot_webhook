import { Check, Zap, Crown, Rocket, ArrowRight } from 'lucide-react'
import { cn } from '../lib/utils'
import { api } from '../api/client'

const TIERS = [
  {
    id: 'starter',
    name: 'Starter',
    price: 29,
    icon: Zap,
    color: 'moss',
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
    color: 'moss',
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
      const data = await api.createCheckoutSession(tierId, email)

      if (data.url) {
        window.location.href = data.url
      }
    } catch (e) {
      alert('Checkout failed. Please try again.')
    }
  }

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <div className="max-w-6xl mx-auto text-center mb-12">
        <h1 className="text-5xl font-bold text-[var(--text)] mb-4">
          Choose Your <span className="text-gradient">Phantom</span> Plan
        </h1>
        <p className="text-xl text-[var(--muted)]">
          Start botting smarter with AI-powered automation
        </p>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
        {TIERS.map((tier) => {
          const Icon = tier.icon
          const colors = {
            moss: 'from-moss-500/20 to-moss-500/10 border-moss-500/30',
            blue: 'from-[var(--info)]/20 to-blue-500/10 border-[var(--info)]/30',
            green: 'from-green-500/20 to-[var(--primary)]/10 border-green-500/30'
          }

          return (
            <div
              key={tier.id}
              className={cn(
                "relative rounded-2xl border p-8 transition-all hover:scale-105",
                tier.popular
                  ? "bg-gradient-to-br from-[var(--info)]/20 to-blue-500/10 border-[var(--info)] shadow-2xl shadow-[var(--info)]/50 scale-105"
                  : `bg-gradient-to-br ${colors[tier.color as keyof typeof colors]}`
              )}
            >
              {tier.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-[var(--info)] text-[var(--text)] text-sm font-bold rounded-full">
                  MOST POPULAR
                </div>
              )}

              <div className="flex items-center gap-3 mb-4">
                <div className={cn(
                  "w-12 h-12 rounded-xl flex items-center justify-center",
                  tier.popular ? "bg-[var(--info)]/10" : "bg-white/10"
                )}>
                  <Icon className="w-6 h-6 text-[var(--text)]" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-[var(--text)]">{tier.name}</h3>
                  <p className="text-sm text-[var(--muted)]">{tier.description}</p>
                </div>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-bold text-[var(--text)]">${tier.price}</span>
                  <span className="text-[var(--muted)]">/month</span>
                </div>
              </div>

              <button
                onClick={() => handleSelectTier(tier.id, tier.price)}
                className={cn(
                  "w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all mb-6",
                  tier.popular
                    ? "bg-[var(--info)] text-[var(--text)] hover:bg-[var(--primary)]"
                    : "bg-white/10 text-[var(--text)] hover:bg-white/20"
                )}
              >
                Get {tier.name}
                <ArrowRight className="w-5 h-5" />
              </button>

              <div className="space-y-3">
                {tier.features.map((feature, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-[var(--muted)]">{feature}</span>
                  </div>
                ))}
              </div>

              {tier.limitations.length > 0 && (
                <div className="mt-6 pt-6 border-t border-white/10">
                  <p className="text-xs text-[var(--muted)] mb-2">Not included:</p>
                  {tier.limitations.map((limitation, i) => (
                    <p key={i} className="text-xs text-[var(--muted)] line-through">
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
        <h2 className="text-2xl font-bold text-[var(--text)] text-center mb-8">Frequently Asked Questions</h2>
        <div className="space-y-4">
          <div className="p-6 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
            <h3 className="font-semibold text-[var(--text)] mb-2">Can I cancel anytime?</h3>
            <p className="text-sm text-[var(--muted)]">Yes, cancel anytime. Your license remains active until the end of your billing period.</p>
          </div>
          <div className="p-6 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
            <h3 className="font-semibold text-[var(--text)] mb-2">Do you offer refunds?</h3>
            <p className="text-sm text-[var(--muted)]">7-day money-back guarantee if you're not satisfied.</p>
          </div>
          <div className="p-6 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
            <h3 className="font-semibold text-[var(--text)] mb-2">Can I upgrade/downgrade?</h3>
            <p className="text-sm text-[var(--muted)]">Yes, change your plan anytime. Upgrades are prorated.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
