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
    label: '總營收',
    value: '$128,430',
    change: '+12.5%',
    positive: true,
    icon: 'fa-solid fa-dollar-sign',
    changeIcon: 'fa-solid fa-arrow-up-right',
    borderColor: 'border-emerald-400',
    iconBg: 'bg-emerald-100 dark:bg-emerald-900/30',
    iconColor: 'text-emerald-500',
  },
  {
    label: '總費用',
    value: '$84,210',
    change: '+3.2%',
    positive: false,
    icon: 'fa-solid fa-receipt',
    changeIcon: 'fa-solid fa-arrow-down-left',
    borderColor: 'border-orange-400',
    iconBg: 'bg-orange-100 dark:bg-orange-900/30',
    iconColor: 'text-orange-500',
  },
  {
    label: '淨利潤',
    value: '$44,220',
    change: '+18.7%',
    positive: true,
    icon: 'fa-solid fa-chart-line',
    changeIcon: 'fa-solid fa-arrow-up-right',
    borderColor: 'border-violet-400',
    iconBg: 'bg-violet-100 dark:bg-violet-900/30',
    iconColor: 'text-violet-500',
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
  { value: 50000, name: '銷貨成本' },
  { value: 12000, name: '運費' },
  { value: 8000, name: '包裝費' },
  { value: 6000, name: '行銷費' },
  { value: 4000, name: '其他' },
])

const topProductsData = ref([
  { name: '高級狗糧 5kg', revenue: 18500, cost: 12000 },
  { name: '水族箱入門組', revenue: 14200, cost: 8800 },
  { name: '貓咪玩具鼠組', revenue: 11800, cost: 5900 },
  { name: '尼龍狗牽繩', revenue: 9600, cost: 5100 },
  { name: '鳥類綜合點心 500g', revenue: 7400, cost: 4200 },
])

// ─── ECharts Color Helpers ───
const textColor     = computed(() => themeStore.isDark ? '#F5E6D0' : '#1e293b')
const axisLineColor = computed(() => themeStore.isDark ? '#4A3225' : '#cbd5e1')
const tooltipBg     = computed(() => themeStore.isDark ? '#2E1E14' : '#ffffff')
const tooltipBorder = computed(() => themeStore.isDark ? '#7A5240' : '#e2e8f0')

// Series colours: in dark (milk-tea) mode use bright golden + cool teal so they
// stand out against warm-brown backgrounds; keep amber/slate for light mode.
const colorRevenue  = computed(() => themeStore.isDark ? '#F5C864' : '#f59e0b')
const colorExpense  = computed(() => themeStore.isDark ? '#64B8C8' : '#94a3b8')
const colorCost     = computed(() => themeStore.isDark ? '#64B8C8' : '#cbd5e1')
const pieColors     = computed(() =>
  themeStore.isDark
    ? ['#F5C864', '#E88080', '#64C8B0', '#C0A0D8', '#F0A858']
    : ['#f59e0b', '#fb923c', '#f87171', '#a8a29e', '#fbbf24']
)

// ─── Line Chart Option ───
const trendOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis' as const,
    backgroundColor: tooltipBg.value,
    borderColor: tooltipBorder.value,
    textStyle: { color: textColor.value },
  },
  legend: {
    data: ['營收', '費用'],
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
      name: '營收',
      type: 'line' as const,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: revenueData.value,
      lineStyle: { color: colorRevenue.value, width: 2 },
      itemStyle: { color: colorRevenue.value },
      areaStyle: { color: themeStore.isDark ? 'rgba(245,200,100,0.12)' : 'rgba(245,158,11,0.15)' },
    },
    {
      name: '費用',
      type: 'line' as const,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: expenseData.value,
      lineStyle: { color: colorExpense.value, width: 2 },
      itemStyle: { color: colorExpense.value },
      areaStyle: { color: themeStore.isDark ? 'rgba(100,184,200,0.12)' : 'rgba(148,163,184,0.15)' },
    },
  ],
}))

// ─── Pie (Doughnut) Chart Option ───
const expensePieOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item' as const,
    backgroundColor: tooltipBg.value,
    borderColor: tooltipBorder.value,
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
      color: pieColors.value,
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
    backgroundColor: tooltipBg.value,
    borderColor: tooltipBorder.value,
    textStyle: { color: textColor.value },
  },
  legend: {
    data: ['營收', '成本'],
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
      name: '營收',
      type: 'bar' as const,
      data: topProductRevenues.value,
      itemStyle: { color: colorRevenue.value, borderRadius: [0, 3, 3, 0] },
      barGap: '10%',
    },
    {
      name: '成本',
      type: 'bar' as const,
      data: topProductCosts.value,
      itemStyle: { color: colorCost.value, borderRadius: [0, 3, 3, 0] },
    },
  ],
}))

// ─── Journal Entries ───
const journalEntries = [
  {
    date: '2026-03-28',
    account: '商品銷售收入',
    description: '高級狗糧大量訂單',
    debit: '',
    credit: '$4,250.00',
  },
  {
    date: '2026-03-27',
    account: '銷貨成本',
    description: '貓咪玩具補貨',
    debit: '$1,820.00',
    credit: '',
  },
  {
    date: '2026-03-26',
    account: '應收帳款',
    description: '發票 #1042 - PetMart Ltd.',
    debit: '$3,600.00',
    credit: '',
  },
  {
    date: '2026-03-25',
    account: '租金費用',
    description: '每月倉庫租金',
    debit: '$2,500.00',
    credit: '',
  },
  {
    date: '2026-03-24',
    account: '商品銷售收入',
    description: '網路商店每日結算',
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
      <div class="flex flex-col items-center gap-3">
        <div class="relative w-12 h-12">
          <div class="absolute inset-0 rounded-full border-4 border-amber-200 dark:border-amber-900/40"></div>
          <div class="absolute inset-0 rounded-full border-4 border-transparent border-t-amber-500 loading-pulse"></div>
        </div>
        <span class="text-sm text-slate-500 dark:text-slate-400">載入中...</span>
      </div>
    </div>

    <template v-else>
      <!-- Metric Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="(metric, idx) in metrics"
          :key="metric.label"
          class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5 border-l-4 card-hover animate-fade-in-up opacity-0"
          :class="[metric.borderColor, `stagger-${idx + 1}`]"
        >
          <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-medium text-slate-500 dark:text-slate-400">
              {{ metric.label }}
            </span>
            <div
              class="w-9 h-9 rounded-lg flex items-center justify-center"
              :class="metric.iconBg"
            >
              <i
                :class="[metric.icon, metric.iconColor]"
                class="text-sm"
              ></i>
            </div>
          </div>

          <p class="text-2xl font-bold text-slate-900 dark:text-stone-50 mb-1 font-mono">
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
            <span class="text-slate-400 dark:text-slate-500">較上月</span>
          </div>
        </div>
      </div>

      <!-- Middle Panels -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- Revenue & Expense Trend -->
        <div
          class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5 card-hover animate-fade-in-up opacity-0 stagger-2"
        >
          <div class="flex items-center gap-2 mb-4">
            <i class="fa-solid fa-chart-area text-amber-500"></i>
            <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">
              營收與費用趨勢
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
            class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5 card-hover animate-fade-in-up opacity-0 stagger-3"
          >
            <div class="flex items-center gap-2 mb-4">
              <i class="fa-solid fa-chart-pie text-amber-500"></i>
              <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">
                費用結構分析
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
            class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5 card-hover animate-fade-in-up opacity-0 stagger-4"
          >
            <div class="flex items-center gap-2 mb-4">
              <i class="fa-solid fa-ranking-star text-amber-500"></i>
              <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">
                熱銷商品毛利排行
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
        class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm card-hover animate-fade-in-up opacity-0 stagger-4"
      >
        <div class="flex items-center gap-2 px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <i class="fa-solid fa-book text-amber-500"></i>
          <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">
            最近傳票記錄
          </h2>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700">
                <th
                  class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  日期
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  科目
                </th>
                <th
                  class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  摘要
                </th>
                <th
                  class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  借方
                </th>
                <th
                  class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  貸方
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(entry, index) in journalEntries"
                :key="index"
                class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-all duration-200 hover:translate-x-1"
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
