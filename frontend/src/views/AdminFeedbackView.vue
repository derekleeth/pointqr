<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { feedbackApi } from '@/api/feedback'
import type { FeedbackAdminItem, FeedbackStatus } from '@/api/feedback'
import { useToast } from 'primevue/usetoast'

const toast = useToast()

const items = ref<FeedbackAdminItem[]>([])
const loading = ref(true)
const searchQuery = ref('')
const typeFilter = ref<string | null>(null)
const statusFilter = ref<string | null>(null)

// Detail dialog
const selectedItem = ref<FeedbackAdminItem | null>(null)
const showDetailDialog = ref(false)
const editNotes = ref('')
const editStatus = ref<FeedbackStatus>('open')
const saving = ref(false)

// Delete dialog
const confirmDeleteId = ref<string | null>(null)
const showDeleteDialog = computed({
  get: () => confirmDeleteId.value !== null,
  set: (val: boolean) => {
    if (!val) confirmDeleteId.value = null
  },
})

const typeOptions = [
  { label: 'All Types', value: null },
  { label: '🐛 Bug', value: 'bug' },
  { label: '💡 Feature Request', value: 'feature_request' },
  { label: '💬 Feedback', value: 'feedback' },
  { label: '❓ Question', value: 'question' },
]

const statusOptions = [
  { label: 'All Statuses', value: null },
  { label: 'Open', value: 'open' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Resolved', value: 'resolved' },
  { label: 'Closed', value: 'closed' },
]

const statusUpdateOptions = [
  { label: 'Open', value: 'open' as FeedbackStatus },
  { label: 'In Progress', value: 'in_progress' as FeedbackStatus },
  { label: 'Resolved', value: 'resolved' as FeedbackStatus },
  { label: 'Closed', value: 'closed' as FeedbackStatus },
]

const filteredItems = computed(() => {
  let result = items.value
  const q = searchQuery.value.toLowerCase()
  if (q) {
    result = result.filter(
      (item) =>
        item.subject.toLowerCase().includes(q) ||
        item.message.toLowerCase().includes(q) ||
        item.user_email.toLowerCase().includes(q),
    )
  }
  if (typeFilter.value) {
    result = result.filter((item) => item.type === typeFilter.value)
  }
  if (statusFilter.value) {
    result = result.filter((item) => item.status === statusFilter.value)
  }
  return result
})

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

function truncate(text: string, len = 60) {
  return text.length > len ? text.slice(0, len) + '…' : text
}

// ---------------------------------------------------------------------------
// API actions
// ---------------------------------------------------------------------------

async function loadItems() {
  loading.value = true
  try {
    items.value = await feedbackApi.adminList()
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load feedback submissions',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

function openDetail(item: FeedbackAdminItem) {
  selectedItem.value = item
  editNotes.value = item.admin_notes ?? ''
  editStatus.value = item.status
  showDetailDialog.value = true
}

async function saveDetail() {
  if (!selectedItem.value) return
  saving.value = true
  try {
    const updated = await feedbackApi.adminUpdate(selectedItem.value.id, {
      status: editStatus.value,
      admin_notes: editNotes.value || null,
    })
    // Update in-place
    const idx = items.value.findIndex((i) => i.id === updated.id)
    if (idx !== -1) items.value[idx] = updated
    selectedItem.value = updated
    showDetailDialog.value = false
    toast.add({
      severity: 'success',
      summary: 'Updated',
      detail: 'Feedback status updated',
      life: 2500,
    })
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err?.response?.data?.detail ?? 'Failed to update feedback',
      life: 3500,
    })
  } finally {
    saving.value = false
  }
}

function confirmDelete(id: string) {
  confirmDeleteId.value = id
}

async function deleteItem() {
  const id = confirmDeleteId.value
  if (!id) return
  try {
    await feedbackApi.adminDelete(id)
    items.value = items.value.filter((i) => i.id !== id)
    // Close detail dialog if viewing this item
    if (selectedItem.value?.id === id) showDetailDialog.value = false
    toast.add({
      severity: 'warn',
      summary: 'Deleted',
      detail: 'Feedback submission deleted',
      life: 2500,
    })
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err?.response?.data?.detail ?? 'Failed to delete',
      life: 3500,
    })
  } finally {
    confirmDeleteId.value = null
  }
}

onMounted(loadItems)
</script>

<template>
  <div class="admin-feedback-view">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Feedback & Issues</h1>
        <p class="page-subtitle">
          {{ items.length }} total submissions ·
          {{ items.filter((i) => i.status === 'open').length }} open
        </p>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <IconField iconPosition="left" class="search-field">
        <InputIcon class="pi pi-search" />
        <InputText
          v-model="searchQuery"
          placeholder="Search feedback…"
          size="small"
        />
      </IconField>

      <Select
        v-model="typeFilter"
        :options="typeOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="All Types"
        size="small"
        class="filter-select"
      />

      <Select
        v-model="statusFilter"
        :options="statusOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="All Statuses"
        size="small"
        class="filter-select"
      />
    </div>

    <!-- Table -->
    <div class="table-card">
      <DataTable
        :value="filteredItems"
        :loading="loading"
        stripedRows
        scrollable
        scrollHeight="flex"
        size="small"
        :rows="20"
        :paginator="filteredItems.length > 20"
        class="feedback-table"
      >
        <Column field="type" header="Type" sortable style="width: 140px">
          <template #body="{ data }">
            <Tag
              :value="formatType(data.type)"
              :severity="typeSeverity(data.type)"
              class="capitalize text-xs"
            />
          </template>
        </Column>

        <Column field="subject" header="Subject" sortable style="min-width: 200px">
          <template #body="{ data }">
            <button
              class="subject-link"
              @click="openDetail(data)"
              :title="data.subject"
            >
              {{ truncate(data.subject, 50) }}
            </button>
          </template>
        </Column>

        <Column field="user_email" header="User" sortable style="min-width: 180px">
          <template #body="{ data }">
            <div class="user-cell">
              <div class="avatar-sm">
                {{ data.user_email[0].toUpperCase() }}
              </div>
              <span class="user-email-text">{{ data.user_email }}</span>
            </div>
          </template>
        </Column>

        <Column field="status" header="Status" sortable style="width: 120px">
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
              v-tooltip="'Open GitHub issue #' + data.github_issue_number"
              class="github-link"
            >
              <i class="pi pi-github" />
              <span class="issue-num">#{{ data.github_issue_number }}</span>
            </a>
            <span v-else class="text-muted">—</span>
          </template>
        </Column>

        <Column header="Slack" style="width: 60px">
          <template #body="{ data }">
            <i
              v-if="data.slack_notified"
              class="pi pi-check-circle"
              style="color: var(--p-green-500)"
              v-tooltip="'Slack notification sent'"
            />
            <span v-else class="text-muted">—</span>
          </template>
        </Column>

        <Column
          field="created_at"
          header="Date"
          sortable
          style="width: 160px"
        >
          <template #body="{ data }">
            <span class="date-text">{{ formatDate(data.created_at) }}</span>
          </template>
        </Column>

        <Column header="Actions" style="width: 100px">
          <template #body="{ data }">
            <div class="action-btns">
              <Button
                icon="pi pi-eye"
                severity="info"
                size="small"
                text
                rounded
                title="View details"
                @click="openDetail(data)"
              />
              <Button
                icon="pi pi-trash"
                severity="danger"
                size="small"
                text
                rounded
                title="Delete"
                @click="confirmDelete(data.id)"
              />
            </div>
          </template>
        </Column>

        <template #empty>
          <div class="empty-state">
            <i class="pi pi-inbox empty-icon" />
            <p>No feedback submissions found</p>
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Detail Dialog -->
    <Dialog
      v-model:visible="showDetailDialog"
      header="Feedback Details"
      modal
      :style="{ width: '600px' }"
    >
      <div v-if="selectedItem" class="detail-content">
        <!-- Meta row -->
        <div class="meta-row">
          <Tag
            :value="formatType(selectedItem.type)"
            :severity="typeSeverity(selectedItem.type)"
            class="capitalize"
          />
          <Tag
            :value="selectedItem.status.replace(/_/g, ' ')"
            :severity="statusSeverity(selectedItem.status)"
            class="capitalize"
          />
          <span class="meta-date">{{ formatDate(selectedItem.created_at) }}</span>
        </div>

        <!-- From -->
        <div class="detail-field">
          <label>From</label>
          <p>{{ selectedItem.user_email }}</p>
        </div>

        <!-- Subject -->
        <div class="detail-field">
          <label>Subject</label>
          <p class="detail-subject">{{ selectedItem.subject }}</p>
        </div>

        <!-- Message -->
        <div class="detail-field">
          <label>Message</label>
          <div class="detail-message">{{ selectedItem.message }}</div>
        </div>

        <!-- GitHub Link -->
        <div v-if="selectedItem.github_issue_url" class="detail-field">
          <label>GitHub Issue</label>
          <a
            :href="selectedItem.github_issue_url"
            target="_blank"
            rel="noopener noreferrer"
            class="github-detail-link"
          >
            <i class="pi pi-github mr-1" />
            Issue #{{ selectedItem.github_issue_number }}
            <i class="pi pi-external-link ml-1 text-xs" />
          </a>
        </div>

        <!-- Slack -->
        <div class="detail-field">
          <label>Slack Notification</label>
          <p>
            <i
              :class="
                selectedItem.slack_notified
                  ? 'pi pi-check-circle'
                  : 'pi pi-minus-circle'
              "
              :style="{
                color: selectedItem.slack_notified
                  ? 'var(--p-green-500)'
                  : 'var(--text-muted)',
              }"
            />
            {{ selectedItem.slack_notified ? 'Sent' : 'Not sent' }}
          </p>
        </div>

        <hr class="detail-divider" />

        <!-- Status Update -->
        <div class="detail-field">
          <label>Update Status</label>
          <Select
            v-model="editStatus"
            :options="statusUpdateOptions"
            optionLabel="label"
            optionValue="value"
            fluid
          />
        </div>

        <!-- Admin Notes -->
        <div class="detail-field">
          <label>Admin Notes</label>
          <Textarea
            v-model="editNotes"
            placeholder="Internal notes (not visible to the user)…"
            :rows="3"
            fluid
            autoResize
          />
        </div>
      </div>

      <template #footer>
        <Button
          label="Cancel"
          severity="secondary"
          text
          @click="showDetailDialog = false"
        />
        <Button
          label="Save Changes"
          icon="pi pi-check"
          :loading="saving"
          @click="saveDetail"
        />
      </template>
    </Dialog>

    <!-- Delete Dialog -->
    <Dialog
      v-model:visible="showDeleteDialog"
      header="Delete Submission"
      modal
      :style="{ width: '360px' }"
    >
      <p>
        Are you sure you want to permanently delete this feedback submission?
      </p>
      <p class="delete-warning">This action cannot be undone.</p>
      <template #footer>
        <Button
          label="Cancel"
          severity="secondary"
          text
          @click="confirmDeleteId = null"
        />
        <Button
          label="Delete"
          severity="danger"
          icon="pi pi-trash"
          @click="deleteItem"
        />
      </template>
    </Dialog>

    <Toast />
  </div>
</template>

<style scoped>
.admin-feedback-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1.5rem;
  gap: 1rem;
  overflow: hidden;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.page-title {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.search-field {
  width: 260px;
}

.filter-select {
  width: 160px;
}

.table-card {
  flex: 1;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg-card);
}

.feedback-table {
  height: 100%;
}

/* Subject link */
.subject-link {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: left;
  padding: 0;
  text-decoration: none;
}
.subject-link:hover {
  text-decoration: underline;
}

/* User cell */
.user-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.avatar-sm {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 700;
  flex-shrink: 0;
}

.user-email-text {
  font-size: 0.8125rem;
  color: var(--text-primary);
}

/* GitHub link */
.github-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 0.8125rem;
}
.github-link:hover {
  text-decoration: underline;
}

.issue-num {
  font-weight: 600;
}

.text-muted {
  color: var(--text-muted);
}

.date-text {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.action-btns {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 3rem;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 2rem;
  opacity: 0.4;
}

/* Detail dialog */
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0.25rem 0;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.meta-date {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-left: auto;
}

.detail-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-field label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
}

.detail-field p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-primary);
}

.detail-subject {
  font-weight: 600;
}

.detail-message {
  font-size: 0.875rem;
  color: var(--text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
  padding: 0.75rem;
  border-radius: 8px;
  background: var(--bg-elevated);
  max-height: 200px;
  overflow-y: auto;
}

.github-detail-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
}
.github-detail-link:hover {
  text-decoration: underline;
}

.detail-divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 0.5rem 0;
}

.delete-warning {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}
</style>

