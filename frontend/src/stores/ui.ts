import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useUIStore = defineStore('ui', () => {
  const SIDEBAR_KEY = 'pointqr-sidebar'

  // Restore collapsed state from localStorage
  const sidebarCollapsed = ref(localStorage.getItem(SIDEBAR_KEY) === 'true')

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem(SIDEBAR_KEY, String(sidebarCollapsed.value))
  }

  function setSidebarCollapsed(v: boolean) {
    sidebarCollapsed.value = v
    localStorage.setItem(SIDEBAR_KEY, String(v))
  }

  return { sidebarCollapsed, toggleSidebar, setSidebarCollapsed }
})

