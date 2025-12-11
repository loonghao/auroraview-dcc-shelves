/**
 * Language switcher component with dropdown menu.
 * Shows current language indicator for easy identification.
 */

import React, { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronDown, Check } from 'lucide-react'
import { SUPPORTED_LANGUAGES, type SupportedLanguage } from '../i18n/types'
import { setLanguage } from '../i18n'

/** Language display info with flag/icon */
const LANGUAGE_DISPLAY: Record<string, { flag: string; short: string }> = {
  en: { flag: '🇺🇸', short: 'EN' },
  zh: { flag: '🇨🇳', short: '中' },
}

interface LanguageSwitcherProps {
  /** Additional class names */
  className?: string
}

export const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({
  className = ''
}) => {
  const { i18n } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // Normalize language code (e.g., zh-CN -> zh, en-US -> en)
  const normalizedLang = (i18n.language || 'en').split('-')[0] as SupportedLanguage
  const currentLangInfo = SUPPORTED_LANGUAGES.find(l => l.code === normalizedLang) || SUPPORTED_LANGUAGES[0]
  const currentDisplay = LANGUAGE_DISPLAY[normalizedLang] || LANGUAGE_DISPLAY.en

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLanguageChange = async (langCode: SupportedLanguage) => {
    await setLanguage(langCode)
    setIsOpen(false)
  }

  return (
    <div ref={menuRef} className={`relative ${className}`}>
      {/* Trigger Button - Shows flag + language code */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-1 px-1.5 py-0.5 rounded-md
          text-white/60 hover:text-white/90 hover:bg-white/10
          transition-all duration-200 ${isOpen ? 'bg-white/10 text-white/90' : ''}`}
        title={currentLangInfo.nativeName}
        aria-label={`Current language: ${currentLangInfo.nativeName}. Click to change.`}
      >
        <span className="text-[11px]">{currentDisplay.flag}</span>
        <span className="text-[10px] font-semibold tracking-wide">{currentDisplay.short}</span>
        <ChevronDown
          size={10}
          className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown Menu - z-[100] to ensure it's above banner */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-1 z-[100] min-w-[130px]
          glass border border-white/10 rounded-lg shadow-xl shadow-black/40
          py-1 animate-fade-in overflow-hidden">
          {SUPPORTED_LANGUAGES.map((lang) => {
            const isActive = lang.code === normalizedLang
            const display = LANGUAGE_DISPLAY[lang.code] || { flag: '🌐', short: lang.code.toUpperCase() }
            return (
              <button
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code)}
                className={`w-full flex items-center gap-2 px-3 py-1.5
                  text-[11px] transition-colors
                  ${isActive
                    ? 'bg-blue-500/20 text-blue-300'
                    : 'text-white/70 hover:bg-white/10 hover:text-white/90'
                  }`}
              >
                <span className="text-[12px]">{display.flag}</span>
                <span className="flex-1 text-left">{lang.nativeName}</span>
                {isActive && <Check size={11} className="text-blue-400" />}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
