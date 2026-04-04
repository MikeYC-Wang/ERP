<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getOrders, shipOrder, completeOrder } from '@/api/orders'

// ─── Loading ───
const loading = ref(false)

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
const orders = ref<Order[]>([])

// ─── Tab State ───
const activeTab = ref<'pending' | 'shipped' | 'completed'>('pending')

const tabs = [
  { key: 'pending' as const, label: '待出貨', icon: 'fa-solid fa-clock' },
  { key: 'shipped' as const, label: '已出貨', icon: 'fa-solid fa-truck' },
  { key: 'completed' as const, label: '已完成', icon: 'fa-solid fa-circle-check' },
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
async function markAsShipped(id: number) {
  try {
    await shipOrder(id)
  } catch (e) {
    console.warn('Failed to ship order via API, applying locally', e)
  }
  const order = orders.value.find((o) => o.id === id)
  if (order) order.status = 'shipped'
}

async function markAsCompleted(id: number) {
  try {
    await completeOrder(id)
  } catch (e) {
    console.warn('Failed to complete order via API, applying locally', e)
  }
  const order = orders.value.find((o) => o.id === id)
  if (order) order.status = 'completed'
}

// ─── Load from API ───
async function loadOrders() {
  loading.value = true
  try {
    const res = await getOrders({ status: activeTab.value })
    const rawList = Array.isArray(res?.data) ? res.data : res?.data?.results ?? []
    if (rawList.length) {
      // Replace only orders matching the current tab from API
      const apiOrders: Order[] = rawList.map((o: Record<string, unknown>) => ({
        id: o.id as number,
        orderNumber: (o.order_number as string) || '',
        customerName: (o.customer_name as string) || '',
        date: (o.date as string) || '',
        status: (o.status as Order['status']) || activeTab.value,
        totalAmount: Number(o.total_amount) || 0,
      }))
      // Remove old orders of this status, add API ones
      orders.value = [
        ...orders.value.filter((o) => o.status !== activeTab.value),
        ...apiOrders,
      ]
    }
  } catch (e) {
    console.warn('Orders API unavailable, using fallback data', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadOrders()
})

watch(activeTab, () => {
  loadOrders()
})
</script>

<template>
  <div class="space-y-6 animate-fade-in-up">
    <!-- Page Header -->
    <div class="flex items-center gap-2">
      <i class="fa-solid fa-cart-shopping text-amber-500"></i>
      <h1 class="text-xl font-bold text-slate-900 dark:text-stone-50">訂單管理</h1>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-blue-400">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-slate-500 dark:text-slate-400">案件總數</span>
          <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-blue-50 dark:bg-blue-900/30">
            <i class="fa-solid fa-file-lines text-sm text-blue-500"></i>
          </div>
        </div>
        <p class="text-2xl font-bold font-mono text-slate-900 dark:text-stone-50">{{ filteredOrderCount }}</p>
        <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">
          {{ activeTab === 'pending' ? '待出貨' : activeTab === 'shipped' ? '已出貨' : '已完成' }}訂單
        </p>
      </div>
      <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-amber-400">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-slate-500 dark:text-slate-400">總金額</span>
          <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-amber-50 dark:bg-amber-900/30">
            <i class="fa-solid fa-dollar-sign text-sm text-amber-500"></i>
          </div>
        </div>
        <p class="text-2xl font-bold font-mono text-slate-900 dark:text-stone-50">${{ filteredTotalAmount.toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</p>
        <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">
          {{ activeTab === 'pending' ? '待出貨' : activeTab === 'shipped' ? '已出貨' : '已完成' }}合計
        </p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-slate-200 dark:border-slate-700">
      <nav class="flex gap-2">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-all duration-300"
          :class="activeTab === tab.key
            ? 'bg-gradient-to-r from-amber-400 to-amber-600 dark:from-[#C9A47A] dark:to-[#A07848] text-white shadow-md'
            : 'text-slate-600 dark:text-slate-400 hover:text-amber-600'"
          @click="activeTab = tab.key"
        >
          <i :class="tab.icon" class="text-xs"></i>
          {{ tab.label }}
          <span
            class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-medium"
            :class="activeTab === tab.key
              ? 'bg-white/20 text-white'
              : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'"
          >
            {{ countByStatus(tab.key) }}
          </span>
        </button>
      </nav>
    </div>

    <!-- Loading Spinner -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <i class="fa-solid fa-spinner fa-spin text-2xl text-amber-500"></i>
    </div>

    <!-- Orders Table -->
    <Transition name="fade" mode="out-in">
      <div v-if="!loading" :key="activeTab" class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-violet-400">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-800 dark:to-slate-800">
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">訂單編號</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">客戶名稱</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">日期</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">金額</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(order, index) in filteredOrders"
                :key="order.id"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                :class="index % 2 === 1 ? 'bg-orange-50/30 dark:bg-gray-800/50' : ''"
              >
                <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ order.orderNumber }}</td>
                <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ order.customerName }}</td>
                <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ order.date }}</td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ Number(order.totalAmount ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</td>
                <td class="px-5 py-3 text-right">
                  <button
                    v-if="activeTab === 'pending'"
                    class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-emerald-400 to-teal-500 hover:from-emerald-500 hover:to-teal-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all"
                    @click="markAsShipped(order.id)"
                  >
                    <i class="fa-solid fa-truck text-[10px]"></i> 標記出貨
                  </button>
                  <button
                    v-else-if="activeTab === 'shipped'"
                    class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-emerald-400 to-teal-500 hover:from-emerald-500 hover:to-teal-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all"
                    @click="markAsCompleted(order.id)"
                  >
                    <i class="fa-solid fa-circle-check text-[10px]"></i> 完成訂單
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
                  查無訂單資料。
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
