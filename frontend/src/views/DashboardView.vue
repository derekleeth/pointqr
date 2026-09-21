<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listQRCodes, deleteQRCode, type QRCodeRead } from '@/api/qrcodes'

const router = useRouter()
const auth = useAuthStore()

const qrCodes = ref<QRCodeRead[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const perPage = 20

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

    <!-- Stats row -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="stat in [
          { label: 'Total QR Codes', value: total },
          { label: 'Total Scans', value: qrCodes.reduce((s, q) => s + q.scan_count, 0) },
          { label: 'Active Dynamic', value: qrCodes.filter((q) => q.type === 'DYNAMIC').length },
          { label: 'Static Codes', value: qrCodes.filter((q) => q.type === 'STATIC').length },
        ]"
        :key="stat.label"
        class="p-5 rounded-xl border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800"
      >
        <p class="text-surface-500 text-sm">{{ stat.label }}</p>
        <p class="text-3xl font-bold text-surface-900 dark:text-surface-0 mt-1">{{ stat.value }}</p>
      </div>
    </div>

    <!-- QR code DataTable -->
    <div
      class="rounded-xl border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800 overflow-hidden"
    >
      <DataTable
        :value="qrCodes"
        :loading="loading"
        striped-rows
        row-hover
        responsive-layout="scroll"
        :pt="{ root: { class: 'w-full' } }"
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
            <span class="text-surface-500 text-sm">{{ formatDate(data.created_at) }}</span>
          </template>
        </Column>

        <Column header="Actions" style="width: 120px">
          <template #body="{ data }">
            <div class="flex gap-1">
              <Button
                icon="pi pi-pencil"
                severity="secondary"
                text
                rounded
                size="small"
                aria-label="Edit"
                @click="handleEdit(data)"
              />
              <Button
                icon="pi pi-trash"
                severity="danger"
                text
                rounded
                size="small"
                aria-label="Delete"
                @click="handleDelete(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
