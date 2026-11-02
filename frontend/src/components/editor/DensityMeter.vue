<script setup lang="ts">
import { computed } from 'vue'
import { useQREditorStore } from '@/stores/qrEditor'

const store = useQREditorStore()

const level = computed(() => store.designConfig.qrOptions.errorCorrectionLevel)

const rating = computed(() => {
  if (store.density.isTooLarge) return { label: 'Too large', severity: 'danger' }
  if (store.density.isDense) return { label: 'Dense', severity: 'warn' }
  return { label: 'Good', severity: 'success' }
})

const suggestions = computed(() => {
  const items = ['Remove optional fields.']
  if (level.value !== 'L' && !store.designConfig.imageOptions.src) {
    items.push('Lower the error correction level in the Design tab.')
  }
  if (store.contentType === 'VCARD' && store.contact.encoding === 'vcard') {
    items.push('Turn on the compact format.')
  }
  return items
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center justify-between gap-3">
      <p class="text-xs text-surface-500">
        {{ store.density.bytes.toLocaleString() }} bytes
        <template v-if="store.density.version">
          · about version {{ store.density.version }} ({{ store.density.modules }}×{{ store.density.modules }})
        </template>
        · ECC {{ level }}
      </p>
      <Tag :value="rating.label" :severity="rating.severity" />
    </div>
    <Message v-if="store.density.isTooLarge || store.density.isDense" :severity="rating.severity === 'danger' ? 'error' : 'warn'" :closable="false" class="text-sm">
      <p v-if="store.density.isTooLarge">This is more than a QR code can hold at ECC {{ level }}.</p>
      <p v-else>This code may be hard to scan, especially when printed small.</p>
      <ul class="list-disc pl-4 mt-1">
        <li v-for="item in suggestions" :key="item">{{ item }}</li>
      </ul>
    </Message>
  </div>
</template>
