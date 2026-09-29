import 'vue-router'

/**
 * Augment vue-router's RouteMeta so route.meta.layout and guards
 * are fully typed without casting to `any`.
 */
declare module 'vue-router' {
  interface RouteMeta {
    /** Which layout component wraps this route's view. */
    layout?: 'AppLayout' | 'AuthLayout'
    /** Redirect unauthenticated users to /login. */
    requiresAuth?: boolean
    /** Redirect authenticated users to /dashboard. */
    guestOnly?: boolean
  }
}

