<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import QRCodeStyling from 'qr-code-styling'
import { useQREditorStore } from '@/stores/qrEditor'
import { useThemeStore } from '@/stores/theme'
import { exportQRCode, startAsyncExport, getExportJob } from '@/api/qrcodes'

const store = useQREditorStore()
const themeStore = useThemeStore()
const isDark = computed(() => themeStore.isDark)
const toast = useToast()
const canvasRef = ref<HTMLDivElement>()
const isExporting = ref(false)
const exportError = ref<string | null>(null)

/** Build CSS style object for a text label. */
function labelStyle(key: 'labelTop' | 'labelBottom') {
  const lbl = store.designConfig[key]
  return {
    fontFamily: lbl.fontFamily,
    fontSize: `${lbl.fontSize}px`,
    fontWeight: lbl.fontWeight,
    fontStyle: lbl.fontStyle,
    color: lbl.color,
    textAlign: lbl.align,
    letterSpacing: `${lbl.letterSpacing}px`,
    padding: `${lbl.padding}px 0`,
    width: '300px',
    display: 'block',
    lineHeight: '1.3',
    whiteSpace: 'pre-wrap' as const,
  }
}

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

/**
 * Measure how tall a label will be when rendered at `width` px.
 * We use an offscreen canvas to get font metrics.
 */
function measureLabelHeight(
  text: string,
  fontFamily: string,
  fontSize: number,
  fontWeight: string,
  width: number,
  padding: number,
): number {
  if (!text) return 0
  // Approximate line height as 1.4× font size
  const lineHeight = fontSize * 1.4
  const ctx = document.createElement('canvas').getContext('2d')!
  ctx.font = `${fontWeight} ${fontSize}px ${fontFamily}`
  const words = text.split('\n')
  let lines = 0
  for (const word of words) {
    const measured = ctx.measureText(word).width
    lines += Math.max(1, Math.ceil(measured / width))
  }
  return lines * lineHeight + padding * 2
}

/**
 * Draw a label's text onto a Canvas 2D context.
 * `y` is the top of the label band.
 */
function drawLabel(
  ctx: CanvasRenderingContext2D,
  lbl: { text: string; fontFamily: string; fontSize: number; fontWeight: string; fontStyle: string; color: string; align: 'left' | 'center' | 'right'; letterSpacing: number; padding: number },
  y: number,
  width: number,
) {
  const lineHeight = lbl.fontSize * 1.4
  ctx.font = `${lbl.fontStyle} ${lbl.fontWeight} ${lbl.fontSize}px ${lbl.fontFamily}`
  ctx.fillStyle = lbl.color
  ctx.textBaseline = 'top'

  // Split by explicit newlines then word-wrap within `width`
  const rawLines = lbl.text.split('\n')
  const wrappedLines: string[] = []
  for (const raw of rawLines) {
    const words = raw.split(' ')
    let cur = ''
    for (const w of words) {
      const test = cur ? `${cur} ${w}` : w
      if (ctx.measureText(test).width > width - 8 && cur) {
        wrappedLines.push(cur)
        cur = w
      } else {
        cur = test
      }
    }
    wrappedLines.push(cur)
  }

  let textY = y + lbl.padding
  for (const line of wrappedLines) {
    let x = 4
    if (lbl.align === 'center') x = (width - ctx.measureText(line).width) / 2
    else if (lbl.align === 'right') x = width - ctx.measureText(line).width - 4

    // Manual letter spacing: draw char by char
    if (lbl.letterSpacing !== 0) {
      let cx = x
      for (const char of line) {
        ctx.fillText(char, cx, textY)
        cx += ctx.measureText(char).width + lbl.letterSpacing
      }
    } else {
      ctx.fillText(line, x, textY)
    }
    textY += lineHeight
  }
}

/** Client-side composited PNG download (QR + labels). */
async function downloadClient(ext: 'png' | 'svg') {
  const cfg = store.designConfig
  const qrSize = 300
  const topLbl = cfg.labelTop
  const botLbl = cfg.labelBottom

  const topH = topLbl.enabled && topLbl.text
    ? measureLabelHeight(topLbl.text, topLbl.fontFamily, topLbl.fontSize, topLbl.fontWeight, qrSize, topLbl.padding)
    : 0
  const botH = botLbl.enabled && botLbl.text
    ? measureLabelHeight(botLbl.text, botLbl.fontFamily, botLbl.fontSize, botLbl.fontWeight, qrSize, botLbl.padding)
    : 0

  const totalH = qrSize + topH + botH
  const name = store.title || 'qrcode'

  if (ext === 'png') {
    // Get the QR as a raw PNG blob via qr-code-styling
    const blob = await qrInstance!.getRawData('png') as Blob
    const img = await createImageBitmap(await blob.arrayBuffer().then(b => new Blob([b], { type: 'image/png' })))

    const canvas = document.createElement('canvas')
    canvas.width = qrSize
    canvas.height = totalH
    const ctx = canvas.getContext('2d')!

    // Background
    ctx.fillStyle = cfg.backgroundOptions.color
    ctx.fillRect(0, 0, qrSize, totalH)

    // Top label
    if (topH > 0) drawLabel(ctx, topLbl, 0, qrSize)

    // QR code
    ctx.drawImage(img, 0, topH, qrSize, qrSize)

    // Bottom label
    if (botH > 0) drawLabel(ctx, botLbl, topH + qrSize, qrSize)

    canvas.toBlob(b => {
      if (!b) return
      const url = URL.createObjectURL(b)
      const a = document.createElement('a')
      a.href = url
      a.download = `${name}.png`
      a.click()
      URL.revokeObjectURL(url)
    }, 'image/png')

  } else {
    // SVG: get raw SVG string from qr-code-styling then inject label text elements
    const blob = await qrInstance!.getRawData('svg') as Blob
    const svgText = await blob.text()

    // Parse and resize the SVG to add label space
    const parser = new DOMParser()
    const doc = parser.parseFromString(svgText, 'image/svg+xml')
    const svg = doc.documentElement

    svg.setAttribute('width', String(qrSize))
    svg.setAttribute('height', String(totalH))
    svg.setAttribute('viewBox', `0 0 ${qrSize} ${totalH}`)

    // Background rect for label areas
    if (topH > 0 || botH > 0) {
      const bg = doc.createElementNS('http://www.w3.org/2000/svg', 'rect')
      bg.setAttribute('x', '0')
      bg.setAttribute('y', '0')
      bg.setAttribute('width', String(qrSize))
      bg.setAttribute('height', String(totalH))
      bg.setAttribute('fill', cfg.backgroundOptions.color)
      svg.insertBefore(bg, svg.firstChild)
    }

    // Shift the QR content down by topH using a <g> wrapper
    if (topH > 0) {
      const children = Array.from(svg.childNodes).slice(1) // skip bg rect
      const g = doc.createElementNS('http://www.w3.org/2000/svg', 'g')
      g.setAttribute('transform', `translate(0,${topH})`)
      children.forEach(c => g.appendChild(c))
      svg.appendChild(g)
    }

    // Helper: append SVG <text> for a label
    function appendSvgLabel(
      lbl: typeof topLbl,
      yOffset: number,
    ) {
      if (!lbl.enabled || !lbl.text) return
      const lines = lbl.text.split('\n')
      const lineH = lbl.fontSize * 1.4
      let lineY = yOffset + lbl.padding + lbl.fontSize

      for (const line of lines) {
        const t = doc.createElementNS('http://www.w3.org/2000/svg', 'text')
        t.setAttribute('x',
          lbl.align === 'center' ? String(qrSize / 2)
          : lbl.align === 'right' ? String(qrSize - 4)
          : '4')
        t.setAttribute('y', String(lineY))
        t.setAttribute('font-family', lbl.fontFamily)
        t.setAttribute('font-size', String(lbl.fontSize))
        t.setAttribute('font-weight', lbl.fontWeight)
        t.setAttribute('font-style', lbl.fontStyle)
        t.setAttribute('fill', lbl.color)
        t.setAttribute('text-anchor',
          lbl.align === 'center' ? 'middle'
          : lbl.align === 'right' ? 'end'
          : 'start')
        if (lbl.letterSpacing !== 0) t.setAttribute('letter-spacing', String(lbl.letterSpacing))
        t.textContent = line
        svg.appendChild(t)
        lineY += lineH
      }
    }

    appendSvgLabel(topLbl, 0)
    appendSvgLabel(botLbl, topH + qrSize)

    const serialized = new XMLSerializer().serializeToString(doc)
    const outBlob = new Blob([serialized], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(outBlob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${name}.svg`
    a.click()
    URL.revokeObjectURL(url)
  }
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
  <div class="flex flex-col items-center gap-6 w-full">
    <!-- QR canvas mat — checkerboard in dark mode so the white QR background
         reads as intentional rather than a bright intrusion into the dark UI -->
    <div class="flex flex-col items-center gap-3 w-full">
      <div
        class="relative rounded-2xl p-4 transition-colors duration-200 flex flex-col items-center"
        :class="isDark
          ? 'qr-checkerboard ring-1 ring-surface-600'
          : 'bg-surface-50 ring-1 ring-surface-200'"
      >
        <!-- Top label -->
        <span
          v-if="store.designConfig.labelTop.enabled && store.designConfig.labelTop.text"
          :style="labelStyle('labelTop')"
        >{{ store.designConfig.labelTop.text }}</span>

        <div
          ref="canvasRef"
          class="rounded-lg overflow-hidden shadow-sm block"
        />

        <!-- Bottom label -->
        <span
          v-if="store.designConfig.labelBottom.enabled && store.designConfig.labelBottom.text"
          :style="labelStyle('labelBottom')"
        >{{ store.designConfig.labelBottom.text }}</span>
      </div>
      <!-- Background colour hint in dark mode -->
      <p class="text-xs text-surface-400 flex items-center gap-1.5">
        <span
          class="inline-block w-3 h-3 rounded-sm border border-surface-300 dark:border-surface-600 flex-shrink-0"
          :style="{ background: store.designConfig.backgroundOptions.color }"
        />
        QR background: <code class="text-surface-500">{{ store.designConfig.backgroundOptions.color }}</code>
      </p>
    </div>

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

<style scoped>
/**
 * Classic design-tool transparency checkerboard for the dark-mode QR mat.
 * Two overlapping gradients produce alternating dark squares at 12px pitch.
 */
.qr-checkerboard {
  background-color: #1e1e2e;
  background-image:
    linear-gradient(45deg, #2a2a3e 25%, transparent 25%),
    linear-gradient(-45deg, #2a2a3e 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #2a2a3e 75%),
    linear-gradient(-45deg, transparent 75%, #2a2a3e 75%);
  background-size: 24px 24px;
  background-position: 0 0, 0 12px, 12px -12px, -12px 0px;
}
</style>
