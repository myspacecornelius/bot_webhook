/**
 * LearnPage - Interactive Documentation
 * Visual, playful, click-through modules with guided tours.
 * Pulls from the same metadata that powers tooltips.
 */

import { useState } from 'react'
import {
  BookOpen, Clock, Target, Zap, Shield, Bell, Filter,
  ChevronRight, Check, ArrowRight, Lightbulb, AlertTriangle
} from 'lucide-react'
import { settingsMetadata, getSettingsByCategory, type SettingCategory } from '../lib/settingsMetadata'
import { cn } from '../lib/utils'

interface LearnModule {
  id: string
  title: string
  description: string
  icon: React.ElementType
  color: string
  duration: string
  category: SettingCategory
  steps: ModuleStep[]
}

interface ModuleStep {
  title: string
  content: string
  tip?: string
  warning?: string
  interactive?: 'slider' | 'toggle' | 'select'
  settingId?: string
}

const LEARN_MODULES: LearnModule[] = [
  {
    id: 'monitor-timing',
    title: 'Monitor Timing & Delays',
    description: 'Learn how to balance speed vs. safety with monitor delays',
    icon: Clock,
    color: 'emerald',
    duration: '3 min',
    category: 'monitor',
    steps: [
      {
        title: 'What is Monitor Delay?',
        content: 'Monitor delay is the time between each check of a store. Lower delays mean faster detection but higher risk of rate limiting.',
        tip: 'Most stores tolerate 3000ms (3 second) delays well.',
      },
      {
        title: 'Finding the Right Balance',
        content: 'Different stores have different tolerances. Boutiques (Kith, Concepts) need longer delays (5-10s). Large retailers (DTLR, Hibbett) can handle shorter delays (2-3s).',
        warning: 'Going below 2000ms almost always triggers rate limits.',
        interactive: 'slider',
        settingId: 'monitor_delay',
      },
      {
        title: 'Error Delay vs Monitor Delay',
        content: 'Error delay kicks in after failures. Keep it higher than monitor delay to give servers time to recover.',
        tip: 'A good rule: error_delay = monitor_delay × 2',
      },
      {
        title: 'Pro Tip: Adaptive Timing',
        content: 'Phantom automatically adjusts timing when it detects rate limits. You can see the current state in the Rate Limit Health panel.',
        tip: 'Watch for "backing_off" status - it means the system is recovering.',
      }
    ]
  },
  {
    id: 'rate-limiting',
    title: 'Understanding Rate Limits',
    description: 'Why you get blocked and how to prevent it',
    icon: Shield,
    color: 'red',
    duration: '4 min',
    category: 'rate-limit',
    steps: [
      {
        title: 'What Causes Rate Limits?',
        content: 'Stores track requests per IP/session. Too many requests too fast = temporary block (HTTP 429).',
        warning: 'Repeated 429s can lead to longer or permanent bans.',
      },
      {
        title: 'The Throttle Presets',
        content: 'Conservative = 5s delays, max 2 concurrent. Balanced = 3s delays, max 3 concurrent. Aggressive = 1.5s delays, max 5 concurrent.',
        interactive: 'select',
        settingId: 'throttle_preset',
      },
      {
        title: 'Backoff & Recovery',
        content: 'When rate limited, Phantom automatically backs off with exponential delays. First 429 = 5s wait, second = 10s, third = 20s, etc.',
        tip: 'The system adds random jitter (±30%) to avoid synchronized retry storms.',
      },
      {
        title: 'Request Coalescing',
        content: 'If multiple monitors need the same data within 100ms, Phantom makes one request and shares the result. This dramatically reduces request volume.',
      },
      {
        title: 'Caching',
        content: 'Responses are cached for 5 seconds by default. This means rapid-fire checks reuse cached data instead of hammering the server.',
        interactive: 'slider',
        settingId: 'cache_ttl',
      }
    ]
  },
  {
    id: 'keyword-matching',
    title: 'Keyword Matching Mastery',
    description: 'Write keywords that catch what you want without false positives',
    icon: Target,
    color: 'blue',
    duration: '3 min',
    category: 'monitor',
    steps: [
      {
        title: 'Basic Keywords',
        content: 'Keywords are matched against product titles. "dunk" matches "Nike Dunk Low Panda". Case-insensitive.',
        tip: 'Use multiple keywords separated by commas: dunk, jordan, yeezy',
      },
      {
        title: 'Required Keywords (+)',
        content: 'Prefix with + to require: "+dunk, +low" only matches products with BOTH "dunk" AND "low".',
        warning: 'Too many required keywords may miss products with slight naming variations.',
      },
      {
        title: 'Exclusions (-)',
        content: 'Prefix with - to exclude: "jordan, -kids, -gs" matches Jordans but excludes kids/GS sizes.',
        tip: 'Common exclusions: -kids, -gs, -toddler, -infant, -ps',
      },
      {
        title: 'Size Filtering',
        content: 'Set target sizes to only alert for your sizes. Use normalized format: 10, 10.5, 11',
        interactive: 'toggle',
        settingId: 'target_sizes',
      }
    ]
  },
  {
    id: 'auto-tasks',
    title: 'Auto-Task Creation',
    description: 'Let monitors automatically create checkout tasks',
    icon: Zap,
    color: 'amber',
    duration: '2 min',
    category: 'monitor',
    steps: [
      {
        title: 'How Auto-Tasks Work',
        content: 'When a monitor detects a matching product, it can automatically create a checkout task using your default profile and proxy settings.',
        warning: 'Make sure your filters are precise - broad keywords + auto-task = many unwanted tasks.',
      },
      {
        title: 'Setting Up',
        content: '1. Configure a default profile\n2. Set up proxy groups\n3. Define precise keywords\n4. Enable auto-task on the monitor',
        tip: 'Test with auto-task disabled first to see what matches.',
      },
      {
        title: 'Confidence Thresholds',
        content: 'Auto-tasks only trigger when match confidence exceeds your threshold (default 70%). Higher = fewer but more accurate tasks.',
      }
    ]
  },
  {
    id: 'notifications',
    title: 'Notification Routing',
    description: 'Get alerted the right way at the right time',
    icon: Bell,
    color: 'purple',
    duration: '2 min',
    category: 'monitor',
    steps: [
      {
        title: 'Notification Types',
        content: 'Desktop notifications, Discord webhooks, and sound alerts. You can use different routes for different priority levels.',
        tip: 'Critical drops → phone notification. Regular monitors → Discord.',
      },
      {
        title: 'Discord Webhooks',
        content: 'Create a webhook in Discord server settings. Paste the URL in Phantom. Test before drops!',
        warning: 'Discord has rate limits too - don\'t spam the same webhook.',
      },
      {
        title: 'Priority-Based Routing',
        content: 'High priority products can go to a different channel than regular finds. Set up multiple webhooks for different urgency levels.',
      }
    ]
  },
  {
    id: 'profit-analysis',
    title: 'Profit Analysis',
    description: 'Use market intelligence to focus on profitable items',
    icon: Filter,
    color: 'green',
    duration: '2 min',
    category: 'advanced',
    steps: [
      {
        title: 'How It Works',
        content: 'Phantom pulls real-time prices from StockX and GOAT. When a product is detected, it estimates profit based on retail vs. resale.',
        tip: 'Profit = Resale Price - Retail - Fees (~13%)',
      },
      {
        title: 'Setting Thresholds',
        content: 'Set a minimum profit threshold to only alert for items worth your time. $50+ is a common starting point.',
        interactive: 'slider',
        settingId: 'profit_threshold',
      },
      {
        title: 'Limitations',
        content: 'Prices fluctuate. A $100 profit estimate today might be $50 by the time you receive and list the item.',
        warning: 'Don\'t rely solely on profit estimates - consider market trends too.',
      }
    ]
  }
]

export function LearnPage() {
  const [activeModule, setActiveModule] = useState<string | null>(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [completedModules, setCompletedModules] = useState<Set<string>>(new Set())

  const module = LEARN_MODULES.find(m => m.id === activeModule)

  const handleCompleteModule = () => {
    if (activeModule) {
      setCompletedModules(prev => new Set([...prev, activeModule]))
    }
    setActiveModule(null)
    setCurrentStep(0)
  }

  const colorMap: Record<string, string> = {
    emerald: 'from-emerald-500/20 to-emerald-500/5 border-emerald-500/30 text-emerald-400',
    red: 'from-red-500/20 to-red-500/5 border-red-500/30 text-red-400',
    blue: 'from-blue-500/20 to-blue-500/5 border-blue-500/30 text-blue-400',
    amber: 'from-amber-500/20 to-amber-500/5 border-amber-500/30 text-amber-400',
    purple: 'from-purple-500/20 to-purple-500/5 border-purple-500/30 text-purple-400',
    green: 'from-green-500/20 to-green-500/5 border-green-500/30 text-green-400',
  }

  if (activeModule && module) {
    return (
      <ModuleView
        module={module}
        currentStep={currentStep}
        onNext={() => setCurrentStep(s => Math.min(s + 1, module.steps.length - 1))}
        onPrev={() => setCurrentStep(s => Math.max(s - 1, 0))}
        onComplete={handleCompleteModule}
        onExit={() => { setActiveModule(null); setCurrentStep(0) }}
        colorMap={colorMap}
      />
    )
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[var(--text)] flex items-center gap-3">
          <BookOpen className="w-7 h-7 text-[var(--primary)]" />
          Learn Phantom
        </h1>
        <p className="text-[var(--muted)] mt-1">
          Interactive guides to master every feature
        </p>
      </div>

      {/* Progress */}
      <div className="mb-6 p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-[var(--text)]">Your Progress</span>
          <span className="text-sm text-[var(--muted)]">
            {completedModules.size} / {LEARN_MODULES.length} completed
          </span>
        </div>
        <div className="h-2 bg-[var(--surface2)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--primary)] transition-all duration-500"
            style={{ width: `${(completedModules.size / LEARN_MODULES.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Module Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {LEARN_MODULES.map(mod => {
          const Icon = mod.icon
          const isCompleted = completedModules.has(mod.id)

          return (
            <button
              key={mod.id}
              onClick={() => setActiveModule(mod.id)}
              className={cn(
                "p-5 rounded-xl border bg-gradient-to-br text-left transition-all hover:scale-[1.02]",
                colorMap[mod.color],
                isCompleted && "opacity-60"
              )}
            >
              <div className="flex items-start justify-between mb-3">
                <Icon className="w-6 h-6" />
                {isCompleted ? (
                  <Check className="w-5 h-5 text-green-400" />
                ) : (
                  <span className="text-xs opacity-70">{mod.duration}</span>
                )}
              </div>
              <h3 className="font-semibold text-[var(--text)] mb-1">{mod.title}</h3>
              <p className="text-sm opacity-80">{mod.description}</p>
              <div className="mt-3 flex items-center gap-1 text-xs opacity-70">
                <span>{mod.steps.length} steps</span>
                <ChevronRight className="w-3 h-3" />
              </div>
            </button>
          )
        })}
      </div>

      {/* Quick Reference */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-[var(--text)] mb-4">Quick Reference</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(['monitor', 'rate-limit', 'task', 'advanced'] as SettingCategory[]).map(category => (
            <div key={category} className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
              <h3 className="font-medium text-[var(--text)] capitalize mb-3">{category.replace('-', ' ')} Settings</h3>
              <div className="space-y-2">
                {getSettingsByCategory(category).slice(0, 4).map(setting => (
                  <div key={setting.id} className="text-sm">
                    <span className="font-medium text-[var(--text)]">{setting.label}</span>
                    <span className="text-[var(--muted)]"> — {setting.shortHelp}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

interface ModuleViewProps {
  module: LearnModule
  currentStep: number
  onNext: () => void
  onPrev: () => void
  onComplete: () => void
  onExit: () => void
  colorMap: Record<string, string>
}

function ModuleView({ module, currentStep, onNext, onPrev, onComplete, onExit, colorMap }: ModuleViewProps) {
  const step = module.steps[currentStep]
  const isLastStep = currentStep === module.steps.length - 1
  const Icon = module.icon

  return (
    <div className="p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <button onClick={onExit} className="text-[var(--muted)] hover:text-[var(--text)] text-sm">
          ← Back to Learn
        </button>
        <span className="text-sm text-[var(--muted)]">
          Step {currentStep + 1} of {module.steps.length}
        </span>
      </div>

      {/* Module Title */}
      <div className={cn("p-4 rounded-xl border bg-gradient-to-br mb-6", colorMap[module.color])}>
        <div className="flex items-center gap-3">
          <Icon className="w-6 h-6" />
          <h1 className="text-xl font-bold text-[var(--text)]">{module.title}</h1>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="flex gap-1 mb-6">
        {module.steps.map((_, i) => (
          <div
            key={i}
            className={cn(
              "h-1 flex-1 rounded-full transition-colors",
              i <= currentStep ? "bg-[var(--primary)]" : "bg-[var(--surface2)]"
            )}
          />
        ))}
      </div>

      {/* Step Content */}
      <div className="p-6 rounded-xl bg-[var(--surface)] border border-[var(--border)] mb-6">
        <h2 className="text-lg font-semibold text-[var(--text)] mb-4">{step.title}</h2>
        <p className="text-[var(--muted)] whitespace-pre-line">{step.content}</p>

        {step.tip && (
          <div className="mt-4 p-3 rounded-lg bg-[var(--primary)]/10 border border-[var(--primary)]/20">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-4 h-4 text-[var(--primary)] mt-0.5 flex-shrink-0" />
              <p className="text-sm text-[var(--text)]">{step.tip}</p>
            </div>
          </div>
        )}

        {step.warning && (
          <div className="mt-4 p-3 rounded-lg bg-[var(--warning)]/10 border border-[var(--warning)]/20">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-[var(--warning)] mt-0.5 flex-shrink-0" />
              <p className="text-sm text-[var(--text)]">{step.warning}</p>
            </div>
          </div>
        )}

        {step.interactive && step.settingId && (
          <InteractiveDemo type={step.interactive} settingId={step.settingId} />
        )}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onPrev}
          disabled={currentStep === 0}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            currentStep === 0
              ? "text-[var(--muted)] cursor-not-allowed"
              : "text-[var(--text)] hover:bg-[var(--surface)]"
          )}
        >
          Previous
        </button>

        {isLastStep ? (
          <button
            onClick={onComplete}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[var(--primary)] text-white font-medium"
          >
            <Check className="w-4 h-4" />
            Complete Module
          </button>
        ) : (
          <button
            onClick={onNext}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[var(--primary)] text-white font-medium"
          >
            Next
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}

function InteractiveDemo({ type, settingId }: { type: string; settingId: string }) {
  const [value, setValue] = useState(50)
  const setting = settingsMetadata[settingId]

  if (!setting) return null

  return (
    <div className="mt-4 p-4 rounded-lg bg-[var(--surface2)] border border-[var(--border)]">
      <p className="text-xs text-[var(--muted)] mb-2">Try it: {setting.label}</p>

      {type === 'slider' && (
        <div className="flex items-center gap-3">
          <input
            type="range"
            min="0"
            max="100"
            value={value}
            onChange={(e) => setValue(parseInt(e.target.value))}
            className="flex-1 accent-[var(--primary)]"
          />
          <span className="w-12 text-center font-mono text-[var(--text)]">{value}</span>
        </div>
      )}

      {type === 'toggle' && (
        <button
          onClick={() => setValue(v => v ? 0 : 1)}
          className={cn(
            "w-12 h-6 rounded-full transition-colors relative",
            value ? "bg-[var(--primary)]" : "bg-[var(--surface)]"
          )}
        >
          <div className={cn(
            "absolute w-5 h-5 rounded-full bg-white top-0.5 transition-all",
            value ? "left-6" : "left-0.5"
          )} />
        </button>
      )}

      {type === 'select' && (
        <select
          className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text)]"
          onChange={(e) => setValue(parseInt(e.target.value))}
        >
          <option value="0">Conservative</option>
          <option value="1">Balanced</option>
          <option value="2">Aggressive</option>
        </select>
      )}
    </div>
  )
}
