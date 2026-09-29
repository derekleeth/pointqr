<script setup lang="ts">
import { computed } from 'vue'
import AppSidebar from '@/components/sidebar/AppSidebar.vue'
import { useUIStore } from '@/stores/ui'

const ui = useUIStore()
const collapsed = computed(() => ui.sidebarCollapsed)
</script>

<template>
  <div class="app-layout" :class="{ 'sidebar-collapsed': collapsed }">
    <AppSidebar />

    <div class="app-body">
      <main class="app-main">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background-color: var(--bg-base);
}

.app-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-main {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 2.5rem;
}

@media (max-width: 1024px) {
  .app-main { padding: 1.25rem 1.5rem; }
}

@media (max-width: 640px) {
  .app-main { padding: 1rem; }
}
</style>
