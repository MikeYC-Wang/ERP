<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import jsPDF from 'jspdf'
import {
  getProducts,
  createProduct,
  updateProduct,
  deleteProduct as apiDeleteProduct,
  getInventoryBatches,
  getStockSummary,
  getPurchaseOrders,
  createPurchaseOrder,
  updatePurchaseOrder,
  deletePurchaseOrder,
  receivePurchaseOrder,
  bulkImportProducts,
  parseProductsXlsx,
  getCategories,
  createCategory,
  updateCategory,
  deleteCategory,
} from '@/api/inventory'
import { getSuppliers } from '@/api/suppliers'

// ─── Loading ───
const loading = ref(false)

// ─── Tab State ───
const activeTab = ref<'products' | 'stock' | 'count' | 'purchase'>('products')

// ─── Tab 1: Products ───
interface PackagingForm {
  id?: number
  name: string
  quantity: number
  price: number
  cost: number
  barcode: string
  is_default: boolean
}

interface Product {
  id: number
  sku: string
  name: string
  unit: string
  baseUnit: string
  price: number
  lastCost: number
  safetyStock: number
  supplier: number | null
  supplierName: string
  category: number | null
  categoryName: string
  packagings: PackagingForm[]
}

interface CategoryRow {
  id: number
  name: string
  parent: number | null
  parent_name?: string
  full_name?: string
  children_count?: number
}

const categories = ref<CategoryRow[]>([])
const topCategories = computed(() => categories.value.filter(c => c.parent === null))
function childCategoriesOf(parentId: number | null): CategoryRow[] {
  if (parentId === null) return []
  return categories.value.filter(c => c.parent === parentId)
}
function defaultPkg(p: Product) {
  return p.packagings.find(k => k.is_default) || p.packagings.find(k => k.quantity === 1) || p.packagings[0]
}
function boxPkg(p: Product) {
  return p.packagings.find(k => !k.is_default && k.quantity > 1)
}
function unitPriceOf(p: Product): number {
  const d = defaultPkg(p); return d ? Number(d.price) : Number(p.price ?? 0)
}
function barcodeOf(p: Product): string {
  const d = defaultPkg(p); return d?.barcode || ''
}
function packQtyOf(p: Product): number {
  const b = boxPkg(p); return b ? Number(b.quantity) : 0
}
function packPriceOf(p: Product): number {
  const b = boxPkg(p); return b ? Number(b.price) : 0
}

function categoryFullName(id: number | null): string {
  if (id === null) return ''
  const c = categories.value.find(x => x.id === id)
  if (!c) return ''
  if (c.parent === null) return c.name
  const parent = categories.value.find(x => x.id === c.parent)
  return parent ? `${parent.name} / ${c.name}` : c.name
}

// Filter bar state (for product table)
const filterTopCategory = ref<number | null>(null)
const filterSubCategory = ref<number | null>(null)
const filterSupplier = ref<number | null>(null)
const filterSearch = ref('')

const filteredProducts = computed(() => {
  const q = filterSearch.value.trim().toLowerCase()
  return products.value.filter(p => {
    if (filterSubCategory.value !== null) {
      if (p.category !== filterSubCategory.value) return false
    } else if (filterTopCategory.value !== null) {
      // top selected, any sub: match if product.category === top OR its parent === top
      const catId = p.category
      if (catId === null) return false
      if (catId === filterTopCategory.value) return true
      const cat = categories.value.find(c => c.id === catId)
      if (!cat || cat.parent !== filterTopCategory.value) return false
    }
    if (filterSupplier.value !== null && p.supplier !== filterSupplier.value) return false
    if (q) {
      if (!p.name.toLowerCase().includes(q) && !p.sku.toLowerCase().includes(q)) return false
    }
    return true
  })
})

function onFilterTopChange() {
  filterSubCategory.value = null
}

const productPage = ref(1)
const productPageSize = 15
const productTotalPages = computed(() => Math.max(1, Math.ceil(filteredProducts.value.length / productPageSize)))
const pagedProducts = computed(() => {
  const start = (productPage.value - 1) * productPageSize
  return filteredProducts.value.slice(start, start + productPageSize)
})
watch([filterTopCategory, filterSubCategory, filterSupplier, filterSearch], () => { productPage.value = 1 })

// Product modal cascading category
const formTopCategory = ref<number | null>(null)

// Category management modal
const showCategoryModal = ref(false)
const newTopName = ref('')
const newChildName = ref<Record<number, string>>({})
const editingCategoryId = ref<number | null>(null)
const editingCategoryName = ref('')

async function loadCategories() {
  try {
    const res = await getCategories({ page_size: 1000 })
    const list = Array.isArray(res.data) ? res.data : res.data?.results ?? []
    categories.value = list.map((c: Record<string, unknown>) => ({
      id: c.id as number,
      name: c.name as string,
      parent: (c.parent as number | null) ?? null,
      parent_name: (c.parent_name as string) || '',
      full_name: (c.full_name as string) || '',
      children_count: Number(c.children_count ?? 0),
    }))
  } catch (e) {
    console.warn('Failed to load categories', e)
  }
}

function openCategoryModal() {
  showCategoryModal.value = true
  newTopName.value = ''
  newChildName.value = {}
  editingCategoryId.value = null
  editingCategoryName.value = ''
}

async function addTopCategory() {
  const name = newTopName.value.trim()
  if (!name) { alert('請輸入分類名稱'); return }
  try {
    await createCategory({ name, parent: null })
    newTopName.value = ''
    await loadCategories()
  } catch (e: unknown) {
    const err = e as { response?: { data?: Record<string, unknown> } }
    alert('新增失敗：' + JSON.stringify(err.response?.data ?? e))
  }
}

async function addChildCategory(parentId: number) {
  const name = (newChildName.value[parentId] || '').trim()
  if (!name) { alert('請輸入子類名稱'); return }
  try {
    await createCategory({ name, parent: parentId })
    newChildName.value[parentId] = ''
    await loadCategories()
  } catch (e: unknown) {
    const err = e as { response?: { data?: Record<string, unknown> } }
    alert('新增失敗：' + JSON.stringify(err.response?.data ?? e))
  }
}

function startEditCategory(cat: CategoryRow) {
  editingCategoryId.value = cat.id
  editingCategoryName.value = cat.name
}

async function saveEditCategory() {
  if (editingCategoryId.value === null) return
  const name = editingCategoryName.value.trim()
  if (!name) { alert('名稱必填'); return }
  const cat = categories.value.find(c => c.id === editingCategoryId.value)
  if (!cat) return
  try {
    await updateCategory(cat.id, { name, parent: cat.parent })
    editingCategoryId.value = null
    editingCategoryName.value = ''
    await loadCategories()
  } catch (e: unknown) {
    const err = e as { response?: { data?: Record<string, unknown> } }
    alert('更新失敗：' + JSON.stringify(err.response?.data ?? e))
  }
}

async function removeCategory(id: number) {
  if (!confirm('確定要刪除此分類？')) return
  try {
    await deleteCategory(id)
    await loadCategories()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    alert(err.response?.data?.error || '刪除失敗')
  }
}

const products = ref<Product[]>([])
const suppliers = ref<{ id: number; name: string }[]>([])

const showProductModal = ref(false)
const editingProduct = ref<Product | null>(null)
const productForm = ref<{
  sku: string
  name: string
  baseUnit: string
  safetyStock: number
  supplier: number | null
  category: number | null
  packagings: PackagingForm[]
}>({
  sku: '',
  name: '',
  baseUnit: '個',
  safetyStock: 0,
  supplier: null,
  category: null,
  packagings: [{ name: '單個', quantity: 1, price: 0, cost: 0, barcode: '', is_default: true }],
})

function newDefaultPackaging(baseUnit: string): PackagingForm {
  return { name: baseUnit || '單個', quantity: 1, price: 0, cost: 0, barcode: '', is_default: true }
}

function openAddProduct() {
  editingProduct.value = null
  productForm.value = {
    sku: '',
    name: '',
    baseUnit: '個',
    safetyStock: 0,
    supplier: null,
    category: null,
    packagings: [newDefaultPackaging('個')],
  }
  formTopCategory.value = null
  showProductModal.value = true
}

function openEditProduct(product: Product) {
  editingProduct.value = product
  productForm.value = {
    sku: product.sku,
    name: product.name,
    baseUnit: product.baseUnit || product.unit || '個',
    safetyStock: product.safetyStock,
    supplier: product.supplier,
    category: product.category,
    packagings: product.packagings.length > 0
      ? product.packagings.map(p => ({ ...p }))
      : [newDefaultPackaging(product.baseUnit || '個')],
  }
  // derive top-level category for cascading dropdown
  if (product.category !== null) {
    const cat = categories.value.find(c => c.id === product.category)
    if (cat) {
      formTopCategory.value = cat.parent === null ? cat.id : cat.parent
    } else {
      formTopCategory.value = null
    }
  } else {
    formTopCategory.value = null
  }
  showProductModal.value = true
}

function onFormTopCategoryChange() {
  productForm.value.category = formTopCategory.value
}

function addPackagingRow() {
  productForm.value.packagings.push({
    name: '', quantity: 1, price: 0, cost: 0, barcode: '', is_default: false,
  })
}

function removePackagingRow(idx: number) {
  const row = productForm.value.packagings[idx]
  // Don't allow removing the last qty=1 row
  const baseRows = productForm.value.packagings.filter(p => Number(p.quantity) === 1)
  if (Number(row.quantity) === 1 && baseRows.length <= 1) {
    alert('必須保留至少一個基本包裝 (數量=1)')
    return
  }
  productForm.value.packagings.splice(idx, 1)
  // Re-assign default if we removed the default
  if (row.is_default && productForm.value.packagings.length > 0) {
    productForm.value.packagings[0].is_default = true
  }
}

function setDefaultPackaging(idx: number) {
  productForm.value.packagings.forEach((p, i) => { p.is_default = i === idx })
}

function mapProductFromApi(p: Record<string, unknown>): Product {
  const pkgs = (p.packagings as Record<string, unknown>[] | undefined) ?? []
  return {
    id: p.id as number,
    sku: p.sku as string,
    name: p.name as string,
    unit: (p.unit as string) || '',
    baseUnit: (p.base_unit as string) || (p.unit as string) || '個',
    price: Number(p.current_price ?? 0),
    lastCost: Number(p.last_cost ?? 0),
    safetyStock: Number(p.safety_stock ?? 0),
    supplier: (p.supplier as number | null) ?? null,
    supplierName: (p.supplier_name as string) || '',
    category: (p.category as number | null) ?? null,
    categoryName: (p.category_name as string) || '',
    packagings: pkgs.map(k => ({
      id: k.id as number,
      name: k.name as string,
      quantity: Number(k.quantity ?? 1),
      price: Number(k.price ?? 0),
      cost: Number(k.cost ?? 0),
      barcode: (k.barcode as string) || '',
      is_default: Boolean(k.is_default),
    })),
  }
}

async function saveProduct() {
  // Validate
  const f = productForm.value
  if (!f.sku || !f.name) { alert('SKU 與商品名稱為必填'); return }
  if (f.packagings.length === 0) { alert('至少需一個包裝'); return }
  const defaults = f.packagings.filter(p => p.is_default)
  if (defaults.length !== 1) { alert('必須恰好一個預設包裝'); return }
  if (!f.packagings.some(p => Number(p.quantity) === 1)) {
    alert('必須包含一個基本包裝 (數量=1)'); return
  }
  if (f.packagings.some(p => Number(p.quantity) < 1)) {
    alert('每個包裝數量必須 >= 1'); return
  }

  // Use default packaging's price as current_price
  const defaultPkg = defaults[0]
  const payload = {
    sku: f.sku,
    name: f.name,
    unit: f.baseUnit,
    base_unit: f.baseUnit,
    current_price: defaultPkg.price,
    safety_stock: f.safetyStock,
    supplier: f.supplier,
    category: f.category,
    packagings: f.packagings.map(p => ({
      name: p.name || f.baseUnit,
      quantity: Number(p.quantity),
      price: Number(p.price),
      cost: Number(p.cost),
      barcode: p.barcode || '',
      is_default: p.is_default,
    })),
  }

  try {
    if (editingProduct.value) {
      const res = await updateProduct(editingProduct.value.id, payload as Record<string, unknown>)
      const mapped = mapProductFromApi(res.data)
      const idx = products.value.findIndex(p => p.id === editingProduct.value!.id)
      if (idx !== -1) products.value[idx] = mapped
    } else {
      const res = await createProduct(payload as Record<string, unknown>)
      products.value.push(mapProductFromApi(res.data))
    }
  } catch (e) {
    console.warn('Failed to save product via API', e)
    alert('儲存失敗')
    return
  }
  showProductModal.value = false
  await loadStockSummary()
}

async function deleteProduct(id: number) {
  try {
    await apiDeleteProduct(id)
  } catch (e) {
    console.warn('Failed to delete product via API, applying locally', e)
  }
  products.value = products.value.filter((p) => p.id !== id)
  await loadStockSummary()
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

const stockBatches = ref<StockBatch[]>([])

function productMatchesFilters(p: Product | undefined): boolean {
  if (!p) return false
  if (filterSubCategory.value !== null) {
    if (p.category !== filterSubCategory.value) return false
  } else if (filterTopCategory.value !== null) {
    if (p.category === null) return false
    if (p.category !== filterTopCategory.value) {
      const cat = categories.value.find(c => c.id === p.category)
      if (!cat || cat.parent !== filterTopCategory.value) return false
    }
  }
  if (filterSupplier.value !== null && p.supplier !== filterSupplier.value) return false
  const q = filterSearch.value.trim().toLowerCase()
  if (q && !p.name.toLowerCase().includes(q) && !p.sku.toLowerCase().includes(q)) return false
  return true
}

const filteredStock = computed(() => {
  return stockBatches.value.filter((b) => {
    const p = products.value.find(pp => pp.sku === b.sku)
    return productMatchesFilters(p)
  })
})

// ─── Tab 3: Inventory Count (盤點) ───
interface StockSummaryRow {
  id: number
  sku: string
  name: string
  unit: string
  safetyStock: number
  totalRemaining: number
  isLow: boolean
}

const stockSummary = ref<StockSummaryRow[]>([])
// Local actual count input: productId -> number
const actualCounts = ref<Record<number, number | null>>({})

const countRows = computed(() =>
  stockSummary.value
    .filter((row) => productMatchesFilters(products.value.find(p => p.id === row.id)))
    .map((row) => {
      const actual = actualCounts.value[row.id] ?? null
      const variance = actual !== null ? actual - row.totalRemaining : null
      return { ...row, actual, variance }
    })
)

const lowStockItems = computed(() =>
  stockSummary.value.filter((r) => r.isLow)
)

async function loadStockSummary() {
  try {
    const res = await getStockSummary()
    const data: Record<string, unknown>[] = Array.isArray(res.data) ? res.data : res.data?.results ?? []
    stockSummary.value = data.map((r) => ({
      id: r.id as number,
      sku: r.sku as string,
      name: r.name as string,
      unit: r.unit as string,
      safetyStock: Number(r.safety_stock ?? 0),
      totalRemaining: Number(r.total_remaining ?? 0),
      isLow: r.is_low as boolean,
    }))
  } catch (e) {
    console.warn('Failed to load stock summary', e)
  }
}

// ─── Tab 4: Purchase Management ───
interface PurchaseItem {
  id?: number
  product: number
  packaging: number | null
  quantity: number
  fee: number
}

interface PurchaseOrderLocal {
  id: number
  order_number: string
  supplier: string
  date: string
  status: string
  items: PurchaseItem[]
}
type PurchaseOrder = PurchaseOrderLocal

const STATUS_LABELS: Record<string, string> = {
  draft: '草稿', confirmed: '已確認', received: '已到貨', cancelled: '已取消',
}
const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  confirmed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  received: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
  cancelled: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-300',
}

const purchaseOrders = ref<PurchaseOrder[]>([])
const supplierNames = ref<string[]>([])
const showPurchaseModal = ref(false)
const editingPurchase = ref<PurchaseOrder | null>(null)
const purchaseForm = ref({
  order_number: '',
  supplier: '',
  date: new Date().toISOString().slice(0, 10),
  status: 'draft',
  items: [{ product: 0, packaging: null, quantity: 1, fee: 0 }] as PurchaseItem[],
})
const purchaseStatusFilter = ref('all')

const filteredPurchases = computed(() =>
  purchaseStatusFilter.value === 'all'
    ? purchaseOrders.value
    : purchaseOrders.value.filter(p => p.status === purchaseStatusFilter.value)
)

function openAddPurchase() {
  editingPurchase.value = null
  purchaseForm.value = {
    order_number: '',
    supplier: '',
    date: new Date().toISOString().slice(0, 10),
    status: 'draft',
    items: [{ product: 0, packaging: null, quantity: 1, fee: 0 }],
  }
  showPurchaseModal.value = true
}

function openEditPurchase(p: PurchaseOrder) {
  editingPurchase.value = p
  purchaseForm.value = {
    order_number: p.order_number,
    supplier: p.supplier,
    date: p.date,
    status: p.status,
    items: p.items.map(i => ({ id: i.id, product: i.product, packaging: (i as PurchaseItem).packaging ?? null, quantity: i.quantity, fee: i.fee })),
  }
  showPurchaseModal.value = true
}

function addPurchaseItem() {
  purchaseForm.value.items.push({ product: 0, packaging: null, quantity: 1, fee: 0 })
}

function onPurchaseProductChange(idx: number) {
  const item = purchaseForm.value.items[idx]
  const prod = products.value.find(p => p.id === item.product)
  if (prod) {
    const def = prod.packagings.find(pk => pk.is_default) || prod.packagings[0]
    item.packaging = def?.id ?? null
    // 商品切換：一律重置 fee 為新包裝的 cost (之前 fee 屬於不同商品)
    item.fee = def && Number(def.cost) > 0 ? Number(def.cost) : 0
  }
}

function getProductPackagings(productId: number): PackagingForm[] {
  return products.value.find(p => p.id === productId)?.packagings ?? []
}

function removePurchaseItem(idx: number) {
  purchaseForm.value.items.splice(idx, 1)
}

async function savePurchase() {
  const payload = { ...purchaseForm.value, items: purchaseForm.value.items.filter(i => i.product) }
  if (editingPurchase.value) {
    const res = await updatePurchaseOrder(editingPurchase.value.id, payload)
    const idx = purchaseOrders.value.findIndex(p => p.id === editingPurchase.value!.id)
    if (idx !== -1) purchaseOrders.value[idx] = res.data
  } else {
    const res = await createPurchaseOrder(payload)
    purchaseOrders.value.unshift(res.data)
  }
  showPurchaseModal.value = false
}

async function removePurchase(id: number) {
  if (!confirm('確定要刪除此採購單？')) return
  await deletePurchaseOrder(id)
  purchaseOrders.value = purchaseOrders.value.filter(p => p.id !== id)
}

function exportPurchasePDF(po: PurchaseOrder) {
  try {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const pageW = doc.internal.pageSize.getWidth()

  // Header
  doc.setFontSize(18)
  doc.setFont('helvetica', 'bold')
  doc.text('Purchase Order', pageW / 2, 20, { align: 'center' })

  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')
  doc.text(`PO Number : ${po.order_number}`, 14, 35)
  doc.text(`Supplier  : ${po.supplier}`, 14, 42)
  doc.text(`Date      : ${po.date}`, 14, 49)
  doc.text(`Status    : ${STATUS_LABELS[po.status] ?? po.status}`, 14, 56)

  // Table header
  let y = 68
  doc.setFillColor(80, 60, 120)
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(9)
  doc.setFont('helvetica', 'bold')
  doc.rect(14, y - 5, pageW - 28, 8, 'F')
  doc.text('Product ID', 16, y)
  doc.text('Qty', 80, y)
  doc.text('Package Price', 105, y)
  doc.text('Amount', 150, y)

  // Table rows
  doc.setTextColor(0, 0, 0)
  doc.setFont('helvetica', 'normal')
  let total = 0
  po.items.forEach((item, i) => {
    y += 10
    if (i % 2 === 0) {
      doc.setFillColor(245, 245, 250)
      doc.rect(14, y - 5, pageW - 28, 8, 'F')
    }
    const prod = products.value.find(p => p.id === item.product)
    const name = prod ? `${prod.name} (${prod.sku})` : `Product #${item.product}`
    const amount = Number(item.fee) * Number(item.quantity)
    total += amount
    doc.text(name.substring(0, 38), 16, y)
    doc.text(String(item.quantity), 80, y)
    doc.text(`$${Number(item.fee).toFixed(2)}`, 105, y)
    doc.text(`$${amount.toFixed(2)}`, 150, y)
  })

  // Total
  y += 12
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.text(`Total: $${total.toLocaleString(undefined, { minimumFractionDigits: 2 })}`, pageW - 14, y, { align: 'right' })

  // Footer
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(150, 150, 150)
  doc.text('PerPetsStore ERP — Generated automatically', pageW / 2, 285, { align: 'center' })

  doc.save(`${po.order_number}.pdf`)
  } catch (e) {
    console.error('PDF 匯出失敗', e)
    alert('PDF 匯出失敗，請稍後再試')
  }
}

async function confirmReceive(id: number) {
  if (!confirm('確認收貨？這會建立庫存批次。')) return
  const res = await receivePurchaseOrder(id)
  const idx = purchaseOrders.value.findIndex(p => p.id === id)
  if (idx !== -1) purchaseOrders.value[idx] = res.data
  await loadStockSummary()
}

// ─── Bulk Import ───
interface BulkRow {
  sku: string
  name: string
  barcode: string
  baseUnit: string
  unitPrice: number
  packQty: number
  packPrice: number
}

const showBulkModal = ref(false)
const bulkStep = ref<1 | 2>(1)
const bulkMode = ref<'xlsx' | 'manual'>('xlsx')
const bulkSupplier = ref<number | null>(null)
const bulkTopCategory = ref<number | null>(null)
const bulkCategory = ref<number | null>(null)
function onBulkTopCategoryChange() {
  bulkCategory.value = bulkTopCategory.value
}
const bulkRows = ref<BulkRow[]>([])
const bulkWarnings = ref<string[]>([])
const bulkSkipped = ref<{ index: number; sku: string; reason: string }[]>([])
const bulkLoading = ref(false)
const bulkFileInput = ref<HTMLInputElement | null>(null)
const bulkFile = ref<File | null>(null)
const bulkSheetNames = ref<string[]>([])
const bulkSelectedSheet = ref<string>('')

function emptyBulkRow(): BulkRow {
  return { sku: '', name: '', barcode: '', baseUnit: '個', unitPrice: 0, packQty: 0, packPrice: 0 }
}

function openBulkModal() {
  showBulkModal.value = true
  bulkStep.value = 1
  bulkMode.value = 'xlsx'
  bulkSupplier.value = suppliers.value[0]?.id ?? null
  bulkTopCategory.value = null
  bulkCategory.value = null
  bulkRows.value = []
  bulkWarnings.value = []
  bulkSkipped.value = []
  bulkFile.value = null
  bulkSheetNames.value = []
  bulkSelectedSheet.value = ''
}

function closeBulkModal() {
  showBulkModal.value = false
}

async function onBulkFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  bulkFile.value = file
  await runBulkParse()
}

async function runBulkParse() {
  if (!bulkFile.value) return
  bulkLoading.value = true
  try {
    const res = await parseProductsXlsx(bulkFile.value, bulkSelectedSheet.value || undefined)
    const rows = (res.data?.rows ?? []) as Array<Record<string, unknown>>
    bulkWarnings.value = (res.data?.warnings ?? []) as string[]
    bulkSheetNames.value = (res.data?.sheet_names ?? []) as string[]
    bulkSelectedSheet.value = (res.data?.selected_sheet as string) || bulkSheetNames.value[0] || ''
    bulkRows.value = rows.map(r => {
      const packagings = (r.packagings as Array<Record<string, unknown>>) ?? []
      const base = packagings.find(p => Number(p.quantity) === 1) ?? packagings[0] ?? {}
      const box = packagings.find(p => Number(p.quantity) > 1)
      return {
        sku: String(r.sku ?? ''),
        name: String(r.name ?? ''),
        barcode: String(r.barcode ?? ''),
        baseUnit: String(r.base_unit ?? '個'),
        unitPrice: Number(base.price ?? 0),
        packQty: box ? Number(box.quantity) : 0,
        packPrice: box ? Number(box.price) : 0,
      }
    })
    bulkStep.value = 2
  } catch (err) {
    alert('解析失敗：' + ((err as { response?: { data?: { error?: string } } }).response?.data?.error ?? String(err)))
  } finally {
    bulkLoading.value = false
    if (bulkFileInput.value) bulkFileInput.value.value = ''
  }
}

async function onBulkSheetChange() {
  await runBulkParse()
}

function goManualStep2() {
  bulkRows.value = [emptyBulkRow()]
  bulkWarnings.value = []
  bulkStep.value = 2
}

function addBulkRow() {
  bulkRows.value.push(emptyBulkRow())
}
function removeBulkRow(idx: number) {
  bulkRows.value.splice(idx, 1)
}
function clearBulkRows() {
  if (confirm('確定全部清空？')) bulkRows.value = []
}

const bulkInvalidCount = computed(() => {
  const skuSet = new Set<string>()
  const dupes = new Set<string>()
  for (const r of bulkRows.value) {
    const k = r.sku.trim()
    if (!k) continue
    if (skuSet.has(k)) dupes.add(k)
    skuSet.add(k)
  }
  return bulkRows.value.filter(r => !r.sku.trim() || !r.name.trim() || dupes.has(r.sku.trim())).length
})

function rowIsDuplicate(row: BulkRow): boolean {
  const k = row.sku.trim()
  if (!k) return false
  return bulkRows.value.filter(r => r.sku.trim() === k).length > 1
}

async function confirmBulkImport() {
  if (!bulkSupplier.value) {
    alert('請選擇供應商')
    return
  }
  if (bulkRows.value.length === 0) {
    alert('沒有任何資料')
    return
  }
  if (bulkInvalidCount.value > 0) {
    if (!confirm(`有 ${bulkInvalidCount.value} 筆不符合資料會被跳過，繼續？`)) return
  }
  const payload = {
    supplier: bulkSupplier.value,
    rows: bulkRows.value
      .filter(r => r.sku.trim() && r.name.trim() && !rowIsDuplicate(r))
      .map(r => {
        const round3 = (n: number) => Math.round((Number(n) || 0) * 1000) / 1000
        const unit = round3(r.unitPrice)
        const pack = round3(r.packPrice)
        const packagings: PackagingForm[] = [{
          name: r.baseUnit || '單個',
          quantity: 1,
          price: unit,
          cost: unit,
          barcode: r.barcode,
          is_default: true,
        }]
        if (r.packQty > 1 && pack > 0) {
          packagings.push({
            name: `整箱(${r.packQty})`,
            quantity: r.packQty,
            price: pack,
            cost: pack,
            barcode: '',
            is_default: false,
          })
        }
        return {
          sku: r.sku.trim(),
          name: r.name.trim(),
          barcode: r.barcode,
          base_unit: r.baseUnit || '個',
          safety_stock: 0,
          category: bulkCategory.value,
          packagings,
        }
      }),
  }
  bulkLoading.value = true
  try {
    const res = await bulkImportProducts(payload)
    const created = res.data?.created ?? 0
    const skipped = res.data?.skipped ?? []
    bulkSkipped.value = skipped
    alert(`成功匯入 ${created} 筆，跳過 ${skipped.length} 筆`)
    await reloadProducts()
    if (skipped.length === 0) {
      closeBulkModal()
    }
  } catch (err) {
    alert('匯入失敗：' + ((err as { response?: { data?: { error?: string } } }).response?.data?.error ?? String(err)))
  } finally {
    bulkLoading.value = false
  }
}

async function reloadProducts() {
  const res = await getProducts({ page_size: 1000 }).catch(() => null)
  if (res?.data) {
    const list = Array.isArray(res.data) ? res.data : res.data?.results ?? []
    products.value = list.map((p: Record<string, unknown>) => mapProductFromApi(p))
  }
}

// ─── Load from API ───
onMounted(async () => {
  loading.value = true
  try {
    const [productsRes, batchesRes, purchasesRes, suppliersRes] = await Promise.all([
      getProducts({ page_size: 1000 }).catch(() => null),
      getInventoryBatches().catch(() => null),
      getPurchaseOrders({ page_size: 1000 }).catch(() => null),
      getSuppliers({ page_size: 1000 }).catch(() => null),
    ])
    if (productsRes?.data) {
      const productList = Array.isArray(productsRes.data) ? productsRes.data : productsRes.data?.results ?? []
      products.value = productList.map((p: Record<string, unknown>) => mapProductFromApi(p))
    }
    const productMap = new Map<number, Product>()
    for (const p of products.value) {
      productMap.set(p.id, p)
    }
    if (batchesRes?.data) {
      const batchList = Array.isArray(batchesRes.data) ? batchesRes.data : batchesRes.data?.results ?? []
      stockBatches.value = batchList.map((b: Record<string, unknown>) => {
        const prod = productMap.get(b.product as number)
        return {
          id: b.id as number,
          productName: prod?.name ?? '',
          sku: prod?.sku ?? '',
          batchNumber: `BATCH-${b.id}`,
          quantity: Number(b.batch_quantity ?? 0),
          remainingQuantity: Number(b.remaining_quantity ?? 0),
          unitCost: Number(b.unit_cost ?? 0),
          receivedDate: (b.received_date as string) || '',
        }
      })
    }
    if (purchasesRes?.data) {
      const list = Array.isArray(purchasesRes.data) ? purchasesRes.data : purchasesRes.data?.results ?? []
      purchaseOrders.value = list
    }
    if (suppliersRes?.data) {
      const list = Array.isArray(suppliersRes.data) ? suppliersRes.data : suppliersRes.data?.results ?? []
      suppliers.value = list.map((s: Record<string, unknown>) => ({ id: s.id as number, name: s.name as string }))
      supplierNames.value = suppliers.value.map(s => s.name)
    }
    await loadStockSummary()
    await loadCategories()
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
      <!-- Safety stock warning badge -->
      <span
        v-if="lowStockItems.length > 0"
        class="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold text-white bg-red-500 rounded-full animate-pulse"
      >
        <i class="fa-solid fa-triangle-exclamation"></i>
        {{ lowStockItems.length }} 項低庫存警示
      </span>
    </div>

    <!-- Low Stock Alert Banner -->
    <div
      v-if="lowStockItems.length > 0"
      class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl px-4 py-3 flex flex-wrap gap-2 items-start"
    >
      <i class="fa-solid fa-triangle-exclamation text-red-500 mt-0.5 shrink-0"></i>
      <div>
        <p class="text-sm font-semibold text-red-700 dark:text-red-400 mb-1">庫存低於安全庫存量警示</p>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="item in lowStockItems"
            :key="item.id"
            class="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 rounded-full border border-red-300 dark:border-red-700"
          >
            {{ item.name }} — 剩餘 {{ item.totalRemaining }}{{ item.unit }} (安全量 {{ item.safetyStock }})
          </span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-slate-200 dark:border-slate-700">
      <nav class="flex gap-2">
        <button
          v-for="tab in ([
            { key: 'products', label: '商品管理', icon: 'fa-solid fa-box' },
            { key: 'stock', label: '庫存水位', icon: 'fa-solid fa-warehouse' },
            { key: 'count', label: '庫存盤點', icon: 'fa-solid fa-clipboard-check' },
            { key: 'purchase', label: '採購管理', icon: 'fa-solid fa-file-invoice' },
          ] as const)"
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
            v-if="tab.key === 'count' && lowStockItems.length > 0"
            class="inline-flex items-center justify-center w-4 h-4 text-xs font-bold text-white bg-red-500 rounded-full"
          >{{ lowStockItems.length }}</span>
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
          <div class="flex flex-wrap items-center justify-between mb-4 gap-2">
            <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">商品管理</h2>
            <div class="flex items-center gap-2 flex-wrap">
              <button
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all duration-300"
                @click="openCategoryModal"
              >
                <i class="fa-solid fa-sitemap text-xs"></i>
                分類管理
              </button>
              <button
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all duration-300"
                @click="openBulkModal"
              >
                <i class="fa-solid fa-file-import text-xs"></i>
                批次新增
              </button>
              <button
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C] rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all duration-300"
                @click="openAddProduct"
              >
                <i class="fa-solid fa-plus text-xs"></i>
                新增商品
              </button>
            </div>
          </div>

          <!-- Filter bar -->
          <div class="flex flex-col md:flex-row md:items-center gap-2 mb-3">
            <select v-model.number="filterTopCategory" @change="onFilterTopChange"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:w-44">
              <option :value="null">全部大類</option>
              <option v-for="c in topCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
            <select v-model.number="filterSubCategory" :disabled="filterTopCategory === null"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:w-44 disabled:opacity-50">
              <option :value="null">全部子類</option>
              <option v-for="c in childCategoriesOf(filterTopCategory)" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
            <select v-model.number="filterSupplier"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:w-44">
              <option :value="null">全部廠商</option>
              <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
            <input v-model="filterSearch" type="text" placeholder="搜尋商品名稱 / SKU"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:flex-1" />
          </div>

          <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-teal-400">
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-800 dark:to-slate-800">
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">SKU</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">名稱</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mobile-hide">分類</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mobile-hide">廠商</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mobile-hide">條碼</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mobile-hide">基本單位</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">單價</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mobile-hide">整箱數</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mobile-hide">整箱價</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mobile-hide">安全庫存</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(product, index) in pagedProducts"
                    :key="product.id"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                    :class="index % 2 === 1 ? 'bg-orange-50/30 dark:bg-gray-800/50' : ''"
                  >
                    <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ product.sku }}</td>
                    <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ product.name }}</td>
                    <td class="px-5 py-3 text-slate-500 dark:text-slate-400 mobile-hide">{{ categoryFullName(product.category) || '—' }}</td>
                    <td class="px-5 py-3 text-slate-500 dark:text-slate-400 mobile-hide">{{ product.supplierName || '—' }}</td>
                    <td class="px-5 py-3 font-mono text-xs text-slate-500 dark:text-slate-400 mobile-hide">{{ barcodeOf(product) || '—' }}</td>
                    <td class="px-5 py-3 text-slate-500 dark:text-slate-400 mobile-hide">{{ product.baseUnit }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ unitPriceOf(product).toFixed(2) }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-500 dark:text-slate-400 mobile-hide">{{ packQtyOf(product) || '—' }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-500 dark:text-slate-400 mobile-hide">{{ packPriceOf(product) ? '$' + packPriceOf(product).toFixed(2) : '—' }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-500 dark:text-slate-400 mobile-hide">{{ product.safetyStock }}</td>
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
            <div class="flex items-center justify-between px-5 py-3 border-t border-slate-200 dark:border-slate-700">
              <span class="text-xs text-slate-500 dark:text-slate-400 leading-tight">
                <span class="block md:inline">共 {{ filteredProducts.length }} 筆</span><span class="hidden md:inline">，</span><span class="block md:inline">第 {{ productPage }}/{{ productTotalPages }} 頁</span>
              </span>
              <div class="flex items-center gap-1">
                <button :disabled="productPage === 1" @click="productPage--"
                  class="px-2.5 py-1.5 text-xs rounded-md disabled:opacity-30 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all">
                  <i class="fa-solid fa-chevron-left"></i>
                </button>
                <span class="text-xs text-slate-500 dark:text-slate-400 px-2">{{ productPage }} / {{ productTotalPages }}</span>
                <button :disabled="productPage >= productTotalPages" @click="productPage++"
                  class="px-2.5 py-1.5 text-xs rounded-md disabled:opacity-30 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all">
                  <i class="fa-solid fa-chevron-right"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Tab 2: Stock Levels -->
      <Transition name="fade" mode="out-in">
        <div v-if="activeTab === 'stock'" key="stock">
          <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200 mb-3">庫存水位</h2>
          <div class="flex flex-col md:flex-row md:items-center gap-2 mb-3">
            <select v-model.number="filterTopCategory" @change="onFilterTopChange"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:w-44">
              <option :value="null">全部大類</option>
              <option v-for="c in topCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
            <select v-model.number="filterSubCategory" :disabled="filterTopCategory === null"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:w-44 disabled:opacity-50">
              <option :value="null">全部子類</option>
              <option v-for="c in childCategoriesOf(filterTopCategory)" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
            <select v-model.number="filterSupplier"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:w-44">
              <option :value="null">全部廠商</option>
              <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
            <input v-model="filterSearch" type="text" placeholder="搜尋商品名稱 / SKU"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:flex-1" />
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
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ Number(batch.unitCost ?? 0).toFixed(2) }}</td>
                    <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ batch.receivedDate }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Tab 3: Inventory Count (盤點) -->
      <Transition name="fade" mode="out-in">
        <div v-if="activeTab === 'count'" key="count">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">庫存盤點</h2>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">輸入實盤數量，系統自動計算差異。橘色高亮表示低於安全庫存。</p>
            </div>
            <button
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-all"
              @click="actualCounts = {}"
            >
              <i class="fa-solid fa-rotate-left"></i> 清除實盤
            </button>
          </div>
          <div class="flex flex-col md:flex-row md:items-center gap-2 mb-3">
            <select v-model.number="filterTopCategory" @change="onFilterTopChange"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:w-44">
              <option :value="null">全部大類</option>
              <option v-for="c in topCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
            <select v-model.number="filterSubCategory" :disabled="filterTopCategory === null"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:w-44 disabled:opacity-50">
              <option :value="null">全部子類</option>
              <option v-for="c in childCategoriesOf(filterTopCategory)" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
            <select v-model.number="filterSupplier"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:w-44">
              <option :value="null">全部廠商</option>
              <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
            <input v-model="filterSearch" type="text" placeholder="搜尋商品名稱 / SKU"
              class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-2 md:flex-1" />
          </div>

          <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-purple-400">
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-gray-800 dark:to-slate-800">
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">商品名稱</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">SKU</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">安全庫存</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">系統庫存</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">實盤數量</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">差異</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">狀態</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(row, index) in countRows"
                    :key="row.id"
                    class="border-b border-slate-100 dark:border-slate-700/50 transition-all"
                    :class="[
                      row.isLow
                        ? 'bg-red-50 dark:bg-red-900/20'
                        : index % 2 === 1 ? 'bg-purple-50/20 dark:bg-gray-800/50' : ''
                    ]"
                  >
                    <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ row.name }}</td>
                    <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ row.sku }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-500 dark:text-slate-400">{{ row.safetyStock }}</td>
                    <td class="px-5 py-3 text-right font-mono" :class="row.isLow ? 'text-red-600 dark:text-red-400 font-bold' : 'text-slate-700 dark:text-stone-200'">
                      {{ row.totalRemaining }}
                      <i v-if="row.isLow" class="fa-solid fa-triangle-exclamation text-red-500 ml-1 text-xs animate-pulse"></i>
                    </td>
                    <td class="px-5 py-3 text-right">
                      <input
                        v-model.number="actualCounts[row.id]"
                        type="number"
                        min="0"
                        class="w-20 text-right rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="—"
                      />
                    </td>
                    <td class="px-5 py-3 text-right font-mono font-semibold">
                      <span v-if="row.variance !== null" :class="row.variance === 0 ? 'text-emerald-600 dark:text-emerald-400' : row.variance > 0 ? 'text-blue-600 dark:text-blue-400' : 'text-red-600 dark:text-red-400'">
                        {{ row.variance > 0 ? '+' : '' }}{{ row.variance }}
                      </span>
                      <span v-else class="text-slate-300 dark:text-slate-600">—</span>
                    </td>
                    <td class="px-5 py-3">
                      <span v-if="row.isLow" class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-900/40 rounded-full">
                        <i class="fa-solid fa-triangle-exclamation"></i> 低庫存
                      </span>
                      <span v-else-if="row.variance !== null && row.variance !== 0" class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full" :class="row.variance > 0 ? 'text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/40' : 'text-orange-700 dark:text-orange-300 bg-orange-100 dark:bg-orange-900/40'">
                        {{ row.variance > 0 ? '盤盈' : '盤虧' }}
                      </span>
                      <span v-else-if="row.variance === 0" class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-900/40 rounded-full">
                        <i class="fa-solid fa-check"></i> 相符
                      </span>
                      <span v-else class="text-slate-400 dark:text-slate-500 text-xs">—</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Tab 4: Purchase Management -->
      <Transition name="fade" mode="out-in">
        <div v-if="activeTab === 'purchase'" key="purchase">
          <div class="flex items-center justify-between mb-4 gap-3">
            <div class="flex items-center gap-2">
              <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">採購管理</h2>
              <select v-model="purchaseStatusFilter" class="text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-2 py-1">
                <option value="all">全部狀態</option>
                <option value="draft">草稿</option>
                <option value="confirmed">已確認</option>
                <option value="received">已到貨</option>
                <option value="cancelled">已取消</option>
              </select>
            </div>
            <button @click="openAddPurchase"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C] rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all duration-300">
              <i class="fa-solid fa-plus text-xs"></i> 新增採購單
            </button>
          </div>

          <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg border-l-4 border-l-blue-400">
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-slate-800">
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">採購單號</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">供應商</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">日期</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">金額合計</th>
                    <th class="text-center px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">狀態</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="filteredPurchases.length === 0">
                    <td colspan="6" class="px-5 py-8 text-center text-sm text-slate-400">尚無採購單</td>
                  </tr>
                  <tr
                    v-for="(po, index) in filteredPurchases"
                    :key="po.id"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-blue-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                    :class="index % 2 === 1 ? 'bg-blue-50/20 dark:bg-gray-800/50' : ''"
                  >
                    <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ po.order_number }}</td>
                    <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ po.supplier }}</td>
                    <td class="px-5 py-3 text-slate-500 dark:text-slate-400">{{ po.date }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">
                      ${{ po.items.reduce((s, i) => s + (Number(i.fee) * Number(i.quantity)), 0).toLocaleString() }}
                    </td>
                    <td class="px-5 py-3 text-center">
                      <span class="inline-flex items-center px-2.5 py-0.5 text-xs font-semibold rounded-full" :class="STATUS_COLORS[po.status]">
                        {{ STATUS_LABELS[po.status] ?? po.status }}
                      </span>
                    </td>
                    <td class="px-5 py-3 text-right">
                      <button v-if="po.status === 'confirmed'" @click="confirmReceive(po.id)"
                        class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 rounded hover:shadow-sm transition-all mr-1">
                        <i class="fa-solid fa-truck-ramp-box"></i> 收貨
                      </button>
                      <button v-if="po.status !== 'received'" @click="openEditPurchase(po)"
                        class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded hover:shadow-sm transition-all mr-1">
                        <i class="fa-solid fa-pen-to-square"></i> 編輯
                      </button>
                      <button v-if="po.status === 'draft'" @click="removePurchase(po.id)"
                        class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-red-400 to-rose-500 hover:from-red-500 hover:to-rose-600 rounded hover:shadow-sm transition-all">
                        <i class="fa-solid fa-trash"></i> 刪除
                      </button>
                      <button @click="exportPurchasePDF(po)"
                        class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 rounded hover:shadow-sm transition-all ml-1">
                        <i class="fa-solid fa-file-pdf"></i> PDF
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Transition>
    </template>

    <!-- Purchase Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showPurchaseModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/40" @click="showPurchaseModal = false"></div>
          <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-2xl mx-4 p-6 max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between mb-5">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-stone-50">
                {{ editingPurchase ? '編輯採購單' : '新增採購單' }}
              </h3>
              <button class="text-slate-400 hover:text-slate-600 dark:hover:text-stone-200" @click="showPurchaseModal = false">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>

            <div class="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">採購單號</label>
                <input v-model="purchaseForm.order_number" type="text" placeholder="留空自動產生"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">供應商</label>
                <select v-model="purchaseForm.supplier"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500">
                  <option value="">-- 選擇供應商 --</option>
                  <option v-for="s in suppliers" :key="s.id" :value="s.name">{{ s.name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">日期</label>
                <input v-model="purchaseForm.date" type="date"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">狀態</label>
                <select v-model="purchaseForm.status"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500">
                  <option value="draft">草稿</option>
                  <option value="confirmed">已確認</option>
                  <option value="cancelled">已取消</option>
                </select>
              </div>
            </div>

            <!-- Items -->
            <div class="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden mb-4">
              <div class="flex items-center justify-between px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
                <span class="text-xs font-semibold text-slate-600 dark:text-slate-300">採購明細</span>
                <button @click="addPurchaseItem" type="button"
                  class="inline-flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400 hover:text-purple-800 transition-colors">
                  <i class="fa-solid fa-plus"></i> 新增明細
                </button>
              </div>
              <!-- Desktop header -->
              <div class="hidden md:grid grid-cols-[1.4fr_1.2fr_0.8fr_0.8fr_40px] gap-3 px-4 py-2 text-xs font-semibold text-slate-500 dark:text-slate-400 bg-slate-50/50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
                <div>商品</div><div>包裝</div><div>數量</div><div>單價</div><div></div>
              </div>
              <div class="divide-y divide-slate-100 dark:divide-slate-700">
                <div v-for="(item, idx) in purchaseForm.items" :key="idx"
                  class="px-4 py-2 flex flex-col gap-2 md:grid md:grid-cols-[1.4fr_1.2fr_0.8fr_0.8fr_40px] md:items-start md:gap-3">
                  <div>
                    <label class="md:hidden text-xs text-slate-500 mb-1 block">商品</label>
                    <select v-model.number="item.product" @change="onPurchaseProductChange(idx)"
                      class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500">
                      <option :value="0" disabled>選擇商品</option>
                      <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }} ({{ p.sku }})</option>
                    </select>
                  </div>
                  <div>
                    <label class="md:hidden text-xs text-slate-500 mb-1 block">包裝</label>
                    <select v-model.number="item.packaging"
                      class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500">
                      <option :value="null" disabled>選擇包裝</option>
                      <option v-for="pk in getProductPackagings(item.product)" :key="pk.id" :value="pk.id">
                        {{ pk.name }} × {{ pk.quantity }}
                      </option>
                    </select>
                  </div>
                  <div class="flex flex-col">
                    <label class="md:hidden text-xs text-slate-500 mb-1 block">數量</label>
                    <input v-model.number="item.quantity" type="number" min="1" placeholder="數量"
                      class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                    <span v-if="item.product && (getProductPackagings(item.product).find(pk => pk.id === item.packaging)?.quantity || 1) > 1" class="text-[10px] text-slate-400 mt-0.5">
                      共 {{ (Number(item.quantity) || 0) * (getProductPackagings(item.product).find(pk => pk.id === item.packaging)?.quantity || 1) }}
                      {{ products.find(p => p.id === item.product)?.baseUnit || '' }}
                    </span>
                  </div>
                  <div>
                    <label class="md:hidden text-xs text-slate-500 mb-1 block">單價</label>
                    <input v-model.number="item.fee" type="number" min="0" step="0.01" placeholder="每包裝單價"
                      title="每包裝單價"
                      class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                  </div>
                  <button @click="removePurchaseItem(idx)" type="button"
                    class="text-red-400 hover:text-red-600 min-w-[40px] min-h-[40px] flex items-center justify-center self-end md:self-auto"
                    :disabled="purchaseForm.items.length <= 1">
                    <i class="fa-solid fa-xmark text-xs"></i>
                  </button>
                </div>
              </div>
            </div>

            <div class="flex justify-between items-center">
              <p class="text-sm text-slate-500 dark:text-slate-400">
                合計：<span class="font-semibold text-slate-700 dark:text-stone-200">
                  ${{ purchaseForm.items.reduce((s, i) => s + (i.fee * i.quantity), 0).toLocaleString() }}
                </span>
              </p>
              <div class="flex gap-3">
                <button class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-all" @click="showPurchaseModal = false">取消</button>
                <button class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 rounded-lg shadow-sm hover:-translate-y-0.5 active:scale-95 transition-all" @click="savePurchase">儲存</button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Product Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showProductModal" class="fixed inset-0 z-50 flex items-center justify-center">
          <div class="absolute inset-0 bg-black/40" @click="showProductModal = false"></div>
          <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-3xl mx-4 p-6 max-h-[90vh] overflow-y-auto modal-enter-active">
            <div class="flex items-center justify-between mb-5">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-stone-50">
                {{ editingProduct ? '編輯商品' : '新增商品' }}
              </h3>
              <button class="text-slate-400 hover:text-slate-600 dark:hover:text-stone-200" @click="showProductModal = false">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>
            <div class="space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">SKU</label>
                  <input v-model="productForm.sku" type="text" placeholder="例如 PF-001"
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">商品名稱</label>
                  <input v-model="productForm.name" type="text" placeholder="商品名稱"
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">廠商</label>
                  <select v-model.number="productForm.supplier"
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500">
                    <option :value="null">-- 無 --</option>
                    <option v-if="suppliers.length === 0" disabled>尚無供應商，請先到供應商管理建立</option>
                    <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">大類</label>
                  <select v-model.number="formTopCategory" @change="onFormTopCategoryChange"
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500">
                    <option :value="null">-- 無 --</option>
                    <option v-for="c in topCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">子類</label>
                  <select v-model.number="productForm.category" :disabled="formTopCategory === null"
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 disabled:opacity-50">
                    <option :value="formTopCategory">（不選子類，使用大類）</option>
                    <option v-for="c in childCategoriesOf(formTopCategory)" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">基本單位</label>
                  <input v-model="productForm.baseUnit" type="text" placeholder="例如 罐、包、個"
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">安全庫存量</label>
                  <input v-model.number="productForm.safetyStock" type="number" min="0" placeholder="0"
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500" />
                </div>
              </div>

              <!-- Packagings -->
              <div class="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
                <div class="flex items-center justify-between px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
                  <span class="text-xs font-semibold text-slate-600 dark:text-slate-300">包裝規格</span>
                  <button @click="addPackagingRow" type="button"
                    class="inline-flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400 hover:text-purple-800">
                    <i class="fa-solid fa-plus"></i> 新增包裝
                  </button>
                </div>
                <!-- Desktop header -->
                <div class="mobile-hide md:grid grid-cols-[1.5fr_0.8fr_1fr_1fr_1.2fr_0.5fr_0.4fr] gap-3 px-4 py-2 text-xs font-semibold text-slate-500 dark:text-slate-400 bg-slate-50/50 dark:bg-slate-800/50">
                  <div>名稱</div><div>含基本單位</div><div>售價</div><div>成本</div><div>條碼</div><div>預設</div><div></div>
                </div>
                <div class="divide-y divide-slate-100 dark:divide-slate-700">
                  <div v-for="(pkg, idx) in productForm.packagings" :key="idx"
                    class="px-4 py-3 flex flex-col gap-2 md:grid md:grid-cols-[1.5fr_0.8fr_1fr_1fr_1.2fr_0.5fr_0.4fr] md:items-center md:gap-3">
                    <div>
                      <label class="md:hidden text-xs text-slate-500 mb-1 block">名稱</label>
                      <input v-model="pkg.name" type="text" placeholder="例如 單罐、整箱(24)"
                        class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                    </div>
                    <div>
                      <label class="md:hidden text-xs text-slate-500 mb-1 block">含基本單位數量</label>
                      <input v-model.number="pkg.quantity" type="number" min="1" placeholder="1"
                        class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                    </div>
                    <div>
                      <label class="md:hidden text-xs text-slate-500 mb-1 block">售價</label>
                      <input v-model.number="pkg.price" type="number" min="0" step="0.01" placeholder="0.00"
                        class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                    </div>
                    <div>
                      <label class="md:hidden text-xs text-slate-500 mb-1 block">成本</label>
                      <input v-model.number="pkg.cost" type="number" min="0" step="0.01" placeholder="0.00"
                        class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                    </div>
                    <div>
                      <label class="md:hidden text-xs text-slate-500 mb-1 block">條碼</label>
                      <input v-model="pkg.barcode" type="text" placeholder="條碼(選填)"
                        class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                    </div>
                    <div class="flex md:block items-center justify-between">
                      <label class="md:hidden text-xs text-slate-500">預設</label>
                      <label class="inline-flex items-center gap-1 text-xs text-slate-600 dark:text-slate-300 md:justify-center">
                        <input type="radio" name="default-pkg" :checked="pkg.is_default" @change="setDefaultPackaging(idx)" />
                        <span class="md:inline hidden">預設</span>
                      </label>
                    </div>
                    <button @click="removePackagingRow(idx)" type="button"
                      class="text-red-400 hover:text-red-600 min-w-[40px] min-h-[40px] flex items-center justify-center self-end md:self-auto">
                      <i class="fa-solid fa-xmark text-xs"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg active:scale-95 transition-all" @click="showProductModal = false">
                取消
              </button>
              <button class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C] rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all" @click="saveProduct">
                儲存
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Bulk Import Modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showBulkModal" class="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4">
          <div class="absolute inset-0 bg-black/50" @click="closeBulkModal"></div>
          <div class="relative bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
            <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
              <h3 class="text-lg font-semibold text-slate-800 dark:text-stone-100">
                批次新增商品
                <span class="ml-2 text-xs text-slate-500">步驟 {{ bulkStep }} / 2</span>
              </h3>
              <button class="text-slate-400 hover:text-slate-600 dark:hover:text-stone-200 min-h-[40px] min-w-[40px]" @click="closeBulkModal">
                <i class="fa-solid fa-xmark text-lg"></i>
              </button>
            </div>

            <!-- Step 1 -->
            <div v-if="bulkStep === 1" class="p-6 overflow-y-auto space-y-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">供應商 <span class="text-red-500">*</span></label>
                <select
                  v-model="bulkSupplier"
                  class="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-stone-200"
                >
                  <option :value="null" disabled>請選擇供應商</option>
                  <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
                </select>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">大類（可選）</label>
                  <select v-model.number="bulkTopCategory" @change="onBulkTopCategoryChange"
                    class="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-stone-200">
                    <option :value="null">-- 無 --</option>
                    <option v-for="c in topCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">子類（可選）</label>
                  <select v-model.number="bulkCategory" :disabled="bulkTopCategory === null"
                    class="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-stone-200 disabled:opacity-50">
                    <option :value="bulkTopCategory">（不選子類，使用大類）</option>
                    <option v-for="c in childCategoriesOf(bulkTopCategory)" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>
              </div>

              <div class="flex gap-2 border-b border-slate-200 dark:border-slate-700">
                <button
                  class="px-4 py-2 text-sm font-medium border-b-2 transition-colors"
                  :class="bulkMode === 'xlsx' ? 'border-purple-500 text-purple-600 dark:text-purple-400' : 'border-transparent text-slate-500'"
                  @click="bulkMode = 'xlsx'"
                >
                  從 Excel 匯入
                </button>
                <button
                  class="px-4 py-2 text-sm font-medium border-b-2 transition-colors"
                  :class="bulkMode === 'manual' ? 'border-purple-500 text-purple-600 dark:text-purple-400' : 'border-transparent text-slate-500'"
                  @click="bulkMode = 'manual'"
                >
                  手動輸入
                </button>
              </div>

              <div v-if="bulkMode === 'xlsx'" class="space-y-3">
                <p class="text-sm text-slate-600 dark:text-slate-400">選擇 .xlsx 檔案，系統將自動解析商品列表。</p>
                <input
                  ref="bulkFileInput"
                  type="file"
                  accept=".xlsx"
                  :disabled="!bulkSupplier || bulkLoading"
                  class="block w-full text-sm text-slate-700 dark:text-stone-200 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100 dark:file:bg-slate-700 dark:file:text-stone-200"
                  @change="onBulkFileChange"
                />
                <p v-if="bulkLoading" class="text-sm text-slate-500">解析中...</p>
              </div>

              <div v-else class="space-y-3">
                <p class="text-sm text-slate-600 dark:text-slate-400">建立空白預覽表，手動輸入商品資料。</p>
                <button
                  class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 rounded-lg hover:shadow-md active:scale-95 transition-all"
                  :disabled="!bulkSupplier"
                  @click="goManualStep2"
                >
                  下一步：手動輸入
                </button>
              </div>
            </div>

            <!-- Step 2 -->
            <div v-if="bulkStep === 2" class="p-4 sm:p-6 overflow-y-auto flex-1 space-y-3">
              <div v-if="bulkSheetNames.length > 1" class="flex flex-col md:flex-row md:items-center gap-2 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700 rounded-lg p-3">
                <span class="text-sm font-medium text-purple-800 dark:text-purple-200">選擇工作表：</span>
                <select v-model="bulkSelectedSheet" @change="onBulkSheetChange" :disabled="bulkLoading"
                  class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-1.5 md:flex-1">
                  <option v-for="s in bulkSheetNames" :key="s" :value="s">{{ s }}</option>
                </select>
                <span v-if="bulkLoading" class="text-xs text-slate-500">解析中…</span>
              </div>
              <div v-if="bulkWarnings.length > 0" class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-3 text-sm text-yellow-800 dark:text-yellow-200">
                <div class="font-semibold mb-1">解析警告</div>
                <ul class="list-disc list-inside space-y-0.5">
                  <li v-for="(w, i) in bulkWarnings" :key="i">{{ w }}</li>
                </ul>
              </div>

              <div class="flex flex-wrap items-center gap-2 justify-between">
                <div class="text-sm text-slate-600 dark:text-slate-300">
                  共 <strong>{{ bulkRows.length }}</strong> 筆
                  <span v-if="bulkInvalidCount > 0" class="text-red-500 ml-2">{{ bulkInvalidCount }} 筆不符合</span>
                </div>
                <div class="flex gap-2">
                  <button class="px-3 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-slate-200 active:scale-95 transition-all" @click="addBulkRow">
                    <i class="fa-solid fa-plus text-xs"></i> 新增一列
                  </button>
                  <button class="px-3 py-2 text-sm font-medium text-red-600 bg-red-50 dark:bg-red-900/20 rounded-lg hover:bg-red-100 active:scale-95 transition-all" @click="clearBulkRows">
                    全部清空
                  </button>
                </div>
              </div>

              <div class="overflow-x-auto border border-slate-200 dark:border-slate-700 rounded-lg">
                <table class="w-full text-xs">
                  <thead class="bg-slate-50 dark:bg-slate-800 sticky top-0">
                    <tr>
                      <th class="px-2 py-2 text-left font-semibold text-slate-600 dark:text-slate-300">SKU *</th>
                      <th class="px-2 py-2 text-left font-semibold text-slate-600 dark:text-slate-300 min-w-[200px]">名稱 *</th>
                      <th class="px-2 py-2 text-left font-semibold text-slate-600 dark:text-slate-300">條碼</th>
                      <th class="px-2 py-2 text-left font-semibold text-slate-600 dark:text-slate-300">基本單位</th>
                      <th class="px-2 py-2 text-right font-semibold text-slate-600 dark:text-slate-300">單價</th>
                      <th class="px-2 py-2 text-right font-semibold text-slate-600 dark:text-slate-300">整箱數</th>
                      <th class="px-2 py-2 text-right font-semibold text-slate-600 dark:text-slate-300">整箱價</th>
                      <th class="px-2 py-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(row, idx) in bulkRows"
                      :key="idx"
                      class="border-t border-slate-100 dark:border-slate-700"
                      :class="(!row.sku.trim() || !row.name.trim() || rowIsDuplicate(row)) ? 'bg-red-50 dark:bg-red-900/10' : ''"
                    >
                      <td class="px-1 py-1"><input v-model="row.sku" class="w-24 px-2 py-1 rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-stone-200" /></td>
                      <td class="px-1 py-1"><input v-model="row.name" class="w-full px-2 py-1 rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-stone-200" /></td>
                      <td class="px-1 py-1"><input v-model="row.barcode" class="w-32 px-2 py-1 rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-stone-200" /></td>
                      <td class="px-1 py-1"><input v-model="row.baseUnit" class="w-16 px-2 py-1 rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-stone-200" /></td>
                      <td class="px-1 py-1"><input v-model.number="row.unitPrice" type="number" step="0.01" @input="row.packPrice = (Number(row.unitPrice)||0) * (Number(row.packQty)||0)" class="w-20 px-2 py-1 text-right rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-stone-200" /></td>
                      <td class="px-1 py-1"><input v-model.number="row.packQty" type="number" @input="row.packPrice = (Number(row.unitPrice)||0) * (Number(row.packQty)||0)" class="w-16 px-2 py-1 text-right rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-stone-200" /></td>
                      <td class="px-1 py-1"><input v-model.number="row.packPrice" type="number" step="0.01" class="w-24 px-2 py-1 text-right rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-stone-200" /></td>
                      <td class="px-1 py-1 text-center">
                        <button class="inline-flex items-center justify-center w-10 h-10 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded active:scale-95 transition-all" @click="removeBulkRow(idx)">
                          <i class="fa-solid fa-trash"></i>
                        </button>
                      </td>
                    </tr>
                    <tr v-if="bulkRows.length === 0">
                      <td colspan="8" class="px-4 py-8 text-center text-slate-400">尚無資料</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div v-if="bulkSkipped.length > 0" class="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-700 rounded-lg p-3 text-sm text-orange-800 dark:text-orange-200">
                <div class="font-semibold mb-1">跳過的項目</div>
                <ul class="list-disc list-inside space-y-0.5 max-h-32 overflow-y-auto">
                  <li v-for="(s, i) in bulkSkipped" :key="i">#{{ s.index + 1 }} {{ s.sku }} — {{ s.reason }}</li>
                </ul>
              </div>
            </div>

            <div class="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between gap-2">
              <button
                v-if="bulkStep === 2"
                class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg active:scale-95 transition-all"
                @click="bulkStep = 1"
              >
                <i class="fa-solid fa-arrow-left text-xs"></i> 返回
              </button>
              <div v-else></div>
              <div class="flex gap-2">
                <button class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg active:scale-95 transition-all" @click="closeBulkModal">
                  取消
                </button>
                <button
                  v-if="bulkStep === 2"
                  :disabled="bulkLoading || bulkRows.length === 0"
                  class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 rounded-lg shadow-sm hover:shadow-md active:scale-95 transition-all disabled:opacity-50"
                  @click="confirmBulkImport"
                >
                  <i class="fa-solid fa-check text-xs"></i> 確認新增
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Category Management Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showCategoryModal" class="fixed inset-0 z-50 flex items-center justify-center">
          <div class="absolute inset-0 bg-black/40"></div>
          <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] flex flex-col modal-enter-active">
            <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-stone-50">分類管理</h3>
              <button class="text-slate-400 hover:text-slate-600 dark:hover:text-stone-200" @click="showCategoryModal = false">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>
            <div class="p-6 overflow-y-auto space-y-4 flex-1">
              <!-- Add new top -->
              <div class="flex gap-2">
                <input v-model="newTopName" type="text" placeholder="新增大類名稱"
                  class="flex-1 px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200" />
                <button @click="addTopCategory"
                  class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 rounded-lg active:scale-95 transition-all min-w-[40px] min-h-[40px]">
                  <i class="fa-solid fa-plus"></i> 新增大類
                </button>
              </div>

              <!-- Tree -->
              <div class="space-y-3">
                <div v-for="top in topCategories" :key="top.id" class="border border-slate-200 dark:border-slate-700 rounded-lg p-3">
                  <div class="flex items-center gap-2">
                    <i class="fa-solid fa-folder text-amber-500"></i>
                    <template v-if="editingCategoryId === top.id">
                      <input v-model="editingCategoryName" type="text"
                        class="flex-1 px-2 py-1 text-sm rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200" />
                      <button @click="saveEditCategory" class="text-emerald-600 hover:text-emerald-800 min-w-[40px] min-h-[40px]">
                        <i class="fa-solid fa-check"></i>
                      </button>
                      <button @click="editingCategoryId = null" class="text-slate-400 hover:text-slate-600 min-w-[40px] min-h-[40px]">
                        <i class="fa-solid fa-xmark"></i>
                      </button>
                    </template>
                    <template v-else>
                      <span class="flex-1 font-medium text-slate-700 dark:text-stone-200">{{ top.name }}</span>
                      <button @click="startEditCategory(top)" class="text-blue-500 hover:text-blue-700 min-w-[40px] min-h-[40px]">
                        <i class="fa-solid fa-pen-to-square"></i>
                      </button>
                      <button @click="removeCategory(top.id)" class="text-red-500 hover:text-red-700 min-w-[40px] min-h-[40px]">
                        <i class="fa-solid fa-trash"></i>
                      </button>
                    </template>
                  </div>
                  <!-- Children -->
                  <div class="mt-2 ml-6 space-y-1">
                    <div v-for="child in childCategoriesOf(top.id)" :key="child.id" class="flex items-center gap-2 text-sm">
                      <i class="fa-solid fa-angle-right text-slate-400"></i>
                      <template v-if="editingCategoryId === child.id">
                        <input v-model="editingCategoryName" type="text"
                          class="flex-1 px-2 py-1 text-xs rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200" />
                        <button @click="saveEditCategory" class="text-emerald-600 hover:text-emerald-800 min-w-[40px] min-h-[40px]">
                          <i class="fa-solid fa-check"></i>
                        </button>
                        <button @click="editingCategoryId = null" class="text-slate-400 hover:text-slate-600 min-w-[40px] min-h-[40px]">
                          <i class="fa-solid fa-xmark"></i>
                        </button>
                      </template>
                      <template v-else>
                        <span class="flex-1 text-slate-600 dark:text-slate-300">{{ child.name }}</span>
                        <button @click="startEditCategory(child)" class="text-blue-500 hover:text-blue-700 min-w-[40px] min-h-[40px]">
                          <i class="fa-solid fa-pen-to-square text-xs"></i>
                        </button>
                        <button @click="removeCategory(child.id)" class="text-red-500 hover:text-red-700 min-w-[40px] min-h-[40px]">
                          <i class="fa-solid fa-trash text-xs"></i>
                        </button>
                      </template>
                    </div>
                    <!-- Add child inline -->
                    <div class="flex gap-2 mt-1">
                      <input v-model="newChildName[top.id]" type="text" placeholder="新增子類"
                        class="flex-1 px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200" />
                      <button @click="addChildCategory(top.id)"
                        class="px-3 py-1 text-xs font-medium text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded min-w-[40px] min-h-[40px]">
                        <i class="fa-solid fa-plus"></i>
                      </button>
                    </div>
                  </div>
                </div>
                <div v-if="topCategories.length === 0" class="text-center text-sm text-slate-400 py-6">尚無分類，請先新增大類</div>
              </div>
            </div>
            <div class="flex items-center justify-end px-6 py-3 border-t border-slate-200 dark:border-slate-700">
              <button @click="showCategoryModal = false"
                class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg">關閉</button>
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
