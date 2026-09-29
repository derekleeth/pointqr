<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

const route = useRoute()
const layout = computed(() => route.meta.layout as string | undefined)
</script>

<template>
  <!-- Authenticated app shell with sidebar -->
  <AppLayout v-if="layout === 'AppLayout'">
    <RouterView />
  </AppLayout>

  <!-- Centered auth pages (login, register) -->
  <AuthLayout v-else-if="layout === 'AuthLayout'">
    <RouterView />
  </AuthLayout>

  <!-- Public pages (home) – full-page, self-contained -->
  <RouterView v-else />

  <!-- Global toast notifications -->
  <Toast position="bottom-right" :pt="{ root: { style: 'z-index: 9999' } }" />
</template>
