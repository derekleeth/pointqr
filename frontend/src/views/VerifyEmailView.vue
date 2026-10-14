<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { apiClient } from '@/api/client'

const route = useRoute()
const theme = useThemeStore()

const loading = ref(true)
const success = ref(false)
const errorMsg = ref('')

onMounted(async () => {
  const token = route.query.token as string | undefined
  if (!token) {
    errorMsg.value = 'This verification link is invalid or has expired.'
    loading.value = false
    return
  }
  try {
    await apiClient.post(`/auth/verify-email?token=${encodeURIComponent(token)}`)
    success.value = true
  } catch {
    errorMsg.value = 'This verification link is invalid or has expired.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="login-page">
    <!-- Background glow -->
    <div class="page-glow" aria-hidden="true" />

    <!-- Top bar -->
    <header class="login-topbar">
      <RouterLink to="/" class="brand-link">
        <div class="brand-icon"><i class="pi pi-stop-circle" /></div>
        <span class="brand-name">PointQR</span>
      </RouterLink>
      <button class="theme-btn" @click="theme.toggle()" :title="theme.isDark ? 'Light mode' : 'Dark mode'">
        <i :class="theme.isDark ? 'pi pi-sun' : 'pi pi-moon'" />
      </button>
    </header>

    <!-- Centered card -->
    <main class="login-main">
      <div class="login-card">
        <!-- Loading -->
        <div v-if="loading" class="state-block">
          <ProgressSpinner style="width: 40px; height: 40px" />
          <p class="state-text">Verifying your email…</p>
        </div>

        <!-- Success -->
        <div v-else-if="success" class="state-block">
          <div class="state-icon-wrap success-wrap">
            <i class="pi pi-check-circle state-icon success-icon" />
          </div>
          <h1 class="card-title">Email verified!</h1>
          <p class="card-subtitle">Your email has been verified. You can now sign in to your account.</p>
          <RouterLink to="/login">
            <Button label="Sign in" icon="pi pi-sign-in" class="w-full mt-btn" />
          </RouterLink>
        </div>

        <!-- Error -->
        <div v-else class="state-block">
          <div class="state-icon-wrap error-wrap">
            <i class="pi pi-times-circle state-icon error-icon" />
          </div>
          <h1 class="card-title">Verification failed</h1>
          <p class="card-subtitle">{{ errorMsg }}</p>
          <p class="hint-text">
            Need a new link?
            <RouterLink to="/login" class="card-link">Go back to sign in</RouterLink>
            and use the "Resend verification email" option.
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ── Page shell (identical to LoginView) ─────── */
.login-page {
  min-height: 100vh;
  background-color: var(--bg-base);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.page-glow {
  position: fixed;
  top: -20%;
  left: 50%;
  transform: translateX(-50%);
  width: 800px;
  height: 600px;
  background: radial-gradient(ellipse at center, var(--color-primary-soft) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

/* ── Top bar ─────────────────────────────────── */
.login-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 2rem;
  position: relative;
  z-index: 1;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--text-primary);
  font-weight: 700;
  font-size: 0.9375rem;
  letter-spacing: -0.02em;
}
.brand-icon {
  width: 28px;
  height: 28px;
  border-radius: 7px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
}
.brand-name { color: var(--text-primary); }

.theme-btn {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: none;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.theme-btn:hover { background: var(--bg-hover); color: var(--text-primary); }

/* ── Main card area ──────────────────────────── */
.login-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.5rem;
  position: relative;
  z-index: 1;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 2.5rem 2rem;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.12);
}

/* ── State blocks ────────────────────────────── */
.state-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.875rem;
}

.state-icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.25rem;
}

.success-wrap {
  background: rgba(34, 197, 94, 0.12);
}

.error-wrap {
  background: rgba(239, 68, 68, 0.1);
}

.state-icon {
  font-size: 2rem;
}

.success-icon { color: #16a34a; }
.error-icon   { color: #ef4444; }

.card-title {
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--text-primary);
  margin: 0;
}

.card-subtitle {
  font-size: 0.9375rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
}

.state-text {
  font-size: 0.9375rem;
  color: var(--text-secondary);
  margin: 0;
}

.hint-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.card-link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}
.card-link:hover { text-decoration: underline; }

.mt-btn { margin-top: 0.5rem; }
</style>
