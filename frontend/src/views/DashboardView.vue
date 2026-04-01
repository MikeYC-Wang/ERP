<script setup lang="ts">
const metrics = [
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
]

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
</script>

<template>
  <div class="space-y-6">
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
        <div
          class="h-64 flex items-center justify-center rounded-lg bg-slate-50 dark:bg-slate-800 border border-dashed border-slate-300 dark:border-slate-600"
        >
          <div class="text-center text-slate-400 dark:text-slate-500">
            <i class="fa-solid fa-chart-line text-3xl mb-2"></i>
            <p class="text-sm">ECharts container</p>
            <p class="text-xs">Chart will be rendered here</p>
          </div>
        </div>
      </div>

      <!-- 3D Interactive View -->
      <div
        class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-5"
      >
        <div class="flex items-center gap-2 mb-4">
          <i class="fa-solid fa-cube text-amber-500"></i>
          <h2 class="text-sm font-semibold text-slate-700 dark:text-stone-200">
            3D Interactive View
          </h2>
        </div>
        <div
          class="h-64 flex items-center justify-center rounded-lg bg-slate-50 dark:bg-slate-800 border border-dashed border-slate-300 dark:border-slate-600"
        >
          <div class="text-center text-slate-400 dark:text-slate-500">
            <i class="fa-solid fa-cubes text-3xl mb-2"></i>
            <p class="text-sm">Spline 3D container</p>
            <p class="text-xs">3D scene will be rendered here</p>
          </div>
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
  </div>
</template>
