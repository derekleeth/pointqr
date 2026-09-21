<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import QRCodeStyling from 'qr-code-styling'
import { useQREditorStore } from '@/stores/qrEditor'
import { exportQRCode } from '@/api/qrcodes'

const store = useQREditorStore()
const canvasRef = ref<HTMLDivElement>()
const isExporting = ref(false)

let qrInstance: QRCodeStyling | null = null
let debounceTimer: ReturnType<typeof setTimeout> | null = null

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

/** High-resolution server export (saved QR codes only). */
async function serverExport(format: 'png' | 'svg' | 'pdf' | 'eps') {
  if (!store.currentQRCode) return
  isExporting.value = true
  try {
    const { data } = await exportQRCode(store.currentQRCode.id, format)
    const url = URL.createObjectURL(data as Blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${store.title || 'qrcode'}.${format}`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    isExporting.value = false
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
          @click="serverExport('png')"
        />
        <Button
          label="SVG"
          icon="pi pi-file"
          size="small"
          :loading="isExporting"
          @click="serverExport('svg')"
        />
        <Button
          label="PDF"
          icon="pi pi-file-pdf"
          size="small"
          :loading="isExporting"
          @click="serverExport('pdf')"
        />
        <Button
          label="EPS"
          icon="pi pi-file"
          size="small"
          :loading="isExporting"
          @click="serverExport('eps')"
        />
      </div>
    </template>
    <template v-else>
      <p class="text-xs text-surface-400 text-center">
        Save the QR code to unlock high-res server export
      </p>
    </template>
  </div>
</template>

