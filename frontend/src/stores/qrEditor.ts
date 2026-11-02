import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import {
  createQRCode,
  updateQRCode,
  DEFAULT_DESIGN_CONFIG,
  type ContactData,
  type DesignConfig,
  type QRCodeRead,
  type QRContentType,
} from '@/api/qrcodes'
import { estimateDensity } from '@/utils/qrData'
import {
  buildContactPayload,
  contactDisplayName,
  contactFromServer,
  emptyContact,
  hasContactErrors,
  hasContactName,
  normalizeContact,
  validateContact,
  withoutHostedFields,
  type ContactFormState,
} from '@/utils/vcard'

const DEFAULT_TITLE = 'Untitled QR Code'
const MAX_TITLE_LENGTH = 255

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
  const title = ref(DEFAULT_TITLE)
  const qrType = ref<'STATIC' | 'DYNAMIC'>('STATIC')
  const targetUrl = ref('')
  const contentType = ref<QRContentType>('URL')
  const contact = ref<ContactFormState>(emptyContact())
  // URL/text content kept aside while the contact form owns designConfig.content
  const plainContent = ref('')

  // -------------------------------------------------------------------------
  // Getters
  // -------------------------------------------------------------------------
  const isEditing = computed(() => !!currentQRCode.value)
  const density = computed(() =>
    estimateDensity(designConfig.value.content, designConfig.value.qrOptions.errorCorrectionLevel),
  )
  const hasContent = computed(() => {
    if (qrType.value === 'DYNAMIC') {
      return contentType.value === 'VCARD'
        ? hasContactName(contact.value)
        : targetUrl.value.trim().length > 0
    }
    return designConfig.value.content.trim().length > 0 && !density.value.isTooLarge
  })
  // Hosted-page fields are hidden on static codes, so they can't be what blocks saving
  const contactErrors = computed(() =>
    validateContact(
      qrType.value === 'STATIC' ? { ...contact.value, social_links: [] } : contact.value,
    ),
  )
  const canSave = computed(
    () =>
      hasContent.value &&
      (contentType.value !== 'VCARD' || !hasContactErrors(contactErrors.value)),
  )
  // A dynamic code's short link doesn't exist until it's saved, and the preview is only a placeholder
  const canDownload = computed(
    () => hasContent.value && (qrType.value !== 'DYNAMIC' || !!currentQRCode.value),
  )

  // -------------------------------------------------------------------------
  // Contact form sync
  // -------------------------------------------------------------------------

  /** The contact as it gets saved, which depends on whether there's a hosted page. */
  function contactToSave(): ContactData {
    const normalized = normalizeContact(contact.value)
    return qrType.value === 'STATIC'
      ? withoutHostedFields(normalized)
      : { ...normalized, encoding: 'vcard' }
  }

  /**
   * Static contact codes encode the vCard itself, so rebuild it for the live preview.
   * Dynamic ones encode the redirect URL the server assigns on the first save.
   */
  function syncContactContent(): void {
    if (contentType.value !== 'VCARD') return
    if (qrType.value === 'DYNAMIC') {
      if (!currentQRCode.value) designConfig.value.content = ''
      return
    }
    designConfig.value.content = hasContactName(contact.value)
      ? buildContactPayload(contactToSave())
      : ''
  }

  // The last title filled in from the contact, so a title the user typed is never overwritten.
  let autoTitle: string | null = null

  /** Name the code after the contact until the user gives it their own title. */
  function syncContactTitle(): void {
    if (title.value !== DEFAULT_TITLE && title.value !== autoTitle) return
    const name =
      contentType.value === 'VCARD'
        ? contactDisplayName(normalizeContact(contact.value)).slice(0, MAX_TITLE_LENGTH)
        : ''
    autoTitle = name || null
    title.value = name || DEFAULT_TITLE
  }

  // Replacing the form from load/reset isn't a user edit, so it must not mark the code dirty.
  let replacingContact = false
  function replaceContact(next: ContactFormState): void {
    replacingContact = true
    contact.value = next
    replacingContact = false
  }

  watch(
    contact,
    () => {
      if (replacingContact) return
      syncContactContent()
      syncContactTitle()
      isDirty.value = true
    },
    { deep: true, flush: 'sync' },
  )

  watch(qrType, syncContactContent, { flush: 'sync' })

  // -------------------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------------------

  /** Load editor state from a persisted QRCodeRead. */
  function loadFromQRCode(qr: QRCodeRead): void {
    currentQRCode.value = qr
    autoTitle = null
    title.value = qr.title
    qrType.value = qr.type
    targetUrl.value = qr.target_url ?? ''
    contentType.value = qr.content_type
    replaceContact(contactFromServer(qr.content_data))
    plainContent.value = qr.content_type === 'VCARD' ? '' : (qr.design_config?.content ?? '')

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
    autoTitle = null
    title.value = DEFAULT_TITLE
    qrType.value = 'STATIC'
    targetUrl.value = ''
    contentType.value = 'URL'
    replaceContact(emptyContact())
    plainContent.value = ''
    designConfig.value = structuredClone(DEFAULT_DESIGN_CONFIG)
    isDirty.value = false
  }

  /** Switch content type, keeping what was typed so switching back doesn't lose it. */
  function setContentType(next: QRContentType): void {
    if (next === contentType.value) return
    const leavingContact = contentType.value === 'VCARD'
    // A saved dynamic code keeps encoding its redirect URL, whatever it points to
    const keepsContent = qrType.value === 'DYNAMIC' && !!currentQRCode.value
    if (next === 'VCARD' && !keepsContent) plainContent.value = designConfig.value.content
    contentType.value = next
    if (next === 'VCARD') syncContactContent()
    else if (leavingContact && !keepsContent) designConfig.value.content = plainContent.value
    syncContactTitle()
    isDirty.value = true
  }

  /** Shallow-merge a partial DesignConfig patch. Use for top-level fields. */
  function updateConfig(patch: Partial<DesignConfig>): void {
    designConfig.value = { ...designConfig.value, ...patch }
    isDirty.value = true
  }

  /** Apply a photo the server has already saved, without touching unsaved form edits. */
  function applySavedPhoto(qr: QRCodeRead): void {
    currentQRCode.value = qr
    replacingContact = true
    contact.value.photo_url = qr.content_data?.photo_url ?? null
    replacingContact = false
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
      const isContact = contentType.value === 'VCARD'
      const payload = {
        title: title.value,
        type: qrType.value,
        target_url: isContact ? undefined : targetUrl.value || undefined,
        content_type: contentType.value,
        content_data: isContact ? contactToSave() : undefined,
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
    contentType,
    contact,
    // getters
    isEditing,
    density,
    hasContent,
    contactErrors,
    canSave,
    canDownload,
    // actions
    loadFromQRCode,
    resetToDefaults,
    setContentType,
    contactToSave,
    applySavedPhoto,
    updateConfig,
    setContent,
    save,
  }
})

