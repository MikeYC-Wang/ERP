<script setup lang="ts">
import { ref, computed } from 'vue'

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
  { id: 1, sku: 'PF-001', name: 'Premium Dog Food 5kg', unit: 'bag', price: 45.00 },
  { id: 2, sku: 'CT-002', name: 'Cat Toy Mouse Set', unit: 'set', price: 12.50 },
  { id: 3, sku: 'AS-003', name: 'Aquarium Starter Kit', unit: 'kit', price: 89.99 },
  { id: 4, sku: 'BT-004', name: 'Bird Treat Mix 500g', unit: 'pack', price: 8.75 },
  { id: 5, sku: 'DL-005', name: 'Dog Leash Nylon', unit: 'piece', price: 15.00 },
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

function saveProduct() {
  if (editingProduct.value) {
    const idx = products.value.findIndex((p) => p.id === editingProduct.value!.id)
    if (idx !== -1) {
      products.value[idx] = { ...products.value[idx], ...productForm.value }
    }
  } else {
    const newId = Math.max(...products.value.map((p) => p.id), 0) + 1
    products.value.push({ id: newId, ...productForm.value })
  }
  showProductModal.value = false
}

function deleteProduct(id: number) {
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
  { id: 1, productName: 'Premium Dog Food 5kg', sku: 'PF-001', batchNumber: 'B-2026-001', quantity: 100, remainingQuantity: 42, unitCost: 32.00, receivedDate: '2026-01-15' },
  { id: 2, productName: 'Cat Toy Mouse Set', sku: 'CT-002', batchNumber: 'B-2026-002', quantity: 200, remainingQuantity: 3, unitCost: 6.50, receivedDate: '2026-01-20' },
  { id: 3, productName: 'Aquarium Starter Kit', sku: 'AS-003', batchNumber: 'B-2026-003', quantity: 30, remainingQuantity: 18, unitCost: 55.00, receivedDate: '2026-02-01' },
  { id: 4, productName: 'Bird Treat Mix 500g', sku: 'BT-004', batchNumber: 'B-2026-004', quantity: 150, remainingQuantity: 2, unitCost: 4.50, receivedDate: '2026-02-10' },
  { id: 5, productName: 'Dog Leash Nylon', sku: 'DL-005', batchNumber: 'B-2026-005', quantity: 80, remainingQuantity: 5, unitCost: 8.00, receivedDate: '2026-02-15' },
  { id: 6, productName: 'Premium Dog Food 5kg', sku: 'PF-001', batchNumber: 'B-2026-006', quantity: 50, remainingQuantity: 50, unitCost: 33.00, receivedDate: '2026-03-01' },
  { id: 7, productName: 'Cat Toy Mouse Set', sku: 'CT-002', batchNumber: 'B-2026-007', quantity: 100, remainingQuantity: 85, unitCost: 6.80, receivedDate: '2026-03-10' },
  { id: 8, productName: 'Aquarium Starter Kit', sku: 'AS-003', batchNumber: 'B-2026-008', quantity: 20, remainingQuantity: 1, unitCost: 56.00, receivedDate: '2026-03-20' },
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
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center gap-2">
      <i class="fa-solid fa-boxes-stacked text-amber-500"></i>
      <h1 class="text-xl font-bold text-slate-900 dark:text-stone-50">Inventory</h1>
    </div>

    <!-- Tabs -->
    <div class="border-b border-slate-200 dark:border-slate-700">
      <nav class="flex gap-4">
        <button
          v-for="tab in ([
            { key: 'products', label: 'Product Management', icon: 'fa-solid fa-box' },
            { key: 'stock', label: 'Stock Levels', icon: 'fa-solid fa-warehouse' },
          ] as const)"
          :key="tab.key"
          class="flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors"
          :class="activeTab === tab.key
            ? 'border-amber-500 text-amber-600 dark:text-amber-400'
            : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-stone-200'"
          @click="activeTab = tab.key"
        >
          <i :class="tab.icon" class="text-xs"></i>
          {{ tab.label }}
        </button>
      </nav>
    </div>

    <!-- ═══════ Tab 1: Product Management ═══════ -->
    <div v-if="activeTab === 'products'">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">Products</h2>
        <button
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-500 hover:bg-amber-600 rounded-lg shadow-sm transition-colors"
          @click="openAddProduct"
        >
          <i class="fa-solid fa-plus text-xs"></i>
          Add Product
        </button>
      </div>

      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700">
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">SKU</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Product Name</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Unit</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Price</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(product, index) in products"
                :key="product.id"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                :class="index % 2 === 1 ? 'bg-slate-50/50 dark:bg-slate-800/30' : ''"
              >
                <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ product.sku }}</td>
                <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ product.name }}</td>
                <td class="px-5 py-3 text-slate-500 dark:text-slate-400">{{ product.unit }}</td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ product.price.toFixed(2) }}</td>
                <td class="px-5 py-3 text-right">
                  <button class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors mr-2" @click="openEditProduct(product)">
                    <i class="fa-solid fa-pen-to-square"></i> Edit
                  </button>
                  <button class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors" @click="deleteProduct(product.id)">
                    <i class="fa-solid fa-trash"></i> Delete
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ═══════ Tab 2: Stock Levels ═══════ -->
    <div v-if="activeTab === 'stock'">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">Stock Levels</h2>
        <select
          v-model="stockFilter"
          class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-1.5"
        >
          <option value="all">All Products</option>
          <option v-for="name in uniqueProductNames" :key="name" :value="name">{{ name }}</option>
        </select>
      </div>

      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700">
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Product Name</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">SKU</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Batch No.</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Received Qty</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Remaining</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Unit Cost</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Received Date</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(batch, index) in filteredStock"
                :key="batch.id"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                :class="[
                  batch.remainingQuantity <= 5
                    ? 'bg-red-50 dark:bg-red-900/20'
                    : index % 2 === 1 ? 'bg-slate-50/50 dark:bg-slate-800/30' : ''
                ]"
              >
                <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ batch.productName }}</td>
                <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ batch.sku }}</td>
                <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ batch.batchNumber }}</td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">{{ batch.quantity }}</td>
                <td class="px-5 py-3 text-right font-mono" :class="batch.remainingQuantity <= 5 ? 'text-red-600 dark:text-red-400 font-bold' : 'text-slate-700 dark:text-stone-200'">
                  {{ batch.remainingQuantity }}
                  <i v-if="batch.remainingQuantity <= 5" class="fa-solid fa-triangle-exclamation text-red-500 ml-1 text-xs"></i>
                </td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ batch.unitCost.toFixed(2) }}</td>
                <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ batch.receivedDate }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ═══════ Product Modal ═══════ -->
    <Teleport to="body">
      <div v-if="showProductModal" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/40" @click="showProductModal = false"></div>
        <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
          <div class="flex items-center justify-between mb-5">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-stone-50">
              {{ editingProduct ? 'Edit Product' : 'Add Product' }}
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
                placeholder="e.g. PF-001"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">Name</label>
              <input
                v-model="productForm.name"
                type="text"
                class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                placeholder="Product name"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">Unit</label>
              <input
                v-model="productForm.unit"
                type="text"
                class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                placeholder="e.g. bag, piece, set"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">Price</label>
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
            <button class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors" @click="showProductModal = false">
              Cancel
            </button>
            <button class="px-4 py-2 text-sm font-medium text-white bg-amber-500 hover:bg-amber-600 rounded-lg shadow-sm transition-colors" @click="saveProduct">
              Save
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
