<script setup lang="ts">
import { ref } from 'vue'
import SidebarMenu from '../components/sidebar/SidebarMenu.vue'
import AppHeader from '../components/header/AppHeader.vue'

const sidebarOpen = ref(false)

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar() {
  sidebarOpen.value = false
}
</script>

<template>
  <div class="flex h-screen overflow-hidden relative" style="background: var(--bg-base)">

    <!-- Aurora background -->
    <div class="aurora-bg" aria-hidden="true">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <div class="particles"></div>
    </div>

    <!-- Desktop sidebar -->
    <div class="hidden lg:flex lg:flex-shrink-0 relative z-10">
      <SidebarMenu />
    </div>

    <!-- Mobile overlay -->
    <Teleport to="body">
      <Transition name="overlay">
        <div
          v-if="sidebarOpen"
          class="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          @click="closeSidebar"
        ></div>
      </Transition>
    </Teleport>

    <!-- Mobile sidebar drawer -->
    <Transition name="drawer">
      <div
        v-if="sidebarOpen"
        class="fixed inset-y-0 left-0 z-50 lg:hidden"
      >
        <SidebarMenu @close="closeSidebar" />
      </div>
    </Transition>

    <!-- Main content area -->
    <div class="flex flex-1 flex-col min-w-0 relative z-10">
      <AppHeader @toggle-sidebar="toggleSidebar" />

      <main class="flex-1 overflow-y-auto p-4 sm:p-6">
        <RouterView v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Drawer transition */
.drawer-enter-active,
.drawer-leave-active {
  transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}
.drawer-enter-from,
.drawer-leave-to {
  transform: translateX(-100%);
}

/* Overlay transition */
.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.25s ease;
}
.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}

/* Page transition */
.page-enter-active {
  transition: all 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}
.page-leave-active {
  transition: all 0.2s ease-in;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(16px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
