import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'
import 'primeicons/primeicons.css'
import './assets/main.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      // Same selector used by our theme store and tailwind.config.js
      darkModeSelector: '.dark',
      cssLayer: false,
    },
  },
})
app.use(ToastService)
app.use(ConfirmationService)
app.directive('tooltip', Tooltip)

// Apply theme immediately so .dark class is set before first paint (no FOUC)
import { useThemeStore } from './stores/theme'
useThemeStore() // watch({ immediate: true }) fires during store creation

// Restore auth state from localStorage before mounting so that user.role is
// available when the router's beforeEach guard runs on the initial navigation.
// Without the await, user.value is still null when the guard checks requiresAdmin,
// causing an erroneous redirect to /dashboard on hard refresh.
import { useAuthStore } from './stores/auth'
;(async () => {
  await useAuthStore().initialize()
  app.mount('#app')
})()

