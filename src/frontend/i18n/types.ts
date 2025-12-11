/**
 * TypeScript types for i18n translation keys.
 * This provides type safety for translation keys.
 */

import type en from './locales/en/translation.json'

// Type for translation resources
export type TranslationResources = typeof en

// Helper type to flatten nested object keys into dot notation
type FlattenKeys<T, Prefix extends string = ''> = T extends object
  ? {
      [K in keyof T]: K extends string
        ? T[K] extends object
          ? FlattenKeys<T[K], `${Prefix}${K}.`>
          : `${Prefix}${K}`
        : never
    }[keyof T]
  : never

// All available translation keys in dot notation (e.g., 'common.save', 'app.title')
export type TranslationKey = FlattenKeys<TranslationResources>

// Supported languages
export type SupportedLanguage = 'en' | 'zh'

export const SUPPORTED_LANGUAGES: { code: SupportedLanguage; name: string; nativeName: string }[] = [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'zh', name: 'Chinese', nativeName: '中文' },
]

export const DEFAULT_LANGUAGE: SupportedLanguage = 'en'

// Cache configuration
export const CACHE_CONFIG = {
  // LocalStorage key prefix
  prefix: 'i18next_',
  // Cache expiry in days
  expirationTime: 7 * 24 * 60 * 60 * 1000, // 7 days in milliseconds
  // Version for cache invalidation
  version: '1.0.0',
}
