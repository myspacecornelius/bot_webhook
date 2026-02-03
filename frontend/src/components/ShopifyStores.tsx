import { useState, useEffect } from 'react';
import { Plus, Trash2, Edit2, RefreshCw, TrendingUp, Clock, CheckCircle, XCircle } from 'lucide-react';
import { api } from '../api/client';

interface ShopifyStore {
  id: string;
  name: string;
  url: string;
  enabled: boolean;
  delay_ms: number;
  target_sizes: string[];
  last_check: string | null;
  success_count: number;
  error_count: number;
  products_found: number;
}

interface RestockEvent {
  product_id: string;
  product_title: string;
  store_name: string;
  sizes_restocked: string[];
  timestamp: string;
  price: number | null;
  image_url: string | null;
}

interface RestockPattern {
  product_title: string;
  store_name: string;
  restock_count: number;
  last_restock: string | null;
  average_interval_hours: number | null;
  next_predicted_restock: string | null;
  confidence_score: number;
}

export default function ShopifyStores() {
  const [stores, setStores] = useState<ShopifyStore[]>([]);
  const [restockHistory, setRestockHistory] = useState<RestockEvent[]>([]);
  const [restockPatterns, setRestockPatterns] = useState<RestockPattern[]>([]);
  const [restockStats, setRestockStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'stores' | 'restocks' | 'patterns'>('stores');

  // Add store form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newStore, setNewStore] = useState({
    name: '',
    url: '',
    delay_ms: 3000,
    target_sizes: ''
  });

  // Edit store
  const [editingStore, setEditingStore] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<any>({});

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [activeTab]);

  const loadData = async () => {
    try {
      // Load stores
      const storesData = await api.getShopifyStores();
      setStores((storesData.stores || []) as any);

      // Load restock data based on active tab
      if (activeTab === 'restocks') {
        const historyData = await api.getRestockHistory(24, 50);
        setRestockHistory((historyData.history || []) as any);

        const statsData = await api.getRestockStats();
        setRestockStats(statsData);
      } else if (activeTab === 'patterns') {
        const patternsData = await api.getRestockPatterns(2);
        setRestockPatterns((patternsData.patterns || []) as any);
      }

      setLoading(false);
    } catch (error) {
      console.error('Failed to load data:', error);
      setLoading(false);
    }
  };

  const handleAddStore = async () => {
    try {
      const sizes = newStore.target_sizes
        .split(',')
        .map(s => s.trim())
        .filter(s => s);

      await api.addShopifyStore(
        newStore.name,
        newStore.url,
        newStore.delay_ms,
        sizes.length > 0 ? sizes : undefined
      );

      setShowAddForm(false);
      setNewStore({ name: '', url: '', delay_ms: 3000, target_sizes: '' });
      loadData();
    } catch (error) {
      console.error('Failed to add store:', error);
      alert('Failed to add store');
    }
  };

  const handleUpdateStore = async (storeId: string) => {
    try {
      const updates: any = {};

      if (editForm.enabled !== undefined) updates.enabled = editForm.enabled;
      if (editForm.delay_ms) updates.delay_ms = parseInt(editForm.delay_ms);
      if (editForm.target_sizes !== undefined) {
        const sizes = editForm.target_sizes
          .split(',')
          .map((s: string) => s.trim())
          .filter((s: string) => s);
        updates.target_sizes = sizes;
      }

      await api.updateShopifyStore(storeId, updates);
      setEditingStore(null);
      setEditForm({});
      loadData();
    } catch (error) {
      console.error('Failed to update store:', error);
      alert('Failed to update store');
    }
  };

  const handleDeleteStore = async (storeId: string, storeName: string) => {
    if (!confirm(`Delete store "${storeName}"?`)) return;

    try {
      await api.deleteShopifyStore(storeId);
      loadData();
    } catch (error) {
      console.error('Failed to delete store:', error);
      alert('Failed to delete store');
    }
  };

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`;
    return `${Math.floor(minutes / 1440)}d ago`;
  };

  const formatInterval = (hours: number | null) => {
    if (!hours) return 'Unknown';
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    if (hours < 24) return `${Math.round(hours)}h`;
    return `${Math.round(hours / 24)}d`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Shopify Stores</h2>
          <p className="text-[var(--muted)] text-sm mt-1">
            Manage monitored stores and track restocks
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Store
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-700">
        <button
          onClick={() => setActiveTab('stores')}
          className={`px-4 py-2 font-medium transition-colors ${activeTab === 'stores'
              ? 'text-blue-500 border-b-2 border-blue-500'
              : 'text-[var(--muted)] hover:text-[var(--muted)]'
            }`}
        >
          Stores ({stores.length})
        </button>
        <button
          onClick={() => setActiveTab('restocks')}
          className={`px-4 py-2 font-medium transition-colors ${activeTab === 'restocks'
              ? 'text-blue-500 border-b-2 border-blue-500'
              : 'text-[var(--muted)] hover:text-[var(--muted)]'
            }`}
        >
          <TrendingUp className="w-4 h-4 inline mr-1" />
          Restocks
        </button>
        <button
          onClick={() => setActiveTab('patterns')}
          className={`px-4 py-2 font-medium transition-colors ${activeTab === 'patterns'
              ? 'text-blue-500 border-b-2 border-blue-500'
              : 'text-[var(--muted)] hover:text-[var(--muted)]'
            }`}
        >
          <Clock className="w-4 h-4 inline mr-1" />
          Patterns
        </button>
      </div>

      {/* Add Store Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold mb-4">Add Shopify Store</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Store Name</label>
                <input
                  type="text"
                  value={newStore.name}
                  onChange={(e) => setNewStore({ ...newStore, name: e.target.value })}
                  placeholder="e.g., Kith"
                  className="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Store URL</label>
                <input
                  type="text"
                  value={newStore.url}
                  onChange={(e) => setNewStore({ ...newStore, url: e.target.value })}
                  placeholder="https://kith.com"
                  className="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Monitor Delay (ms)</label>
                <input
                  type="number"
                  value={newStore.delay_ms}
                  onChange={(e) => setNewStore({ ...newStore, delay_ms: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Target Sizes (comma-separated)</label>
                <input
                  type="text"
                  value={newStore.target_sizes}
                  onChange={(e) => setNewStore({ ...newStore, target_sizes: e.target.value })}
                  placeholder="10, 10.5, 11, 11.5"
                  className="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 outline-none"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button
                onClick={handleAddStore}
                disabled={!newStore.name || !newStore.url}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded transition-colors"
              >
                Add Store
              </button>
              <button
                onClick={() => setShowAddForm(false)}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stores Tab */}
      {activeTab === 'stores' && (
        <div className="grid gap-4">
          {stores.length === 0 ? (
            <div className="text-center py-12 text-[var(--muted)]">
              <p>No stores configured</p>
              <button
                onClick={() => setShowAddForm(true)}
                className="mt-4 text-blue-500 hover:text-blue-400"
              >
                Add your first store
              </button>
            </div>
          ) : (
            stores.map((store) => (
              <div
                key={store.id}
                className="bg-gray-800 rounded-lg p-4 border border-gray-700"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold">{store.name}</h3>
                      {store.enabled ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-[var(--muted)]" />
                      )}
                    </div>
                    <p className="text-sm text-[var(--muted)] mt-1">{store.url}</p>

                    {editingStore === store.id ? (
                      <div className="mt-3 space-y-2">
                        <input
                          type="number"
                          placeholder="Delay (ms)"
                          value={editForm.delay_ms || store.delay_ms}
                          onChange={(e) => setEditForm({ ...editForm, delay_ms: e.target.value })}
                          className="w-full px-3 py-1 bg-gray-700 rounded text-sm"
                        />
                        <input
                          type="text"
                          placeholder="Target sizes (comma-separated)"
                          value={editForm.target_sizes !== undefined ? editForm.target_sizes : store.target_sizes.join(', ')}
                          onChange={(e) => setEditForm({ ...editForm, target_sizes: e.target.value })}
                          className="w-full px-3 py-1 bg-gray-700 rounded text-sm"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleUpdateStore(store.id)}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => {
                              setEditingStore(null);
                              setEditForm({});
                            }}
                            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-3 flex flex-wrap gap-4 text-sm">
                        <div>
                          <span className="text-[var(--muted)]">Delay:</span>{' '}
                          <span className="text-[var(--text)]">{store.delay_ms}ms</span>
                        </div>
                        <div>
                          <span className="text-[var(--muted)]">Sizes:</span>{' '}
                          <span className="text-[var(--text)]">
                            {store.target_sizes.length > 0 ? store.target_sizes.join(', ') : 'All'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[var(--muted)]">Last Check:</span>{' '}
                          <span className="text-[var(--text)]">{formatTimestamp(store.last_check)}</span>
                        </div>
                      </div>
                    )}

                    <div className="mt-3 flex gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>{store.success_count} checks</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <XCircle className="w-4 h-4 text-red-500" />
                        <span>{store.error_count} errors</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <TrendingUp className="w-4 h-4 text-blue-500" />
                        <span>{store.products_found} products</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setEditingStore(store.id);
                        setEditForm({});
                      }}
                      className="p-2 hover:bg-gray-700 rounded transition-colors"
                      title="Edit"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteStore(store.id, store.name)}
                      className="p-2 hover:bg-red-900/50 rounded transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Restocks Tab */}
      {activeTab === 'restocks' && (
        <div className="space-y-4">
          {restockStats && (
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-2xl font-bold text-blue-500">{restockStats.restocks_last_24h}</div>
                <div className="text-sm text-[var(--muted)]">Last 24h</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-500">{restockStats.restocks_last_7d}</div>
                <div className="text-sm text-[var(--muted)]">Last 7 days</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-2xl font-bold text-moss-500">{restockStats.patterns_detected}</div>
                <div className="text-sm text-[var(--muted)]">Patterns</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-2xl font-bold text-orange-500">{restockStats.predicted_restocks_24h}</div>
                <div className="text-sm text-[var(--muted)]">Predicted</div>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {restockHistory.length === 0 ? (
              <div className="text-center py-12 text-[var(--muted)]">
                No restocks detected in the last 24 hours
              </div>
            ) : (
              restockHistory.map((event, idx) => (
                <div key={idx} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-start gap-4">
                    {event.image_url && (
                      <img
                        src={event.image_url}
                        alt={event.product_title}
                        className="w-16 h-16 object-cover rounded"
                      />
                    )}
                    <div className="flex-1">
                      <h4 className="font-semibold">{event.product_title}</h4>
                      <p className="text-sm text-[var(--muted)] mt-1">{event.store_name}</p>
                      <div className="flex gap-2 mt-2">
                        {event.sizes_restocked.map((size) => (
                          <span
                            key={size}
                            className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-xs"
                          >
                            {size}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="text-right">
                      {event.price && (
                        <div className="text-lg font-bold text-green-500">${event.price}</div>
                      )}
                      <div className="text-sm text-[var(--muted)] mt-1">
                        {formatTimestamp(event.timestamp)}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Patterns Tab */}
      {activeTab === 'patterns' && (
        <div className="space-y-3">
          {restockPatterns.length === 0 ? (
            <div className="text-center py-12 text-[var(--muted)]">
              No restock patterns detected yet
              <p className="text-sm mt-2">Patterns appear after 2+ restocks of the same product</p>
            </div>
          ) : (
            restockPatterns.map((pattern, idx) => (
              <div key={idx} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold">{pattern.product_title}</h4>
                    <p className="text-sm text-[var(--muted)] mt-1">{pattern.store_name}</p>
                    <div className="flex gap-4 mt-3 text-sm">
                      <div>
                        <span className="text-[var(--muted)]">Restocks:</span>{' '}
                        <span className="text-[var(--text)] font-medium">{pattern.restock_count}</span>
                      </div>
                      <div>
                        <span className="text-[var(--muted)]">Interval:</span>{' '}
                        <span className="text-[var(--text)] font-medium">
                          {formatInterval(pattern.average_interval_hours)}
                        </span>
                      </div>
                      <div>
                        <span className="text-[var(--muted)]">Confidence:</span>{' '}
                        <span className={`font-medium ${pattern.confidence_score > 0.7 ? 'text-green-500' :
                            pattern.confidence_score > 0.4 ? 'text-yellow-500' :
                              'text-red-500'
                          }`}>
                          {Math.round(pattern.confidence_score * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>
                  {pattern.next_predicted_restock && (
                    <div className="text-right">
                      <div className="text-sm text-[var(--muted)]">Next Predicted</div>
                      <div className="text-lg font-bold text-blue-500">
                        {formatTimestamp(pattern.next_predicted_restock)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
