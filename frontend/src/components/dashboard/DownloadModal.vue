<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import QRCodeStyling from 'qr-code-styling'
import { useToast } from 'primevue/usetoast'
import { useThemeStore } from '@/stores/theme'
import {
  exportQRCode,
  DEFAULT_DESIGN_CONFIG,
  type DesignConfig,
  type QRCodeRead,
  type TextLabelOptions,
} from '@/api/qrcodes'

const props = defineProps<{
  visible: boolean
  qrCode: QRCodeRead | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

const themeStore = useThemeStore()
const isDark = computed(() => themeStore.isDark)
const toast = useToast()

const canvasRef = ref<HTMLDivElement>()
const isDownloading = ref(false)
const selectedFormat = ref<'png' | 'svg' | 'pdf' | 'eps'>('png')
const pngResolution = ref<number>(1200)
const includeLabels = ref(true)

let previewInstance: QRCodeStyling | null = null

// Merged config ensuring defaults for all fields
const mergedConfig = computed<DesignConfig>(() => {
  if (!props.qrCode) return structuredClone(DEFAULT_DESIGN_CONFIG)
  const saved = props.qrCode.design_config ?? {}
  const defaults = structuredClone(DEFAULT_DESIGN_CONFIG)
  return {
    ...defaults,
    ...saved,
    imageOptions: { ...defaults.imageOptions, ...(saved.imageOptions ?? {}) },
    labelTop: { ...defaults.labelTop, ...(saved.labelTop ?? {}) },
    labelBottom: { ...defaults.labelBottom, ...(saved.labelBottom ?? {}) },
  }
})

// Whether the QR code has active text labels
const hasLabels = computed(() => {
  const top = mergedConfig.value.labelTop
  const bot = mergedConfig.value.labelBottom
  return Boolean((top.enabled && top.text) || (bot.enabled && bot.text))
})

// Resolved encoded content
const qrContent = computed(() => {
  if (!props.qrCode) return 'https://pointqr.app'
  const cfg = mergedConfig.value
  if (cfg.content) return cfg.content
  if (props.qrCode.type === 'DYNAMIC' && props.qrCode.short_code) {
    return `${window.location.origin}/r/${props.qrCode.short_code}`
  }
  return props.qrCode.target_url || 'https://pointqr.app'
})

// Options for QRCodeStyling
function buildOptions(size = 240) {
  const cfg = mergedConfig.value
  return {
    width: size,
    height: size,
    data: qrContent.value,
    margin: cfg.margin,
    qrOptions: cfg.qrOptions,
    dotsOptions: cfg.dotsOptions,
    backgroundOptions: cfg.backgroundOptions,
    cornersSquareOptions: cfg.cornersSquareOptions,
    cornersDotOptions: cfg.cornersDotOptions,
    ...(cfg.imageOptions?.src
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

// Render the on-screen preview
async function renderPreview() {
  await nextTick()
  if (!canvasRef.value || !props.qrCode) return

  canvasRef.value.innerHTML = ''
  previewInstance = new QRCodeStyling(buildOptions(220))
  previewInstance.append(canvasRef.value)
}

// Watch for modal visibility or qrCode changes
watch(
  () => [props.visible, props.qrCode],
  ([visible, qr]) => {
    if (visible && qr) {
      renderPreview()
    } else {
      if (previewInstance && canvasRef.value) {
        canvasRef.value.innerHTML = ''
      }
      previewInstance = null
    }
  },
  { deep: true },
)

function labelStyle(lbl: TextLabelOptions) {
  return {
    fontFamily: lbl.fontFamily,
    fontSize: `${Math.min(lbl.fontSize, 14)}px`,
    fontWeight: lbl.fontWeight,
    fontStyle: lbl.fontStyle,
    color: lbl.color,
    textAlign: lbl.align,
    letterSpacing: `${lbl.letterSpacing}px`,
    padding: `${Math.min(lbl.padding, 6)}px 0`,
    width: '220px',
    display: 'block',
    lineHeight: '1.3',
    whiteSpace: 'pre-wrap' as const,
  }
}

function safeFilename(title: string): string {
  return title.trim().replace(/[^a-zA-Z0-9_\-]/g, '_') || 'qrcode'
}

function measureLabelHeight(
  text: string,
  fontFamily: string,
  fontSize: number,
  fontWeight: string,
  width: number,
  padding: number,
): number {
  if (!text) return 0
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

function drawLabel(
  ctx: CanvasRenderingContext2D,
  lbl: {
    text: string
    fontFamily: string
    fontSize: number
    fontWeight: string
    fontStyle: string
    color: string
    align: 'left' | 'center' | 'right'
    letterSpacing: number
    padding: number
  },
  y: number,
  width: number,
) {
  const lineHeight = lbl.fontSize * 1.4
  ctx.font = `${lbl.fontStyle} ${lbl.fontWeight} ${lbl.fontSize}px ${lbl.fontFamily}`
  ctx.fillStyle = lbl.color
  ctx.textBaseline = 'top'

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

// Client-side composite PNG export
async function downloadPNG(size: number, withLabels: boolean) {
  if (!props.qrCode) return
  const cfg = mergedConfig.value
  const topLbl = cfg.labelTop
  const botLbl = cfg.labelBottom

  const hasTop = withLabels && topLbl.enabled && Boolean(topLbl.text)
  const hasBot = withLabels && botLbl.enabled && Boolean(botLbl.text)

  const scale = size / 300

  const topH = hasTop
    ? measureLabelHeight(
        topLbl.text,
        topLbl.fontFamily,
        topLbl.fontSize * scale,
        topLbl.fontWeight,
        size,
        topLbl.padding * scale,
      )
    : 0
  const botH = hasBot
    ? measureLabelHeight(
        botLbl.text,
        botLbl.fontFamily,
        botLbl.fontSize * scale,
        botLbl.fontWeight,
        size,
        botLbl.padding * scale,
      )
    : 0

  const totalH = size + topH + botH

  // Render QR at target size using an off-screen instance
  const exportQR = new QRCodeStyling(buildOptions(size))
  const blob = (await exportQR.getRawData('png')) as Blob
  const img = await createImageBitmap(blob)

  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = totalH
  const ctx = canvas.getContext('2d')!

  // Background
  ctx.fillStyle = cfg.backgroundOptions.color || '#ffffff'
  ctx.fillRect(0, 0, size, totalH)

  // Top label
  if (hasTop) {
    drawLabel(
      ctx,
      {
        ...topLbl,
        fontSize: topLbl.fontSize * scale,
        padding: topLbl.padding * scale,
        letterSpacing: topLbl.letterSpacing * scale,
      },
      0,
      size,
    )
  }

  // Draw QR code matrix
  ctx.drawImage(img, 0, topH, size, size)

  // Bottom label
  if (hasBot) {
    drawLabel(
      ctx,
      {
        ...botLbl,
        fontSize: botLbl.fontSize * scale,
        padding: botLbl.padding * scale,
        letterSpacing: botLbl.letterSpacing * scale,
      },
      topH + size,
      size,
    )
  }

  canvas.toBlob((b) => {
    if (!b) return
    const url = URL.createObjectURL(b)
    const a = document.createElement('a')
    a.href = url
    a.download = `${safeFilename(props.qrCode!.title)}.png`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, 'image/png')
}

// Client-side composite SVG export
async function downloadSVG(withLabels: boolean) {
  if (!props.qrCode) return
  const cfg = mergedConfig.value
  const qrSize = 300
  const topLbl = cfg.labelTop
  const botLbl = cfg.labelBottom

  const hasTop = withLabels && topLbl.enabled && Boolean(topLbl.text)
  const hasBot = withLabels && botLbl.enabled && Boolean(botLbl.text)

  const topH = hasTop
    ? measureLabelHeight(topLbl.text, topLbl.fontFamily, topLbl.fontSize, topLbl.fontWeight, qrSize, topLbl.padding)
    : 0
  const botH = hasBot
    ? measureLabelHeight(botLbl.text, botLbl.fontFamily, botLbl.fontSize, botLbl.fontWeight, qrSize, botLbl.padding)
    : 0

  const totalH = qrSize + topH + botH

  const exportQR = new QRCodeStyling(buildOptions(qrSize))
  const blob = (await exportQR.getRawData('svg')) as Blob
  const svgText = await blob.text()

  const parser = new DOMParser()
  const doc = parser.parseFromString(svgText, 'image/svg+xml')
  const svg = doc.documentElement

  svg.setAttribute('width', String(qrSize))
  svg.setAttribute('height', String(totalH))
  svg.setAttribute('viewBox', `0 0 ${qrSize} ${totalH}`)

  if (topH > 0 || botH > 0) {
    const bg = doc.createElementNS('http://www.w3.org/2000/svg', 'rect')
    bg.setAttribute('x', '0')
    bg.setAttribute('y', '0')
    bg.setAttribute('width', String(qrSize))
    bg.setAttribute('height', String(totalH))
    bg.setAttribute('fill', cfg.backgroundOptions.color || '#ffffff')
    svg.insertBefore(bg, svg.firstChild)
  }

  if (topH > 0) {
    const children = Array.from(svg.childNodes).slice(1)
    const g = doc.createElementNS('http://www.w3.org/2000/svg', 'g')
    g.setAttribute('transform', `translate(0,${topH})`)
    children.forEach((c) => g.appendChild(c))
    svg.appendChild(g)
  }

  function appendSvgLabel(lbl: typeof topLbl, yOffset: number) {
    if (!lbl.enabled || !lbl.text) return
    const lines = lbl.text.split('\n')
    const lineH = lbl.fontSize * 1.4
    let lineY = yOffset + lbl.padding + lbl.fontSize

    for (const line of lines) {
      const t = doc.createElementNS('http://www.w3.org/2000/svg', 'text')
      t.setAttribute(
        'x',
        lbl.align === 'center'
          ? String(qrSize / 2)
          : lbl.align === 'right'
            ? String(qrSize - 4)
            : '4',
      )
      t.setAttribute('y', String(lineY))
      t.setAttribute('font-family', lbl.fontFamily)
      t.setAttribute('font-size', String(lbl.fontSize))
      t.setAttribute('font-weight', lbl.fontWeight)
      t.setAttribute('font-style', lbl.fontStyle)
      t.setAttribute('fill', lbl.color)
      t.setAttribute(
        'text-anchor',
        lbl.align === 'center' ? 'middle' : lbl.align === 'right' ? 'end' : 'start',
      )
      if (lbl.letterSpacing !== 0) t.setAttribute('letter-spacing', String(lbl.letterSpacing))
      t.textContent = line
      svg.appendChild(t)
      lineY += lineH
    }
  }

  if (hasTop) appendSvgLabel(topLbl, 0)
  if (hasBot) appendSvgLabel(botLbl, topH + qrSize)

  const serialized = new XMLSerializer().serializeToString(doc)
  const outBlob = new Blob([serialized], { type: 'image/svg+xml' })
  const url = URL.createObjectURL(outBlob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${safeFilename(props.qrCode!.title)}.svg`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// Server-side PDF / EPS export
async function downloadServer(format: 'pdf' | 'eps') {
  if (!props.qrCode) return
  const res = await exportQRCode(props.qrCode.id, format)
  const mimeTypes: Record<string, string> = {
    pdf: 'application/pdf',
    eps: 'application/postscript',
  }
  const blob = new Blob([res.data], { type: mimeTypes[format] || 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${safeFilename(props.qrCode.title)}.${format}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// Main download handler triggered by button
async function triggerDownload(format?: 'png' | 'svg' | 'pdf' | 'eps') {
  const fmt = format || selectedFormat.value
  if (!props.qrCode) return
  isDownloading.value = true

  try {
    if (fmt === 'png') {
      await downloadPNG(pngResolution.value, includeLabels.value)
    } else if (fmt === 'svg') {
      await downloadSVG(includeLabels.value)
    } else {
      await downloadServer(fmt)
    }

    toast.add({
      severity: 'success',
      summary: 'Download started',
      detail: `${safeFilename(props.qrCode.title)}.${fmt}`,
      life: 3000,
    })
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Download failed',
      detail: err?.response?.data?.detail || err?.message || 'Could not export QR code',
      life: 5000,
    })
  } finally {
    isDownloading.value = false
  }
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    dismissable-mask
    :header="`Download: ${qrCode?.title || 'Barcode'}`"
    :style="{ width: '90vw', maxWidth: '720px' }"
    :pt="{
      root: { style: 'background-color: var(--bg-card); border-color: var(--border); border-radius: 18px; overflow: hidden;' },
      header: { style: 'background-color: var(--bg-card); border-bottom: 1px solid var(--border); padding: 1.25rem 1.5rem;' },
      title: { style: 'color: var(--text-primary); font-size: 1.25rem; font-weight: 700;' },
      content: { style: 'background-color: var(--bg-card); padding: 1.5rem;' },
      footer: { style: 'background-color: var(--bg-card); border-top: 1px solid var(--border); padding: 1rem 1.5rem;' },
    }"
    @update:visible="emit('update:visible', $event)"
  >
    <div v-if="qrCode" class="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
      <!-- Left: QR Code Display Preview Mat -->
      <div class="md:col-span-5 flex flex-col items-center gap-3">
        <div
          class="relative rounded-2xl p-4 transition-colors duration-200 flex flex-col items-center w-full max-w-[270px]"
          :class="isDark ? 'qr-checkerboard ring-1 ring-surface-700' : 'bg-surface-50 ring-1 ring-surface-200'"
        >
          <!-- Top text label if present -->
          <span
            v-if="mergedConfig.labelTop.enabled && mergedConfig.labelTop.text"
            :style="labelStyle(mergedConfig.labelTop)"
          >
            {{ mergedConfig.labelTop.text }}
          </span>

          <!-- QR canvas target -->
          <div ref="canvasRef" class="rounded-lg overflow-hidden shadow-sm block my-1" />

          <!-- Bottom text label if present -->
          <span
            v-if="mergedConfig.labelBottom.enabled && mergedConfig.labelBottom.text"
            :style="labelStyle(mergedConfig.labelBottom)"
          >
            {{ mergedConfig.labelBottom.text }}
          </span>
        </div>

        <!-- Quick metadata badge info -->
        <div class="w-full flex items-center justify-between text-xs px-1 text-surface-500">
          <div class="flex items-center gap-1.5">
            <Tag
              :value="qrCode.type"
              :severity="qrCode.type === 'DYNAMIC' ? 'info' : 'secondary'"
              class="text-[10px] px-1.5 py-0.5"
            />
            <span class="font-mono">{{ qrCode.scan_count }} scans</span>
          </div>
          <span class="truncate max-w-[120px]" :title="qrContent">
            {{ qrContent.replace(/^https?:\/\//, '') }}
          </span>
        </div>

        <!-- Quick 1-click download pills -->
        <div class="w-full pt-2">
          <p class="text-[11px] font-medium text-surface-400 mb-1.5 text-center">
            Quick 1-Click Download
          </p>
          <div class="grid grid-cols-4 gap-1.5">
            <Button
              label="PNG"
              size="small"
              severity="secondary"
              outlined
              class="!text-xs !py-1 !px-2 font-mono"
              :disabled="isDownloading"
              @click="triggerDownload('png')"
            />
            <Button
              label="SVG"
              size="small"
              severity="secondary"
              outlined
              class="!text-xs !py-1 !px-2 font-mono"
              :disabled="isDownloading"
              @click="triggerDownload('svg')"
            />
            <Button
              label="PDF"
              size="small"
              severity="secondary"
              outlined
              class="!text-xs !py-1 !px-2 font-mono"
              :disabled="isDownloading"
              @click="triggerDownload('pdf')"
            />
            <Button
              label="EPS"
              size="small"
              severity="secondary"
              outlined
              class="!text-xs !py-1 !px-2 font-mono"
              :disabled="isDownloading"
              @click="triggerDownload('eps')"
            />
          </div>
        </div>
      </div>

      <!-- Right: Download Options Panel -->
      <div class="md:col-span-7 flex flex-col gap-4">
        <div>
          <label class="text-xs font-semibold uppercase tracking-wider text-surface-500 mb-2 block">
            Select Format
          </label>
          <div class="grid grid-cols-2 gap-2">
            <!-- PNG Option Card -->
            <button
              type="button"
              class="format-card"
              :class="{ 'is-selected': selectedFormat === 'png' }"
              @click="selectedFormat = 'png'"
            >
              <div class="flex items-center gap-2 mb-1">
                <i class="pi pi-image text-primary-500" />
                <span class="font-bold text-sm text-surface-900 dark:text-surface-0">PNG</span>
              </div>
              <p class="text-[11px] text-surface-500 line-clamp-1">Web, social & screen</p>
            </button>

            <!-- SVG Option Card -->
            <button
              type="button"
              class="format-card"
              :class="{ 'is-selected': selectedFormat === 'svg' }"
              @click="selectedFormat = 'svg'"
            >
              <div class="flex items-center gap-2 mb-1">
                <i class="pi pi-file text-primary-500" />
                <span class="font-bold text-sm text-surface-900 dark:text-surface-0">SVG</span>
              </div>
              <p class="text-[11px] text-surface-500 line-clamp-1">Scalable vector graphic</p>
            </button>

            <!-- PDF Option Card -->
            <button
              type="button"
              class="format-card"
              :class="{ 'is-selected': selectedFormat === 'pdf' }"
              @click="selectedFormat = 'pdf'"
            >
              <div class="flex items-center gap-2 mb-1">
                <i class="pi pi-file-pdf text-red-500" />
                <span class="font-bold text-sm text-surface-900 dark:text-surface-0">PDF</span>
              </div>
              <p class="text-[11px] text-surface-500 line-clamp-1">Print ready document</p>
            </button>

            <!-- EPS Option Card -->
            <button
              type="button"
              class="format-card"
              :class="{ 'is-selected': selectedFormat === 'eps' }"
              @click="selectedFormat = 'eps'"
            >
              <div class="flex items-center gap-2 mb-1">
                <i class="pi pi-sliders-h text-amber-500" />
                <span class="font-bold text-sm text-surface-900 dark:text-surface-0">EPS</span>
              </div>
              <p class="text-[11px] text-surface-500 line-clamp-1">Commercial prepress vector</p>
            </button>
          </div>
        </div>

        <!-- PNG specific options: Resolution -->
        <div v-if="selectedFormat === 'png'" class="p-3 rounded-xl border border-surface-200 dark:border-surface-700 bg-surface-50 dark:bg-surface-800/50 flex flex-col gap-2">
          <label class="text-xs font-semibold text-surface-700 dark:text-surface-300">
            Image Resolution / Size
          </label>
          <div class="grid grid-cols-3 gap-2">
            <button
              type="button"
              class="size-btn"
              :class="{ 'is-active': pngResolution === 600 }"
              @click="pngResolution = 600"
            >
              <span class="font-semibold text-xs">Standard</span>
              <span class="text-[10px] text-surface-400">600 × 600</span>
            </button>
            <button
              type="button"
              class="size-btn"
              :class="{ 'is-active': pngResolution === 1200 }"
              @click="pngResolution = 1200"
            >
              <span class="font-semibold text-xs">High-Res</span>
              <span class="text-[10px] text-surface-400">1200 × 1200</span>
            </button>
            <button
              type="button"
              class="size-btn"
              :class="{ 'is-active': pngResolution === 2400 }"
              @click="pngResolution = 2400"
            >
              <span class="font-semibold text-xs">Ultra 4K</span>
              <span class="text-[10px] text-surface-400">2400 × 2400</span>
            </button>
          </div>
        </div>

        <!-- Labels toggle option if code has labels -->
        <div
          v-if="hasLabels && (selectedFormat === 'png' || selectedFormat === 'svg')"
          class="flex items-center justify-between p-3 rounded-xl border border-surface-200 dark:border-surface-700"
        >
          <div>
            <p class="text-xs font-semibold text-surface-800 dark:text-surface-200">Include text labels</p>
            <p class="text-[11px] text-surface-500">Export outer top and bottom captions with the barcode</p>
          </div>
          <input
            id="include-labels"
            v-model="includeLabels"
            type="checkbox"
            class="w-4 h-4 rounded text-primary-600 focus:ring-primary-500 border-surface-300 dark:border-surface-600 cursor-pointer"
          />
        </div>

        <!-- Vector notice for PDF and EPS -->
        <div
          v-if="selectedFormat === 'pdf' || selectedFormat === 'eps'"
          class="flex items-center gap-2 p-3 rounded-xl text-xs bg-primary-500/10 text-primary-600 dark:text-primary-300 border border-primary-500/20"
        >
          <i class="pi pi-info-circle text-base" />
          <span>Vector formats scale losslessly to any billboard or print size without pixelation.</span>
        </div>

        <!-- Primary Download Button -->
        <Button
          :label="`Download ${selectedFormat.toUpperCase()}`"
          icon="pi pi-download"
          size="large"
          class="w-full mt-auto font-semibold"
          :loading="isDownloading"
          @click="triggerDownload()"
        />
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full">
        <span class="text-xs text-surface-400">
          PointQR Generator
        </span>
        <Button
          label="Done"
          severity="secondary"
          text
          size="small"
          @click="emit('update:visible', false)"
        />
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
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

.format-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0.75rem;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease-in-out;
}

.format-card:hover {
  background: var(--bg-hover);
  border-color: var(--color-primary);
}

.format-card.is-selected {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  box-shadow: 0 0 0 1px var(--color-primary);
}

.size-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 0.25rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  cursor: pointer;
  transition: all 0.15s ease;
}

.size-btn:hover {
  background: var(--bg-hover);
}

.size-btn.is-active {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}
</style>
