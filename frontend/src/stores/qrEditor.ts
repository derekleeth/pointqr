import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  createQRCode,
  updateQRCode,
  DEFAULT_DESIGN_CONFIG,
  type DesignConfig,
  type QRCodeRead,
} from '@/api/qrcodes'

export const useQREditorStore = defineStore('qrEditor', () => {
  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------
  const currentQRCode = ref<QRCodeRead | null>(null)
  const isDirty = ref(false)
  const isSaving = ref(false)
  const exportJobId = ref<string | null>(null)
  const exportStatus = ref<'idle' | 'pending' | 'processing' | 'completed' | 'failed'>('idle')

  // Deep-cloned mutable design config
  const designConfig = ref<DesignConfig>(structuredClone(DEFAULT_DESIGN_CONFIG))
  const title = ref('Untitled QR Code')
  const qrType = ref<'STATIC' | 'DYNAMIC'>('STATIC')
  const targetUrl = ref('')

  // -------------------------------------------------------------------------
  // Getters
  // -------------------------------------------------------------------------
  const isEditing = computed(() => !!currentQRCode.value)
  const hasContent = computed(() =>
    qrType.value === 'DYNAMIC'
      ? targetUrl.value.trim().length > 0
      : designConfig.value.content.trim().length > 0,
  )

  // -------------------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------------------

  /** Load editor state from a persisted QRCodeRead. */
  function loadFromQRCode(qr: QRCodeRead): void {
    currentQRCode.value = qr
    title.value = qr.title
    qrType.value = qr.type
    targetUrl.value = qr.target_url ?? ''

    const saved = qr.design_config ?? {}

    // Deep-merge: start from a clean clone of defaults, then overlay each
    // top-level key from the server. For nested objects (labels, imageOptions,
    // etc.) we merge against their own sub-defaults so missing fields never
    // cause undefined access.
    const defaults = structuredClone(DEFAULT_DESIGN_CONFIG)
    designConfig.value = {
      ...defaults,
      ...saved,
      // Explicit sub-object merges so a partially-populated server response
      // (e.g. old records saved before labels were added) still produces a
      // fully-valid config object.
      imageOptions: { ...defaults.imageOptions, ...(saved.imageOptions ?? {}) },
      labelTop: { ...defaults.labelTop, ...(saved.labelTop ?? {}) },
      labelBottom: { ...defaults.labelBottom, ...(saved.labelBottom ?? {}) },
    }
    isDirty.value = false
  }

  /** Reset the editor to blank defaults. */
  function resetToDefaults(): void {
    currentQRCode.value = null
    title.value = 'Untitled QR Code'
    qrType.value = 'STATIC'
    targetUrl.value = ''
    designConfig.value = structuredClone(DEFAULT_DESIGN_CONFIG)
    isDirty.value = false
  }

  /** Shallow-merge a partial DesignConfig patch. Use for top-level fields. */
  function updateConfig(patch: Partial<DesignConfig>): void {
    designConfig.value = { ...designConfig.value, ...patch }
    isDirty.value = true
  }

  /** Update the encoded QR content and mark dirty. */
  function setContent(content: string): void {
    designConfig.value.content = content
    isDirty.value = true
  }

  /** Create or update the QR code via the API and clear the dirty flag. */
  async function save(): Promise<QRCodeRead> {
    isSaving.value = true
    try {
      const payload = {
        title: title.value,
        type: qrType.value,
        target_url: targetUrl.value || undefined,
        design_config: designConfig.value,
      }

      let result: QRCodeRead
      if (currentQRCode.value) {
        const { data } = await updateQRCode(currentQRCode.value.id, payload)
        result = data
      } else {
        const { data } = await createQRCode(payload)
        result = data
      }

      // Sync local state from server response so designConfig.content reflects
      // the redirect URL that the backend injected for dynamic QR codes.
      loadFromQRCode(result)
      return result
    } finally {
      isSaving.value = false
    }
  }

  return {
    // state
    currentQRCode,
    isDirty,
    isSaving,
    exportJobId,
    exportStatus,
    designConfig,
    title,
    qrType,
    targetUrl,
    // getters
    isEditing,
    hasContent,
    // actions
    loadFromQRCode,
    resetToDefaults,
    updateConfig,
    setContent,
    save,
  }
})

