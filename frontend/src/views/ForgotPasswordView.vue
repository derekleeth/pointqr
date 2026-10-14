<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { apiClient } from '@/api/client'

const theme = useThemeStore()

const email = ref('')
const loading = ref(false)
const submitted = ref(false)
const error = ref('')

async function handleSubmit() {
  if (!email.value) {
    error.value = 'Please enter your email address.'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await apiClient.post('/auth/forgot-password', { email: email.value })
    submitted.value = true
  } catch {
    // Show the generic success message even on error to avoid user enumeration
    submitted.value = true
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
        <div v-if="submitted" class="state-block">
          <div class="state-icon-wrap success-wrap">
            <i class="pi pi-envelope state-icon success-icon" />
          </div>
          <h1 class="card-title">Check your inbox</h1>
          <p class="card-subtitle">
            If that email exists in our system, a password reset link has been sent.
            Please check your inbox (and spam folder).
          </p>
          <RouterLink to="/login" class="card-link back-link">← Back to sign in</RouterLink>
        </div>

        <!-- Form state -->
        <template v-else>
          <div class="card-header">
            <h1 class="card-title">Forgot your password?</h1>
            <p class="card-subtitle">Enter your email and we'll send you a reset link.</p>
          </div>

          <!-- Error -->
          <div class="error-msg" v-if="error">
            <i class="pi pi-exclamation-circle" />
            {{ error }}
          </div>

          <form @submit.prevent="handleSubmit" class="login-form" novalidate>
            <div class="field">
              <label for="email" class="field-label">Email address</label>
              <InputText
                id="email"
                v-model="email"
                type="email"
                placeholder="you@example.com"
                class="w-full"
                autocomplete="email"
                :disabled="loading"
              />
            </div>

            <Button
              type="submit"
              label="Send reset link"
              icon="pi pi-send"
              class="w-full"
              :loading="loading"
            />
          </form>

          <p class="card-footer">
            Remember your password?
            <RouterLink to="/login" class="card-link">Sign in →</RouterLink>
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

.state-icon  { font-size: 2rem; }
.success-icon { color: #16a34a; }

.back-link {
  margin-top: 0.5rem;
  font-size: 0.875rem;
}

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
