<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useQREditorStore } from '@/stores/qrEditor'
import { getQRCode } from '@/api/qrcodes'
import QRCanvas from '@/components/editor/QRCanvas.vue'
import ContentPanel from '@/components/editor/ContentPanel.vue'
import DesignPanel from '@/components/editor/DesignPanel.vue'

const route = useRoute()
const router = useRouter()
const store = useQREditorStore()
const toast = useToast()

// Below lg the editor is one column, so the form and the preview take turns
// on screen. Both stay mounted (hidden with CSS) so the preview keeps
// rendering, downloads keep working and the open tab is kept.
type EditorPane = 'edit' | 'preview'
const pane = ref<EditorPane>('edit')
const paneOptions = [
  { label: 'Edit', value: 'edit', icon: 'pi pi-pencil' },
  { label: 'Preview', value: 'preview', icon: 'pi pi-eye' },
]
const rootRef = ref<HTMLElement>()
// Each pane keeps its own scroll position, so peeking at the preview
// returns you to the field you were on
const paneScroll: Record<EditorPane, number> = { edit: 0, preview: 0 }

async function setPane(next: EditorPane | null) {
  if (!next || next === pane.value) return
  const scroller = rootRef.value?.closest('.app-main') as HTMLElement | null
  if (scroller) paneScroll[pane.value] = scroller.scrollTop
  pane.value = next
  await nextTick()
  if (scroller) scroller.scrollTop = paneScroll[next]
}

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
  const isNew = !route.params.id
  try {
    const qr = await store.save()
    // Update URL to edit mode without re-mounting the component
    if (isNew) {
      router.replace(`/editor/${qr.id}`)
      toast.add({
        severity: 'success',
        summary: 'QR Code Created',
        detail: `"${qr.title}" was saved successfully.`,
        life: 3000,
      })
    }
  } catch (err: unknown) {
    console.error('Save failed', err)
    // Extract a human-readable message from the Axios error response if available
    // (FastAPI validation errors arrive as a list of { msg } objects rather than a string)
    const raw = (err as { response?: { data?: { detail?: string | { msg: string }[] } } })?.response?.data?.detail
    const detail = Array.isArray(raw)
      ? raw.map((e) => e.msg).join(' ')
      : raw ?? 'An unexpected error occurred. Please try again.'
    toast.add({
      severity: 'error',
      summary: 'Save Failed',
      detail,
      life: 6000,
    })
  }
}
</script>

<template>
  <div ref="rootRef" class="qr-editor flex flex-col gap-4 lg:gap-6">
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
        :disabled="!store.canSave"
        class="max-lg:!hidden"
        @click="handleSave"
      />
    </div>

    <!-- Single-column layouts: switch between the form and the preview,
         with Save always in reach -->
    <div class="editor-switcher">
      <SelectButton
        :model-value="pane"
        :options="paneOptions"
        option-label="label"
        option-value="value"
        :allow-empty="false"
        aria-label="Show the form or the preview"
        class="pane-toggle"
        @update:model-value="setPane"
      >
        <template #option="{ option }">
          <i :class="option.icon" class="text-sm" aria-hidden="true" />
          <span>{{ option.label }}</span>
        </template>
      </SelectButton>
      <Button
        :label="store.isSaving ? 'Saving…' : 'Save'"
        icon="pi pi-save"
        :loading="store.isSaving"
        :disabled="!store.canSave"
        class="switcher-save"
        @click="handleSave"
      />
    </div>

    <!-- ------------------------------------------------------------------ -->
    <!-- Two-panel editor layout                                             -->
    <!-- ------------------------------------------------------------------ -->
    <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,3fr)_minmax(23rem,2fr)] gap-6 items-start">
      <!-- Left panel: tabs for Content + Design controls -->
      <div class="min-w-0" :class="{ 'max-lg:hidden': pane !== 'edit' }">
        <div
          class="rounded-xl overflow-hidden border transition-colors duration-200"
          style="background-color: var(--bg-card); border-color: var(--border);"
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
              <TabPanel value="content" class="editor-tabpanel">
                <ContentPanel />
              </TabPanel>
              <TabPanel value="design" class="editor-tabpanel">
                <DesignPanel />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </div>
      </div>

      <!-- Right panel: live QR preview + download actions -->
      <div class="min-w-0 flex justify-center" :class="{ 'max-lg:hidden': pane !== 'preview' }">
        <div
          class="rounded-xl border p-4 sm:p-8 w-full flex flex-col items-center gap-6 transition-colors duration-200"
          style="background-color: var(--bg-card); border-color: var(--border);"
        >
          <h2 class="text-base font-semibold text-surface-900 dark:text-surface-0 self-start">
            Live Preview
            <span class="text-xs font-normal text-surface-400 ml-2">updates in real-time</span>
          </h2>
          <!-- Dynamic QR notice -->
          <p
            v-if="store.qrType === 'DYNAMIC'"
            class="self-start text-xs text-primary-600 dark:text-primary-400 flex items-center gap-1"
          >
            <i class="pi pi-link text-xs" />
            Dynamic QR — Redirect URL will be encoded automatically
          </p>
          <p
            v-if="store.qrType === 'DYNAMIC' && !store.isEditing"
            class="self-start text-xs text-surface-400"
          >
            This preview is a placeholder. Save the code to get the real one and download it.
          </p>
          <QRCanvas />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Sticky so the switch and Save stay reachable from deep in a long form.
   The opaque background hides the form scrolling underneath. Sticky offsets
   are measured inside the scroll area's padding, so a negative top equal to
   that padding (see .app-main in AppLayout) pins the bar flush to the top. */
.editor-switcher {
  position: sticky;
  top: -1rem;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-block: -0.5rem;
  padding-block: 0.5rem;
  background-color: var(--bg-base);
}
@media (min-width: 641px) {
  .editor-switcher { top: -1.25rem; }
}
/* Two-column layout shows both panes, so no switch */
@media (min-width: 1024px) {
  .editor-switcher { display: none; }
}

.pane-toggle {
  flex: 1;
  display: flex;
}
.pane-toggle :deep(.p-togglebutton) {
  flex: 1;
  min-height: 44px;
}
.pane-toggle :deep(.p-togglebutton-content) {
  gap: 0.5rem;
}
.switcher-save {
  min-height: 44px;
  flex-shrink: 0;
}

.editor-tabpanel {
  padding: 1rem;
}

/* Phones: the page, tab panel and accordion padding stack up and squeeze
   the fields, so trim each layer. */
@media (max-width: 640px) {
  .qr-editor :deep(.p-tabpanels) {
    padding: 0.75rem;
  }
  .editor-tabpanel {
    padding: 0;
  }
  .qr-editor :deep(.p-accordionheader) {
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }
  .qr-editor :deep(.p-accordioncontent-content) {
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }
}

/* Touch: give the editor's small controls a 44 px hit area */
@media (pointer: coarse) {
  .qr-editor :deep(input[type='color']) {
    min-height: 44px;
  }
  .qr-editor :deep(.p-button-sm) {
    min-height: 44px;
    min-width: 44px;
  }
  /* The slider handle is drawn at 20 px; this widens what a finger can grab
     without changing how it looks (the theme already uses ::before) */
  .qr-editor :deep(.p-slider-handle)::after {
    content: '';
    position: absolute;
    inset: -12px;
  }
  .qr-editor :deep(.p-slider-horizontal) {
    margin-block: 12px;
  }
}
</style>
