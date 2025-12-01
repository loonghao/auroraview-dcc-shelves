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
 * Check if the icon name is a local file path (relative or with extension).
 * Local paths: icons/tool.png, ./icons/tool.svg, tool.ico
 */
const isLocalPath = (name: string): boolean => {
  // Has file extension (png, svg, ico, jpg, jpeg, gif, webp)
  if (/\.(png|svg|ico|jpe?g|gif|webp)$/i.test(name)) return true
  // Starts with relative path indicators
  if (name.startsWith('./') || name.startsWith('../') || name.startsWith('icons/')) return true
  return false
}

/**
 * Convert a relative asset path to the AuroraView protocol URL.
 * In production: https://auroraview.localhost/assets/{path}
 * In dev mode: direct relative path (Vite serves from public or root)
 */
const resolveAssetUrl = (relativePath: string): string => {
  const isDev = import.meta.env.DEV
  // Normalize path separators
  const normalizedPath = relativePath.replace(/\\/g, '/')
  // Remove leading ./ if present
  const cleanPath = normalizedPath.replace(/^\.\//, '')

  if (isDev) {
    // In dev mode, Vite serves from project root
    // Assets in examples/ directory need to be served
    return `/${cleanPath}`
  }

  // Production: use AuroraView protocol
  // The asset_root is set to the config directory in Python
  return `https://auroraview.localhost/${cleanPath}`
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

  // If it's a local path, render as image
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
