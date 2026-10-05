import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ── Public ───────────────────────────────────────────
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      // No layout – HomeView is self-contained with its own nav
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { layout: 'AuthLayout', guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { layout: 'AuthLayout', guestOnly: true },
    },

    // ── Authenticated (sidebar layout) ───────────────────
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { layout: 'AppLayout', requiresAuth: true },
    },
    {
      path: '/editor',
      name: 'editor-new',
      component: () => import('@/views/QREditorView.vue'),
      meta: { layout: 'AppLayout', requiresAuth: true },
    },
    {
      path: '/editor/:id',
      name: 'editor-edit',
      component: () => import('@/views/QREditorView.vue'),
      meta: { layout: 'AppLayout', requiresAuth: true },
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: () => import('@/views/AnalyticsView.vue'),
      meta: { layout: 'AppLayout', requiresAuth: true },
    },

    // ── Admin (sidebar layout, admin role required) ───────
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('@/views/AdminUsersView.vue'),
      meta: { layout: 'AppLayout', requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/settings',
      name: 'admin-settings',
      component: () => import('@/views/AdminSettingsView.vue'),
      meta: { layout: 'AppLayout', requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/monitor',
      name: 'admin-monitor',
      component: () => import('@/views/AdminMonitorView.vue'),
      meta: { layout: 'AppLayout', requiresAuth: true, requiresAdmin: true },
    },
  ],
})

// Global navigation guard
router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }

  if (to.meta.requiresAdmin && auth.user?.role !== 'admin') {
    return { name: 'dashboard' }
  }
})

export default router
