<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { feedbackApi } from '@/api/feedback'
import type { FeedbackType, FeedbackSubmission } from '@/api/feedback'
import { useToast } from 'primevue/usetoast'

const toast = useToast()

// ---------------------------------------------------------------------------
// Form state
// ---------------------------------------------------------------------------

const typeOptions = [
  { label: '🐛 Bug Report', value: 'bug' as FeedbackType },
  { label: '💡 Feature Request', value: 'feature_request' as FeedbackType },
  { label: '💬 General Feedback', value: 'feedback' as FeedbackType },
  { label: '❓ Question', value: 'question' as FeedbackType },
]

const selectedType = ref<FeedbackType | null>(null)
const subject = ref('')
const message = ref('')
const submitting = ref(false)
const submitted = ref(false)
const lastSubmission = ref<FeedbackSubmission | null>(null)

const charCount = computed(() => message.value.length)
const canSubmit = computed(
  () =>
    selectedType.value &&
    subject.value.trim().length >= 3 &&
    message.value.trim().length >= 10 &&
    !submitting.value,
)

async function handleSubmit() {
  if (!canSubmit.value || !selectedType.value) return

  submitting.value = true
  try {
    const result = await feedbackApi.submit({
      type: selectedType.value,
      subject: subject.value.trim(),
      message: message.value.trim(),
    })
    lastSubmission.value = result
    submitted.value = true
    toast.add({
      severity: 'success',
      summary: 'Submitted',
      detail: 'Your feedback has been sent. Thank you!',
      life: 4000,
    })
  } catch (err: any) {
    const detail =
      err?.response?.data?.detail ?? 'Failed to submit feedback. Please try again.'
    toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 })
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  selectedType.value = null
  subject.value = ''
  message.value = ''
  submitted.value = false
  lastSubmission.value = null
}

// ---------------------------------------------------------------------------
// Submission history
// ---------------------------------------------------------------------------

const history = ref<FeedbackSubmission[]>([])
const loadingHistory = ref(true)

async function loadHistory() {
  loadingHistory.value = true
  try {
    history.value = await feedbackApi.listOwn()
  } catch {
    /* silent */
  } finally {
    loadingHistory.value = false
  }
}

function statusSeverity(status: string) {
  switch (status) {
    case 'open':
      return 'info'
    case 'in_progress':
      return 'warn'
    case 'resolved':
      return 'success'
    case 'closed':
      return 'secondary'
    default:
      return 'info'
  }
}

function typeSeverity(type: string) {
  switch (type) {
    case 'bug':
      return 'danger'
    case 'feature_request':
      return 'info'
    case 'feedback':
      return 'secondary'
    case 'question':
      return 'warn'
    default:
      return 'secondary'
  }
}

function formatType(type: string) {
  return type.replace(/_/g, ' ')
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(loadHistory)
</script>

<template>
  <div class="flex flex-col gap-8 max-w-3xl">
    <!-- Header -->
    <div>
      <h1 class="text-3xl font-bold text-surface-900 dark:text-surface-0">Feedback</h1>
      <p class="text-surface-500 mt-1">
        Submit a bug report, feature request, question, or general feedback.
      </p>
    </div>

    <!-- Success State -->
    <div
      v-if="submitted && lastSubmission"
      class="rounded-xl border p-6 transition-colors duration-200"
      style="background-color: var(--bg-card); border-color: var(--border)"
    >
      <div class="text-center py-6">
        <i
          class="pi pi-check-circle text-5xl mb-4"
          style="color: var(--p-green-500)"
        />
        <h2 class="text-xl font-semibold text-surface-900 dark:text-surface-0 mb-2">
          Thank you for your feedback!
        </h2>
        <p class="text-sm mb-4" style="color: var(--text-secondary)">
          Your submission has been received and recorded.
        </p>

        <!-- GitHub Issue Link -->
        <div
          v-if="lastSubmission.github_issue_url"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-lg mb-4"
          style="background-color: var(--bg-elevated)"
        >
          <i class="pi pi-github" />
          <span class="text-sm">GitHub issue created: </span>
          <a
            :href="lastSubmission.github_issue_url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-sm font-medium underline"
            style="color: var(--color-primary)"
          >
            View on GitHub
          </a>
        </div>

        <div>
          <Button
            label="Submit Another"
            icon="pi pi-plus"
            severity="secondary"
            @click="resetForm(); loadHistory()"
          />
        </div>
      </div>
    </div>

    <!-- Submission Form -->
    <div
      v-else
      class="rounded-xl border p-6 transition-colors duration-200"
      style="background-color: var(--bg-card); border-color: var(--border)"
    >
      <div class="flex items-center gap-3 mb-6">
        <span
          class="flex items-center justify-center w-10 h-10 rounded-lg"
          style="background-color: var(--color-primary-soft)"
        >
          <i class="pi pi-send text-lg text-primary-500 dark:text-primary-400" />
        </span>
        <div>
          <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">
            Submit Feedback
          </h2>
          <p class="text-sm" style="color: var(--text-secondary)">
            Let us know how we can improve PointQR
          </p>
        </div>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-5">
        <!-- Type -->
        <div class="flex flex-col gap-1.5">
          <label
            for="feedback-type"
            class="text-sm font-medium text-surface-900 dark:text-surface-0"
          >
            Type <span class="text-red-500">*</span>
          </label>
          <Select
            id="feedback-type"
            v-model="selectedType"
            :options="typeOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Select a category"
            fluid
          />
        </div>

        <!-- Subject -->
        <div class="flex flex-col gap-1.5">
          <label
            for="feedback-subject"
            class="text-sm font-medium text-surface-900 dark:text-surface-0"
          >
            Subject <span class="text-red-500">*</span>
          </label>
          <InputText
            id="feedback-subject"
            v-model="subject"
            placeholder="Brief summary of your feedback"
            fluid
            :maxlength="255"
          />
          <small v-if="subject.length > 0 && subject.trim().length < 3" class="text-red-500">
            Subject must be at least 3 characters
          </small>
        </div>

        <!-- Message -->
        <div class="flex flex-col gap-1.5">
          <label
            for="feedback-message"
            class="text-sm font-medium text-surface-900 dark:text-surface-0"
          >
            Message <span class="text-red-500">*</span>
          </label>
          <Textarea
            id="feedback-message"
            v-model="message"
            placeholder="Describe your feedback in detail..."
            :rows="6"
            fluid
            :maxlength="5000"
            autoResize
          />
          <div class="flex justify-between">
            <small v-if="message.length > 0 && message.trim().length < 10" class="text-red-500">
              Message must be at least 10 characters
            </small>
            <small v-else />
            <small style="color: var(--text-muted)">{{ charCount }} / 5000</small>
          </div>
        </div>

        <!-- Hint -->
        <Message v-if="selectedType === 'bug' || selectedType === 'feature_request'" severity="info" :closable="false">
          <span class="text-sm">
            <i class="pi pi-github mr-1" />
            Bug reports and feature requests are automatically filed as GitHub issues.
          </span>
        </Message>

        <div class="pt-1">
          <Button
            type="submit"
            label="Submit Feedback"
            icon="pi pi-send"
            :loading="submitting"
            :disabled="!canSubmit"
          />
        </div>
      </form>
    </div>

    <!-- Submission History -->
    <div
      class="rounded-xl border p-6 transition-colors duration-200"
      style="background-color: var(--bg-card); border-color: var(--border)"
    >
      <div class="flex items-center gap-3 mb-5">
        <span
          class="flex items-center justify-center w-10 h-10 rounded-lg"
          style="background-color: var(--color-primary-soft)"
        >
          <i class="pi pi-history text-lg text-primary-500 dark:text-primary-400" />
        </span>
        <div>
          <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">
            Your Submissions
          </h2>
          <p class="text-sm" style="color: var(--text-secondary)">
            Track the status of your past feedback
          </p>
        </div>
      </div>

      <ProgressSpinner v-if="loadingHistory" style="width: 30px; height: 30px" />

      <div v-else-if="history.length === 0" class="text-center py-6">
        <i class="pi pi-inbox text-3xl mb-2" style="color: var(--text-muted)" />
        <p class="text-sm" style="color: var(--text-muted)">No submissions yet.</p>
      </div>

      <DataTable
        v-else
        :value="history"
        :rows="10"
        :paginator="history.length > 10"
        stripedRows
        size="small"
        class="text-sm"
      >
        <Column field="type" header="Type" :sortable="true" style="width: 130px">
          <template #body="{ data }">
            <Tag :value="formatType(data.type)" :severity="typeSeverity(data.type)" class="capitalize text-xs" />
          </template>
        </Column>
        <Column field="subject" header="Subject" :sortable="true" />
        <Column field="status" header="Status" :sortable="true" style="width: 120px">
          <template #body="{ data }">
            <Tag
              :value="data.status.replace(/_/g, ' ')"
              :severity="statusSeverity(data.status)"
              class="capitalize text-xs"
            />
          </template>
        </Column>
        <Column header="GitHub" style="width: 80px">
          <template #body="{ data }">
            <a
              v-if="data.github_issue_url"
              :href="data.github_issue_url"
              target="_blank"
              rel="noopener noreferrer"
              v-tooltip="'View GitHub Issue'"
              style="color: var(--color-primary)"
            >
              <i class="pi pi-external-link" />
            </a>
            <span v-else style="color: var(--text-muted)">—</span>
          </template>
        </Column>
        <Column field="created_at" header="Date" :sortable="true" style="width: 170px">
          <template #body="{ data }">
            <span style="color: var(--text-secondary)">{{ formatDate(data.created_at) }}</span>
          </template>
        </Column>
      </DataTable>
    </div>

    <Toast />
  </div>
</template>

