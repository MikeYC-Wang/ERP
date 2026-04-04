<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useThemeStore } from '@/stores/theme'
import apiClient from '@/api/client'

const themeStore = useThemeStore()

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
  alert('即將推出')
}

function handleClearCache() {
  localStorage.clear()
  window.location.reload()
}
</script>

<template>
  <div class="space-y-6 animate-fade-in-up">
    <!-- Page Header -->
    <div class="flex items-center gap-2">
      <i class="fa-solid fa-gear text-amber-500"></i>
      <h1 class="text-xl font-bold text-slate-900 dark:text-stone-50">系統設定</h1>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Card 1: Appearance -->
      <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-purple-400">
        <div class="flex items-center gap-2 mb-5">
          <i class="fa-solid fa-palette text-amber-500"></i>
          <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">外觀設定</h2>
        </div>

        <div class="space-y-5">
          <!-- Dark Mode Toggle -->
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-slate-700 dark:text-stone-200">
                {{ themeStore.isDark ? '深色模式' : '淺色模式' }}
              </p>
              <p class="text-xs text-slate-400 dark:text-slate-500">切換淺色與深色佈景主題</p>
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
        </div>
      </div>

      <!-- Card 2: System Info -->
      <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-blue-400">
        <div class="flex items-center gap-2 mb-5">
          <i class="fa-solid fa-circle-info text-amber-500"></i>
          <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">系統資訊</h2>
        </div>

        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-500 dark:text-slate-400">版本</span>
            <span class="text-sm font-medium text-slate-700 dark:text-stone-200">PerPetsStore ERP v1.0</span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-500 dark:text-slate-400">API 連線狀態</span>
            <div class="flex items-center gap-2">
              <span
                v-if="apiConnected === null"
                class="text-sm text-slate-400 dark:text-slate-500"
              >
                <i class="fa-solid fa-spinner fa-spin text-xs mr-1"></i> 檢測中
              </span>
              <template v-else-if="apiConnected">
                <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <span class="text-sm font-medium text-emerald-600 dark:text-emerald-400">已連線</span>
              </template>
              <template v-else>
                <span class="inline-block w-2.5 h-2.5 rounded-full bg-red-500"></span>
                <span class="text-sm font-medium text-red-600 dark:text-red-400">未連線</span>
              </template>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-500 dark:text-slate-400">前端技術</span>
            <span class="text-sm font-medium text-slate-700 dark:text-stone-200">Vue 3 + Vite + TypeScript</span>
          </div>
        </div>
      </div>

      <!-- Card 3: Data Management -->
      <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5 lg:col-span-2 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-amber-400">
        <div class="flex items-center gap-2 mb-5">
          <i class="fa-solid fa-database text-amber-500"></i>
          <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">資料管理</h2>
        </div>

        <div class="flex gap-3">
          <button
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C] rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all duration-300"
            @click="handleExport"
          >
            <i class="fa-solid fa-file-export text-xs"></i>
            匯出資料
          </button>
          <button
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-red-400 to-rose-500 hover:from-red-500 hover:to-rose-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all duration-300"
            @click="handleClearCache"
          >
            <i class="fa-solid fa-trash-can text-xs"></i>
            清除快取
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
