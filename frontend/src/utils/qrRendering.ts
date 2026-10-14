/**
 * Shared QR rendering utilities.
 *
 * Extracted from QRCanvas.vue and DownloadModal.vue to eliminate duplication.
 * Used by the QR editor, download modal, and print sheet generator.
 */

import type { TextLabelOptions } from '@/api/qrcodes'

/**
 * Measure how tall a label will be when rendered at `width` px.
 * Uses an offscreen canvas to get font metrics.
 */
export function measureLabelHeight(
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

/**
 * Draw a label's text onto a Canvas 2D context.
 * `y` is the top of the label band.
 */
export function drawLabel(
  ctx: CanvasRenderingContext2D,
  lbl: TextLabelOptions,
  y: number,
  width: number,
): void {
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

/**
 * Render a full QR code cell (QR bitmap + optional top/bottom labels) onto
 * an offscreen canvas and return the canvas.
 *
 * @param qrBlob - The raw PNG blob from qr-code-styling's getRawData('png')
 * @param cfg    - The design config for label / background info
 * @param size   - The QR bitmap size in pixels
 * @returns A canvas element containing the composited QR cell
 */
export async function renderQRCell(
  qrBlob: Blob,
  cfg: {
    backgroundOptions: { color: string }
    labelTop: TextLabelOptions
    labelBottom: TextLabelOptions
  },
  size: number,
): Promise<HTMLCanvasElement> {
  const topLbl = cfg.labelTop
  const botLbl = cfg.labelBottom

  const topH =
    topLbl.enabled && topLbl.text
      ? measureLabelHeight(topLbl.text, topLbl.fontFamily, topLbl.fontSize, topLbl.fontWeight, size, topLbl.padding)
      : 0
  const botH =
    botLbl.enabled && botLbl.text
      ? measureLabelHeight(botLbl.text, botLbl.fontFamily, botLbl.fontSize, botLbl.fontWeight, size, botLbl.padding)
      : 0

  const totalH = size + topH + botH

  // Decode the QR PNG blob into an ImageBitmap
  const img = await createImageBitmap(qrBlob)

  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = totalH
  const ctx = canvas.getContext('2d')!

  // Background fill
  ctx.fillStyle = cfg.backgroundOptions.color
  ctx.fillRect(0, 0, size, totalH)

  // Top label
  if (topH > 0) drawLabel(ctx, topLbl, 0, size)

  // QR bitmap
  ctx.drawImage(img, 0, topH, size, size)

  // Bottom label
  if (botH > 0) drawLabel(ctx, botLbl, topH + size, size)

  return canvas
}

