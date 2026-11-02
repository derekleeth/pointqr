/** Helpers for the string a QR code encodes: byte encoding and density estimates. */

import type { QROptions } from '@/api/qrcodes'

type ErrorCorrectionLevel = QROptions['errorCorrectionLevel']

/** Byte-mode capacity of QR versions 1–40 at each error correction level (ISO 18004). */
const BYTE_CAPACITY: Record<ErrorCorrectionLevel, number[]> = {
  L: [17, 32, 53, 78, 106, 134, 154, 192, 230, 271, 321, 367, 425, 458, 520, 586, 644, 718, 792, 858, 929, 1003, 1091, 1171, 1273, 1367, 1465, 1528, 1628, 1732, 1840, 1952, 2068, 2188, 2303, 2431, 2563, 2699, 2809, 2953],
  M: [14, 26, 42, 62, 84, 106, 122, 152, 180, 213, 251, 287, 331, 362, 412, 450, 504, 560, 624, 666, 711, 779, 857, 911, 997, 1059, 1125, 1190, 1264, 1370, 1452, 1538, 1628, 1722, 1809, 1911, 1989, 2099, 2213, 2331],
  Q: [11, 20, 32, 46, 60, 74, 86, 108, 130, 151, 177, 203, 241, 258, 292, 322, 364, 394, 442, 482, 509, 565, 611, 661, 715, 751, 805, 868, 908, 982, 1030, 1112, 1168, 1228, 1283, 1351, 1423, 1499, 1579, 1663],
  H: [7, 14, 24, 34, 44, 58, 64, 84, 98, 119, 137, 155, 177, 194, 220, 250, 280, 310, 338, 382, 403, 439, 461, 511, 535, 593, 625, 658, 698, 742, 790, 842, 898, 958, 983, 1051, 1093, 1139, 1219, 1273],
}

/** Versions above this get hard to scan: it's the size ~300 bytes needs at ECC H. */
const DENSE_VERSION = 18

export interface QRDensity {
  bytes: number
  /** Smallest QR version that fits, or null if the payload is too large for any version. */
  version: number | null
  modules: number | null
  isDense: boolean
  isTooLarge: boolean
}

export function estimateDensity(content: string, level: ErrorCorrectionLevel): QRDensity {
  const bytes = new TextEncoder().encode(content).length
  const index = BYTE_CAPACITY[level].findIndex((capacity) => bytes <= capacity)
  const version = index === -1 ? null : index + 1
  return {
    bytes,
    version,
    modules: version === null ? null : version * 4 + 17,
    isDense: version !== null && version > DENSE_VERSION,
    isTooLarge: version === null,
  }
}

/**
 * Prepare a string for qr-code-styling so non-ASCII text survives.
 *
 * The library turns each UTF-16 code unit into one byte (charCode & 0xff), which
 * corrupts anything outside Latin-1 and leaves accents in a charset that vCard
 * importers don't expect. Passing one character per UTF-8 byte yields a true
 * UTF-8 payload. ASCII strings come back unchanged.
 */
export function toQRData(content: string): string {
  return Array.from(new TextEncoder().encode(content), (b) => String.fromCharCode(b)).join('')
}
