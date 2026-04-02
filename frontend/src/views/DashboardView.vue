<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useThemeStore } from '@/stores/theme'
import { getSummary, getMonthlyTrend, getExpenseBreakdown, getTopProducts } from '@/api/dashboard'

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

const themeStore = useThemeStore()
const loading = ref(false)

// ─── Metrics ───
const metrics = ref([
  {
    label: 'Total Revenue',
    value: '$128,430',
    change: '+12.5%',
    positive: true,
    icon: 'fa-solid fa-dollar-sign',
    changeIcon: 'fa-solid fa-arrow-up-right',
  },
  {
    label: 'Total Expenses',
    value: '$84,210',
    change: '+3.2%',
    positive: false,
    icon: 'fa-solid fa-receipt',
    changeIcon: 'fa-solid fa-arrow-down-left',
  },
  {
    label: 'Net Profit',
    value: '$44,220',
    change: '+18.7%',
    positive: true,
    icon: 'fa-solid fa-chart-line',
    changeIcon: 'fa-solid fa-arrow-up-right',
  },
])

// ─── Mock Data for Charts ───
const monthLabels = [
  'Apr 25', 'May 25', 'Jun 25', 'Jul 25', 'Aug 25', 'Sep 25',
  'Oct 25', 'Nov 25', 'Dec 25', 'Jan 26', 'Feb 26', 'Mar 26',
]
const revenueData = ref([12400, 15200, 13800, 16500, 14200, 18300, 17100, 19800, 15600, 20100, 16800, 18900])
const expenseData = ref([8200, 9100, 7800, 10200, 8600, 11400, 9800, 11200, 8900, 12000, 9500, 10800])

const expenseBreakdownData = ref([
  { value: 50000, name: 'COGS' },
  { value: 12000, name: 'Shipping' },
  { value: 8000, name: 'Packaging' },
  { value: 6000, name: 'Marketing' },
  { value: 4000, name: 'Other' },
])

const topProductsData = ref([
  { name: 'Premium Dog Food 5kg', revenue: 18500, cost: 12000 },
  { name: 'Aquarium Starter Kit', revenue: 14200, cost: 8800 },
  { name: 'Cat Toy Mouse Set', revenue: 11800, cost: 5900 },
  { name: 'Dog Leash Nylon', revenue: 9600, cost: 5100 },
  { name: 'Bird Treat Mix 500g', revenue: 7400, cost: 4200 },
])

// ─── ECharts Color Helpers ───
const textColor = computed(() => themeStore.isDark ? '#e7e5e4' : '#1e293b')
const axisLineColor = computed(() => themeStore.isDark ? '#475569' : '#cbd5e1')

// ─── Line Chart Option ───
const trendOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis' as const,
    backgroundColor: themeStore.isDark ? '#1e293b' : '#fff',
    borderColor: themeStore.isDark ? '#475569' : '#e2e8f0',
    textStyle: { color: textColor.value },
  },
  legend: {
    data: ['Revenue', 'Expenses'],
    top: 0,
    textStyle: { color: textColor.value },
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true,
  },
  xAxis: {
    type: 'category' as const,
    boundaryGap: false,
    data: monthLabels,
    axisLabel: { color: textColor.value, fontSize: 11 },
    axisLine: { lineStyle: { color: axisLineColor.value } },
  },
  yAxis: {
    type: 'value' as const,
    axisLabel: {
      color: textColor.value,
      fontSize: 11,
      formatter: (v: number) => `$${(v / 1000).toFixed(0)}k`,
    },
    splitLine: { lineStyle: { color: axisLineColor.value, type: 'dashed' as const } },
  },
  series: [
    {
      name: 'Revenue',
      type: 'line' as const,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: revenueData.value,
      lineStyle: { color: '#f59e0b', width: 2 },
      itemStyle: { color: '#f59e0b' },
      areaStyle: { color: 'rgba(245, 158, 11, 0.15)' },
    },
    {
      name: 'Expenses',
      type: 'line' as const,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: expenseData.value,
      lineStyle: { color: '#94a3b8', width: 2 },
      itemStyle: { color: '#94a3b8' },
      areaStyle: { color: 'rgba(148, 163, 184, 0.15)' },
    },
  ],
}))

// ─── Pie (Doughnut) Chart Option ───
const expensePieOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item' as const,
    backgroundColor: themeStore.isDark ? '#1e293b' : '#fff',
    borderColor: themeStore.isDark ? '#475569' : '#e2e8f0',
    textStyle: { color: textColor.value },
    formatter: '{b}: ${c} ({d}%)',
  },
  legend: {
    orient: 'vertical' as const,
    right: 10,
    top: 'center' as const,
    textStyle: { color: textColor.value, fontSize: 11 },
  },
  series: [
    {
      type: 'pie' as const,
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      label: {
        show: true,
        formatter: '{d}%',
        color: textColor.value,
        fontSize: 11,
      },
      data: expenseBreakdownData.value,
      color: ['#f59e0b', '#fb923c', '#f87171', '#a8a29e', '#fbbf24'],
    },
  ],
}))

// ─── Horizontal Bar Chart Option ───
const topProductNames = computed(() => topProductsData.value.map((p) => p.name).reverse())
const topProductRevenues = computed(() => topProductsData.value.map((p) => p.revenue).reverse())
const topProductCosts = computed(() => topProductsData.value.map((p) => p.cost).reverse())

const barOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis' as const,
    axisPointer: { type: 'shadow' as const },
    backgroundColor: themeStore.isDark ? '#1e293b' : '#fff',
    borderColor: themeStore.isDark ? '#475569' : '#e2e8f0',
    textStyle: { color: textColor.value },
  },
  legend: {
    data: ['Revenue', 'Cost'],
    top: 0,
    textStyle: { color: textColor.value, fontSize: 11 },
  },
  grid: {
    left: '3%',
    right: '8%',
    bottom: '3%',
    containLabel: true,
  },
  xAxis: {
    type: 'value' as const,
    axisLabel: {
      color: textColor.value,
      fontSize: 11,
      formatter: (v: number) => `$${(v / 1000).toFixed(0)}k`,
    },
    splitLine: { lineStyle: { color: axisLineColor.value, type: 'dashed' as const } },
  },
  yAxis: {
    type: 'category' as const,
    data: topProductNames.value,
    axisLabel: { color: textColor.value, fontSize: 11 },
    axisLine: { lineStyle: { color: axisLineColor.value } },
  },
  series: [
    {
      name: 'Revenue',
      type: 'bar' as const,
      data: topProductRevenues.value,
      itemStyle: { color: '#f59e0b', borderRadius: [0, 3, 3, 0] },
      barGap: '10%',
    },
    {
      name: 'Cost',
      type: 'bar' as const,
      data: topProductCosts.value,
      itemStyle: { color: '#cbd5e1', borderRadius: [0, 3, 3, 0] },
    },
  ],
}))

// ─── Journal Entries ───
const journalEntries = [
  {
    date: '2026-03-28',
    account: 'Sales Revenue',
    description: 'Premium dog food bulk order',
    debit: '',
    credit: '$4,250.00',
  },
  {
    date: '2026-03-27',
    account: 'Cost of Goods Sold',
    description: 'Inventory restock - cat toys',
    debit: '$1,820.00',
    credit: '',
  },
  {
    date: '2026-03-26',
    account: 'Accounts Receivable',
    description: 'Invoice #1042 - PetMart Ltd.',
    debit: '$3,600.00',
    credit: '',
  },
  {
    date: '2026-03-25',
    account: 'Rent Expense',
    description: 'Monthly warehouse rental',
    debit: '$2,500.00',
    credit: '',
  },
  {
    date: '2026-03-24',
    account: 'Sales Revenue',
    description: 'Online store daily settlement',
    debit: '',
    credit: '$6,780.00',
  },
]

// ─── Load from API ───
onMounted(async () => {
  loading.value = true
  try {
    const [summaryRes, trendRes, breakdownRes, productsRes] = await Promise.all([
      getSummary().catch(() => null),
      getMonthlyTrend().catch(() => null),
      getExpenseBreakdown().catch(() => null),
      getTopProducts().catch(() => null),
    ])
    if (summaryRes?.data) {
      const d = summaryRes.data
      if (d.total_revenue != null) metrics.value[0].value = `$${Number(d.total_revenue).toLocaleString()}`
      if (d.total_expenses != null) metrics.value[1].value = `$${Number(d.total_expenses).toLocaleString()}`
      if (d.net_profit != null) metrics.value[2].value = `$${Number(d.net_profit).toLocaleString()}`
    }
    if (trendRes?.data) {
      if (trendRes.data.revenue) revenueData.value = trendRes.data.revenue
      if (trendRes.data.expenses) expenseData.value = trendRes.data.expenses
    }
    if (breakdownRes?.data?.labels && breakdownRes.data.values) {
      expenseBreakdownData.value = breakdownRes.data.labels.map((name: string, i: number) => ({
        value: breakdownRes.data.values[i],
        name,
      }))
    }
    if (productsRes?.data?.products) {
      topProductsData.value = productsRes.data.products.map((p: any) => ({
        name: p.name,
        revenue: p.revenue,
        cost: p.cost,
      }))
    }
  } catch (e) {
    console.warn('Dashboard API unavailable, using fallback data', e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Loading Overlay -->
    <div
      v-if="loading"
      class="flex items-center justify-center py-12"
    >
      <i class="fa-solid fa-spinner fa-spin text-2xl text-amber-500"></i>
    </div>

    <template v-else>
      <!-- Metric Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="metric in metrics"
          :key="metric.label"
          class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5"
        >
          <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-medium text-slate-500 dark:text-slate-400">
              {{ metric.label }}
            </span>
            <div
              class="w-9 h-9 rounded-lg flex items-center justify-center"
              :class="
                metric.positive
                  ? 'bg-emerald-50 dark:bg-emerald-900/30'
                  : 'bg-red-50 dark:bg-red-900/30'
              "
            >
              <i
                :class="metric.icon"
                class="text-sm"
                :style="{
                  color: metric.positive ? 'rgb(16 185 129)' : 'rgb(239 68 68)',
                }"
              ></i>
            </div>
          </div>

          <p class="text-2xl font-bold text-slate-900 dark:text-stone-50 mb-1">
            {{ metric.value }}
          </p>

          <div class="flex items-center gap-1 text-sm">
            <i
              :class="metric.changeIcon"
              class="text-xs"
              :style="{
                color: metric.positive ? 'rgb(16 185 129)' : 'rgb(239 68 68)',
              }"
            ></i>
            <span
              :class="
                metric.positive
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-red-600 dark:text-red-400'
              "
            >
              {{ metric.change }}
            </span>
            <span class="text-slate-400 dark:text-slate-500">vs last month</span>
          </div>
        </div>
      </div>

      <!-- Middle Panels -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- Revenue & Expense Trend -->
        <div
          class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5"
        >
          <div class="flex items-center gap-2 mb-4">
            <i class="fa-solid fa-chart-area text-amber-500"></i>
            <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">
              Revenue &amp; Expense Trend
            </h2>
          </div>
          <v-chart
            class="h-80 w-full"
            :option="trendOption"
            autoresize
          />
        </div>

        <!-- Right Panel: Pie + Bar -->
        <div class="flex flex-col gap-4">
          <!-- Expense Breakdown Doughnut -->
          <div
            class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5"
          >
            <div class="flex items-center gap-2 mb-4">
              <i class="fa-solid fa-chart-pie text-amber-500"></i>
              <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">
                Expense Breakdown
              </h2>
            </div>
            <v-chart
              class="h-48 w-full"
              :option="expensePieOption"
              autoresize
            />
          </div>

          <!-- Top Products Bar -->
          <div
            class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5"
          >
            <div class="flex items-center gap-2 mb-4">
              <i class="fa-solid fa-ranking-star text-amber-500"></i>
              <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">
                Top Products by Gross Profit
              </h2>
            </div>
            <v-chart
              class="h-48 w-full"
              :option="barOption"
              autoresize
            />
          </div>
        </div>
      </div>

      <!-- Recent Journal Entries -->
      <div
        class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm"
      >
        <div class="flex items-center gap-2 px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <i class="fa-solid fa-book text-amber-500"></i>
          <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">
            Recent Journal Entries
          </h2>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700">
                <th
                  class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Date
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Account
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Description
                </th>
                <th
                  class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Debit
                </th>
                <th
                  class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Credit
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(entry, index) in journalEntries"
                :key="index"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                :class="index % 2 === 1 ? 'bg-slate-50/50 dark:bg-slate-800/30' : ''"
              >
                <td class="px-5 py-3 text-slate-600 dark:text-slate-300 font-mono text-xs">
                  {{ entry.date }}
                </td>
                <td class="px-5 py-3 font-medium text-slate-700 dark:text-stone-200">
                  {{ entry.account }}
                </td>
                <td class="px-5 py-3 text-slate-500 dark:text-slate-400">
                  {{ entry.description }}
                </td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">
                  {{ entry.debit || '-' }}
                </td>
                <td class="px-5 py-3 text-right font-mono text-slate-700 dark:text-stone-200">
                  {{ entry.credit || '-' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
