<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const stats = [
  { label: 'Total QR Codes', value: '0' },
  { label: 'Total Scans', value: '0' },
  { label: 'Active Dynamic', value: '0' },
  { label: 'Batch Jobs', value: '0' },
]

onMounted(async () => {
  if (!auth.user) {
    await auth.initialize()
  }
})
</script>

<template>
  <div class="flex flex-col gap-8">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-surface-900 dark:text-surface-0">Dashboard</h1>
        <p class="text-surface-500 mt-1">
          Welcome back,
          <span class="font-medium text-surface-700 dark:text-surface-200">{{
            auth.user?.email
          }}</span>!
        </p>
      </div>
      <Button label="New QR Code" icon="pi pi-plus" />
    </div>

    <!-- Stats (placeholder for Phase 4) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="stat in stats"
        :key="stat.label"
        class="p-5 rounded-xl border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800"
      >
        <p class="text-surface-500 text-sm">{{ stat.label }}</p>
        <p class="text-3xl font-bold text-surface-900 dark:text-surface-0 mt-1">{{ stat.value }}</p>
      </div>
    </div>

    <!-- QR Code list (placeholder for Phase 2) -->
    <div
      class="rounded-xl border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800 p-8 flex flex-col items-center gap-4 text-center"
    >
      <span class="text-5xl">✨</span>
      <h2 class="text-xl font-semibold text-surface-900 dark:text-surface-0">
        No QR codes yet
      </h2>
      <p class="text-surface-500 max-w-sm">
        Create your first QR code to get started. Customize the design, add a logo, and track every
        scan.
      </p>
      <Button label="Create Your First QR Code" icon="pi pi-plus" />
    </div>
  </div>
</template>
