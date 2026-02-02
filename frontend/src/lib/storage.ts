import type { MonitorSetup } from '../types/monitor-setup'

const STORAGE_KEY = 'monitorSetups.v1'

// Storage interface that works in both web and Electron
interface StorageAdapter {
  get(key: string): Promise<string | null>
  set(key: string, value: string): Promise<void>
  delete(key: string): Promise<void>
}

// Web localStorage adapter
class LocalStorageAdapter implements StorageAdapter {
  async get(key: string): Promise<string | null> {
    return localStorage.getItem(key)
  }

  async set(key: string, value: string): Promise<void> {
    localStorage.setItem(key, value)
  }

  async delete(key: string): Promise<void> {
    localStorage.removeItem(key)
  }
}

// Electron store adapter (uses IPC)
class ElectronStorageAdapter implements StorageAdapter {
  async get(key: string): Promise<string | null> {
    if (typeof window !== 'undefined' && (window as any).electron) {
      return (window as any).electron.store.get(key)
    }
    return null
  }

  async set(key: string, value: string): Promise<void> {
    if (typeof window !== 'undefined' && (window as any).electron) {
      await (window as any).electron.store.set(key, value)
    }
  }

  async delete(key: string): Promise<void> {
    if (typeof window !== 'undefined' && (window as any).electron) {
      await (window as any).electron.store.delete(key)
    }
  }
}

// Auto-detect environment
const storage: StorageAdapter = 
  typeof window !== 'undefined' && (window as any).electron?.isElectron
    ? new ElectronStorageAdapter()
    : new LocalStorageAdapter()

export class MonitorSetupStore {
  async getAll(): Promise<MonitorSetup[]> {
    const data = await storage.get(STORAGE_KEY)
    if (!data) return []
    
    try {
      return JSON.parse(data)
    } catch {
      return []
    }
  }

  async save(setup: MonitorSetup): Promise<void> {
    const setups = await this.getAll()
    const index = setups.findIndex(s => s.id === setup.id)
    
    if (index >= 0) {
      setups[index] = { ...setup, updatedAt: Date.now() }
    } else {
      setups.push(setup)
    }
    
    await storage.set(STORAGE_KEY, JSON.stringify(setups))
  }

  async delete(id: string): Promise<void> {
    const setups = await this.getAll()
    const filtered = setups.filter(s => s.id !== id)
    await storage.set(STORAGE_KEY, JSON.stringify(filtered))
  }

  async get(id: string): Promise<MonitorSetup | null> {
    const setups = await this.getAll()
    return setups.find(s => s.id === id) || null
  }

  async togglePin(id: string): Promise<void> {
    const setups = await this.getAll()
    const setup = setups.find(s => s.id === id)
    if (setup) {
      setup.pinned = !setup.pinned
      setup.updatedAt = Date.now()
      await storage.set(STORAGE_KEY, JSON.stringify(setups))
    }
  }

  async export(): Promise<string> {
    const setups = await this.getAll()
    return JSON.stringify(setups, null, 2)
  }

  async import(json: string): Promise<void> {
    const imported = JSON.parse(json) as MonitorSetup[]
    const existing = await this.getAll()
    const merged = [...existing, ...imported]
    await storage.set(STORAGE_KEY, JSON.stringify(merged))
  }
}

export const setupStore = new MonitorSetupStore()
