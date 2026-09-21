<script setup lang="ts">
import { ref } from 'vue'
import { useQREditorStore } from '@/stores/qrEditor'
import { uploadLogo } from '@/api/qrcodes'

const store = useQREditorStore()

// ---------------------------------------------------------------------------
// Option lists for selects
// ---------------------------------------------------------------------------
const dotTypeOptions = [
  { label: 'Square', value: 'square' },
  { label: 'Dots', value: 'dots' },
  { label: 'Rounded', value: 'rounded' },
  { label: 'Classy', value: 'classy' },
  { label: 'Classy Rounded', value: 'classy-rounded' },
  { label: 'Extra Rounded', value: 'extra-rounded' },
]

const cornerSquareOptions = [
  { label: 'Square', value: 'square' },
  { label: 'Dot', value: 'dot' },
  { label: 'Extra Rounded', value: 'extra-rounded' },
]

const cornerDotOptions = [
  { label: 'Square', value: 'square' },
  { label: 'Dot', value: 'dot' },
]

// ---------------------------------------------------------------------------
// Logo upload
// ---------------------------------------------------------------------------
const logoUploading = ref(false)
const logoError = ref('')

async function handleLogoSelect(event: { files: File[] }) {
  const file = event.files[0]
  if (!file || !store.currentQRCode) return

  logoUploading.value = true
  logoError.value = ''
  try {
    const { data } = await uploadLogo(store.currentQRCode.id, file)
    store.loadFromQRCode(data)
  } catch {
    logoError.value = 'Upload failed. Use a PNG, SVG, or JPEG under 500 KB.'
  } finally {
    logoUploading.value = false
  }
}

function removeLogo() {
  store.updateConfig({
    imageOptions: { ...store.designConfig.imageOptions, src: null },
  })
}
</script>

<template>
  <Accordion :value="['dots']" multiple>
    <!-- ------------------------------------------------------------------ -->
    <!-- Dot Style                                                           -->
    <!-- ------------------------------------------------------------------ -->
    <AccordionPanel value="dots">
      <AccordionHeader>
        <span class="flex items-center gap-2">
          <i class="pi pi-th-large text-sm" />
          Dot Style
        </span>
      </AccordionHeader>
      <AccordionContent>
        <div class="flex flex-col gap-3 py-2">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-surface-500">Pattern</label>
            <Select
              :model-value="store.designConfig.dotsOptions.type"
              :options="dotTypeOptions"
              option-label="label"
              option-value="value"
              class="w-full"
              @update:model-value="
                (v) =>
                  store.updateConfig({
                    dotsOptions: { ...store.designConfig.dotsOptions, type: v },
                  })
              "
            />
          </div>
          <div class="flex items-center gap-3">
            <label class="text-xs text-surface-500 w-12 shrink-0">Color</label>
            <input
              type="color"
              :value="store.designConfig.dotsOptions.color"
              class="h-8 w-16 rounded cursor-pointer border border-surface-300 dark:border-surface-600"
              @input="
                (e) =>
                  store.updateConfig({
                    dotsOptions: {
                      ...store.designConfig.dotsOptions,
                      color: (e.target as HTMLInputElement).value,
                    },
                  })
              "
            />
            <code class="text-xs text-surface-500">{{ store.designConfig.dotsOptions.color }}</code>
          </div>
        </div>
      </AccordionContent>
    </AccordionPanel>

    <!-- ------------------------------------------------------------------ -->
    <!-- Corner Squares                                                      -->
    <!-- ------------------------------------------------------------------ -->
    <AccordionPanel value="corners-sq">
      <AccordionHeader>
        <span class="flex items-center gap-2">
          <i class="pi pi-stop text-sm" />
          Corner Squares
        </span>
      </AccordionHeader>
      <AccordionContent>
        <div class="flex flex-col gap-3 py-2">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-surface-500">Style</label>
            <Select
              :model-value="store.designConfig.cornersSquareOptions.type"
              :options="cornerSquareOptions"
              option-label="label"
              option-value="value"
              class="w-full"
              @update:model-value="
                (v) =>
                  store.updateConfig({
                    cornersSquareOptions: {
                      ...store.designConfig.cornersSquareOptions,
                      type: v,
                    },
                  })
              "
            />
          </div>
          <div class="flex items-center gap-3">
            <label class="text-xs text-surface-500 w-12 shrink-0">Color</label>
            <input
              type="color"
              :value="store.designConfig.cornersSquareOptions.color"
              class="h-8 w-16 rounded cursor-pointer border border-surface-300 dark:border-surface-600"
              @input="
                (e) =>
                  store.updateConfig({
                    cornersSquareOptions: {
                      ...store.designConfig.cornersSquareOptions,
                      color: (e.target as HTMLInputElement).value,
                    },
                  })
              "
            />
            <code class="text-xs text-surface-500">{{
              store.designConfig.cornersSquareOptions.color
            }}</code>
          </div>
        </div>
      </AccordionContent>
    </AccordionPanel>

    <!-- ------------------------------------------------------------------ -->
    <!-- Corner Dots                                                         -->
    <!-- ------------------------------------------------------------------ -->
    <AccordionPanel value="corners-dot">
      <AccordionHeader>
        <span class="flex items-center gap-2">
          <i class="pi pi-circle text-sm" />
          Corner Dots
        </span>
      </AccordionHeader>
      <AccordionContent>
        <div class="flex flex-col gap-3 py-2">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-surface-500">Style</label>
            <Select
              :model-value="store.designConfig.cornersDotOptions.type"
              :options="cornerDotOptions"
              option-label="label"
              option-value="value"
              class="w-full"
              @update:model-value="
                (v) =>
                  store.updateConfig({
                    cornersDotOptions: { ...store.designConfig.cornersDotOptions, type: v },
                  })
              "
            />
          </div>
          <div class="flex items-center gap-3">
            <label class="text-xs text-surface-500 w-12 shrink-0">Color</label>
            <input
              type="color"
              :value="store.designConfig.cornersDotOptions.color"
              class="h-8 w-16 rounded cursor-pointer border border-surface-300 dark:border-surface-600"
              @input="
                (e) =>
                  store.updateConfig({
                    cornersDotOptions: {
                      ...store.designConfig.cornersDotOptions,
                      color: (e.target as HTMLInputElement).value,
                    },
                  })
              "
            />
          </div>
        </div>
      </AccordionContent>
    </AccordionPanel>

    <!-- ------------------------------------------------------------------ -->
    <!-- Background                                                          -->
    <!-- ------------------------------------------------------------------ -->
    <AccordionPanel value="background">
      <AccordionHeader>
        <span class="flex items-center gap-2">
          <i class="pi pi-palette text-sm" />
          Background
        </span>
      </AccordionHeader>
      <AccordionContent>
        <div class="flex items-center gap-3 py-2">
          <label class="text-xs text-surface-500 w-12 shrink-0">Color</label>
          <input
            type="color"
            :value="store.designConfig.backgroundOptions.color"
            class="h-8 w-16 rounded cursor-pointer border border-surface-300 dark:border-surface-600"
            @input="
              (e) =>
                store.updateConfig({
                  backgroundOptions: { color: (e.target as HTMLInputElement).value },
                })
            "
          />
          <code class="text-xs text-surface-500">{{
            store.designConfig.backgroundOptions.color
          }}</code>
        </div>
      </AccordionContent>
    </AccordionPanel>

    <!-- ------------------------------------------------------------------ -->
    <!-- Logo                                                               -->
    <!-- ------------------------------------------------------------------ -->
    <AccordionPanel value="logo">
      <AccordionHeader>
        <span class="flex items-center gap-2">
          <i class="pi pi-image text-sm" />
          Logo / Icon
        </span>
      </AccordionHeader>
      <AccordionContent>
        <div class="flex flex-col gap-4 py-2">
          <!-- Current logo preview -->
          <template v-if="store.designConfig.imageOptions.src">
            <div class="flex items-center gap-3">
              <img
                :src="store.designConfig.imageOptions.src"
                class="h-12 w-12 rounded object-contain border border-surface-200 dark:border-surface-700"
                alt="Logo preview"
              />
              <Button label="Remove Logo" severity="danger" text size="small" @click="removeLogo" />
            </div>
          </template>

          <!-- Upload control (only when QR is saved) -->
          <template v-else-if="store.currentQRCode">
            <FileUpload
              mode="basic"
              accept="image/png,image/svg+xml,image/jpeg,image/webp"
              :max-file-size="512000"
              choose-label="Upload Logo"
              :auto="true"
              :disabled="logoUploading"
              @select="handleLogoSelect"
            />
            <Message v-if="logoError" severity="error" :closable="false" class="text-xs">
              {{ logoError }}
            </Message>
            <p class="text-xs text-surface-400">PNG, SVG, or JPEG · max 500 KB</p>
          </template>

          <!-- Prompt to save first -->
          <template v-else>
            <Message severity="warn" :closable="false" class="text-sm">
              Save the QR code first, then upload a logo.
            </Message>
          </template>

          <!-- Logo size slider -->
          <div class="flex flex-col gap-1">
            <label class="text-xs text-surface-500">
              Logo Size —
              {{ Math.round(store.designConfig.imageOptions.imageSize * 100) }}%
            </label>
            <Slider
              :model-value="store.designConfig.imageOptions.imageSize"
              :min="0.1"
              :max="0.6"
              :step="0.05"
              class="w-full"
              @update:model-value="
                (v) =>
                  store.updateConfig({
                    imageOptions: { ...store.designConfig.imageOptions, imageSize: Number(v) },
                  })
              "
            />
          </div>
        </div>
      </AccordionContent>
    </AccordionPanel>
  </Accordion>
</template>

