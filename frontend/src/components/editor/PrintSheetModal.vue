<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useQREditorStore } from '@/stores/qrEditor'
import {
  computeLayout,
  generatePrintSheetPDF,
  downloadBlob,
  DEFAULT_PRINT_SHEET_CONFIG,
  type PrintSheetConfig,
  type PageSize,
  type Orientation,
  type CutGuideStyle,
} from '@/utils/printSheetGenerator'
import type { DesignConfig } from '@/api/qrcodes'

const props = defineProps<{
  visible: boolean
  /** Optional design config override (used when opened from DownloadModal). */
  designConfig?: DesignConfig
  /** Optional title override for the filename. */
  title?: string
}>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void }>()
const toast = useToast()
const store = useQREditorStore()

/** Resolved design config — prefers the explicit prop, falls back to the editor store. */
const resolvedConfig = computed<DesignConfig>(() => props.designConfig ?? store.designConfig)
/** Resolved title for the PDF filename. */
const resolvedTitle = computed(() => props.title ?? store.title ?? 'qrcode')

// ---------------------------------------------------------------------------
// Config state
// ---------------------------------------------------------------------------
const config = ref<PrintSheetConfig>(structuredClone(DEFAULT_PRINT_SHEET_CONFIG))
const isGenerating = ref(false)

// ---------------------------------------------------------------------------
// Option lists
// ---------------------------------------------------------------------------
const pageSizeOptions = [
  { label: 'US Letter (8.5 × 11 in)', value: 'letter' },
  { label: 'A4 (210 × 297 mm)', value: 'a4' },
]

const orientationOptions = [
  { label: 'Portrait', value: 'portrait', icon: 'pi pi-mobile' },
  { label: 'Landscape', value: 'landscape', icon: 'pi pi-tablet' },
]

const cutGuideOptions = [
  { label: 'Crop Marks', value: 'crop-marks' },
  { label: 'Dashed Lines', value: 'dashed-lines' },
  { label: 'None', value: 'none' },
]

// ---------------------------------------------------------------------------
// Layout computation (reactive)
// ---------------------------------------------------------------------------
const layout = computed(() => computeLayout(config.value, resolvedConfig.value))

/** Descriptive text for the grid size */
const gridSummary = computed(() => {
  const l = layout.value
  return `${l.cols} × ${l.rows} = ${l.total} QR code${l.total !== 1 ? 's' : ''} per page`
})

/** Page dimension display */
const pageDimDisplay = computed(() => {
  const l = layout.value
  return `${l.pageW.toFixed(1)} × ${l.pageH.toFixed(1)} mm`
})

// ---------------------------------------------------------------------------
// Preview dimensions (scale to fit ~400px preview box)
// ---------------------------------------------------------------------------
const PREVIEW_MAX = 360

const previewScale = computed(() => {
  const l = layout.value
  const scaleW = PREVIEW_MAX / l.pageW
  const scaleH = PREVIEW_MAX / l.pageH
  return Math.min(scaleW, scaleH)
})

const previewPageW = computed(() => layout.value.pageW * previewScale.value)
const previewPageH = computed(() => layout.value.pageH * previewScale.value)

function previewCellStyle(row: number, col: number) {
  const l = layout.value
  const s = previewScale.value
  const x = l.offsetX + col * (l.cellW + config.value.gutterMm)
  const y = l.offsetY + row * (l.cellH + config.value.gutterMm)
  return {
    position: 'absolute' as const,
    left: `${x * s}px`,
    top: `${y * s}px`,
    width: `${l.cellW * s}px`,
    height: `${l.cellH * s}px`,
  }
}

// ---------------------------------------------------------------------------
// PDF generation
// ---------------------------------------------------------------------------
async function handleGenerate() {
  isGenerating.value = true
  try {
    const blob = await generatePrintSheetPDF(config.value, resolvedConfig.value)
    const name = resolvedTitle.value
    downloadBlob(blob, `${name.replace(/[^a-zA-Z0-9_\-]/g, '_')}_print_sheet.pdf`)
    toast.add({
      severity: 'success',
      summary: 'Print sheet generated',
      detail: `PDF with ${layout.value.total} QR codes is ready.`,
      life: 4000,
    })
  } catch (err) {
    console.error('Print sheet generation failed', err)
    toast.add({
      severity: 'error',
      summary: 'Generation failed',
      detail: 'Could not generate the print sheet. Please try again.',
      life: 6000,
    })
  } finally {
    isGenerating.value = false
  }
}

function handleClose() {
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    modal
    header="Print Sheet Generator"
    :style="{ width: '820px' }"
    :breakpoints="{ '860px': '95vw' }"
    @update:visible="handleClose"
  >
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- ================================================================ -->
      <!-- Left column: Controls                                             -->
      <!-- ================================================================ -->
      <div class="flex flex-col gap-5">
        <!-- Page size -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-semibold text-surface-500 uppercase tracking-wide">
            Page Size
          </label>
          <Select
            v-model="config.pageSize"
            :options="pageSizeOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>

        <!-- Orientation -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-semibold text-surface-500 uppercase tracking-wide">
            Orientation
          </label>
          <div class="flex gap-2">
            <Button
              v-for="opt in orientationOptions"
              :key="opt.value"
              :label="opt.label"
              :icon="opt.icon"
              size="small"
              :severity="config.orientation === opt.value ? 'primary' : 'secondary'"
              @click="config.orientation = opt.value as Orientation"
            />
          </div>
        </div>

        <!-- QR code size -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-semibold text-surface-500 uppercase tracking-wide">
            QR Code Size — {{ config.qrSizeMm }} mm
            <span class="font-normal normal-case text-surface-400">
              ({{ (config.qrSizeMm / 25.4).toFixed(2) }} in)
            </span>
          </label>
          <Slider
            v-model="config.qrSizeMm"
            :min="15"
            :max="120"
            :step="1"
            class="w-full"
          />
        </div>

        <!-- Page margins -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-semibold text-surface-500 uppercase tracking-wide">
            Page Margins — {{ config.marginMm }} mm
          </label>
          <Slider
            v-model="config.marginMm"
            :min="3"
            :max="30"
            :step="1"
            class="w-full"
          />
        </div>

        <!-- Gutter -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-semibold text-surface-500 uppercase tracking-wide">
            Spacing Between Codes — {{ config.gutterMm }} mm
          </label>
          <Slider
            v-model="config.gutterMm"
            :min="0"
            :max="25"
            :step="1"
            class="w-full"
          />
        </div>

        <!-- Cut guides -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-semibold text-surface-500 uppercase tracking-wide">
            Cut Guides
          </label>
          <Select
            v-model="config.cutGuideStyle"
            :options="cutGuideOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>

        <!-- Include labels toggle -->
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-surface-500 uppercase tracking-wide">
            Include Text Labels
          </span>
          <ToggleSwitch v-model="config.includeLabels" />
        </div>
      </div>

      <!-- ================================================================ -->
      <!-- Right column: Live preview                                        -->
      <!-- ================================================================ -->
      <div class="flex flex-col items-center gap-4">
        <p class="text-sm font-semibold text-surface-700 dark:text-surface-200">
          Sheet Preview
        </p>

        <!-- Preview box -->
        <div
          class="relative border border-surface-300 dark:border-surface-600 bg-white shadow-sm rounded"
          :style="{
            width: `${previewPageW}px`,
            height: `${previewPageH}px`,
          }"
        >
          <!-- Margin area indicator -->
          <div
            class="absolute border border-dashed border-surface-200 dark:border-surface-500 rounded-sm"
            :style="{
              left: `${config.marginMm * previewScale}px`,
              top: `${config.marginMm * previewScale}px`,
              width: `${layout.printW * previewScale}px`,
              height: `${layout.printH * previewScale}px`,
            }"
          />

          <!-- QR cell placeholders -->
          <template v-for="row in layout.rows" :key="`row-${row}`">
            <div
              v-for="col in layout.cols"
              :key="`cell-${row}-${col}`"
              class="rounded-sm flex items-center justify-center"
              :style="{
                ...previewCellStyle(row - 1, col - 1),
                backgroundColor: resolvedConfig.backgroundOptions.color,
                border: '1px solid rgba(0,0,0,0.1)',
              }"
            >
              <!-- Tiny QR icon -->
              <i
                class="pi pi-qrcode text-surface-400"
                :style="{ fontSize: `${Math.max(8, layout.cellW * previewScale * 0.4)}px` }"
              />
            </div>
          </template>

          <!-- Crop marks in preview -->
          <template v-if="config.cutGuideStyle === 'crop-marks'">
            <template v-for="row in layout.rows" :key="`mark-${row}`">
              <template v-for="col in layout.cols" :key="`mark-${row}-${col}`">
                <!-- We just show small L-shaped corners in the preview -->
                <div
                  class="absolute border-t border-l border-surface-300"
                  :style="{
                    left: `${(layout.offsetX + (col - 1) * (layout.cellW + config.gutterMm) - 2) * previewScale}px`,
                    top: `${(layout.offsetY + (row - 1) * (layout.cellH + config.gutterMm) - 2) * previewScale}px`,
                    width: `${3 * previewScale}px`,
                    height: `${3 * previewScale}px`,
                  }"
                />
              </template>
            </template>
          </template>
        </div>

        <!-- Grid summary -->
        <div class="text-center">
          <p class="text-lg font-bold text-primary-600 dark:text-primary-400">
            {{ gridSummary }}
          </p>
          <p class="text-xs text-surface-400 mt-1">
            {{ pageDimDisplay }} · {{ config.orientation }}
          </p>
        </div>
      </div>
    </div>

    <!-- ================================================================== -->
    <!-- Footer                                                              -->
    <!-- ================================================================== -->
    <template #footer>
      <div class="flex items-center justify-between w-full">
        <p class="text-xs text-surface-400">
          Rendered at 300 DPI for print quality
        </p>
        <div class="flex gap-2">
          <Button
            label="Cancel"
            severity="secondary"
            text
            @click="handleClose"
          />
          <Button
            label="Generate PDF"
            icon="pi pi-file-pdf"
            :loading="isGenerating"
            :disabled="isGenerating || !resolvedConfig.content"
            @click="handleGenerate"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

