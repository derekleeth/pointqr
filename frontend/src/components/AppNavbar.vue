<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <nav
    class="w-full border-b border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800 px-6 py-3 flex items-center justify-between"
  >
    <!-- Logo -->
    <RouterLink to="/" class="flex items-center gap-2 no-underline">
      <span class="text-2xl">📱</span>
      <span class="text-xl font-bold text-surface-900 dark:text-surface-0">
        Point<span class="text-primary-500">QR</span>
      </span>
    </RouterLink>

    <!-- Nav links -->
    <div class="flex items-center gap-3">
      <template v-if="auth.isAuthenticated">
        <span class="text-sm text-surface-500 hidden sm:block">{{ auth.user?.email }}</span>
        <Button
          label="Dashboard"
          severity="secondary"
          text
          size="small"
          icon="pi pi-th-large"
          @click="router.push('/dashboard')"
        />
        <Button
          label="Sign Out"
          severity="danger"
          text
          size="small"
          icon="pi pi-sign-out"
          @click="handleLogout"
        />
      </template>
      <template v-else>
        <Button
          label="Sign In"
          severity="secondary"
          text
          size="small"
          @click="router.push('/login')"
        />
        <Button
          label="Get Started"
          size="small"
          icon="pi pi-arrow-right"
          icon-pos="right"
          @click="router.push('/register')"
        />
      </template>
    </div>
  </nav>
</template>
