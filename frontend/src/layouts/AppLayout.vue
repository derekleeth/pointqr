<script setup lang="ts">
import { computed } from 'vue'
import AppSidebar from '@/components/sidebar/AppSidebar.vue'
import { useUIStore } from '@/stores/ui'
import { useThemeStore } from '@/stores/theme'

const ui = useUIStore()
const theme = useThemeStore()

const mode = computed(() => ui.shellMode)
// Drawer (mobile) or expanded overlay (tablet) is open on top of the content
const overlayOpen = computed(() => ui.navOpen && mode.value !== 'desktop')
</script>

<template>
  <div
    class="app-layout"
    :class="[`shell-${mode}`, { 'sidebar-collapsed': ui.railCollapsed }]"
  >
    <AppSidebar />

    <Transition name="backdrop">
      <div
        v-if="overlayOpen"
        class="nav-backdrop"
        aria-hidden="true"
        @click="ui.closeNav()"
      />
    </Transition>

    <div class="app-body" :inert="overlayOpen || undefined">
      <!-- Phone-only top bar with the menu button -->
      <header v-if="mode === 'mobile'" class="mobile-topbar">
        <button
          class="menu-btn"
          type="button"
          aria-label="Open menu"
          aria-controls="app-sidebar"
          :aria-expanded="ui.navOpen"
          @click="ui.openNav()"
        >
          <i class="pi pi-bars" />
        </button>
        <RouterLink to="/dashboard" class="topbar-brand" aria-label="PointQR dashboard">
          <img
            :src="theme.isDark ? '/PointQR-Dark-v2.png' : '/PointQR-Light-v3.png'"
            alt="PointQR"
            class="topbar-logo"
          />
        </RouterLink>
      </header>

      <main class="app-main">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;   /* fallback for browsers without dvh */
  height: 100dvh;  /* follows the mobile browser's visible area */
  overflow: hidden;
  background-color: var(--bg-base);
}

/* Tablet: the sidebar is fixed-position, so reserve room for the 64 px rail */
.app-layout.shell-tablet {
  padding-left: var(--sidebar-wc);
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

/* ── Mobile top bar ───────────────────────────────── */
.mobile-topbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  height: 56px;
  padding: 0 0.5rem;
  flex-shrink: 0;
  background: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
}

.menu-btn {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  background: none;
  color: var(--text-primary);
  font-size: 1.25rem;
  cursor: pointer;
}
.menu-btn:hover { background: var(--bg-hover); }
.menu-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.topbar-brand {
  display: flex;
  align-items: center;
  height: 44px;
}
.topbar-logo {
  height: 52px;
  width: auto;
  object-fit: contain;
}

/* ── Backdrop behind the drawer / tablet overlay ──── */
.nav-backdrop {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.45);
}
.backdrop-enter-active,
.backdrop-leave-active { transition: opacity 0.22s ease; }
.backdrop-enter-from,
.backdrop-leave-to { opacity: 0; }

@media (prefers-reduced-motion: reduce) {
  .backdrop-enter-active,
  .backdrop-leave-active { transition: none; }
}
</style>
