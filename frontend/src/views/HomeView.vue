<script setup lang="ts">
import { ref, computed } from 'vue'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()

const printSheetFeatures = [
  {
    icon: 'pi pi-file',
    title: 'Standard Paper Sizes',
    desc: 'Print on US Letter or A4 paper, in portrait or landscape, using any home or office printer.',
  },
  {
    icon: 'pi pi-th-large',
    title: 'Automatic Layout',
    desc: 'Pick how big you want each code and PointQR figures out how many fit on the page.',
  },
  {
    icon: 'pi pi-table',
    title: 'Cut Guides Included',
    desc: 'Add corner crop marks or dashed lines so trimming with scissors or a paper cutter is quick and neat.',
  },
  {
    icon: 'pi pi-sliders-h',
    title: 'Adjustable Spacing',
    desc: 'Tweak the margins and the gaps between codes to fit your printer, label sheets, or sticker paper.',
  },
  {
    icon: 'pi pi-tag',
    title: 'Your Text on Every Code',
    desc: 'Labels like "SCAN ME" or your WiFi password stay attached to every copy on the sheet.',
  },
  {
    icon: 'pi pi-bolt',
    title: 'Print-Ready in Seconds',
    desc: 'Get a crisp, high-quality PDF instantly, right in your browser. No waiting, no design software needed.',
  },
]

const features = [
  {
    icon: 'pi pi-palette',
    category: 'Design',
    title: 'Make It Look Like Yours',
    desc: 'Pick colors, dot shapes, and corner styles, and drop in your logo. The preview updates as you go, so what you see is what you print.',
  },
  {
    icon: 'pi pi-pencil',
    category: 'Labels',
    title: 'Add Text Above & Below',
    desc: 'Put a message like "SCAN TO ORDER" on top and your website or WiFi password underneath, with your choice of font, size, and color.',
  },
  {
    icon: 'pi pi-print',
    category: 'Printing',
    title: 'Print Sheets of Codes',
    desc: 'Fill a whole page with copies of your QR code, complete with cut guides, ready for flyers, table tents, or stickers.',
    badge: 'Popular',
  },
  {
    icon: 'pi pi-refresh',
    category: 'Dynamic Codes',
    title: 'Change the Link Anytime',
    desc: 'Printed 200 flyers and the link changed? No problem. Point your dynamic QR code somewhere new without reprinting a thing.',
  },
  {
    icon: 'pi pi-chart-bar',
    category: 'Scan Tracking',
    title: 'See Who\'s Scanning',
    desc: 'Find out how many people scanned your code, when they did it, what kind of phone they used, and roughly where they were.',
  },
  {
    icon: 'pi pi-download',
    category: 'Downloads',
    title: 'Download in Any Format',
    desc: 'Save your code as a PNG image for sharing or an SVG for sharp, scalable printing, with your text labels built right in.',
  },
]

const useCases = [
  {
    icon: 'pi pi-shopping-bag',
    title: 'Fundraisers & Popcorn Sales',
    desc: 'Link to your Scout popcorn or fundraiser order page and print a sheet of codes to hand out to neighbors.',
  },
  {
    icon: 'pi pi-book',
    title: 'Restaurant & Café Menus',
    desc: 'Put a code on every table and update the menu link whenever the specials change.',
  },
  {
    icon: 'pi pi-calendar',
    title: 'Events & Flyers',
    desc: 'Send people to tickets, RSVPs, or event details, and see how many flyers actually got scanned.',
  },
  {
    icon: 'pi pi-wifi',
    title: 'Guest WiFi',
    desc: 'Print a code with your network name and password underneath so guests can get online in one tap.',
  },
  {
    icon: 'pi pi-briefcase',
    title: 'Small Businesses',
    desc: 'Add codes to business cards, packaging, and storefront signs that link to reviews, social pages, or your shop.',
  },
  {
    icon: 'pi pi-users',
    title: 'Schools, Clubs & Teams',
    desc: 'Share sign-up forms, schedules, and newsletters with a code you can update all season long.',
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
          <a href="#uses" class="nav-link">Ideas</a>
          <a href="#pricing" class="nav-link">Pricing</a>
          <RouterLink to="/developers" class="nav-link">Developers</RouterLink>
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
          <span>Free QR codes with printable sheets & scan tracking</span>
        </div>
        <h1 id="hero-title" class="hero-title">
          Beautiful QR Codes,<br />
          <span class="text-gradient">Ready to Print & Share</span>
        </h1>
        <p class="hero-subtitle">
          Design a QR code that matches your style, add a message above and below it, and print a whole
          sheet at once. Change where it points anytime and see how many people scan it.
        </p>
        <div class="hero-cta">
          <RouterLink to="/register" class="btn-primary btn-lg">
            <i class="pi pi-user-plus" />
            Get Started Free
          </RouterLink>
          <a href="#features" class="btn-ghost btn-lg">
            <i class="pi pi-th-large" />
            See Features
          </a>
        </div>

        <!-- Quick highlights pills -->
        <div class="hero-pills">
          <span class="hero-pill"><i class="pi pi-print" /> Printable Sheets with Cut Guides</span>
          <span class="hero-pill"><i class="pi pi-refresh" /> Change Links Without Reprinting</span>
          <span class="hero-pill"><i class="pi pi-chart-bar" /> Scan Tracking</span>
          <span class="hero-pill"><i class="pi pi-pencil" /> Custom Text Labels</span>
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
            <span>Design, Print & Track in Minutes</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Print Sheet Spotlight ─────────────────── -->
    <section id="print-sheets" class="spotlight-section" aria-labelledby="print-sheets-title">
      <div class="spotlight-header">
        <p class="features-eyebrow">The Missing Feature in Existing Tools</p>
        <h2 id="print-sheets-title" class="spotlight-title">Print a Whole Sheet of QR Codes at Once</h2>
        <p class="spotlight-subtitle">
          Most QR tools give you a single image and leave you to copy and paste it dozens of times.
          PointQR lays out a full page of your QR code for you, with cut guides, so you can print, trim,
          and hand them out.
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
              <div class="sheet-tag sheet-tag-accent">High-Quality PDF</div>
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
              <span><i class="pi pi-check-circle" /> Cut Guides</span>
              <span><i class="pi pi-check-circle" /> Automatic Layout</span>
              <span><i class="pi pi-check-circle" /> Ready in Seconds</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── All Features Grid ─────────────────────── -->
    <section id="features" class="features" aria-labelledby="features-title">
      <div class="features-header">
        <p class="features-eyebrow">Features</p>
        <h2 id="features-title" class="features-title">Everything you need to create, print, and track QR codes</h2>
        <p class="features-subtitle">
          No design skills required. Make a code in a couple of minutes and update it whenever you need to.
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

    <!-- ── Use Cases ──────────────────────────────── -->
    <section id="uses" class="uses-section" aria-labelledby="uses-title">
      <div class="features-header">
        <p class="features-eyebrow">Ideas to Get You Started</p>
        <h2 id="uses-title" class="features-title">Perfect for everyday projects</h2>
        <p class="features-subtitle">
          From cub scout popcorn sales to restaurant menus, here are a few ways people use PointQR.
        </p>
      </div>

      <div class="usecases-grid uses-grid">
        <div v-for="uc in useCases" :key="uc.title" class="usecase-card">
          <div class="usecase-icon-box">
            <i :class="uc.icon" />
          </div>
          <h3 class="usecase-title">{{ uc.title }}</h3>
          <p class="usecase-desc">{{ uc.desc }}</p>
        </div>
      </div>
    </section>

    <!-- ── Pricing ───────────────────────────────── -->
    <section id="pricing" class="pricing" aria-labelledby="pricing-title">
      <div class="features-header">
        <p class="features-eyebrow">Pricing</p>
        <h2 id="pricing-title" class="features-title">Start free, and stay free</h2>
        <p class="features-subtitle">
          The free plan will always be free. Paid plans for heavier use are on the way.
        </p>
      </div>

      <div class="pricing-cards-container">
        <!-- Free Card -->
        <div class="pricing-card pricing-card-highlighted">
          <div class="pricing-badge badge-highlight">Free Forever</div>
          <h3 class="plan-title">Free</h3>
          <p class="plan-desc">For fundraisers, clubs, and anyone getting started.</p>
          <div class="plan-price">
            <span class="price-val">$0</span>
            <span class="price-term">/ forever</span>
          </div>
          <ul class="pricing-list">
            <li><i class="pi pi-check" /> <strong>3 Dynamic QR Codes</strong> (change links anytime)</li>
            <li><i class="pi pi-check" /> <strong>Unlimited Static QR Codes</strong></li>
            <li><i class="pi pi-check" /> <strong>300 Tracked Scans / month</strong></li>
            <li><i class="pi pi-check" /> 90 days of scan history</li>
            <li><i class="pi pi-check" /> Full design editor & text labels</li>
            <li><i class="pi pi-check" /> Printable sheets with cut guides</li>
            <li><i class="pi pi-check" /> PNG & SVG downloads</li>
          </ul>
          <RouterLink to="/register" class="btn-primary w-full text-center justify-center">
            Get Started Free
          </RouterLink>
        </div>

        <!-- Pro Card (coming soon) -->
        <div class="pricing-card pricing-card-soon">
          <div class="pricing-badge badge-soon">Coming Soon</div>
          <h3 class="plan-title">Pro</h3>
          <p class="plan-desc">For small businesses and busy organizers.</p>
          <div class="plan-price">
            <span class="price-val price-soon">Coming Soon</span>
          </div>
          <ul class="pricing-list">
            <li><i class="pi pi-check" /> <strong>Everything in Free</strong></li>
            <li><i class="pi pi-check" /> <strong>100 Dynamic QR Codes</strong></li>
            <li><i class="pi pi-check" /> <strong>10,000 Tracked Scans / month</strong></li>
            <li><i class="pi pi-check" /> 1 year of scan history</li>
          </ul>
          <span class="btn-ghost w-full text-center justify-center btn-disabled" aria-disabled="true">
            Coming Soon
          </span>
        </div>

        <!-- Max Card (coming soon) -->
        <div class="pricing-card pricing-card-soon">
          <div class="pricing-badge badge-soon">Coming Soon</div>
          <h3 class="plan-title">Max</h3>
          <p class="plan-desc">For organizations running lots of campaigns.</p>
          <div class="plan-price">
            <span class="price-val price-soon">Coming Soon</span>
          </div>
          <ul class="pricing-list">
            <li><i class="pi pi-check" /> <strong>Everything in Pro</strong></li>
            <li><i class="pi pi-check" /> <strong>1,000 Dynamic QR Codes</strong></li>
            <li><i class="pi pi-check" /> <strong>Unlimited Tracked Scans</strong></li>
            <li><i class="pi pi-check" /> 2 years of scan history</li>
          </ul>
          <span class="btn-ghost w-full text-center justify-center btn-disabled" aria-disabled="true">
            Coming Soon
          </span>
        </div>

        <!-- Self-Hosted Card -->
        <div class="pricing-card">
          <div class="pricing-badge">Open Source</div>
          <h3 class="plan-title">Self-Hosted Community</h3>
          <p class="plan-desc">Run PointQR on your own server with no limits.</p>
          <div class="plan-price">
            <span class="price-val">$0</span>
            <span class="price-term">/ forever (GPL-3.0)</span>
          </div>
          <ul class="pricing-list">
            <li><i class="pi pi-check" /> <strong>Unlimited Dynamic QR Codes</strong></li>
            <li><i class="pi pi-check" /> <strong>Unlimited Tracked Scans</strong></li>
            <li><i class="pi pi-check" /> <strong>Your data stays on your hardware</strong></li>
            <li><i class="pi pi-check" /> Every feature, no gating</li>
            <li><i class="pi pi-check" /> Requires a server & some technical know-how</li>
          </ul>
          <RouterLink :to="{ path: '/developers', hash: '#self-hosting' }" class="btn-ghost w-full text-center justify-center">
            <i class="pi pi-server" />
            Self-Hosting Guide
          </RouterLink>
        </div>
      </div>

      <p class="pricing-footnote">
        Developer? Every account includes REST API access.
        <RouterLink to="/developers">Read about the API & self-hosting →</RouterLink>
      </p>
    </section>

    <!-- ── CTA Banner ─────────────────────────────── -->
    <section class="cta-section">
      <div class="cta-card">
        <h2 class="cta-title">Ready to make your first QR code?</h2>
        <p class="cta-sub">
          Sign up free, design your code, and print a sheet of them in just a few minutes.
        </p>
        <div class="cta-buttons">
          <RouterLink to="/register" class="btn-primary btn-lg">
            Create Free Account →
          </RouterLink>
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
          <a href="#print-sheets">Print Sheets</a>
          <a href="#features">Features</a>
          <a href="#pricing">Pricing</a>
          <RouterLink to="/developers">Developers & Self-Hosting</RouterLink>
          <a href="https://github.com/derekleeth/pointqr" target="_blank" rel="noopener noreferrer">GitHub</a>
          <RouterLink to="/login">Login</RouterLink>
          <RouterLink to="/register">Register</RouterLink>
        </nav>
      </div>
    </footer>
  </div>
</template>

<style scoped src="@/assets/public-site.css"></style>
