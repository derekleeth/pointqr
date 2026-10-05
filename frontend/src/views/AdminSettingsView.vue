<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi, type SiteSettings } from '@/api/admin'
import { useToast } from 'primevue/usetoast'

const toast = useToast()
const settings = ref<SiteSettings | null>(null)
const loading = ref(true)
const saving = ref(false)

async function loadSettings() {
  loading.value = true
  try {
    settings.value = await adminApi.getSettings()
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load settings', life: 3000 })
  } finally {
    loading.value = false
  }
}

async function toggleRegistration() {
  if (!settings.value) return
  saving.value = true
  const newVal = !settings.value.registration_enabled
  try {
    const updated = await adminApi.updateSettings({ registration_enabled: newVal })
    settings.value = updated
    toast.add({
      severity: newVal ? 'success' : 'warn',
      summary: newVal ? 'Registration enabled' : 'Registration disabled',
      detail: newVal
        ? 'New users can now register accounts.'
        : 'Public registration is now closed. Use User Management to create accounts.',
      life: 4000,
    })
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err?.response?.data?.detail ?? 'Failed to save setting',
      life: 3500,
    })
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<template>
  <div class="admin-settings-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">Site Settings</h1>
        <p class="page-subtitle">Platform-wide configuration — changes take effect immediately</p>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <ProgressSpinner style="width: 36px; height: 36px" />
    </div>

    <div v-else-if="settings" class="settings-grid">

      <!-- Registration Card -->
      <div class="settings-card">
        <div class="card-header">
          <i class="pi pi-user-plus card-icon" />
          <div class="card-header-text">
            <h2 class="card-title">Public Registration</h2>
            <p class="card-desc">Controls whether visitors can self-register new accounts.</p>
          </div>
          <Tag
            :value="settings.registration_enabled ? 'Enabled' : 'Disabled'"
            :severity="settings.registration_enabled ? 'success' : 'danger'"
            class="status-tag"
          />
        </div>

        <div class="card-body">
          <!-- Live toggle row -->
          <div class="toggle-row">
            <div class="toggle-info">
              <p class="toggle-label">Allow public sign-ups</p>
              <p class="toggle-desc">
                {{ settings.registration_enabled
                  ? 'Anyone can create an account via the registration page.'
                  : 'Registration is closed. Only admins can create accounts.' }}
              </p>
            </div>
            <div class="toggle-action">
              <ToggleSwitch
                :model-value="settings.registration_enabled"
                :disabled="saving"
                @update:model-value="toggleRegistration"
              />
            </div>
          </div>

          <!-- Status detail -->
          <div
            class="status-detail"
            :class="settings.registration_enabled ? 'detail-enabled' : 'detail-disabled'"
          >
            <i :class="settings.registration_enabled ? 'pi pi-check-circle' : 'pi pi-lock'" />
            <span>
              {{ settings.registration_enabled
                ? 'Registration is open to the public'
                : 'Registration is closed — admin invite only' }}
            </span>
          </div>

          <Message v-if="!settings.registration_enabled" severity="warn" :closable="false">
            <template #default>
              <span>
                When disabled, use the
                <RouterLink to="/admin/users" class="inline-link">User Management</RouterLink>
                page to create new accounts manually.
              </span>
            </template>
          </Message>

          <Message severity="info" :closable="false">
            <template #default>
              <span>
                This value is stored in the database and overrides <code>REGISTRATION_ENABLED</code>
                in <code>.env</code>. It takes effect immediately — no restart required.
              </span>
            </template>
          </Message>
        </div>
      </div>

      <!-- Admin Account Card -->
      <div class="settings-card">
        <div class="card-header">
          <i class="pi pi-shield card-icon" />
          <div class="card-header-text">
            <h2 class="card-title">Bootstrap Admin Account</h2>
            <p class="card-desc">
              Seeded from environment variables on first startup. Use
              <RouterLink to="/admin/users" class="inline-link">User Management</RouterLink>
              to promote other users to admin.
            </p>
          </div>
        </div>

        <div class="card-body">
          <div class="kv-grid">
            <div class="kv-item">
              <span class="kv-label">ADMIN_EMAIL</span>
              <span class="kv-value">Set in <code>.env</code></span>
            </div>
            <div class="kv-item">
              <span class="kv-label">ADMIN_PASSWORD</span>
              <span class="kv-value">Set in <code>.env</code> (bcrypt-hashed on first run)</span>
            </div>
          </div>

          <Message severity="warn" :closable="false">
            <template #default>
              Change <code>ADMIN_PASSWORD</code> in <code>.env</code> before going to production.
              The password is hashed and stored only once (when the row is first created).
            </template>
          </Message>
        </div>
      </div>

      <!-- Environment Card -->
      <div class="settings-card">
        <div class="card-header">
          <i class="pi pi-info-circle card-icon" />
          <div class="card-header-text">
            <h2 class="card-title">Environment</h2>
            <p class="card-desc">Runtime information about this deployment.</p>
          </div>
        </div>

        <div class="card-body">
          <div class="kv-grid">
            <div class="kv-item">
              <span class="kv-label">Runtime settings source</span>
              <span class="kv-value">Database (overrides <code>.env</code>)</span>
            </div>
            <div class="kv-item">
              <span class="kv-label">API docs</span>
              <span class="kv-value">
                <a href="/api/docs" target="_blank" class="inline-link">Swagger UI ↗</a>
              </span>
            </div>
          </div>
        </div>
      </div>

    </div>

    <Toast />
  </div>
</template>

<style scoped>
.admin-settings-view {
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  gap: 1.25rem;
  overflow-y: auto;
  height: 100%;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.page-title {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 4rem;
}

.settings-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 760px;
}

.settings-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg-card);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 0.875rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
}

.card-icon {
  font-size: 1.125rem;
  color: var(--color-primary);
  margin-top: 2px;
  flex-shrink: 0;
}

.card-header-text {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.card-desc {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin: 0.2rem 0 0;
}

.status-tag {
  flex-shrink: 0;
}

.card-body {
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Toggle row */
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 0.75rem 1rem;
  background: var(--bg-elevated);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.toggle-info {
  flex: 1;
  min-width: 0;
}

.toggle-label {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.toggle-desc {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0;
}

.toggle-action {
  flex-shrink: 0;
}

/* Status badge */
.status-detail {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.875rem;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
}

.detail-enabled {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}

.detail-disabled {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

/* KV table */
.kv-grid {
  display: flex;
  flex-direction: column;
}

.kv-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.875rem;
}

.kv-item:last-child {
  border-bottom: none;
}

.kv-label {
  font-weight: 500;
  color: var(--text-secondary);
  font-family: monospace;
}

.kv-value {
  color: var(--text-primary);
}

code {
  background: var(--bg-elevated);
  padding: 0.1em 0.35em;
  border-radius: 4px;
  font-size: 0.85em;
  font-family: monospace;
}

.inline-link {
  color: var(--color-primary);
  text-decoration: none;
}

.inline-link:hover {
  text-decoration: underline;
}
</style>
