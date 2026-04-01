import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('../views/DashboardView.vue'),
          meta: { title: 'Dashboard', icon: 'fa-solid fa-gauge-high' },
        },
        {
          path: 'accounting',
          name: 'Accounting',
          component: () => import('../views/AccountingView.vue'),
          meta: { title: 'Accounting', icon: 'fa-solid fa-file-invoice-dollar' },
        },
        {
          path: 'inventory',
          name: 'Inventory',
          component: () => import('../views/InventoryView.vue'),
          meta: { title: 'Inventory', icon: 'fa-solid fa-boxes-stacked' },
        },
        {
          path: 'orders',
          name: 'Orders',
          component: () => import('../views/OrdersView.vue'),
          meta: { title: 'Orders', icon: 'fa-solid fa-cart-shopping' },
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('../views/SettingsView.vue'),
          meta: { title: 'Settings', icon: 'fa-solid fa-gear' },
        },
      ],
    },
  ],
})

export default router
