<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { listQRCodes, deleteQRCode, type QRCodeRead, type QRContentType } from '@/api/qrcodes'
import DownloadModal from '@/components/dashboard/DownloadModal.vue'

const router = useRouter()
const auth = useAuthStore()
const ui = useUIStore()

// Phones get a card list instead of the table (same breakpoint as the app shell's drawer)
const useCards = computed(() => ui.shellMode === 'mobile')

const qrCodes = ref<QRCodeRead[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const perPage = 20

const selectedQRCode = ref<QRCodeRead | null>(null)
const downloadModalVisible = ref(false)
const betaDismissed = ref(false)

const CONTENT_TYPES: Record<QRContentType, { label: string; icon: string }> = {
  URL: { label: 'URL', icon: 'pi-link' },
  TEXT: { label: 'Text', icon: 'pi-align-left' },
  VCARD: { label: 'Contact', icon: 'pi-id-card' },
}
const contentFilterOptions = [
  { label: 'All', value: 'ALL' },
  ...Object.entries(CONTENT_TYPES).map(([value, { label }]) => ({ label, value })),
]
const contentFilter = ref<QRContentType | 'ALL'>('ALL')
const filteredQRCodes = computed(() =>
  contentFilter.value === 'ALL'
    ? qrCodes.value
    : qrCodes.value.filter((q) => q.content_type === contentFilter.value),
)

// Cards can't use the table's sortable headers, so phones get a sort menu instead
type CardSort = 'newest' | 'oldest' | 'name' | 'scans'
const cardSortOptions: { label: string; value: CardSort }[] = [
  { label: 'Newest', value: 'newest' },
  { label: 'Oldest', value: 'oldest' },
  { label: 'Name', value: 'name' },
  { label: 'Most scans', value: 'scans' },
]
const cardSort = ref<CardSort>('newest')
const sortedCards = computed(() => {
  const list = [...filteredQRCodes.value]
  switch (cardSort.value) {
    case 'newest': return list.sort((a, b) => b.created_at.localeCompare(a.created_at))
    case 'oldest': return list.sort((a, b) => a.created_at.localeCompare(b.created_at))
    case 'name': return list.sort((a, b) => a.title.localeCompare(b.title))
    case 'scans': return list.sort((a, b) => b.scan_count - a.scan_count)
  }
  return list
})

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

    <!-- Content type filter (+ sort on phones) -->
    <div v-if="qrCodes.length" class="flex items-center justify-between gap-3 flex-wrap -mb-4">
      <SelectButton
        v-model="contentFilter"
        :options="contentFilterOptions"
        option-label="label"
        option-value="value"
        :allow-empty="false"
        aria-label="Filter by content type"
        size="small"
      />
      <Select
        v-if="useCards"
        v-model="cardSort"
        :options="cardSortOptions"
        option-label="label"
        option-value="value"
        size="small"
        aria-label="Sort QR codes"
        class="card-sort"
      >
        <template #value="{ value }">
          <span class="inline-flex items-center gap-2">
            <i class="pi pi-sort-alt text-xs" style="color: var(--text-secondary)" />
            {{ cardSortOptions.find((o) => o.value === value)?.label }}
          </span>
        </template>
      </Select>
    </div>

    <!-- Phone: card list -->
    <template v-if="useCards">
      <div v-if="loading && !qrCodes.length" class="flex flex-col gap-3" aria-busy="true">
        <div v-for="n in 3" :key="n" class="qr-card">
          <div class="flex items-center gap-3 p-3.5">
            <Skeleton shape="circle" size="2.5rem" />
            <div class="flex-1 flex flex-col gap-2">
              <Skeleton width="60%" height="1rem" />
              <Skeleton width="40%" height="0.75rem" />
            </div>
          </div>
        </div>
      </div>

      <div
        v-else-if="!qrCodes.length"
        class="flex flex-col items-center gap-4 py-12 px-4 text-center rounded-xl border"
        style="background-color: var(--bg-card); border-color: var(--border);"
      >
        <span class="text-5xl">✨</span>
        <h2 class="text-xl font-semibold text-surface-900 dark:text-surface-0">No QR codes yet</h2>
        <p class="text-surface-500 max-w-sm">Create your first QR code to get started.</p>
        <Button label="Create Your First QR Code" icon="pi pi-plus" @click="router.push('/editor')" />
      </div>

      <div
        v-else-if="!sortedCards.length"
        class="py-12 text-center text-surface-500 rounded-xl border"
        style="background-color: var(--bg-card); border-color: var(--border);"
      >
        No {{ CONTENT_TYPES[contentFilter as QRContentType]?.label }} QR codes yet.
      </div>

      <ul v-else class="flex flex-col gap-3 list-none m-0 p-0" aria-label="Your QR codes">
        <li v-for="qr in sortedCards" :key="qr.id" class="qr-card">
          <button
            type="button"
            class="qr-card-main"
            :aria-label="`Download ${qr.title}`"
            @click="handleDownload(qr)"
          >
            <span class="qr-card-icon" aria-hidden="true">
              <i :class="`pi ${CONTENT_TYPES[qr.content_type].icon}`" />
            </span>
            <span class="flex-1 min-w-0 flex flex-col gap-0.5">
              <span class="qr-card-title">{{ qr.title }}</span>
              <span class="qr-card-meta">
                {{ CONTENT_TYPES[qr.content_type].label }} · {{ formatDate(qr.created_at) }}
              </span>
            </span>
            <Tag
              :value="qr.type"
              :severity="qr.type === 'DYNAMIC' ? 'info' : 'secondary'"
              class="flex-shrink-0"
            />
          </button>
          <div class="qr-card-foot">
            <span class="qr-card-scans">
              <i class="pi pi-chart-bar text-xs" aria-hidden="true" />
              <span class="font-mono">{{ qr.scan_count.toLocaleString() }}</span>
              {{ qr.scan_count === 1 ? 'scan' : 'scans' }}
            </span>
            <div class="flex">
              <Button
                icon="pi pi-download"
                severity="secondary"
                text
                rounded
                class="qr-card-action"
                :aria-label="`Download ${qr.title}`"
                @click="handleDownload(qr)"
              />
              <Button
                icon="pi pi-pencil"
                severity="secondary"
                text
                rounded
                class="qr-card-action"
                :aria-label="`Edit ${qr.title}`"
                @click="handleEdit(qr)"
              />
              <Button
                icon="pi pi-trash"
                severity="danger"
                text
                rounded
                class="qr-card-action"
                :aria-label="`Delete ${qr.title}`"
                @click="handleDelete(qr)"
              />
            </div>
          </div>
        </li>
      </ul>
    </template>

    <!-- Tablet and up: table -->
    <div
      v-else
      class="rounded-xl overflow-hidden border transition-colors duration-200"
      style="background-color: var(--bg-card); border-color: var(--border);"
    >
      <DataTable
        :value="filteredQRCodes"
        :loading="loading"
        striped-rows
        row-hover
        responsive-layout="scroll"
        scrollable
        v-scroll-cue
        @row-click="handleDownload($event.data)"
        :pt="{
          root: { style: 'background: transparent' },
          thead: { style: 'background: transparent' },
          headerRow: { style: `background-color: var(--bg-elevated); border-bottom: 1px solid var(--border);` },
          headerCell: { style: 'background: transparent; color: var(--text-secondary); font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; border: none; padding: 0.75rem 1rem;' },
          bodyRow: { style: 'background: transparent; border-bottom: 1px solid var(--border); cursor: pointer;' },
          rowGroupFooter: { style: 'background: transparent' },
          emptyMessage: { style: 'background: transparent' },
        }"
      >
        <template #empty>
          <div v-if="qrCodes.length" class="py-16 text-center text-surface-500">
            No {{ CONTENT_TYPES[contentFilter as QRContentType]?.label }} QR codes yet.
          </div>
          <div v-else class="flex flex-col items-center gap-4 py-16 text-center">
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

        <Column field="content_type" header="Content" style="width: 120px">
          <template #body="{ data }">
            <span class="inline-flex items-center gap-1.5 text-sm" style="color: var(--text-secondary)">
              <i :class="`pi ${CONTENT_TYPES[data.content_type as QRContentType].icon} text-xs`" />
              {{ CONTENT_TYPES[data.content_type as QRContentType].label }}
            </span>
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

        <Column header="Actions" frozen align-frozen="right" style="width: 140px">
          <template #body="{ data }">
            <div class="flex gap-1" @click.stop>
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

<style scoped>
.card-sort { min-width: 9rem; }

.qr-card {
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  background-color: var(--bg-card);
  overflow: hidden;
}

/* The top of the card opens the download modal, like a table row does */
.qr-card-main {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  min-height: 64px;
  padding: 0.875rem 0.875rem 0.5rem;
  border: none;
  background: none;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.qr-card-main:active { background-color: var(--bg-hover); }
.qr-card-main:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
  border-radius: 0.75rem 0.75rem 0 0;
}

.qr-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  flex-shrink: 0;
  border-radius: 0.625rem;
  background-color: var(--color-primary-soft);
  color: var(--color-primary);
}

.qr-card-title {
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.qr-card-meta {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.qr-card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0 0.375rem 0.25rem 0.875rem;
}

.qr-card-scans {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.qr-card-action {
  width: 44px !important;
  height: 44px !important;
}
</style>
