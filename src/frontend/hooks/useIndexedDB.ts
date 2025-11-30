/**
 * IndexedDB hook for persistent storage of user settings.
 */

import { useState, useEffect, useCallback } from 'react'

const DB_NAME = 'dcc-shelves-db'
const DB_VERSION = 1
const STORE_NAME = 'settings'

export interface BannerSettings {
  imageUrl?: string        // URL or base64 data
  imageType: 'url' | 'local'
  objectFit: 'cover' | 'contain' | 'fill'
  objectPosition: string   // e.g., 'center', 'top', '50% 30%'
  scale: number           // 1.0 = 100%
  brightness: number      // 0-200, default 100
}

export const DEFAULT_BANNER_SETTINGS: BannerSettings = {
  imageUrl: '/image/banner.png',
  imageType: 'local',
  objectFit: 'cover',
  objectPosition: 'center',
  scale: 1.0,
  brightness: 100,
}

let dbInstance: IDBDatabase | null = null

const openDB = (): Promise<IDBDatabase> => {
  return new Promise((resolve, reject) => {
    if (dbInstance) {
      resolve(dbInstance)
      return
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onerror = () => reject(request.error)
    
    request.onsuccess = () => {
      dbInstance = request.result
      resolve(dbInstance)
    }

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'key' })
      }
    }
  })
}

export function useIndexedDB<T>(key: string, defaultValue: T) {
  const [value, setValue] = useState<T>(defaultValue)
  const [isLoading, setIsLoading] = useState(true)

  // Load value from IndexedDB
  useEffect(() => {
    const load = async () => {
      try {
        const db = await openDB()
        const tx = db.transaction(STORE_NAME, 'readonly')
        const store = tx.objectStore(STORE_NAME)
        const request = store.get(key)

        request.onsuccess = () => {
          if (request.result?.value !== undefined) {
            setValue(request.result.value)
          }
          setIsLoading(false)
        }

        request.onerror = () => {
          console.error('[IndexedDB] Failed to load:', key)
          setIsLoading(false)
        }
      } catch (err) {
        console.error('[IndexedDB] Error:', err)
        setIsLoading(false)
      }
    }
    load()
  }, [key])

  // Save value to IndexedDB
  const save = useCallback(async (newValue: T) => {
    setValue(newValue)
    try {
      const db = await openDB()
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      store.put({ key, value: newValue })
    } catch (err) {
      console.error('[IndexedDB] Failed to save:', err)
    }
  }, [key])

  return { value, save, isLoading }
}

// Helper to convert File to base64
export const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

