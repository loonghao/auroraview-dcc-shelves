<script setup lang="ts">
import type { ContextMenuState, ButtonConfig } from '../types'
import { FileCode, Folder, Info, Copy } from 'lucide-vue-next'

defineProps<{
  state: ContextMenuState
}>()

const emit = defineEmits<{
  close: []
  action: [action: string, button: ButtonConfig]
}>()

function handleAction(action: string) {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="state.visible && state.button"
      class="fixed z-50"
      :style="{ left: `${state.x}px`, top: `${state.y}px` }"
    >
      <!-- Backdrop -->
      <div class="fixed inset-0" @click="emit('close')" />

      <!-- Menu -->
      <div
        class="relative bg-[#2a2a2a] border border-[#444] rounded-lg shadow-xl
               py-1 min-w-[160px] animate-fade-in"
      >
        <div class="px-3 py-2 border-b border-[#444]">
          <div class="text-xs text-white font-medium truncate">{{ state.button.name }}</div>
          <div class="text-[10px] text-gray-500">{{ state.button.toolType }}</div>
        </div>

        <button
          @click="handleAction('open_path')"
          class="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-[#3a3a3a]
                 flex items-center gap-2 transition-colors"
        >
          <Folder :size="14" />
          Open Location
        </button>

        <button
          @click="handleAction('copy_path')"
          class="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-[#3a3a3a]
                 flex items-center gap-2 transition-colors"
        >
          <Copy :size="14" />
          Copy Path
        </button>

        <button
          @click="handleAction('view_source')"
          class="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-[#3a3a3a]
                 flex items-center gap-2 transition-colors"
        >
          <FileCode :size="14" />
          View Source
        </button>

        <div class="border-t border-[#444] my-1" />

        <button
          @click="handleAction('details')"
          class="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-[#3a3a3a]
                 flex items-center gap-2 transition-colors"
        >
          <Info :size="14" />
          Details
        </button>
      </div>
    </div>
  </Teleport>
</template>

