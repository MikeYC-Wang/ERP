<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

defineEmits<{
  (e: 'close'): void
}>()

const menuItems = [
  { name: '儀表板', path: '/dashboard', icon: 'fa-solid fa-gauge-high' },
  { name: '會計',   path: '/accounting', icon: 'fa-solid fa-file-invoice-dollar' },
  { name: '進銷存', path: '/inventory',  icon: 'fa-solid fa-boxes-stacked' },
  { name: '訂單',   path: '/orders',     icon: 'fa-solid fa-cart-shopping' },
  { name: '聯絡人', path: '/contacts',   icon: 'fa-solid fa-address-book' },
  { name: '設定',   path: '/settings',   icon: 'fa-solid fa-gear' },
]

const currentPath = computed(() => route.path)

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <aside class="relative flex flex-col h-full w-64 glass border-r overflow-hidden"
         style="border-color: var(--border-soft)">

    <!-- Animated gradient strip on left edge -->
    <div class="absolute left-0 top-0 bottom-0 w-[3px] sidebar-strip"></div>

    <!-- Decorative glow blob inside sidebar -->
    <div class="absolute -top-16 -left-16 w-48 h-48 rounded-full pointer-events-none"
         style="background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%); filter: blur(24px)">
    </div>

    <!-- Logo -->
    <div class="px-5 py-6 border-b" style="border-color: var(--border-soft)">
      <div class="flex items-center gap-3 group cursor-pointer">
        <!-- Icon with animated glow -->
        <div class="relative w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 group-hover:scale-110"
             style="background: var(--bg-elevated); box-shadow: 0 0 16px var(--accent-glow)">
          <i class="fa-solid fa-paw text-lg" style="color: var(--accent)"></i>
          <!-- Pulse ring -->
          <span class="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                style="box-shadow: 0 0 0 3px var(--accent-glow); animation: none"></span>
        </div>
        <div>
          <h1 class="font-display text-base font-bold leading-tight" style="color: var(--text-primary)">
            PerPetsStore
          </h1>
          <p class="text-[11px] italic" style="color: var(--text-muted)">
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
        class="relative w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-250 group"
        :class="currentPath === item.path ? 'nav-active' : 'nav-inactive'"
      >
        <!-- Active glow backdrop -->
        <span
          v-if="currentPath === item.path"
          class="absolute inset-0 rounded-xl opacity-100"
          style="background: linear-gradient(135deg, var(--accent), var(--accent-cyan)); box-shadow: 0 4px 20px var(--accent-glow), 0 0 40px var(--accent-glow-cyan)"
        ></span>

        <i :class="item.icon" class="relative w-5 text-center text-base z-10"></i>
        <span class="relative z-10">{{ item.name }}</span>

        <!-- Active dot indicator -->
        <span
          v-if="currentPath === item.path"
          class="relative z-10 ml-auto w-1.5 h-1.5 rounded-full"
          style="background: white; box-shadow: 0 0 6px rgba(255,255,255,0.8)"
        ></span>

        <!-- Hover shimmer for inactive -->
        <span
          v-if="currentPath !== item.path"
          class="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"
          style="background: var(--bg-elevated)"
        ></span>
      </button>
    </nav>

    <!-- Footer -->
    <div class="px-5 py-4 border-t" style="border-color: var(--border-soft)">
      <p class="text-xs" style="color: var(--text-muted)">v0.1.0</p>
    </div>
  </aside>
</template>

<style scoped>
.nav-active {
  color: white;
}
.nav-inactive {
  color: var(--text-secondary);
}
.nav-inactive:hover {
  color: var(--text-primary);
}
</style>
