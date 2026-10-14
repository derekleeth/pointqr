/**
 * Multi-up repeating PDF print sheet generator.
 *
 * Renders a styled QR code repeatedly across a printable PDF page (US Letter
 * or A4) with configurable margins, gutters, cut guides, and sizing.
 *
 * All measurements are in millimetres internally; jsPDF also defaults to mm.
 */

import { jsPDF } from 'jspdf'
import QRCodeStyling from 'qr-code-styling'
import type { DesignConfig } from '@/api/qrcodes'
import { renderQRCell } from '@/utils/qrRendering'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type PageSize = 'letter' | 'a4'
export type Orientation = 'portrait' | 'landscape'
export type CutGuideStyle = 'crop-marks' | 'dashed-lines' | 'none'

export interface PrintSheetConfig {
  /** Paper size */
  pageSize: PageSize
  /** Portrait or landscape */
  orientation: Orientation
  /** QR code width/height in mm (the QR bitmap only, excluding labels) */
  qrSizeMm: number
  /** Page margins in mm (uniform all sides) */
  marginMm: number
  /** Gap between QR cells in mm */
  gutterMm: number
  /** Cut guide style */
  cutGuideStyle: CutGuideStyle
  /** Include top/bottom labels in each cell */
  includeLabels: boolean
}

export const DEFAULT_PRINT_SHEET_CONFIG: PrintSheetConfig = {
  pageSize: 'letter',
  orientation: 'portrait',
  qrSizeMm: 50,
  marginMm: 12,
  gutterMm: 5,
  cutGuideStyle: 'crop-marks',
  includeLabels: true,
}

// ---------------------------------------------------------------------------
// Page dimension constants (mm)
// ---------------------------------------------------------------------------

const PAGE_DIMS: Record<PageSize, { w: number; h: number }> = {
  letter: { w: 215.9, h: 279.4 },
  a4: { w: 210, h: 297 },
}

// ---------------------------------------------------------------------------
// Layout calculator
// ---------------------------------------------------------------------------

export interface SheetLayout {
  /** Number of columns */
  cols: number
  /** Number of rows */
  rows: number
  /** Total codes on the page */
  total: number
  /** Width of one cell in mm (same as qrSizeMm for now) */
  cellW: number
  /** Height of one cell in mm (QR + label heights) */
  cellH: number
  /** Printable area width (page width minus margins) */
  printW: number
  /** Printable area height (page height minus margins) */
  printH: number
  /** Page width in mm */
  pageW: number
  /** Page height in mm */
  pageH: number
  /** Horizontal offset to centre the grid */
  offsetX: number
  /** Vertical offset to centre the grid */
  offsetY: number
}

/**
 * Compute how many QR codes fit on the page given the config.
 * The cell height accounts for label heights when `includeLabels` is true.
 */
export function computeLayout(
  config: PrintSheetConfig,
  designConfig: DesignConfig,
): SheetLayout {
  const dims = PAGE_DIMS[config.pageSize]
  const pageW = config.orientation === 'portrait' ? dims.w : dims.h
  const pageH = config.orientation === 'portrait' ? dims.h : dims.w

  const printW = pageW - config.marginMm * 2
  const printH = pageH - config.marginMm * 2

  // Estimate cell height: QR size + label heights (scaled proportionally)
  const cellW = config.qrSizeMm
  let cellH = config.qrSizeMm

  if (config.includeLabels) {
    const topLbl = designConfig.labelTop
    const botLbl = designConfig.labelBottom
    // Estimate label heights as a proportion of the QR size
    // (based on the 300px reference size in the editor)
    const scale = config.qrSizeMm / (300 * 0.2646) // 300px ≈ 79.4mm at 96dpi
    if (topLbl.enabled && topLbl.text) {
      const linesApprox = topLbl.text.split('\n').length
      cellH += (topLbl.fontSize * 1.4 * linesApprox + topLbl.padding * 2) * scale * 0.2646
    }
    if (botLbl.enabled && botLbl.text) {
      const linesApprox = botLbl.text.split('\n').length
      cellH += (botLbl.fontSize * 1.4 * linesApprox + botLbl.padding * 2) * scale * 0.2646
    }
  }

  const cols = Math.max(1, Math.floor((printW + config.gutterMm) / (cellW + config.gutterMm)))
  const rows = Math.max(1, Math.floor((printH + config.gutterMm) / (cellH + config.gutterMm)))

  // Centre the grid within the printable area
  const gridW = cols * cellW + (cols - 1) * config.gutterMm
  const gridH = rows * cellH + (rows - 1) * config.gutterMm
  const offsetX = config.marginMm + (printW - gridW) / 2
  const offsetY = config.marginMm + (printH - gridH) / 2

  return { cols, rows, total: cols * rows, cellW, cellH, printW, printH, pageW, pageH, offsetX, offsetY }
}

// ---------------------------------------------------------------------------
// PDF generator
// ---------------------------------------------------------------------------

/**
 * Generate a multi-up print sheet PDF.
 *
 * @param config      - Print sheet layout configuration
 * @param designConfig - The full QR design config from the editor store
 * @returns A Blob containing the PDF
 */
export async function generatePrintSheetPDF(
  config: PrintSheetConfig,
  designConfig: DesignConfig,
): Promise<Blob> {
  const layout = computeLayout(config, designConfig)

  // --- 1. Render a high-resolution QR cell bitmap --------------------------

  // Determine pixel size: render at 300 DPI equivalent
  // 1 mm ≈ 11.811 px at 300 DPI
  const PX_PER_MM = 300 / 25.4 // ~11.811
  const qrPx = Math.round(config.qrSizeMm * PX_PER_MM)

  // Build a qr-code-styling instance at the target pixel resolution
  const qrOptions: Record<string, unknown> = {
    width: qrPx,
    height: qrPx,
    data: designConfig.content || 'https://pointqr.app',
    margin: designConfig.margin,
    qrOptions: designConfig.qrOptions,
    dotsOptions: designConfig.dotsOptions,
    backgroundOptions: designConfig.backgroundOptions,
    cornersSquareOptions: designConfig.cornersSquareOptions,
    cornersDotOptions: designConfig.cornersDotOptions,
  }

  if (designConfig.imageOptions.src) {
    qrOptions.image = designConfig.imageOptions.src
    qrOptions.imageOptions = {
      margin: designConfig.imageOptions.margin,
      imageSize: designConfig.imageOptions.imageSize,
      hideBackgroundDots: designConfig.imageOptions.hideBackgroundDots,
    }
  }

  const qrInstance = new QRCodeStyling(qrOptions as never)
  const qrBlob = (await qrInstance.getRawData('png')) as Blob

  // Build a cell config for labels (scale font sizes proportionally)
  const labelScale = qrPx / 300 // scale factor relative to the 300px editor preview
  const cellCfg = {
    backgroundOptions: designConfig.backgroundOptions,
    labelTop: config.includeLabels
      ? {
          ...designConfig.labelTop,
          fontSize: Math.round(designConfig.labelTop.fontSize * labelScale),
          padding: Math.round(designConfig.labelTop.padding * labelScale),
          letterSpacing: designConfig.labelTop.letterSpacing * labelScale,
        }
      : { ...designConfig.labelTop, enabled: false },
    labelBottom: config.includeLabels
      ? {
          ...designConfig.labelBottom,
          fontSize: Math.round(designConfig.labelBottom.fontSize * labelScale),
          padding: Math.round(designConfig.labelBottom.padding * labelScale),
          letterSpacing: designConfig.labelBottom.letterSpacing * labelScale,
        }
      : { ...designConfig.labelBottom, enabled: false },
  }

  const cellCanvas = await renderQRCell(qrBlob, cellCfg, qrPx)

  // Convert the cell canvas to a data URL for jsPDF
  const cellDataUrl = cellCanvas.toDataURL('image/png')

  // Cell dimensions in mm (based on actual canvas pixel ratio)
  const cellWMm = layout.cellW
  const cellHMm = (cellCanvas.height / cellCanvas.width) * layout.cellW

  // --- 2. Create the PDF --------------------------------------------------

  const pdf = new jsPDF({
    orientation: config.orientation === 'portrait' ? 'p' : 'l',
    unit: 'mm',
    format: config.pageSize === 'letter' ? 'letter' : 'a4',
  })

  // Recalculate rows with actual cell height
  const effectiveLayout = computeLayoutWithCellH(config, cellHMm, layout.pageW, layout.pageH)

  // --- 3. Place QR cells on the grid --------------------------------------

  for (let row = 0; row < effectiveLayout.rows; row++) {
    for (let col = 0; col < effectiveLayout.cols; col++) {
      const x = effectiveLayout.offsetX + col * (cellWMm + config.gutterMm)
      const y = effectiveLayout.offsetY + row * (cellHMm + config.gutterMm)
      pdf.addImage(cellDataUrl, 'PNG', x, y, cellWMm, cellHMm)
    }
  }

  // --- 4. Draw cut guides -------------------------------------------------

  if (config.cutGuideStyle !== 'none') {
    drawCutGuides(pdf, effectiveLayout, config, cellWMm, cellHMm)
  }

  return pdf.output('blob')
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

interface EffectiveLayout {
  cols: number
  rows: number
  total: number
  offsetX: number
  offsetY: number
}

function computeLayoutWithCellH(
  config: PrintSheetConfig,
  cellHMm: number,
  pageW: number,
  pageH: number,
): EffectiveLayout {
  const printW = pageW - config.marginMm * 2
  const printH = pageH - config.marginMm * 2
  const cellWMm = config.qrSizeMm

  const cols = Math.max(1, Math.floor((printW + config.gutterMm) / (cellWMm + config.gutterMm)))
  const rows = Math.max(1, Math.floor((printH + config.gutterMm) / (cellHMm + config.gutterMm)))

  const gridW = cols * cellWMm + (cols - 1) * config.gutterMm
  const gridH = rows * cellHMm + (rows - 1) * config.gutterMm
  const offsetX = config.marginMm + (printW - gridW) / 2
  const offsetY = config.marginMm + (printH - gridH) / 2

  return { cols, rows, total: cols * rows, offsetX, offsetY }
}

function drawCutGuides(
  pdf: jsPDF,
  layout: EffectiveLayout,
  config: PrintSheetConfig,
  cellW: number,
  cellH: number,
): void {
  const markLen = 3 // mm — length of each crop mark line
  const markOffset = 1.5 // mm — gap between crop mark and cell edge

  pdf.setDrawColor(180, 180, 180) // light grey
  pdf.setLineWidth(0.15)

  if (config.cutGuideStyle === 'dashed-lines') {
    pdf.setLineDashPattern([1.5, 1.5], 0)
  }

  for (let row = 0; row < layout.rows; row++) {
    for (let col = 0; col < layout.cols; col++) {
      const x = layout.offsetX + col * (cellW + config.gutterMm)
      const y = layout.offsetY + row * (cellH + config.gutterMm)

      if (config.cutGuideStyle === 'crop-marks') {
        // Top-left corner
        pdf.line(x - markOffset - markLen, y, x - markOffset, y)
        pdf.line(x, y - markOffset - markLen, x, y - markOffset)

        // Top-right corner
        pdf.line(x + cellW + markOffset, y, x + cellW + markOffset + markLen, y)
        pdf.line(x + cellW, y - markOffset - markLen, x + cellW, y - markOffset)

        // Bottom-left corner
        pdf.line(x - markOffset - markLen, y + cellH, x - markOffset, y + cellH)
        pdf.line(x, y + cellH + markOffset, x, y + cellH + markOffset + markLen)

        // Bottom-right corner
        pdf.line(x + cellW + markOffset, y + cellH, x + cellW + markOffset + markLen, y + cellH)
        pdf.line(x + cellW, y + cellH + markOffset, x + cellW, y + cellH + markOffset + markLen)
      } else {
        // Dashed rectangle around the cell
        pdf.rect(x, y, cellW, cellH)
      }
    }
  }

  // Reset dash pattern
  if (config.cutGuideStyle === 'dashed-lines') {
    pdf.setLineDashPattern([], 0)
  }
}

/**
 * Trigger a browser download for the generated PDF blob.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

