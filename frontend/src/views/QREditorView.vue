<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQREditorStore } from '@/stores/qrEditor'
import { getQRCode } from '@/api/qrcodes'
import QRCanvas from '@/components/editor/QRCanvas.vue'
import ContentPanel from '@/components/editor/ContentPanel.vue'
import DesignPanel from '@/components/editor/DesignPanel.vue'

const route = useRoute()
const router = useRouter()
const store = useQREditorStore()

onMounted(async () => {
  const qrId = route.params.id as string | undefined
  if (qrId) {
    try {
      const { data } = await getQRCode(qrId)
      store.loadFromQRCode(data)
    } catch {
      router.push('/dashboard')
    }
  } else {
    store.resetToDefaults()
  }
})

onUnmounted(() => {
  store.resetToDefaults()
})

async function handleSave() {
  try {
    const qr = await store.save()
    // Update URL to edit mode without re-mounting the component
    if (!route.params.id) {
      router.replace(`/editor/${qr.id}`)
    }
  } catch (err) {
    console.error('Save failed', err)
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <!-- ------------------------------------------------------------------ -->
    <!-- Header bar                                                          -->
    <!-- ------------------------------------------------------------------ -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div class="flex items-center gap-3 min-w-0">
        <Button
          icon="pi pi-arrow-left"
          severity="secondary"
          text
          rounded
          aria-label="Back to dashboard"
          @click="router.push('/dashboard')"
        />
        <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0 truncate">
          {{ store.isEditing ? 'Edit QR Code' : 'New QR Code' }}
        </h1>
        <Tag v-if="store.isDirty" value="Unsaved" severity="warn" />
      </div>
      <Button
        :label="store.isSaving ? 'Saving…' : 'Save'"
        icon="pi pi-save"
        :loading="store.isSaving"
        :disabled="!store.hasContent"
        @click="handleSave"
      />
    </div>

    <!-- ------------------------------------------------------------------ -->
    <!-- Two-panel editor layout                                             -->
    <!-- ------------------------------------------------------------------ -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">
      <!-- Left panel: tabs for Content + Design controls -->
      <div class="lg:col-span-2">
        <div
          class="rounded-xl border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800 overflow-hidden"
        >
          <Tabs value="content">
            <TabList>
              <Tab value="content">
                <span class="flex items-center gap-1.5">
                  <i class="pi pi-pencil text-xs" /> Content
                </span>
              </Tab>
              <Tab value="design">
                <span class="flex items-center gap-1.5">
                  <i class="pi pi-palette text-xs" /> Design
                </span>
              </Tab>
            </TabList>
            <TabPanels>
              <TabPanel value="content" class="p-4">
                <ContentPanel />
              </TabPanel>
              <TabPanel value="design" class="p-4">
                <DesignPanel />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </div>
      </div>

      <!-- Right panel: live QR preview + download actions -->
      <div class="lg:col-span-3 flex justify-center">
        <div
          class="rounded-xl border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800 p-8 w-full flex flex-col items-center gap-6"
        >
          <h2 class="text-base font-semibold text-surface-900 dark:text-surface-0 self-start">
            Live Preview
            <span class="text-xs font-normal text-surface-400 ml-2">updates in real-time</span>
          </h2>
          <QRCanvas />
        </div>
      </div>
    </div>
  </div>
</template>
