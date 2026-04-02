<script setup lang="ts">
import { ref, computed } from 'vue'

// ─── Tab State ───
const activeTab = ref<'subjects' | 'journal' | 'reports'>('subjects')

// ─── Tab 1: Account Subjects ───
interface AccountSubject {
  id: number
  code: string
  name: string
  category: string
}

const categories = ['Assets', 'Liabilities', 'Equity', 'Revenue', 'Operating Expenses'] as const

const subjects = ref<AccountSubject[]>([
  { id: 1, code: '1001', name: 'Merchandise Inventory', category: 'Assets' },
  { id: 2, code: '1002', name: 'Accounts Receivable', category: 'Assets' },
  { id: 3, code: '2001', name: 'Accounts Payable', category: 'Liabilities' },
  { id: 4, code: '4001', name: 'Sales Revenue', category: 'Revenue' },
  { id: 5, code: '5001', name: 'Rent Expense', category: 'Operating Expenses' },
])

const showSubjectModal = ref(false)
const editingSubject = ref<AccountSubject | null>(null)
const subjectForm = ref({ code: '', name: '', category: 'Assets' })

function openAddSubject() {
  editingSubject.value = null
  subjectForm.value = { code: '', name: '', category: 'Assets' }
  showSubjectModal.value = true
}

function openEditSubject(subject: AccountSubject) {
  editingSubject.value = subject
  subjectForm.value = { code: subject.code, name: subject.name, category: subject.category }
  showSubjectModal.value = true
}

function saveSubject() {
  if (editingSubject.value) {
    const idx = subjects.value.findIndex((s) => s.id === editingSubject.value!.id)
    if (idx !== -1) {
      subjects.value[idx] = { ...subjects.value[idx], ...subjectForm.value }
    }
  } else {
    const newId = Math.max(...subjects.value.map((s) => s.id), 0) + 1
    subjects.value.push({ id: newId, ...subjectForm.value })
  }
  showSubjectModal.value = false
}

function deleteSubject(id: number) {
  subjects.value = subjects.value.filter((s) => s.id !== id)
}

// ─── Tab 2: Journal Vouchers ───
interface VoucherEntry {
  accountSubject: string
  debitAmount: number
  creditAmount: number
}

interface JournalVoucher {
  id: number
  date: string
  voucherNumber: string
  description: string
  isSystemGenerated: boolean
  entries: VoucherEntry[]
}

const currentYear = new Date().getFullYear()
const recentYears = [currentYear - 2, currentYear - 1, currentYear]
const selectedJournalYear = ref(currentYear)

const vouchers = ref<JournalVoucher[]>([
  {
    id: 1,
    date: '2026-03-15',
    voucherNumber: 'JV-2026-001',
    description: 'Monthly rent payment',
    isSystemGenerated: false,
    entries: [
      { accountSubject: '5001', debitAmount: 2500, creditAmount: 0 },
      { accountSubject: '1001', debitAmount: 0, creditAmount: 2500 },
    ],
  },
  {
    id: 2,
    date: '2026-03-20',
    voucherNumber: 'JV-2026-002',
    description: 'Sales revenue recognition',
    isSystemGenerated: true,
    entries: [
      { accountSubject: '1002', debitAmount: 8500, creditAmount: 0 },
      { accountSubject: '4001', debitAmount: 0, creditAmount: 8500 },
    ],
  },
  {
    id: 3,
    date: '2026-03-25',
    voucherNumber: 'JV-2026-003',
    description: 'Inventory purchase',
    isSystemGenerated: true,
    entries: [
      { accountSubject: '1001', debitAmount: 12000, creditAmount: 0 },
      { accountSubject: '2001', debitAmount: 0, creditAmount: 12000 },
    ],
  },
])

const filteredVouchers = computed(() => {
  return vouchers.value.filter((v) => v.date.startsWith(String(selectedJournalYear.value)))
})

const showVoucherModal = ref(false)
const voucherForm = ref({
  date: '',
  description: '',
  entries: [
    { accountSubject: '', debitAmount: 0, creditAmount: 0 },
    { accountSubject: '', debitAmount: 0, creditAmount: 0 },
  ] as VoucherEntry[],
})

function openAddVoucher() {
  voucherForm.value = {
    date: '',
    description: '',
    entries: [
      { accountSubject: '', debitAmount: 0, creditAmount: 0 },
      { accountSubject: '', debitAmount: 0, creditAmount: 0 },
    ],
  }
  showVoucherModal.value = true
}

function addVoucherEntry() {
  voucherForm.value.entries.push({ accountSubject: '', debitAmount: 0, creditAmount: 0 })
}

function removeVoucherEntry(index: number) {
  if (voucherForm.value.entries.length > 2) {
    voucherForm.value.entries.splice(index, 1)
  }
}

const totalDebit = computed(() =>
  voucherForm.value.entries.reduce((sum, e) => sum + Number(e.debitAmount || 0), 0),
)
const totalCredit = computed(() =>
  voucherForm.value.entries.reduce((sum, e) => sum + Number(e.creditAmount || 0), 0),
)
const isBalanced = computed(() => totalDebit.value === totalCredit.value && totalDebit.value > 0)

function saveVoucher() {
  if (!isBalanced.value) return
  const newId = Math.max(...vouchers.value.map((v) => v.id), 0) + 1
  vouchers.value.push({
    id: newId,
    date: voucherForm.value.date,
    voucherNumber: `JV-${voucherForm.value.date.substring(0, 4)}-${String(newId).padStart(3, '0')}`,
    description: voucherForm.value.description,
    isSystemGenerated: false,
    entries: [...voucherForm.value.entries],
  })
  showVoucherModal.value = false
}

// ─── Tab 3: Financial Reports ───
const activeReport = ref<'trial' | 'income' | 'balance'>('trial')
const selectedReportYear = ref(currentYear)

const trialBalanceData = [
  { name: 'Merchandise Inventory', debit: 45000, credit: 0 },
  { name: 'Accounts Receivable', debit: 18500, credit: 0 },
  { name: 'Accounts Payable', debit: 0, credit: 12000 },
  { name: 'Sales Revenue', debit: 0, credit: 128430 },
  { name: 'Rent Expense', debit: 30000, credit: 0 },
  { name: 'Owner Equity', debit: 0, credit: 53070 },
]

const incomeStatementData = {
  revenue: [
    { name: 'Sales Revenue', amount: 128430 },
    { name: 'Service Revenue', amount: 15200 },
  ],
  expenses: [
    { name: 'Cost of Goods Sold', amount: 84210 },
    { name: 'Rent Expense', amount: 30000 },
    { name: 'Utilities Expense', amount: 4800 },
    { name: 'Salary Expense', amount: 12000 },
  ],
}

const incomeTotal = computed(
  () => incomeStatementData.revenue.reduce((s, r) => s + r.amount, 0),
)
const expenseTotal = computed(
  () => incomeStatementData.expenses.reduce((s, e) => s + e.amount, 0),
)
const netIncome = computed(() => incomeTotal.value - expenseTotal.value)

const balanceSheetData = {
  assets: [
    { name: 'Cash', amount: 32000 },
    { name: 'Merchandise Inventory', amount: 45000 },
    { name: 'Accounts Receivable', amount: 18500 },
  ],
  liabilities: [
    { name: 'Accounts Payable', amount: 12000 },
    { name: 'Notes Payable', amount: 25000 },
  ],
  equity: [
    { name: 'Owner Capital', amount: 40000 },
    { name: 'Retained Earnings', amount: 18500 },
  ],
}

const totalAssets = computed(
  () => balanceSheetData.assets.reduce((s, a) => s + a.amount, 0),
)
const totalLiabilities = computed(
  () => balanceSheetData.liabilities.reduce((s, l) => s + l.amount, 0),
)
const totalEquity = computed(
  () => balanceSheetData.equity.reduce((s, e) => s + e.amount, 0),
)
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center gap-2">
      <i class="fa-solid fa-file-invoice-dollar text-amber-500"></i>
      <h1 class="text-xl font-bold text-slate-900 dark:text-stone-50">Accounting</h1>
    </div>

    <!-- Tabs -->
    <div class="border-b border-slate-200 dark:border-slate-700">
      <nav class="flex gap-4">
        <button
          v-for="tab in ([
            { key: 'subjects', label: 'Account Subjects', icon: 'fa-solid fa-list-ol' },
            { key: 'journal', label: 'Journal Vouchers', icon: 'fa-solid fa-book' },
            { key: 'reports', label: 'Financial Reports', icon: 'fa-solid fa-chart-pie' },
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

    <!-- ═══════ Tab 1: Account Subjects ═══════ -->
    <div v-if="activeTab === 'subjects'">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">Account Subjects</h2>
        <button
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-500 hover:bg-amber-600 rounded-lg shadow-sm transition-colors"
          @click="openAddSubject"
        >
          <i class="fa-solid fa-plus text-xs"></i>
          Add Subject
        </button>
      </div>

      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700">
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Code</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Name</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Category</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(subject, index) in subjects"
                :key="subject.id"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                :class="index % 2 === 1 ? 'bg-slate-50/50 dark:bg-slate-800/30' : ''"
              >
                <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ subject.code }}</td>
                <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ subject.name }}</td>
                <td class="px-5 py-3 text-slate-500 dark:text-slate-400">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                    {{ subject.category }}
                  </span>
                </td>
                <td class="px-5 py-3 text-right">
                  <button class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors mr-2" @click="openEditSubject(subject)">
                    <i class="fa-solid fa-pen-to-square"></i> Edit
                  </button>
                  <button class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors" @click="deleteSubject(subject.id)">
                    <i class="fa-solid fa-trash"></i> Delete
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ═══════ Tab 2: Journal Vouchers ═══════ -->
    <div v-if="activeTab === 'journal'">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">Journal Vouchers</h2>
          <select
            v-model="selectedJournalYear"
            class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-1.5"
          >
            <option v-for="year in recentYears" :key="year" :value="year">{{ year }}</option>
          </select>
        </div>
        <button
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-500 hover:bg-amber-600 rounded-lg shadow-sm transition-colors"
          @click="openAddVoucher"
        >
          <i class="fa-solid fa-plus text-xs"></i>
          Add Voucher
        </button>
      </div>

      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700">
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Date</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Voucher No.</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Description</th>
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Type</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(voucher, index) in filteredVouchers"
                :key="voucher.id"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                :class="index % 2 === 1 ? 'bg-slate-50/50 dark:bg-slate-800/30' : ''"
              >
                <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ voucher.date }}</td>
                <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ voucher.voucherNumber }}</td>
                <td class="px-5 py-3 text-slate-500 dark:text-slate-400">{{ voucher.description }}</td>
                <td class="px-5 py-3">
                  <span
                    v-if="voucher.isSystemGenerated"
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                  >
                    <i class="fa-solid fa-gear mr-1 text-[10px]"></i> System
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                  >
                    <i class="fa-solid fa-user mr-1 text-[10px]"></i> Manual
                  </span>
                </td>
                <td class="px-5 py-3 text-right">
                  <button class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors">
                    <i class="fa-solid fa-eye"></i> View
                  </button>
                </td>
              </tr>
              <tr v-if="filteredVouchers.length === 0">
                <td colspan="5" class="px-5 py-8 text-center text-slate-400 dark:text-slate-500">
                  No vouchers found for {{ selectedJournalYear }}.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ═══════ Tab 3: Financial Reports ═══════ -->
    <div v-if="activeTab === 'reports'">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="flex gap-1 bg-slate-100 dark:bg-slate-700 rounded-lg p-1">
            <button
              v-for="report in ([
                { key: 'trial', label: 'Trial Balance' },
                { key: 'income', label: 'Income Statement' },
                { key: 'balance', label: 'Balance Sheet' },
              ] as const)"
              :key="report.key"
              class="px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
              :class="activeReport === report.key
                ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-stone-50 shadow-sm'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-stone-200'"
              @click="activeReport = report.key"
            >
              {{ report.label }}
            </button>
          </div>
        </div>
        <select
          v-model="selectedReportYear"
          class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-1.5"
        >
          <option v-for="year in recentYears" :key="year" :value="year">{{ year }}</option>
        </select>
      </div>

      <!-- Trial Balance -->
      <div v-if="activeReport === 'trial'" class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div class="flex items-center gap-2 px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <i class="fa-solid fa-scale-balanced text-amber-500"></i>
          <h3 class="text-sm font-semibold text-slate-700 dark:text-stone-200">Trial Balance - {{ selectedReportYear }}</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700">
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Account Name</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Debit Balance</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Credit Balance</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, index) in trialBalanceData"
                :key="row.name"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                :class="index % 2 === 1 ? 'bg-slate-50/50 dark:bg-slate-800/30' : ''"
              >
                <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ row.name }}</td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">{{ row.debit ? `$${row.debit.toLocaleString()}` : '-' }}</td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">{{ row.credit ? `$${row.credit.toLocaleString()}` : '-' }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="border-t-2 border-slate-300 dark:border-slate-600 font-bold">
                <td class="px-5 py-3 text-slate-900 dark:text-stone-50">Total</td>
                <td class="px-5 py-3 text-right font-mono text-slate-900 dark:text-stone-50">${{ trialBalanceData.reduce((s, r) => s + r.debit, 0).toLocaleString() }}</td>
                <td class="px-5 py-3 text-right font-mono text-slate-900 dark:text-stone-50">${{ trialBalanceData.reduce((s, r) => s + r.credit, 0).toLocaleString() }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- Income Statement -->
      <div v-if="activeReport === 'income'" class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div class="flex items-center gap-2 px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <i class="fa-solid fa-chart-line text-amber-500"></i>
          <h3 class="text-sm font-semibold text-slate-700 dark:text-stone-200">Income Statement - {{ selectedReportYear }}</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700">
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Item</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr class="bg-emerald-50/50 dark:bg-emerald-900/10">
                <td class="px-5 py-2 font-semibold text-emerald-700 dark:text-emerald-400" colspan="2">Revenue</td>
              </tr>
              <tr
                v-for="item in incomeStatementData.revenue"
                :key="item.name"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              >
                <td class="px-5 py-3 pl-10 text-slate-700 dark:text-stone-200">{{ item.name }}</td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ item.amount.toLocaleString() }}</td>
              </tr>
              <tr class="border-b border-slate-200 dark:border-slate-700 font-semibold">
                <td class="px-5 py-2 text-emerald-700 dark:text-emerald-400">Total Revenue</td>
                <td class="px-5 py-2 text-right font-mono text-emerald-700 dark:text-emerald-400">${{ incomeTotal.toLocaleString() }}</td>
              </tr>
              <tr class="bg-red-50/50 dark:bg-red-900/10">
                <td class="px-5 py-2 font-semibold text-red-700 dark:text-red-400" colspan="2">Expenses</td>
              </tr>
              <tr
                v-for="item in incomeStatementData.expenses"
                :key="item.name"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              >
                <td class="px-5 py-3 pl-10 text-slate-700 dark:text-stone-200">{{ item.name }}</td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ item.amount.toLocaleString() }}</td>
              </tr>
              <tr class="border-b border-slate-200 dark:border-slate-700 font-semibold">
                <td class="px-5 py-2 text-red-700 dark:text-red-400">Total Expenses</td>
                <td class="px-5 py-2 text-right font-mono text-red-700 dark:text-red-400">${{ expenseTotal.toLocaleString() }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="border-t-2 border-slate-300 dark:border-slate-600 font-bold">
                <td class="px-5 py-3 text-slate-900 dark:text-stone-50">Net Income</td>
                <td class="px-5 py-3 text-right font-mono" :class="netIncome >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'">${{ netIncome.toLocaleString() }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- Balance Sheet -->
      <div v-if="activeReport === 'balance'" class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div class="flex items-center gap-2 px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <i class="fa-solid fa-building-columns text-amber-500"></i>
          <h3 class="text-sm font-semibold text-slate-700 dark:text-stone-200">Balance Sheet - {{ selectedReportYear }}</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700">
                <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Item</th>
                <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr class="bg-blue-50/50 dark:bg-blue-900/10">
                <td class="px-5 py-2 font-semibold text-blue-700 dark:text-blue-400" colspan="2">Assets</td>
              </tr>
              <tr
                v-for="item in balanceSheetData.assets"
                :key="item.name"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              >
                <td class="px-5 py-3 pl-10 text-slate-700 dark:text-stone-200">{{ item.name }}</td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ item.amount.toLocaleString() }}</td>
              </tr>
              <tr class="border-b border-slate-200 dark:border-slate-700 font-semibold">
                <td class="px-5 py-2 text-blue-700 dark:text-blue-400">Total Assets</td>
                <td class="px-5 py-2 text-right font-mono text-blue-700 dark:text-blue-400">${{ totalAssets.toLocaleString() }}</td>
              </tr>

              <tr class="bg-orange-50/50 dark:bg-orange-900/10">
                <td class="px-5 py-2 font-semibold text-orange-700 dark:text-orange-400" colspan="2">Liabilities</td>
              </tr>
              <tr
                v-for="item in balanceSheetData.liabilities"
                :key="item.name"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              >
                <td class="px-5 py-3 pl-10 text-slate-700 dark:text-stone-200">{{ item.name }}</td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ item.amount.toLocaleString() }}</td>
              </tr>
              <tr class="border-b border-slate-200 dark:border-slate-700 font-semibold">
                <td class="px-5 py-2 text-orange-700 dark:text-orange-400">Total Liabilities</td>
                <td class="px-5 py-2 text-right font-mono text-orange-700 dark:text-orange-400">${{ totalLiabilities.toLocaleString() }}</td>
              </tr>

              <tr class="bg-purple-50/50 dark:bg-purple-900/10">
                <td class="px-5 py-2 font-semibold text-purple-700 dark:text-purple-400" colspan="2">Owner's Equity</td>
              </tr>
              <tr
                v-for="item in balanceSheetData.equity"
                :key="item.name"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              >
                <td class="px-5 py-3 pl-10 text-slate-700 dark:text-stone-200">{{ item.name }}</td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ item.amount.toLocaleString() }}</td>
              </tr>
              <tr class="border-b border-slate-200 dark:border-slate-700 font-semibold">
                <td class="px-5 py-2 text-purple-700 dark:text-purple-400">Total Equity</td>
                <td class="px-5 py-2 text-right font-mono text-purple-700 dark:text-purple-400">${{ totalEquity.toLocaleString() }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="border-t-2 border-slate-300 dark:border-slate-600 font-bold">
                <td class="px-5 py-3 text-slate-900 dark:text-stone-50">Total Liabilities + Equity</td>
                <td class="px-5 py-3 text-right font-mono text-slate-900 dark:text-stone-50">${{ (totalLiabilities + totalEquity).toLocaleString() }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>

    <!-- ═══════ Subject Modal ═══════ -->
    <Teleport to="body">
      <div v-if="showSubjectModal" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/40" @click="showSubjectModal = false"></div>
        <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
          <div class="flex items-center justify-between mb-5">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-stone-50">
              {{ editingSubject ? 'Edit Subject' : 'Add Subject' }}
            </h3>
            <button class="text-slate-400 hover:text-slate-600 dark:hover:text-stone-200" @click="showSubjectModal = false">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">Code</label>
              <input
                v-model="subjectForm.code"
                type="text"
                class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                placeholder="e.g. 1001"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">Name</label>
              <input
                v-model="subjectForm.name"
                type="text"
                class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                placeholder="e.g. Cash"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">Category</label>
              <select
                v-model="subjectForm.category"
                class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-6">
            <button class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors" @click="showSubjectModal = false">
              Cancel
            </button>
            <button class="px-4 py-2 text-sm font-medium text-white bg-amber-500 hover:bg-amber-600 rounded-lg shadow-sm transition-colors" @click="saveSubject">
              Save
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══════ Voucher Modal ═══════ -->
    <Teleport to="body">
      <div v-if="showVoucherModal" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/40" @click="showVoucherModal = false"></div>
        <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-2xl mx-4 p-6 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between mb-5">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-stone-50">Add Voucher</h3>
            <button class="text-slate-400 hover:text-slate-600 dark:hover:text-stone-200" @click="showVoucherModal = false">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">Date</label>
                <input
                  v-model="voucherForm.date"
                  type="date"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">Description</label>
                <input
                  v-model="voucherForm.description"
                  type="text"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="Voucher description"
                />
              </div>
            </div>

            <!-- Entries -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-medium text-slate-700 dark:text-stone-200">Entries</label>
                <button class="inline-flex items-center gap-1 text-xs font-medium text-amber-600 dark:text-amber-400 hover:text-amber-700" @click="addVoucherEntry">
                  <i class="fa-solid fa-plus"></i> Add Entry
                </button>
              </div>
              <div class="space-y-2">
                <div
                  v-for="(entry, index) in voucherForm.entries"
                  :key="index"
                  class="grid grid-cols-[1fr_120px_120px_40px] gap-2 items-center"
                >
                  <select
                    v-model="entry.accountSubject"
                    class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  >
                    <option value="" disabled>Select account</option>
                    <option v-for="subject in subjects" :key="subject.id" :value="subject.code">
                      {{ subject.code }} - {{ subject.name }}
                    </option>
                  </select>
                  <input
                    v-model.number="entry.debitAmount"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="Debit"
                    class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                  <input
                    v-model.number="entry.creditAmount"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="Credit"
                    class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                  <button
                    class="flex items-center justify-center w-8 h-8 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                    :class="voucherForm.entries.length <= 2 ? 'opacity-30 cursor-not-allowed' : ''"
                    :disabled="voucherForm.entries.length <= 2"
                    @click="removeVoucherEntry(index)"
                  >
                    <i class="fa-solid fa-trash text-xs"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- Totals -->
            <div class="flex items-center justify-between px-4 py-3 rounded-lg border" :class="isBalanced ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800' : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'">
              <div class="flex gap-6 text-sm">
                <span class="text-slate-700 dark:text-stone-200">
                  Debit Total: <strong class="font-mono">${{ totalDebit.toLocaleString() }}</strong>
                </span>
                <span class="text-slate-700 dark:text-stone-200">
                  Credit Total: <strong class="font-mono">${{ totalCredit.toLocaleString() }}</strong>
                </span>
              </div>
              <div v-if="!isBalanced" class="flex items-center gap-1 text-sm text-red-600 dark:text-red-400 font-medium">
                <i class="fa-solid fa-triangle-exclamation text-xs"></i>
                Debit and credit are not balanced
              </div>
              <div v-else class="flex items-center gap-1 text-sm text-emerald-600 dark:text-emerald-400 font-medium">
                <i class="fa-solid fa-check text-xs"></i>
                Balanced
              </div>
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-6">
            <button class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors" @click="showVoucherModal = false">
              Cancel
            </button>
            <button
              class="px-4 py-2 text-sm font-medium text-white rounded-lg shadow-sm transition-colors"
              :class="isBalanced ? 'bg-amber-500 hover:bg-amber-600' : 'bg-slate-300 dark:bg-slate-600 cursor-not-allowed'"
              :disabled="!isBalanced"
              @click="saveVoucher"
            >
              Save
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
