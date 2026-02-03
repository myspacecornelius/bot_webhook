import { useState, useEffect } from 'react'
import {
  ShoppingCart,
  Play,
  Pause,
  Trash2,
  Plus,
  CheckCircle,
  XCircle,
  Clock,
  MoreVertical,
  Copy,
  PlayCircle,
  StopCircle,
  Zap
} from 'lucide-react'
import { api } from '../api/client'
import { cn } from '../lib/utils'

interface Task {
  id: string
  status: 'idle' | 'running' | 'success' | 'failed' | 'waiting'
  statusMessage: string
  siteName: string
  siteUrl: string
  productName?: string
  monitorInput: string
  size: string
  mode: string
  profileId?: string
  proxyGroupId?: string
  createdAt: string
}

const STATUS_CONFIG = {
  idle: { icon: Clock, color: 'text-[var(--muted)]', bg: 'bg-gray-500/20' },
  running: { icon: PlayCircle, color: 'text-[var(--info)]', bg: 'bg-[var(--info)]/10' },
  waiting: { icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
  success: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/20' },
  failed: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/20' },
}

function TaskRow({ task, onStart, onStop, onDelete, onDuplicate }: {
  task: Task
  onStart: () => void
  onStop: () => void
  onDelete: () => void
  onDuplicate: () => void
}) {
  const [showMenu, setShowMenu] = useState(false)
  const config = STATUS_CONFIG[task.status] || STATUS_CONFIG.idle
  const StatusIcon = config.icon

  return (
    <div className={cn(
      "group flex items-center gap-4 p-4 rounded-xl border transition-all",
      task.status === 'running' ? "bg-[var(--info)]/10 border-[var(--info)]/30" :
        task.status === 'success' ? "bg-green-500/5 border-green-500/30" :
          task.status === 'failed' ? "bg-red-500/5 border-red-500/30" :
            "bg-[var(--surface)] border-[var(--border)] hover:border-moss-500/30"
    )}>
      {/* Status */}
      <div className={cn("p-2 rounded-lg", config.bg)}>
        <StatusIcon className={cn("w-5 h-5", config.color)} />
      </div>

      {/* Site Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-[var(--text)]">{task.siteName}</span>
          <span className="px-2 py-0.5 text-xs bg-moss-500/20 text-moss-400 rounded">
            {task.mode}
          </span>
        </div>
        <p className="text-sm text-[var(--muted)] truncate">{task.monitorInput}</p>
      </div>

      {/* Size */}
      <div className="text-center px-4">
        <p className="text-lg font-bold text-[var(--text)]">{task.size || 'Any'}</p>
        <p className="text-xs text-[var(--muted)]">Size</p>
      </div>

      {/* Status Message */}
      <div className="w-48">
        <p className={cn("text-sm truncate", config.color)}>{task.statusMessage || 'Ready'}</p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {task.status === 'running' ? (
          <button
            onClick={onStop}
            className="p-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
            title="Stop Task"
          >
            <Pause className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={onStart}
            className="p-2 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors"
            title="Start Task"
          >
            <Play className="w-4 h-4" />
          </button>
        )}

        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 rounded-lg bg-[var(--surface2)] text-[var(--muted)] hover:text-[var(--text)] transition-colors"
            title="More Options"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          {showMenu && (
            <div className="absolute right-0 top-full mt-1 w-36 py-1 bg-[var(--surface2)] border border-[var(--border)] rounded-lg shadow-xl z-10">
              <button
                onClick={() => { onDuplicate(); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--muted)] hover:bg-moss-500/20 hover:text-[var(--text)]"
              >
                <Copy className="w-4 h-4" /> Duplicate
              </button>
              <button
                onClick={() => { onDelete(); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/20"
              >
                <Trash2 className="w-4 h-4" /> Delete
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function QuickTaskModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [url, setUrl] = useState('')
  const [sizes, setSizes] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [autoStart, setAutoStart] = useState(true)
  const [loading, setLoading] = useState(false)
  const [detected, setDetected] = useState<any>(null)

  const handleSubmit = async () => {
    if (!url.trim()) return

    setLoading(true)
    try {
      const result = await api.createQuickTask({
        url: url.trim(),
        sizes: sizes ? sizes.split(',').map(s => s.trim()).filter(Boolean) : undefined,
        quantity,
        mode: 'fast',
        auto_start: autoStart,
      })

      setDetected({ message: result.message })
      onCreated()

      // Show success briefly then close
      setTimeout(() => onClose(), 1500)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onClose}>
      <div className="w-full max-w-md bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-[var(--info)]/10 rounded-lg">
            <Zap className="w-5 h-5 text-[var(--info)]" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-[var(--text)]">Quick Task</h2>
            <p className="text-sm text-[var(--muted)]">Paste a URL and we'll do the rest</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-[var(--muted)] mb-2">Product URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full px-4 py-3 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] placeholder-gray-500 focus:outline-none focus:border-[var(--info)]"
              placeholder="https://kith.com/products/..."
              autoFocus
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-[var(--muted)] mb-2">Sizes (optional)</label>
              <input
                type="text"
                value={sizes}
                onChange={(e) => setSizes(e.target.value)}
                className="w-full px-4 py-2.5 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] placeholder-gray-500 focus:outline-none focus:border-[var(--info)]"
                placeholder="10, 10.5, 11"
              />
            </div>
            <div>
              <label className="block text-sm text-[var(--muted)] mb-2">Quantity</label>
              <input
                type="number"
                min="1"
                max="20"
                value={quantity}
                onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                className="w-full px-4 py-2.5 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] focus:outline-none focus:border-[var(--info)]"
              />
            </div>
          </div>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={autoStart}
              onChange={(e) => setAutoStart(e.target.checked)}
              className="w-4 h-4 rounded border-gray-600 bg-[var(--surface2)] text-[var(--info)] focus:ring-moss-500"
            />
            <span className="text-sm text-[var(--muted)]">Auto-start task after creation</span>
          </label>

          {detected && (
            <div className="p-3 bg-[var(--primary)]/10 border border-moss-500/30 rounded-lg">
              <p className="text-sm text-[var(--primary)] font-medium">✓ Task created!</p>
              <p className="text-xs text-[var(--muted)] mt-1">
                {detected.site_name} • {detected.site_type} • {detected.monitor_input}
              </p>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-[var(--muted)] hover:text-[var(--text)] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !url.trim()}
            className="flex items-center gap-2 px-5 py-2 bg-[var(--info)] hover:bg-[var(--primary)] disabled:opacity-50 text-[var(--text)] font-medium rounded-lg transition-colors"
          >
            <Zap className="w-4 h-4" />
            {loading ? 'Creating...' : `Create ${quantity > 1 ? `${quantity} Tasks` : 'Task'}`}
          </button>
        </div>
      </div>
    </div>
  )
}

function CreateTaskModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [formData, setFormData] = useState({
    siteName: 'DTLR',
    siteUrl: 'https://www.dtlr.com',
    monitorInput: '',
    sizes: '',
    mode: 'safe',
    profileId: '',
    proxyGroupId: '',
    quantity: 1,
  })
  const [loading, setLoading] = useState(false)

  const sites = [
    { name: 'DTLR', url: 'https://www.dtlr.com' },
    { name: 'Shoe Palace', url: 'https://www.shoepalace.com' },
    { name: 'Jimmy Jazz', url: 'https://www.jimmyjazz.com' },
    { name: 'Hibbett', url: 'https://www.hibbett.com' },
    { name: 'Kith', url: 'https://kith.com' },
    { name: 'Undefeated', url: 'https://undefeated.com' },
    { name: 'Bodega', url: 'https://bdgastore.com' },
  ]

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const sizes = formData.sizes.split(',').map(s => s.trim()).filter(Boolean)

      for (let i = 0; i < formData.quantity; i++) {
        await api.createTask({
          site_name: formData.siteName,
          site_url: formData.siteUrl,
          monitor_input: formData.monitorInput,
          sizes: sizes,
          mode: formData.mode,
          profile_id: formData.profileId || undefined,
          proxy_group_id: formData.proxyGroupId || undefined,
        })
      }

      onCreated()
      onClose()
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onClose}>
      <div className="w-full max-w-lg bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-[var(--text)] mb-6">Create Task</h2>

        <div className="space-y-4">
          {/* Site Selection */}
          <div>
            <label className="block text-sm text-[var(--muted)] mb-2">Site</label>
            <select
              value={formData.siteName}
              onChange={(e) => {
                const site = sites.find(s => s.name === e.target.value)
                setFormData({ ...formData, siteName: e.target.value, siteUrl: site?.url || '' })
              }}
              className="w-full px-4 py-2.5 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] focus:outline-none focus:border-moss-500"
            >
              {sites.map(site => (
                <option key={site.name} value={site.name}>{site.name}</option>
              ))}
            </select>
          </div>

          {/* Keywords/SKU */}
          <div>
            <label className="block text-sm text-[var(--muted)] mb-2">Keywords / SKU / URL</label>
            <input
              type="text"
              value={formData.monitorInput}
              onChange={(e) => setFormData({ ...formData, monitorInput: e.target.value })}
              className="w-full px-4 py-2.5 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] placeholder-gray-500 focus:outline-none focus:border-moss-500"
              placeholder="+jordan +retro +chicago -gs -kids"
            />
          </div>

          {/* Sizes */}
          <div>
            <label className="block text-sm text-[var(--muted)] mb-2">Sizes (comma separated)</label>
            <input
              type="text"
              value={formData.sizes}
              onChange={(e) => setFormData({ ...formData, sizes: e.target.value })}
              className="w-full px-4 py-2.5 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] placeholder-gray-500 focus:outline-none focus:border-moss-500"
              placeholder="10, 10.5, 11, 11.5, 12"
            />
          </div>

          {/* Mode and Quantity */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-[var(--muted)] mb-2">Mode</label>
              <select
                value={formData.mode}
                onChange={(e) => setFormData({ ...formData, mode: e.target.value })}
                className="w-full px-4 py-2.5 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] focus:outline-none focus:border-moss-500"
              >
                <option value="safe">Safe</option>
                <option value="normal">Normal</option>
                <option value="fast">Fast</option>
                <option value="preload">Preload</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-[var(--muted)] mb-2">Quantity</label>
              <input
                type="number"
                min="1"
                max="50"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 1 })}
                className="w-full px-4 py-2.5 bg-[var(--surface2)] border border-[var(--border)] rounded-lg text-[var(--text)] focus:outline-none focus:border-moss-500"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-[var(--muted)] hover:text-[var(--text)] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !formData.monitorInput}
            className="flex items-center gap-2 px-5 py-2 bg-moss-600 hover:bg-moss-500 disabled:opacity-50 text-[var(--text)] font-medium rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create {formData.quantity > 1 ? `${formData.quantity} Tasks` : 'Task'}
          </button>
        </div>
      </div>
    </div>
  )
}

export function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [showQuickTask, setShowQuickTask] = useState(false)
  const [filter, setFilter] = useState<'all' | 'running' | 'idle'>('all')

  const fetchTasks = async () => {
    try {
      const data = await api.getTasks()
      setTasks((data.tasks || []) as any)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchTasks()
    // Reduced polling frequency - WebSocket handles real-time task updates
    const interval = setInterval(fetchTasks, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleStartTask = async (id: string) => {
    try {
      await api.startTask(id)
      fetchTasks()
    } catch (e) {
      console.error(e)
    }
  }

  const handleStopTask = async (id: string) => {
    try {
      await api.stopTask(id)
      fetchTasks()
    } catch (e) {
      console.error(e)
    }
  }

  const handleDeleteTask = async (id: string) => {
    try {
      await api.deleteTask(id)
      fetchTasks()
    } catch (e) {
      console.error(e)
    }
  }

  const handleStartAll = async () => {
    try {
      await api.startAllTasks()
      fetchTasks()
    } catch (e) {
      console.error(e)
    }
  }

  const handleStopAll = async () => {
    try {
      await api.stopAllTasks()
      fetchTasks()
    } catch (e) {
      console.error(e)
    }
  }

  const filteredTasks = tasks.filter(t => {
    if (filter === 'running') return t.status === 'running'
    if (filter === 'idle') return t.status === 'idle'
    return true
  })

  const runningCount = tasks.filter(t => t.status === 'running').length
  const successCount = tasks.filter(t => t.status === 'success').length

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)] flex items-center gap-3">
            <ShoppingCart className="w-7 h-7 text-moss-400" />
            Tasks
          </h1>
          <p className="text-[var(--muted)] text-sm mt-1">
            {tasks.length} total • {runningCount} running • {successCount} successful
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Filter */}
          <div className="flex items-center gap-1 p-1 bg-[var(--surface)] rounded-lg border border-[var(--border)]">
            {(['all', 'running', 'idle'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  "px-3 py-1.5 text-sm font-medium rounded-md transition-colors capitalize",
                  filter === f
                    ? "bg-moss-500/20 text-moss-400"
                    : "text-[var(--muted)] hover:text-[var(--text)]"
                )}
              >
                {f}
              </button>
            ))}
          </div>

          <button
            onClick={handleStopAll}
            className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/30 transition-colors"
          >
            <StopCircle className="w-4 h-4" />
            Stop All
          </button>

          <button
            onClick={handleStartAll}
            className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 border border-green-500/30 rounded-lg hover:bg-green-500/30 transition-colors"
          >
            <PlayCircle className="w-4 h-4" />
            Start All
          </button>

          <button
            onClick={() => setShowQuickTask(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--info)]/10 text-[var(--info)] border border-[var(--info)]/30 rounded-lg hover:bg-[var(--info)]/10 transition-colors"
          >
            <Zap className="w-4 h-4" />
            Quick Task
          </button>

          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-5 py-2 bg-moss-600 hover:bg-moss-500 text-[var(--text)] font-medium rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Task
          </button>
        </div>
      </div>

      {/* Tasks List */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-moss-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-[var(--muted)]">
          <ShoppingCart className="w-16 h-16 mb-4 opacity-30" />
          <p className="text-lg font-medium">No tasks yet</p>
          <p className="text-sm mb-4">Create a task to start checking out products</p>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-moss-600 hover:bg-moss-500 text-[var(--text)] font-medium rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Your First Task
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredTasks.map(task => (
            <TaskRow
              key={task.id}
              task={task}
              onStart={() => handleStartTask(task.id)}
              onStop={() => handleStopTask(task.id)}
              onDelete={() => handleDeleteTask(task.id)}
              onDuplicate={() => {/* TODO */ }}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <CreateTaskModal
          onClose={() => setShowCreate(false)}
          onCreated={fetchTasks}
        />
      )}

      {/* Quick Task Modal */}
      {showQuickTask && (
        <QuickTaskModal
          onClose={() => setShowQuickTask(false)}
          onCreated={fetchTasks}
        />
      )}
    </div>
  )
}
