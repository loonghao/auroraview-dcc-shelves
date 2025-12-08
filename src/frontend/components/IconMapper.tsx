import React, { useState } from 'react'
import {
  Box,
  Wrench,
  FileCode,
  Terminal,
  Folder,
  FolderOpen,
  Image,
  Film,
  Music,
  Palette,
  Layers,
  Cpu,
  Database,
  Globe,
  Settings,
  Zap,
  Package,
  Grid,
  Pencil,
  HelpCircle,
  LucideIcon,
  Activity,
  Edit3,
  Trees,
  Cable,
  Lightbulb,
  ArrowLeftRight,
  Sun,
  Upload,
  Copy,
  ImagePlus,
  ArrowRightLeft,
  Link2Off,
  Split,
  Star,
  DownloadCloud,
  User,
  BookOpen,
} from 'lucide-react'

interface IconMapperProps {
  name: string
  className?: string
  size?: number
}

/**
 * Check if the string is already a full URL (http/https/auroraview protocol).
 */
const isFullUrl = (name: string): boolean => {
  return /^(https?|auroraview):\/\//i.test(name)
}

/**
 * Check if the icon name is a local file path (relative or absolute).
 * Local paths: icons/tool.png, ./icons/tool.svg, tool.ico, C:/path/to/icon.svg
 * Does NOT match full URLs that are already resolved.
 */
const isLocalPath = (name: string): boolean => {
  // If it's already a full URL, it's not a local path that needs resolution
  if (isFullUrl(name)) return false
  // Has file extension (png, svg, ico, jpg, jpeg, gif, webp)
  if (/\.(png|svg|ico|jpe?g|gif|webp)$/i.test(name)) return true
  // Starts with relative path indicators
  if (name.startsWith('./') || name.startsWith('../') || name.startsWith('icons/')) return true
  // Absolute path (Windows: C:/ or Unix: /)
  if (/^[A-Za-z]:[\\/]/.test(name) || name.startsWith('/')) return true
  return false
}

/**
 * Check if the path is an absolute file path.
 */
const isAbsolutePath = (path: string): boolean => {
  // Windows absolute path: C:/ or C:\
  if (/^[A-Za-z]:[\\/]/.test(path)) return true
  // Unix absolute path: /
  if (path.startsWith('/') && !path.startsWith('//')) return true
  return false
}

/**
 * AuroraView protocol base URL for loading local assets.
 * Uses https://auroraview.localhost/file/ for absolute paths
 * and https://auroraview.localhost/ for relative paths.
 */
const AURORAVIEW_BASE_URL = 'https://auroraview.localhost'

/**
 * Convert a file path to the appropriate URL for loading.
 * - Full URLs: return as-is (already resolved by backend)
 * - Absolute paths: use AuroraView file protocol (https://auroraview.localhost/file/...)
 * - Relative paths in dev: use Vite dev server
 * - Relative paths in prod: use AuroraView protocol
 */
const resolveAssetUrl = (filePath: string): string => {
  // If already a full URL, return as-is (already resolved by backend)
  if (isFullUrl(filePath)) {
    return filePath
  }

  const isDev = import.meta.env.DEV
  // Normalize path separators
  const normalizedPath = filePath.replace(/\\/g, '/')

  // Handle absolute paths - use AuroraView file protocol
  if (isAbsolutePath(normalizedPath)) {
    // Remove leading slash for consistent format
    const cleanPath = normalizedPath.replace(/^\/+/, '')
    return `${AURORAVIEW_BASE_URL}/file/${cleanPath}`
  }

  // Remove leading ./ if present for relative paths
  const cleanPath = normalizedPath.replace(/^\.\//, '')

  if (isDev) {
    // In dev mode, Vite serves from project root
    return `/${cleanPath}`
  }

  // Production: use AuroraView protocol for relative paths
  return `${AURORAVIEW_BASE_URL}/${cleanPath}`
}

const iconMap: Record<string, LucideIcon> = {
  // Case-sensitive (lightbox style)
  Box: Box,
  Wrench: Wrench,
  Palette: Palette,
  Zap: Zap,
  Package: Package,
  Film: Film,
  Layers: Layers,
  Grid: Grid,
  Folder: Folder,
  FolderOpen: FolderOpen,
  Terminal: Terminal,
  Cpu: Cpu,
  Pencil: Pencil,
  Activity: Activity,
  Edit3: Edit3,
  Trees: Trees,
  Cable: Cable,
  Lightbulb: Lightbulb,
  ArrowLeftRight: ArrowLeftRight,
  Sun: Sun,
  Upload: Upload,
  Copy: Copy,
  ImagePlus: ImagePlus,
  ArrowRightLeft: ArrowRightLeft,
  Link2Off: Link2Off,
  Split: Split,
  Star: Star,
  DownloadCloud: DownloadCloud,
  User: User,
  BookOpen: BookOpen,
  // Lowercase fallbacks
  box: Box,
  wrench: Wrench,
  'file-code': FileCode,
  terminal: Terminal,
  folder: Folder,
  image: Image,
  film: Film,
  music: Music,
  palette: Palette,
  layers: Layers,
  cpu: Cpu,
  database: Database,
  globe: Globe,
  settings: Settings,
  zap: Zap,
  package: Package,
  grid: Grid,
  pencil: Pencil,
}

export const IconMapper: React.FC<IconMapperProps> = ({ name, className, size = 24 }) => {
  const [imageError, setImageError] = useState(false)

  // If it's already a full URL (from backend), use it directly
  if (isFullUrl(name) && !imageError) {
    return (
      <img
        src={name}
        alt=""
        width={size}
        height={size}
        className={className}
        style={{ objectFit: 'contain' }}
        onError={() => setImageError(true)}
      />
    )
  }

  // If it's a local path, resolve and render as image
  if (isLocalPath(name) && !imageError) {
    const imageUrl = resolveAssetUrl(name)
    return (
      <img
        src={imageUrl}
        alt=""
        width={size}
        height={size}
        className={className}
        style={{ objectFit: 'contain' }}
        onError={() => setImageError(true)}
      />
    )
  }

  // Fall back to Lucide icon
  const IconComponent = iconMap[name] || HelpCircle
  return <IconComponent className={className} size={size} />
}
