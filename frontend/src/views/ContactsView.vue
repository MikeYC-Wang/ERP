<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  getSuppliers, createSupplier, updateSupplier, deleteSupplier,
} from '@/api/suppliers'
import {
  getCustomers, createCustomer, updateCustomer, deleteCustomer,
} from '@/api/customers'

const loading = ref(false)
const activeTab = ref<'suppliers' | 'customers'>('suppliers')

// ─── Shared contact form shape ───
interface Contact {
  id: number
  name: string
  contact_name: string
  phone: string
  email: string
  address: string
}

const emptyForm = (): Omit<Contact, 'id'> => ({ name: '', contact_name: '', phone: '', email: '', address: '' })

// ─── Suppliers ───
const suppliers = ref<Contact[]>([])
const supplierSearch = ref('')
const showSupplierModal = ref(false)
const editingSupplier = ref<Contact | null>(null)
const supplierForm = ref(emptyForm())

const filteredSuppliers = computed(() =>
  supplierSearch.value
    ? suppliers.value.filter(s => s.name.includes(supplierSearch.value) || s.contact_name.includes(supplierSearch.value))
    : suppliers.value
)

function openAddSupplier() {
  editingSupplier.value = null
  supplierForm.value = emptyForm()
  showSupplierModal.value = true
}

function openEditSupplier(s: Contact) {
  editingSupplier.value = s
  supplierForm.value = { name: s.name, contact_name: s.contact_name, phone: s.phone, email: s.email, address: s.address }
  showSupplierModal.value = true
}

async function saveSupplier() {
  if (editingSupplier.value) {
    const res = await updateSupplier(editingSupplier.value.id, supplierForm.value)
    const idx = suppliers.value.findIndex(s => s.id === editingSupplier.value!.id)
    if (idx !== -1) suppliers.value[idx] = res.data
  } else {
    const res = await createSupplier(supplierForm.value)
    suppliers.value.push(res.data)
  }
  showSupplierModal.value = false
}

async function removeSupplier(id: number) {
  if (!confirm('確定要刪除此供應商？')) return
  await deleteSupplier(id)
  suppliers.value = suppliers.value.filter(s => s.id !== id)
}

// ─── Customers ───
const customers = ref<Contact[]>([])
const customerSearch = ref('')
const showCustomerModal = ref(false)
const editingCustomer = ref<Contact | null>(null)
const customerForm = ref(emptyForm())

const filteredCustomers = computed(() =>
  customerSearch.value
    ? customers.value.filter(c => c.name.includes(customerSearch.value) || c.contact_name.includes(customerSearch.value))
    : customers.value
)

function openAddCustomer() {
  editingCustomer.value = null
  customerForm.value = emptyForm()
  showCustomerModal.value = true
}

function openEditCustomer(c: Contact) {
  editingCustomer.value = c
  customerForm.value = { name: c.name, contact_name: c.contact_name, phone: c.phone, email: c.email, address: c.address }
  showCustomerModal.value = true
}

async function saveCustomer() {
  if (editingCustomer.value) {
    const res = await updateCustomer(editingCustomer.value.id, customerForm.value)
    const idx = customers.value.findIndex(c => c.id === editingCustomer.value!.id)
    if (idx !== -1) customers.value[idx] = res.data
  } else {
    const res = await createCustomer(customerForm.value)
    customers.value.push(res.data)
  }
  showCustomerModal.value = false
}

async function removeCustomer(id: number) {
  if (!confirm('確定要刪除此客戶？')) return
  await deleteCustomer(id)
  customers.value = customers.value.filter(c => c.id !== id)
}

// ─── Load ───
onMounted(async () => {
  loading.value = true
  try {
    const [sRes, cRes] = await Promise.all([
      getSuppliers({ page_size: 1000 }).catch(() => null),
      getCustomers({ page_size: 1000 }).catch(() => null),
    ])
    if (sRes?.data) suppliers.value = Array.isArray(sRes.data) ? sRes.data : sRes.data?.results ?? []
    if (cRes?.data) customers.value = Array.isArray(cRes.data) ? cRes.data : cRes.data?.results ?? []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6 animate-fade-in-up">
    <!-- Header -->
    <div class="flex items-center gap-2">
      <i class="fa-solid fa-address-book text-amber-500"></i>
      <h1 class="text-xl font-bold text-slate-900 dark:text-stone-50">聯絡人管理</h1>
    </div>

    <!-- Tabs -->
    <div class="border-b border-slate-200 dark:border-slate-700">
      <nav class="flex gap-2">
        <button
          v-for="tab in ([
            { key: 'suppliers', label: '供應商', icon: 'fa-solid fa-truck' },
            { key: 'customers', label: '客戶', icon: 'fa-solid fa-users' },
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
          <span class="text-xs opacity-70">({{ tab.key === 'suppliers' ? suppliers.length : customers.length }})</span>
        </button>
      </nav>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <i class="fa-solid fa-spinner fa-spin text-2xl text-amber-500"></i>
    </div>

    <template v-else>
      <!-- ── Suppliers Tab ── -->
      <Transition name="fade" mode="out-in">
        <div v-if="activeTab === 'suppliers'" key="suppliers">
          <div class="flex items-center justify-between mb-4 gap-3">
            <div class="relative flex-1 max-w-xs">
              <i class="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
              <input v-model="supplierSearch" type="text" placeholder="搜尋供應商…"
                class="w-full pl-8 pr-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 focus:outline-none focus:ring-2 focus:ring-purple-400" />
            </div>
            <button @click="openAddSupplier"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C] rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all">
              <i class="fa-solid fa-plus text-xs"></i> 新增供應商
            </button>
          </div>

          <ContactTable :items="filteredSuppliers" entity="供應商" @edit="openEditSupplier" @remove="removeSupplier" />
        </div>
      </Transition>

      <!-- ── Customers Tab ── -->
      <Transition name="fade" mode="out-in">
        <div v-if="activeTab === 'customers'" key="customers">
          <div class="flex items-center justify-between mb-4 gap-3">
            <div class="relative flex-1 max-w-xs">
              <i class="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
              <input v-model="customerSearch" type="text" placeholder="搜尋客戶…"
                class="w-full pl-8 pr-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 focus:outline-none focus:ring-2 focus:ring-purple-400" />
            </div>
            <button @click="openAddCustomer"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C] rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all">
              <i class="fa-solid fa-plus text-xs"></i> 新增客戶
            </button>
          </div>

          <ContactTable :items="filteredCustomers" entity="客戶" @edit="openEditCustomer" @remove="removeCustomer" />
        </div>
      </Transition>
    </template>

    <!-- ── Supplier Modal ── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showSupplierModal" class="fixed inset-0 z-50 flex items-center justify-center">
          <div class="absolute inset-0 bg-black/40" @click="showSupplierModal = false"></div>
          <ContactForm
            :form="supplierForm"
            :title="editingSupplier ? '編輯供應商' : '新增供應商'"
            @save="saveSupplier"
            @cancel="showSupplierModal = false"
          />
        </div>
      </Transition>
    </Teleport>

    <!-- ── Customer Modal ── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showCustomerModal" class="fixed inset-0 z-50 flex items-center justify-center">
          <div class="absolute inset-0 bg-black/40" @click="showCustomerModal = false"></div>
          <ContactForm
            :form="customerForm"
            :title="editingCustomer ? '編輯客戶' : '新增客戶'"
            @save="saveCustomer"
            @cancel="showCustomerModal = false"
          />
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<!-- ── Inline sub-components ── -->
<script lang="ts">
import { defineComponent, h } from 'vue'
import type { PropType } from 'vue'

interface Contact { id: number; name: string; contact_name: string; phone: string; email: string; address: string }

// Table component
const ContactTable = defineComponent({
  name: 'ContactTable',
  props: {
    items: { type: Array as PropType<Contact[]>, required: true },
    entity: { type: String, required: true },
  },
  emits: ['edit', 'remove'],
  setup(props, { emit }) {
    return () => h('div', { class: 'bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden hover:shadow-lg transition-all border-l-4 border-l-purple-400' }, [
      h('div', { class: 'overflow-x-auto' }, [
        h('table', { class: 'w-full text-sm' }, [
          h('thead', {}, [
            h('tr', { class: 'border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-purple-50 to-violet-50 dark:from-gray-800 dark:to-slate-800' }, [
              ['名稱', '聯絡人', '電話', 'Email', '地址', '操作'].map(th =>
                h('th', { class: `text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 ${th === '操作' ? 'text-right' : ''}` }, th)
              ),
            ]),
          ]),
          h('tbody', {}, props.items.length === 0
            ? [h('tr', {}, [h('td', { colspan: 6, class: 'px-5 py-8 text-center text-sm text-slate-400' }, `尚無${props.entity}資料`)])]
            : props.items.map((item, idx) =>
                h('tr', { key: item.id, class: `border-b border-slate-100 dark:border-slate-700/50 hover:bg-purple-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all ${idx % 2 === 1 ? 'bg-purple-50/20 dark:bg-gray-800/50' : ''}` }, [
                  h('td', { class: 'px-5 py-3 font-medium text-slate-700 dark:text-stone-200' }, item.name),
                  h('td', { class: 'px-5 py-3 text-slate-500 dark:text-slate-400' }, item.contact_name || '—'),
                  h('td', { class: 'px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300' }, item.phone || '—'),
                  h('td', { class: 'px-5 py-3 text-xs text-slate-600 dark:text-slate-300' }, item.email || '—'),
                  h('td', { class: 'px-5 py-3 text-xs text-slate-500 dark:text-slate-400 max-w-xs truncate' }, item.address || '—'),
                  h('td', { class: 'px-5 py-3 text-right' }, [
                    h('button', { class: 'inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded hover:shadow-sm transition-all mr-2', onClick: () => emit('edit', item) }, [h('i', { class: 'fa-solid fa-pen-to-square' }), ' 編輯']),
                    h('button', { class: 'inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-red-400 to-rose-500 hover:from-red-500 hover:to-rose-600 rounded hover:shadow-sm transition-all', onClick: () => emit('remove', item.id) }, [h('i', { class: 'fa-solid fa-trash' }), ' 刪除']),
                  ]),
                ])
              )
          ),
        ]),
      ]),
    ])
  },
})

// Form component
const ContactForm = defineComponent({
  name: 'ContactForm',
  props: {
    form: { type: Object as PropType<Omit<Contact, 'id'>>, required: true },
    title: { type: String, required: true },
  },
  emits: ['save', 'cancel'],
  setup(props, { emit }) {
    const fields: { key: keyof Omit<Contact, 'id'>; label: string; type?: string }[] = [
      { key: 'name', label: '名稱' },
      { key: 'contact_name', label: '聯絡人' },
      { key: 'phone', label: '電話' },
      { key: 'email', label: 'Email', type: 'email' },
      { key: 'address', label: '地址' },
    ]
    return () => h('div', { class: 'relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md mx-4 p-6' }, [
      h('div', { class: 'flex items-center justify-between mb-5' }, [
        h('h3', { class: 'text-lg font-semibold text-slate-900 dark:text-stone-50' }, props.title),
        h('button', { class: 'text-slate-400 hover:text-slate-600', onClick: () => emit('cancel') }, [h('i', { class: 'fa-solid fa-xmark' })]),
      ]),
      h('div', { class: 'space-y-3' }, fields.map(f =>
        h('div', {}, [
          h('label', { class: 'block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1' }, f.label),
          h('input', {
            value: props.form[f.key],
            onInput: (e: Event) => { (props.form as Record<string, string>)[f.key] = (e.target as HTMLInputElement).value },
            type: f.type ?? 'text',
            class: 'w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500',
          }),
        ])
      )),
      h('div', { class: 'flex justify-end gap-3 mt-5' }, [
        h('button', { class: 'px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-all', onClick: () => emit('cancel') }, '取消'),
        h('button', { class: 'px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 rounded-lg shadow-sm hover:-translate-y-0.5 active:scale-95 transition-all', onClick: () => emit('save') }, '儲存'),
      ]),
    ])
  },
})

export { ContactTable, ContactForm }
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
