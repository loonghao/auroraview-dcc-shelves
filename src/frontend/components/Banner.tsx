import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Settings } from 'lucide-react'
import type { BannerConfig } from '../types'
import { useIndexedDB, DEFAULT_BANNER_SETTINGS } from '../hooks/useIndexedDB'
import type { BannerSettings } from '../hooks/useIndexedDB'
import { BannerSettingsDialog } from './BannerSettingsDialog'
import { ZoomControls } from './ZoomControls'

interface BannerProps {
  banner: BannerConfig
}

export const Banner: React.FC<BannerProps> = ({ banner }) => {
  const { t, i18n } = useTranslation()
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const [imageKey, setImageKey] = useState(0) // Force image refresh

  const { value: bannerSettings, save: saveBannerSettings, isLoading } =
    useIndexedDB<BannerSettings>('banner-settings', DEFAULT_BANNER_SETTINGS)

  // Use user settings first, then config image, then default
  const backgroundUrl = bannerSettings.imageUrl || banner.image || DEFAULT_BANNER_SETTINGS.imageUrl

  // Get localized title and subtitle
  const isZh = i18n.language === 'zh'
  const title = (isZh && banner.title_zh) || banner.title || t('banner.defaultTitle')
  const subtitle = (isZh && banner.subtitle_zh) || banner.subtitle || t('banner.defaultSubtitle')

  // Reset image states when settings change
  useEffect(() => {
    setImageLoaded(false)
    setImageError(false)
  }, [bannerSettings])

  const handleSaveSettings = (settings: BannerSettings) => {
    saveBannerSettings(settings)
    setImageKey(prev => prev + 1) // Force image element to remount
    setImageLoaded(false)
    setImageError(false)
  }

  return (
    <div
      className="shrink-0 h-20 w-full relative overflow-hidden group"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Image background with custom positioning */}
      {!imageError && !isLoading && (
        <img
          key={imageKey}
          src={backgroundUrl}
          alt=""
          className={`absolute inset-0 w-full h-full transition-opacity duration-500 ${
            imageLoaded ? 'opacity-100' : 'opacity-0'
          }`}
          style={{
            objectFit: bannerSettings.objectFit,
            objectPosition: bannerSettings.objectPosition,
            transform: `scale(${bannerSettings.scale})`,
            filter: `brightness(${bannerSettings.brightness}%)`,
            transformOrigin: 'center',
          }}
          onLoad={() => setImageLoaded(true)}
          onError={() => setImageError(true)}
        />
      )}

      {/* Fallback gradient when image fails or loading */}
      <div
        className={`absolute inset-0 transition-opacity duration-500 ${
          imageLoaded && !imageError ? 'opacity-0 pointer-events-none' : 'opacity-100'
        }`}
        style={{
          background: `
            radial-gradient(ellipse 80% 50% at 20% 40%, ${banner.gradientFrom || 'rgba(59, 130, 246, 0.5)'} 0%, transparent 50%),
            radial-gradient(ellipse 60% 40% at 80% 60%, ${banner.gradientTo || 'rgba(147, 51, 234, 0.5)'} 0%, transparent 50%),
            linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)
          `,
        }}
      />

      {/* Title and Subtitle overlay */}
      <div className="absolute inset-0 flex flex-col justify-center items-center text-center px-4 z-10">
        <h1 className="text-lg font-bold text-white/95 tracking-wide drop-shadow-lg">
          {title}
        </h1>
        <p className="text-xs text-white/70 mt-0.5 drop-shadow-md">
          {subtitle}
        </p>
      </div>

      {/* Bottom fade to content */}
      <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-t from-[#0d0d0d] to-transparent z-20" />

      {/* Controls overlay - appears on hover */}
      <div
        className={`absolute top-2 right-2 flex items-center gap-2 transition-all duration-200 z-30 ${
          isHovered ? 'opacity-100' : 'opacity-0'
        }`}
      >
        {/* Zoom controls */}
        <div className="px-2 py-1 rounded-lg bg-black/40 border border-white/10">
          <ZoomControls compact />
        </div>

        {/* Settings button */}
        <button
          onClick={() => setShowSettings(true)}
          className="p-1.5 rounded-lg bg-black/40 hover:bg-black/60 border border-white/10 transition-colors"
          title={t('banner.settings')}
        >
          <Settings className="w-4 h-4 text-white/70" />
        </button>
      </div>

      {/* Settings Dialog */}
      <BannerSettingsDialog
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        settings={bannerSettings}
        onSave={handleSaveSettings}
      />
    </div>
  )
}
