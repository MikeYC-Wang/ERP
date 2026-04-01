<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

defineEmits<{
  (e: 'close'): void
}>()

const menuItems = [
  { name: 'Dashboard', path: '/dashboard', icon: 'fa-solid fa-gauge-high' },
  { name: 'Accounting', path: '/accounting', icon: 'fa-solid fa-file-invoice-dollar' },
  { name: 'Inventory', path: '/inventory', icon: 'fa-solid fa-boxes-stacked' },
  { name: 'Orders', path: '/orders', icon: 'fa-solid fa-cart-shopping' },
  { name: 'Settings', path: '/settings', icon: 'fa-solid fa-gear' },
]

const currentPath = computed(() => route.path)

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <aside
    class="flex flex-col h-full w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700"
  >
    <!-- Logo area -->
    <div class="px-5 py-6 border-b border-slate-200 dark:border-slate-700">
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center"
        >
          <i class="fa-solid fa-paw text-amber-600 dark:text-amber-400 text-lg"></i>
        </div>
        <div>
          <h1 class="text-lg font-bold text-slate-900 dark:text-stone-50 leading-tight">
            PerPetsStore
          </h1>
          <p class="text-xs text-slate-500 dark:text-slate-400 italic">
            Because They Deserve the Best.
          </p>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
      <button
        v-for="item in menuItems"
        :key="item.path"
        @click="navigate(item.path); $emit('close')"
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150"
        :class="
          currentPath === item.path
            ? 'bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-stone-50'
        "
      >
        <i
          :class="item.icon"
          class="w-5 text-center"
          :style="currentPath === item.path ? '' : ''"
        ></i>
        <span>{{ item.name }}</span>
        <span
          v-if="currentPath === item.path"
          class="ml-auto w-1.5 h-1.5 rounded-full bg-amber-500"
        ></span>
      </button>
    </nav>

    <!-- Footer -->
    <div class="px-5 py-4 border-t border-slate-200 dark:border-slate-700">
      <p class="text-xs text-slate-400 dark:text-slate-500">v0.1.0</p>
    </div>
  </aside>
</template>
