<script setup lang="ts">
import { ref, computed } from 'vue'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
const copied = ref(false)
const apiCopied = ref(false)
const activeApiTab = ref('update')

const bashSnippet = `# 1. Clone the repository
git clone https://github.com/derekleeth/pointqr.git
cd pointqr

# 2. Configure environment
cp .env.example .env

# 3. Spin up all services with Docker Compose
docker compose up -d --build`

function copySnippet() {
  navigator.clipboard.writeText(bashSnippet)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2500)
}

const devFeatures = [
  {
    icon: 'pi pi-code',
    category: 'Developer & Automation',
    title: 'REST API & Webhook Automation',
    desc: 'Full REST API backend for automated code creation, on-the-fly destination swapping, asynchronous vector rendering, and analytics synchronization.',
    badge: 'API First',
  },
  {
    icon: 'pi pi-refresh',
    category: 'High Performance',
    title: 'Sub-15ms Dynamic Redirects',
    desc: 'Redirects are served from an in-process cache backed by indexed PostgreSQL queries, keeping scan-to-destination latency under 15ms.',
  },
  {
    icon: 'pi pi-palette',
    category: 'Design Engine',
    title: 'Live 50ms Design Canvas',
    desc: 'Sub-50ms debounced live preview across 6 dot patterns, corner styles, gradients, and embedded logos with automatic Level H error correction.',
  },
  {
    icon: 'pi pi-download',
    category: 'Multi-Format Output',
    title: 'Composited & Async Server Exports',
    desc: 'Instant client-side PNG/SVG with baked-in text labels, plus asynchronous Celery worker exports for print-ready PNG (300 DPI), SVG, PDF, and EPS vectors.',
  },
  {
    icon: 'pi pi-shield',
    category: 'Security & Hardening',
    title: 'API Rate Limiting & Protection',
    desc: 'Built-in slowapi sliding-window rate limiters protecting authentication, logo uploads, and heavy export endpoints against brute-force attacks and abuse.',
  },
  {
    icon: 'pi pi-server',
    category: 'Operations & DevOps',
    title: 'Live Telemetry & Site Admin',
    desc: 'Real-time WebSocket telemetry dashboard for Celery & RabbitMQ queues, plus instant runtime site toggles for public registration and email verification without restarts.',
  },
]

const apiTabs = [
  {
    id: 'update',
    label: 'Dynamic Redirect Updates',
    method: 'PATCH',
    methodClass: 'method-patch',
    lang: 'bash',
    headline: 'Update Destination URLs Instantly Without Reprinting',
    desc: 'Automate marketing campaigns, daily menu rotations, or emergency redirect failovers in sub-15ms with a single API call.',
    code: `# Update destination URL in real time — zero downtime, zero reprinting
curl -X PATCH "https://pointqr.app/api/v1/qrcodes/qr_7f8a92" \\
  -H "Authorization: Bearer $POINTQR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "target_url": "https://store.company.com/deals/autumn-sale"
  }'`,
  },
  {
    id: 'create',
    label: 'Mint Branded QR Codes',
    method: 'POST',
    methodClass: 'method-post',
    lang: 'python',
    headline: 'Generate Custom-Styled QR Codes from Webhooks',
    desc: 'Integrate directly into Stripe checkout, Eventbrite ticketing, or CRM workflows to generate branded QR codes with custom labels automatically.',
    code: `import requests

# Programmatically mint a QR code with custom colors & top/bottom labels
res = requests.post(
    "https://pointqr.app/api/v1/qrcodes",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "title": "VIP Ticket #9481",
        "type": "dynamic",
        "target_url": "https://event.com/ticket/9481",
        "design_config": {
            "dotsOptions": {"type": "rounded", "color": "#6366f1"},
            "labelTop": {"enabled": True, "text": "VIP ACCESS"},
            "labelBottom": {"enabled": True, "text": "BOOTH A-12"}
        }
    }
)
data = res.json()
print(f"Created: {data['id']} -> {data['short_code']}")`,
  },
  {
    id: 'export',
    label: 'Async Vector Exports',
    method: 'POST',
    methodClass: 'method-post',
    lang: 'bash',
    headline: 'Offload Print-Grade Vector Rendering to Background Workers',
    desc: 'Trigger async Celery rendering for 300 DPI PNG, pure SVG, PDF, or EPS vector assets without blocking API request threads.',
    code: `# Dispatch async vector rendering job to Celery worker queue
curl -X POST "https://pointqr.app/api/v1/qrcodes/qr_7f8a92/export/async?format=eps" \\
  -H "Authorization: Bearer $POINTQR_API_KEY"

# Returns 202 Accepted with tracking BatchJob ID:
# {"job_id": "job_e3b8a1", "status": "PENDING", "format": "eps"}`,
  },
  {
    id: 'analytics',
    label: 'Telemetry & Analytics Sync',
    method: 'GET',
    methodClass: 'method-get',
    lang: 'typescript',
    headline: 'Sync Scan Logs & Telemetry Directly into Your BI Stack',
    desc: 'Ingest scan counts, device category breakdowns, operating systems, and geolocation stats into Metabase, BigQuery, or Grafana.',
    code: `// Fetch aggregated scan performance and device breakdowns
const res = await fetch("https://pointqr.app/api/v1/analytics/summary", {
  headers: { Authorization: \`Bearer \${API_KEY}\` }
});
const { total_scans, unique_scans, by_device } = await res.json();

console.log(\`Total scans: \${total_scans} | Mobile share: \${by_device.mobile}%\`);`,
  },
]

const currentApiTab = computed(() => {
  return apiTabs.find(t => t.id === activeApiTab.value) || apiTabs[0]
})

function copyApiSnippet() {
  navigator.clipboard.writeText(currentApiTab.value.code)
  apiCopied.value = true
  setTimeout(() => {
    apiCopied.value = false
  }, 2500)
}

const automationUseCases = [
  {
    icon: 'pi pi-calendar',
    title: 'Dynamic Content Scheduling',
    desc: 'Use cron jobs or workflow engines (n8n, Zapier) to switch QR code destinations between morning/evening menus or active event stages.',
  },
  {
    icon: 'pi pi-ticket',
    title: 'Automated Event Ticketing',
    desc: 'Trigger API generation on checkout to create personalized attendee badges with attendee names and seat numbers composited into outer labels.',
  },
  {
    icon: 'pi pi-sync',
    title: 'CI/CD & Release Routing',
    desc: 'Automate QR destination routing during deployments to point testers and users to the latest release or blue/green staging environment.',
  },
  {
    icon: 'pi pi-print',
    title: 'Automated Print Pipelines',
    desc: 'Hook ERP or PIM product creations into asynchronous vector exports (EPS, PDF) to stream ready-to-print assets directly into RIP software.',
  },
  {
    icon: 'pi pi-chart-line',
    title: 'Data Warehouse Ingestion',
    desc: 'Extract time-series scan activity, device categories, and referrers into your analytics warehouse to measure offline campaign attribution.',
  },
  {
    icon: 'pi pi-shield',
    title: 'Incident Failover Routing',
    desc: 'Sub-15ms redirect engine allows instant emergency failover routing on billboards, packaging, or brochures during service disruptions.',
  },
]

const techStack = [
  {
    layer: 'Frontend SPA',
    tech: 'Vue 3 + Vite + PrimeVue 4',
    desc: 'Composition API, TypeScript, Tailwind CSS, Pinia store, and Chart.js telemetry visualization.',
    icon: 'pi pi-desktop',
  },
  {
    layer: 'Backend API',
    tech: 'FastAPI (Python 3.12+ async)',
    desc: 'High-throughput async ASGI engine with native OpenAPI Swagger docs and Pydantic v2 validation.',
    icon: 'pi pi-code',
  },
  {
    layer: 'Relational Database',
    tech: 'PostgreSQL 16 + Alembic',
    desc: 'ACID transactional persistence for users, QR designs, scan events, and schema migrations.',
    icon: 'pi pi-database',
  },
  {
    layer: 'Distributed Task Queue',
    tech: 'Celery 5 + RabbitMQ 3.13',
    desc: 'Dedicated queues for scan analytics, image rendering, and batch generation without blocking HTTP requests.',
    icon: 'pi pi-sync',
  },
  {
    layer: 'Scheduled Automation',
    tech: 'Celery Beat Daemon',
    desc: 'Periodic lifecycle cleanup sweeping expired export files (24h retention) and monitoring volume storage capacity.',
    icon: 'pi pi-clock',
  },
  {
    layer: 'Gateway & Reverse Proxy',
    tech: 'Nginx Alpine',
    desc: 'High-performance reverse proxy with SSL termination, HTTP/2 compression, and direct static storage volume serving.',
    icon: 'pi pi-shield',
  },
]
</script>

<template>
  <div class="home-page">
    <!-- ── Top Nav ───────────────────────────────── -->
    <header class="home-nav">
      <div class="nav-left">
        <RouterLink to="/" class="home-brand">
          <span class="brand-text">PointQR</span>
          <span class="brand-badge">v0.2.0</span>
        </RouterLink>
        <nav class="nav-menu" aria-label="Page sections">
          <RouterLink to="/" class="nav-link">Home</RouterLink>
          <a href="#dev-features" class="nav-link">Under the Hood</a>
          <a href="#automation" class="nav-link">REST API</a>
          <a href="#self-hosting" class="nav-link">Self-Hosting</a>
          <RouterLink :to="{ path: '/', hash: '#pricing' }" class="nav-link">Pricing</RouterLink>
        </nav>
      </div>

      <nav class="home-nav-links" aria-label="Account">
        <a
          href="https://github.com/derekleeth/pointqr"
          target="_blank"
          rel="noopener noreferrer"
          class="nav-icon-btn"
          title="Source code on GitHub"
          aria-label="Source code on GitHub"
        >
          <i class="pi pi-github" />
        </a>
        <button
          class="theme-toggle"
          @click="theme.toggle()"
          :title="theme.isDark ? 'Light mode' : 'Dark mode'"
          :aria-label="theme.isDark ? 'Light mode' : 'Dark mode'"
        >
          <i :class="theme.isDark ? 'pi pi-sun' : 'pi pi-moon'" />
        </button>
        <RouterLink to="/login" class="btn-ghost">Log in</RouterLink>
        <RouterLink to="/register" class="btn-primary">Get Started</RouterLink>
      </nav>
    </header>

    <main>
    <!-- ── Page Hero ─────────────────────────────── -->
    <section class="page-hero" aria-labelledby="dev-hero-title">
      <div class="hero-glow" />
      <div class="page-hero-content">
        <div class="hero-badge">
          <i class="pi pi-code" style="font-size:0.75rem" />
          <span>For Developers & Self-Hosters</span>
        </div>
        <h1 id="dev-hero-title" class="hero-title">
          Open Source,<br />
          <span class="text-gradient">API-First & Self-Hostable</span>
        </h1>
        <p class="hero-subtitle">
          Automate QR creation and redirects through a full REST API, or run the entire stack on your own
          hardware with Docker Compose. PointQR is 100% open source under the GNU GPL v3.
        </p>
        <div class="hero-cta">
          <a href="#automation" class="btn-primary btn-lg">
            <i class="pi pi-code" />
            Explore the API
          </a>
          <a href="#self-hosting" class="btn-ghost btn-lg">
            <i class="pi pi-server" />
            Self-Host Guide
          </a>
          <a
            href="https://github.com/derekleeth/pointqr"
            target="_blank"
            rel="noopener noreferrer"
            class="btn-ghost btn-lg"
          >
            <i class="pi pi-github" />
            GitHub
          </a>
        </div>

        <div class="hero-pills" style="justify-content:center">
          <span class="hero-pill"><i class="pi pi-bolt" /> &lt;15ms Redirect Latency</span>
          <span class="hero-pill"><i class="pi pi-code" /> OpenAPI 3.1 REST API</span>
          <span class="hero-pill"><i class="pi pi-server" /> 100% ARM64 & x86 Self-Hostable</span>
        </div>
      </div>
    </section>

    <!-- ── Technical Features Grid ───────────────── -->
    <section id="dev-features" class="features" aria-labelledby="dev-features-title">
      <div class="features-header">
        <p class="features-eyebrow">Under the Hood</p>
        <h2 id="dev-features-title" class="features-title">Built for speed, automation, and control</h2>
        <p class="features-subtitle">
          The engineering details behind the hosted cloud edition, all available when you run it yourself.
        </p>
      </div>

      <div class="features-grid">
        <div v-for="f in devFeatures" :key="f.title" class="feature-card">
          <div class="feature-top">
            <div class="feature-icon">
              <i :class="f.icon" />
            </div>
            <span v-if="f.badge" class="feature-badge">{{ f.badge }}</span>
          </div>
          <span class="feature-category">{{ f.category }}</span>
          <h3 class="feature-title">{{ f.title }}</h3>
          <p class="feature-desc">{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <!-- ── Developer & Automation Section ────────── -->
    <section id="automation" class="api-section" aria-labelledby="automation-title">
      <div class="api-header">
        <p class="features-eyebrow">Developer First & Scriptable</p>
        <h2 id="automation-title" class="api-title">Automate Everything Directly via REST API</h2>
        <p class="api-subtitle">
          Don't just use PointQR in the browser. Integrate dynamic QR creation, real-time destination swaps,
          asynchronous background vector exports, and scan analytics extraction straight into your backend
          services, CI/CD pipelines, CRMs, and webhooks.
        </p>
      </div>

      <!-- Interactive API Tabs & Code Showcase -->
      <div class="api-showcase-container">
        <!-- Tab selector buttons -->
        <div class="api-tabs-bar">
          <button
            v-for="tab in apiTabs"
            :key="tab.id"
            class="api-tab-btn"
            :class="{ active: activeApiTab === tab.id }"
            @click="activeApiTab = tab.id"
          >
            <span class="api-method-badge" :class="tab.methodClass">{{ tab.method }}</span>
            <span class="api-tab-label">{{ tab.label }}</span>
          </button>
        </div>

        <!-- Active tab code preview box -->
        <div class="api-code-card">
          <div class="api-code-header">
            <div class="api-code-info">
              <h3 class="api-headline">{{ currentApiTab.headline }}</h3>
              <p class="api-desc">{{ currentApiTab.desc }}</p>
            </div>
            <div class="api-code-actions">
              <span class="api-lang-tag">{{ currentApiTab.lang }}</span>
              <button class="terminal-copy-btn" @click="copyApiSnippet">
                <i :class="apiCopied ? 'pi pi-check' : 'pi pi-copy'" />
                <span>{{ apiCopied ? 'Copied!' : 'Copy Snippet' }}</span>
              </button>
            </div>
          </div>
          <pre class="api-code-block"><code>{{ currentApiTab.code }}</code></pre>
        </div>
      </div>

      <!-- Real-World Automation Possibilities Grid -->
      <div class="automation-usecases-wrap">
        <h3 class="usecases-headline">Real-World Automation Possibilities</h3>
        <div class="usecases-grid">
          <div v-for="uc in automationUseCases" :key="uc.title" class="usecase-card">
            <div class="usecase-icon-box">
              <i :class="uc.icon" />
            </div>
            <h4 class="usecase-title">{{ uc.title }}</h4>
            <p class="usecase-desc">{{ uc.desc }}</p>
          </div>
        </div>

        <!-- OpenAPI / Swagger Callout -->
        <div class="openapi-callout">
          <div class="openapi-left">
            <i class="pi pi-book openapi-icon" />
            <div>
              <h4 class="openapi-title">OpenAPI 3.1 & Interactive Swagger Documentation</h4>
              <p class="openapi-desc">
                Fully typed FastAPI schemas allow you to auto-generate SDK clients for Python, TypeScript,
                Go, Java, and C# using open-source generators.
              </p>
            </div>
          </div>
          <div class="openapi-actions">
            <a href="/api/docs" target="_blank" rel="noopener noreferrer" class="btn-primary">
              <i class="pi pi-external-link" />
              Explore Swagger UI
            </a>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Self-Hosting & Architecture ───────────── -->
    <section id="self-hosting" class="self-host-section" aria-labelledby="self-hosting-title">
      <div class="self-host-header">
        <p class="features-eyebrow">Data Sovereignty & Independence</p>
        <h2 id="self-hosting-title" class="self-host-title">Self-Host with Modern Infrastructure</h2>
        <p class="self-host-subtitle">
          PointQR is 100% open source under the GNU General Public License v3. Deploy on your local server, home lab, or any cloud VPS
          in minutes using standard Docker Compose. No telemetry, no feature gating, and unlimited dynamic QR codes.
        </p>
      </div>

      <!-- Quick start bash snippet -->
      <div class="terminal-container">
        <div class="terminal-bar">
          <div class="terminal-dots">
            <span class="dot dot-red" />
            <span class="dot dot-yellow" />
            <span class="dot dot-green" />
          </div>
          <span class="terminal-title">bash — Quick Start Self-Host</span>
          <button class="terminal-copy-btn" @click="copySnippet">
            <i :class="copied ? 'pi pi-check' : 'pi pi-copy'" />
            <span>{{ copied ? 'Copied!' : 'Copy Commands' }}</span>
          </button>
        </div>
        <pre class="terminal-code"><code>{{ bashSnippet }}</code></pre>
      </div>

      <!-- Tech Stack Breakdown -->
      <div class="architecture-wrap">
        <h3 class="arch-headline">Application Architecture & Components</h3>
        <div class="tech-grid">
          <div v-for="t in techStack" :key="t.tech" class="tech-card">
            <div class="tech-card-header">
              <i :class="t.icon" class="tech-icon" />
              <div>
                <span class="tech-layer">{{ t.layer }}</span>
                <h4 class="tech-name">{{ t.tech }}</h4>
              </div>
            </div>
            <p class="tech-desc">{{ t.desc }}</p>
          </div>
        </div>
      </div>

      <!-- Deployment & Hardware Specs Callout -->
      <div class="hardware-specs-grid">
        <div class="spec-card">
          <div class="spec-icon"><i class="pi pi-box" /></div>
          <h3>ARM64 & x86-64 Native</h3>
          <p>
            Fully multi-arch compatible. Run effortlessly on ARM VPS instances (Hetzner CAX, AWS Graviton,
            Oracle Ampere, Raspberry Pi) or traditional x86 servers (Hetzner CX, Netcup, Intel/AMD).
          </p>
        </div>
        <div class="spec-card">
          <div class="spec-icon"><i class="pi pi-sliders-v" /></div>
          <h3>Ultra-Lean Resource Footprint</h3>
          <p>
            Idle footprint of only ~600–800 MB RAM across all 5 core containers (FastAPI, Postgres, RabbitMQ,
            Celery, and Nginx). Runs smoothly on budget 4 GB VPS nodes under $6/mo.
          </p>
        </div>
        <div class="spec-card">
          <div class="spec-icon"><i class="pi pi-shield" /></div>
          <h3>Automated Storage Lifecycle</h3>
          <p>
            A dedicated Celery Beat scheduler automatically purges transient export files older than 24 hours
            and monitors volume disk utilization while safeguarding user assets in permanent storage.
          </p>
        </div>
      </div>
    </section>

    <!-- ── CTA Banner ─────────────────────────────── -->
    <section class="cta-section">
      <div class="cta-card">
        <h2 class="cta-title">Ready to build with PointQR?</h2>
        <p class="cta-sub">
          Grab an API key from a free cloud account, or clone the repo and have your own instance running in minutes.
        </p>
        <div class="cta-buttons">
          <RouterLink to="/register" class="btn-primary btn-lg">
            Create Free Account →
          </RouterLink>
          <a
            href="https://github.com/derekleeth/pointqr"
            target="_blank"
            rel="noopener noreferrer"
            class="btn-ghost btn-lg"
          >
            <i class="pi pi-github" />
            Star on GitHub
          </a>
        </div>
      </div>
    </section>
    </main>

    <!-- ── Footer ────────────────────────────────── -->
    <footer class="home-footer">
      <div class="footer-content">
        <div class="footer-left">
          <span class="footer-brand">PointQR</span>
          <span class="footer-copy">© {{ new Date().getFullYear() }} PointQR. Open source under the GNU GPL v3.</span>
        </div>
        <nav class="footer-links" aria-label="Footer">
          <RouterLink to="/">Home</RouterLink>
          <a href="#automation">REST API</a>
          <a href="#self-hosting">Self-Hosting</a>
          <RouterLink :to="{ path: '/', hash: '#pricing' }">Pricing</RouterLink>
          <a href="https://github.com/derekleeth/pointqr" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a href="/api/docs" target="_blank" rel="noopener noreferrer">Swagger API</a>
          <RouterLink to="/login">Login</RouterLink>
          <RouterLink to="/register">Register</RouterLink>
        </nav>
      </div>
    </footer>
  </div>
</template>

<style scoped src="@/assets/public-site.css"></style>
