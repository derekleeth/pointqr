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
        <!-- Static card -->
        <div
          class="flex-1 relative border-2 rounded-lg p-3 cursor-pointer transition-all select-none"
          :class="
            !isDynamic
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/40 ring-2 ring-primary-300 dark:ring-primary-700'
              : 'border-surface-200 dark:border-surface-700 hover:border-surface-400 dark:hover:border-surface-500'
          "
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
          class="flex-1 relative border-2 rounded-lg p-3 cursor-pointer transition-all select-none"
          :class="
            isDynamic
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/40 ring-2 ring-primary-300 dark:ring-primary-700'
              : 'border-surface-200 dark:border-surface-700 hover:border-surface-400 dark:hover:border-surface-500'
          "
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
      <!-- Helper text for dynamic URL field -->
      <p v-if="isDynamic" class="text-xs text-primary-600 dark:text-primary-400">
        Scans will redirect to this URL via PointQR's redirect service.
      </p>
    </div>

    <Message v-if="isDynamic" severity="info" :closable="false" class="text-sm">
      <span class="font-semibold">Dynamic QR</span> → Redirect URL will be encoded automatically.
      You can update the destination URL at any time without reprinting.
    </Message>
  </div>
</template>

