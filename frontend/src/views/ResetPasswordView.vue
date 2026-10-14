<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { apiClient } from '@/api/client'

const route = useRoute()
const theme = useThemeStore()

const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const success = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''

  if (!newPassword.value || !confirmPassword.value) {
    error.value = 'Please fill in both password fields.'
    return
  }
  if (newPassword.value.length < 8) {
    error.value = 'Password must be at least 8 characters.'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    return
  }

  const token = route.query.token as string | undefined
  if (!token) {
    error.value = 'This reset link is invalid or has expired. Please request a new one.'
    return
  }

  loading.value = true
  try {
    await apiClient.post('/auth/reset-password', { token, new_password: newPassword.value })
    success.value = true
  } catch (e: any) {
    if (e?.response?.status === 400) {
      error.value = 'This reset link is invalid or has expired. Please request a new one.'
    } else {
      error.value = 'Something went wrong. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
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
        <!-- Success state -->
        <div v-if="success" class="state-block">
          <div class="state-icon-wrap success-wrap">
            <i class="pi pi-check-circle state-icon success-icon" />
          </div>
          <h1 class="card-title">Password reset!</h1>
          <p class="card-subtitle">Your password has been updated. You can now sign in with your new password.</p>
          <RouterLink to="/login">
            <Button label="Sign in" icon="pi pi-sign-in" class="w-full mt-btn" />
          </RouterLink>
        </div>

        <!-- Form state -->
        <template v-else>
          <div class="card-header">
            <h1 class="card-title">Set new password</h1>
            <p class="card-subtitle">Choose a strong password for your account.</p>
          </div>

          <!-- Error -->
          <div class="error-msg" v-if="error">
            <i class="pi pi-exclamation-circle" />
            {{ error }}
          </div>

          <form @submit.prevent="handleSubmit" class="login-form" novalidate>
            <div class="field">
              <label for="new-password" class="field-label">New password</label>
              <Password
                id="new-password"
                v-model="newPassword"
                placeholder="Min. 8 characters"
                class="w-full"
                :feedback="true"
                toggle-mask
                :input-style="{ width: '100%' }"
                autocomplete="new-password"
                :disabled="loading"
              />
            </div>

            <div class="field">
              <label for="confirm-password" class="field-label">Confirm password</label>
              <Password
                id="confirm-password"
                v-model="confirmPassword"
                placeholder="••••••••"
                class="w-full"
                :feedback="false"
                toggle-mask
                :input-style="{ width: '100%' }"
                autocomplete="new-password"
                :disabled="loading"
              />
            </div>

            <Button
              type="submit"
              label="Reset password"
              icon="pi pi-lock-open"
              class="w-full"
              :loading="loading"
            />
          </form>

          <p class="card-footer">
            <RouterLink to="/forgot-password" class="card-link">← Request a new reset link</RouterLink>
          </p>
        </template>
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

/* ── State block (success) ───────────────────── */
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

.success-wrap { background: rgba(34, 197, 94, 0.12); }

.state-icon   { font-size: 2rem; }
.success-icon { color: #16a34a; }

.mt-btn { margin-top: 0.5rem; }

/* ── Card header / form ──────────────────────── */
.card-header { margin-bottom: 1.75rem; }

.card-title {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--text-primary);
  margin: 0 0 0.375rem;
}

.card-subtitle {
  font-size: 0.9375rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
}

/* ── Error banner ────────────────────────────── */
.error-msg {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #ef4444;
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}

/* ── Form ────────────────────────────────────── */
.login-form { display: flex; flex-direction: column; gap: 1.125rem; }

.field { display: flex; flex-direction: column; gap: 0.375rem; }

.field-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

/* ── Card footer ─────────────────────────────── */
.card-footer {
  text-align: center;
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 1.5rem 0 0;
}

.card-link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}
.card-link:hover { text-decoration: underline; }
</style>
