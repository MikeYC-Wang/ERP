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
          meta: { title: '儀表板', icon: 'fa-solid fa-gauge-high' },
        },
        {
          path: 'accounting',
          name: 'Accounting',
          component: () => import('../views/AccountingView.vue'),
          meta: { title: '會計', icon: 'fa-solid fa-file-invoice-dollar' },
        },
        {
          path: 'inventory',
          name: 'Inventory',
          component: () => import('../views/InventoryView.vue'),
          meta: { title: '進銷存', icon: 'fa-solid fa-boxes-stacked' },
        },
        {
          path: 'orders',
          name: 'Orders',
          component: () => import('../views/OrdersView.vue'),
          meta: { title: '訂單', icon: 'fa-solid fa-cart-shopping' },
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('../views/SettingsView.vue'),
          meta: { title: '設定', icon: 'fa-solid fa-gear' },
        },
      ],
    },
  ],
})

export default router
