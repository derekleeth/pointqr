<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useThemeStore } from '@/stores/theme'

const router = useRouter()
const theme = useThemeStore()

const features = [
  {
    icon: 'pi pi-palette',
    title: 'Live Design Editor',
    desc: 'Customize dots, corners, colors, and embed your logo — all with a real-time preview that updates in under 50ms.',
  },
  {
    icon: 'pi pi-refresh',
    title: 'Dynamic QR Codes',
    desc: 'Change the destination URL anytime without reprinting. Your QR code stays the same, the destination evolves.',
  },
  {
    icon: 'pi pi-chart-bar',
    title: 'Scan Analytics',
    desc: 'Track every scan with timestamps, device types, geolocation, and browser data — all in one dashboard.',
  },
  {
    icon: 'pi pi-download',
    title: 'High-Res Exports',
    desc: 'Export print-ready PNG, SVG, PDF, or EPS at any resolution. Perfect for packaging, signage, and print.',
  },
]
</script>

<template>
  <div class="home-page">
    <!-- ── Top Nav ───────────────────────────────── -->
    <header class="home-nav">
      <RouterLink to="/" class="home-brand">
        <img
          :src="theme.isDark ? '/PointQR-Light-v3.png' : '/PointQR-Dark-v2.png'"
          alt="PointQR"
          class="home-brand-logo"
        />
      </RouterLink>
      <nav class="home-nav-links">
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
        <button class="theme-toggle" @click="theme.toggle()" :title="theme.isDark ? 'Light mode' : 'Dark mode'">
          <i :class="theme.isDark ? 'pi pi-sun' : 'pi pi-moon'" />
        </button>
        <RouterLink to="/login" class="btn-ghost">Log in</RouterLink>
        <RouterLink to="/register" class="btn-primary">Get Started</RouterLink>
      </nav>
    </header>

    <!-- ── Hero ──────────────────────────────────── -->
    <section class="hero">
      <div class="hero-glow" />
      <div class="hero-content">
        <div class="hero-badge">
          <i class="pi pi-sparkles" style="font-size:0.75rem" />
          Built for marketing teams, agencies & creators
        </div>
        <h1 class="hero-title">
          QR Codes,<br />
          <span class="text-gradient">Reimagined</span>
        </h1>
        <p class="hero-subtitle">
          Create stunning, trackable QR codes in seconds. Customize every pixel,
          update destinations without reprinting, and understand exactly how people engage.
        </p>
        <div class="hero-cta">
          <button class="btn-primary btn-lg" @click="router.push('/register')">
            <i class="pi pi-user-plus" />
            Get Started Free
          </button>
          <button class="btn-ghost btn-lg" @click="router.push('/login')">
            Sign in →
          </button>
        </div>
      </div>

      <!-- Decorative QR grid -->
      <div class="hero-visual" aria-hidden="true">
        <div class="qr-demo-card">
          <div class="qr-dots-grid">
            <div v-for="i in 81" :key="i"
              class="qr-dot"
              :class="{ 'qr-dot--filled': [1,2,3,4,5,6,7,9,15,16,22,23,24,25,26,27,29,37,39,45,46,47,48,49,50,53,54,55,61,65,67,68,69,71,72,73,74,75,76,77,78,79,80,81].includes(i) }"
            />
          </div>
          <div class="qr-card-label">pointqr.app/r/Ab3xKm9Z</div>
        </div>
      </div>
    </section>

    <!-- ── Features ───────────────────────────────── -->
    <section class="features">
      <p class="features-eyebrow">Everything you need</p>
      <h2 class="features-title">Powerful tools, simple workflow</h2>
      <div class="features-grid">
        <div v-for="f in features" :key="f.title" class="feature-card">
          <div class="feature-icon">
            <i :class="f.icon" />
          </div>
          <h3 class="feature-title">{{ f.title }}</h3>
          <p class="feature-desc">{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <!-- ── CTA Banner ─────────────────────────────── -->
    <section class="cta-section">
      <div class="cta-card">
        <h2 class="cta-title">Ready to get started?</h2>
        <p class="cta-sub">Join teams using PointQR to power their QR code strategy.</p>
        <button class="btn-primary btn-lg" @click="router.push('/register')">
          Create your free account →
        </button>
      </div>
    </section>

    <!-- ── Footer ────────────────────────────────── -->
    <footer class="home-footer">
      <span>© {{ new Date().getFullYear() }} PointQR</span>
      <a href="https://github.com/derekleeth/pointqr" target="_blank" rel="noopener noreferrer">GitHub</a>
      <RouterLink to="/login">Login</RouterLink>
      <RouterLink to="/register">Register</RouterLink>
    </footer>
  </div>
</template>

<style scoped>
/* ── Page shell ─────────────────────────────── */
.home-page {
  min-height: 100vh;
  background-color: var(--bg-base);
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
}

/* ── Nav ─────────────────────────────────────── */
.home-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2.5rem;
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 50;
  background: color-mix(in srgb, var(--bg-base) 80%, transparent);
}

.home-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  font-weight: 700;
  font-size: 1rem;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}
.home-brand-logo {
  height: 36px;
  width: auto;
  display: block;
}

.home-nav-links {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.theme-toggle,
.nav-icon-btn {
  width: 34px;
  height: 34px;
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
.nav-icon-btn:hover { background: var(--bg-hover); color: var(--text-primary); }

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
  transition: background 0.15s;
}
.btn-primary:hover { background: var(--color-primary-hover); }
.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background: none;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  border: 1px solid var(--border);
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s;
}
.btn-ghost:hover { background: var(--bg-hover); color: var(--text-primary); }
.btn-lg { padding: 0.75rem 1.5rem; font-size: 1rem; border-radius: 10px; }

/* ── Hero ────────────────────────────────────── */
.hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 3rem;
  padding: 6rem 2.5rem 5rem;
  overflow: hidden;
  flex: 1;
}

.hero-glow {
  position: absolute;
  inset: -10%;
  background: radial-gradient(ellipse 60% 60% at 50% 0%, var(--color-primary-soft) 0%, transparent 70%);
  pointer-events: none;
}

.hero-content {
  flex: 1;
  max-width: 580px;
  position: relative;
  z-index: 1;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.75rem;
  border-radius: 99px;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  font-size: 0.8125rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
}

.hero-title {
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.03em;
  margin: 0 0 1.25rem;
  color: var(--text-primary);
}

.hero-subtitle {
  font-size: 1.0625rem;
  line-height: 1.7;
  color: var(--text-secondary);
  margin: 0 0 2.5rem;
  max-width: 460px;
}

.hero-cta {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  flex-wrap: wrap;
}

/* ── Decorative QR card ──────────────────────── */
.hero-visual {
  position: relative;
  z-index: 1;
  flex-shrink: 0;
}

.qr-demo-card {
  width: 240px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 24px 80px rgba(0,0,0,0.15);
}

.qr-dots-grid {
  display: grid;
  grid-template-columns: repeat(9, 1fr);
  gap: 3px;
  margin-bottom: 1rem;
}
.qr-dot {
  aspect-ratio: 1;
  border-radius: 2px;
  background: var(--bg-elevated);
}
.qr-dot--filled {
  background: var(--color-primary);
}
.qr-card-label {
  font-size: 0.6875rem;
  color: var(--text-muted);
  text-align: center;
  font-family: monospace;
}

/* ── Features ────────────────────────────────── */
.features {
  padding: 5rem 2.5rem;
  background: var(--bg-card);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.features-eyebrow {
  text-align: center;
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-primary);
  margin: 0 0 0.75rem;
}
.features-title {
  text-align: center;
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--text-primary);
  margin: 0 0 3rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  max-width: 1100px;
  margin: 0 auto;
}

.feature-card {
  padding: 1.75rem;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  transition: border-color 0.2s, transform 0.2s;
}
.feature-card:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
}

.feature-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.125rem;
  margin-bottom: 1rem;
}
.feature-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem;
}
.feature-desc {
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0;
}

/* ── CTA Banner ──────────────────────────────── */
.cta-section {
  padding: 5rem 2.5rem;
}
.cta-card {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
  padding: 3.5rem 2.5rem;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg-card);
}
.cta-title {
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--text-primary);
  margin: 0 0 0.75rem;
}
.cta-sub {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0 0 2rem;
}

/* ── Footer ──────────────────────────────────── */
.home-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  padding: 1.5rem 2.5rem;
  border-top: 1px solid var(--border);
  font-size: 0.8125rem;
  color: var(--text-muted);
}
.home-footer a {
  color: var(--text-muted);
  text-decoration: none;
}
.home-footer a:hover { color: var(--text-secondary); }

@media (max-width: 768px) {
  .hero { flex-direction: column; padding: 3rem 1.5rem 2.5rem; text-align: center; }
  .hero-subtitle { margin: 0 auto 2rem; }
  .hero-cta { justify-content: center; }
  .hero-visual { display: none; }
  .home-nav { padding: 1rem 1.5rem; }
}
</style>

