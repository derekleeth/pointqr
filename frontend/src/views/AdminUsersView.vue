<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { adminApi, type AdminUser } from '@/api/admin'
import { useToast } from 'primevue/usetoast'

const toast = useToast()

const users = ref<AdminUser[]>([])
const loading = ref(true)
const searchQuery = ref('')

// Create user dialog
const showCreateDialog = ref(false)
const creating = ref(false)
const newUser = ref({ email: '', password: '', role: 'user', tier: 'free' })

// Delete confirm dialog
const confirmDeleteId = ref<string | null>(null)
const showDeleteDialog = computed({
  get: () => confirmDeleteId.value !== null,
  set: (val: boolean) => { if (!val) confirmDeleteId.value = null },
})

const filteredUsers = computed(() => {
  const q = searchQuery.value.toLowerCase()
  if (!q) return users.value
  return users.value.filter(
    (u) => u.email.toLowerCase().includes(q) || u.role.includes(q) || u.tier.includes(q),
  )
})

async function loadUsers() {
  loading.value = true
  try {
    users.value = await adminApi.listUsers()
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load users', life: 3000 })
  } finally {
    loading.value = false
  }
}

async function handleRoleChange(user: AdminUser, newRole: string) {
  const original = user.role
  user.role = newRole as 'admin' | 'user'
  try {
    const updated = await adminApi.updateRole(user.id, newRole)
    Object.assign(user, updated)
    toast.add({ severity: 'success', summary: 'Updated', detail: `${user.email} is now ${newRole}`, life: 2500 })
  } catch (err: any) {
    user.role = original
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err?.response?.data?.detail ?? 'Failed to update role',
      life: 3500,
    })
  }
}

async function handleTierChange(user: AdminUser, newTier: string) {
  const original = user.tier
  user.tier = newTier as 'free' | 'pro' | 'enterprise'
  try {
    const updated = await adminApi.updateTier(user.id, newTier)
    Object.assign(user, updated)
    toast.add({ severity: 'success', summary: 'Updated', detail: `Tier changed to ${newTier}`, life: 2500 })
  } catch (err: any) {
    user.tier = original
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err?.response?.data?.detail ?? 'Failed to update tier',
      life: 3500,
    })
  }
}

async function toggleStatus(user: AdminUser) {
  const original = user.is_active
  user.is_active = !user.is_active
  try {
    const updated = await adminApi.updateStatus(user.id, user.is_active)
    Object.assign(user, updated)
    toast.add({
      severity: 'info',
      summary: user.is_active ? 'Enabled' : 'Disabled',
      detail: `${user.email} has been ${user.is_active ? 'enabled' : 'disabled'}`,
      life: 2500,
    })
  } catch (err: any) {
    user.is_active = original
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err?.response?.data?.detail ?? 'Failed to update status',
      life: 3500,
    })
  }
}

function confirmDelete(userId: string) {
  confirmDeleteId.value = userId
}

async function deleteUser() {
  const id = confirmDeleteId.value
  if (!id) return
  try {
    await adminApi.deleteUser(id)
    users.value = users.value.filter((u) => u.id !== id)
    toast.add({ severity: 'warn', summary: 'Deleted', detail: 'User has been deleted', life: 2500 })
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err?.response?.data?.detail ?? 'Failed to delete user',
      life: 3500,
    })
  } finally {
    confirmDeleteId.value = null
  }
}

async function createUser() {
  creating.value = true
  try {
    const created = await adminApi.createUser(newUser.value)
    users.value.unshift({ ...created, qr_code_count: 0, total_scans: 0 })
    showCreateDialog.value = false
    newUser.value = { email: '', password: '', role: 'user', tier: 'free' }
    toast.add({ severity: 'success', summary: 'Created', detail: `${created.email} added`, life: 2500 })
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err?.response?.data?.detail ?? 'Failed to create user',
      life: 3500,
    })
  } finally {
    creating.value = false
  }
}

onMounted(loadUsers)
</script>

<template>
  <div class="admin-users-view">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">User Management</h1>
        <p class="page-subtitle">{{ users.length }} registered users</p>
      </div>
      <Button
        label="New User"
        icon="pi pi-user-plus"
        size="small"
        @click="showCreateDialog = true"
      />
    </div>

    <!-- Search -->
    <div class="toolbar">
      <IconField iconPosition="left" class="search-field">
        <InputIcon class="pi pi-search" />
        <InputText v-model="searchQuery" placeholder="Search users…" size="small" />
      </IconField>
    </div>

    <!-- Table -->
    <div class="table-card">
      <DataTable
        :value="filteredUsers"
        :loading="loading"
        stripedRows
        scrollable
        scrollHeight="flex"
        size="small"
        class="users-table"
      >
        <Column field="email" header="Email" sortable style="min-width: 220px">
          <template #body="{ data }">
            <div class="user-cell">
              <div class="avatar-sm">{{ data.email[0].toUpperCase() }}</div>
              <div>
                <p class="user-email">{{ data.email }}</p>
                <p class="user-date">Joined {{ new Date(data.created_at).toLocaleDateString() }}</p>
              </div>
            </div>
          </template>
        </Column>

        <Column field="role" header="Role" sortable style="width: 140px">
          <template #body="{ data }">
            <Select
              :model-value="data.role"
              :options="['admin', 'user']"
              size="small"
              class="full-select"
              @change="(e: any) => handleRoleChange(data, e.value)"
            />
          </template>
        </Column>

        <Column field="tier" header="Tier" sortable style="width: 160px">
          <template #body="{ data }">
            <Select
              :model-value="data.tier"
              :options="['free', 'pro', 'enterprise']"
              size="small"
              class="full-select"
              @change="(e: any) => handleTierChange(data, e.value)"
            />
          </template>
        </Column>

        <Column field="qr_code_count" header="QR Codes" sortable style="width: 110px">
          <template #body="{ data }">
            <Tag :value="String(data.qr_code_count)" severity="secondary" />
          </template>
        </Column>

        <Column field="total_scans" header="Total Scans" sortable style="width: 120px">
          <template #body="{ data }">
            <Tag :value="String(data.total_scans)" severity="info" />
          </template>
        </Column>

        <Column field="is_active" header="Status" style="width: 100px">
          <template #body="{ data }">
            <Tag
              :value="data.is_active ? 'Active' : 'Disabled'"
              :severity="data.is_active ? 'success' : 'danger'"
            />
          </template>
        </Column>

        <Column header="Actions" style="width: 120px">
          <template #body="{ data }">
            <div class="action-btns">
              <Button
                :icon="data.is_active ? 'pi pi-ban' : 'pi pi-check-circle'"
                :severity="data.is_active ? 'warn' : 'success'"
                size="small"
                text
                rounded
                :title="data.is_active ? 'Disable user' : 'Enable user'"
                @click="toggleStatus(data)"
              />
              <Button
                icon="pi pi-trash"
                severity="danger"
                size="small"
                text
                rounded
                title="Delete user"
                @click="confirmDelete(data.id)"
              />
            </div>
          </template>
        </Column>

        <template #empty>
          <div class="empty-state">
            <i class="pi pi-users empty-icon" />
            <p>No users found</p>
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Create User Dialog -->
    <Dialog
      v-model:visible="showCreateDialog"
      header="Create New User"
      modal
      :style="{ width: '420px' }"
    >
      <div class="dialog-form">
        <div class="form-field">
          <label>Email</label>
          <InputText v-model="newUser.email" type="email" placeholder="user@example.com" fluid />
        </div>
        <div class="form-field">
          <label>Password</label>
          <Password v-model="newUser.password" :feedback="false" toggleMask fluid />
        </div>
        <div class="form-row">
          <div class="form-field">
            <label>Role</label>
            <Select v-model="newUser.role" :options="['user', 'admin']" fluid />
          </div>
          <div class="form-field">
            <label>Tier</label>
            <Select v-model="newUser.tier" :options="['free', 'pro', 'enterprise']" fluid />
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" text @click="showCreateDialog = false" />
        <Button
          label="Create"
          icon="pi pi-user-plus"
          :loading="creating"
          :disabled="!newUser.email || !newUser.password"
          @click="createUser"
        />
      </template>
    </Dialog>

    <!-- Delete Confirm Dialog -->
    <Dialog
      v-model:visible="showDeleteDialog"
      header="Delete User"
      modal
      :style="{ width: '360px' }"
    >
      <p>Are you sure you want to permanently delete this user and all their data?</p>
      <p class="delete-warning">This action cannot be undone.</p>
      <template #footer>
        <Button label="Cancel" severity="secondary" text @click="confirmDeleteId = null" />
        <Button label="Delete" severity="danger" icon="pi pi-trash" @click="deleteUser" />
      </template>
    </Dialog>

    <Toast />
  </div>
</template>

<style scoped>
.admin-users-view {
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
}

.search-field {
  width: 280px;
}

.table-card {
  flex: 1;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg-card);
}

.users-table {
  height: 100%;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.avatar-sm {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.user-email {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0;
}

.user-date {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 0;
}

.full-select {
  width: 100%;
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

/* Dialog */
.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0.5rem 0;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-field label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.delete-warning {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}
</style>
