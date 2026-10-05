<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi, type SiteSettings } from '@/api/admin'
import { useToast } from 'primevue/usetoast'

const toast = useToast()
const settings = ref<SiteSettings | null>(null)
const loading = ref(true)

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

onMounted(loadSettings)
</script>

<template>
  <div class="admin-settings-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">Site Settings</h1>
        <p class="page-subtitle">Platform-wide configuration managed via environment variables</p>
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
          <div>
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
          <div class="setting-row">
            <div>
              <p class="setting-label">REGISTRATION_ENABLED</p>
              <p class="setting-value">{{ settings.registration_enabled ? 'true' : 'false' }}</p>
            </div>
            <div class="current-badge" :class="settings.registration_enabled ? 'badge-enabled' : 'badge-disabled'">
              <i :class="settings.registration_enabled ? 'pi pi-check-circle' : 'pi pi-ban'" />
              {{ settings.registration_enabled ? 'Open to public' : 'Closed – admin invite only' }}
            </div>
          </div>

          <Message severity="info" :closable="false" class="info-message">
            <template #default>
              <div class="message-body">
                <strong>To change this setting:</strong>
                <ol>
                  <li>Open <code>.env</code> at the project root.</li>
                  <li>Set <code>REGISTRATION_ENABLED=false</code> (or <code>true</code>).</li>
                  <li>Restart the backend container: <code>docker compose restart backend</code></li>
                </ol>
                <p>
                  When disabled, use the
                  <RouterLink to="/admin/users" class="inline-link">User Management</RouterLink>
                  page to create accounts manually.
                </p>
              </div>
            </template>
          </Message>
        </div>
      </div>

      <!-- Admin Account Card -->
      <div class="settings-card">
        <div class="card-header">
          <i class="pi pi-shield card-icon" />
          <div>
            <h2 class="card-title">Bootstrap Admin Account</h2>
            <p class="card-desc">The admin user seeded from environment variables on first startup.</p>
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

          <Message severity="warn" :closable="false" class="info-message">
            <template #default>
              <div class="message-body">
                <strong>Security reminder:</strong> change <code>ADMIN_PASSWORD</code> in
                <code>.env</code> before going to production. The password is hashed and stored
                only once — when the admin row is first created. Changing it in <code>.env</code>
                after that has no effect unless you delete the admin row from the database.
              </div>
            </template>
          </Message>
        </div>
      </div>

      <!-- Environment Info Card -->
      <div class="settings-card">
        <div class="card-header">
          <i class="pi pi-info-circle card-icon" />
          <div>
            <h2 class="card-title">Environment</h2>
            <p class="card-desc">Runtime information about this deployment.</p>
          </div>
        </div>

        <div class="card-body">
          <div class="kv-grid">
            <div class="kv-item">
              <span class="kv-label">Config source</span>
              <span class="kv-value"><code>.env</code> file (Pydantic Settings)</span>
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
  margin-left: auto;
  flex-shrink: 0;
}

.card-body {
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.setting-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin: 0;
  font-family: monospace;
}

.setting-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0.2rem 0 0;
  font-family: monospace;
}

.current-badge {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
}

.badge-enabled {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}

.badge-disabled {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.info-message {
  font-size: 0.875rem;
}

.message-body ol {
  margin: 0.5rem 0 0.75rem 1.25rem;
  padding: 0;
}

.message-body li {
  margin-bottom: 0.25rem;
}

.message-body p {
  margin: 0;
}

code {
  background: var(--bg-elevated);
  padding: 0.1em 0.35em;
  border-radius: 4px;
  font-size: 0.85em;
  font-family: monospace;
}

.kv-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
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

.inline-link {
  color: var(--color-primary);
  text-decoration: none;
}

.inline-link:hover {
  text-decoration: underline;
}
</style>
