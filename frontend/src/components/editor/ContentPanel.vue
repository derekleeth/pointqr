<script setup lang="ts">
import { computed } from 'vue'
import { useQREditorStore } from '@/stores/qrEditor'
import ContactForm from '@/components/editor/ContactForm.vue'
import DensityMeter from '@/components/editor/DensityMeter.vue'

const store = useQREditorStore()

// For static QRs: bind to designConfig.content (what gets encoded in the QR).
// For dynamic QRs: bind to targetUrl (the destination — the backend encodes
// the redirect short-link into designConfig.content automatically).
const content = computed({
  get: () => (store.qrType === 'DYNAMIC' ? store.targetUrl : store.designConfig.content),
  set: (v: string) => {
    if (store.qrType === 'DYNAMIC') {
      store.targetUrl = v
      store.isDirty = true
    } else {
      store.setContent(v)
    }
  },
})

const isDynamic = computed({
  get: () => store.qrType === 'DYNAMIC',
  set: (v: boolean) => {
    // The API doesn't change a code's type after creation
    if (store.isEditing || (v && !canBeDynamic.value)) return
    store.qrType = v ? 'DYNAMIC' : 'STATIC'
  },
})

// Text can't redirect, and hosted contact pages don't exist until /r/{short_code}
// learns to serve them (Phase 3 of docs/features/contact-qr-codes.md). A dynamic
// contact code printed before then would scan to an empty redirect.
const canBeDynamic = computed(() => store.contentType === 'URL')

const contentTypeOptions = computed(() =>
  [
    { label: 'URL', value: 'URL' },
    { label: 'Text', value: 'TEXT' },
    { label: 'Contact', value: 'VCARD' },
  ].map((option) => ({
    ...option,
    disabled: isDynamic.value && option.value !== store.contentType,
  })),
)
</script>

<template>
  <div class="flex flex-col gap-5">
    <!-- Title -->
    <div class="flex flex-col gap-1">
      <label class="text-sm font-medium text-surface-700 dark:text-surface-300">Name</label>
      <InputText
        v-model="store.title"
        placeholder="My QR Code"
        class="w-full"
        @input="store.isDirty = true"
      />
    </div>

    <!-- Static vs Dynamic selector -->
    <div class="flex flex-col gap-2">
      <label class="text-sm font-medium text-surface-700 dark:text-surface-300">QR Type</label>
      <div class="flex gap-3">
        <!-- Static card -->
        <div
          class="flex-1 relative border-2 rounded-lg p-3 transition-all select-none"
          :class="[
            store.isEditing ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
            !isDynamic
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/40 ring-2 ring-primary-300 dark:ring-primary-700'
              : 'border-surface-200 dark:border-surface-700 hover:border-surface-400 dark:hover:border-surface-500',
          ]"
          @click="isDynamic = false"
        >
          <!-- Check badge (selected) -->
          <span
            v-if="!isDynamic"
            class="absolute top-2 right-2 flex items-center justify-center w-4 h-4 rounded-full bg-primary-500 text-white"
          >
            <i class="pi pi-check" style="font-size: 0.55rem" />
          </span>
          <p
            class="font-semibold text-sm"
            :class="!isDynamic ? 'text-primary-700 dark:text-primary-300' : 'text-surface-900 dark:text-surface-0'"
          >
            Static
          </p>
          <p class="text-xs mt-0.5" :class="!isDynamic ? 'text-primary-500 dark:text-primary-400' : 'text-surface-500'">
            Content fixed at creation
          </p>
        </div>

        <!-- Dynamic card -->
        <div
          class="flex-1 relative border-2 rounded-lg p-3 transition-all select-none"
          :class="[
            store.isEditing || !canBeDynamic ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
            isDynamic
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/40 ring-2 ring-primary-300 dark:ring-primary-700'
              : 'border-surface-200 dark:border-surface-700 hover:border-surface-400 dark:hover:border-surface-500',
          ]"
          @click="isDynamic = true"
        >
          <!-- Check badge (selected) -->
          <span
            v-if="isDynamic"
            class="absolute top-2 right-2 flex items-center justify-center w-4 h-4 rounded-full bg-primary-500 text-white"
          >
            <i class="pi pi-check" style="font-size: 0.55rem" />
          </span>
          <p
            class="font-semibold text-sm"
            :class="isDynamic ? 'text-primary-700 dark:text-primary-300' : 'text-surface-900 dark:text-surface-0'"
          >
            Dynamic
          </p>
          <p class="text-xs mt-0.5" :class="isDynamic ? 'text-primary-500 dark:text-primary-400' : 'text-surface-500'">
            Redirect URL editable anytime
          </p>
        </div>
      </div>
    </div>

    <!-- Content type selector -->
    <div class="flex flex-col gap-2">
      <label class="text-sm font-medium text-surface-700 dark:text-surface-300">Content</label>
      <SelectButton
        :model-value="store.contentType"
        :options="contentTypeOptions"
        option-label="label"
        option-value="value"
        option-disabled="disabled"
        :allow-empty="false"
        aria-label="Content type"
        @update:model-value="store.setContentType"
      />
      <p v-if="store.isEditing" class="text-xs text-surface-400">
        Static or dynamic can't be changed once a code is created.
      </p>
      <p v-else-if="isDynamic" class="text-xs text-surface-400">
        Dynamic codes currently support URLs only.
      </p>
      <p v-else-if="!canBeDynamic" class="text-xs text-surface-400">
        {{ store.contentType === 'TEXT' ? 'Text' : 'Contact' }} codes are static only for now.
      </p>
    </div>

    <!-- Contact form -->
    <ContactForm v-if="store.contentType === 'VCARD'" />

    <!-- Content input -->
    <div v-else class="flex flex-col gap-1">
      <label class="text-sm font-medium text-surface-700 dark:text-surface-300">
        {{ isDynamic ? 'Destination URL' : store.contentType === 'TEXT' ? 'Text' : 'URL' }}
      </label>
      <Textarea
        v-model="content"
        :placeholder="isDynamic ? 'https://your-destination.com' : store.contentType === 'TEXT' ? 'Your message' : 'https://example.com'"
        rows="3"
        class="w-full font-mono text-sm"
        auto-resize
      />
      <p class="text-xs text-surface-400">
        {{ content.length }} characters
      </p>
      <!-- Helper text for dynamic URL field -->
      <p v-if="isDynamic" class="text-xs text-primary-600 dark:text-primary-400">
        Scans will redirect to this URL via PointQR's redirect service.
      </p>
    </div>

    <!-- A dynamic code's payload is always a short redirect URL, so density only matters when static -->
    <DensityMeter v-if="!isDynamic && store.designConfig.content" />

    <Message v-if="isDynamic && store.contentType === 'URL'" severity="info" :closable="false" class="text-sm">
      <span class="font-semibold">Dynamic QR</span> → Redirect URL will be encoded automatically.
      You can update the destination URL at any time without reprinting.
    </Message>
  </div>
</template>

