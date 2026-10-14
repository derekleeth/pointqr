import { apiClient } from './client'

export interface APIKeyInfo {
  has_key: boolean
  key_hint: string | null
  created_at: string | null
}

export interface APIKeyCreated {
  api_key: string
  key_hint: string
  created_at: string
  message: string
}

export async function getAPIKeyInfo() {
  return apiClient.get<APIKeyInfo>('/apikeys')
}

export async function generateAPIKey() {
  return apiClient.post<APIKeyCreated>('/apikeys')
}

export async function revokeAPIKey() {
  return apiClient.delete('/apikeys')
}
