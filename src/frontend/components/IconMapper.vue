<script setup lang="ts">
import {
  Box,
  Wrench,
  FileCode,
  Terminal,
  Folder,
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
  Grid3x3,
  Pencil,
} from 'lucide-vue-next'

defineProps<{
  name: string
  size?: number
}>()

const iconMap: Record<string, typeof Box> = {
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
  grid: Grid3x3,
  pencil: Pencil,
}

function getIcon(name: string) {
  const key = name.toLowerCase().replace(/[_\s]/g, '-')
  return iconMap[key] || Box
}
</script>

<template>
  <component :is="getIcon(name)" :size="size || 24" />
</template>

