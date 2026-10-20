<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listQRCodes, deleteQRCode, type QRCodeRead } from '@/api/qrcodes'
import DownloadModal from '@/components/dashboard/DownloadModal.vue'

const router = useRouter()
const auth = useAuthStore()

const qrCodes = ref<QRCodeRead[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const perPage = 20

const selectedQRCode = ref<QRCodeRead | null>(null)
const downloadModalVisible = ref(false)
const betaDismissed = ref(false)

onMounted(async () => {
  if (!auth.user) await auth.initialize()
  await fetchQRCodes()
})

async function fetchQRCodes() {
  loading.value = true
  try {
    const { data } = await listQRCodes(page.value, perPage)
    qrCodes.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function handleDelete(qr: QRCodeRead) {
  if (!confirm(`Delete "${qr.title}"? This cannot be undone.`)) return
  await deleteQRCode(qr.id)
  await fetchQRCodes()
}

function handleEdit(qr: QRCodeRead) {
  router.push(`/editor/${qr.id}`)
}

function handleDownload(qr: QRCodeRead) {
  selectedQRCode.value = qr
  downloadModalVisible.value = true
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
</script>

<template>
  <div class="flex flex-col gap-8">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-3xl font-bold text-surface-900 dark:text-surface-0">Dashboard</h1>
        <p class="text-surface-500 mt-1">
          Welcome back,
          <span class="font-medium text-surface-700 dark:text-surface-200">{{
            auth.user?.email
          }}</span>!
        </p>
      </div>
      <Button
        label="New QR Code"
        icon="pi pi-plus"
        @click="router.push('/editor')"
      />
    </div>

    <!-- Beta Disclaimer Banner -->
    <div
      v-if="!betaDismissed"
      class="flex items-start justify-between gap-4 p-4 rounded-xl border transition-all duration-200"
      style="background-color: rgba(245, 158, 11, 0.06); border-color: rgba(245, 158, 11, 0.28);"
      role="region"
      aria-label="Beta Disclaimer"
    >
      <div class="flex items-start gap-3.5">
        <span
          class="flex items-center justify-center w-9 h-9 rounded-lg flex-shrink-0 mt-0.5"
          style="background-color: rgba(245, 158, 11, 0.15); color: #d97706;"
        >
          <i class="pi pi-info-circle text-lg dark:text-amber-400" />
        </span>
        <div class="flex flex-col gap-1">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-semibold text-surface-900 dark:text-surface-0 text-sm sm:text-base">
              Cloud Hosted Beta
            </span>
            <Tag value="BETA" severity="warn" class="text-xs font-bold tracking-wide" />
          </div>
          <p class="text-sm text-surface-600 dark:text-surface-300 leading-relaxed">
            Please note that the cloud-hosted application is currently in beta. Features, APIs, and background processing are actively being developed and enhanced. You may encounter occasional updates and changes — you can submit feedback and suggestions anytime on the
            <RouterLink
              to="/feedback"
              class="font-medium text-amber-700 dark:text-amber-400 underline underline-offset-2 hover:text-amber-800 dark:hover:text-amber-300 transition-colors"
            >feedback page</RouterLink>.
          </p>
        </div>
      </div>
      <Button
        icon="pi pi-times"
        severity="secondary"
        text
        rounded
        size="small"
        aria-label="Dismiss disclaimer"
        title="Dismiss disclaimer"
        class="flex-shrink-0 text-surface-500 hover:text-surface-700 dark:hover:text-surface-200"
        @click="betaDismissed = true"
      />
    </div>

    <!-- Stats row -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="stat in [
          { label: 'Total QR Codes', value: total, icon: 'pi-qrcode' },
          { label: 'Total Scans', value: qrCodes.reduce((s, q) => s + q.scan_count, 0), icon: 'pi-chart-bar' },
          { label: 'Active Dynamic', value: qrCodes.filter((q) => q.type === 'DYNAMIC').length, icon: 'pi-link' },
          { label: 'Static Codes', value: qrCodes.filter((q) => q.type === 'STATIC').length, icon: 'pi-lock' },
        ]"
        :key="stat.label"
        class="p-5 rounded-xl border transition-colors duration-200"
        style="background-color: var(--bg-card); border-color: var(--border);"
      >
        <div class="flex items-start justify-between">
          <div>
            <p class="text-sm" style="color: var(--text-secondary)">{{ stat.label }}</p>
            <p class="text-3xl font-bold mt-1 text-surface-900 dark:text-surface-0">{{ stat.value }}</p>
          </div>
          <span
            class="flex items-center justify-center w-9 h-9 rounded-lg text-primary-500 dark:text-primary-400"
            style="background-color: var(--color-primary-soft)"
          >
            <i :class="`pi ${stat.icon} text-base`" />
          </span>
        </div>
      </div>
    </div>

    <!-- QR code DataTable -->
    <div
      class="rounded-xl overflow-hidden border transition-colors duration-200"
      style="background-color: var(--bg-card); border-color: var(--border);"
    >
      <DataTable
        :value="qrCodes"
        :loading="loading"
        striped-rows
        row-hover
        responsive-layout="scroll"
        :pt="{
          root: { style: 'background: transparent' },
          thead: { style: 'background: transparent' },
          headerRow: { style: `background-color: var(--bg-elevated); border-bottom: 1px solid var(--border);` },
          headerCell: { style: 'background: transparent; color: var(--text-secondary); font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; border: none; padding: 0.75rem 1rem;' },
          bodyRow: { style: 'background: transparent; border-bottom: 1px solid var(--border);' },
          rowGroupFooter: { style: 'background: transparent' },
          emptyMessage: { style: 'background: transparent' },
        }"
      >
        <template #empty>
          <div class="flex flex-col items-center gap-4 py-16 text-center">
            <span class="text-5xl">✨</span>
            <h2 class="text-xl font-semibold text-surface-900 dark:text-surface-0">
              No QR codes yet
            </h2>
            <p class="text-surface-500 max-w-sm">
              Create your first QR code to get started.
            </p>
            <Button label="Create Your First QR Code" icon="pi pi-plus" @click="router.push('/editor')" />
          </div>
        </template>

        <Column field="title" header="Name" sortable>
          <template #body="{ data }">
            <span class="font-medium text-surface-900 dark:text-surface-0">{{ data.title }}</span>
          </template>
        </Column>

        <Column field="type" header="Type" style="width: 100px">
          <template #body="{ data }">
            <Tag
              :value="data.type"
              :severity="data.type === 'DYNAMIC' ? 'info' : 'secondary'"
            />
          </template>
        </Column>

        <Column field="scan_count" header="Scans" sortable style="width: 90px">
          <template #body="{ data }">
            <span class="font-mono">{{ data.scan_count.toLocaleString() }}</span>
          </template>
        </Column>

        <Column field="created_at" header="Created" sortable style="width: 130px">
          <template #body="{ data }">
            <span class="text-sm" style="color: var(--text-secondary)">{{ formatDate(data.created_at) }}</span>
          </template>
        </Column>

        <Column header="Actions" style="width: 140px">
          <template #body="{ data }">
            <div class="flex gap-1">
              <Button
                icon="pi pi-download"
                severity="secondary"
                text
                rounded
                size="small"
                aria-label="Download"
                title="Download"
                @click="handleDownload(data)"
              />
              <Button
                icon="pi pi-pencil"
                severity="secondary"
                text
                rounded
                size="small"
                aria-label="Edit"
                title="Edit"
                @click="handleEdit(data)"
              />
              <Button
                icon="pi pi-trash"
                severity="danger"
                text
                rounded
                size="small"
                aria-label="Delete"
                title="Delete"
                @click="handleDelete(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Download Barcode Modal -->
    <DownloadModal
      v-model:visible="downloadModalVisible"
      :qr-code="selectedQRCode"
    />
  </div>
</template>

