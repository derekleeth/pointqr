<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const features = [
  {
    icon: '🎨',
    title: 'Beautiful Customization',
    description: 'Dots, gradients, logos, frames — design QR codes that match your brand.',
  },
  {
    icon: '⚡',
    title: 'Dynamic Redirects',
    description: 'Update your link anytime without reprinting. Sub-15ms redirect latency.',
  },
  {
    icon: '📊',
    title: 'Real-time Analytics',
    description: 'Track scans by location, device, time of day and more.',
  },
]
</script>

<template>
  <section class="flex flex-col items-center justify-center text-center py-24 gap-8">
    <div class="flex flex-col items-center gap-4">
      <span class="text-6xl">📱</span>
      <h1 class="text-5xl font-bold text-surface-900 dark:text-surface-0">
        Point<span class="text-primary-500">QR</span>
      </h1>
      <p class="text-xl text-surface-500 max-w-xl">
        Create, customize, and track beautiful QR codes in seconds.
        Dynamic redirects, real-time analytics, and bulk generation — all in one place.
      </p>
    </div>

    <div class="flex gap-4 flex-wrap justify-center">
      <template v-if="auth.isAuthenticated">
        <Button
          label="Go to Dashboard"
          icon="pi pi-th-large"
          size="large"
          @click="router.push('/dashboard')"
        />
      </template>
      <template v-else>
        <Button
          label="Get Started Free"
          icon="pi pi-arrow-right"
          icon-pos="right"
          size="large"
          @click="router.push('/register')"
        />
        <Button
          label="Sign In"
          severity="secondary"
          size="large"
          @click="router.push('/login')"
        />
      </template>
    </div>

    <!-- Feature highlights -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 max-w-4xl w-full">
      <div
        v-for="feature in features"
        :key="feature.title"
        class="p-6 rounded-xl border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800 text-left"
      >
        <span class="text-3xl">{{ feature.icon }}</span>
        <h3 class="text-lg font-semibold mt-3 mb-1 text-surface-900 dark:text-surface-0">
          {{ feature.title }}
        </h3>
        <p class="text-surface-500 text-sm">{{ feature.description }}</p>
      </div>
    </div>
  </section>
</template>
