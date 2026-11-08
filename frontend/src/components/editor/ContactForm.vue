<script setup lang="ts">
import { computed, ref } from 'vue'
import { uploadContactPhoto } from '@/api/qrcodes'
import { useQREditorStore } from '@/stores/qrEditor'
import {
  MAX_EMAILS,
  MAX_PHONES,
  MAX_SOCIAL_LINKS,
  buildVCard,
  contactDisplayName,
  hasContactErrors,
  hasContactName,
} from '@/utils/vcard'

const store = useQREditorStore()

const phoneTypes = [
  { label: 'Mobile', value: 'mobile' },
  { label: 'Work', value: 'work' },
  { label: 'Home', value: 'home' },
  { label: 'Fax', value: 'fax' },
  { label: 'Other', value: 'other' },
]
const emailTypes = [
  { label: 'Work', value: 'work' },
  { label: 'Home', value: 'home' },
  { label: 'Other', value: 'other' },
]
const addressTypes = [
  { label: 'Work', value: 'work' },
  { label: 'Home', value: 'home' },
]

const hasName = computed(() => hasContactName(store.contact))
const canDownload = computed(() => hasName.value && !hasContactErrors(store.contactErrors))

const useMecard = computed({
  get: () => store.contact.encoding === 'mecard',
  set: (v: boolean) => {
    store.contact.encoding = v ? 'mecard' : 'vcard'
  },
})

/** Let users check the contact on their own phone before printing. */
function downloadVcf() {
  const contact = store.contactToSave()
  const name = contactDisplayName(contact).replace(/[^\p{L}\p{N} _-]+/gu, '').trim() || 'contact'
  const url = URL.createObjectURL(new Blob([buildVCard(contact)], { type: 'text/vcard;charset=utf-8' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `${name}.vcf`
  a.click()
  URL.revokeObjectURL(url)
}

const DEFAULT_THEME_COLOR = '#4f46e5'
const MAX_PHOTO_BYTES = 5 * 1024 * 1024

// The live page, once the code is saved. It's the same URL the QR code encodes.
const hostedPageUrl = computed(() =>
  store.qrType === 'DYNAMIC' && store.currentQRCode?.short_code ? store.designConfig.content : '',
)

const photoUploading = ref(false)
const photoError = ref('')

async function handlePhotoSelect(event: { files: File[] }) {
  const file = event.files[0]
  if (!file || !store.currentQRCode) return

  photoUploading.value = true
  photoError.value = ''
  try {
    const { data } = await uploadContactPhoto(store.currentQRCode.id, file)
    store.applySavedPhoto(data)
  } catch {
    photoError.value = 'Upload failed. Use a PNG, JPEG, or WebP image under 5 MB.'
  } finally {
    photoUploading.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <Accordion multiple :value="['name', 'reach']">
      <!-- Name -->
      <AccordionPanel value="name">
        <AccordionHeader>Name</AccordionHeader>
        <AccordionContent>
          <div class="flex flex-col gap-3">
            <div class="grid grid-cols-2 gap-3">
              <div class="flex flex-col gap-1">
                <label for="contact-first-name" class="text-sm font-medium text-surface-700 dark:text-surface-300">First name</label>
                <InputText id="contact-first-name" v-model="store.contact.first_name" maxlength="100" class="w-full" />
              </div>
              <div class="flex flex-col gap-1">
                <label for="contact-last-name" class="text-sm font-medium text-surface-700 dark:text-surface-300">Last name</label>
                <InputText id="contact-last-name" v-model="store.contact.last_name" maxlength="100" class="w-full" />
              </div>
              <div class="flex flex-col gap-1">
                <label for="contact-prefix" class="text-sm font-medium text-surface-700 dark:text-surface-300">Prefix</label>
                <InputText id="contact-prefix" v-model="store.contact.prefix" maxlength="50" placeholder="Dr." class="w-full" />
              </div>
              <div class="flex flex-col gap-1">
                <label for="contact-suffix" class="text-sm font-medium text-surface-700 dark:text-surface-300">Suffix</label>
                <InputText id="contact-suffix" v-model="store.contact.suffix" maxlength="50" placeholder="PhD" class="w-full" />
              </div>
            </div>
            <div class="flex flex-col gap-1">
              <label for="contact-display-name" class="text-sm font-medium text-surface-700 dark:text-surface-300">Display name</label>
              <InputText id="contact-display-name" v-model="store.contact.display_name" maxlength="255" class="w-full" />
              <p class="text-xs text-surface-400">Optional. Built from the name fields when left empty.</p>
            </div>
            <p v-if="!hasName" class="text-xs text-primary-600 dark:text-primary-400">
              Enter a first name, last name or organization to generate the code.
            </p>
          </div>
        </AccordionContent>
      </AccordionPanel>

      <!-- Work -->
      <AccordionPanel value="work">
        <AccordionHeader>Work</AccordionHeader>
        <AccordionContent>
          <div class="flex flex-col gap-3">
            <div class="flex flex-col gap-1">
              <label for="contact-organization" class="text-sm font-medium text-surface-700 dark:text-surface-300">Organization</label>
              <InputText id="contact-organization" v-model="store.contact.organization" maxlength="255" class="w-full" />
            </div>
            <div class="flex flex-col gap-1">
              <label for="contact-job-title" class="text-sm font-medium text-surface-700 dark:text-surface-300">Job title</label>
              <InputText id="contact-job-title" v-model="store.contact.job_title" maxlength="255" class="w-full" />
            </div>
          </div>
        </AccordionContent>
      </AccordionPanel>

      <!-- Phone, email, web -->
      <AccordionPanel value="reach">
        <AccordionHeader>Phone, email &amp; web</AccordionHeader>
        <AccordionContent>
          <div class="flex flex-col gap-4">
            <div class="flex flex-col gap-2">
              <span class="text-sm font-medium text-surface-700 dark:text-surface-300">Phone</span>
              <div v-for="(phone, i) in store.contact.phones" :key="i" class="flex flex-col gap-1">
                <div class="flex flex-wrap gap-2">
                  <Select
                    v-model="phone.type"
                    :options="phoneTypes"
                    option-label="label"
                    option-value="value"
                    :aria-label="`Phone ${i + 1} type`"
                    class="w-32 flex-shrink-0"
                  />
                  <div class="flex flex-1 min-w-48 gap-2">
                    <InputText
                      v-model="phone.number"
                      type="tel"
                      maxlength="32"
                      placeholder="+1 555 010 0100"
                      :aria-label="`Phone ${i + 1} number`"
                      :invalid="!!store.contactErrors.phones[i]"
                      class="flex-1 min-w-0"
                    />
                    <Button
                      icon="pi pi-times"
                      severity="secondary"
                      text
                      rounded
                      :aria-label="`Remove phone ${i + 1}`"
                      @click="store.contact.phones.splice(i, 1)"
                    />
                  </div>
                </div>
                <p v-if="store.contactErrors.phones[i]" class="text-xs text-red-500">{{ store.contactErrors.phones[i] }}</p>
              </div>
              <Button
                label="Add phone"
                icon="pi pi-plus"
                size="small"
                severity="secondary"
                text
                class="self-start"
                :disabled="store.contact.phones.length >= MAX_PHONES"
                @click="store.contact.phones.push({ type: 'mobile', number: '' })"
              />
            </div>

            <div class="flex flex-col gap-2">
              <span class="text-sm font-medium text-surface-700 dark:text-surface-300">Email</span>
              <div v-for="(email, i) in store.contact.emails" :key="i" class="flex flex-col gap-1">
                <div class="flex flex-wrap gap-2">
                  <Select
                    v-model="email.type"
                    :options="emailTypes"
                    option-label="label"
                    option-value="value"
                    :aria-label="`Email ${i + 1} type`"
                    class="w-32 flex-shrink-0"
                  />
                  <div class="flex flex-1 min-w-48 gap-2">
                    <InputText
                      v-model="email.address"
                      type="email"
                      maxlength="254"
                      placeholder="name@example.com"
                      :aria-label="`Email ${i + 1} address`"
                      :invalid="!!store.contactErrors.emails[i]"
                      class="flex-1 min-w-0"
                    />
                    <Button
                      icon="pi pi-times"
                      severity="secondary"
                      text
                      rounded
                      :aria-label="`Remove email ${i + 1}`"
                      @click="store.contact.emails.splice(i, 1)"
                    />
                  </div>
                </div>
                <p v-if="store.contactErrors.emails[i]" class="text-xs text-red-500">{{ store.contactErrors.emails[i] }}</p>
              </div>
              <Button
                label="Add email"
                icon="pi pi-plus"
                size="small"
                severity="secondary"
                text
                class="self-start"
                :disabled="store.contact.emails.length >= MAX_EMAILS"
                @click="store.contact.emails.push({ type: 'work', address: '' })"
              />
            </div>

            <div class="flex flex-col gap-1">
              <label for="contact-website" class="text-sm font-medium text-surface-700 dark:text-surface-300">Website</label>
              <InputText
                id="contact-website"
                v-model="store.contact.website"
                type="url"
                maxlength="2048"
                placeholder="https://example.com"
                :invalid="!!store.contactErrors.website"
                class="w-full"
              />
              <p v-if="store.contactErrors.website" class="text-xs text-red-500">{{ store.contactErrors.website }}</p>
            </div>
          </div>
        </AccordionContent>
      </AccordionPanel>

      <!-- Address -->
      <AccordionPanel value="address">
        <AccordionHeader>Address</AccordionHeader>
        <AccordionContent>
          <div class="flex flex-col gap-3">
            <div class="flex flex-col gap-1">
              <label for="contact-address-type" class="text-sm font-medium text-surface-700 dark:text-surface-300">Type</label>
              <Select
                v-model="store.contact.address.type"
                input-id="contact-address-type"
                :options="addressTypes"
                option-label="label"
                option-value="value"
                class="w-28"
              />
            </div>
            <div class="flex flex-col gap-1">
              <label for="contact-street" class="text-sm font-medium text-surface-700 dark:text-surface-300">Street</label>
              <InputText id="contact-street" v-model="store.contact.address.street" maxlength="255" class="w-full" />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div class="flex flex-col gap-1">
                <label for="contact-city" class="text-sm font-medium text-surface-700 dark:text-surface-300">City</label>
                <InputText id="contact-city" v-model="store.contact.address.city" maxlength="100" class="w-full" />
              </div>
              <div class="flex flex-col gap-1">
                <label for="contact-region" class="text-sm font-medium text-surface-700 dark:text-surface-300">State / region</label>
                <InputText id="contact-region" v-model="store.contact.address.region" maxlength="100" class="w-full" />
              </div>
              <div class="flex flex-col gap-1">
                <label for="contact-postal-code" class="text-sm font-medium text-surface-700 dark:text-surface-300">Postal code</label>
                <InputText id="contact-postal-code" v-model="store.contact.address.postal_code" maxlength="20" class="w-full" />
              </div>
              <div class="flex flex-col gap-1">
                <label for="contact-country" class="text-sm font-medium text-surface-700 dark:text-surface-300">Country</label>
                <InputText id="contact-country" v-model="store.contact.address.country" maxlength="100" class="w-full" />
              </div>
            </div>
          </div>
        </AccordionContent>
      </AccordionPanel>

      <!-- Other -->
      <AccordionPanel value="other">
        <AccordionHeader>Other</AccordionHeader>
        <AccordionContent>
          <div class="flex flex-col gap-3">
            <div class="flex flex-col gap-1">
              <label for="contact-birthday" class="text-sm font-medium text-surface-700 dark:text-surface-300">Birthday</label>
              <InputText id="contact-birthday" v-model="store.contact.birthday" type="date" class="w-full" />
            </div>
            <div class="flex flex-col gap-1">
              <label for="contact-note" class="text-sm font-medium text-surface-700 dark:text-surface-300">Note</label>
              <Textarea id="contact-note" v-model="store.contact.note" rows="3" maxlength="500" auto-resize class="w-full" />
              <p class="text-xs text-surface-400">{{ store.contact.note?.length ?? 0 }} / 500 characters</p>
            </div>
          </div>
        </AccordionContent>
      </AccordionPanel>

      <!-- Contact page: only dynamic codes have one -->
      <AccordionPanel v-if="store.qrType === 'DYNAMIC'" value="page">
        <AccordionHeader>Contact page</AccordionHeader>
        <AccordionContent>
          <div class="flex flex-col gap-4">
            <div class="flex flex-col gap-2">
              <span class="text-sm font-medium text-surface-700 dark:text-surface-300">Photo</span>
              <template v-if="store.contact.photo_url">
                <div class="flex items-center gap-3">
                  <img :src="store.contact.photo_url" alt="Contact photo" class="h-16 w-16 rounded-full object-cover" />
                  <Button label="Remove photo" severity="danger" text size="small" @click="store.contact.photo_url = null" />
                </div>
              </template>
              <template v-else-if="store.currentQRCode">
                <FileUpload
                  mode="basic"
                  accept="image/png,image/jpeg,image/webp"
                  :max-file-size="MAX_PHOTO_BYTES"
                  choose-label="Upload photo"
                  :auto="true"
                  :disabled="photoUploading"
                  @select="handlePhotoSelect"
                />
                <p class="text-xs text-surface-400">PNG, JPEG, or WebP · max 5 MB. Location data is removed.</p>
              </template>
              <p v-else class="text-xs text-surface-400">Save the code first, then add a photo.</p>
              <p v-if="photoError" class="text-xs text-red-500">{{ photoError }}</p>
            </div>

            <div class="flex flex-col gap-1">
              <label for="contact-theme-color" class="text-sm font-medium text-surface-700 dark:text-surface-300">Theme color</label>
              <div class="flex items-center gap-3">
                <input
                  id="contact-theme-color"
                  type="color"
                  :value="store.contact.theme_color ?? DEFAULT_THEME_COLOR"
                  class="h-10 w-14 cursor-pointer rounded"
                  @input="store.contact.theme_color = ($event.target as HTMLInputElement).value"
                />
                <Button
                  v-if="store.contact.theme_color"
                  label="Use default"
                  severity="secondary"
                  text
                  size="small"
                  @click="store.contact.theme_color = null"
                />
              </div>
            </div>

            <div class="flex flex-col gap-2">
              <span class="text-sm font-medium text-surface-700 dark:text-surface-300">Social links</span>
              <div v-for="(link, i) in store.contact.social_links" :key="i" class="flex flex-col gap-1">
                <div class="flex flex-wrap gap-2">
                  <InputText
                    v-model="link.label"
                    maxlength="50"
                    placeholder="LinkedIn"
                    :aria-label="`Link ${i + 1} label`"
                    class="w-32 flex-shrink-0"
                  />
                  <div class="flex flex-1 min-w-48 gap-2">
                    <InputText
                      v-model="link.url"
                      type="url"
                      maxlength="2048"
                      placeholder="https://"
                      :aria-label="`Link ${i + 1} URL`"
                      :invalid="!!store.contactErrors.socialLinks[i]"
                      class="flex-1 min-w-0"
                    />
                    <Button
                      icon="pi pi-times"
                      severity="secondary"
                      text
                      :aria-label="`Remove link ${i + 1}`"
                      @click="store.contact.social_links.splice(i, 1)"
                    />
                  </div>
                </div>
                <p v-if="store.contactErrors.socialLinks[i]" class="text-xs text-red-500">{{ store.contactErrors.socialLinks[i] }}</p>
              </div>
              <Button
                label="Add link"
                icon="pi pi-plus"
                size="small"
                severity="secondary"
                text
                class="self-start"
                :disabled="store.contact.social_links.length >= MAX_SOCIAL_LINKS"
                @click="store.contact.social_links.push({ label: '', url: '' })"
              />
            </div>
          </div>
        </AccordionContent>
      </AccordionPanel>
    </Accordion>

    <a
      v-if="hostedPageUrl"
      :href="hostedPageUrl"
      target="_blank"
      rel="noopener"
      class="self-start text-sm text-primary-600 dark:text-primary-400 underline"
    >
      Open contact page
    </a>

    <!-- MECARD is only an option when the payload lives in the code itself -->
    <div v-if="store.qrType === 'STATIC'" class="flex flex-col gap-1">
      <div class="flex items-center justify-between gap-3">
        <label for="contact-compact" class="text-sm font-medium text-surface-700 dark:text-surface-300">Compact format (MECARD)</label>
        <ToggleSwitch v-model="useMecard" input-id="contact-compact" />
      </div>
      <p class="text-xs text-surface-400">
        Makes a less dense code, but leaves out the job title, name prefix and suffix, and phone and email types.
      </p>
    </div>

    <Button
      label="Download .vcf"
      icon="pi pi-id-card"
      size="small"
      severity="secondary"
      outlined
      class="self-start"
      :disabled="!canDownload"
      title="Save the contact file to check it on your own phone"
      @click="downloadVcf"
    />
  </div>
</template>

<style scoped>
/* The accordion content is a grid, so without this a row's natural width stretches it past the panel */
:deep(.p-accordioncontent-wrapper) {
  min-width: 0;
}
</style>
