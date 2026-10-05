<script setup lang="ts">
/**
 * AdminMonitorView – Real-time Celery / RabbitMQ monitoring dashboard.
 *
 * Uses Chart.js (already a project dependency) rendered into canvas elements
 * that are updated in-place on every WebSocket frame.  Updating chart.data
 * directly and calling chart.update('none') avoids full re-renders and keeps
 * the animation budget sensible at 3-second intervals.
 */
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import {
  Chart,
  LineElement,
  PointElement,
  LineController,
  CategoryScale,
  LinearScale,
  Filler,
  Legend,
  Tooltip,
  DoughnutController,
  ArcElement,
  type ChartOptions,
  type ChartData,
} from 'chart.js'
import { useQueueMetrics } from '@/composables/useQueueMetrics'
import { useThemeStore } from '@/stores/theme'

// Register only what we use (tree-shake Chart.js)
Chart.register(
  LineElement,
  PointElement,
  LineController,
  CategoryScale,
  LinearScale,
  Filler,
  Legend,
  Tooltip,
  DoughnutController,
  ArcElement,
)

const theme = useThemeStore()

// ── Composable ────────────────────────────────────────────────────────────────
const {
  isConnected,
  wsStatus,
  lastError,
  latest,
  lineChartData,
  doughnutChartData,
  celeryStats,
  jobStats,
  totalJobsEver,
  successRate,
} = useQueueMetrics()

// ── Canvas refs ───────────────────────────────────────────────────────────────
const lineCanvas = ref<HTMLCanvasElement | null>(null)
const doughnutCanvas = ref<HTMLCanvasElement | null>(null)

let lineChart: Chart | null = null
let doughnutChart: Chart | null = null

// ── Chart helpers ─────────────────────────────────────────────────────────────

function gridColor() {
  return theme.isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'
}
function tickColor() {
  return theme.isDark ? '#94a3b8' : '#64748b'
}

function buildLineOptions(): ChartOptions<'line'> {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,          // disable all animations for perf at high freq
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: tickColor(),
          font: { size: 11 },
          boxWidth: 12,
          padding: 12,
          // Only show "ready" entries by default (halves legend clutter)
          filter: (item) => item.text?.includes('ready') ?? true,
        },
      },
      tooltip: {
        callbacks: {
          title: (items) => items[0]?.label ?? '',
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: tickColor(),
          maxTicksLimit: 8,
          maxRotation: 0,
          font: { size: 10 },
        },
        grid: { color: gridColor() },
      },
      y: {
        beginAtZero: true,
        ticks: {
          color: tickColor(),
          precision: 0,
          font: { size: 10 },
        },
        grid: { color: gridColor() },
      },
    },
  }
}

function buildDoughnutOptions(): ChartOptions<'doughnut'> {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    cutout: '68%',
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: tickColor(),
          font: { size: 11 },
          boxWidth: 12,
          padding: 12,
        },
      },
    },
  }
}

function initCharts() {
  if (lineCanvas.value) {
    lineChart = new Chart(lineCanvas.value, {
      type: 'line',
      data: lineChartData.value as ChartData<'line'>,
      options: buildLineOptions(),
    })
  }
  if (doughnutCanvas.value) {
    doughnutChart = new Chart(doughnutCanvas.value, {
      type: 'doughnut',
      data: doughnutChartData.value as ChartData<'doughnut'>,
      options: buildDoughnutOptions(),
    })
  }
}

function destroyCharts() {
  lineChart?.destroy()
  doughnutChart?.destroy()
  lineChart = null
  doughnutChart = null
}

// ── Reactive update loop ──────────────────────────────────────────────────────
// Watch the chart-ready data refs and push mutations directly into the Chart
// instances.  This avoids Vue re-rendering the whole component on every frame.

watch(lineChartData, (next) => {
  if (!lineChart) return
  // Mutate in place – Chart.js watches references, not deep content
  lineChart.data.labels = next.labels
  lineChart.data.datasets = next.datasets as never
  // 'none' skips the easing animation; the chart still redraws immediately
  lineChart.update('none')
})

watch(doughnutChartData, (next) => {
  if (!doughnutChart) return
  doughnutChart.data.labels = next.labels
  doughnutChart.data.datasets = next.datasets as never
  doughnutChart.update('none')
})

// Re-apply theme-sensitive colours when theme toggles
watch(() => theme.isDark, () => {
  if (!lineChart || !doughnutChart) return
  lineChart.options = buildLineOptions()
  doughnutChart.options = buildDoughnutOptions()
  lineChart.update('none')
  doughnutChart.update('none')
})

onMounted(async () => {
  await nextTick()
  initCharts()
})

onUnmounted(() => {
  destroyCharts()
})
</script>

<template>
  <div class="monitor-view">
    <!-- ── Header ──────────────────────────────────────────────────────── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Queue Monitor</h1>
        <p class="page-subtitle">Real-time Celery &amp; RabbitMQ telemetry via WebSocket</p>
      </div>

      <!-- Connection status badge -->
      <div class="status-badge" :class="isConnected ? 'badge-live' : 'badge-offline'">
        <span class="status-dot" />
        {{ isConnected ? 'Live' : wsStatus === 'CONNECTING' ? 'Connecting…' : 'Offline' }}
      </div>
    </div>

    <!-- ── Error banner ─────────────────────────────────────────────────── -->
    <Message v-if="lastError" severity="warn" :closable="false" class="error-msg">
      {{ lastError }}
    </Message>

    <!-- ── KPI strip – Live workers (instantaneous) ──────────────────── -->
    <p class="kpi-section-label">Live Workers</p>
    <div class="kpi-strip">
      <div class="kpi-card">
        <p class="kpi-label">Active Tasks</p>
        <p class="kpi-value kpi-active">{{ celeryStats.active }}</p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">Reserved</p>
        <p class="kpi-value kpi-reserved">{{ celeryStats.reserved }}</p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">Scheduled</p>
        <p class="kpi-value kpi-scheduled">{{ celeryStats.scheduled }}</p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">Revoked</p>
        <p class="kpi-value kpi-revoked">{{ celeryStats.revoked }}</p>
      </div>
      <div class="kpi-card kpi-wide">
        <p class="kpi-label">Last update</p>
        <p class="kpi-value kpi-ts">
          {{ latest ? new Date(latest.ts).toLocaleTimeString() : '—' }}
        </p>
      </div>
    </div>

    <!-- ── KPI strip – Job history (cumulative DB counts) ────────────── -->
    <p class="kpi-section-label">Job History</p>
    <div class="kpi-strip">
      <div class="kpi-card">
        <p class="kpi-label">Total Jobs</p>
        <p class="kpi-value">{{ totalJobsEver }}</p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">Completed</p>
        <p class="kpi-value kpi-scheduled">{{ jobStats.completed }}</p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">Failed</p>
        <p class="kpi-value kpi-revoked">{{ jobStats.failed }}</p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">In Progress</p>
        <p class="kpi-value kpi-active">{{ jobStats.processing + jobStats.pending }}</p>
      </div>
      <div class="kpi-card kpi-wide">
        <p class="kpi-label">Success Rate</p>
        <p class="kpi-value kpi-scheduled">
          {{ successRate !== null ? `${successRate}%` : '—' }}
        </p>
      </div>
    </div>

    <!-- ── Charts ─────────────────────────────────────────────────────────── -->
    <div class="charts-grid">
      <!-- Line chart: queue depth over time -->
      <div class="chart-card chart-card--line">
        <div class="chart-header">
          <h2 class="chart-title">Queue Depth Over Time</h2>
          <span class="chart-hint">Ready (solid) · Unacked (dashed)</span>
        </div>
        <div class="chart-body">
          <canvas ref="lineCanvas" />
        </div>
      </div>

      <!-- Doughnut chart: cumulative job status breakdown -->
      <div class="chart-card chart-card--donut">
        <div class="chart-header">
          <h2 class="chart-title">Job Status Breakdown</h2>
          <span class="chart-hint">{{ totalJobsEver }} total · all time</span>
        </div>
        <div class="chart-body">
          <canvas ref="doughnutCanvas" />
        </div>
      </div>
    </div>

    <!-- ── Queue table ─────────────────────────────────────────────────────── -->
    <div class="table-card">
      <h2 class="chart-title" style="padding: 1rem 1rem 0.5rem">Queue Snapshot</h2>
      <DataTable
        :value="latest?.queues ?? []"
        size="small"
        stripedRows
        class="queues-table"
      >
        <Column field="name" header="Queue" style="min-width: 160px" />
        <Column field="ready" header="Ready" style="width: 120px">
          <template #body="{ data }">
            <Tag :value="String(data.ready)" severity="info" />
          </template>
        </Column>
        <Column field="unacked" header="Unacked" style="width: 120px">
          <template #body="{ data }">
            <Tag
              :value="String(data.unacked)"
              :severity="data.unacked > 0 ? 'warn' : 'secondary'"
            />
          </template>
        </Column>
        <Column field="total" header="Total" style="width: 120px">
          <template #body="{ data }">
            <Tag :value="String(data.total)" severity="secondary" />
          </template>
        </Column>
        <template #empty>
          <div class="empty-state">
            <i class="pi pi-wifi empty-icon" />
            <p>{{ isConnected ? 'No queues found' : 'Awaiting connection…' }}</p>
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.monitor-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1.5rem;
  gap: 1.25rem;
  overflow-y: auto;
}

/* ── Header ──────────────────────────────────────────────────────────────── */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.page-title {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0;
}

/* ── Status badge ────────────────────────────────────────────────────────── */
.status-badge {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  font-size: 0.8125rem;
  font-weight: 600;
  white-space: nowrap;
}

.badge-live {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.badge-offline {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

/* Live pulse animation */
.badge-live .status-dot {
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.7); }
}

/* ── Error message ────────────────────────────────────────────────────────── */
.error-msg { margin: 0; }

/* ── KPI strip ────────────────────────────────────────────────────────────── */
.kpi-section-label {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}

.kpi-strip {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.kpi-card {
  flex: 1;
  min-width: 120px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.875rem 1rem;
}

.kpi-wide { min-width: 160px; }

.kpi-label {
  margin: 0 0 0.25rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.kpi-value {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1;
}

.kpi-active    { color: #6366f1; }
.kpi-reserved  { color: #f59e0b; }
.kpi-scheduled { color: #10b981; }
.kpi-revoked   { color: #ef4444; }
.kpi-ts        { font-size: 1rem; color: var(--text-secondary); }

/* ── Charts grid ──────────────────────────────────────────────────────────── */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 1rem;
}

@media (max-width: 900px) {
  .charts-grid { grid-template-columns: 1fr; }
}

.chart-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chart-header {
  padding: 0.875rem 1rem 0.5rem;
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.chart-title {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.chart-body {
  position: relative;
  flex: 1;
  min-height: 220px;
  padding: 0 0.75rem 0.875rem;
}

.chart-card--donut .chart-body {
  min-height: 240px;
}

/* ── Queue table ──────────────────────────────────────────────────────────── */
.table-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
}

.queues-table {
  width: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 1.75rem;
  opacity: 0.4;
}
</style>
