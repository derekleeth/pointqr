import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

export type Theme = 'dark' | 'light'

export const useThemeStore = defineStore('theme', () => {
  const STORAGE_KEY = 'pointqr-theme'

  // Default to dark; restore from localStorage if previously changed
  const theme = ref<Theme>(
    (localStorage.getItem(STORAGE_KEY) as Theme | null) ?? 'dark'
  )

  const isDark = ref(theme.value === 'dark')

  function applyTheme(t: Theme) {
    isDark.value = t === 'dark'
    if (t === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  function setTheme(t: Theme) {
    theme.value = t
  }

  // Apply immediately on store creation + on every change
  watch(theme, (t) => {
    localStorage.setItem(STORAGE_KEY, t)
    applyTheme(t)
  }, { immediate: true })

  return { theme, isDark, toggle, setTheme }
})
