import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { useMediaQuery } from '@vueuse/core'

/**
 * How the app shell lays out the sidebar at the current viewport width.
 * - mobile  (< 768 px):    sidebar is an off-canvas drawer opened from a top bar
 * - tablet  (768-1024 px): sidebar is a 64 px rail; expanding it overlays the content
 * - desktop (> 1024 px):   sidebar sits in the layout and honours the saved collapse preference
 */
export type ShellMode = 'mobile' | 'tablet' | 'desktop'

export const useUIStore = defineStore('ui', () => {
  const SIDEBAR_KEY = 'pointqr-sidebar'

  // Desktop collapse preference, restored from localStorage.
  // Only the desktop collapse button changes this, so using a phone or tablet never alters it.
  const sidebarCollapsed = ref(readSaved())

  function readSaved(): boolean {
    try {
      return localStorage.getItem(SIDEBAR_KEY) === 'true'
    } catch {
      return false
    }
  }

  function save(v: boolean) {
    try {
      localStorage.setItem(SIDEBAR_KEY, String(v))
    } catch {
      /* storage unavailable: keep the in-memory value */
    }
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    save(sidebarCollapsed.value)
  }

  function setSidebarCollapsed(v: boolean) {
    sidebarCollapsed.value = v
    save(v)
  }

  // ── Responsive shell ─────────────────────────────────
  const isMobile = useMediaQuery('(max-width: 767.98px)')
  const isTabletOrBelow = useMediaQuery('(max-width: 1024px)')

  const shellMode = computed<ShellMode>(() => {
    if (isMobile.value) return 'mobile'
    if (isTabletOrBelow.value) return 'tablet'
    return 'desktop'
  })

  // Drawer (mobile) or expanded overlay (tablet). Never persisted.
  const navOpen = ref(false)

  function openNav() { navOpen.value = true }
  function closeNav() { navOpen.value = false }
  function toggleNav() { navOpen.value = !navOpen.value }

  // Moving between modes (rotating a tablet, resizing a window) starts closed.
  watch(shellMode, () => { navOpen.value = false })

  /** Whether the sidebar should render as the narrow icon rail right now. */
  const railCollapsed = computed(() => {
    switch (shellMode.value) {
      case 'mobile': return false
      case 'tablet': return !navOpen.value
      default: return sidebarCollapsed.value
    }
  })

  return {
    sidebarCollapsed,
    toggleSidebar,
    setSidebarCollapsed,
    shellMode,
    navOpen,
    openNav,
    closeNav,
    toggleNav,
    railCollapsed,
  }
})
