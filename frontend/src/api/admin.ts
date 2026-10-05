import { apiClient } from './client'

export interface AdminUser {
  id: string
  email: string
  is_active: boolean
  is_verified: boolean
  role: 'admin' | 'user'
  tier: 'free' | 'pro' | 'enterprise'
  created_at: string
  qr_code_count: number
  total_scans: number
}

export interface SiteSettings {
  registration_enabled: boolean
}

export const adminApi = {
  /** Fetch all users with usage stats */
  listUsers(): Promise<AdminUser[]> {
    return apiClient.get<AdminUser[]>('/admin/users').then((r) => r.data)
  },

  /** Create a user as admin (bypasses registration_enabled flag) */
  createUser(payload: {
    email: string
    password: string
    role: string
    tier: string
  }): Promise<AdminUser> {
    return apiClient.post<AdminUser>('/admin/users', payload).then((r) => r.data)
  },

  /** Update a user's role */
  updateRole(userId: string, role: string): Promise<AdminUser> {
    return apiClient
      .patch<AdminUser>(`/admin/users/${userId}/role`, { role })
      .then((r) => r.data)
  },

  /** Update a user's tier */
  updateTier(userId: string, tier: string): Promise<AdminUser> {
    return apiClient
      .patch<AdminUser>(`/admin/users/${userId}/tier`, { tier })
      .then((r) => r.data)
  },

  /** Enable or disable a user account */
  updateStatus(userId: string, is_active: boolean): Promise<AdminUser> {
    return apiClient
      .patch<AdminUser>(`/admin/users/${userId}/status`, { is_active })
      .then((r) => r.data)
  },

  /** Permanently delete a user */
  deleteUser(userId: string): Promise<void> {
    return apiClient.delete(`/admin/users/${userId}`).then(() => undefined)
  },

  /** Get current site settings */
  getSettings(): Promise<SiteSettings> {
    return apiClient.get<SiteSettings>('/admin/settings').then((r) => r.data)
  },
}

/** Public endpoint – does not require authentication */
export function fetchRegistrationStatus(): Promise<{ registration_enabled: boolean }> {
  return apiClient
    .get<{ registration_enabled: boolean }>('/auth/registration-status')
    .then((r) => r.data)
}
