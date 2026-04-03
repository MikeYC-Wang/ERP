<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  getAccountSubjects,
  createAccountSubject,
  updateAccountSubject,
  deleteAccountSubject as apiDeleteSubject,
  getJournalVouchers,
  createJournalVoucher,
} from '@/api/accounting'

// ─── Loading ───
const loading = ref(false)

// ─── Tab State ───
const activeTab = ref<'subjects' | 'journal' | 'reports'>('subjects')

// ─── Tab 1: Account Subjects ───
interface AccountSubject {
  id: number
  code: string
  name: string
  category: string
}

const categoryMap: Record<string, string> = {
  'Assets': '資產',
  'Liabilities': '負債',
  'Equity': '投入',
  'Revenue': '收入',
  'Operating Expenses': '營業費用',
}
const categories = ['Assets', 'Liabilities', 'Equity', 'Revenue', 'Operating Expenses'] as const

const subjects = ref<AccountSubject[]>([
  { id: 1, code: '1001', name: '商品存貨', category: 'Assets' },
  { id: 2, code: '1002', name: '應收帳款', category: 'Assets' },
  { id: 3, code: '2001', name: '應付帳款', category: 'Liabilities' },
  { id: 4, code: '4001', name: '銷貨收入', category: 'Revenue' },
  { id: 5, code: '5001', name: '租金費用', category: 'Operating Expenses' },
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

async function saveSubject() {
  if (editingSubject.value) {
    try {
      await updateAccountSubject(editingSubject.value.id, subjectForm.value)
    } catch (e) {
      console.warn('Failed to update subject via API, applying locally', e)
    }
    const idx = subjects.value.findIndex((s) => s.id === editingSubject.value!.id)
    if (idx !== -1) {
      subjects.value[idx] = { ...subjects.value[idx], ...subjectForm.value }
    }
  } else {
    try {
      const res = await createAccountSubject(subjectForm.value)
      subjects.value.push(res.data)
      showSubjectModal.value = false
      return
    } catch (e) {
      console.warn('Failed to create subject via API, applying locally', e)
    }
    const newId = Math.max(...subjects.value.map((s) => s.id), 0) + 1
    subjects.value.push({ id: newId, ...subjectForm.value })
  }
  showSubjectModal.value = false
}

async function deleteSubject(id: number) {
  try {
    await apiDeleteSubject(id)
  } catch (e) {
    console.warn('Failed to delete subject via API, applying locally', e)
  }
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
    description: '每月租金支付',
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
    description: '銷貨收入認列',
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
    description: '進貨存貨',
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

async function saveVoucher() {
  if (!isBalanced.value) return
  try {
    const payload = {
      date: voucherForm.value.date,
      description: voucherForm.value.description,
      entries: voucherForm.value.entries.map((e) => ({
        account_subject: Number(e.accountSubject),
        debit_amount: e.debitAmount,
        credit_amount: e.creditAmount,
      })),
    }
    await createJournalVoucher(payload)
  } catch (e) {
    console.warn('Failed to create voucher via API, applying locally', e)
  }
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
  { name: '商品存貨', debit: 45000, credit: 0 },
  { name: '應收帳款', debit: 18500, credit: 0 },
  { name: '應付帳款', debit: 0, credit: 12000 },
  { name: '銷貨收入', debit: 0, credit: 128430 },
  { name: '租金費用', debit: 30000, credit: 0 },
  { name: '業主權益', debit: 0, credit: 53070 },
]

const incomeStatementData = {
  revenue: [
    { name: '銷貨收入', amount: 128430 },
    { name: '服務收入', amount: 15200 },
  ],
  expenses: [
    { name: '銷貨成本', amount: 84210 },
    { name: '租金費用', amount: 30000 },
    { name: '水電費用', amount: 4800 },
    { name: '薪資費用', amount: 12000 },
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
    { name: '現金', amount: 32000 },
    { name: '商品存貨', amount: 45000 },
    { name: '應收帳款', amount: 18500 },
  ],
  liabilities: [
    { name: '應付帳款', amount: 12000 },
    { name: '應付票據', amount: 25000 },
  ],
  equity: [
    { name: '業主資本', amount: 40000 },
    { name: '保留盈餘', amount: 18500 },
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

// ─── Load from API ───
onMounted(async () => {
  loading.value = true
  try {
    const [subjectsRes, vouchersRes] = await Promise.all([
      getAccountSubjects().catch(() => null),
      getJournalVouchers().catch(() => null),
    ])
    if (subjectsRes?.data && Array.isArray(subjectsRes.data)) {
      subjects.value = subjectsRes.data
    }
    if (vouchersRes?.data && Array.isArray(vouchersRes.data)) {
      vouchers.value = vouchersRes.data.map((v: Record<string, unknown>) => ({
        id: v.id as number,
        date: v.date as string,
        voucherNumber: v.voucher_number as string,
        description: v.description as string,
        isSystemGenerated: v.is_system_generated as boolean,
        entries: (v.entries as Array<Record<string, unknown>>)?.map((e) => ({
          accountSubject: String(e.account_subject),
          debitAmount: Number(e.debit_amount),
          creditAmount: Number(e.credit_amount),
        })) || [],
      }))
    }
  } catch (e) {
    console.warn('Accounting API unavailable, using fallback data', e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6 animate-fade-in-up">
    <!-- Page Header -->
    <div class="flex items-center gap-2">
      <i class="fa-solid fa-file-invoice-dollar text-amber-500"></i>
      <h1 class="text-xl font-bold text-slate-900 dark:text-stone-50">會計管理</h1>
    </div>

    <!-- Tabs -->
    <div class="border-b border-slate-200 dark:border-slate-700">
      <nav class="flex gap-2">
        <button
          v-for="tab in ([
            { key: 'subjects', label: '會計科目', icon: 'fa-solid fa-list-ol' },
            { key: 'journal', label: '日記帳', icon: 'fa-solid fa-book' },
            { key: 'reports', label: '財務報表', icon: 'fa-solid fa-chart-pie' },
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
      <!-- Tab 1: Account Subjects -->
      <Transition name="fade" mode="out-in">
        <div v-if="activeTab === 'subjects'" key="subjects">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">會計科目</h2>
            <button
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all duration-300"
              @click="openAddSubject"
            >
              <i class="fa-solid fa-plus text-xs"></i>
              新增
            </button>
          </div>

          <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-amber-400">
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-800 dark:to-slate-800">
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">代碼</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">名稱</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">類別</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(subject, index) in subjects"
                    :key="subject.id"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                    :class="index % 2 === 1 ? 'bg-orange-50/30 dark:bg-gray-800/50' : ''"
                  >
                    <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ subject.code }}</td>
                    <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ subject.name }}</td>
                    <td class="px-5 py-3 text-slate-500 dark:text-slate-400">
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                        {{ categoryMap[subject.category] || subject.category }}
                      </span>
                    </td>
                    <td class="px-5 py-3 text-right">
                      <button class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all mr-2" @click="openEditSubject(subject)">
                        <i class="fa-solid fa-pen-to-square"></i> 編輯
                      </button>
                      <button class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-red-400 to-rose-500 hover:from-red-500 hover:to-rose-600 rounded hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all" @click="deleteSubject(subject.id)">
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

      <!-- Tab 2: Journal Vouchers -->
      <Transition name="fade" mode="out-in">
        <div v-if="activeTab === 'journal'" key="journal">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">日記帳</h2>
              <select
                v-model="selectedJournalYear"
                class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-1.5"
              >
                <option v-for="year in recentYears" :key="year" :value="year">{{ year }}</option>
              </select>
            </div>
            <button
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all duration-300"
              @click="openAddVoucher"
            >
              <i class="fa-solid fa-plus text-xs"></i>
              新增傳票
            </button>
          </div>

          <div class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-amber-400">
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-800 dark:to-slate-800">
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">日期</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">傳票編號</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">摘要</th>
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">類型</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(voucher, index) in filteredVouchers"
                    :key="voucher.id"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                    :class="index % 2 === 1 ? 'bg-orange-50/30 dark:bg-gray-800/50' : ''"
                  >
                    <td class="px-5 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ voucher.date }}</td>
                    <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ voucher.voucherNumber }}</td>
                    <td class="px-5 py-3 text-slate-500 dark:text-slate-400">{{ voucher.description }}</td>
                    <td class="px-5 py-3">
                      <span
                        v-if="voucher.isSystemGenerated"
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                      >
                        <i class="fa-solid fa-gear mr-1 text-[10px]"></i> 系統自動
                      </span>
                      <span
                        v-else
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                      >
                        <i class="fa-solid fa-user mr-1 text-[10px]"></i> 手動
                      </span>
                    </td>
                    <td class="px-5 py-3 text-right">
                      <button class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all">
                        <i class="fa-solid fa-eye"></i> 檢視
                      </button>
                    </td>
                  </tr>
                  <tr v-if="filteredVouchers.length === 0">
                    <td colspan="5" class="px-5 py-8 text-center text-slate-400 dark:text-slate-500">
                      {{ selectedJournalYear }} 年度無傳票資料。
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Tab 3: Financial Reports -->
      <Transition name="fade" mode="out-in">
        <div v-if="activeTab === 'reports'" key="reports">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="flex gap-1 bg-slate-100 dark:bg-slate-700 rounded-lg p-1">
                <button
                  v-for="report in ([
                    { key: 'trial', label: '試算表' },
                    { key: 'income', label: '損益表' },
                    { key: 'balance', label: '資產負債表' },
                  ] as const)"
                  :key="report.key"
                  class="px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-300"
                  :class="activeReport === report.key
                    ? 'bg-gradient-to-r from-amber-400 to-orange-500 text-white shadow-sm'
                    : 'text-slate-500 dark:text-slate-400 hover:text-amber-600'"
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
          <div v-if="activeReport === 'trial'" class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-amber-400">
            <div class="flex items-center gap-2 px-5 py-4 border-b border-slate-200 dark:border-slate-700">
              <i class="fa-solid fa-scale-balanced text-amber-500"></i>
              <h3 class="text-sm font-semibold text-slate-700 dark:text-stone-200">試算表 - {{ selectedReportYear }}</h3>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-800 dark:to-slate-800">
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">科目名稱</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">借方餘額</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">貸方餘額</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(row, index) in trialBalanceData"
                    :key="row.name"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                    :class="index % 2 === 1 ? 'bg-orange-50/30 dark:bg-gray-800/50' : ''"
                  >
                    <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">{{ row.name }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">{{ row.debit ? `$${row.debit.toLocaleString()}` : '-' }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">{{ row.credit ? `$${row.credit.toLocaleString()}` : '-' }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr class="border-t-2 border-slate-300 dark:border-slate-600 font-bold">
                    <td class="px-5 py-3 text-slate-900 dark:text-stone-50">合計</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-900 dark:text-stone-50">${{ trialBalanceData.reduce((s, r) => s + r.debit, 0).toLocaleString() }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-900 dark:text-stone-50">${{ trialBalanceData.reduce((s, r) => s + r.credit, 0).toLocaleString() }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <!-- Income Statement -->
          <div v-if="activeReport === 'income'" class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-emerald-400">
            <div class="flex items-center gap-2 px-5 py-4 border-b border-slate-200 dark:border-slate-700">
              <i class="fa-solid fa-chart-line text-amber-500"></i>
              <h3 class="text-sm font-semibold text-slate-700 dark:text-stone-200">損益表 - {{ selectedReportYear }}</h3>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-800 dark:to-slate-800">
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">項目</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">金額</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="bg-emerald-50/50 dark:bg-emerald-900/10">
                    <td class="px-5 py-2 font-semibold text-emerald-700 dark:text-emerald-400" colspan="2">收入</td>
                  </tr>
                  <tr
                    v-for="item in incomeStatementData.revenue"
                    :key="item.name"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                  >
                    <td class="px-5 py-3 pl-10 text-slate-700 dark:text-stone-200">{{ item.name }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ item.amount.toLocaleString() }}</td>
                  </tr>
                  <tr class="border-b border-slate-200 dark:border-slate-700 font-semibold">
                    <td class="px-5 py-2 text-emerald-700 dark:text-emerald-400">總收入</td>
                    <td class="px-5 py-2 text-right font-mono text-emerald-700 dark:text-emerald-400">${{ incomeTotal.toLocaleString() }}</td>
                  </tr>
                  <tr class="bg-red-50/50 dark:bg-red-900/10">
                    <td class="px-5 py-2 font-semibold text-red-700 dark:text-red-400" colspan="2">費用</td>
                  </tr>
                  <tr
                    v-for="item in incomeStatementData.expenses"
                    :key="item.name"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                  >
                    <td class="px-5 py-3 pl-10 text-slate-700 dark:text-stone-200">{{ item.name }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ item.amount.toLocaleString() }}</td>
                  </tr>
                  <tr class="border-b border-slate-200 dark:border-slate-700 font-semibold">
                    <td class="px-5 py-2 text-red-700 dark:text-red-400">總費用</td>
                    <td class="px-5 py-2 text-right font-mono text-red-700 dark:text-red-400">${{ expenseTotal.toLocaleString() }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr class="border-t-2 border-slate-300 dark:border-slate-600 font-bold">
                    <td class="px-5 py-3 text-slate-900 dark:text-stone-50">本期淨利</td>
                    <td class="px-5 py-3 text-right font-mono" :class="netIncome >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'">${{ netIncome.toLocaleString() }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <!-- Balance Sheet -->
          <div v-if="activeReport === 'balance'" class="bg-white dark:bg-gray-800/90 dark:ring-1 dark:ring-white/5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-l-4 border-l-blue-400">
            <div class="flex items-center gap-2 px-5 py-4 border-b border-slate-200 dark:border-slate-700">
              <i class="fa-solid fa-building-columns text-amber-500"></i>
              <h3 class="text-sm font-semibold text-slate-700 dark:text-stone-200">資產負債表 - {{ selectedReportYear }}</h3>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-800 dark:to-slate-800">
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">項目</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">金額</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="bg-blue-50/50 dark:bg-blue-900/10">
                    <td class="px-5 py-2 font-semibold text-blue-700 dark:text-blue-400" colspan="2">資產</td>
                  </tr>
                  <tr
                    v-for="item in balanceSheetData.assets"
                    :key="item.name"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                  >
                    <td class="px-5 py-3 pl-10 text-slate-700 dark:text-stone-200">{{ item.name }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ item.amount.toLocaleString() }}</td>
                  </tr>
                  <tr class="border-b border-slate-200 dark:border-slate-700 font-semibold">
                    <td class="px-5 py-2 text-blue-700 dark:text-blue-400">資產合計</td>
                    <td class="px-5 py-2 text-right font-mono text-blue-700 dark:text-blue-400">${{ totalAssets.toLocaleString() }}</td>
                  </tr>

                  <tr class="bg-orange-50/50 dark:bg-orange-900/10">
                    <td class="px-5 py-2 font-semibold text-orange-700 dark:text-orange-400" colspan="2">負債</td>
                  </tr>
                  <tr
                    v-for="item in balanceSheetData.liabilities"
                    :key="item.name"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                  >
                    <td class="px-5 py-3 pl-10 text-slate-700 dark:text-stone-200">{{ item.name }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ item.amount.toLocaleString() }}</td>
                  </tr>
                  <tr class="border-b border-slate-200 dark:border-slate-700 font-semibold">
                    <td class="px-5 py-2 text-orange-700 dark:text-orange-400">負債合計</td>
                    <td class="px-5 py-2 text-right font-mono text-orange-700 dark:text-orange-400">${{ totalLiabilities.toLocaleString() }}</td>
                  </tr>

                  <tr class="bg-purple-50/50 dark:bg-purple-900/10">
                    <td class="px-5 py-2 font-semibold text-purple-700 dark:text-purple-400" colspan="2">業主權益</td>
                  </tr>
                  <tr
                    v-for="item in balanceSheetData.equity"
                    :key="item.name"
                    class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-amber-50 dark:hover:bg-gray-700/50 hover:translate-x-1 transition-all"
                  >
                    <td class="px-5 py-3 pl-10 text-slate-700 dark:text-stone-200">{{ item.name }}</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">${{ item.amount.toLocaleString() }}</td>
                  </tr>
                  <tr class="border-b border-slate-200 dark:border-slate-700 font-semibold">
                    <td class="px-5 py-2 text-purple-700 dark:text-purple-400">業主權益合計</td>
                    <td class="px-5 py-2 text-right font-mono text-purple-700 dark:text-purple-400">${{ totalEquity.toLocaleString() }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr class="border-t-2 border-slate-300 dark:border-slate-600 font-bold">
                    <td class="px-5 py-3 text-slate-900 dark:text-stone-50">負債 + 業主權益合計</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-900 dark:text-stone-50">${{ (totalLiabilities + totalEquity).toLocaleString() }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </Transition>
    </template>

    <!-- Subject Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showSubjectModal" class="fixed inset-0 z-50 flex items-center justify-center">
          <div class="absolute inset-0 bg-black/40" @click="showSubjectModal = false"></div>
          <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md mx-4 p-6 modal-enter-active">
            <div class="flex items-center justify-between mb-5">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-stone-50">
                {{ editingSubject ? '編輯會計科目' : '新增會計科目' }}
              </h3>
              <button class="text-slate-400 hover:text-slate-600 dark:hover:text-stone-200" @click="showSubjectModal = false">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">代碼</label>
                <input
                  v-model="subjectForm.code"
                  type="text"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="例如 1001"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">名稱</label>
                <input
                  v-model="subjectForm.name"
                  type="text"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="例如 現金"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">類別</label>
                <select
                  v-model="subjectForm.category"
                  class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <option v-for="cat in categories" :key="cat" :value="cat">{{ categoryMap[cat] }}</option>
                </select>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg active:scale-95 transition-all" @click="showSubjectModal = false">
                取消
              </button>
              <button class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all" @click="saveSubject">
                儲存
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Voucher Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showVoucherModal" class="fixed inset-0 z-50 flex items-center justify-center">
          <div class="absolute inset-0 bg-black/40" @click="showVoucherModal = false"></div>
          <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-2xl mx-4 p-6 max-h-[90vh] overflow-y-auto modal-enter-active">
            <div class="flex items-center justify-between mb-5">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-stone-50">新增傳票</h3>
              <button class="text-slate-400 hover:text-slate-600 dark:hover:text-stone-200" @click="showVoucherModal = false">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>
            <div class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">日期</label>
                  <input
                    v-model="voucherForm.date"
                    type="date"
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-stone-200 mb-1">摘要</label>
                  <input
                    v-model="voucherForm.description"
                    type="text"
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    placeholder="傳票摘要說明"
                  />
                </div>
              </div>

              <!-- Entries -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <label class="text-sm font-medium text-slate-700 dark:text-stone-200">分錄</label>
                  <button class="inline-flex items-center gap-1 text-xs font-medium text-amber-600 dark:text-amber-400 hover:text-amber-700 active:scale-95 transition-transform" @click="addVoucherEntry">
                    <i class="fa-solid fa-plus"></i> 新增分錄
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
                      <option value="" disabled>選擇科目</option>
                      <option v-for="subject in subjects" :key="subject.id" :value="subject.code">
                        {{ subject.code }} - {{ subject.name }}
                      </option>
                    </select>
                    <input
                      v-model.number="entry.debitAmount"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="借方"
                      class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    />
                    <input
                      v-model.number="entry.creditAmount"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="貸方"
                      class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    />
                    <button
                      class="flex items-center justify-center w-8 h-8 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded active:scale-95 transition-all"
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
                    借方合計: <strong class="font-mono">${{ totalDebit.toLocaleString() }}</strong>
                  </span>
                  <span class="text-slate-700 dark:text-stone-200">
                    貸方合計: <strong class="font-mono">${{ totalCredit.toLocaleString() }}</strong>
                  </span>
                </div>
                <div v-if="!isBalanced" class="flex items-center gap-1 text-sm text-red-600 dark:text-red-400 font-medium">
                  <i class="fa-solid fa-triangle-exclamation text-xs"></i>
                  借貸方不平衡
                </div>
                <div v-else class="flex items-center gap-1 text-sm text-emerald-600 dark:text-emerald-400 font-medium">
                  <i class="fa-solid fa-check text-xs"></i>
                  已平衡
                </div>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg active:scale-95 transition-all" @click="showVoucherModal = false">
                取消
              </button>
              <button
                class="px-4 py-2 text-sm font-medium text-white rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all"
                :class="isBalanced ? 'bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600' : 'bg-slate-300 dark:bg-slate-600 cursor-not-allowed'"
                :disabled="!isBalanced"
                @click="saveVoucher"
              >
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
