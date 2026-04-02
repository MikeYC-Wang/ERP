<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useThemeStore } from '@/stores/theme'
import apiClient from '@/api/client'

const themeStore = useThemeStore()

// ─── Appearance ───
const selectedLanguage = ref('zh')

// ─── System Info ───
const apiConnected = ref<boolean | null>(null)

onMounted(async () => {
  try {
    await apiClient.get('')
    apiConnected.value = true
  } catch {
    apiConnected.value = false
  }
})

// ─── Data Management ───
function handleExport() {
  alert('Coming soon')
}

function handleClearCache() {
  localStorage.clear()
  window.location.reload()
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center gap-2">
      <i class="fa-solid fa-gear text-amber-500"></i>
      <h1 class="text-xl font-bold text-slate-900 dark:text-stone-50">Settings</h1>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Card 1: Appearance -->
      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5">
        <div class="flex items-center gap-2 mb-5">
          <i class="fa-solid fa-palette text-amber-500"></i>
          <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">Appearance</h2>
        </div>

        <div class="space-y-5">
          <!-- Dark Mode Toggle -->
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-slate-700 dark:text-stone-200">Dark Mode</p>
              <p class="text-xs text-slate-400 dark:text-slate-500">Toggle between light and dark theme</p>
            </div>
            <button
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
              :class="themeStore.isDark ? 'bg-amber-500' : 'bg-slate-300'"
              @click="themeStore.toggleTheme()"
            >
              <span
                class="inline-block h-4 w-4 rounded-full bg-white transition-transform shadow-sm"
                :class="themeStore.isDark ? 'translate-x-6' : 'translate-x-1'"
              ></span>
            </button>
          </div>

          <!-- Language -->
          <div>
            <p class="text-sm font-medium text-slate-700 dark:text-stone-200 mb-2">Language</p>
            <div class="flex gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="selectedLanguage"
                  type="radio"
                  value="zh"
                  class="w-4 h-4 text-amber-500 border-slate-300 dark:border-slate-600 focus:ring-amber-500"
                />
                <span class="text-sm text-slate-700 dark:text-stone-200">Chinese</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="selectedLanguage"
                  type="radio"
                  value="en"
                  class="w-4 h-4 text-amber-500 border-slate-300 dark:border-slate-600 focus:ring-amber-500"
                />
                <span class="text-sm text-slate-700 dark:text-stone-200">English</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Card 2: System Info -->
      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5">
        <div class="flex items-center gap-2 mb-5">
          <i class="fa-solid fa-circle-info text-amber-500"></i>
          <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">System Information</h2>
        </div>

        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-500 dark:text-slate-400">System Version</span>
            <span class="text-sm font-medium text-slate-700 dark:text-stone-200">PerPetsStore ERP v1.0</span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-500 dark:text-slate-400">API Connection</span>
            <div class="flex items-center gap-2">
              <span
                v-if="apiConnected === null"
                class="text-sm text-slate-400 dark:text-slate-500"
              >
                <i class="fa-solid fa-spinner fa-spin text-xs mr-1"></i> Checking...
              </span>
              <template v-else-if="apiConnected">
                <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <span class="text-sm font-medium text-emerald-600 dark:text-emerald-400">Connected</span>
              </template>
              <template v-else>
                <span class="inline-block w-2.5 h-2.5 rounded-full bg-red-500"></span>
                <span class="text-sm font-medium text-red-600 dark:text-red-400">Disconnected</span>
              </template>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-500 dark:text-slate-400">Frontend Stack</span>
            <span class="text-sm font-medium text-slate-700 dark:text-stone-200">Vue 3 + Vite + TypeScript</span>
          </div>
        </div>
      </div>

      <!-- Card 3: Data Management -->
      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5 lg:col-span-2">
        <div class="flex items-center gap-2 mb-5">
          <i class="fa-solid fa-database text-amber-500"></i>
          <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">Data Management</h2>
        </div>

        <div class="flex gap-3">
          <button
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-500 hover:bg-amber-600 rounded-lg shadow-sm transition-colors"
            @click="handleExport"
          >
            <i class="fa-solid fa-file-export text-xs"></i>
            Export Data
          </button>
          <button
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            @click="handleClearCache"
          >
            <i class="fa-solid fa-trash-can text-xs"></i>
            Clear Cache
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
