import { useState } from 'react'
import { 
  TrendingUp, 
  Search,
  RefreshCw,
  Flame,
  Tag
} from 'lucide-react'
import { api } from '../api/client'
import { cn, formatPrice } from '../lib/utils'

interface TrendingProduct {
  name: string
  sku: string
  brand: string
  retailPrice: number
  resellPrice: number
  profit: number
  profitMargin: number
  hyped: boolean
  releaseDate?: string
  imageUrl?: string
}

interface ResearchResult {
  name: string
  sku: string
  keywords: string[]
  recommendedSites: string[]
  hyped: number
  estimatedProfit: number
}

function ProductCard({ product }: { product: TrendingProduct }) {
  const profitColor = product.profit >= 100 ? 'text-green-400' : product.profit >= 30 ? 'text-yellow-400' : 'text-[var(--muted)]'
  
  return (
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 hover:border-moss-500/30 transition-all">
      <div className="flex items-start gap-4">
        <div className="w-20 h-20 rounded-lg bg-[var(--surface2)] flex items-center justify-center overflow-hidden">
          {product.imageUrl ? (
            <img src={product.imageUrl} alt="" className="w-full h-full object-cover" />
          ) : (
            <Tag className="w-8 h-8 text-[var(--muted)]" />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {product.hyped && (
              <span className="flex items-center gap-1 px-2 py-0.5 text-xs bg-orange-500/20 text-orange-400 rounded">
                <Flame className="w-3 h-3" /> Hyped
              </span>
            )}
            <span className="px-2 py-0.5 text-xs bg-moss-500/20 text-moss-400 rounded">
              {product.brand}
            </span>
          </div>
          <h3 className="font-medium text-[var(--text)] truncate">{product.name}</h3>
          <p className="text-xs text-[var(--muted)]">{product.sku}</p>
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-2 mt-4">
        <div className="p-2 rounded-lg bg-[var(--surface2)] text-center">
          <p className="text-sm font-bold text-[var(--text)]">{formatPrice(product.retailPrice)}</p>
          <p className="text-xs text-[var(--muted)]">Retail</p>
        </div>
        <div className="p-2 rounded-lg bg-[var(--surface2)] text-center">
          <p className="text-sm font-bold text-[var(--info)]">{formatPrice(product.resellPrice)}</p>
          <p className="text-xs text-[var(--muted)]">Resell</p>
        </div>
        <div className="p-2 rounded-lg bg-[var(--surface2)] text-center">
          <p className={cn("text-sm font-bold", profitColor)}>+{formatPrice(product.profit)}</p>
          <p className="text-xs text-[var(--muted)]">Profit</p>
        </div>
      </div>
    </div>
  )
}

function ResearchPanel({ result, onClose }: { result: ResearchResult | null; onClose: () => void }) {
  if (!result) return null
  
  return (
    <div className="bg-[var(--surface)] border border-moss-500/30 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-[var(--text)]">Research Results</h3>
        <button onClick={onClose} className="text-[var(--muted)] hover:text-[var(--text)] text-sm">
          Clear
        </button>
      </div>
      
      <div className="space-y-4">
        <div>
          <p className="text-sm text-[var(--muted)] mb-2">Product</p>
          <p className="text-[var(--text)] font-medium">{result.name}</p>
          <p className="text-xs text-[var(--muted)]">{result.sku}</p>
        </div>
        
        <div>
          <p className="text-sm text-[var(--muted)] mb-2">Hype Score</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-[var(--surface2)] rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full"
                style={{ width: `${result.hyped}%` }}
              />
            </div>
            <span className="text-sm font-medium text-orange-400">{result.hyped}/100</span>
          </div>
        </div>
        
        <div>
          <p className="text-sm text-[var(--muted)] mb-2">Estimated Profit</p>
          <p className="text-2xl font-bold text-green-400">+{formatPrice(result.estimatedProfit)}</p>
        </div>
        
        <div>
          <p className="text-sm text-[var(--muted)] mb-2">Recommended Keywords</p>
          <div className="flex flex-wrap gap-1">
            {result.keywords.map((kw, i) => (
              <span key={i} className="px-2 py-1 text-xs bg-[var(--surface2)] text-[var(--muted)] rounded">
                {kw}
              </span>
            ))}
          </div>
        </div>
        
        <div>
          <p className="text-sm text-[var(--muted)] mb-2">Recommended Sites</p>
          <div className="flex flex-wrap gap-1">
            {result.recommendedSites.map((site, i) => (
              <span key={i} className="px-2 py-1 text-xs bg-moss-500/20 text-moss-400 rounded">
                {site}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export function Intelligence() {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchSku, setSearchSku] = useState('')
  const [searchPrice, setSearchPrice] = useState('')
  const [loading, setLoading] = useState(false)
  const [researchResult, setResearchResult] = useState<ResearchResult | null>(null)
  
  const [trendingProducts] = useState<TrendingProduct[]>([
    {
      name: 'Jordan 4 Retro Black Cat',
      sku: 'CU1110-010',
      brand: 'Jordan',
      retailPrice: 200,
      resellPrice: 350,
      profit: 150,
      profitMargin: 75,
      hyped: true,
    },
    {
      name: 'Jordan 1 Retro High Chicago',
      sku: 'DZ5485-612',
      brand: 'Jordan',
      retailPrice: 180,
      resellPrice: 380,
      profit: 200,
      profitMargin: 111,
      hyped: true,
    },
    {
      name: 'Nike Dunk Low Panda',
      sku: 'DD1391-100',
      brand: 'Nike',
      retailPrice: 110,
      resellPrice: 160,
      profit: 50,
      profitMargin: 45,
      hyped: false,
    },
    {
      name: 'Yeezy Boost 350 V2 Onyx',
      sku: 'HQ4540',
      brand: 'Yeezy',
      retailPrice: 230,
      resellPrice: 280,
      profit: 50,
      profitMargin: 22,
      hyped: false,
    },
    {
      name: 'New Balance 550 White Grey',
      sku: 'BB550PB1',
      brand: 'New Balance',
      retailPrice: 110,
      resellPrice: 180,
      profit: 70,
      profitMargin: 64,
      hyped: false,
    },
    {
      name: 'Travis Scott Jordan 1 Low',
      sku: 'CQ4277-001',
      brand: 'Jordan',
      retailPrice: 150,
      resellPrice: 650,
      profit: 500,
      profitMargin: 333,
      hyped: true,
    },
  ])
  
  const handleResearch = async () => {
    if (!searchQuery) return
    setLoading(true)
    
    try {
      const data = await api.researchProduct(searchQuery, searchSku, parseFloat(searchPrice) || 0)
      setResearchResult({
        name: data.name || searchQuery,
        sku: data.sku || searchSku,
        keywords: data.keywords || [],
        recommendedSites: data.sites || [],
        hyped: data.hype_score || 0,
        estimatedProfit: data.profit || 0,
      })
    } catch (e) {
      // Mock result for demo
      setResearchResult({
        name: searchQuery,
        sku: searchSku || 'N/A',
        keywords: ['+jordan', '+retro', '+chicago', '-gs', '-kids', '-ps'],
        recommendedSites: ['DTLR', 'Shoe Palace', 'Jimmy Jazz', 'Hibbett'],
        hyped: 85,
        estimatedProfit: 180,
      })
    }
    
    setLoading(false)
  }
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)] flex items-center gap-3">
            <TrendingUp className="w-7 h-7 text-green-400" />
            Market Intelligence
          </h1>
          <p className="text-[var(--muted)] text-sm mt-1">
            Research products and track market trends
          </p>
        </div>
      </div>
      
      {/* Research Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5">
          <h3 className="font-semibold text-[var(--text)] mb-4 flex items-center gap-2">
            <Search className="w-5 h-5 text-moss-400" />
            Product Research
          </h3>
          
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="col-span-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2.5 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] placeholder-gray-500 focus:outline-none focus:border-moss-500"
                placeholder="Product name (e.g., Jordan 4 Black Cat)"
              />
            </div>
            <input
              type="text"
              value={searchSku}
              onChange={(e) => setSearchSku(e.target.value)}
              className="w-full px-4 py-2.5 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] placeholder-gray-500 focus:outline-none focus:border-moss-500"
              placeholder="SKU (optional)"
            />
          </div>
          
          <div className="flex gap-4">
            <input
              type="number"
              value={searchPrice}
              onChange={(e) => setSearchPrice(e.target.value)}
              className="w-32 px-4 py-2.5 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] placeholder-gray-500 focus:outline-none focus:border-moss-500"
              placeholder="Retail $"
            />
            <button
              onClick={handleResearch}
              disabled={loading || !searchQuery}
              className="flex items-center gap-2 px-5 py-2.5 bg-moss-600 hover:bg-moss-500 disabled:opacity-50 text-[var(--text)] font-medium rounded-lg transition-colors"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              Research
            </button>
          </div>
        </div>
        
        <ResearchPanel result={researchResult} onClose={() => setResearchResult(null)} />
      </div>
      
      {/* Trending Products */}
      <div>
        <h2 className="text-lg font-semibold text-[var(--text)] mb-4 flex items-center gap-2">
          <Flame className="w-5 h-5 text-orange-400" />
          Trending Products
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {trendingProducts.map((product, i) => (
            <ProductCard key={i} product={product} />
          ))}
        </div>
      </div>
    </div>
  )
}
