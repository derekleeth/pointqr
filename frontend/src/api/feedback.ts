import { apiClient } from './client'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type FeedbackType = 'bug' | 'feature_request' | 'feedback' | 'question'
export type FeedbackStatus = 'open' | 'in_progress' | 'resolved' | 'closed'

export interface FeedbackSubmission {
  id: string
  type: FeedbackType
  subject: string
  message: string
  status: FeedbackStatus
  github_issue_url: string | null
  github_issue_number: number | null
  created_at: string
}

export interface FeedbackAdminItem {
  id: string
  user_id: string
  user_email: string
  type: FeedbackType
  subject: string
  message: string
  status: FeedbackStatus
  github_issue_url: string | null
  github_issue_number: number | null
  slack_notified: boolean
  admin_notes: string | null
  created_at: string
  updated_at: string
}

export interface FeedbackCreatePayload {
  type: FeedbackType
  subject: string
  message: string
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

export const feedbackApi = {
  /** Submit feedback (authenticated user) */
  submit(payload: FeedbackCreatePayload): Promise<FeedbackSubmission> {
    return apiClient
      .post<FeedbackSubmission>('/feedback', payload)
      .then((r) => r.data)
  },

  /** List own submissions */
  listOwn(): Promise<FeedbackSubmission[]> {
    return apiClient
      .get<FeedbackSubmission[]>('/feedback')
      .then((r) => r.data)
  },

  /** Admin: list all submissions */
  adminList(): Promise<FeedbackAdminItem[]> {
    return apiClient
      .get<FeedbackAdminItem[]>('/feedback/admin')
      .then((r) => r.data)
  },

  /** Admin: update status */
  adminUpdate(
    id: string,
    payload: { status: FeedbackStatus; admin_notes?: string | null },
  ): Promise<FeedbackAdminItem> {
    return apiClient
      .patch<FeedbackAdminItem>(`/feedback/admin/${id}`, payload)
      .then((r) => r.data)
  },

  /** Admin: delete submission */
  adminDelete(id: string): Promise<void> {
    return apiClient.delete(`/feedback/admin/${id}`).then(() => undefined)
  },
}

