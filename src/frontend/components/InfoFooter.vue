<script setup lang="ts">
import type { ButtonConfig } from '../types'

defineProps<{
  button: ButtonConfig | null
}>()
</script>

<template>
  <div
    class="shrink-0 h-8 bg-[#1a1a1a] border-t border-[#2a2a2a]
           flex items-center px-4 text-xs text-gray-500"
  >
    <template v-if="button">
      <span class="text-gray-400 font-medium">{{ button.name }}</span>
      <span class="mx-2">•</span>
      <span class="truncate max-w-md">{{ button.description || button.toolPath }}</span>
    </template>
    <template v-else>
      <span>Hover over a tool to see details</span>
    </template>
  </div>
</template>

