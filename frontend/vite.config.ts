import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { PrimeVueResolver } from '@primevue/auto-import-resolver'
import { fileURLToPath, URL } from 'node:url'

// Default hostnames allowed by Vite dev server when not configured in .env
const defaultAllowedHosts = [
  'localhost', // Allows localhost
  '.pointqr.com', // Allows the domain and all its subdomains
  'monkey-v-1', // Allows the specific hostname
  'all', // Allows any hostname on the local network (VM names, custom hostnames, etc.)
]

function parseAllowedHosts(raw?: string): string[] | true {
  if (!raw || !raw.trim()) {
    return defaultAllowedHosts
  }

  const trimmed = raw.trim().replace(/^["']|["']$/g, '')
  if (trimmed.toLowerCase() === 'true' || trimmed.toLowerCase() === 'all') {
    return true
  }

  return trimmed
    .split(',')
    .map((host) => host.trim().replace(/^["']|["']$/g, ''))
    .filter(Boolean)
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const rootDir = fileURLToPath(new URL('..', import.meta.url))
  const env = {
    ...loadEnv(mode, rootDir, ''),
    ...loadEnv(mode, process.cwd(), ''),
    ...process.env,
  }

  const allowedHosts = parseAllowedHosts(env.ALLOWED_HOSTS || env.VITE_ALLOWED_HOSTS)

  return {
    plugins: [
      vue(),
      // Auto-import PrimeVue components used in templates (no manual imports needed)
      Components({
        resolvers: [PrimeVueResolver()],
      }),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      // Allow any hostname on the local network (VM names, custom hostnames, etc.)
      // Vite 5+ blocks non-localhost hostnames by default as a DNS rebinding guard.
      allowedHosts,
      // Proxy API requests to FastAPI when running Vite outside Docker
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
    // Pre-bundle all PrimeVue component packages at startup so Vite never hits
    // a 504 "Outdated Optimize Dep" error when first navigating to a route that
    // uses a component not yet seen by the dev server.
    optimizeDeps: {
      include: [
        'chart.js',
        'chart.js/auto',
        'primevue/button',
        'primevue/inputtext',
        'primevue/password',
        'primevue/select',
        'primevue/selectbutton',
        'primevue/datatable',
        'primevue/column',
        'primevue/tag',
        'primevue/chart',
        'primevue/progressspinner',
        'primevue/progressbar',
        'primevue/dialog',
        'primevue/toast',
        'primevue/accordion',
        'primevue/accordionpanel',
        'primevue/accordionheader',
        'primevue/accordioncontent',
        'primevue/slider',
        'primevue/toggleswitch',
        'primevue/fileupload',
        'primevue/colorpicker',
        'primevue/tabs',
        'primevue/tablist',
        'primevue/tab',
        'primevue/tabpanels',
        'primevue/tabpanel',
      ],
    },
  }
})

