<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  loading.value = true
  errorMessage.value = ''
  try {
    await auth.login(email.value, password.value)
    const redirect = (route.query.redirect as string) ?? '/dashboard'
    router.push(redirect)
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    errorMessage.value = axiosErr.response?.data?.detail ?? 'Login failed. Please try again.'
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
          <span class="text-4xl">📱</span>
          <h1 class="text-2xl font-bold mt-2 text-surface-900 dark:text-surface-0">
            Welcome back
          </h1>
          <p class="text-surface-500 mt-1">Sign in to your PointQR account</p>
        </div>

        <form class="flex flex-col gap-4" @submit.prevent="handleLogin">
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
              placeholder="Your password"
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

          <Button
            type="submit"
            label="Sign In"
            icon="pi pi-sign-in"
            :loading="loading"
            class="w-full mt-2"
          />
        </form>

        <p class="text-center text-sm text-surface-500 mt-6">
          Don't have an account?
          <RouterLink to="/register" class="text-primary-500 hover:underline font-medium">
            Create one free
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>
