<script setup lang="ts">
import { ref, computed } from 'vue'

// ─── Types ───
interface Order {
  id: number
  orderNumber: string
  customerName: string
  date: string
  status: 'pending' | 'shipped' | 'completed'
  totalAmount: number
}

// ─── Data ───
const orders = ref<Order[]>([
  // Pending (4)
  { id: 1, orderNumber: 'ORD-2026-001', customerName: 'PetMart Ltd.', date: '2026-03-28', status: 'pending', totalAmount: 4250.00 },
  { id: 2, orderNumber: 'ORD-2026-002', customerName: 'Happy Paws Shop', date: '2026-03-27', status: 'pending', totalAmount: 1820.00 },
  { id: 3, orderNumber: 'ORD-2026-003', customerName: 'Aqua World', date: '2026-03-26', status: 'pending', totalAmount: 3600.00 },
  { id: 4, orderNumber: 'ORD-2026-004', customerName: 'Feathered Friends', date: '2026-03-25', status: 'pending', totalAmount: 950.00 },
  // Shipped (3)
  { id: 5, orderNumber: 'ORD-2026-005', customerName: 'Pet Paradise', date: '2026-03-22', status: 'shipped', totalAmount: 6780.00 },
  { id: 6, orderNumber: 'ORD-2026-006', customerName: 'Animal Kingdom', date: '2026-03-20', status: 'shipped', totalAmount: 2340.00 },
  { id: 7, orderNumber: 'ORD-2026-007', customerName: 'Bark & Purr Co.', date: '2026-03-18', status: 'shipped', totalAmount: 5100.00 },
  // Completed (5)
  { id: 8, orderNumber: 'ORD-2026-008', customerName: 'PetMart Ltd.', date: '2026-03-10', status: 'completed', totalAmount: 3200.00 },
  { id: 9, orderNumber: 'ORD-2026-009', customerName: 'Happy Paws Shop', date: '2026-03-08', status: 'completed', totalAmount: 1450.00 },
  { id: 10, orderNumber: 'ORD-2026-010', customerName: 'Aqua World', date: '2026-03-05', status: 'completed', totalAmount: 7800.00 },
  { id: 11, orderNumber: 'ORD-2026-011', customerName: 'Pet Paradise', date: '2026-03-01', status: 'completed', totalAmount: 2100.00 },
  { id: 12, orderNumber: 'ORD-2026-012', customerName: 'Animal Kingdom', date: '2026-02-28', status: 'completed', totalAmount: 4500.00 },
])

// ─── Tab State ───
const activeTab = ref<'pending' | 'shipped' | 'completed'>('pending')

const tabs = [
  { key: 'pending' as const, label: 'Pending', icon: 'fa-solid fa-clock' },
  { key: 'shipped' as const, label: 'Shipped', icon: 'fa-solid fa-truck' },
  { key: 'completed' as const, label: 'Completed', icon: 'fa-solid fa-circle-check' },
]

// ─── Computed ───
function countByStatus(status: string) {
  return orders.value.filter((o) => o.status === status).length
}

const filteredOrders = computed(() => {
  return orders.value.filter((o) => o.status === activeTab.value)
})

const filteredOrderCount = computed(() => filteredOrders.value.length)
const filteredTotalAmount = computed(() =>
  filteredOrders.value.reduce((sum, o) => sum + o.totalAmount, 0),
)

// ─── Actions ───
function markAsShipped(id: number) {
  const order = orders.value.find((o) => o.id === id)
  if (order) order.status = 'shipped'
}

function markAsCompleted(id: number) {
  const order = orders.value.find((o) => o.id === id)
  if (order) order.status = 'completed'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center gap-2">
      <i class="fa-solid fa-cart-shopping text-amber-500"></i>
      <h1 class="text-xl font-bold text-slate-900 dark:text-stone-50">Orders</h1>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-slate-500 dark:text-slate-400">Order Count</span>
          <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-amber-50 dark:bg-amber-900/30">
            <i class="fa-solid fa-file-lines text-sm text-amber-500"></i>
          </div>
        </div>
        <p class="text-2xl font-bold text-slate-900 dark:text-stone-50">{{ filteredOrderCount }}</p>
        <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">
          {{ activeTab === 'pending' ? 'Pending' : activeTab === 'shipped' ? 'Shipped' : 'Completed' }} orders
        </p>
      </div>
      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-slate-500 dark:text-slate-400">Total Amount</span>
          <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-emerald-50 dark:bg-emerald-900/30">
            <i class="fa-solid fa-dollar-sign text-sm text-emerald-500"></i>
          </div>
        </div>
        <p class="text-2xl font-bold text-slate-900 dark:text-stone-50">${{ filteredTotalAmount.toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</p>
        <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">
          {{ activeTab === 'pending' ? 'Pending' : activeTab === 'shipped' ? 'Shipped' : 'Completed' }} total
        </p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-slate-200 dark:border-slate-700">
      <nav class="flex gap-4">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors"
          :class="activeTab === tab.key
            ? 'border-amber-500 text-amber-600 dark:text-amber-400'
            : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-stone-200'"
          @click="activeTab = tab.key"
        >
          <i :class="tab.icon" class="text-xs"></i>
          {{ tab.label }}
          <span
            class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-medium"
            :class="activeTab === tab.key
              ? 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300'
              : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'"
          >
            {{ countByStatus(tab.key) }}
          </span>
        </button>
      </nav>
    </div>

    <!-- Orders Table -->
    <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-slate-200 dark:border-slate-700">
              <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Order No.</th>
              <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Customer</th>
              <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Date</th>
              <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Total</th>
              <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(order, index) in filteredOrders"
              :key="order.id"
              class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              :class="index % 2 === 1 ? 'bg-slate-50/50 dark:bg-slate-800/30' : ''"
            >
              <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ order.orderNumber }}</td>
              <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ order.customerName }}</td>
              <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ order.date }}</td>
              <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ order.totalAmount.toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</td>
              <td class="px-5 py-3 text-right">
                <button
                  v-if="activeTab === 'pending'"
                  class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-blue-500 hover:bg-blue-600 rounded-lg shadow-sm transition-colors"
                  @click="markAsShipped(order.id)"
                >
                  <i class="fa-solid fa-truck text-[10px]"></i> Mark Shipped
                </button>
                <button
                  v-else-if="activeTab === 'shipped'"
                  class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-emerald-500 hover:bg-emerald-600 rounded-lg shadow-sm transition-colors"
                  @click="markAsCompleted(order.id)"
                >
                  <i class="fa-solid fa-circle-check text-[10px]"></i> Complete
                </button>
                <span
                  v-else
                  class="text-xs text-slate-400 dark:text-slate-500"
                >
                  -
                </span>
              </td>
            </tr>
            <tr v-if="filteredOrders.length === 0">
              <td colspan="5" class="px-5 py-8 text-center text-slate-400 dark:text-slate-500">
                No orders found.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
