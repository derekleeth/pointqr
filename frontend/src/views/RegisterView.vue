<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const router = useRouter()
const auth = useAuthStore()
const theme = useThemeStore()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  error.value = ''
  if (!email.value || !password.value) {
    error.value = 'All fields are required.'
    return
  }
  if (password.value.length < 8) {
    error.value = 'Password must be at least 8 characters.'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    return
  }
  loading.value = true
  try {
    await auth.register(email.value, password.value)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Registration failed. The email may already be in use.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="page-glow" aria-hidden="true" />

    <header class="login-topbar">
      <RouterLink to="/" class="brand-link">
        <div class="brand-icon"><i class="pi pi-stop-circle" /></div>
        <span class="brand-name">PointQR</span>
      </RouterLink>
      <button class="theme-btn" @click="theme.toggle()">
        <i :class="theme.isDark ? 'pi pi-sun' : 'pi pi-moon'" />
      </button>
    </header>

    <main class="login-main">
      <div class="login-card">
        <div class="card-header">
          <h1 class="card-title">Create your account</h1>
          <p class="card-subtitle">Start building better QR codes today</p>
        </div>

        <div class="error-msg" v-if="error">
          <i class="pi pi-exclamation-circle" />
          {{ error }}
        </div>

        <form @submit.prevent="handleRegister" class="login-form" novalidate>
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
            <label for="password" class="field-label">Password</label>
            <Password
              id="password"
              v-model="password"
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
            <label for="confirm" class="field-label">Confirm password</label>
            <Password
              id="confirm"
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
            label="Create account"
            icon="pi pi-user-plus"
            class="w-full"
            :loading="loading"
          />
        </form>

        <p class="card-footer">
          Already have an account?
          <RouterLink to="/login" class="card-link">Sign in →</RouterLink>
        </p>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* Shared with LoginView — identical structure */
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
.card-subtitle { font-size: 0.9375rem; color: var(--text-secondary); margin: 0; }
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
.login-form { display: flex; flex-direction: column; gap: 1.125rem; }
.field { display: flex; flex-direction: column; gap: 0.375rem; }
.field-label { font-size: 0.875rem; font-weight: 500; color: var(--text-primary); }
.card-footer { text-align: center; font-size: 0.875rem; color: var(--text-secondary); margin: 1.5rem 0 0; }
.card-link { color: var(--color-primary); text-decoration: none; font-weight: 500; }
.card-link:hover { text-decoration: underline; }
</style>
