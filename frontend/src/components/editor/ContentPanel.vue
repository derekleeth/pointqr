<script setup lang="ts">
import { computed } from 'vue'
import { useQREditorStore } from '@/stores/qrEditor'

const store = useQREditorStore()

// Two-way binding for the QR encoded content
const content = computed({
  get: () => store.designConfig.content,
  set: (v: string) => store.setContent(v),
})

const isDynamic = computed({
  get: () => store.qrType === 'DYNAMIC',
  set: (v: boolean) => {
    store.qrType = v ? 'DYNAMIC' : 'STATIC'
  },
})
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
        <div
          class="flex-1 border rounded-lg p-3 cursor-pointer transition-all"
          :class="
            !isDynamic
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
              : 'border-surface-200 dark:border-surface-700 hover:border-surface-400'
          "
          @click="isDynamic = false"
        >
          <p class="font-semibold text-sm text-surface-900 dark:text-surface-0">Static</p>
          <p class="text-xs text-surface-500 mt-0.5">Content fixed at creation</p>
        </div>
        <div
          class="flex-1 border rounded-lg p-3 cursor-pointer transition-all"
          :class="
            isDynamic
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
              : 'border-surface-200 dark:border-surface-700 hover:border-surface-400'
          "
          @click="isDynamic = true"
        >
          <p class="font-semibold text-sm text-surface-900 dark:text-surface-0">Dynamic</p>
          <p class="text-xs text-surface-500 mt-0.5">Redirect URL editable anytime</p>
        </div>
      </div>
    </div>

    <!-- Content input -->
    <div class="flex flex-col gap-1">
      <label class="text-sm font-medium text-surface-700 dark:text-surface-300">
        {{ isDynamic ? 'Destination URL' : 'Content (URL, text, vCard…)' }}
      </label>
      <Textarea
        v-model="content"
        :placeholder="isDynamic ? 'https://your-destination.com' : 'https://example.com'"
        rows="3"
        class="w-full font-mono text-sm"
        auto-resize
      />
      <p class="text-xs text-surface-400">
        {{ content.length }} characters
      </p>
    </div>

    <Message v-if="isDynamic" severity="info" :closable="false" class="text-sm">
      The QR code encodes a PointQR short link. You can update the destination URL at any time
      without reprinting — available in Phase 3.
    </Message>
  </div>
</template>

