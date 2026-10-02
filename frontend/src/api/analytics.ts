/**
 * Analytics API module.
 * Typed wrappers for all /v1/analytics endpoints.
 */

import { apiClient } from './client'

// ---------------------------------------------------------------------------
// Response types (mirrors backend schemas/analytics.py)
// ---------------------------------------------------------------------------

export interface ScanSummary {
  total_scans: number
  unique_ips: number
  total_qr_codes: number
  dynamic_count: number
  static_count: number
}

export interface TimeSeriesPoint {
  period: string   // e.g. "2024-05-01", "2024-05-01 14:00", "2024-05"
  count: number
}

export interface TimeSeriesResponse {
  granularity: 'day' | 'hour' | 'month'
  points: TimeSeriesPoint[]
}

export interface BreakdownItem {
  label: string
  count: number
}

export interface BreakdownResponse {
  items: BreakdownItem[]
}

// ---------------------------------------------------------------------------
// Shared query param type
// ---------------------------------------------------------------------------

export interface AnalyticsParams {
  qr_id?: string
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/** Aggregate summary stats for the current user. */
export const getAnalyticsSummary = (params?: AnalyticsParams) =>
  apiClient.get<ScanSummary>('/analytics/summary', { params })

/** Scans over time, bucketed by granularity. */
export const getScansOverTime = (params: {
  granularity?: 'day' | 'hour' | 'month'
  days?: number
  qr_id?: string
}) => apiClient.get<TimeSeriesResponse>('/analytics/scans-over-time', { params })

/** Scan counts by device type (mobile / tablet / desktop). */
export const getByDevice = (params?: AnalyticsParams) =>
  apiClient.get<BreakdownResponse>('/analytics/by-device', { params })

/** Scan counts by operating system. */
export const getByOS = (params?: AnalyticsParams) =>
  apiClient.get<BreakdownResponse>('/analytics/by-os', { params })

/** Scan counts by browser. */
export const getByBrowser = (params?: AnalyticsParams) =>
  apiClient.get<BreakdownResponse>('/analytics/by-browser', { params })

/** Scan counts by country (ISO 3166-1 alpha-2). */
export const getByCountry = (params?: AnalyticsParams) =>
  apiClient.get<BreakdownResponse>('/analytics/by-country', { params })
