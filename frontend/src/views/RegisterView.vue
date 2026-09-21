<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

async function handleRegister() {
  errorMessage.value = ''
  successMessage.value = ''

  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }
  if (password.value.length < 8) {
    errorMessage.value = 'Password must be at least 8 characters.'
    return
  }

  loading.value = true
  try {
    await auth.register(email.value, password.value)
    // Auto-login after registration
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    errorMessage.value =
      axiosErr.response?.data?.detail ?? 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex justify-center items-center min-h-[70vh]">
    <div class="w-full max-w-md">
      <div class="card p-8 rounded-2xl border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800 shadow-sm">
        <div class="text-center mb-8">
          <span class="text-4xl">🎉</span>
          <h1 class="text-2xl font-bold mt-2 text-surface-900 dark:text-surface-0">
            Create your account
          </h1>
          <p class="text-surface-500 mt-1">Start generating QR codes for free</p>
        </div>

        <form class="flex flex-col gap-4" @submit.prevent="handleRegister">
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium text-surface-700 dark:text-surface-300">Email</label>
            <InputText
              v-model="email"
              type="email"
              placeholder="you@example.com"
              autocomplete="email"
              :disabled="loading"
              required
              class="w-full"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium text-surface-700 dark:text-surface-300">Password</label>
            <Password
              v-model="password"
              placeholder="Min. 8 characters"
              toggle-mask
              input-class="w-full"
              :disabled="loading"
              required
            />
          </div>

          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium text-surface-700 dark:text-surface-300">
              Confirm Password
            </label>
            <Password
              v-model="confirmPassword"
              placeholder="Repeat your password"
              :feedback="false"
              toggle-mask
              input-class="w-full"
              :disabled="loading"
              required
            />
          </div>

          <Message v-if="errorMessage" severity="error" :closable="false">
            {{ errorMessage }}
          </Message>
          <Message v-if="successMessage" severity="success" :closable="false">
            {{ successMessage }}
          </Message>

          <Button
            type="submit"
            label="Create Account"
            icon="pi pi-user-plus"
            :loading="loading"
            class="w-full mt-2"
          />
        </form>

        <p class="text-center text-sm text-surface-500 mt-6">
          Already have an account?
          <RouterLink to="/login" class="text-primary-500 hover:underline font-medium">
            Sign in
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>
