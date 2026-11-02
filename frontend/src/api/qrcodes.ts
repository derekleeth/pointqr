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

export interface TextLabelOptions {
  enabled: boolean
  text: string
  fontFamily: string
  fontSize: number
  fontWeight: 'normal' | 'bold'
  fontStyle: 'normal' | 'italic'
  color: string
  align: 'left' | 'center' | 'right'
  letterSpacing: number
  padding: number
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
  labelTop: TextLabelOptions
  labelBottom: TextLabelOptions
}

// ---------------------------------------------------------------------------
// Contact (vCard) types – match ContactData in backend/app/schemas/qrcode.py
// ---------------------------------------------------------------------------

export type QRContentType = 'URL' | 'TEXT' | 'VCARD'

export interface ContactPhone {
  type: 'mobile' | 'work' | 'home' | 'fax' | 'other'
  number: string
}

export interface ContactEmail {
  type: 'work' | 'home' | 'other'
  address: string
}

export interface ContactAddress {
  type: 'work' | 'home'
  street: string | null
  city: string | null
  region: string | null
  postal_code: string | null
  country: string | null
}

export interface ContactSocialLink {
  label: string
  url: string
}

export interface ContactData {
  prefix: string | null
  first_name: string | null
  last_name: string | null
  suffix: string | null
  display_name: string | null
  organization: string | null
  job_title: string | null
  phones: ContactPhone[]
  emails: ContactEmail[]
  website: string | null
  address: ContactAddress | null
  note: string | null
  birthday: string | null
  encoding: 'vcard' | 'mecard'
  social_links: ContactSocialLink[]
  photo_url: string | null
  theme_color: string | null
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
  content_type: QRContentType
  content_data: ContactData | null
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
  content_type?: QRContentType
  content_data?: ContactData
  design_config?: Partial<DesignConfig>
}

export interface QRCodeUpdate {
  title?: string
  target_url?: string
  content_type?: QRContentType
  content_data?: ContactData
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
  labelTop: {
    enabled: false,
    text: '',
    fontFamily: 'sans-serif',
    fontSize: 14,
    fontWeight: 'normal',
    fontStyle: 'normal',
    color: '#000000',
    align: 'center',
    letterSpacing: 0,
    padding: 8,
  },
  labelBottom: {
    enabled: false,
    text: '',
    fontFamily: 'sans-serif',
    fontSize: 14,
    fontWeight: 'normal',
    fontStyle: 'normal',
    color: '#000000',
    align: 'center',
    letterSpacing: 0,
    padding: 8,
  },
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

// ---------------------------------------------------------------------------
// Async (Celery) export job types and API functions
// ---------------------------------------------------------------------------

export interface BatchJobRead {
  id: string
  user_id: string
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  total_items: number
  processed_items: number
  result_url: string | null
  created_at: string
}

/** Trigger an async server export — returns a BatchJob with a job ID. */
export function startAsyncExport(qrId: string, format: 'png' | 'svg' | 'pdf' | 'eps') {
  return apiClient.post<BatchJobRead>(`/qrcodes/${qrId}/export/async`, null, {
    params: { format },
  })
}

/** Poll the status of an async export job. */
export function getExportJob(jobId: string) {
  return apiClient.get<BatchJobRead>(`/qrcodes/jobs/${jobId}`)
}

export const uploadContactPhoto = (id: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return apiClient.post<QRCodeRead>(`/qrcodes/${id}/photo`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const uploadLogo = (id: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return apiClient.post<QRCodeRead>(`/qrcodes/${id}/logo`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

