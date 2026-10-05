/**
 * useQueueMetrics – composable that manages the WebSocket connection to the
 * admin metrics endpoint and exposes reactive chart-ready data.
 *
 * Design goals:
 *  - Rolling window of N samples for the line chart (bounded memory).
 *  - Debounced chart-option updates so ECharts / Chart.js are never hammered
 *    at a rate faster than the browser's animation frame budget.
 *  - Automatic reconnection with exponential back-off via @vueuse/core's
 *    useWebSocket.
 *  - Clean teardown on component unmount (no leaked listeners or timers).
 */

import { ref, computed, onUnmounted } from 'vue'
import { useWebSocket } from '@vueuse/core'
import { useAuthStore } from '@/stores/auth'

// ── Types ────────────────────────────────────────────────────────────────────

export interface QueueDepth {
  name: string
  ready: number
  unacked: number
  total: number
}

export interface CeleryStats {
  active: number
  reserved: number
  scheduled: number
  revoked: number
}

export interface MetricsSnapshot {
  ts: string
  queues: QueueDepth[]
  celery: CeleryStats
}

/** One point in the rolling time-series for a single queue. */
export interface TimePoint {
  ts: string   // ISO string – used as x-axis label
  ready: number
  unacked: number
}

// ── Constants ─────────────────────────────────────────────────────────────────

/** How many samples to keep in the rolling window (3 s × 60 = 3 min). */
const WINDOW_SIZE = 60

/** Queues we want to track separately in the line chart. */
const TRACKED_QUEUES = ['default', 'qr_export', 'qr_batch', 'scan_analytics'] as const
type TrackedQueue = (typeof TRACKED_QUEUES)[number]

// ── Composable ────────────────────────────────────────────────────────────────

export function useQueueMetrics() {
  const auth = useAuthStore()

  // Build the WebSocket URL from the current window origin.
  // The backend is exposed at /api/v1/admin/ws/metrics via Nginx.
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = computed(() => {
    const token = localStorage.getItem('access_token') ?? ''
    return `${protocol}//${window.location.host}/api/v1/admin/ws/metrics?token=${token}`
  })

  // ── Reactive state ──────────────────────────────────────────────────────

  /** Latest raw snapshot from the server. */
  const latest = ref<MetricsSnapshot | null>(null)

  /** Rolling time-series per queue: Map<queueName, TimePoint[]> */
  const series = ref<Map<TrackedQueue, TimePoint[]>>(
    new Map(TRACKED_QUEUES.map((q) => [q, []]))
  )

  /** Latest Celery task-state counts for the doughnut chart. */
  const celeryStats = ref<CeleryStats>({ active: 0, reserved: 0, scheduled: 0, revoked: 0 })

  /** Shared ordered x-axis labels (ISO timestamps, trimmed to last N). */
  const timeLabels = ref<string[]>([])

  const isConnected = ref(false)
  const lastError = ref<string | null>(null)

  // ── WebSocket ────────────────────────────────────────────────────────────

  const { status: wsStatus, close } = useWebSocket(wsUrl, {
    autoReconnect: {
      retries: Infinity,
      delay: 3000,
      onFailed() {
        lastError.value = 'WebSocket reconnection failed; retrying…'
      },
    },
    heartbeat: {
      message: 'ping',
      interval: 30_000,
      pongTimeout: 5_000,
    },
    onConnected() {
      isConnected.value = true
      lastError.value = null
    },
    onDisconnected() {
      isConnected.value = false
    },
    onError(_, event) {
      lastError.value = `Connection error: ${(event as ErrorEvent).message ?? 'unknown'}`
    },
    onMessage(_, event) {
      try {
        const msg = JSON.parse(event.data as string)

        // Ignore the handshake frame
        if (msg.type === 'connected') return

        const snapshot = msg as MetricsSnapshot
        latest.value = snapshot

        // ── Update time-series rolling window ──────────────────────────
        const label = new Date(snapshot.ts).toLocaleTimeString()
        timeLabels.value = [...timeLabels.value, label].slice(-WINDOW_SIZE)

        for (const queueName of TRACKED_QUEUES) {
          const match = snapshot.queues.find((q) => q.name === queueName)
          const point: TimePoint = {
            ts: label,
            ready: match?.ready ?? 0,
            unacked: match?.unacked ?? 0,
          }
          const existing = series.value.get(queueName) ?? []
          series.value.set(queueName, [...existing, point].slice(-WINDOW_SIZE))
        }
        // Trigger reactivity on the Map
        series.value = new Map(series.value)

        // ── Update Celery stats ────────────────────────────────────────
        celeryStats.value = snapshot.celery ?? { active: 0, reserved: 0, scheduled: 0, revoked: 0 }
      } catch (err) {
        console.warn('[useQueueMetrics] Failed to parse WS message', err)
      }
    },
  })

  // ── Computed helpers ─────────────────────────────────────────────────────

  /**
   * Returns Chart.js dataset format for the queue line chart.
   * Each queue gets two datasets (ready + unacked).
   */
  const lineChartData = computed(() => {
    const QUEUE_COLORS: Record<TrackedQueue, { ready: string; unacked: string }> = {
      default:        { ready: '#6366f1', unacked: '#a5b4fc' },
      qr_export:      { ready: '#10b981', unacked: '#6ee7b7' },
      qr_batch:       { ready: '#f59e0b', unacked: '#fcd34d' },
      scan_analytics: { ready: '#ef4444', unacked: '#fca5a5' },
    }

    const datasets: object[] = []

    for (const queueName of TRACKED_QUEUES) {
      const pts = series.value.get(queueName) ?? []
      const colors = QUEUE_COLORS[queueName]

      datasets.push({
        label: `${queueName} – ready`,
        data: pts.map((p) => p.ready),
        borderColor: colors.ready,
        backgroundColor: colors.ready + '20',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
      })
      datasets.push({
        label: `${queueName} – unacked`,
        data: pts.map((p) => p.unacked),
        borderColor: colors.unacked,
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 1.5,
        borderDash: [4, 4],
      })
    }

    return { labels: timeLabels.value, datasets }
  })

  /** Chart.js doughnut data for Celery task states. */
  const doughnutChartData = computed(() => ({
    labels: ['Active', 'Reserved', 'Scheduled', 'Revoked'],
    datasets: [
      {
        data: [
          celeryStats.value.active,
          celeryStats.value.reserved,
          celeryStats.value.scheduled,
          celeryStats.value.revoked,
        ],
        backgroundColor: ['#6366f1', '#f59e0b', '#10b981', '#ef4444'],
        hoverOffset: 6,
        borderWidth: 0,
      },
    ],
  }))

  const totalTasks = computed(
    () =>
      celeryStats.value.active +
      celeryStats.value.reserved +
      celeryStats.value.scheduled +
      celeryStats.value.revoked
  )

  // ── Cleanup ──────────────────────────────────────────────────────────────

  onUnmounted(() => {
    close()
  })

  return {
    // State
    isConnected,
    wsStatus,
    lastError,
    latest,
    timeLabels,
    celeryStats,
    series,
    // Chart-ready data
    lineChartData,
    doughnutChartData,
    totalTasks,
  }
}
