import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { apiClient } from '@/api/client'

export interface User {
  id: string
  email: string
  role: 'admin' | 'user'
  tier: 'free' | 'pro' | 'enterprise'
  is_active: boolean
  is_verified: boolean
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const user = ref<User | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!accessToken.value)

  // Actions
  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearTokens() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function login(email: string, password: string): Promise<void> {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await apiClient.post<{ access_token: string; refresh_token: string }>(
      '/auth/login',
      formData,
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
    )
    setTokens(response.data.access_token, response.data.refresh_token)
    await fetchMe()
  }

  async function register(email: string, password: string): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', { email, password })
    return response.data
  }

  async function fetchMe(): Promise<void> {
    const response = await apiClient.get<User>('/auth/me')
    user.value = response.data
  }

  async function refresh(): Promise<void> {
    if (!refreshToken.value) throw new Error('No refresh token')
    const response = await apiClient.post<{ access_token: string; refresh_token: string }>(
      '/auth/refresh',
      { refresh_token: refreshToken.value },
    )
    setTokens(response.data.access_token, response.data.refresh_token)
  }

  function logout(): void {
    clearTokens()
  }

  // Restore user on page load if token exists
  async function initialize(): Promise<void> {
    if (accessToken.value) {
      try {
        await fetchMe()
      } catch {
        clearTokens()
      }
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    refresh,
    initialize,
  }
})
