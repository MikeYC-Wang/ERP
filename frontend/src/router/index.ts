import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true },
    },
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
          path: 'contacts',
          name: 'Contacts',
          component: () => import('../views/ContactsView.vue'),
          meta: { title: '聯絡人', icon: 'fa-solid fa-address-book' },
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

// Navigation guard
router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  if (!to.meta.public && !token) {
    return { name: 'Login' }
  }
  if (to.name === 'Login' && token) {
    return { name: 'Dashboard' }
  }
})

export default router
