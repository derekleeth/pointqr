<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEventListener } from '@vueuse/core'
import { useUIStore } from '@/stores/ui'
import { useThemeStore } from '@/stores/theme'
import { useAuthStore } from '@/stores/auth'

const ui = useUIStore()
const theme = useThemeStore()
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const mode = computed(() => ui.shellMode)
const collapsed = computed(() => ui.railCollapsed)

// The drawer (mobile) and the expanded tablet overlay sit on top of the
// content, so they behave like a modal: focus is trapped, Escape closes.
const isModal = computed(() => ui.navOpen && mode.value !== 'desktop')

const root = ref<HTMLElement | null>(null)
const toggleBtn = ref<HTMLButtonElement | null>(null)

const toggleLabel = computed(() => {
  if (mode.value === 'mobile') return 'Close menu'
  return collapsed.value ? 'Expand sidebar' : 'Collapse sidebar'
})
const toggleIcon = computed(() => {
  if (mode.value === 'mobile') return 'pi pi-times'
  return collapsed.value ? 'pi pi-chevron-right' : 'pi pi-chevron-left'
})

function onToggle() {
  if (mode.value === 'desktop') ui.toggleSidebar() // saved preference
  else ui.toggleNav()                              // never saved
}

// Close the drawer / overlay whenever the route changes
watch(() => route.fullPath, () => ui.closeNav())

// Move focus in when opened, give it back when closed
let returnFocus: HTMLElement | null = null
watch(isModal, async (open) => {
  if (open) {
    returnFocus = document.activeElement as HTMLElement | null
    await nextTick()
    toggleBtn.value?.focus()
  } else if (returnFocus) {
    const el = returnFocus
    returnFocus = null
    if (document.contains(el) && el.getClientRects().length) el.focus()
  }
})

const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'

function focusables(): HTMLElement[] {
  if (!root.value) return []
  return Array.from(root.value.querySelectorAll<HTMLElement>(FOCUSABLE))
    .filter((el) => el.getClientRects().length > 0)
}

useEventListener(document, 'keydown', (e: KeyboardEvent) => {
  if (!isModal.value) return
  if (e.key === 'Escape') {
    e.preventDefault()
    ui.closeNav()
    return
  }
  if (e.key !== 'Tab') return
  const items = focusables()
  if (!items.length) return
  const first = items[0]
  const last = items[items.length - 1]
  const active = document.activeElement as HTMLElement | null
  const inside = !!active && !!root.value?.contains(active)
  if (e.shiftKey && (active === first || !inside)) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && (active === last || !inside)) {
    e.preventDefault()
    first.focus()
  }
})

interface NavItem {
  label: string
  icon: string
  to: string
  soon?: boolean
  exact?: boolean
}

interface NavGroup {
  id: string
  label: string
  items: NavItem[]
}

const navGroups = computed<NavGroup[]>(() => {
  const groups: NavGroup[] = [
    {
      id: 'overview',
      label: 'Overview',
      items: [
        { label: 'Dashboard', icon: 'pi pi-home', to: '/dashboard', exact: true },
      ],
    },
    {
      id: 'qrcodes',
      label: 'QR Codes',
      items: [
        { label: 'All QR Codes', icon: 'pi pi-th-large', to: '/dashboard' },
        { label: 'Create New', icon: 'pi pi-plus-circle', to: '/editor', exact: true },
      ],
    },
    {
      id: 'analytics',
      label: 'Analytics',
      items: [
        { label: 'Scan Analytics', icon: 'pi pi-chart-bar', to: '/analytics' },
        { label: 'Batch Jobs', icon: 'pi pi-inbox', to: '/batch', soon: true },
      ],
    },
    {
      id: 'account',
      label: 'Account',
      items: [
        { label: 'API Keys', icon: 'pi pi-key', to: '/api-keys' },
        { label: 'API Docs', icon: 'pi pi-book', to: '/api-docs' },
        { label: 'Settings', icon: 'pi pi-cog', to: '/settings' },
        { label: 'Feedback', icon: 'pi pi-comments', to: '/feedback' },
      ],
    },
  ]

  if (auth.user?.role === 'admin') {
    groups.push({
      id: 'admin',
      label: 'Admin',
      items: [
        { label: 'Users', icon: 'pi pi-users', to: '/admin/users' },
        { label: 'Site Settings', icon: 'pi pi-sliders-h', to: '/admin/settings' },
        { label: 'Queue Monitor', icon: 'pi pi-chart-line', to: '/admin/monitor' },
        { label: 'Feedback', icon: 'pi pi-comments', to: '/admin/feedback' },
      ],
    })
  }

  return groups
})

function isActive(item: NavItem): boolean {
  if (item.to === '/dashboard') return route.path === '/dashboard'
  if (item.exact) return route.path === item.to
  return route.path === item.to || route.path.startsWith(item.to + '/')
}

const userInitial = computed(() =>
  (auth.user?.email ?? 'U')[0].toUpperCase()
)

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <aside
    id="app-sidebar"
    ref="root"
    class="sidebar"
    :class="[`mode-${mode}`, { 'is-collapsed': collapsed, 'is-open': ui.navOpen }]"
    :role="isModal ? 'dialog' : undefined"
    :aria-modal="isModal ? 'true' : undefined"
    aria-label="Main navigation"
    :inert="(mode === 'mobile' && !ui.navOpen) || undefined"
  >

    <!-- ── Header ─────────────────────────── -->
    <div class="sidebar-header">
      <RouterLink
        to="/dashboard"
        class="brand"
        v-tooltip.right="collapsed ? 'Dashboard' : undefined"
      >
        <img
          :src="theme.isDark ? '/PointQR-Dark-v2.png' : '/PointQR-Light-v3.png'"
          alt="PointQR"
          class="brand-logo"
          v-show="!collapsed"
        />
        <!-- Collapsed: show a small square crop of the logo -->
        <img
          :src="theme.isDark ? '/PointQR-Dark-v2.png' : '/PointQR-Light-v3.png'"
          alt="PointQR"
          class="brand-logo-icon"
          v-show="collapsed"
        />
      </RouterLink>

      <button
        ref="toggleBtn"
        type="button"
        class="collapse-btn"
        @click="onToggle"
        v-tooltip.right="mode === 'desktop' ? toggleLabel : undefined"
        :aria-label="toggleLabel"
        :aria-expanded="mode === 'desktop' ? undefined : ui.navOpen"
        aria-controls="app-sidebar"
      >
        <i :class="toggleIcon" />
      </button>
    </div>

    <!-- ── Navigation ─────────────────────── -->
    <nav class="sidebar-nav">
      <div
        v-for="group in navGroups"
        :key="group.id"
        class="nav-section"
        :class="{ 'is-admin': group.id === 'admin' }"
      >

        <p class="section-label" v-show="!collapsed">{{ group.label }}</p>
        <div class="section-divider" v-show="collapsed" />

        <component
          :is="item.soon ? 'span' : 'RouterLink'"
          v-for="item in group.items"
          :key="item.label"
          v-bind="item.soon ? {} : { to: item.to }"
          class="nav-item"
          :class="{
            'is-active': isActive(item),
            'is-soon': item.soon,
            'is-admin-item': group.id === 'admin',
          }"
          v-tooltip.right="collapsed ? item.label : undefined"
        >
          <i :class="item.icon" class="nav-icon" />
          <span class="nav-label" v-show="!collapsed">{{ item.label }}</span>
          <span class="badge-soon" v-if="item.soon && !collapsed">Soon</span>
        </component>
      </div>
    </nav>

    <!-- ── Footer ─────────────────────────── -->
    <div class="sidebar-footer">
      <!-- GitHub source link -->
      <a
        href="https://github.com/derekleeth/pointqr"
        target="_blank"
        rel="noopener noreferrer"
        class="footer-row"
        v-tooltip.right="collapsed ? 'Source Code (GitHub)' : undefined"
      >
        <i class="pi pi-github nav-icon" />
        <span v-show="!collapsed">GitHub</span>
      </a>

      <!-- Theme toggle -->
      <button class="footer-row" @click="theme.toggle()"
        v-tooltip.right="collapsed ? (theme.isDark ? 'Light mode' : 'Dark mode') : undefined">
        <i :class="theme.isDark ? 'pi pi-sun' : 'pi pi-moon'" class="nav-icon" />
        <span v-show="!collapsed">{{ theme.isDark ? 'Light mode' : 'Dark mode' }}</span>
      </button>

      <!-- User avatar + info -->
      <div class="user-row" v-tooltip.right="collapsed ? auth.user?.email : undefined">
        <div class="avatar">{{ userInitial }}</div>
        <div class="user-meta" v-show="!collapsed">
          <p class="user-email">{{ auth.user?.email }}</p>
          <p class="user-tier">{{ auth.user?.tier }}</p>
        </div>
      </div>

      <!-- Logout -->
      <button class="footer-row danger-row" @click="logout"
        v-tooltip.right="collapsed ? 'Logout' : undefined">
        <i class="pi pi-sign-out nav-icon" />
        <span v-show="!collapsed">Logout</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
/* ── Shell ──────────────────────────────────────────── */
.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  transition: width 0.22s ease, min-width 0.22s ease;
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}
.sidebar.is-collapsed {
  width: var(--sidebar-wc);
  min-width: var(--sidebar-wc);
}

/* Tablet (768-1024 px): a fixed 64 px rail; expanding overlays the content */
.sidebar.mode-tablet {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  height: auto;
  z-index: 1000;
}
.sidebar.mode-tablet.is-open {
  box-shadow: 0 0 32px rgba(0, 0, 0, 0.25);
}

/* Phone (< 768 px): an off-canvas drawer */
.sidebar.mode-mobile {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  height: auto;
  width: min(var(--sidebar-w) + 40px, 85vw);
  min-width: 0;
  z-index: 1000;
  transform: translateX(-100%);
  visibility: hidden;
  transition: transform 0.22s ease, visibility 0s linear 0.22s;
}
.sidebar.mode-mobile.is-open {
  transform: none;
  visibility: visible;
  box-shadow: 0 0 32px rgba(0, 0, 0, 0.3);
  transition: transform 0.22s ease, visibility 0s;
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar.mode-mobile,
  .sidebar.mode-mobile.is-open { transition: none; }
}

/* ── Header ─────────────────────────────────────────── */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100px;
  padding: 0 0.75rem;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.is-collapsed .sidebar-header {
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.25rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  text-decoration: none;
  min-width: 0;
  overflow: hidden;
}
.is-collapsed .brand {
  justify-content: center;
}
.brand-logo {
  height: 120px;
  width: auto;
  max-width: 130px;
  object-fit: contain;
  flex-shrink: 0;
}
.brand-logo-icon {
  width: 48px;
  height: 48px;
  object-fit: cover;
  object-position: left center;
  border-radius: 6px;
  flex-shrink: 0;
}

.collapse-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.65rem;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.collapse-btn { position: relative; }
/* Keep the 24 px look but give it a 44 px hit area */
.collapse-btn::before {
  content: '';
  position: absolute;
  inset: -10px;
}
.collapse-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.collapse-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

/* ── Navigation ─────────────────────────────────────── */
.sidebar-nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.375rem 0;
}

.nav-section { margin-bottom: 0.125rem; }

.section-label {
  margin: 0;
  padding: 0.5rem 0.875rem 0.25rem;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.055em;
  color: var(--text-muted);
  white-space: nowrap;
}
.section-divider {
  height: 1px;
  background: var(--border);
  margin: 0.375rem 0.75rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.46rem 0.75rem;
  margin: 0.1rem 0.5rem;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.14s, color 0.14s;
  position: relative;
  border: none;
  background: none;
}
.is-collapsed .nav-item {
  justify-content: center;
  padding: 0.56rem;
  margin: 0.1rem auto;
  width: calc(100% - 1rem);
  gap: 0;
}
.nav-item:not(.is-soon):hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.nav-item.is-active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}
.nav-item.is-soon { opacity: 0.45; cursor: not-allowed; }

/* Admin section styling */
.nav-section.is-admin {
  margin-top: 0.25rem;
  padding-top: 0.25rem;
  border-top: 1px solid var(--border);
}
.nav-section.is-admin .section-label {
  color: #f59e0b;
}
.nav-item.is-admin-item:not(.is-soon):hover {
  background: rgba(245, 158, 11, 0.08);
  color: #d97706;
}
.nav-item.is-admin-item.is-active {
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
}

.nav-icon { font-size: 0.875rem; width: 16px; text-align: center; flex-shrink: 0; }
.nav-label { flex: 1; overflow: hidden; text-overflow: ellipsis; }

.badge-soon {
  font-size: 0.625rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  background: var(--bg-elevated);
  color: var(--text-muted);
  flex-shrink: 0;
}

/* ── Footer ─────────────────────────────────────────── */
.sidebar-footer {
  border-top: 1px solid var(--border);
  padding: 0.375rem 0;
  flex-shrink: 0;
}

.footer-row {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.46rem 0.75rem;
  margin: 0.1rem 0.5rem;
  border-radius: 8px;
  width: calc(100% - 1rem);
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  white-space: nowrap;
  text-decoration: none;
  transition: background 0.14s, color 0.14s;
}
.is-collapsed .footer-row {
  justify-content: center;
  padding: 0.56rem;
  gap: 0;
}
.footer-row:hover { background: var(--bg-hover); color: var(--text-primary); }
.danger-row:hover { background: rgba(239, 68, 68, 0.08); color: #ef4444; }

.user-row {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.46rem 0.75rem;
  margin: 0.1rem 0.5rem;
}
.is-collapsed .user-row {
  justify-content: center;
  padding: 0.56rem;
  gap: 0;
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8125rem;
  font-weight: 700;
  flex-shrink: 0;
}

.user-meta { flex: 1; min-width: 0; overflow: hidden; }
.user-email {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-tier {
  font-size: 0.6875rem;
  color: var(--text-muted);
  margin: 0;
  text-transform: capitalize;
}

/* ── Touch sizing: 44 px tap targets ────────────────── */
/* Applies on phones and tablets, and on any touch-first device. Desktop
   with a mouse keeps the compact rows. */
.mode-mobile .nav-item,
.mode-mobile .footer-row,
.mode-tablet .nav-item,
.mode-tablet .footer-row {
  min-height: 44px;
}
/* Phones are short: scroll the whole drawer as one column rather than
   pinning the footer and leaving a small scrolling nav in between */
.sidebar.mode-mobile {
  overflow-y: auto;
  overscroll-behavior: contain;
}
.mode-mobile .sidebar-nav {
  flex: none;
  overflow: visible;
}
.mode-mobile .sidebar-header { height: 80px; }
.mode-mobile .collapse-btn {
  width: 44px;
  height: 44px;
  font-size: 0.875rem;
  border: none;
}
@media (pointer: coarse) {
  .nav-item,
  .footer-row { min-height: 44px; }
}
</style>
