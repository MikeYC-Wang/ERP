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
    class="relative h-16 flex items-center justify-between px-4 sm:px-6 glass border-b"
    style="border-color: var(--border-soft)"
  >
    <!-- Subtle top highlight line -->
    <div class="absolute top-0 left-0 right-0 h-[1px]"
         style="background: linear-gradient(90deg, transparent, var(--accent-glow), var(--accent-glow-cyan), transparent)">
    </div>

    <!-- Left -->
    <div class="flex items-center gap-3">
      <!-- Mobile hamburger -->
      <button
        @click="$emit('toggle-sidebar')"
        class="lg:hidden p-2 rounded-lg transition-all duration-200 hover:ring-glow"
        style="color: var(--text-secondary); background: var(--bg-elevated)"
        aria-label="Toggle sidebar"
      >
        <i class="fa-solid fa-bars text-base"></i>
      </button>

      <!-- Breadcrumb -->
      <nav class="flex items-center gap-2 text-sm">
        <span style="color: var(--text-muted)">
          <i class="fa-solid fa-house text-xs"></i>
          <span class="ml-1">首頁</span>
        </span>
        <span style="color: var(--border-hard)">/</span>
        <span class="font-semibold font-display" style="color: var(--text-primary)">{{ pageTitle }}</span>
      </nav>
    </div>

    <!-- Right -->
    <div class="flex items-center gap-3">

      <!-- Theme toggle -->
      <button
        @click="handleToggleTheme"
        class="relative w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-300 hover:-translate-y-0.5 overflow-hidden"
        style="background: var(--bg-elevated); box-shadow: var(--shadow-sm)"
        :aria-label="themeStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
      >
        <!-- Glow backdrop on hover -->
        <span class="absolute inset-0 rounded-xl opacity-0 hover:opacity-100 transition-opacity"
              style="background: var(--accent-glow)"></span>
        <i
          class="relative z-10 text-base theme-icon-rotate"
          :class="[
            themeStore.isDark ? 'fa-solid fa-sun' : 'fa-solid fa-moon',
            { rotated }
          ]"
          :style="{ color: themeStore.isDark ? 'var(--accent-warm)' : 'var(--accent)' }"
        ></i>
      </button>

      <!-- Divider -->
      <div class="w-px h-6" style="background: var(--border-soft)"></div>

      <!-- User -->
      <div class="flex items-center gap-2 cursor-pointer group">
        <div
          class="relative w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 group-hover:scale-110"
          style="background: var(--bg-elevated); box-shadow: 0 0 12px var(--accent-glow)"
        >
          <i class="fa-solid fa-user text-sm" style="color: var(--accent)"></i>
          <!-- Online indicator -->
          <span class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2"
                style="background: #22C55E; border-color: var(--bg-surface)"></span>
        </div>
        <span class="text-sm font-medium hidden sm:inline" style="color: var(--text-primary)">
          Mike
        </span>
      </div>
    </div>
  </header>
</template>
