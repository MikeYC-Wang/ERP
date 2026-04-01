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
  <div class="flex h-screen overflow-hidden bg-stone-50 dark:bg-slate-800">
    <!-- Desktop sidebar -->
    <div class="hidden lg:flex lg:flex-shrink-0">
      <SidebarMenu />
    </div>

    <!-- Mobile sidebar overlay -->
    <Teleport to="body">
      <Transition name="overlay">
        <div
          v-if="sidebarOpen"
          class="fixed inset-0 z-40 bg-black/30 lg:hidden"
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
    <div class="flex flex-1 flex-col min-w-0">
      <AppHeader @toggle-sidebar="toggleSidebar" />

      <main class="flex-1 overflow-y-auto p-4 sm:p-6">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Drawer transition */
.drawer-enter-active,
.drawer-leave-active {
  transition: transform 0.25s ease;
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
</style>
