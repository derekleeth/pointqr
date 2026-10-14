<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  getAPIKeyInfo,
  generateAPIKey,
  revokeAPIKey,
  type APIKeyInfo,
  type APIKeyCreated,
} from '@/api/apikeys'

const auth = useAuthStore()

const loading = ref(false)
const keyInfo = ref<APIKeyInfo | null>(null)
const newKey = ref<APIKeyCreated | null>(null)
const copied = ref(false)
const showRevokeConfirm = ref(false)
const showRegenerateConfirm = ref(false)

const apiBaseUrl = `${window.location.origin}/api`

onMounted(async () => {
  if (!auth.user) await auth.initialize()
  await fetchKeyInfo()
})

async function fetchKeyInfo() {
  loading.value = true
  try {
    const { data } = await getAPIKeyInfo()
    keyInfo.value = data
  } finally {
    loading.value = false
  }
}

async function handleGenerate() {
  loading.value = true
  try {
    const { data } = await generateAPIKey()
    newKey.value = data
    keyInfo.value = { has_key: true, key_hint: data.key_hint, created_at: data.created_at }
  } finally {
    loading.value = false
    showRegenerateConfirm.value = false
  }
}

async function handleRevoke() {
  loading.value = true
  try {
    await revokeAPIKey()
    keyInfo.value = { has_key: false, key_hint: null, created_at: null }
    newKey.value = null
  } finally {
    loading.value = false
    showRevokeConfirm.value = false
  }
}

function copyKey() {
  if (!newKey.value) return
  const text = newKey.value.api_key
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      copied.value = true
      setTimeout(() => (copied.value = false), 2000)
    })
  } else {
    // Fallback for non-secure contexts (HTTP)
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="flex flex-col gap-8 max-w-3xl">
    <!-- Header -->
    <div>
      <h1 class="text-3xl font-bold text-surface-900 dark:text-surface-0">API Key</h1>
      <p class="text-surface-500 mt-1">
        Manage your personal API key for programmatic access to your QR codes.
      </p>
    </div>

    <!-- API Key Status Card -->
    <div
      class="rounded-xl border p-6 transition-colors duration-200"
      style="background-color: var(--bg-card); border-color: var(--border)"
    >
      <div class="flex items-start justify-between flex-wrap gap-4">
        <div class="flex items-center gap-3">
          <span
            class="flex items-center justify-center w-10 h-10 rounded-lg"
            style="background-color: var(--color-primary-soft)"
          >
            <i class="pi pi-key text-lg text-primary-500 dark:text-primary-400" />
          </span>
          <div>
            <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">
              Personal API Key
            </h2>
            <p class="text-sm" style="color: var(--text-secondary)">
              <template v-if="keyInfo?.has_key">
                Active since {{ formatDate(keyInfo.created_at!) }}
              </template>
              <template v-else>
                No API key configured
              </template>
            </p>
          </div>
        </div>
        <div class="flex gap-2">
          <template v-if="keyInfo?.has_key">
            <Button
              label="Regenerate"
              icon="pi pi-refresh"
              severity="warn"
              outlined
              size="small"
              :loading="loading"
              @click="showRegenerateConfirm = true"
            />
            <Button
              label="Revoke"
              icon="pi pi-trash"
              severity="danger"
              outlined
              size="small"
              :loading="loading"
              @click="showRevokeConfirm = true"
            />
          </template>
          <Button
            v-else
            label="Generate API Key"
            icon="pi pi-plus"
            :loading="loading"
            @click="handleGenerate"
          />
        </div>
      </div>

      <!-- Newly generated key display -->
      <div
        v-if="newKey"
        class="mt-6 rounded-lg border p-4"
        style="background-color: var(--bg-elevated); border-color: var(--border)"
      >
        <div class="flex items-center gap-2 mb-3">
          <i class="pi pi-exclamation-triangle text-orange-500" />
          <span class="text-sm font-semibold text-orange-600 dark:text-orange-400">
            Copy your API key now — it will not be shown again!
          </span>
        </div>
        <div class="flex items-center gap-2">
          <InputText
            :model-value="newKey.api_key"
            readonly
            class="flex-1 font-mono text-sm"
          />
          <Button
            :icon="copied ? 'pi pi-check' : 'pi pi-copy'"
            :severity="copied ? 'success' : 'secondary'"
            outlined
            :label="copied ? 'Copied!' : 'Copy'"
            @click="copyKey"
          />
        </div>
      </div>
    </div>

    <!-- Usage Guide Card -->
    <div
      class="rounded-xl border p-6 transition-colors duration-200"
      style="background-color: var(--bg-card); border-color: var(--border)"
    >
      <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0 mb-4">
        <i class="pi pi-book mr-2" />Using Your API Key
      </h2>

      <p class="text-sm mb-4" style="color: var(--text-secondary)">
        Include your API key in the
        <code
          class="px-1.5 py-0.5 rounded text-xs font-mono"
          style="background-color: var(--bg-elevated)"
          >X-API-Key</code
        >
        header with every request. The API key provides the same access level as your logged-in
        account.
      </p>

      <div class="space-y-4">
        <!-- Example: List QR codes -->
        <div>
          <p
            class="text-xs font-semibold uppercase tracking-wider mb-2"
            style="color: var(--text-secondary)"
          >
            List your QR codes
          </p>
          <pre
            class="rounded-lg p-4 text-sm font-mono overflow-x-auto"
            style="background-color: var(--bg-elevated); color: var(--text-primary)"
          ><code>curl -H "X-API-Key: pqr_your_key_here" \
  {{ apiBaseUrl }}/v1/qrcodes</code></pre>
        </div>

        <!-- Example: Create QR code -->
        <div>
          <p
            class="text-xs font-semibold uppercase tracking-wider mb-2"
            style="color: var(--text-secondary)"
          >
            Create a QR code
          </p>
          <pre
            class="rounded-lg p-4 text-sm font-mono overflow-x-auto"
            style="background-color: var(--bg-elevated); color: var(--text-primary)"
          ><code>curl -X POST -H "X-API-Key: pqr_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"title": "My QR", "type": "STATIC", "target_url": "https://example.com", "design_config": {"content": "https://example.com"}}' \
  {{ apiBaseUrl }}/v1/qrcodes</code></pre>
        </div>
      </div>
    </div>

    <!-- Regenerate Confirmation Dialog -->
    <Dialog
      v-model:visible="showRegenerateConfirm"
      header="Regenerate API Key?"
      :modal="true"
      :style="{ width: '28rem' }"
    >
      <p class="text-sm" style="color: var(--text-secondary)">
        This will invalidate your existing API key immediately. Any integrations using the current
        key will stop working.
      </p>
      <template #footer>
        <Button
          label="Cancel"
          severity="secondary"
          text
          @click="showRegenerateConfirm = false"
        />
        <Button
          label="Regenerate"
          icon="pi pi-refresh"
          severity="warn"
          :loading="loading"
          @click="handleGenerate"
        />
      </template>
    </Dialog>

    <!-- Revoke Confirmation Dialog -->
    <Dialog
      v-model:visible="showRevokeConfirm"
      header="Revoke API Key?"
      :modal="true"
      :style="{ width: '28rem' }"
    >
      <p class="text-sm" style="color: var(--text-secondary)">
        This will permanently delete your API key. Any integrations using this key will stop working
        immediately.
      </p>
      <template #footer>
        <Button
          label="Cancel"
          severity="secondary"
          text
          @click="showRevokeConfirm = false"
        />
        <Button
          label="Revoke Key"
          icon="pi pi-trash"
          severity="danger"
          :loading="loading"
          @click="handleRevoke"
        />
      </template>
    </Dialog>
  </div>
</template>
