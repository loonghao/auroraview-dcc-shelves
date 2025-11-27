<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Search, X, Settings, LayoutGrid, Box, Filter, Minus } from 'lucide-vue-next'
import type { ButtonConfig, ShelfConfig, ContextMenuState } from './types'
import { useShelfIPC } from './composables/useShelfIPC'
import ShelfGroup from './components/ShelfGroup.vue'
import ContextMenu from './components/ContextMenu.vue'
import InfoFooter from './components/InfoFooter.vue'

const { config, isConnected, launchTool } = useShelfIPC()

// State
const searchQuery = ref('')
const activeShelfId = ref<string | null>(null)
const hoveredButton = ref<ButtonConfig | null>(null)
const contextMenu = ref<ContextMenuState>({
  visible: false,
  x: 0,
  y: 0,
  button: null,
})

// Computed
const shelves = computed<ShelfConfig[]>(() => config.value?.shelves || [])

const tabs = computed(() => [
  { id: null, label: 'All Tools' },
  ...shelves.value.map((s) => ({ id: s.id, label: s.name })),
])

const filteredShelves = computed(() => {
  let result = shelves.value

  // Filter by active shelf
  if (activeShelfId.value) {
    result = result.filter((s) => s.id === activeShelfId.value)
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result
      .map((shelf) => ({
        ...shelf,
        buttons: shelf.buttons.filter(
          (b) =>
            b.name.toLowerCase().includes(query) ||
            b.description.toLowerCase().includes(query)
        ),
      }))
      .filter((s) => s.buttons.length > 0)
  }

  return result
})

const hasResults = computed(() =>
  filteredShelves.value.some((s) => s.buttons.length > 0)
)

// Methods
async function handleLaunch(button: ButtonConfig) {
  console.log(`Launching: ${button.name}`)
  try {
    const result = await launchTool(button.id)
    console.log('Launch result:', result)
  } catch (e) {
    console.error('Launch failed:', e)
  }
}

function handleContextMenu(e: MouseEvent, button: ButtonConfig) {
  contextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    button,
  }
}

function closeContextMenu() {
  contextMenu.value.visible = false
}
</script>

<template>
  <div
    class="flex flex-col h-screen bg-[#121212] text-gray-200 font-sans
           selection:bg-brand-500/30 overflow-hidden"
    @click="closeContextMenu"
  >
    <!-- Title bar -->
    <div
      class="shrink-0 h-10 flex items-center justify-between px-4 bg-[#1a1a1a]
             select-none border-b border-[#2a2a2a]"
    >
      <div class="flex items-center space-x-2 text-white/90">
        <Box :size="16" class="text-brand-500" />
        <span class="font-bold tracking-wider text-sm">DCC SHELVES</span>
      </div>
      <div class="flex items-center space-x-3 text-gray-400">
        <button class="hover:text-white transition-colors"><Settings :size="14" /></button>
        <button class="hover:text-white transition-colors"><Minus :size="14" /></button>
        <button class="hover:text-red-500 transition-colors"><X :size="14" /></button>
      </div>
    </div>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0 px-4 relative max-w-5xl mx-auto w-full overflow-hidden">
      <!-- Header controls -->
      <div class="shrink-0 pt-4 pb-4 space-y-3 z-10 bg-[#121212]">
        <!-- Search bar -->
        <div class="flex items-center space-x-2">
          <div class="relative flex-1 group">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search
                class="h-4 w-4 text-gray-500 group-focus-within:text-brand-500 transition-colors"
              />
            </div>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search tools..."
              class="block w-full pl-9 pr-8 py-2 bg-[#1e1e1e] border border-[#333]
                     rounded text-sm text-gray-200 placeholder-gray-600
                     focus:outline-none focus:border-brand-500/50 focus:ring-1
                     focus:ring-brand-500/50 transition-all"
            />
            <button
              v-if="searchQuery"
              @click="searchQuery = ''"
              class="absolute inset-y-0 right-0 pr-2.5 flex items-center
                     text-gray-500 hover:text-gray-300"
            >
              <X class="h-3 w-3" />
            </button>
          </div>
          <button
            class="p-2 bg-[#1e1e1e] border border-[#333] rounded
                   hover:border-gray-500 text-gray-400 hover:text-white transition-colors"
          >
            <Filter :size="16" />
          </button>
        </div>

        <!-- Tabs -->
        <div class="flex items-center space-x-2 overflow-x-auto scrollbar-hide pt-1 pb-1">
          <button
            v-for="tab in tabs"
            :key="tab.id ?? 'all'"
            @click="activeShelfId = tab.id"
            :class="[
              'px-3 py-1 text-xs font-medium rounded-sm border transition-all duration-200',
              'whitespace-nowrap flex items-center',
              activeShelfId === tab.id
                ? 'bg-brand-600 border-brand-500 text-white shadow-[0_0_10px_rgba(16,185,129,0.3)]'
                : 'bg-transparent border-transparent text-gray-500 hover:text-gray-300 hover:bg-[#1e1e1e]',
            ]"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <!-- Tool grid -->
      <div class="flex-1 overflow-y-auto pb-4 -mr-2 pr-2 custom-scrollbar">
        <!-- Empty state -->
        <div
          v-if="!hasResults"
          class="flex flex-col items-center justify-center h-48 text-gray-600"
        >
          <LayoutGrid :size="32" class="mb-3 opacity-20" />
          <p class="text-sm">No tools found</p>
        </div>

        <!-- Shelf groups -->
        <ShelfGroup
          v-for="shelf in filteredShelves"
          :key="shelf.id"
          :shelf="shelf"
          @launch="handleLaunch"
          @contextmenu="handleContextMenu"
          @mouseenter="(b: ButtonConfig) => (hoveredButton = b)"
          @mouseleave="hoveredButton = null"
        />
      </div>
    </div>

    <!-- Footer -->
    <InfoFooter :button="hoveredButton" />

    <!-- Context menu -->
    <ContextMenu :state="contextMenu" @close="closeContextMenu" />
  </div>
</template>

