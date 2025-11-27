<script setup lang="ts">
import type { ButtonConfig } from '../types'
import IconMapper from './IconMapper.vue'

const props = defineProps<{
  button: ButtonConfig
}>()

const emit = defineEmits<{
  launch: [button: ButtonConfig]
  contextmenu: [event: MouseEvent, button: ButtonConfig]
}>()

function handleClick() {
  emit('launch', props.button)
}

function handleContextMenu(e: MouseEvent) {
  e.preventDefault()
  emit('contextmenu', e, props.button)
}
</script>

<template>
  <div
    @click="handleClick"
    @contextmenu="handleContextMenu"
    class="group relative flex flex-col items-center p-3 rounded-xl
           transition-all duration-150 cursor-pointer
           bg-[#1e1e1e] hover:bg-[#2a2a2a] hover:ring-1 hover:ring-brand-500/30
           hover:shadow-lg hover:-translate-y-0.5"
  >
    <!-- Icon -->
    <div class="mb-2 transition-transform duration-200 group-hover:scale-110
                text-gray-400 group-hover:text-gray-100">
      <IconMapper :name="button.icon || 'box'" :size="36" />
    </div>

    <!-- Name -->
    <span class="text-[11px] font-medium text-center truncate leading-tight max-w-full
                 text-gray-400 group-hover:text-brand-400 transition-colors">
      {{ button.name }}
    </span>

    <!-- Type indicator -->
    <div
      v-if="button.toolType === 'python'"
      class="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 opacity-60"
      title="Python Script"
    />
    <div
      v-else
      class="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-green-500 opacity-60"
      title="Executable"
    />
  </div>
</template>

