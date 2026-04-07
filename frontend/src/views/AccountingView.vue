<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import * as XLSX from 'xlsx'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import {
  getAccountSubjects,
  createAccountSubject,
  updateAccountSubject,
  deleteAccountSubject as apiDeleteSubject,
  getJournalVouchers,
  createJournalVoucher,
  updateJournalVoucher,
  deleteJournalVoucher,
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
  'asset': '資產',
  'liability': '負債',
  'equity': '投入',
  'revenue': '收入',
  'expense': '營業費用',
}
const categories = ['asset', 'liability', 'equity', 'revenue', 'expense'] as const

const subjects = ref<AccountSubject[]>([])

const showSubjectModal = ref(false)
const editingSubject = ref<AccountSubject | null>(null)
const subjectForm = ref({ code: '', name: '', category: 'asset' })

function openAddSubject() {
  editingSubject.value = null
  subjectForm.value = { code: '', name: '', category: 'asset' }
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
  isPosted: boolean
  entries: VoucherEntry[]
}

// ─── Pagination helper ───
function pageWindow(current: number, total: number, size = 5): number[] {
  const half = Math.floor(size / 2)
  let start = Math.max(1, current - half)
  const end = Math.min(total, start + size - 1)
  if (end - start + 1 < size) start = Math.max(1, end - size + 1)
  return Array.from({ length: end - start + 1 }, (_, i) => start + i)
}

// ─── Pagination: Account Subjects ───
const subjectPage = ref(1)
const SUBJECT_PAGE_SIZE = 15
const pagedSubjects = computed(() => {
  const start = (subjectPage.value - 1) * SUBJECT_PAGE_SIZE
  return subjects.value.slice(start, start + SUBJECT_PAGE_SIZE)
})
const subjectTotalPages = computed(() => Math.max(1, Math.ceil(subjects.value.length / SUBJECT_PAGE_SIZE)))
const subjectVisiblePages = computed(() => pageWindow(subjectPage.value, subjectTotalPages.value))

const currentYear = new Date().getFullYear()
const recentYears = [currentYear - 2, currentYear - 1, currentYear]
const months = [
  { value: 0, label: '全年' },
  { value: 1, label: '1月' }, { value: 2, label: '2月' }, { value: 3, label: '3月' },
  { value: 4, label: '4月' }, { value: 5, label: '5月' }, { value: 6, label: '6月' },
  { value: 7, label: '7月' }, { value: 8, label: '8月' }, { value: 9, label: '9月' },
  { value: 10, label: '10月' }, { value: 11, label: '11月' }, { value: 12, label: '12月' },
]
const selectedJournalYear = ref(currentYear)
const selectedJournalMonth = ref(0)

const vouchers = ref<JournalVoucher[]>([])

// ─── 傳票檢視 Modal ───
const showViewModal = ref(false)
const viewingVoucher = ref<JournalVoucher | null>(null)

function openViewVoucher(voucher: JournalVoucher) {
  viewingVoucher.value = voucher
  showViewModal.value = true
}

async function deleteVoucher(voucher: JournalVoucher) {
  if (!confirm(`確定刪除傳票「${voucher.voucherNumber}」？此操作無法復原。`)) return
  try {
    await deleteJournalVoucher(voucher.id)
    vouchers.value = vouchers.value.filter((v) => v.id !== voucher.id)
  } catch (e) {
    alert('刪除失敗，請確認此傳票非系統自動產生。')
  }
}

const filteredVouchers = computed(() => {
  return vouchers.value.filter((v) => {
    if (!v.date.startsWith(String(selectedJournalYear.value))) return false
    if (selectedJournalMonth.value === 0) return true
    const mm = String(selectedJournalMonth.value).padStart(2, '0')
    return v.date.startsWith(`${selectedJournalYear.value}-${mm}`)
  })
})

// ─── Pagination: Journal Vouchers ───
const voucherPage = ref(1)
const VOUCHER_PAGE_SIZE = 15
const pagedVouchers = computed(() => {
  const start = (voucherPage.value - 1) * VOUCHER_PAGE_SIZE
  return filteredVouchers.value.slice(start, start + VOUCHER_PAGE_SIZE)
})
const voucherTotalPages = computed(() => Math.max(1, Math.ceil(filteredVouchers.value.length / VOUCHER_PAGE_SIZE)))
const voucherVisiblePages = computed(() => pageWindow(voucherPage.value, voucherTotalPages.value))
watch([selectedJournalYear, selectedJournalMonth], () => { voucherPage.value = 1 })

const showVoucherModal = ref(false)

interface VoucherPair {
  debitSubject: string
  creditSubject: string
  amount: number
  amountInput: string
}

function makeEmptyPair(): VoucherPair {
  return { debitSubject: '', creditSubject: '', amount: 0, amountInput: '' }
}

const voucherForm = ref({
  date: '',
  description: '',
  isPosted: false,
  pairs: [makeEmptyPair()] as VoucherPair[],
})

const editingVoucherId = ref<number | null>(null)

function findSubjectIdByName(name: string): string {
  const s = subjects.value.find((x) => x.name === name)
  return s ? String(s.id) : ''
}

function openAddVoucher() {
  editingVoucherId.value = null
  const pair1: VoucherPair = {
    debitSubject: findSubjectIdByName('銀行存款'),
    creditSubject: findSubjectIdByName('商品銷售收入'),
    amount: 0,
    amountInput: '',
  }
  const pair2: VoucherPair = {
    debitSubject: findSubjectIdByName('商品成本'),
    creditSubject: findSubjectIdByName('商品存貨'),
    amount: 0,
    amountInput: '',
  }
  voucherForm.value = {
    date: '',
    description: '',
    isPosted: true,
    pairs: [pair1, pair2],
  }
  showVoucherModal.value = true
}

function openEditVoucher(voucher: JournalVoucher) {
  editingVoucherId.value = voucher.id
  // Reconstruct pairs from flat entries: pair up [debit, credit] in order
  const pairs: VoucherPair[] = []
  for (let i = 0; i < voucher.entries.length; i += 2) {
    const d = voucher.entries[i]
    const c = voucher.entries[i + 1]
    const amt = Number(d?.debitAmount || c?.creditAmount || 0)
    pairs.push({
      debitSubject: d ? String(d.accountSubject) : '',
      creditSubject: c ? String(c.accountSubject) : '',
      amount: amt,
      amountInput: String(amt),
    })
  }
  if (pairs.length === 0) pairs.push(makeEmptyPair())
  voucherForm.value = {
    date: voucher.date,
    description: voucher.description,
    isPosted: voucher.isPosted,
    pairs,
  }
  showVoucherModal.value = true
}

function addVoucherEntry() {
  voucherForm.value.pairs.push(makeEmptyPair())
}

function removeVoucherEntry(index: number) {
  if (voucherForm.value.pairs.length > 1) {
    voucherForm.value.pairs.splice(index, 1)
  }
}

// Safe formula evaluator: only digits, + - * / ( ) . and whitespace.
// Strips a leading '='. Returns NaN on invalid input.
function evaluateFormula(raw: string): number {
  if (raw == null) return NaN
  let s = String(raw).trim()
  if (s === '') return NaN
  if (s.startsWith('=')) s = s.slice(1).trim()
  if (!/^[0-9+\-*/().\s]+$/.test(s)) return NaN
  try {
    // eslint-disable-next-line no-new-func
    const fn = new Function(`"use strict"; return (${s});`)
    const v = fn()
    if (typeof v !== 'number' || !isFinite(v)) return NaN
    return v
  } catch {
    return NaN
  }
}

function commitAmount(pair: VoucherPair) {
  const raw = pair.amountInput
  if (raw == null || String(raw).trim() === '') {
    pair.amount = 0
    pair.amountInput = ''
    return
  }
  // Plain number fast path
  const asNum = Number(raw)
  if (!isNaN(asNum) && !/[=+\-*/()]/.test(String(raw).trim().replace(/^-/, ''))) {
    pair.amount = asNum
    pair.amountInput = String(asNum)
    return
  }
  const v = evaluateFormula(String(raw))
  if (!isNaN(v)) {
    const rounded = Math.round(v * 100) / 100
    pair.amount = rounded
    pair.amountInput = String(rounded)
  }
}

const totalDebit = computed(() =>
  voucherForm.value.pairs.reduce((sum, p) => sum + Number(p.amount || 0), 0),
)
const totalCredit = totalDebit
const isBalanced = computed(() =>
  totalDebit.value > 0 &&
  voucherForm.value.pairs.every(
    (p) => p.debitSubject !== '' && p.creditSubject !== '' && Number(p.amount) > 0,
  ),
)

function mapApiVoucher(v: Record<string, unknown>): JournalVoucher {
  return {
    id: v.id as number,
    date: v.date as string,
    voucherNumber: v.voucher_number as string,
    description: v.description as string,
    isSystemGenerated: v.is_system_generated as boolean,
    isPosted: v.is_posted as boolean,
    entries: (v.items as Array<Record<string, unknown>>)?.map((e) => ({
      accountSubject: String(e.account_subject),
      debitAmount: Number(e.debit_amount),
      creditAmount: Number(e.credit_amount),
    })) || [],
  }
}

async function saveVoucher() {
  if (!isBalanced.value) return
  const items: Array<{ account_subject: number; debit_amount: number; credit_amount: number }> = []
  voucherForm.value.pairs.forEach((p) => {
    items.push({ account_subject: Number(p.debitSubject), debit_amount: Number(p.amount), credit_amount: 0 })
    items.push({ account_subject: Number(p.creditSubject), debit_amount: 0, credit_amount: Number(p.amount) })
  })
  const payload = {
    date: voucherForm.value.date,
    description: voucherForm.value.description,
    is_posted: voucherForm.value.isPosted,
    items,
  }
  if (editingVoucherId.value != null) {
    try {
      const res = await updateJournalVoucher(editingVoucherId.value, payload)
      const updated = mapApiVoucher(res.data as Record<string, unknown>)
      const idx = vouchers.value.findIndex((v) => v.id === editingVoucherId.value)
      if (idx !== -1) vouchers.value[idx] = updated
    } catch (e) {
      console.warn('Failed to update voucher via API, applying locally', e)
      const idx = vouchers.value.findIndex((v) => v.id === editingVoucherId.value)
      if (idx !== -1) {
        vouchers.value[idx] = {
          ...vouchers.value[idx],
          date: voucherForm.value.date,
          description: voucherForm.value.description,
          isPosted: voucherForm.value.isPosted,
          entries: voucherForm.value.pairs.flatMap((p) => [
            { accountSubject: p.debitSubject, debitAmount: Number(p.amount), creditAmount: 0 },
            { accountSubject: p.creditSubject, debitAmount: 0, creditAmount: Number(p.amount) },
          ]),
        }
      }
    }
  } else {
    try {
      const res = await createJournalVoucher(payload)
      vouchers.value.push(mapApiVoucher(res.data as Record<string, unknown>))
    } catch (e) {
      console.warn('Failed to create voucher via API, applying locally', e)
      const newId = Math.max(...vouchers.value.map((v) => v.id), 0) + 1
      vouchers.value.push({
        id: newId,
        date: voucherForm.value.date,
        voucherNumber: `JV-${voucherForm.value.date.substring(0, 4)}-${String(newId).padStart(3, '0')}`,
        description: voucherForm.value.description,
        isSystemGenerated: false,
        isPosted: voucherForm.value.isPosted,
        entries: voucherForm.value.pairs.flatMap((p) => [
          { accountSubject: p.debitSubject, debitAmount: Number(p.amount), creditAmount: 0 },
          { accountSubject: p.creditSubject, debitAmount: 0, creditAmount: Number(p.amount) },
        ]),
      })
    }
  }
  showVoucherModal.value = false
}

// ─── Tab 3: Financial Reports ───
const activeReport = ref<'trial' | 'income' | 'balance'>('trial')
const selectedReportYear = ref(currentYear)
const selectedReportMonth = ref(0)

// ─── 財務報表：依年份＋月份過濾 ───
// reportVouchers：損益表/資產負債表用 → 單期（只看選定月份）
const reportVouchers = computed(() =>
  vouchers.value.filter((v) => {
    if (!v.isPosted) return false
    if (!v.date.startsWith(String(selectedReportYear.value))) return false
    if (selectedReportMonth.value === 0) return true
    const mm = String(selectedReportMonth.value).padStart(2, '0')
    return v.date.startsWith(`${selectedReportYear.value}-${mm}`)
  })
)

// ─── 財務報表：從傳票明細動態彙算 ───
const subjectNameMap = computed(() => {
  const m: Record<string, string> = {}
  subjects.value.forEach((s) => { m[String(s.id)] = s.name })
  return m
})

const subjectCategoryMap = computed(() => {
  const m: Record<string, string> = {}
  subjects.value.forEach((s) => { m[String(s.id)] = s.category })
  return m
})

// 試算表用累計傳票：全年 → 全年；單月 → 年初到該月底
const trialVouchers = computed(() => {
  if (selectedReportMonth.value === 0) return reportVouchers.value
  const mm = String(selectedReportMonth.value).padStart(2, '0')
  return vouchers.value.filter((v) => {
    if (!v.isPosted) return false
    if (!v.date.startsWith(String(selectedReportYear.value))) return false
    return v.date.substring(5, 7) <= mm
  })
})

const trialBalanceData = computed(() => {
  // 彙算累計發生額（年初到選定月底）
  const gross: Record<string, { totalDebit: number; totalCredit: number }> = {}
  trialVouchers.value.forEach((v) => {
    v.entries.forEach((e) => {
      if (!gross[e.accountSubject]) gross[e.accountSubject] = { totalDebit: 0, totalCredit: 0 }
      gross[e.accountSubject].totalDebit += e.debitAmount
      gross[e.accountSubject].totalCredit += e.creditAmount
    })
  })
  // 以科目清單為基底（$0 科目也顯示），轉為餘額式
  return subjects.value.map((s) => {
    const { totalDebit = 0, totalCredit = 0 } = gross[String(s.id)] ?? {}
    const net = totalDebit - totalCredit
    return {
      name: s.name,
      debit: net > 0 ? net : 0,
      credit: net < 0 ? -net : 0,
    }
  })
})

const incomeStatementData = computed(() => {
  const revenue: { name: string; amount: number }[] = []
  const expenses: { name: string; amount: number }[] = []
  const totals: Record<string, number> = {}
  reportVouchers.value.forEach((v) => {
    v.entries.forEach((e) => {
      const net = e.creditAmount - e.debitAmount
      if (!totals[e.accountSubject]) totals[e.accountSubject] = 0
      totals[e.accountSubject] += net
    })
  })
  Object.entries(totals).forEach(([id, net]) => {
    const cat = subjectCategoryMap.value[id]
    const name = subjectNameMap.value[id] || `科目#${id}`
    if (cat === 'revenue') revenue.push({ name, amount: net })
    else if (cat === 'expense') expenses.push({ name, amount: -net })
  })
  return { revenue, expenses }
})

const incomeTotal = computed(
  () => incomeStatementData.value.revenue.reduce((s, r) => s + r.amount, 0),
)
const expenseTotal = computed(
  () => incomeStatementData.value.expenses.reduce((s, e) => s + e.amount, 0),
)
const netIncome = computed(() => incomeTotal.value - expenseTotal.value)

const balanceSheetData = computed(() => {
  const assets: { name: string; amount: number }[] = []
  const liabilities: { name: string; amount: number }[] = []
  const equity: { name: string; amount: number }[] = []
  // 先彙算傳票（累計到選定月底，與試算表邏輯一致）
  const totals: Record<string, number> = {}
  trialVouchers.value.forEach((v) => {
    v.entries.forEach((e) => {
      if (!totals[e.accountSubject]) totals[e.accountSubject] = 0
      totals[e.accountSubject] += (e.debitAmount - e.creditAmount)
    })
  })
  // 以科目清單為基底，$0 科目也顯示
  subjects.value.forEach((s) => {
    const net = totals[String(s.id)] ?? 0
    if (s.category === 'asset') assets.push({ name: s.name, amount: net })
    else if (s.category === 'liability') liabilities.push({ name: s.name, amount: -net })
    else if (s.category === 'equity') equity.push({ name: s.name, amount: -net })
  })
  // 保留盈餘 = 累計淨利（年初到選定月底）
  let trialRevenue = 0, trialExpense = 0
  trialVouchers.value.forEach((v) => {
    v.entries.forEach((e) => {
      const cat = subjectCategoryMap.value[e.accountSubject]
      if (cat === 'revenue') trialRevenue += (e.creditAmount - e.debitAmount)
      else if (cat === 'expense') trialExpense += (e.debitAmount - e.creditAmount)
    })
  })
  equity.push({ name: '保留盈餘', amount: trialRevenue - trialExpense })
  return { assets, liabilities, equity }
})

const totalAssets = computed(
  () => balanceSheetData.value.assets.reduce((s, a) => s + a.amount, 0),
)
const totalLiabilities = computed(
  () => balanceSheetData.value.liabilities.reduce((s, l) => s + l.amount, 0),
)
const totalEquity = computed(
  () => balanceSheetData.value.equity.reduce((s, e) => s + e.amount, 0),
)

// ─── 匯出功能 ───
const reportTableRef = ref<HTMLElement | null>(null)

function exportExcel() {
  const periodLabel = selectedReportMonth.value === 0
    ? `${selectedReportYear.value}全年`
    : `${selectedReportYear.value}-${String(selectedReportMonth.value).padStart(2,'0')}`

  const wb = XLSX.utils.book_new()

  // 試算表
  const trialRows = [
    ['科目名稱', '借方餘額', '貸方餘額'],
    ...trialBalanceData.value.map((r) => [r.name, r.debit || 0, r.credit || 0]),
    ['合計',
      trialBalanceData.value.reduce((s, r) => s + r.debit, 0),
      trialBalanceData.value.reduce((s, r) => s + r.credit, 0),
    ],
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(trialRows), '試算表')

  // 損益表
  const incomeRows = [
    ['項目', '金額'],
    ['--- 收入 ---', ''],
    ...incomeStatementData.value.revenue.map((r) => [r.name, r.amount]),
    ['總收入', incomeTotal.value],
    ['--- 費用 ---', ''],
    ...incomeStatementData.value.expenses.map((e) => [e.name, e.amount]),
    ['總費用', expenseTotal.value],
    ['本期淨利', netIncome.value],
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(incomeRows), '損益表')

  // 資產負債表
  const balanceRows = [
    ['項目', '金額'],
    ['--- 資產 ---', ''],
    ...balanceSheetData.value.assets.map((a) => [a.name, a.amount]),
    ['資產合計', totalAssets.value],
    ['--- 負債 ---', ''],
    ...balanceSheetData.value.liabilities.map((l) => [l.name, l.amount]),
    ['負債合計', totalLiabilities.value],
    ['--- 投入 ---', ''],
    ...balanceSheetData.value.equity.map((e) => [e.name, e.amount]),
    ['投入合計', totalEquity.value],
    ['負債及投入總計', totalLiabilities.value + totalEquity.value],
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(balanceRows), '資產負債表')

  XLSX.writeFile(wb, `財務報表_${periodLabel}.xlsx`)
}

async function exportPDF() {
  const el = reportTableRef.value
  if (!el) return
  const canvas = await html2canvas(el, { scale: 2, backgroundColor: '#ffffff' })
  const imgData = canvas.toDataURL('image/png')
  const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' })
  const pdfW = pdf.internal.pageSize.getWidth()
  const pdfH = (canvas.height * pdfW) / canvas.width
  pdf.addImage(imgData, 'PNG', 0, 0, pdfW, pdfH)
  const periodLabel = selectedReportMonth.value === 0
    ? `${selectedReportYear.value}全年`
    : `${selectedReportYear.value}-${String(selectedReportMonth.value).padStart(2,'0')}`
  pdf.save(`財務報表_${periodLabel}.pdf`)
}

// ─── Load from API ───
onMounted(async () => {
  loading.value = true
  try {
    const [subjectsRes, vouchersRes] = await Promise.all([
      getAccountSubjects({ page_size: 1000 }).catch(() => null),
      getJournalVouchers({ page_size: 1000 }).catch(() => null),
    ])
    const subjectsData = Array.isArray(subjectsRes?.data)
      ? subjectsRes.data
      : Array.isArray(subjectsRes?.data?.results)
        ? subjectsRes.data.results
        : null
    if (subjectsData) {
      subjects.value = subjectsData.map((s: Record<string, unknown>) => ({
        id: s.id as number,
        code: s.code as string,
        name: s.name as string,
        category: s.category as string,
      }))
    }
    const vouchersData = Array.isArray(vouchersRes?.data)
      ? vouchersRes.data
      : Array.isArray(vouchersRes?.data?.results)
        ? vouchersRes.data.results
        : null
    if (vouchersData) {
      vouchers.value = vouchersData.map((v: Record<string, unknown>) => ({
        id: v.id as number,
        date: v.date as string,
        voucherNumber: v.voucher_number as string,
        description: v.description as string,
        isSystemGenerated: v.is_system_generated as boolean,
        isPosted: v.is_posted as boolean,
        entries: (v.items as Array<Record<string, unknown>>)?.map((e) => ({
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
            ? 'bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] text-white shadow-md'
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
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C] rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all duration-300"
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
                    v-for="(subject, index) in pagedSubjects"
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
            <!-- 會計科目分頁 -->
            <div class="flex items-center justify-between px-5 py-3 border-t border-slate-200 dark:border-slate-700">
              <span class="text-xs text-slate-500 dark:text-slate-400">
                共 {{ subjects.length }} 筆，第 {{ subjectPage }}/{{ subjectTotalPages }} 頁
              </span>
              <div class="flex items-center gap-1">
                <button
                  :disabled="subjectPage === 1"
                  @click="subjectPage--"
                  class="px-2.5 py-1.5 text-xs rounded-md transition-all"
                  :class="subjectPage === 1 ? 'text-slate-300 dark:text-slate-600 cursor-not-allowed' : 'text-slate-600 dark:text-slate-300 hover:bg-amber-50 dark:hover:bg-amber-900/20 hover:text-amber-600'"
                >
                  <i class="fa-solid fa-chevron-left"></i>
                </button>
                <span v-if="subjectVisiblePages[0] > 1" class="px-1 text-xs text-slate-400">…</span>
                <button
                  v-for="p in subjectVisiblePages"
                  :key="p"
                  @click="subjectPage = p"
                  class="w-7 h-7 text-xs rounded-md transition-all"
                  :class="subjectPage === p
                    ? 'bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] text-white font-semibold shadow-sm'
                    : 'text-slate-600 dark:text-slate-300 hover:bg-amber-50 dark:hover:bg-amber-900/20'"
                >{{ p }}</button>
                <span v-if="subjectVisiblePages[subjectVisiblePages.length - 1] < subjectTotalPages" class="px-1 text-xs text-slate-400">…</span>
                <button
                  :disabled="subjectPage === subjectTotalPages"
                  @click="subjectPage++"
                  class="px-2.5 py-1.5 text-xs rounded-md transition-all"
                  :class="subjectPage === subjectTotalPages ? 'text-slate-300 dark:text-slate-600 cursor-not-allowed' : 'text-slate-600 dark:text-slate-300 hover:bg-amber-50 dark:hover:bg-amber-900/20 hover:text-amber-600'"
                >
                  <i class="fa-solid fa-chevron-right"></i>
                </button>
              </div>
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
              <select
                v-model="selectedJournalMonth"
                class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-1.5"
              >
                <option v-for="m in months" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
            </div>
            <button
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C] rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all duration-300"
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
                    <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">狀態</th>
                    <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(voucher, index) in pagedVouchers"
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
                    <td class="px-5 py-3">
                      <span
                        v-if="voucher.isPosted"
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                      >
                        <i class="fa-solid fa-circle-check mr-1 text-[10px]"></i> 已入帳
                      </span>
                      <span
                        v-else
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-stone-100 dark:bg-stone-700/50 text-stone-600 dark:text-stone-300"
                      >
                        <i class="fa-regular fa-circle mr-1 text-[10px]"></i> 未入帳
                      </span>
                    </td>
                    <td class="px-5 py-3 text-right">
                      <button class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all mr-1" @click="openViewVoucher(voucher)">
                        <i class="fa-solid fa-eye"></i> 檢視
                      </button>
                      <button
                        v-if="!voucher.isSystemGenerated"
                        class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all mr-1"
                        @click="openEditVoucher(voucher)"
                      >
                        <i class="fa-solid fa-pen-to-square"></i> 編輯
                      </button>
                      <button
                        v-if="!voucher.isSystemGenerated"
                        class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-red-400 to-rose-500 hover:from-red-500 hover:to-rose-600 rounded hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all"
                        @click="deleteVoucher(voucher)"
                      >
                        <i class="fa-solid fa-trash"></i> 刪除
                      </button>
                    </td>
                  </tr>
                  <tr v-if="pagedVouchers.length === 0">
                    <td colspan="6" class="px-5 py-8 text-center text-slate-400 dark:text-slate-500">
                      {{ selectedJournalYear }} 年度無傳票資料。
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <!-- 日記帳分頁 -->
            <div class="flex items-center justify-between px-5 py-3 border-t border-slate-200 dark:border-slate-700">
              <span class="text-xs text-slate-500 dark:text-slate-400">
                共 {{ filteredVouchers.length }} 筆，第 {{ voucherPage }}/{{ voucherTotalPages }} 頁
              </span>
              <div class="flex items-center gap-1">
                <button
                  :disabled="voucherPage === 1"
                  @click="voucherPage--"
                  class="px-2.5 py-1.5 text-xs rounded-md transition-all"
                  :class="voucherPage === 1 ? 'text-slate-300 dark:text-slate-600 cursor-not-allowed' : 'text-slate-600 dark:text-slate-300 hover:bg-amber-50 dark:hover:bg-amber-900/20 hover:text-amber-600'"
                >
                  <i class="fa-solid fa-chevron-left"></i>
                </button>
                <span v-if="voucherVisiblePages[0] > 1" class="px-1 text-xs text-slate-400">…</span>
                <button
                  v-for="p in voucherVisiblePages"
                  :key="p"
                  @click="voucherPage = p"
                  class="w-7 h-7 text-xs rounded-md transition-all"
                  :class="voucherPage === p
                    ? 'bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] text-white font-semibold shadow-sm'
                    : 'text-slate-600 dark:text-slate-300 hover:bg-amber-50 dark:hover:bg-amber-900/20'"
                >{{ p }}</button>
                <span v-if="voucherVisiblePages[voucherVisiblePages.length - 1] < voucherTotalPages" class="px-1 text-xs text-slate-400">…</span>
                <button
                  :disabled="voucherPage === voucherTotalPages"
                  @click="voucherPage++"
                  class="px-2.5 py-1.5 text-xs rounded-md transition-all"
                  :class="voucherPage === voucherTotalPages ? 'text-slate-300 dark:text-slate-600 cursor-not-allowed' : 'text-slate-600 dark:text-slate-300 hover:bg-amber-50 dark:hover:bg-amber-900/20 hover:text-amber-600'"
                >
                  <i class="fa-solid fa-chevron-right"></i>
                </button>
              </div>
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
                    ? 'bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] text-white shadow-sm'
                    : 'text-slate-500 dark:text-slate-400 hover:text-amber-600'"
                  @click="activeReport = report.key"
                >
                  {{ report.label }}
                </button>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <select
                v-model="selectedReportYear"
                class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-1.5"
              >
                <option v-for="year in recentYears" :key="year" :value="year">{{ year }}</option>
              </select>
              <select
                v-model="selectedReportMonth"
                class="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-stone-200 px-3 py-1.5"
              >
                <option v-for="m in months" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
              <button
                @click="exportExcel"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all"
              >
                <i class="fa-solid fa-file-excel"></i> Excel
              </button>
              <button
                @click="exportPDF"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-red-500 to-rose-500 hover:from-red-600 hover:to-rose-600 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all"
              >
                <i class="fa-solid fa-file-pdf"></i> PDF
              </button>
            </div>
          </div>

          <div ref="reportTableRef">
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
                    <td class="px-5 py-2 font-semibold text-purple-700 dark:text-purple-400" colspan="2">投入</td>
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
                    <td class="px-5 py-2 text-purple-700 dark:text-purple-400">投入合計</td>
                    <td class="px-5 py-2 text-right font-mono text-purple-700 dark:text-purple-400">${{ totalEquity.toLocaleString() }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr class="border-t-2 border-slate-300 dark:border-slate-600 font-bold">
                    <td class="px-5 py-3 text-slate-900 dark:text-stone-50">負債及投入總計</td>
                    <td class="px-5 py-3 text-right font-mono text-slate-900 dark:text-stone-50">${{ (totalLiabilities + totalEquity).toLocaleString() }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
          </div><!-- /reportTableRef -->
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
              <button class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C] rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all" @click="saveSubject">
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
          <div class="absolute inset-0 bg-black/40"></div>
          <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-2xl mx-4 p-6 max-h-[90vh] overflow-y-auto modal-enter-active">
            <div class="flex items-center justify-between mb-5">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-stone-50">{{ editingVoucherId != null ? '編輯傳票' : '新增傳票' }}</h3>
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
                <div class="grid grid-cols-[1fr_1fr_140px_40px] gap-2 mb-1 px-1">
                  <span class="text-xs font-medium text-slate-500 dark:text-slate-400">借方科目</span>
                  <span class="text-xs font-medium text-slate-500 dark:text-slate-400">貸方科目</span>
                  <span class="text-xs font-medium text-slate-500 dark:text-slate-400 pl-[5px]">金額</span>
                  <span></span>
                </div>
                <div class="space-y-2">
                  <div
                    v-for="(pair, index) in voucherForm.pairs"
                    :key="index"
                    class="grid grid-cols-[1fr_1fr_140px_40px] gap-2 items-center"
                  >
                    <select
                      v-model="pair.debitSubject"
                      class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    >
                      <option value="" disabled>借方科目</option>
                      <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
                        {{ subject.code }} - {{ subject.name }}
                      </option>
                    </select>
                    <select
                      v-model="pair.creditSubject"
                      class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    >
                      <option value="" disabled>貸方科目</option>
                      <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
                        {{ subject.code }} - {{ subject.name }}
                      </option>
                    </select>
                    <input
                      v-model="pair.amountInput"
                      type="text"
                      inputmode="decimal"
                      placeholder="金額 (=420*2)"
                      class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-stone-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 font-mono"
                      @blur="commitAmount(pair)"
                      @keydown.enter.prevent="commitAmount(pair)"
                    />
                    <button
                      class="flex items-center justify-center w-8 h-8 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded active:scale-95 transition-all"
                      :class="voucherForm.pairs.length <= 1 ? 'opacity-30 cursor-not-allowed' : ''"
                      :disabled="voucherForm.pairs.length <= 1"
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
              <!-- Posted Flag -->
              <label class="flex items-center gap-2 px-1 cursor-pointer select-none">
                <input
                  v-model="voucherForm.isPosted"
                  type="checkbox"
                  class="w-4 h-4 rounded border-slate-300 dark:border-slate-600 text-amber-500 focus:ring-amber-500"
                />
                <span class="text-sm font-medium text-slate-700 dark:text-stone-200">已入帳</span>
                <span class="text-xs text-slate-500 dark:text-slate-400">（勾選後才會納入報表與儀表板統計）</span>
              </label>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-stone-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg active:scale-95 transition-all" @click="showVoucherModal = false">
                取消
              </button>
              <button
                class="px-4 py-2 text-sm font-medium text-white rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all"
                :class="isBalanced ? 'bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C]' : 'bg-slate-300 dark:bg-slate-600 cursor-not-allowed'"
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

    <!-- View Voucher Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showViewModal && viewingVoucher" class="fixed inset-0 z-50 flex items-center justify-center">
          <div class="absolute inset-0 bg-black/40" @click="showViewModal = false"></div>
          <div class="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-xl mx-4 p-6 modal-enter-active">
            <!-- Header -->
            <div class="flex items-center justify-between mb-5">
              <div>
                <h3 class="text-base font-semibold text-slate-900 dark:text-stone-50">{{ viewingVoucher.voucherNumber }}</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{{ viewingVoucher.date }}　{{ viewingVoucher.description }}</p>
              </div>
              <div class="flex items-center gap-2">
                <span
                  v-if="viewingVoucher.isSystemGenerated"
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                >
                  <i class="fa-solid fa-gear mr-1 text-[10px]"></i> 系統自動
                </span>
                <span
                  v-else
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                >
                  <i class="fa-solid fa-user mr-1 text-[10px]"></i> 手動
                </span>
                <button class="text-slate-400 hover:text-slate-600 dark:hover:text-stone-200 ml-1" @click="showViewModal = false">
                  <i class="fa-solid fa-xmark"></i>
                </button>
              </div>
            </div>

            <!-- Entries Table -->
            <div class="rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-800 dark:to-slate-800 border-b border-slate-200 dark:border-slate-700">
                    <th class="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 dark:text-slate-400">科目</th>
                    <th class="text-right px-4 py-2.5 text-xs font-semibold text-slate-500 dark:text-slate-400">借方</th>
                    <th class="text-right px-4 py-2.5 text-xs font-semibold text-slate-500 dark:text-slate-400">貸方</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(entry, i) in viewingVoucher.entries"
                    :key="i"
                    class="border-b border-slate-100 dark:border-slate-700/50 last:border-0"
                    :class="i % 2 === 1 ? 'bg-orange-50/30 dark:bg-gray-800/50' : ''"
                  >
                    <td class="px-4 py-2.5 text-slate-700 dark:text-stone-200">
                      {{ subjectNameMap[entry.accountSubject] || `科目#${entry.accountSubject}` }}
                    </td>
                    <td class="px-4 py-2.5 text-right font-mono text-slate-700 dark:text-stone-200">
                      {{ entry.debitAmount ? `$${Number(entry.debitAmount).toLocaleString()}` : '-' }}
                    </td>
                    <td class="px-4 py-2.5 text-right font-mono text-slate-700 dark:text-stone-200">
                      {{ entry.creditAmount ? `$${Number(entry.creditAmount).toLocaleString()}` : '-' }}
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr class="border-t-2 border-slate-300 dark:border-slate-600 font-semibold bg-slate-50 dark:bg-slate-800/80">
                    <td class="px-4 py-2.5 text-slate-700 dark:text-stone-200">合計</td>
                    <td class="px-4 py-2.5 text-right font-mono text-slate-700 dark:text-stone-200">
                      ${{ viewingVoucher.entries.reduce((s, e) => s + Number(e.debitAmount), 0).toLocaleString() }}
                    </td>
                    <td class="px-4 py-2.5 text-right font-mono text-slate-700 dark:text-stone-200">
                      ${{ viewingVoucher.entries.reduce((s, e) => s + Number(e.creditAmount), 0).toLocaleString() }}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div class="flex justify-end mt-5">
              <button
                class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-violet-600 dark:from-[#C9A47A] dark:to-[#A07848] hover:from-purple-600 hover:to-violet-700 dark:hover:from-[#B8936A] dark:hover:to-[#8F6A3C] rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 transition-all"
                @click="showViewModal = false"
              >
                關閉
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
