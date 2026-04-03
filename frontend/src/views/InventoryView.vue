<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  getProducts,
  createProduct,
  updateProduct,
  deleteProduct as apiDeleteProduct,
  getInventoryBatches,
} from '@/api/inventory'

// ─── Loading ───
const loading = ref(false)

// ─── Tab State ───
const activeTab = ref<'products' | 'stock'>('products')

// ─── Tab 1: Products ───
interface Product {
  id: number
  sku: string
  name: string
  unit: string
  price: number
}

const products = ref<Product[]>([
  { id: 1, sku: 'PF-001', name: '高級犬糧 5kg', unit: '袋', price: 45.00 },
  { id: 2, sku: 'CT-002', name: '貓咪玩具組', unit: '組', price: 12.50 },
  { id: 3, sku: 'AS-003', name: '水族箱入門套組', unit: '組', price: 89.99 },
  { id: 4, sku: 'BT-004', name: '鳥類綜合零食 500g', unit: '包', price: 8.75 },
  { id: 5, sku: 'DL-005', name: '犬用尼龍牽繩', unit: '條', price: 15.00 },
])

const showProductModal = ref(false)
const editingProduct = ref<Product | null>(null)
const productForm = ref({ sku: '', name: '', unit: '', price: 0 })

function openAddProduct() {
  editingProduct.value = null
  productForm.value = { sku: '', name: '', unit: '', price: 0 }
  showProductModal.value = true
}

function openEditProduct(product: Product) {
  editingProduct.value = product
  productForm.value = { sku: product.sku, name: product.name, unit: product.unit, price: product.price }
  showProductModal.value = true
}

async function saveProduct() {
  if (editingProduct.value) {
    try {
      await updateProduct(editingProduct.value.id, productForm.value)
    } catch (e) {
      console.warn('Failed to update product via API, applying locally', e)
    }
    const idx = products.value.findIndex((p) => p.id === editingProduct.value!.id)
    if (idx !== -1) {
      products.value[idx] = { ...products.value[idx], ...productForm.value }
    }
  } else {
    try {
      const res = await createProduct(productForm.value)
      products.value.push(res.data)
      showProductModal.value = false
      return
    } catch (e) {
      console.warn('Failed to create product via API, applying locally', e)
    }
    const newId = Math.max(...products.value.map((p) => p.id), 0) + 1
    products.value.push({ id: newId, ...productForm.value })
  }
  showProductModal.value = false
}

async function deleteProduct(id: number) {
  try {
    await apiDeleteProduct(id)
  } catch (e) {
    console.warn('Failed to delete product via API, applying locally', e)
  }
  products.value = products.value.filter((p) => p.id !== id)
}

// ─── Tab 2: Stock Levels ───
interface StockBatch {
  id: number
  productName: string
  sku: string
  batchNumber: string
  quantity: number
  remainingQuantity: number
  unitCost: number
  receivedDate: string
}

const stockBatches = ref<StockBatch[]>([
  { id: 1, productName: '高級犬糧 5kg', sku: 'PF-001', batchNumber: 'B-2026-001', quantity: 100, remainingQuantity: 42, unitCost: 32.00, receivedDate: '2026-01-15' },
  { id: 2, productName: '貓咪玩具組', sku: 'CT-002', batchNumber: 'B-2026-002', quantity: 200, remainingQuantity: 3, unitCost: 6.50, receivedDate: '2026-01-20' },
  { id: 3, productName: '水族箱入門套組', sku: 'AS-003', batchNumber: 'B-2026-003', quantity: 30, remainingQuantity: 18, unitCost: 55.00, receivedDate: '2026-02-01' },
  { id: 4, productName: '鳥類綜合零食 500g', sku: 'BT-004', batchNumber: 'B-2026-004', quantity: 150, remainingQuantity: 2, unitCost: 4.50, receivedDate: '2026-02-10' },
  { id: 5, productName: '犬用尼龍牽繩', sku: 'DL-005', batchNumber: 'B-2026-005', quantity: 80, remainingQuantity: 5, unitCost: 8.00, receivedDate: '2026-02-15' },
  { id: 6, productName: '高級犬糧 5kg', sku: 'PF-001', batchNumber: 'B-2026-006', quantity: 50, remainingQuantity: 50, unitCost: 33.00, receivedDate: '2026-03-01' },
  { id: 7, productName: '貓咪玩具組', sku: 'CT-002', batchNumber: 'B-2026-007', quantity: 100, remainingQuantity: 85, unitCost: 6.80, receivedDate: '2026-03-10' },
  { id: 8, productName: '水族箱入門套組', sku: 'AS-003', batchNumber: 'B-2026-008', quantity: 20, remainingQuantity: 1, unitCost: 56.00, receivedDate: '2026-03-20' },
])

const stockFilter = ref('all')

const uniqueProductNames = computed(() => {
  const names = new Set(stockBatches.value.map((b) => b.productName))
  return Array.from(names).sort()
})

const filteredStock = computed(() => {
  if (stockFilter.value === 'all') return stockBatches.value
  return stockBatches.value.filter((b) => b.productName === stockFilter.value)
})

// ─── Load from API ───
onMounted(async () => {
  loading.value = true
  try {
    const [productsRes, batchesRes] = await Promise.all([
      getProducts().catch(() => null),
      getInventoryBatches().catch(() => null),
    ])
    if (productsRes?.data && Array.isArray(productsRes.data)) {
      products.value = productsRes.data
    }
    if (batchesRes?.data && Array.isArray(batchesRes.data)) {
      stockBatches.value = batchesRes.data.map((b: Record<string, unknown>) => ({
        id: b.id as number,
        productName: (b.product_name as string) || '',
        sku: (b.sku as string) || '',
        batchNumber: (b.batch_number as string) || '',
        quantity: b.quantity as number,
        remainingQuantity: b.remaining_quantity as number,
        unitCost: b.unit_cost as number,
        receivedDate: (b.received_date as string) || '',
      }))
    }
  } catch (e) {
    console.warn('Inventory API unavailable, using fallback data', e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6 animate-fade-in-up">
    <!-- Page Header -->
    <div class="flex items-center gap-2">
      <i class="fa-solid fa-boxes-stacked text-amber-500"></i>
      <h1 class="text-xl font-bold text-slate-900 dark:text-stone-50">庫存管理</h1>
    </div>

    <!-- Tabs -->
    <div class="border-b border-slate-200 dark:border-slate-700">
      <nav class="flex gap-2">
        <button
          v-for="tab in ([
            { key: 'products', label: '商品管理', icon: 'fa-solid fa-box' },
            { key: 'stock', label: '庫存水位', icon: 'fa-solid fa-warehouse' },
          ] as const)"
          :key="tab.key"
          class="flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-all duration-300"
          :class="activeTab === tab.key
            ? 'bg-gradient-to-r from-amber-400 to-orange-500 text-white shadow-md'
            : 'text-slate-600 dark:text-slate-400 hover:text-amber-600'"
          @click="activeTab = tab.key"
        >
          <i :class="tab.icon" class="text-xs"></i>
          {{ tab.label }}
        </button>
      </nav>
    </div>

    <!-- Loading Spinner -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <i class="fa-solid fa-spinner fa-spin text-2xl text-amber-500"></i>
    </div>

    <template v-else>
      <!-- Tab 1: Product Management -->
      <Transition name="fade" mode="out-in">
        <div v-if="activeTab === 'products'" key="products">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">商品管理</h2>
            <button
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all duration-300"
              @click="openAddProduct"
            >
              <i class="fa-solid fa-plus text-xs"></i>
              新增商品
            </button>
          </div>

          <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-teal-400">
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-800 dark:to-slate-800">
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">SKU</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">商品名稱</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">單位</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">售價</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(product, index) in products"
                    :key="product.id"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                    :class="index % 2 === 1 ? 'bg-orange-50/30 dark:bg-gray-800/50' : ''"
                  >
                    <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ product.sku }}</td>
                    <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ product.name }}</td>
                    <td class="px-5 py-3 text-slate-500 dark:text-slate-400">{{ product.unit }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ product.price.toFixed(2) }}</td>
                    <td class="px-5 py-3 text-right">
                      <button class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all mr-2" @click="openEditProduct(product)">
                        <i class="fa-solid fa-pen-to-square"></i> 編輯
                      </button>
                      <button class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-red-400 to-rose-500 hover:from-red-500 hover:to-rose-600 rounded hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all" @click="deleteProduct(product.id)">
                        <i class="fa-solid fa-trash"></i> 刪除
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Tab 2: Stock Levels -->
      <Transition name="fade" mode="out-in">
        <div v-if="activeTab === 'stock'" key="stock">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">庫存水位</h2>
            <select
              v-model="stockFilter"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-1.5"
            >
              <option value="all">全部商品</option>
              <option v-for="name in uniqueProductNames" :key="name" :value="name">{{ name }}</option>
            </select>
          </div>

          <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-teal-400">
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-800 dark:to-slate-800">
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">商品名稱</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">SKU</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">批次編號</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">進貨數量</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">剩餘數量</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">單位成本</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">進貨日期</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(batch, index) in filteredStock"
                    :key="batch.id"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                    :class="[
                      batch.remainingQuantity <= 5
                        ? 'bg-red-50 dark:bg-red-900/20'
                        : index % 2 === 1 ? 'bg-orange-50/30 dark:bg-gray-800/50' : ''
                    ]"
                  >
                    <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ batch.productName }}</td>
                    <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ batch.sku }}</td>
                    <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ batch.batchNumber }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">{{ batch.quantity }}</td>
                    <td class="px-5 py-3 text-right font-mono" :class="batch.remainingQuantity <= 5 ? 'text-red-600 dark:text-red-400 font-bold' : 'text-slate-700 dark:text-stone-200'">
                      {{ batch.remainingQuantity }}
                      <i v-if="batch.remainingQuantity <= 5" class="fa-solid fa-triangle-exclamation text-red-500 ml-1 text-xs animate-pulse"></i>
                    </td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ batch.unitCost.toFixed(2) }}</td>
                    <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ batch.receivedDate }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Transition>
    </template>

    <!-- Product Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showProductModal" class="fixed inset-0 z-50 flex items-center justify-center">
          <div class="absolute inset-0 bg-black/40" @click="showProductModal = false"></div>
          <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md mx-4 p-6 modal-enter-active">
            <div class="flex items-center justify-between mb-5">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-stone-50">
                {{ editingProduct ? '編輯商品' : '新增商品' }}
              </h3>
              <button class="text-slate-400 hover:text-slate-600 dark:hover:text-stone-200" @click="showProductModal = false">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">SKU</label>
                <input
                  v-model="productForm.sku"
                  type="text"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="例如 PF-001"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">商品名稱</label>
                <input
                  v-model="productForm.name"
                  type="text"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="商品名稱"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">單位</label>
                <input
                  v-model="productForm.unit"
                  type="text"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="例如 袋、條、組"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">售價</label>
                <input
                  v-model.number="productForm.price"
                  type="number"
                  min="0"
                  step="0.01"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="0.00"
                />
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg active:scale-95 transition-all" @click="showProductModal = false">
                取消
              </button>
              <button class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all" @click="saveProduct">
                儲存
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
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
.modal-enter-active {
  animation: modalIn 0.25s ease-out forwards;
}
.modal-leave-active {
  animation: modalOut 0.2s ease-in forwards;
}
</style>
