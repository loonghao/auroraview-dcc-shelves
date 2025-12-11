/**
 * i18n configuration with LocalStorage caching and language detection.
 *
 * Features:
 * - Offline-first: All translations bundled locally
 * - LocalStorage caching for user preferences
 * - Automatic browser language detection
 * - TypeScript support
 */

import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

// Import translation resources
import enTranslation from './locales/en/translation.json'
import zhTranslation from './locales/zh/translation.json'

import { DEFAULT_LANGUAGE, CACHE_CONFIG } from './types'

// Bundle all translations (offline-first approach)
const resources = {
  en: { translation: enTranslation },
  zh: { translation: zhTranslation },
}

// Initialize i18n
i18n
  // Detect user language from browser
  .use(LanguageDetector)
  // Pass i18n instance to react-i18next
  .use(initReactI18next)
  // Initialize i18n
  .init({
    resources,
    fallbackLng: DEFAULT_LANGUAGE,
    supportedLngs: ['en', 'zh'],
    // Normalize language codes (e.g., zh-CN -> zh)
    load: 'languageOnly',

    // Language detection options
    detection: {
      // Order of detection methods - localStorage first for user preference
      order: ['localStorage', 'querystring', 'navigator'],
      // Keys to lookup in localStorage
      lookupQuerystring: 'lng',
      lookupLocalStorage: 'i18nextLng',
      // Cache user language to localStorage
      caches: ['localStorage'],
      // Don't check cookie
      lookupCookie: undefined,
    },

    interpolation: {
      // React already escapes values
      escapeValue: false,
    },

    // React settings
    react: {
      // Use Suspense for async loading (not needed with bundled resources)
      useSuspense: false,
      // Bind to language changed event to trigger re-renders
      bindI18n: 'languageChanged loaded',
      bindI18nStore: 'added removed',
    },

    // Debug mode (disable in production)
    debug: import.meta.env.DEV,
  })

// Expose i18n to window for debugging
if (typeof window !== 'undefined') {
  (window as unknown as { i18next: typeof i18n }).i18next = i18n
}

// Export for use in components
export default i18n

// Re-export types
export * from './types'

/**
 * Helper function to get cached language preference.
 */
export function getCachedLanguage(): string | null {
  try {
    return localStorage.getItem('i18nextLng')
  } catch {
    return null
  }
}

/**
 * Helper function to set language and cache it.
 */
export function setLanguage(lang: string): Promise<void> {
  return new Promise((resolve) => {
    i18n.changeLanguage(lang, () => {
      try {
        localStorage.setItem('i18nextLng', lang)
        localStorage.setItem(`${CACHE_CONFIG.prefix}timestamp`, Date.now().toString())
      } catch (e) {
        console.warn('[i18n] Failed to cache language preference:', e)
      }
      resolve()
    })
  })
}

/**
 * Check if cache is valid based on version and expiration.
 */
export function isCacheValid(): boolean {
  try {
    const timestamp = localStorage.getItem(`${CACHE_CONFIG.prefix}timestamp`)
    const version = localStorage.getItem(`${CACHE_CONFIG.prefix}version`)

    if (!timestamp || version !== CACHE_CONFIG.version) {
      return false
    }

    const elapsed = Date.now() - parseInt(timestamp, 10)
    return elapsed < CACHE_CONFIG.expirationTime
  } catch {
    return false
  }
}

/**
 * Clear i18n cache (useful for force refresh).
 */
export function clearI18nCache(): void {
  try {
    const keysToRemove = Object.keys(localStorage).filter(key =>
      key.startsWith(CACHE_CONFIG.prefix) || key === 'i18nextLng'
    )
    keysToRemove.forEach(key => localStorage.removeItem(key))
  } catch (e) {
    console.warn('[i18n] Failed to clear cache:', e)
  }
}
