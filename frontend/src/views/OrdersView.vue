<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getOrders, createOrder, shipOrder, completeOrder } from '@/api/orders'
import { getCustomers } from '@/api/customers'
import { getProducts } from '@/api/inventory'

// ─── Loading ───
const loading = ref(false)

// ─── Types ───
interface Order {
  id: number
  orderNumber: string
  customerName: string
  customerId: number | null
  date: string
  status: 'pending' | 'shipped' | 'completed'
  totalAmount: number
}

interface Customer { id: number; name: string }
interface Product { id: number; name: string; sku: string; price: number; unit: string }

// ─── Data ───
const orders = ref<Order[]>([])
const customers = ref<Customer[]>([])
const products = ref<Product[]>([])

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

const filteredOrders = computed(() => orders.value.filter((o) => o.status === activeTab.value))
const filteredOrderCount = computed(() => filteredOrders.value.length)
const filteredTotalAmount = computed(() =>
  filteredOrders.value.reduce((sum, o) => sum + o.totalAmount, 0),
)

// ─── New Order Modal ───
const showOrderModal = ref(false)
const orderForm = ref({
  order_number: '',
  customer_name: '',
  customer_ref: null as number | null,
  order_date: new Date().toISOString().slice(0, 10),
  status: 'pending',
  total_amount: 0,
  items: [{ product: 0, quantity: 1, selling_price: 0 }] as { product: number; quantity: number; selling_price: number }[],
})

const orderTotal = computed(() =>
  orderForm.value.items.reduce((s, i) => s + i.quantity * i.selling_price, 0),
)

function openAddOrder() {
  orderForm.value = {
    order_number: '',
    customer_name: '',
    customer_ref: null,
    order_date: new Date().toISOString().slice(0, 10),
    status: 'pending',
    total_amount: 0,
    items: [{ product: 0, quantity: 1, selling_price: 0 }],
  }
  showOrderModal.value = true
}

function addOrderItem() {
  orderForm.value.items.push({ product: 0, quantity: 1, selling_price: 0 })
}

function removeOrderItem(idx: number) {
  orderForm.value.items.splice(idx, 1)
}

function onCustomerSelect() {
  const c = customers.value.find(c => c.id === orderForm.value.customer_ref)
  if (c) orderForm.value.customer_name = c.name
}

function onProductSelect(idx: number) {
  const p = products.value.find(p => p.id === orderForm.value.items[idx].product)
  if (p) orderForm.value.items[idx].selling_price = p.price
}

async function saveOrder() {
  const payload = {
    ...orderForm.value,
    total_amount: orderTotal.value,
    items: orderForm.value.items.filter(i => i.product > 0),
  }
  const res = await createOrder(payload)
  const o = res.data
  orders.value.unshift({
    id: o.id,
    orderNumber: o.order_number,
    customerName: o.customer_name,
    customerId: o.customer_ref,
    date: o.order_date,
    status: o.status,
    totalAmount: Number(o.total_amount),
  })
  showOrderModal.value = false
}

// ─── Actions ───
async function markAsShipped(id: number) {
  try { await shipOrder(id) } catch (e) { console.warn(e) }
  const order = orders.value.find((o) => o.id === id)
  if (order) order.status = 'shipped'
}

async function markAsCompleted(id: number) {
  try { await completeOrder(id) } catch (e) { console.warn(e) }
  const order = orders.value.find((o) => o.id === id)
  if (order) order.status = 'completed'
}

// ─── Load from API ───
async function loadOrders() {
  loading.value = true
  try {
    const res = await getOrders({ status: activeTab.value, page_size: 1000 })
    const rawList = Array.isArray(res?.data) ? res.data : res?.data?.results ?? []
    const apiOrders: Order[] = rawList.map((o: Record<string, unknown>) => ({
      id: o.id as number,
      orderNumber: (o.order_number as string) || '',
      customerName: (o.customer_name as string) || '',
      customerId: (o.customer_ref as number | null) ?? null,
      date: ((o.order_date ?? o.date) as string) || '',
      status: (o.status as Order['status']) || activeTab.value,
      totalAmount: Number(o.total_amount) || 0,
    }))
    orders.value = [
      ...orders.value.filter((o) => o.status !== activeTab.value),
      ...apiOrders,
    ]
  } catch (e) {
    console.warn('Orders API unavailable', e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  loadOrders()
  const [cRes, pRes] = await Promise.all([
    getCustomers({ page_size: 1000 }).catch(() => null),
    getProducts({ page_size: 1000 }).catch(() => null),
  ])
  if (cRes?.data) {
    const list = Array.isArray(cRes.data) ? cRes.data : cRes.data?.results ?? []
    customers.value = list.map((c: Record<string, unknown>) => ({ id: c.id as number, name: c.name as string }))
  }
  if (pRes?.data) {
    const list = Array.isArray(pRes.data) ? pRes.data : pRes.data?.results ?? []
    products.value = list.map((p: Record<string, unknown>) => ({
      id: p.id as number, name: p.name as string, sku: p.sku as string,
      price: Number(p.current_price ?? 0), unit: p.unit as string,
    }))
  }
})

watch(activeTab, () => loadOrders())
</script>

<template>
  <div class="space-y-6 animate-fade-in-up">
    <!-- Page Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <i class="fa-solid fa-cart-shopping text-amber-500"></i>
        <h1 class="text-xl font-bold text-slate-900 dark:text-stone-50">訂單管理</h1>
      </div>
      <button
        @click="openAddOrder"
        class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C] rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all"
      >
        <i class="fa-solid fa-plus text-xs"></i> 新增訂單
      </button>
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
            ? 'bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] text-white shadow-md'
            : 'text-slate-600 dark:text-slate-400 hover:text-amber-600'"
          @click="activeTab = tab.key"
        >
          <i :class="tab.icon" class="text-xs"></i>
          {{ tab.label }}
          <span
            class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-medium"
            :class="activeTab === tab.key ? 'bg-white/20 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'"
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
                  <button v-if="activeTab === 'pending'" @click="markAsShipped(order.id)"
                    class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-emerald-400 to-teal-500 hover:from-emerald-500 hover:to-teal-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all">
                    <i class="fa-solid fa-truck text-[10px]"></i> 標記出貨
                  </button>
                  <button v-else-if="activeTab === 'shipped'" @click="markAsCompleted(order.id)"
                    class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-emerald-400 to-teal-500 hover:from-emerald-500 hover:to-teal-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all">
                    <i class="fa-solid fa-circle-check text-[10px]"></i> 完成訂單
                  </button>
                  <span v-else class="text-xs text-slate-400 dark:text-slate-500">-</span>
                </td>
              </tr>
              <tr v-if="filteredOrders.length === 0">
                <td colspan="5" class="px-5 py-8 text-center text-slate-400 dark:text-slate-500">查無訂單資料。</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Transition>

    <!-- New Order Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showOrderModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/40" @click="showOrderModal = false"></div>
          <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between mb-5">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-stone-50">新增訂單</h3>
              <button class="text-slate-400 hover:text-slate-600" @click="showOrderModal = false">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>

            <div class="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">訂單編號</label>
                <input v-model="orderForm.order_number" type="text" placeholder="留空自動產生"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">客戶</label>
                <select v-model.number="orderForm.customer_ref" @change="onCustomerSelect"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500">
                  <option :value="null">-- 選擇客戶 --</option>
                  <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">客戶名稱（可手填）</label>
                <input v-model="orderForm.customer_name" type="text" placeholder="客戶名稱"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">訂單日期</label>
                <input v-model="orderForm.order_date" type="date"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
              </div>
            </div>

            <!-- Items -->
            <div class="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden mb-4">
              <div class="flex items-center justify-between px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
                <span class="text-xs font-semibold text-slate-600 dark:text-slate-300">訂單明細</span>
                <button @click="addOrderItem" type="button" class="inline-flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400 hover:text-purple-800">
                  <i class="fa-solid fa-plus"></i> 新增明細
                </button>
              </div>
              <div class="divide-y divide-slate-100 dark:divide-slate-700">
                <div v-for="(item, idx) in orderForm.items" :key="idx" class="flex items-center gap-2 px-4 py-2">
                  <select v-model.number="item.product" @change="onProductSelect(idx)"
                    class="flex-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500">
                    <option :value="0" disabled>選擇商品</option>
                    <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }} ({{ p.sku }})</option>
                  </select>
                  <input v-model.number="item.quantity" type="number" min="1" placeholder="數量"
                    class="w-20 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                  <input v-model.number="item.selling_price" type="number" min="0" step="0.01" placeholder="售價"
                    class="w-24 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                  <button @click="removeOrderItem(idx)" type="button" class="text-red-400 hover:text-red-600 px-1" :disabled="orderForm.items.length <= 1">
                    <i class="fa-solid fa-xmark text-xs"></i>
                  </button>
                </div>
              </div>
            </div>

            <div class="flex justify-between items-center">
              <p class="text-sm text-slate-500 dark:text-slate-400">
                合計：<span class="font-semibold text-slate-700 dark:text-stone-200">${{ orderTotal.toLocaleString() }}</span>
              </p>
              <div class="flex gap-3">
                <button class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-all" @click="showOrderModal = false">取消</button>
                <button class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 rounded-lg shadow-sm hover:-translate-y-0.5 active:scale-95 transition-all" @click="saveOrder">儲存</button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
