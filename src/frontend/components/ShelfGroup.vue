<script setup lang="ts">
import type { ShelfConfig, ButtonConfig } from '../types'
import ToolButton from './ToolButton.vue'

defineProps<{
  shelf: ShelfConfig
}>()

const emit = defineEmits<{
  launch: [button: ButtonConfig]
  contextmenu: [event: MouseEvent, button: ButtonConfig]
}>()

function handleLaunch(button: ButtonConfig) {
  emit('launch', button)
}

function handleContextMenu(e: MouseEvent, button: ButtonConfig) {
  emit('contextmenu', e, button)
}
</script>

<template>
  <div class="mb-6 animate-fade-in">
    <!-- Shelf title -->
    <h2 class="text-xs font-bold text-gray-400 mb-3 pl-1 uppercase tracking-wider opacity-80">
      {{ shelf.name }}
    </h2>

    <!-- Button grid -->
    <div class="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 gap-3">
      <ToolButton
        v-for="button in shelf.buttons"
        :key="button.id"
        :button="button"
        @launch="handleLaunch"
        @contextmenu="handleContextMenu"
      />
    </div>
  </div>
</template>

