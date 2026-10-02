<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  getAnalyticsSummary,
  getScansOverTime,
  getByDevice,
  getByOS,
  getByBrowser,
  getByCountry,
  type ScanSummary,
  type TimeSeriesResponse,
  type BreakdownResponse,
} from '@/api/analytics'
import { listQRCodes, type QRCodeRead } from '@/api/qrcodes'

const auth = useAuthStore()

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const loadingSummary  = ref(true)
const loadingChart    = ref(true)
const loadingBreakdown = ref(true)
const loadingCountry  = ref(true)

const summary   = ref<ScanSummary | null>(null)
const timeSeries = ref<TimeSeriesResponse | null>(null)
const byDevice  = ref<BreakdownResponse | null>(null)
const byOS      = ref<BreakdownResponse | null>(null)
const byBrowser = ref<BreakdownResponse | null>(null)
const byCountry = ref<BreakdownResponse | null>(null)

// QR code filter
const qrCodes    = ref<QRCodeRead[]>([])
const selectedQR = ref<QRCodeRead | null>(null)
const granularity = ref<'day' | 'hour' | 'month'>('day')
const days        = ref(30)

const granularityOptions = [
  { label: 'By Day',   value: 'day'   },
  { label: 'By Hour',  value: 'hour'  },
  { label: 'By Month', value: 'month' },
]
const daysOptions = [
  { label: 'Last 7 days',  value: 7   },
  { label: 'Last 30 days', value: 30  },
  { label: 'Last 90 days', value: 90  },
  { label: 'Last 365 days', value: 365 },
]

// ---------------------------------------------------------------------------
// Computed QR filter param
// ---------------------------------------------------------------------------
const qrIdParam = computed(() => selectedQR.value?.id ?? undefined)

// ---------------------------------------------------------------------------
// Data loaders
// ---------------------------------------------------------------------------

async function loadSummary() {
  loadingSummary.value = true
  try {
    const { data } = await getAnalyticsSummary({ qr_id: qrIdParam.value })
    summary.value = data
  } finally {
    loadingSummary.value = false
  }
}

async function loadTimeSeries() {
  loadingChart.value = true
  try {
    const { data } = await getScansOverTime({
      granularity: granularity.value,
      days: days.value,
      qr_id: qrIdParam.value,
    })
    timeSeries.value = data
  } finally {
    loadingChart.value = false
  }
}

async function loadBreakdowns() {
  loadingBreakdown.value = true
  loadingCountry.value   = true
  try {
    const [devRes, osRes, brRes, ctRes] = await Promise.all([
      getByDevice({ qr_id: qrIdParam.value }),
      getByOS({ qr_id: qrIdParam.value }),
      getByBrowser({ qr_id: qrIdParam.value }),
      getByCountry({ qr_id: qrIdParam.value }),
    ])
    byDevice.value  = devRes.data
    byOS.value      = osRes.data
    byBrowser.value = brRes.data
    byCountry.value = ctRes.data
  } finally {
    loadingBreakdown.value = false
    loadingCountry.value   = false
  }
}

async function loadAll() {
  await Promise.all([loadSummary(), loadTimeSeries(), loadBreakdowns()])
}

onMounted(async () => {
  if (!auth.user) await auth.initialize()
  // Load QR codes for the filter dropdown
  try {
    const { data } = await listQRCodes(1, 100)
    qrCodes.value = data.items
  } catch { /* ignore */ }
  await loadAll()
})

// Re-fetch when filter changes
watch([selectedQR, granularity, days], () => loadAll())

// ---------------------------------------------------------------------------
// Chart.js data builders
// ---------------------------------------------------------------------------

const CHART_COLORS = [
  '#6366f1', '#22d3ee', '#34d399', '#f59e0b', '#f87171',
  '#a78bfa', '#fb923c', '#38bdf8', '#4ade80', '#e879f9',
]

const lineChartData = computed(() => {
  if (!timeSeries.value) return null
  return {
    labels: timeSeries.value.points.map(p => p.period),
    datasets: [
      {
        label: 'Scans',
        data: timeSeries.value.points.map(p => p.count),
        fill: true,
        tension: 0.4,
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99,102,241,0.12)',
        pointBackgroundColor: '#6366f1',
        pointRadius: timeSeries.value.points.length > 60 ? 0 : 3,
      },
    ],
  }
})

const lineChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { mode: 'index', intersect: false },
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.05)' },
      ticks: { color: '#8b93a8', maxTicksLimit: 10, maxRotation: 0 },
    },
    y: {
      beginAtZero: true,
      grid: { color: 'rgba(255,255,255,0.05)' },
      ticks: { color: '#8b93a8', precision: 0 },
    },
  },
}))

function buildDoughnut(items: BreakdownResponse['items'] | undefined) {
  if (!items?.length) return null
  return {
    labels: items.map(i => i.label),
    datasets: [
      {
        data: items.map(i => i.count),
        backgroundColor: CHART_COLORS.slice(0, items.length),
        borderWidth: 0,
        hoverOffset: 6,
      },
    ],
  }
}

const deviceChartData  = computed(() => buildDoughnut(byDevice.value?.items))
const osChartData      = computed(() => buildDoughnut(byOS.value?.items))
const browserChartData = computed(() => buildDoughnut(byBrowser.value?.items))

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '70%',
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        color: '#8b93a8',
        boxWidth: 10,
        padding: 12,
        font: { size: 11 },
      },
    },
  },
}

// ---------------------------------------------------------------------------
// Summary card definitions
// ---------------------------------------------------------------------------

const summaryCards = computed(() => [
  {
    label: 'Total Scans',
    value: summary.value?.total_scans ?? '—',
    icon: 'pi-chart-bar',
    hint: 'All-time scan events',
  },
  {
    label: 'Unique Visitors',
    value: summary.value?.unique_ips ?? '—',
    icon: 'pi-users',
    hint: 'Distinct hashed IPs',
  },
  {
    label: 'QR Codes',
    value: summary.value?.total_qr_codes ?? '—',
    icon: 'pi-qrcode',
    hint: 'Active codes',
  },
  {
    label: 'Dynamic Codes',
    value: summary.value?.dynamic_count ?? '—',
    icon: 'pi-link',
    hint: 'Trackable redirect codes',
  },
])

// ---------------------------------------------------------------------------
// Country table helpers
// ---------------------------------------------------------------------------

const countryRows = computed(() =>
  (byCountry.value?.items ?? []).map((item, idx) => ({
    rank: idx + 1,
    country: item.label,
    scans: item.count,
    pct: summary.value?.total_scans
      ? ((item.count / summary.value.total_scans) * 100).toFixed(1) + '%'
      : '—',
  }))
)

const hasData = computed(() => (summary.value?.total_scans ?? 0) > 0)
</script>

<template>
  <div class="flex flex-col gap-8">

    <!-- ── Page header ───────────────────────────────────── -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-3xl font-bold text-surface-900 dark:text-surface-0">Scan Analytics</h1>
        <p class="text-surface-500 mt-1">Track how your QR codes are performing.</p>
      </div>

      <!-- Filters -->
      <div class="flex items-center gap-2 flex-wrap">
        <!-- QR Code filter -->
        <Select
          v-model="selectedQR"
          :options="qrCodes"
          optionLabel="title"
          placeholder="All QR codes"
          show-clear
          class="text-sm"
          style="min-width: 180px"
        />
        <!-- Days -->
        <Select
          v-model="days"
          :options="daysOptions"
          optionLabel="label"
          optionValue="value"
          class="text-sm"
          style="min-width: 140px"
        />
        <!-- Granularity -->
        <SelectButton
          v-model="granularity"
          :options="granularityOptions"
          optionLabel="label"
          optionValue="value"
          class="text-sm"
        />
      </div>
    </div>

    <!-- ── Empty state ─────────────────────────────────── -->
    <div
      v-if="!loadingSummary && !hasData"
      class="flex flex-col items-center gap-4 py-20 text-center rounded-xl border"
      style="background-color: var(--bg-card); border-color: var(--border);"
    >
      <span class="text-6xl">📊</span>
      <h2 class="text-xl font-semibold text-surface-900 dark:text-surface-0">No scan data yet</h2>
      <p class="text-surface-500 max-w-sm">
        Start sharing your dynamic QR codes and scans will appear here in real-time.
      </p>
    </div>

    <template v-else>

      <!-- ── Summary cards ───────────────────────────────── -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="card in summaryCards"
          :key="card.label"
          class="p-5 rounded-xl border transition-colors duration-200"
          style="background-color: var(--bg-card); border-color: var(--border);"
        >
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm" style="color: var(--text-secondary)">{{ card.label }}</p>
              <p class="text-3xl font-bold mt-1 text-surface-900 dark:text-surface-0">
                <span v-if="loadingSummary" class="animate-pulse">…</span>
                <span v-else>{{ typeof card.value === 'number' ? card.value.toLocaleString() : card.value }}</span>
              </p>
              <p class="text-xs mt-1" style="color: var(--text-muted)">{{ card.hint }}</p>
            </div>
            <span
              class="flex items-center justify-center w-9 h-9 rounded-lg text-primary-500 dark:text-primary-400"
              style="background-color: var(--color-primary-soft)"
            >
              <i :class="`pi ${card.icon} text-base`" />
            </span>
          </div>
        </div>
      </div>

      <!-- ── Scans over time ────────────────────────────── -->
      <div
        class="p-5 rounded-xl border transition-colors duration-200"
        style="background-color: var(--bg-card); border-color: var(--border);"
      >
        <h2 class="text-base font-semibold mb-4 text-surface-900 dark:text-surface-0">
          Scans Over Time
        </h2>

        <div v-if="loadingChart" class="flex items-center justify-center h-56">
          <ProgressSpinner style="width: 40px; height: 40px" />
        </div>
        <div
          v-else-if="lineChartData && lineChartData.labels.length"
          style="height: 220px; position: relative"
        >
          <Chart type="line" :data="lineChartData" :options="lineChartOptions" />
        </div>
        <div v-else class="flex items-center justify-center h-32 text-surface-500 text-sm">
          No scan data in this period.
        </div>
      </div>

      <!-- ── Breakdown doughnuts ────────────────────────── -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- By Device -->
        <div
          class="p-5 rounded-xl border transition-colors duration-200"
          style="background-color: var(--bg-card); border-color: var(--border);"
        >
          <h2 class="text-base font-semibold mb-4 text-surface-900 dark:text-surface-0">By Device</h2>
          <div v-if="loadingBreakdown" class="flex justify-center items-center h-40">
            <ProgressSpinner style="width: 32px; height: 32px" />
          </div>
          <div v-else-if="deviceChartData" style="height: 200px; position: relative">
            <Chart type="doughnut" :data="deviceChartData" :options="doughnutOptions" />
          </div>
          <div v-else class="flex justify-center items-center h-40 text-surface-500 text-sm">
            No data
          </div>
        </div>

        <!-- By Browser -->
        <div
          class="p-5 rounded-xl border transition-colors duration-200"
          style="background-color: var(--bg-card); border-color: var(--border);"
        >
          <h2 class="text-base font-semibold mb-4 text-surface-900 dark:text-surface-0">By Browser</h2>
          <div v-if="loadingBreakdown" class="flex justify-center items-center h-40">
            <ProgressSpinner style="width: 32px; height: 32px" />
          </div>
          <div v-else-if="browserChartData" style="height: 200px; position: relative">
            <Chart type="doughnut" :data="browserChartData" :options="doughnutOptions" />
          </div>
          <div v-else class="flex justify-center items-center h-40 text-surface-500 text-sm">
            No data
          </div>
        </div>

        <!-- By OS -->
        <div
          class="p-5 rounded-xl border transition-colors duration-200"
          style="background-color: var(--bg-card); border-color: var(--border);"
        >
          <h2 class="text-base font-semibold mb-4 text-surface-900 dark:text-surface-0">By OS</h2>
          <div v-if="loadingBreakdown" class="flex justify-center items-center h-40">
            <ProgressSpinner style="width: 32px; height: 32px" />
          </div>
          <div v-else-if="osChartData" style="height: 200px; position: relative">
            <Chart type="doughnut" :data="osChartData" :options="doughnutOptions" />
          </div>
          <div v-else class="flex justify-center items-center h-40 text-surface-500 text-sm">
            No data
          </div>
        </div>
      </div>

      <!-- ── By Country table ───────────────────────────── -->
      <div
        class="rounded-xl overflow-hidden border transition-colors duration-200"
        style="background-color: var(--bg-card); border-color: var(--border);"
      >
        <div class="p-5 pb-0">
          <h2 class="text-base font-semibold text-surface-900 dark:text-surface-0">By Country</h2>
          <p class="text-xs mt-0.5 mb-4" style="color: var(--text-muted)">
            GeoIP lookup will be enabled in a future update — country data will populate once active.
          </p>
        </div>
        <DataTable
          :value="countryRows"
          :loading="loadingCountry"
          :rows="10"
          paginator
          paginator-template="FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink"
          current-page-report-template="{first}–{last} of {totalRecords}"
          striped-rows
          row-hover
          responsive-layout="scroll"
          :pt="{
            root: { style: 'background: transparent' },
            thead: { style: 'background: transparent' },
            headerRow: { style: `background-color: var(--bg-elevated); border-bottom: 1px solid var(--border);` },
            headerCell: { style: 'background: transparent; color: var(--text-secondary); font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; border: none; padding: 0.75rem 1rem;' },
            bodyRow: { style: 'background: transparent; border-bottom: 1px solid var(--border);' },
            emptyMessage: { style: 'background: transparent' },
          }"
        >
          <template #empty>
            <div class="py-10 text-center text-surface-500 text-sm">
              No country data available yet.
            </div>
          </template>

          <Column field="rank" header="#" style="width: 50px">
            <template #body="{ data }">
              <span class="font-mono text-sm" style="color: var(--text-muted)">{{ data.rank }}</span>
            </template>
          </Column>

          <Column field="country" header="Country" sortable>
            <template #body="{ data }">
              <span class="font-medium text-surface-900 dark:text-surface-0">{{ data.country }}</span>
            </template>
          </Column>

          <Column field="scans" header="Scans" sortable style="width: 110px">
            <template #body="{ data }">
              <span class="font-mono">{{ data.scans.toLocaleString() }}</span>
            </template>
          </Column>

          <Column field="pct" header="Share" style="width: 90px">
            <template #body="{ data }">
              <span style="color: var(--text-secondary)">{{ data.pct }}</span>
            </template>
          </Column>
        </DataTable>
      </div>

    </template>
  </div>
</template>
