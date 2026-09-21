/**
 * QR Code API module.
 * All types and functions for interacting with the /v1/qrcodes endpoints.
 */

import { apiClient } from './client'

// ---------------------------------------------------------------------------
// Design config types (mirrors backend DesignConfig schema and qr-code-styling)
// ---------------------------------------------------------------------------

export interface QROptions {
  errorCorrectionLevel: 'L' | 'M' | 'Q' | 'H'
}

export interface DotsOptions {
  color: string
  type: 'square' | 'dots' | 'rounded' | 'classy' | 'classy-rounded' | 'extra-rounded'
}

export interface BackgroundOptions {
  color: string
}

export interface CornersSquareOptions {
  color: string
  type: 'square' | 'dot' | 'extra-rounded'
}

export interface CornersDotOptions {
  color: string
  type: 'square' | 'dot'
}

export interface ImageOptions {
  src: string | null
  margin: number
  imageSize: number
  hideBackgroundDots: boolean
}

export interface DesignConfig {
  content: string
  width: number
  height: number
  margin: number
  qrOptions: QROptions
  dotsOptions: DotsOptions
  backgroundOptions: BackgroundOptions
  cornersSquareOptions: CornersSquareOptions
  cornersDotOptions: CornersDotOptions
  imageOptions: ImageOptions
}

// ---------------------------------------------------------------------------
// QR code resource types
// ---------------------------------------------------------------------------

export interface QRCodeRead {
  id: string
  user_id: string
  title: string
  type: 'STATIC' | 'DYNAMIC'
  short_code: string | null
  target_url: string | null
  design_config: DesignConfig | null
  is_active: boolean
  scan_count: number
  created_at: string
  updated_at: string
}

export interface QRCodeListResponse {
  items: QRCodeRead[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface QRCodeCreate {
  title: string
  type: 'STATIC' | 'DYNAMIC'
  target_url?: string
  design_config?: Partial<DesignConfig>
}

export interface QRCodeUpdate {
  title?: string
  target_url?: string
  design_config?: Partial<DesignConfig>
  is_active?: boolean
}

// ---------------------------------------------------------------------------
// Default design config – used when creating a fresh QR code
// ---------------------------------------------------------------------------

export const DEFAULT_DESIGN_CONFIG: DesignConfig = {
  content: '',
  width: 300,
  height: 300,
  margin: 10,
  qrOptions: { errorCorrectionLevel: 'H' },
  dotsOptions: { color: '#000000', type: 'square' },
  backgroundOptions: { color: '#ffffff' },
  cornersSquareOptions: { color: '#000000', type: 'square' },
  cornersDotOptions: { color: '#000000', type: 'square' },
  imageOptions: { src: null, margin: 5, imageSize: 0.4, hideBackgroundDots: true },
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export const listQRCodes = (page = 1, perPage = 20) =>
  apiClient.get<QRCodeListResponse>('/qrcodes', { params: { page, per_page: perPage } })

export const createQRCode = (data: QRCodeCreate) =>
  apiClient.post<QRCodeRead>('/qrcodes', data)

export const getQRCode = (id: string) =>
  apiClient.get<QRCodeRead>(`/qrcodes/${id}`)

export const updateQRCode = (id: string, data: QRCodeUpdate) =>
  apiClient.patch<QRCodeRead>(`/qrcodes/${id}`, data)

export const deleteQRCode = (id: string) =>
  apiClient.delete(`/qrcodes/${id}`)

export const exportQRCode = (id: string, format: 'png' | 'svg' | 'pdf' | 'eps') =>
  apiClient.post(`/qrcodes/${id}/export`, null, {
    params: { format },
    responseType: 'blob',
  })

export const uploadLogo = (id: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return apiClient.post<QRCodeRead>(`/qrcodes/${id}/logo`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
