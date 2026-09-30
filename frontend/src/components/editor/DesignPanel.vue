<script setup lang="ts">
import { ref } from 'vue'
import { useQREditorStore } from '@/stores/qrEditor'
import { uploadLogo, type TextLabelOptions } from '@/api/qrcodes'

const store = useQREditorStore()

// ---------------------------------------------------------------------------
// Option lists for selects
// ---------------------------------------------------------------------------
const fontFamilyOptions = [
  { label: 'System Sans-serif', value: 'sans-serif' },
  { label: 'System Serif', value: 'serif' },
  { label: 'System Monospace', value: 'monospace' },
  { label: 'Arial', value: 'Arial, sans-serif' },
  { label: 'Georgia', value: 'Georgia, serif' },
  { label: 'Courier New', value: "'Courier New', monospace" },
  { label: 'Trebuchet MS', value: "'Trebuchet MS', sans-serif" },
  { label: 'Impact', value: 'Impact, sans-serif' },
]

const alignOptions = [
  { label: 'Left', value: 'left', icon: 'pi pi-align-left' },
  { label: 'Center', value: 'center', icon: 'pi pi-align-center' },
  { label: 'Right', value: 'right', icon: 'pi pi-align-right' },
]

/** Patch one label key (labelTop or labelBottom) with a partial update. */
function updateLabel(key: 'labelTop' | 'labelBottom', patch: Partial<TextLabelOptions>) {
  store.updateConfig({ [key]: { ...store.designConfig[key], ...patch } })
}

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

    <!-- ------------------------------------------------------------------ -->
    <!-- Text Labels                                                          -->
    <!-- ------------------------------------------------------------------ -->
    <AccordionPanel value="labels">
      <AccordionHeader>
        <span class="flex items-center gap-2">
          <i class="pi pi-pencil text-sm" />
          Text Labels
        </span>
      </AccordionHeader>
      <AccordionContent>
        <div class="flex flex-col gap-6 py-2">
          <!-- Iterate over both label slots -->
          <template
            v-for="key in (['labelTop', 'labelBottom'] as const)"
            :key="key"
          >
            <div class="flex flex-col gap-3">
              <!-- Section heading + enable toggle -->
              <div class="flex items-center justify-between">
                <span class="text-xs font-semibold text-surface-600 dark:text-surface-300 uppercase tracking-wide">
                  {{ key === 'labelTop' ? 'Top Label' : 'Bottom Label' }}
                </span>
                <ToggleSwitch
                  :model-value="store.designConfig[key].enabled"
                  @update:model-value="(v) => updateLabel(key, { enabled: v })"
                />
              </div>

              <!-- Controls (only visible when enabled) -->
              <template v-if="store.designConfig[key].enabled">
                <!-- Text input -->
                <div class="flex flex-col gap-1">
                  <label class="text-xs text-surface-500">Text</label>
                  <Textarea
                    :model-value="store.designConfig[key].text"
                    placeholder="Label text…"
                    rows="2"
                    class="w-full text-sm"
                    auto-resize
                    @update:model-value="(v) => updateLabel(key, { text: String(v) })"
                  />
                </div>

                <!-- Font family -->
                <div class="flex flex-col gap-1">
                  <label class="text-xs text-surface-500">Font</label>
                  <Select
                    :model-value="store.designConfig[key].fontFamily"
                    :options="fontFamilyOptions"
                    option-label="label"
                    option-value="value"
                    class="w-full"
                    @update:model-value="(v) => updateLabel(key, { fontFamily: v })"
                  />
                </div>

                <!-- Font size -->
                <div class="flex flex-col gap-1">
                  <label class="text-xs text-surface-500">
                    Size — {{ store.designConfig[key].fontSize }}px
                  </label>
                  <Slider
                    :model-value="store.designConfig[key].fontSize"
                    :min="8"
                    :max="48"
                    :step="1"
                    class="w-full"
                    @update:model-value="(v) => updateLabel(key, { fontSize: Number(v) })"
                  />
                </div>

                <!-- Weight + Style toggles -->
                <div class="flex gap-2">
                  <Button
                    :label="'B'"
                    size="small"
                    :severity="store.designConfig[key].fontWeight === 'bold' ? 'primary' : 'secondary'"
                    class="font-bold w-10"
                    @click="updateLabel(key, { fontWeight: store.designConfig[key].fontWeight === 'bold' ? 'normal' : 'bold' })"
                  />
                  <Button
                    :label="'I'"
                    size="small"
                    :severity="store.designConfig[key].fontStyle === 'italic' ? 'primary' : 'secondary'"
                    class="italic w-10"
                    @click="updateLabel(key, { fontStyle: store.designConfig[key].fontStyle === 'italic' ? 'normal' : 'italic' })"
                  />
                </div>

                <!-- Color -->
                <div class="flex items-center gap-3">
                  <label class="text-xs text-surface-500 w-12 shrink-0">Color</label>
                  <input
                    type="color"
                    :value="store.designConfig[key].color"
                    class="h-8 w-16 rounded cursor-pointer border border-surface-300 dark:border-surface-600"
                    @input="(e) => updateLabel(key, { color: (e.target as HTMLInputElement).value })"
                  />
                  <code class="text-xs text-surface-500">{{ store.designConfig[key].color }}</code>
                </div>

                <!-- Alignment -->
                <div class="flex flex-col gap-1">
                  <label class="text-xs text-surface-500">Alignment</label>
                  <div class="flex gap-1">
                    <Button
                      v-for="opt in alignOptions"
                      :key="opt.value"
                      :icon="opt.icon"
                      size="small"
                      :severity="store.designConfig[key].align === opt.value ? 'primary' : 'secondary'"
                      :aria-label="opt.label"
                      @click="updateLabel(key, { align: opt.value as 'left' | 'center' | 'right' })"
                    />
                  </div>
                </div>

                <!-- Letter spacing -->
                <div class="flex flex-col gap-1">
                  <label class="text-xs text-surface-500">
                    Letter Spacing — {{ store.designConfig[key].letterSpacing }}px
                  </label>
                  <Slider
                    :model-value="store.designConfig[key].letterSpacing"
                    :min="-2"
                    :max="10"
                    :step="0.5"
                    class="w-full"
                    @update:model-value="(v) => updateLabel(key, { letterSpacing: Number(v) })"
                  />
                </div>

                <!-- Padding -->
                <div class="flex flex-col gap-1">
                  <label class="text-xs text-surface-500">
                    Padding — {{ store.designConfig[key].padding }}px
                  </label>
                  <Slider
                    :model-value="store.designConfig[key].padding"
                    :min="0"
                    :max="32"
                    :step="2"
                    class="w-full"
                    @update:model-value="(v) => updateLabel(key, { padding: Number(v) })"
                  />
                </div>
              </template>
            </div>

            <!-- Divider between top and bottom sections -->
            <Divider v-if="key === 'labelTop'" class="my-0" />
          </template>
        </div>
      </AccordionContent>
    </AccordionPanel>
  </Accordion>
</template>

