/**
 * Hook for getting localized tool properties.
 *
 * Returns localized name, description, and category based on current i18n language.
 * Falls back to default (English) values if translation is not available.
 *
 * @example
 * ```tsx
 * const { name, description } = useLocalizedTool(tool)
 * return <div>{name}: {description}</div>
 * ```
 */

import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import type { ButtonConfig } from '../types'

export interface LocalizedTool {
  /** Localized tool name */
  name: string
  /** Localized tool description */
  description: string
  /** Localized category name */
  category: string
}

/**
 * Get localized tool properties based on current language.
 *
 * @param tool - The tool configuration object
 * @returns Object with localized name, description, and category
 */
export function useLocalizedTool(tool: ButtonConfig): LocalizedTool {
  const { i18n } = useTranslation()

  return useMemo(() => {
    // Normalize language code (e.g., zh-CN -> zh)
    const lang = (i18n.language || 'en').split('-')[0]

    // Helper to get localized value with fallback
    const getLocalized = (
      defaultValue: string,
      localizedValues: Record<string, string | undefined>
    ): string => {
      // Check for language-specific value
      const localizedKey = `${lang}` as keyof typeof localizedValues
      const localized = localizedValues[localizedKey]
      if (localized) return localized

      // Fall back to default
      return defaultValue
    }

    return {
      name: getLocalized(tool.name, { zh: tool.name_zh }),
      description: getLocalized(tool.description, { zh: tool.description_zh }),
      category: getLocalized(tool.category, { zh: tool.category_zh }),
    }
  }, [tool, i18n.language])
}

/**
 * Get localized property for a single tool field.
 * Useful when you only need one property.
 *
 * @param value - Default value
 * @param localizedValue - Localized value (or undefined)
 * @returns Localized value if current language matches, otherwise default
 */
export function useLocalizedValue(
  value: string,
  localizedValue?: string
): string {
  const { i18n } = useTranslation()

  return useMemo(() => {
    const lang = (i18n.language || 'en').split('-')[0]

    // Return localized value for Chinese, otherwise default
    if (lang === 'zh' && localizedValue) {
      return localizedValue
    }

    return value
  }, [value, localizedValue, i18n.language])
}

/**
 * Batch localize multiple tools.
 * More efficient than calling useLocalizedTool for each tool.
 *
 * @param tools - Array of tool configurations
 * @returns Array of localized tool objects
 */
export function useLocalizedTools(tools: ButtonConfig[]): LocalizedTool[] {
  const { i18n } = useTranslation()

  return useMemo(() => {
    const lang = (i18n.language || 'en').split('-')[0]

    return tools.map((tool) => ({
      name: lang === 'zh' && tool.name_zh ? tool.name_zh : tool.name,
      description:
        lang === 'zh' && tool.description_zh
          ? tool.description_zh
          : tool.description,
      category:
        lang === 'zh' && tool.category_zh ? tool.category_zh : tool.category,
    }))
  }, [tools, i18n.language])
}

