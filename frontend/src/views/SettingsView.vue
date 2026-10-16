<script setup lang="ts">
import { ref } from 'vue'
import { apiClient } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

async function handleChangePassword() {
  successMessage.value = ''
  errorMessage.value = ''

  if (newPassword.value.length < 8) {
    errorMessage.value = 'New password must be at least 8 characters.'
    return
  }

  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'New passwords do not match.'
    return
  }

  if (currentPassword.value === newPassword.value) {
    errorMessage.value = 'New password must be different from current password.'
    return
  }

  loading.value = true
  try {
    await apiClient.put('/auth/change-password', {
      current_password: currentPassword.value,
      new_password: newPassword.value,
    })
    successMessage.value = 'Password changed successfully.'
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (err: any) {
    const detail = err.response?.data?.detail
    errorMessage.value = typeof detail === 'string' ? detail : 'Failed to change password. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-8 max-w-3xl">
    <!-- Header -->
    <div>
      <h1 class="text-3xl font-bold text-surface-900 dark:text-surface-0">Settings</h1>
      <p class="text-surface-500 mt-1">
        Manage your account settings and preferences.
      </p>
    </div>

    <!-- Account Info Card -->
    <div
      class="rounded-xl border p-6 transition-colors duration-200"
      style="background-color: var(--bg-card); border-color: var(--border)"
    >
      <div class="flex items-center gap-3 mb-4">
        <span
          class="flex items-center justify-center w-10 h-10 rounded-lg"
          style="background-color: var(--color-primary-soft)"
        >
          <i class="pi pi-user text-lg text-primary-500 dark:text-primary-400" />
        </span>
        <div>
          <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">
            Account Information
          </h2>
          <p class="text-sm" style="color: var(--text-secondary)">
            Your account details
          </p>
        </div>
      </div>

      <div class="space-y-3">
        <div class="flex items-center gap-3">
          <span class="text-sm font-medium w-20" style="color: var(--text-secondary)">Email</span>
          <span class="text-sm font-mono text-surface-900 dark:text-surface-0">{{ auth.user?.email }}</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-sm font-medium w-20" style="color: var(--text-secondary)">Tier</span>
          <Tag :value="auth.user?.tier" severity="info" class="capitalize" />
        </div>
        <div class="flex items-center gap-3">
          <span class="text-sm font-medium w-20" style="color: var(--text-secondary)">Role</span>
          <Tag :value="auth.user?.role" :severity="auth.user?.role === 'admin' ? 'warn' : 'secondary'" class="capitalize" />
        </div>
      </div>
    </div>

    <!-- Change Password Card -->
    <div
      class="rounded-xl border p-6 transition-colors duration-200"
      style="background-color: var(--bg-card); border-color: var(--border)"
    >
      <div class="flex items-center gap-3 mb-6">
        <span
          class="flex items-center justify-center w-10 h-10 rounded-lg"
          style="background-color: var(--color-primary-soft)"
        >
          <i class="pi pi-lock text-lg text-primary-500 dark:text-primary-400" />
        </span>
        <div>
          <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">
            Change Password
          </h2>
          <p class="text-sm" style="color: var(--text-secondary)">
            Update your password to keep your account secure
          </p>
        </div>
      </div>

      <!-- Success Message -->
      <Message v-if="successMessage" severity="success" :closable="false" class="mb-4">
        {{ successMessage }}
      </Message>

      <!-- Error Message -->
      <Message v-if="errorMessage" severity="error" :closable="false" class="mb-4">
        {{ errorMessage }}
      </Message>

      <form @submit.prevent="handleChangePassword" class="space-y-4">
        <div class="flex flex-col gap-1.5">
          <label
            for="current-password"
            class="text-sm font-medium text-surface-900 dark:text-surface-0"
          >
            Current Password
          </label>
          <Password
            id="current-password"
            v-model="currentPassword"
            :feedback="false"
            toggleMask
            fluid
            placeholder="Enter your current password"
            inputClass="w-full"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label
            for="new-password"
            class="text-sm font-medium text-surface-900 dark:text-surface-0"
          >
            New Password
          </label>
          <Password
            id="new-password"
            v-model="newPassword"
            toggleMask
            fluid
            placeholder="Enter your new password"
            inputClass="w-full"
          />
          <small style="color: var(--text-muted)">Minimum 8 characters</small>
        </div>

        <div class="flex flex-col gap-1.5">
          <label
            for="confirm-password"
            class="text-sm font-medium text-surface-900 dark:text-surface-0"
          >
            Confirm New Password
          </label>
          <Password
            id="confirm-password"
            v-model="confirmPassword"
            :feedback="false"
            toggleMask
            fluid
            placeholder="Confirm your new password"
            inputClass="w-full"
          />
        </div>

        <div class="pt-2">
          <Button
            type="submit"
            label="Update Password"
            icon="pi pi-check"
            :loading="loading"
            :disabled="!currentPassword || !newPassword || !confirmPassword"
          />
        </div>
      </form>
    </div>
  </div>
</template>
