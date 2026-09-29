<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import QRCodeStyling from 'qr-code-styling'
import { useQREditorStore } from '@/stores/qrEditor'
import { exportQRCode, startAsyncExport, getExportJob } from '@/api/qrcodes'

const store = useQREditorStore()
const toast = useToast()
const canvasRef = ref<HTMLDivElement>()
const isExporting = ref(false)
const exportError = ref<string | null>(null)

let qrInstance: QRCodeStyling | null = null
let debounceTimer: ReturnType<typeof setTimeout> | null = null
let pollInterval: ReturnType<typeof setInterval> | null = null

/** Build the options object that qr-code-styling expects. */
function buildOptions() {
  const cfg = store.designConfig
  return {
    width: 300,
    height: 300,
    data: cfg.content || 'https://pointqr.app',
    margin: cfg.margin,
    qrOptions: cfg.qrOptions,
    dotsOptions: cfg.dotsOptions,
    backgroundOptions: cfg.backgroundOptions,
    cornersSquareOptions: cfg.cornersSquareOptions,
    cornersDotOptions: cfg.cornersDotOptions,
    // Only pass image prop when a src is set
    ...(cfg.imageOptions.src
      ? {
          image: cfg.imageOptions.src,
          imageOptions: {
            margin: cfg.imageOptions.margin,
            imageSize: cfg.imageOptions.imageSize,
            hideBackgroundDots: cfg.imageOptions.hideBackgroundDots,
          },
        }
      : {}),
  }
}

onMounted(() => {
  qrInstance = new QRCodeStyling(buildOptions())
  if (canvasRef.value) {
    qrInstance.append(canvasRef.value)
  }
})

onUnmounted(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
  if (pollInterval) clearInterval(pollInterval)
  qrInstance = null
})

// Watch the entire designConfig for changes and debounce updates at 50 ms
// to hit the sub-50ms live re-render target from the project spec.
watch(
  () => store.designConfig,
  () => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      qrInstance?.update(buildOptions())
    }, 50)
  },
  { deep: true },
)

// ---------------------------------------------------------------------------
// Downloads
// ---------------------------------------------------------------------------

/** Client-side instant download (no server round-trip needed). */
function downloadClient(ext: 'png' | 'svg') {
  qrInstance?.download({ name: store.title || 'qrcode', extension: ext })
}

/** Stop any active export poll and reset state. */
function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

/**
 * High-resolution server export via async Celery job.
 * - Fires startAsyncExport to get a job ID.
 * - Polls getExportJob every 2 s (max 30 polls / 60 s).
 * - On COMPLETED: navigates to result_url for download.
 * - On FAILED or timeout: shows a toast error.
 */
async function serverExport(format: 'png' | 'svg' | 'pdf' | 'eps') {
  if (!store.currentQRCode) return

  exportError.value = null
  isExporting.value = true
  store.exportStatus = 'pending'

  try {
    const { data: job } = await startAsyncExport(store.currentQRCode.id, format)
    store.exportJobId = job.id
    store.exportStatus = 'processing'

    let polls = 0
    const MAX_POLLS = 30 // 30 × 2 s = 60 s timeout

    pollInterval = setInterval(async () => {
      polls++

      // Timeout guard
      if (polls > MAX_POLLS) {
        stopPolling()
        isExporting.value = false
        store.exportStatus = 'failed'
        exportError.value = 'Export timed out after 60 seconds. Please try again.'
        toast.add({
          severity: 'error',
          summary: 'Export timed out',
          detail: exportError.value,
          life: 6000,
        })
        return
      }

      try {
        const { data: status } = await getExportJob(job.id)

        if (status.status === 'COMPLETED' && status.result_url) {
          stopPolling()
          isExporting.value = false
          store.exportStatus = 'completed'
          // Trigger download by navigating to the pre-signed result URL
          window.location.href = status.result_url
        } else if (status.status === 'FAILED') {
          stopPolling()
          isExporting.value = false
          store.exportStatus = 'failed'
          exportError.value = 'Export failed on the server. Please try again.'
          toast.add({
            severity: 'error',
            summary: 'Export failed',
            detail: exportError.value,
            life: 6000,
          })
        }
        // else PENDING / PROCESSING — keep polling
      } catch {
        // Network error during poll — keep going until timeout
      }
    }, 2000)
  } catch (err) {
    isExporting.value = false
    store.exportStatus = 'failed'
    exportError.value = 'Could not start the export job. Please try again.'
    toast.add({
      severity: 'error',
      summary: 'Export error',
      detail: exportError.value,
      life: 6000,
    })
  }
}
</script>

<template>
  <div class="flex flex-col items-center gap-6">
    <!-- Live QR canvas (qr-code-styling mounts here) -->
    <div
      ref="canvasRef"
      class="rounded-xl overflow-hidden shadow-md border border-surface-200 dark:border-surface-700"
    />

    <!-- Client-side quick download -->
    <div class="flex gap-2 flex-wrap justify-center">
      <Button
        label="PNG"
        icon="pi pi-download"
        size="small"
        severity="secondary"
        :disabled="!store.hasContent"
        @click="downloadClient('png')"
      />
      <Button
        label="SVG"
        icon="pi pi-download"
        size="small"
        severity="secondary"
        :disabled="!store.hasContent"
        @click="downloadClient('svg')"
      />
    </div>

    <!-- High-res server export (requires saved QR) -->
    <template v-if="store.currentQRCode">
      <Divider />
      <p class="text-xs text-surface-400 text-center -mt-2">
        High-resolution server export
      </p>
      <div class="flex gap-2 flex-wrap justify-center">
        <Button
          label="PNG (HQ)"
          icon="pi pi-image"
          size="small"
          :loading="isExporting"
          :disabled="isExporting"
          @click="serverExport('png')"
        />
        <Button
          label="SVG"
          icon="pi pi-file"
          size="small"
          :loading="isExporting"
          :disabled="isExporting"
          @click="serverExport('svg')"
        />
        <Button
          label="PDF"
          icon="pi pi-file-pdf"
          size="small"
          :loading="isExporting"
          :disabled="isExporting"
          @click="serverExport('pdf')"
        />
        <Button
          label="EPS"
          icon="pi pi-file"
          size="small"
          :loading="isExporting"
          :disabled="isExporting"
          @click="serverExport('eps')"
        />
      </div>
      <!-- Inline error feedback (also surfaced via toast) -->
      <p v-if="exportError" class="text-xs text-red-500 text-center mt-1">
        {{ exportError }}
      </p>
    </template>
    <template v-else>
      <p class="text-xs text-surface-400 text-center">
        Save the QR code to unlock high-res server export
      </p>
    </template>
  </div>
</template>

