<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useToast } from 'primevue/usetoast'

const router = useRouter()
const auth = useAuthStore()
const theme = useThemeStore()
const toast = useToast()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!email.value || !password.value) {
    error.value = 'Please enter your email and password.'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    const redirect = (router.currentRoute.value.query.redirect as string) ?? '/dashboard'
    router.push(redirect)
  } catch {
    error.value = 'Invalid email or password. Please try again.'
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
        <!-- Card header -->
        <div class="card-header">
          <h1 class="card-title">Welcome back</h1>
          <p class="card-subtitle">Sign in to your PointQR account</p>
        </div>

        <!-- Error -->
        <div class="error-msg" v-if="error">
          <i class="pi pi-exclamation-circle" />
          {{ error }}
        </div>

        <!-- Form -->
        <form @submit.prevent="handleLogin" class="login-form" novalidate>
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

          <div class="field">
            <div class="field-label-row">
              <label for="password" class="field-label">Password</label>
            </div>
            <Password
              id="password"
              v-model="password"
              placeholder="••••••••"
              class="w-full"
              :feedback="false"
              toggle-mask
              :input-style="{ width: '100%' }"
              autocomplete="current-password"
              :disabled="loading"
            />
          </div>

          <Button
            type="submit"
            label="Sign in"
            icon="pi pi-sign-in"
            class="w-full"
            :loading="loading"
          />
        </form>

        <!-- Footer -->
        <p class="card-footer">
          Don't have an account?
          <RouterLink to="/register" class="card-link">Create one →</RouterLink>
        </p>
      </div>
    </main>
  </div>
</template>

<style scoped>
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
  max-width: 400px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 2.5rem 2rem;
  box-shadow: 0 24px 64px rgba(0,0,0,0.12);
}

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

.field-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
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

