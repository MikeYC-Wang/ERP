<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore } from '../../stores/theme'

const route = useRoute()
const themeStore = useThemeStore()

const rotated = ref(false)

defineEmits<{
  (e: 'toggle-sidebar'): void
}>()

const pageTitle = computed(() => (route.meta.title as string) || '儀表板')

function handleToggleTheme() {
  rotated.value = !rotated.value
  themeStore.toggleTheme()
}
</script>

<template>
  <header
    class="h-16 flex items-center justify-between px-4 sm:px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700"
    style="box-shadow: 0 1px 0 0 rgba(245,158,11,0.15)"
  >
    <!-- Left: hamburger + breadcrumb -->
    <div class="flex items-center gap-3">
      <!-- Mobile hamburger -->
      <button
        @click="$emit('toggle-sidebar')"
        class="lg:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-400 transition-colors"
        aria-label="Toggle sidebar"
      >
        <i class="fa-solid fa-bars text-lg"></i>
      </button>

      <!-- Breadcrumb -->
      <nav class="flex items-center gap-2 text-sm">
        <span class="text-slate-400 dark:text-slate-500">
          <i class="fa-solid fa-house text-xs"></i>
          <span class="ml-1">首頁</span>
        </span>
        <span class="text-slate-300 dark:text-slate-600">/</span>
        <span class="font-medium text-slate-700 dark:text-stone-200">{{ pageTitle }}</span>
      </nav>
    </div>

    <!-- Right: theme toggle + user -->
    <div class="flex items-center gap-3">
      <!-- Theme toggle -->
      <button
        @click="handleToggleTheme"
        class="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-400 transition-colors"
        :aria-label="themeStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
      >
        <i
          class="text-lg theme-icon-rotate"
          :class="[themeStore.isDark ? 'fa-solid fa-sun text-amber-400' : 'fa-solid fa-moon text-slate-500', { rotated }]"
        ></i>
      </button>

      <!-- User -->
      <div class="flex items-center gap-2 pl-3 border-l border-slate-200 dark:border-slate-700">
        <div
          class="w-8 h-8 rounded-full bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center"
        >
          <i class="fa-solid fa-user text-amber-600 dark:text-amber-400 text-sm"></i>
        </div>
        <span class="text-sm font-medium text-slate-700 dark:text-stone-200 hidden sm:inline">
          Mike
        </span>
      </div>
    </div>
  </header>
</template>
