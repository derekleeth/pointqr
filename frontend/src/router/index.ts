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
})

export default router

