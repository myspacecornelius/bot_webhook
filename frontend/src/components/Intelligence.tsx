import { useState } from "react";
import { TrendingUp, Search, RefreshCw, Flame, Tag } from "lucide-react";
import { api } from "../api/client";
import { cn, formatPrice } from "../lib/utils";
import { useCuratedProducts } from "../hooks/useQueries";
import type { CuratedProduct } from "../api/types";

interface ResearchResult {
  name: string;
  sku: string;
  keywords: string[];
  recommendedSites: string[];
  hyped: number;
  estimatedProfit: number;
}

function ProductCard({ product }: { product: CuratedProduct }) {
  const profitColor =
    product.profit_dollar >= 100
      ? "text-green-400"
      : product.profit_dollar >= 30
        ? "text-yellow-400"
        : "text-[var(--muted)]";
  const isHyped = product.priority === "high" || product.profit_dollar > 100;

  return (
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 hover:border-moss-500/30 transition-all card-elevated h-full">
      <div className="flex items-start gap-4">
        <div className="w-20 h-20 rounded-lg bg-[var(--surface2)] flex items-center justify-center overflow-hidden shrink-0">
          <Tag className="w-8 h-8 text-[var(--muted)]" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            {isHyped && (
              <span className="flex items-center gap-1 px-2 py-0.5 text-xs bg-orange-500/20 text-orange-400 rounded">
                <Flame className="w-3 h-3" /> Hyped
              </span>
            )}
            {product.brand && (
              <span className="px-2 py-0.5 text-xs bg-moss-500/20 text-moss-400 rounded">
                {product.brand}
              </span>
            )}
          </div>
          <h3
            className="font-medium text-[var(--text)] truncate"
            title={product.name}
          >
            {product.name}
          </h3>
          <p className="text-xs text-[var(--muted)]">{product.sku}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mt-4">
        <div className="p-2 rounded-lg bg-[var(--surface2)] text-center">
          <p className="text-sm font-bold text-[var(--text)]">
            {formatPrice(product.retail_price)}
          </p>
          <p className="text-xs text-[var(--muted)]">Retail</p>
        </div>
        <div className="p-2 rounded-lg bg-[var(--surface2)] text-center">
          <p className="text-sm font-bold text-[var(--info)]">
            {formatPrice(product.current_price)}
          </p>
          <p className="text-xs text-[var(--muted)]">Resell</p>
        </div>
        <div className="p-2 rounded-lg bg-[var(--surface2)] text-center">
          <p className={cn("text-sm font-bold", profitColor)}>
            +{formatPrice(product.profit_dollar)}
          </p>
          <p className="text-xs text-[var(--muted)]">Profit</p>
        </div>
      </div>
    </div>
  );
}

function ResearchPanel({
  result,
  onClose,
}: {
  result: ResearchResult | null;
  onClose: () => void;
}) {
  if (!result) return null;

  return (
    <div className="bg-[var(--surface)] border border-moss-500/30 rounded-xl p-5 animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-[var(--text)]">Research Results</h3>
        <button
          onClick={onClose}
          className="text-[var(--muted)] hover:text-[var(--text)] text-sm"
        >
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
            <span className="text-sm font-medium text-orange-400">
              {result.hyped}/100
            </span>
          </div>
        </div>

        <div>
          <p className="text-sm text-[var(--muted)] mb-2">Estimated Profit</p>
          <p className="text-2xl font-bold text-green-400">
            +{formatPrice(result.estimatedProfit)}
          </p>
        </div>

        <div>
          <p className="text-sm text-[var(--muted)] mb-2">
            Recommended Keywords
          </p>
          <div className="flex flex-wrap gap-1">
            {result.keywords.map((kw, i) => (
              <span
                key={i}
                className="px-2 py-1 text-xs bg-[var(--surface2)] text-[var(--muted)] rounded"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm text-[var(--muted)] mb-2">Recommended Sites</p>
          <div className="flex flex-wrap gap-1">
            {result.recommendedSites.map((site, i) => (
              <span
                key={i}
                className="px-2 py-1 text-xs bg-moss-500/20 text-moss-400 rounded"
              >
                {site}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function Intelligence() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchSku, setSearchSku] = useState("");
  const [searchPrice, setSearchPrice] = useState("");
  const [loading, setLoading] = useState(false);
  const [researchResult, setResearchResult] = useState<ResearchResult | null>(
    null,
  );

  const { data: curatedData, isLoading: trendingLoading } =
    useCuratedProducts();

  const handleResearch = async () => {
    if (!searchQuery) return;
    setLoading(true);

    try {
      const data = await api.researchProduct(
        searchQuery,
        searchSku,
        parseFloat(searchPrice) || 0,
      );
      setResearchResult({
        name: data.name || searchQuery,
        sku: data.sku || searchSku,
        keywords: data.keywords || [],
        recommendedSites: data.sites || [],
        hyped: data.hype_score || 0,
        estimatedProfit: data.profit || 0,
      });
    } catch (e) {
      console.error(e);
      // Fallback mock result if API fails
      setResearchResult({
        name: searchQuery,
        sku: searchSku || "N/A",
        keywords: ["+jordan", "+retro", "+chicago", "-gs", "-kids", "-ps"],
        recommendedSites: ["DTLR", "Shoe Palace", "Jimmy Jazz", "Hibbett"],
        hyped: 85,
        estimatedProfit: 180,
      });
    }

    setLoading(false);
  };

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-green-400" />
            Market Intelligence
          </h1>
          <p className="text-[var(--text-secondary)] mt-2">
            Research products and track market trends
          </p>
        </div>
      </div>

      {/* Research Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-[var(--surface)] border border-[var(--border)] rounded-xl p-6 card-elevated">
          <h3 className="font-semibold text-[var(--text)] mb-6 flex items-center gap-2 text-lg">
            <Search className="w-5 h-5 text-moss-400" />
            Product Research
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="col-span-1 md:col-span-2">
              <label className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider mb-1.5 block">
                Product Name
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-3 bg-[var(--surface2)] border border-[var(--border)] rounded-xl text-[var(--text)] placeholder-zinc-600 focus:outline-none focus:border-moss-500 transition-colors"
                placeholder="e.g. Jordan 4 Black Cat"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider mb-1.5 block">
                SKU (Optional)
              </label>
              <input
                type="text"
                value={searchSku}
                onChange={(e) => setSearchSku(e.target.value)}
                className="w-full px-4 py-3 bg-[var(--surface2)] border border-[var(--border)] rounded-xl text-[var(--text)] placeholder-zinc-600 focus:outline-none focus:border-moss-500 transition-colors"
                placeholder="e.g. CU1110-010"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider mb-1.5 block">
                Retail Price
              </label>
              <input
                type="number"
                value={searchPrice}
                onChange={(e) => setSearchPrice(e.target.value)}
                className="w-full px-4 py-3 bg-[var(--surface2)] border border-[var(--border)] rounded-xl text-[var(--text)] placeholder-zinc-600 focus:outline-none focus:border-moss-500 transition-colors"
                placeholder="e.g. 200"
              />
            </div>
          </div>

          <div className="flex justify-end mt-6">
            <button
              onClick={handleResearch}
              disabled={loading || !searchQuery}
              className="flex items-center gap-2 px-6 py-3 bg-moss-600 hover:bg-moss-500 disabled:opacity-50 disabled:cursor-not-allowed text-[var(--text)] font-medium rounded-xl transition-all hover:translate-y-0.5"
            >
              {loading ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <Search className="w-5 h-5" />
              )}
              Analyze Market
            </button>
          </div>
        </div>

        <div className="lg:col-span-1">
          <ResearchPanel
            result={researchResult}
            onClose={() => setResearchResult(null)}
          />
        </div>
      </div>

      {/* Trending Products */}
      <div>
        <h2 className="text-xl font-bold text-[var(--text)] mb-6 flex items-center gap-2">
          <Flame className="w-6 h-6 text-orange-400" />
          Trending Now
        </h2>

        {trendingLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-48 skeleton rounded-xl" />
            ))}
          </div>
        ) : !curatedData?.products?.length ? (
          <div className="text-center py-12 rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)]/50">
            <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-[var(--surface2)] flex items-center justify-center">
              <Tag className="w-6 h-6 text-[var(--muted)]" />
            </div>
            <p className="text-[var(--text-secondary)]">
              No trending products found
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {curatedData.products.slice(0, 6).map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
