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

const printSheetFeatures = [
  {
    icon: 'pi pi-file',
    title: 'Standard Paper Formats',
    desc: 'Support for US Letter (8.5 × 11 in) and A4 (210 × 297 mm) with instant Portrait or Landscape orientation toggles.',
  },
  {
    icon: 'pi pi-th-large',
    title: 'Auto-Fit Grid Calculator',
    desc: 'Set custom QR sizes in millimetres or inches. The layout engine automatically calculates rows, columns, and total yield per sheet.',
  },
  {
    icon: 'pi pi-table',
    title: 'Precision Cut Guides',
    desc: 'Choose between professional corner Crop Marks or Dashed Lines for quick and effortless trimming with scissors or guillotines.',
  },
  {
    icon: 'pi pi-sliders-h',
    title: 'Custom Margins & Gutters',
    desc: 'Fine-tune page margins and spacing between QR codes to fit any printer hardware, label sheet, or custom cutter.',
  },
  {
    icon: 'pi pi-tag',
    title: 'Typography & Label Preservation',
    desc: 'Preserves top and bottom custom callout banners ("SCAN ME", WiFi details) and brand styling across every repeated tile.',
  },
  {
    icon: 'pi pi-bolt',
    title: 'Instant 300 DPI Client PDF',
    desc: 'Generated directly in your browser using jsPDF at crisp 300 DPI print quality — zero server queues, zero waiting.',
  },
]

const features = [
  {
    icon: 'pi pi-palette',
    category: 'Design & Customization',
    title: 'Live 50ms Design Canvas',
    desc: 'Sub-50ms debounced live preview. Customize 6 dot patterns, corner squares, corner dots, gradients, backgrounds, and embed logos with auto Level H error correction.',
  },
  {
    icon: 'pi pi-pencil',
    category: 'Branding & Typography',
    title: 'Custom Outer Text Labels',
    desc: 'Add independent top and bottom banner labels. Full typography controls: font family, size (8–48px), bold, italic, colors, text alignment, letter spacing, and padding.',
  },
  {
    icon: 'pi pi-print',
    category: 'Physical Distribution',
    title: 'Multi-Up Repeating Print Sheets',
    desc: 'Tile identical styled QR codes across US Letter or A4 sheets with auto-fit grid calculation, adjustable gutters, margins, and precision cut guides.',
    badge: 'Popular',
  },
  {
    icon: 'pi pi-refresh',
    category: 'High Performance',
    title: 'Dynamic QR & Sub-15ms Redirects',
    desc: 'Change destination URLs anytime without reprinting physical collateral. Sub-15ms redirection latency powered by in-process caching and indexed PostgreSQL queries.',
  },
  {
    icon: 'pi pi-code',
    category: 'Developer & Automation',
    title: 'REST API & Webhook Automation',
    desc: 'Full REST API backend for automated code creation, on-the-fly destination swapping, asynchronous vector rendering, and analytics synchronization.',
    badge: 'API First',
  },
  {
    icon: 'pi pi-chart-bar',
    category: 'Data & Intelligence',
    title: 'Comprehensive Scan Analytics',
    desc: 'Track scans over time with granular hourly, daily, and monthly bucketing. Segment scans by device category, operating system, browser, and country distribution.',
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

const activeScreenshot = ref('editor')

const screenshots = [
  {
    id: 'editor',
    icon: 'pi pi-palette',
    label: 'QR Code Editor',
    path: '/qrcodes/edit',
    src: '/screen-shot-edit-qr-code.png',
    alt: 'PointQR QR code editor with design controls on the left and a live preview of a branded dynamic QR code on the right',
    headline: 'Design with a Live, Real-Time Preview',
    desc: 'Tweak dot styles, corner shapes, backgrounds, logos, and text labels while the preview updates instantly. Download PNG/SVG or jump straight into a multi-up print sheet.',
    highlights: ['Collapsible design panels', 'Embedded logo sizing', 'Top & bottom text labels', 'One-click Print Sheet'],
  },
  {
    id: 'analytics',
    icon: 'pi pi-chart-bar',
    label: 'Scan Analytics',
    path: '/analytics',
    src: '/screen-shot-scan-analytics.png',
    alt: 'PointQR scan analytics dashboard showing total scans, unique visitors, a scans-over-time chart, and device, browser, and OS breakdowns',
    headline: 'See How Every Code Performs',
    desc: 'Summary cards, a scans-over-time chart with hourly, daily, or monthly bucketing, and device, browser, and OS breakdowns, filterable per QR code and date range.',
    highlights: ['Total & unique scans', 'Hour / Day / Month bucketing', 'Per-code filtering', 'Device, browser & OS charts'],
  },
  {
    id: 'map',
    icon: 'pi pi-map',
    label: 'Scan Map',
    path: '/analytics',
    src: '/screen-shot-scan-map.png',
    alt: 'PointQR scan map plotting scan locations worldwide, with by-country and by-city tables below',
    headline: 'Know Where Your Scans Happen',
    desc: 'Privacy-friendly GeoIP enrichment plots scans on an interactive world map, with sortable country and city tables showing share of total scans.',
    highlights: ['Interactive world map', 'Country & city rankings', 'Sortable scan share', 'No raw IPs stored'],
  },
]

const currentScreenshot = computed(() => {
  return screenshots.find(s => s.id === activeScreenshot.value) || screenshots[0]
})

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
          <a href="#print-sheets" class="nav-link">Print Sheets</a>
          <a href="#features" class="nav-link">Features</a>
          <a href="#automation" class="nav-link">API & Automation</a>
          <a href="#self-hosting" class="nav-link">Self-Hosting & Tech Stack</a>
          <a href="#pricing" class="nav-link">Pricing</a>
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
    <!-- ── Hero ──────────────────────────────────── -->
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero-glow" />
      <div class="hero-content">
        <div class="hero-badge">
          <i class="pi pi-sparkles" style="font-size:0.75rem" />
          <span>Multi-Up PDF Print Sheets & Full REST API Automation</span>
        </div>
        <h1 id="hero-title" class="hero-title">
          Dynamic QR Codes,<br />
          <span class="text-gradient">Engineered for Print & Scale</span>
        </h1>
        <p class="hero-subtitle">
          Design pixel-perfect static and dynamic QR codes with live 50ms previews,
          sub-15ms redirect latency, and privacy-first analytics. Tile multiple codes on
          printable PDF sheets with cut guides, or automate workflows directly via the REST API.
        </p>
        <div class="hero-cta">
          <RouterLink to="/register" class="btn-primary btn-lg">
            <i class="pi pi-user-plus" />
            Get Started Free
          </RouterLink>
          <a href="#automation" class="btn-ghost btn-lg">
            <i class="pi pi-code" />
            API & Automation
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

        <!-- Quick highlights pills -->
        <div class="hero-pills">
          <span class="hero-pill"><i class="pi pi-print" /> Multi-Up Print Sheets (300 DPI)</span>
          <span class="hero-pill"><i class="pi pi-bolt" /> &lt;15ms Redirect Latency</span>
          <span class="hero-pill"><i class="pi pi-code" /> Full REST API & Automation</span>
          <span class="hero-pill"><i class="pi pi-pencil" /> Custom Outer Labels</span>
          <span class="hero-pill"><i class="pi pi-server" /> 100% ARM64 & x86 Self-Hostable</span>
        </div>
      </div>

      <!-- Hero visual -->
      <div class="hero-visual">
        <div class="hero-visual-card">
          <img
            :src="theme.isDark ? '/PointQR-Light-v3.png' : '/PointQR-Dark-v2.png'"
            alt="PointQR logo – geometric pointer dog with a QR code"
            class="hero-logo"
            width="290"
            height="290"
            fetchpriority="high"
          />
          <div class="visual-badge">
            <span class="pulse-dot" />
            <span>Real-time Generator & Automation Engine</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Print Sheet Spotlight ─────────────────── -->
    <section id="print-sheets" class="spotlight-section" aria-labelledby="print-sheets-title">
      <div class="spotlight-header">
        <p class="features-eyebrow">The Missing Feature in Existing Tools</p>
        <h2 id="print-sheets-title" class="spotlight-title">Multi-Up Repeating PDF Print Sheet Generator</h2>
        <p class="spotlight-subtitle">
          Most QR tools only export an isolated image file, leaving you to manually copy and arrange dozens
          of codes in desktop publishing software. PointQR includes a first-class, client-side PDF print sheet
          engine that tiles your QR code across standard paper with precision cut guides.
        </p>
      </div>

      <div class="spotlight-container">
        <!-- Left: Feature points -->
        <div class="spotlight-features">
          <div v-for="item in printSheetFeatures" :key="item.title" class="spotlight-feature-item">
            <div class="spotlight-icon">
              <i :class="item.icon" />
            </div>
            <div>
              <h3 class="spotlight-item-title">{{ item.title }}</h3>
              <p class="spotlight-item-desc">{{ item.desc }}</p>
            </div>
          </div>
        </div>

        <!-- Right: Visual sheet mockup -->
        <div class="sheet-preview-wrapper">
          <div class="sheet-mockup">
            <div class="sheet-mockup-header">
              <div class="sheet-tag">US Letter (8.5 × 11 in)</div>
              <div class="sheet-tag">3 × 4 Grid (12 Codes)</div>
              <div class="sheet-tag sheet-tag-accent">300 DPI Print Quality</div>
            </div>

            <!-- Paper boundary -->
            <div class="sheet-paper">
              <div class="sheet-margin-guide">
                <!-- 3x4 grid representation -->
                <div class="sheet-grid-preview">
                  <div v-for="n in 12" :key="n" class="mini-qr-cell">
                    <span class="mini-crop-tl" />
                    <span class="mini-crop-tr" />
                    <span class="mini-crop-bl" />
                    <span class="mini-crop-br" />
                    <span class="mini-label-top">SCAN ME</span>
                    <div class="mini-qr-box">
                      <i class="pi pi-qrcode" />
                    </div>
                    <span class="mini-label-bot">pointqr.app</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="sheet-mockup-footer">
              <span><i class="pi pi-check-circle" /> Precision Crop Marks</span>
              <span><i class="pi pi-check-circle" /> Auto-Fit Margin Math</span>
              <span><i class="pi pi-check-circle" /> Zero Server Queuing</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── All Features Grid ─────────────────────── -->
    <section id="features" class="features" aria-labelledby="features-title">
      <div class="features-header">
        <p class="features-eyebrow">Comprehensive Feature Set</p>
        <h2 id="features-title" class="features-title">Everything you need to create, manage, and track QR codes</h2>
        <p class="features-subtitle">
          Designed for creators, developers, marketers, and homelabbers who need professional versatility and absolute control.
        </p>
      </div>

      <div class="features-grid">
        <div v-for="f in features" :key="f.title" class="feature-card">
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

    <!-- ── Product Tour / Screenshots ────────────── -->
    <section id="interface" class="tour-section" aria-labelledby="tour-title">
      <div class="tour-header">
        <p class="features-eyebrow">A Look Inside</p>
        <h2 id="tour-title" class="tour-title">A Clean, Focused Dashboard for Your QR Codes</h2>
        <p class="tour-subtitle">
          Sign in and everything is one click away: design and edit codes, watch scans roll in,
          and see where your audience is scanning from, all from a single sidebar.
        </p>
      </div>

      <div class="tour-container">
        <div class="tour-tabs" role="tablist" aria-label="Interface screenshots">
          <button
            v-for="shot in screenshots"
            :key="shot.id"
            role="tab"
            class="tour-tab-btn"
            :class="{ active: activeScreenshot === shot.id }"
            :aria-selected="activeScreenshot === shot.id"
            @click="activeScreenshot = shot.id"
          >
            <i :class="shot.icon" />
            <span>{{ shot.label }}</span>
          </button>
        </div>

        <div class="tour-frame">
          <div class="tour-frame-bar">
            <div class="terminal-dots">
              <span class="dot dot-red" />
              <span class="dot dot-yellow" />
              <span class="dot dot-green" />
            </div>
            <span class="tour-frame-url">
              <i class="pi pi-lock" />
              pointqr.app{{ currentScreenshot.path }}
            </span>
          </div>
          <img
            :key="currentScreenshot.id"
            :src="currentScreenshot.src"
            :alt="currentScreenshot.alt"
            class="tour-image"
            width="2560"
            height="1229"
            loading="lazy"
          />
        </div>

        <div class="tour-caption">
          <div>
            <h3 class="tour-caption-title">{{ currentScreenshot.headline }}</h3>
            <p class="tour-caption-desc">{{ currentScreenshot.desc }}</p>
          </div>
          <ul class="tour-highlights">
            <li v-for="h in currentScreenshot.highlights" :key="h">
              <i class="pi pi-check-circle" /> {{ h }}
            </li>
          </ul>
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
          PointQR is 100% open source under the MIT license. Deploy on your local server, home lab, or any cloud VPS
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

    <!-- ── Pricing / Comparison ──────────────────── -->
    <section id="pricing" class="pricing" aria-labelledby="pricing-title">
      <p class="features-eyebrow">Deployment Options</p>
      <h2 id="pricing-title" class="features-title">Choose How You Run PointQR</h2>
      <p class="pricing-subtitle">
        Use our hosted beta for quick experimentation, or deploy your own self-hosted instance with zero limitations.
      </p>

      <div class="pricing-cards-container">
        <!-- Hosted Beta Card -->
        <div class="pricing-card">
          <div class="pricing-badge">Hosted Beta</div>
          <h3 class="plan-title">Cloud Edition</h3>
          <p class="plan-desc">Great for quick testing and individual creators.</p>
          <div class="plan-price">
            <span class="price-val">Free</span>
            <span class="price-term">/ during beta</span>
          </div>
          <ul class="pricing-list">
            <li><i class="pi pi-check" /> <strong>3 Dynamic QR Codes</strong> (change URLs anytime)</li>
            <li><i class="pi pi-check" /> <strong>Unlimited Static QR Codes</strong></li>
            <li><i class="pi pi-check" /> <strong>200 Tracked Scans / month</strong></li>
            <li><i class="pi pi-check" /> Full Live Design Canvas & Typography Controls</li>
            <li><i class="pi pi-check" /> Multi-Up Repeating PDF Print Sheet Generator</li>
            <li><i class="pi pi-check" /> Instant Client PNG & SVG Composite Downloads</li>
            <li><i class="pi pi-check" /> Managed Cloud Hosting (Zero maintenance)</li>
          </ul>
          <RouterLink to="/register" class="btn-ghost w-full text-center justify-center">
            Get Started Free
          </RouterLink>
        </div>

        <!-- Self-Hosted Card -->
        <div class="pricing-card pricing-card-highlighted">
          <div class="pricing-badge badge-highlight">Recommended · Open Source</div>
          <h3 class="plan-title">Self-Hosted Community</h3>
          <p class="plan-desc">Total independence, unlimited scale, and complete data privacy.</p>
          <div class="plan-price">
            <span class="price-val">$0</span>
            <span class="price-term">/ forever (MIT License)</span>
          </div>
          <ul class="pricing-list">
            <li><i class="pi pi-check" /> <strong>Unlimited Dynamic QR Codes</strong></li>
            <li><i class="pi pi-check" /> <strong>Unlimited Static QR Codes</strong></li>
            <li><i class="pi pi-check" /> <strong>Unlimited Tracked Scans</strong> (No monthly quotas)</li>
            <li><i class="pi pi-check" /> <strong>Full REST API & Webhook Automation</strong></li>
            <li><i class="pi pi-check" /> <strong>100% Data Sovereignty</strong> (Data stays on your hardware)</li>
            <li><i class="pi pi-check" /> Multi-Up Repeating PDF Print Sheet Generator</li>
            <li><i class="pi pi-check" /> High-Res Background Vector Exports (PDF, EPS, SVG, PNG)</li>
            <li><i class="pi pi-check" /> Live WebSocket Celery & RabbitMQ Admin Telemetry</li>
            <li><i class="pi pi-check" /> Custom Domain, Custom SSL & Email Verification</li>
          </ul>
          <a
            href="https://github.com/derekleeth/pointqr"
            target="_blank"
            rel="noopener noreferrer"
            class="btn-primary w-full text-center justify-center"
          >
            <i class="pi pi-github" />
            View Repository & Deploy
          </a>
        </div>
      </div>
    </section>

    <!-- ── CTA Banner ─────────────────────────────── -->
    <section class="cta-section">
      <div class="cta-card">
        <h2 class="cta-title">Ready to take control of your QR codes?</h2>
        <p class="cta-sub">
          Create custom-styled dynamic codes, generate multi-up print sheets, and automate workflows via the REST API.
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
          <span class="footer-copy">© {{ new Date().getFullYear() }} PointQR. Open source under MIT license.</span>
        </div>
        <nav class="footer-links" aria-label="Footer">
          <a href="#print-sheets">Print Sheets</a>
          <a href="#features">Features</a>
          <a href="#automation">API & Automation</a>
          <a href="#self-hosting">Self-Hosting</a>
          <a href="#pricing">Pricing</a>
          <a href="https://github.com/derekleeth/pointqr" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a href="/api/docs" target="_blank" rel="noopener noreferrer">Swagger API</a>
          <RouterLink to="/login">Login</RouterLink>
          <RouterLink to="/register">Register</RouterLink>
        </nav>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* ── Page Shell ──────────────────────────────── */
.home-page {
  min-height: 100vh;
  background-color: var(--bg-base);
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
  scroll-behavior: smooth;
}

/* ── Top Nav ─────────────────────────────────── */
.home-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 2.5rem;
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(14px);
  position: sticky;
  top: 0;
  z-index: 50;
  background: color-mix(in srgb, var(--bg-base) 85%, transparent);
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.home-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  font-weight: 800;
  font-size: 1.125rem;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.brand-badge {
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 99px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border: 1px solid color-mix(in srgb, var(--color-primary) 30%, transparent);
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.nav-link {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.15s ease;
}
.nav-link:hover {
  color: var(--text-primary);
}

.home-nav-links {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.theme-toggle,
.nav-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: none;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  transition: all 0.15s;
}
.theme-toggle:hover,
.nav-icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* ── Buttons ─────────────────────────────────── */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.125rem;
  border-radius: 8px;
  background: var(--color-primary);
  color: #fff;
  font-size: 0.875rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s ease;
}
.btn-primary:hover {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
}
.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background: var(--bg-elevated);
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  border: 1px solid var(--border);
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s ease;
}
.btn-ghost:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: color-mix(in srgb, var(--color-primary) 40%, var(--border));
}
.btn-lg {
  padding: 0.75rem 1.5rem;
  font-size: 0.95rem;
  border-radius: 10px;
}
.w-full {
  width: 100%;
}

/* ── Hero ────────────────────────────────────── */
.hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4.5rem;
  padding: 5rem 2.5rem 4.5rem;
  overflow: hidden;
}

.hero-glow {
  position: absolute;
  inset: -20% -10% auto;
  height: 600px;
  background: radial-gradient(ellipse 65% 55% at 50% 10%, var(--color-primary-soft) 0%, transparent 70%);
  pointer-events: none;
}

.hero-content {
  flex: 1;
  max-width: 620px;
  position: relative;
  z-index: 1;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.85rem;
  border-radius: 99px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 35%, var(--border));
  background: color-mix(in srgb, var(--bg-card) 75%, transparent);
  color: var(--text-primary);
  font-size: 0.8125rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}
.hero-badge i {
  color: var(--color-primary);
}

.hero-title {
  font-size: clamp(2.4rem, 4.5vw, 3.8rem);
  font-weight: 800;
  line-height: 1.12;
  letter-spacing: -0.035em;
  margin: 0 0 1.25rem;
  color: var(--text-primary);
}

.hero-subtitle {
  font-size: 1.0625rem;
  line-height: 1.7;
  color: var(--text-secondary);
  margin: 0 0 2rem;
  max-width: 540px;
}

.hero-cta {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  flex-wrap: wrap;
  margin-bottom: 2.25rem;
}

.hero-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.625rem;
}

.hero-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78125rem;
  font-weight: 500;
  padding: 0.3rem 0.65rem;
  border-radius: 6px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  color: var(--text-secondary);
}
.hero-pill i {
  color: var(--color-primary);
  font-size: 0.75rem;
}

.hero-visual {
  position: relative;
  z-index: 1;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-visual-card {
  padding: 2.25rem;
  border-radius: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
}

.hero-logo {
  width: 290px;
  height: auto;
  display: block;
}

.visual-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.78125rem;
  color: var(--text-muted);
  font-weight: 500;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.15); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

/* ── Spotlight Section (Print Sheet Generator) ── */
.spotlight-section {
  padding: 5.5rem 2.5rem;
  background: var(--bg-card);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.spotlight-header {
  text-align: center;
  max-width: 820px;
  margin: 0 auto 3.5rem;
}

.spotlight-title {
  font-size: clamp(1.8rem, 3.2vw, 2.5rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin: 0.5rem 0 1rem;
}

.spotlight-subtitle {
  font-size: 1.05rem;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0;
}

.spotlight-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3.5rem;
  max-width: 1140px;
  margin: 0 auto;
  align-items: center;
}

.spotlight-features {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.spotlight-feature-item {
  display: flex;
  align-items: flex-start;
  gap: 1.125rem;
}

.spotlight-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
  flex-shrink: 0;
}

.spotlight-item-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.35rem;
}

.spotlight-item-desc {
  font-size: 0.875rem;
  line-height: 1.55;
  color: var(--text-secondary);
  margin: 0;
}

/* ── Sheet Mockup ────────────────────────────── */
.sheet-preview-wrapper {
  display: flex;
  justify-content: center;
}

.sheet-mockup {
  width: 100%;
  max-width: 480px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.5rem;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.06);
}

.sheet-mockup-header {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}

.sheet-tag {
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.55rem;
  border-radius: 6px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.sheet-tag-accent {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-color: color-mix(in srgb, var(--color-primary) 30%, transparent);
  font-weight: 600;
}

.sheet-paper {
  background: #ffffff;
  color: #111827;
  border-radius: 8px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
  padding: 1rem;
  aspect-ratio: 8.5 / 11;
  display: flex;
  flex-direction: column;
}

.sheet-margin-guide {
  flex: 1;
  border: 1px dashed rgba(100, 116, 139, 0.35);
  border-radius: 4px;
  padding: 0.5rem;
}

.sheet-grid-preview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(4, 1fr);
  gap: 0.45rem;
  height: 100%;
}

.mini-qr-cell {
  position: relative;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 3px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.2rem;
}

.mini-label-top,
.mini-label-bot {
  font-size: 0.45rem;
  font-weight: 700;
  color: #334155;
  text-transform: uppercase;
  line-height: 1;
}

.mini-qr-box {
  color: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  padding: 0.1rem 0;
}

.mini-crop-tl,
.mini-crop-tr,
.mini-crop-bl,
.mini-crop-br {
  position: absolute;
  width: 4px;
  height: 4px;
  border-color: #94a3b8;
}
.mini-crop-tl { top: -2px; left: -2px; border-top: 1px solid; border-left: 1px solid; }
.mini-crop-tr { top: -2px; right: -2px; border-top: 1px solid; border-right: 1px solid; }
.mini-crop-bl { bottom: -2px; left: -2px; border-bottom: 1px solid; border-left: 1px solid; }
.mini-crop-br { bottom: -2px; right: -2px; border-bottom: 1px solid; border-right: 1px solid; }

.sheet-mockup-footer {
  margin-top: 1rem;
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.sheet-mockup-footer i {
  color: var(--color-primary);
  margin-right: 0.25rem;
}

/* ── Features Grid ───────────────────────────── */
.features {
  padding: 5.5rem 2.5rem;
  background: var(--bg-base);
}

.features-header {
  text-align: center;
  max-width: 780px;
  margin: 0 auto 3.5rem;
}

.features-eyebrow {
  font-size: 0.8125rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-primary);
  margin: 0 0 0.5rem;
}

.features-title {
  font-size: clamp(1.8rem, 3vw, 2.5rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin: 0 0 1rem;
}

.features-subtitle {
  font-size: 1.05rem;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.5rem;
  max-width: 1140px;
  margin: 0 auto;
}

.feature-card {
  padding: 1.75rem;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
}
.feature-card:hover {
  border-color: var(--color-primary);
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.05);
}

.feature-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.875rem;
}

.feature-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
}

.feature-badge {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  background: var(--color-primary);
  color: #fff;
}

.feature-category {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 0.35rem;
}

.feature-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.5rem;
}

.feature-desc {
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0;
}

/* ── Product Tour / Screenshots ──────────────── */
.tour-section {
  padding: 5.5rem 2.5rem;
  background: var(--bg-base);
  border-top: 1px solid var(--border);
}

.tour-header {
  text-align: center;
  max-width: 820px;
  margin: 0 auto 2.5rem;
}

.tour-title {
  font-size: clamp(1.8rem, 3.2vw, 2.5rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin: 0.5rem 0 1rem;
}

.tour-subtitle {
  font-size: 1.05rem;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0;
}

.tour-container {
  max-width: 1140px;
  margin: 0 auto;
}

.tour-tabs {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.tour-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.1rem;
  border-radius: 99px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.tour-tab-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.tour-tab-btn.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-color: color-mix(in srgb, var(--color-primary) 40%, transparent);
}

.tour-frame {
  border-radius: 14px;
  border: 1px solid var(--border);
  overflow: hidden;
  background: #0f172a;
  box-shadow: 0 24px 50px rgba(0, 0, 0, 0.18);
}

.tour-frame-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.7rem 1rem;
  background: #1e293b;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.tour-frame-url {
  flex: 1;
  max-width: 420px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.06);
  font-size: 0.75rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tour-frame-url i {
  font-size: 0.65rem;
  color: #10b981;
}

.tour-image {
  display: block;
  width: 100%;
  height: auto;
  animation: tour-fade 0.25s ease;
}

@keyframes tour-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

.tour-caption {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 2rem;
  align-items: center;
  margin-top: 1.75rem;
  padding: 1.5rem 1.75rem;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--bg-card);
}

.tour-caption-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.4rem;
}

.tour-caption-desc {
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0;
}

.tour-highlights {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem 1rem;
}

.tour-highlights li {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
}
.tour-highlights i {
  color: var(--color-primary);
  font-size: 0.85rem;
}

/* ── Developer & Automation Hub ──────────────── */
.api-section {
  padding: 5.5rem 2.5rem;
  background: var(--bg-card);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.api-header {
  text-align: center;
  max-width: 820px;
  margin: 0 auto 3rem;
}

.api-title {
  font-size: clamp(1.8rem, 3.2vw, 2.5rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin: 0.5rem 0 1rem;
}

.api-subtitle {
  font-size: 1.05rem;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0;
}

.api-showcase-container {
  max-width: 1000px;
  margin: 0 auto 3.5rem;
}

.api-tabs-bar {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.api-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  border: 1px solid transparent;
  background: none;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.api-tab-btn:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.api-tab-btn.active {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border-color: var(--border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.api-method-badge {
  font-size: 0.6875rem;
  font-weight: 700;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
}
.method-patch { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.method-post { background: rgba(16, 185, 129, 0.15); color: #10b981; }
.method-get { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }

.api-code-card {
  margin-top: 1rem;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  overflow: hidden;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.2);
}

.api-code-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  background: #1e293b;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  gap: 1.5rem;
}

.api-headline {
  font-size: 1rem;
  font-weight: 700;
  color: #f8fafc;
  margin: 0 0 0.35rem;
}

.api-desc {
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #94a3b8;
  margin: 0;
}

.api-code-actions {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  flex-shrink: 0;
}

.api-lang-tag {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  color: #94a3b8;
}

.api-code-block {
  margin: 0;
  padding: 1.25rem 1.5rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  overflow-x: auto;
  color: #38bdf8;
}

/* Automation Use Cases */
.automation-usecases-wrap {
  max-width: 1140px;
  margin: 0 auto;
}

.usecases-headline {
  text-align: center;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 2rem;
}

.usecases-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.25rem;
  margin-bottom: 2.5rem;
}

.usecase-card {
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
}

.usecase-icon-box {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  margin-bottom: 0.875rem;
}

.usecase-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.35rem;
}

.usecase-desc {
  font-size: 0.85rem;
  line-height: 1.55;
  color: var(--text-secondary);
  margin: 0;
}

/* OpenAPI Banner */
.openapi-callout {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 1.75rem 2rem;
  border-radius: 16px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 35%, var(--border));
  background: var(--bg-base);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

.openapi-left {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.openapi-icon {
  font-size: 1.75rem;
  color: var(--color-primary);
  flex-shrink: 0;
}

.openapi-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.25rem;
}

.openapi-desc {
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--text-secondary);
  margin: 0;
}

/* ── Self-Hosting & Tech Stack ───────────────── */
.self-host-section {
  padding: 5.5rem 2.5rem;
  background: var(--bg-base);
  border-bottom: 1px solid var(--border);
}

.self-host-header {
  text-align: center;
  max-width: 820px;
  margin: 0 auto 3rem;
}

.self-host-title {
  font-size: clamp(1.8rem, 3vw, 2.5rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin: 0.5rem 0 1rem;
}

.self-host-subtitle {
  font-size: 1.05rem;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0;
}

/* Terminal */
.terminal-container {
  max-width: 820px;
  margin: 0 auto 4rem;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  overflow: hidden;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.2);
}

.terminal-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: #1e293b;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.terminal-dots {
  display: flex;
  gap: 6px;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.dot-red { background: #ef4444; }
.dot-yellow { background: #f59e0b; }
.dot-green { background: #10b981; }

.terminal-title {
  font-size: 0.78125rem;
  font-family: monospace;
  color: #94a3b8;
}

.terminal-copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.15);
  padding: 0.3rem 0.65rem;
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}
.terminal-copy-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.terminal-code {
  margin: 0;
  padding: 1.25rem 1.5rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  overflow-x: auto;
  color: #38bdf8;
}

/* Architecture Wrap */
.architecture-wrap {
  max-width: 1140px;
  margin: 0 auto 3rem;
}

.arch-headline {
  text-align: center;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 2rem;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.25rem;
}

.tech-card {
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--bg-card);
}

.tech-card-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.tech-icon {
  font-size: 1.35rem;
  color: var(--color-primary);
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: var(--bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
}

.tech-layer {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted);
  display: block;
}

.tech-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.tech-desc {
  font-size: 0.875rem;
  line-height: 1.55;
  color: var(--text-secondary);
  margin: 0;
}

/* Hardware specs */
.hardware-specs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  max-width: 1140px;
  margin: 0 auto;
}

.spec-card {
  padding: 1.75rem;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--bg-card);
}

.spec-icon {
  font-size: 1.25rem;
  color: var(--color-primary);
  margin-bottom: 0.75rem;
}

.spec-card h3 {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.5rem;
}

.spec-card p {
  font-size: 0.875rem;
  line-height: 1.55;
  color: var(--text-secondary);
  margin: 0;
}

/* ── Pricing ─────────────────────────────────── */
.pricing {
  padding: 5.5rem 2.5rem;
  background: var(--bg-card);
}

.pricing-subtitle {
  text-align: center;
  font-size: 1.05rem;
  color: var(--text-secondary);
  margin: -1.5rem auto 3.5rem;
  max-width: 600px;
}

.pricing-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 2rem;
  max-width: 900px;
  margin: 0 auto;
}

.pricing-card {
  padding: 2.5rem;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  position: relative;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease;
}

.pricing-card-highlighted {
  border-color: var(--color-primary);
  box-shadow: 0 10px 30px color-mix(in srgb, var(--color-primary) 15%, transparent);
  background: var(--bg-card);
}

.pricing-badge {
  display: inline-block;
  align-self: flex-start;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.65rem;
  border-radius: 99px;
  background: var(--bg-base);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.badge-highlight {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

.plan-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 0.35rem;
}

.plan-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0 0 1.5rem;
}

.plan-price {
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
  margin-bottom: 1.75rem;
}

.price-val {
  font-size: 2.25rem;
  font-weight: 800;
  color: var(--text-primary);
}

.price-term {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.pricing-list {
  list-style: none;
  padding: 0;
  margin: 0 0 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  flex: 1;
}

.pricing-list li {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  font-size: 0.9rem;
  line-height: 1.45;
  color: var(--text-secondary);
}

.pricing-list li i {
  color: var(--color-primary);
  font-size: 0.95rem;
  margin-top: 0.2rem;
  flex-shrink: 0;
}

.pricing-list strong {
  color: var(--text-primary);
}

/* ── CTA Banner ──────────────────────────────── */
.cta-section {
  padding: 5rem 2.5rem;
  background: var(--bg-base);
}

.cta-card {
  max-width: 820px;
  margin: 0 auto;
  text-align: center;
  padding: 4rem 2.5rem;
  border-radius: 24px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.05);
}

.cta-title {
  font-size: clamp(1.8rem, 3.2vw, 2.4rem);
  font-weight: 800;
  letter-spacing: -0.025em;
  color: var(--text-primary);
  margin: 0 0 0.875rem;
}

.cta-sub {
  font-size: 1.05rem;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0 0 2.25rem;
  max-width: 540px;
  margin-left: auto;
  margin-right: auto;
}

.cta-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

/* ── Footer ──────────────────────────────────── */
.home-footer {
  padding: 2.5rem 2.5rem;
  border-top: 1px solid var(--border);
  background: var(--bg-card);
  font-size: 0.8125rem;
}

.footer-content {
  max-width: 1140px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.footer-brand {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 0.95rem;
}

.footer-copy {
  color: var(--text-muted);
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.footer-links a {
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.15s ease;
}
.footer-links a:hover {
  color: var(--text-primary);
}

/* ── Responsive ──────────────────────────────── */
@media (max-width: 980px) {
  .hero {
    flex-direction: column;
    padding: 3.5rem 1.5rem 2.5rem;
    text-align: center;
  }
  .hero-subtitle {
    margin: 0 auto 2rem;
  }
  .hero-cta {
    justify-content: center;
  }
  .hero-pills {
    justify-content: center;
  }
  .spotlight-container {
    grid-template-columns: 1fr;
    gap: 2.5rem;
  }
  .nav-menu {
    display: none;
  }
  .openapi-callout {
    flex-direction: column;
    align-items: flex-start;
  }
  .tour-caption {
    grid-template-columns: 1fr;
    gap: 1.25rem;
  }
}

@media (max-width: 640px) {
  .home-nav {
    padding: 0.875rem 1.25rem;
  }
  .footer-content {
    flex-direction: column;
    align-items: flex-start;
  }
  .api-code-header {
    flex-direction: column;
    gap: 0.75rem;
  }
  .tour-section {
    padding: 4rem 1.25rem;
  }
  .tour-highlights {
    grid-template-columns: 1fr;
  }
}
</style>
