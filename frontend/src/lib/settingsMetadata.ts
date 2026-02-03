/**
 * Settings Metadata Registry
 * Single source of truth for all setting descriptions, tooltips, and documentation.
 */

export type SettingCategory = 'monitor' | 'rate-limit' | 'task' | 'store' | 'advanced'

export interface SettingMetadata {
  id: string
  label: string
  shortHelp: string
  longHelp: string
  whenToUse: string
  tradeoffs: string
  commonMistakes: string[]
  defaults: string
  learnMorePath: string
  category: SettingCategory
}

export const settingsMetadata: Record<string, SettingMetadata> = {
  monitor_delay: {
    id: 'monitor_delay',
    label: 'Monitor Delay',
    shortHelp: 'Time between checks for a single store (in milliseconds).',
    longHelp: 'Controls how frequently the monitor polls each store. Lower = faster detection but higher rate limit risk.',
    whenToUse: 'Use 2000-3000ms for high-priority drops. Use 5000-10000ms for background monitoring.',
    tradeoffs: 'Faster polling = quicker detection but more rate limits.',
    commonMistakes: ['Setting delay too low (<2000ms)', 'Same delay for all stores', 'Not accounting for multiple monitors'],
    defaults: '3000ms',
    learnMorePath: '/learn/monitor-timing',
    category: 'monitor'
  },
  monitor_mode: {
    id: 'monitor_mode',
    label: 'Monitor Mode',
    shortHelp: 'How the monitor searches for products.',
    longHelp: 'Keywords searches titles. URL monitors specific pages. Collection watches categories. Variant tracks SKUs.',
    whenToUse: 'Keywords for general drops. URL for known restocks. Collection for new releases.',
    tradeoffs: 'Keywords wider net but false positives. URL precise but misses new products.',
    commonMistakes: ['URL mode when product URL changes', 'Too broad keywords', 'Not updating keywords'],
    defaults: 'Keywords',
    learnMorePath: '/learn/monitor-modes',
    category: 'monitor'
  },
  target_sizes: {
    id: 'target_sizes',
    label: 'Target Sizes',
    shortHelp: 'Sizes to monitor and alert on.',
    longHelp: 'Only products with these sizes trigger notifications. Use normalized formats (10, 10.5).',
    whenToUse: 'Always set to your actual sizes to avoid noise.',
    tradeoffs: 'Fewer sizes = less noise but may miss profitable restocks.',
    commonMistakes: ['Too many sizes', 'Wrong format (US10 vs 10)', 'Forgetting to update'],
    defaults: 'Empty (all sizes)',
    learnMorePath: '/learn/size-filtering',
    category: 'monitor'
  },
  keywords: {
    id: 'keywords',
    label: 'Keywords',
    shortHelp: 'Product title keywords to match (comma-separated).',
    longHelp: 'Alert when title contains ANY keyword. Use + for required, - for exclusions.',
    whenToUse: 'For drops where you know the product name.',
    tradeoffs: 'More specific = fewer false positives but may miss variations.',
    commonMistakes: ['Too generic like "Nike"', 'Forgetting regional names', 'Not using exclusions'],
    defaults: 'Empty',
    learnMorePath: '/learn/keyword-matching',
    category: 'monitor'
  },
  price_min: {
    id: 'price_min',
    label: 'Min Price',
    shortHelp: 'Only alert for products above this price.',
    longHelp: 'Filters out low-value items from stores with mixed inventory.',
    whenToUse: 'When monitoring stores with both GR and limited releases.',
    tradeoffs: 'May filter legitimately discounted limited releases.',
    commonMistakes: ['Setting too high', 'Forgetting currency differences'],
    defaults: '0',
    learnMorePath: '/learn/price-filtering',
    category: 'monitor'
  },
  price_max: {
    id: 'price_max',
    label: 'Max Price',
    shortHelp: 'Only alert for products below this price.',
    longHelp: 'Filters expensive items outside budget or poor resale margins.',
    whenToUse: 'When you have a budget limit.',
    tradeoffs: 'May miss occasionally underpriced valuable items.',
    commonMistakes: ['Setting too low', 'Not accounting for tax'],
    defaults: 'Unlimited',
    learnMorePath: '/learn/price-filtering',
    category: 'monitor'
  },
  auto_task: {
    id: 'auto_task',
    label: 'Auto-Task Creation',
    shortHelp: 'Automatically create checkout tasks when products are found.',
    longHelp: 'Monitor creates tasks for detected products matching criteria.',
    whenToUse: 'For high-confidence monitors where you want immediate checkout.',
    tradeoffs: 'Faster checkout but may create unwanted tasks.',
    commonMistakes: ['Enabling with broad keywords', 'No default profile', 'Forgetting task limits'],
    defaults: 'Disabled',
    learnMorePath: '/learn/auto-tasks',
    category: 'monitor'
  },
  throttle_preset: {
    id: 'throttle_preset',
    label: 'Throttle Preset',
    shortHelp: 'Pre-configured rate limiting strategy.',
    longHelp: 'Conservative = safest. Balanced = good mix. Aggressive = fastest but risky.',
    whenToUse: 'Conservative for background. Aggressive only during drops with good proxies.',
    tradeoffs: 'Aggressive faster but needs quality proxies.',
    commonMistakes: ['Aggressive with DC proxies', 'Not switching back after drops'],
    defaults: 'Balanced',
    learnMorePath: '/learn/rate-limiting',
    category: 'rate-limit'
  },
  global_concurrency: {
    id: 'global_concurrency',
    label: 'Global Concurrency',
    shortHelp: 'Maximum simultaneous requests across all monitors.',
    longHelp: 'Limits total outbound requests to prevent network overload.',
    whenToUse: 'Lower on slow connection. Higher with dedicated resources.',
    tradeoffs: 'Higher = faster but more resource usage.',
    commonMistakes: ['Too high on residential connection', 'Not accounting for tasks'],
    defaults: '20',
    learnMorePath: '/learn/concurrency',
    category: 'rate-limit'
  },
  per_store_concurrency: {
    id: 'per_store_concurrency',
    label: 'Per-Store Concurrency',
    shortHelp: 'Maximum simultaneous requests to a single store.',
    longHelp: 'Prevents hammering individual stores.',
    whenToUse: 'Keep low (1-3) for most stores.',
    tradeoffs: 'Higher = faster but looks suspicious.',
    commonMistakes: ['Above 3 for boutiques', 'Not reducing during high traffic'],
    defaults: '3',
    learnMorePath: '/learn/concurrency',
    category: 'rate-limit'
  },
  cache_ttl: {
    id: 'cache_ttl',
    label: 'Cache TTL',
    shortHelp: 'How long to cache responses (seconds).',
    longHelp: 'Cached responses reused instead of new requests.',
    whenToUse: 'Increase for background. Decrease during active drops.',
    tradeoffs: 'Longer cache = fewer requests but staler data.',
    commonMistakes: ['Disabling during drops', 'Too long during restocks'],
    defaults: '5 seconds',
    learnMorePath: '/learn/caching',
    category: 'rate-limit'
  },
  task_mode: {
    id: 'task_mode',
    label: 'Task Mode',
    shortHelp: 'Checkout speed vs. safety tradeoff.',
    longHelp: 'Fast = aggressive. Normal = balanced. Safe = slower but fewer flags.',
    whenToUse: 'Fast for quantity-limited. Safe for strong bot detection.',
    tradeoffs: 'Fast = more checkouts but more flags.',
    commonMistakes: ['Fast on strict stores', 'Safe when speed critical'],
    defaults: 'Normal',
    learnMorePath: '/learn/task-modes',
    category: 'task'
  },
  proxy_group: {
    id: 'proxy_group',
    label: 'Proxy Group',
    shortHelp: 'Proxy pool for this task/monitor.',
    longHelp: 'Assigns specific proxy group. Residential recommended for most.',
    whenToUse: 'Separate groups by store type. Best proxies for hardest stores.',
    tradeoffs: 'Better proxies = higher success but expensive.',
    commonMistakes: ['Same group for monitors and checkout', 'DC on strict Shopify'],
    defaults: 'Default group',
    learnMorePath: '/learn/proxies',
    category: 'task'
  },
  profile_group: {
    id: 'profile_group',
    label: 'Profile Group',
    shortHelp: 'Payment/shipping profile pool for tasks.',
    longHelp: 'Which profiles to use for checkout.',
    whenToUse: 'Multiple profiles to avoid duplicate detection.',
    tradeoffs: 'More profiles = more chances but need more cards.',
    commonMistakes: ['Reusing same profile too much', 'Not verifying before drops'],
    defaults: 'Default group',
    learnMorePath: '/learn/profiles',
    category: 'task'
  },
  store_enabled: {
    id: 'store_enabled',
    label: 'Store Enabled',
    shortHelp: 'Whether this store is actively monitored.',
    longHelp: 'Disabled stores not polled. Useful for temporary pause.',
    whenToUse: 'Disable stores not dropping soon to save resources.',
    tradeoffs: 'More stores = more coverage but more resource usage.',
    commonMistakes: ['Too many enabled causing slow monitoring', 'Forgetting to re-enable'],
    defaults: 'Enabled',
    learnMorePath: '/learn/stores',
    category: 'store'
  },
  regex_keywords: {
    id: 'regex_keywords',
    label: 'Regex Keywords',
    shortHelp: 'Use regular expressions for keyword matching.',
    longHelp: 'Enables powerful pattern matching. Requires regex knowledge.',
    whenToUse: 'When simple keywords cannot express your needs.',
    tradeoffs: 'Powerful but complex. Incorrect patterns break matching.',
    commonMistakes: ['Unescaped special characters', 'Overly complex patterns', 'Not testing first'],
    defaults: 'Disabled',
    learnMorePath: '/learn/regex',
    category: 'advanced'
  },
  dedup_minutes: {
    id: 'dedup_minutes',
    label: 'Dedup Minutes',
    shortHelp: 'Ignore repeat detections for this many minutes.',
    longHelp: 'Prevents spam from same product being detected multiple times.',
    whenToUse: 'Increase for noisy stores. Decrease for fast-moving restocks.',
    tradeoffs: 'Longer = less spam but may miss actual restocks.',
    commonMistakes: ['Too long missing real restocks', 'Too short causing spam'],
    defaults: '30 minutes',
    learnMorePath: '/learn/deduplication',
    category: 'advanced'
  },
  profit_threshold: {
    id: 'profit_threshold',
    label: 'Profit Threshold',
    shortHelp: 'Minimum estimated profit to trigger alerts.',
    longHelp: 'Uses market intelligence to estimate profit. Only alerts above threshold.',
    whenToUse: 'When focused on profitable reselling only.',
    tradeoffs: 'May miss items with uncertain but good profit.',
    commonMistakes: ['Setting too high during market shifts', 'Ignoring fees'],
    defaults: '$0 (all products)',
    learnMorePath: '/learn/profit-analysis',
    category: 'advanced'
  }
}

export function getSettingMetadata(id: string): SettingMetadata | undefined {
  return settingsMetadata[id]
}

export function getSettingsByCategory(category: SettingCategory): SettingMetadata[] {
  return Object.values(settingsMetadata).filter(s => s.category === category)
}
