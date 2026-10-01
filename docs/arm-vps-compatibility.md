# ARM VPS Compatibility & Deployment Guide

> **Status:** Evaluated & Documented  
> **Target Architecture:** `ARM64` / `aarch64` (e.g., Hetzner CAX series, AWS Graviton `t4g`, Oracle Cloud Ampere A1, Scaleway ARM)  
> **Key Finding:** **PointQR can run natively on a cheaper ARM VPS with 30%–50% cost savings.** All core services run natively; only the local developer SMTP tool (`mailhog`) requires a modern drop-in replacement (`mailpit`).
> **Target Architecture:** `ARM64` / `aarch64` vs `x86_64` (Hetzner CX vs CAX series)  
> **Key Finding:** **PointQR can run on either ARM or x86.** However, with current Hetzner pricing (including IPv4), **the x86 CX23 ($7.09/mo) is actually cheaper than the ARM CAX11 ($7.59/mo)**. Choosing x86 avoids paying extra and allows 100% of existing containers (including MailHog) to run out of the box with zero changes.

---

## 1. Executive Summary

When deciding between an x86 server and an ARM server for hosting PointQR:
- **ARM VPS instances are significantly more cost-effective** (often 30%–50% cheaper for equivalent or better CPU and memory performance).
- **PointQR's core stack is 100% ARM-compatible** without requiring emulation:
- **Price Comparison:** With current Hetzner pricing (including IPv4), **x86 CX23 is $7.09/mo**, whereas **ARM CAX11 is $7.59/mo**. You do **not** need to pay more for x86; x86 is actually slightly cheaper!
- **Zero Configuration on x86:** On x86 (CX23 or CX33), your entire existing Docker Compose stack runs immediately without modifying MailHog.
- **ARM Compatibility:** If you do choose an ARM VPS (such as CAX11 or Oracle Cloud Free Tier), PointQR's core stack is 100% ARM-compatible:
  - **FastAPI Backend:** Multi-stage build on `python:3.12-slim`. Every single dependency (`asyncpg`, `pydantic-core`, `cryptography`, `bcrypt`, `pillow`, `uvloop`, `celery`) has pre-compiled `manylinux_2_17_aarch64` wheels on PyPI.
  - **PostgreSQL 16:** Official `postgres:16-alpine` multi-arch image (`linux/arm64`).
  - **RabbitMQ 3.13:** Official `rabbitmq:3.13-management-alpine` multi-arch image (`linux/arm64`).
  - **Nginx:** Official `nginx:alpine` multi-arch image (`linux/arm64`).
  - **Vue 3 Frontend:** `node:22-alpine` multi-arch image (`linux/arm64`) with Alpine musl binaries for Vite/Rollup.
- **The Only Blocker:** `mailhog/mailhog:latest` is an abandoned x86-only image that throws `exec format error` on ARM Linux. It must be replaced with **Mailpit** (`axllent/mailpit:latest`), which is a drop-in replacement, or disabled in production where a real SMTP provider is used.
- **The Only ARM Blocker:** `mailhog/mailhog:latest` is an abandoned x86-only image that throws `exec format error` on ARM Linux. If deploying to an ARM server, it must be replaced with **Mailpit** (`axllent/mailpit:latest`), which is a drop-in replacement.

---

## 2. Service-by-Service Compatibility Audit

| Service | Current Image / Base | Supported Architectures | ARM64 Status | Notes |
|---|---|---|---|---|
| **PostgreSQL** | `postgres:16-alpine` | `amd64`, `arm64`, `arm/v7`, `ppc64le`, `s390x` | ✅ **Native** | Official Alpine multi-arch build on Docker Hub. |
| **RabbitMQ** | `rabbitmq:3.13-management-alpine` | `amd64`, `arm64` | ✅ **Native** | Official Alpine multi-arch build with Management UI. |
| **Nginx** | `nginx:alpine` | `amd64`, `arm64`, `arm/v7`, `s390x` | ✅ **Native** | High-performance reverse proxy running natively on ARM. |
| **Backend (FastAPI)** | `python:3.12-slim` + `uv` | `amd64`, `arm64` | ✅ **Native** | All Python wheels provide pre-compiled aarch64 binaries. No local C compilation needed. |
| **Celery Worker** | `python:3.12-slim` + `uv` | `amd64`, `arm64` | ✅ **Native** | Shares backend image. `segno` + `Pillow` exports run natively. |
| **Frontend** | `node:22-alpine` (`Dockerfile.dev`) | `amd64`, `arm64` | ✅ **Native** | Node 22 on Alpine ARM64. Vite/Rollup install native musl-arm64 binaries. |
| **MailHog** | `mailhog/mailhog:latest` | `amd64` **ONLY** | ❌ **Incompatible** | Abandoned project. Fails on ARM Linux VPS unless slow QEMU emulation is configured. |

---

## 3. The One Required Change: MailHog → Mailpit

### Why MailHog Fails on ARM
The official `mailhog/mailhog` image on Docker Hub was compiled strictly for `linux/amd64`. When pulled on an ARM VPS, Docker will attempt to execute an x86 binary on ARM CPU architecture, leading to:
```text
standard_init_linux.go: exec user process caused: exec format error
```

### The Solution: Mailpit
[Mailpit](https://github.com/axllent/mailpit) is the modern, actively maintained successor to MailHog. It is written in Go, provides official multi-arch Docker images (`linux/arm64` and `linux/amd64`), uses less memory, and is a drop-in replacement with identical port bindings:
- **SMTP Port:** `1025`
- **Web UI Port:** `8025`

#### Docker Compose Configuration
When ready to migrate, update `docker-compose.yml`:
```yaml
  # ---------------------------------------------------------------------------
  # Mailpit – Multi-arch (ARM64/x86) SMTP catcher (MailHog replacement)
  # ---------------------------------------------------------------------------
  mailhog:
    image: axllent/mailpit:latest
    container_name: pointqr_mailhog
    restart: unless-stopped
    ports:
      - "1025:1025"   # SMTP
      - "8025:8025"   # Web UI
    networks:
      - pointqr_network
```
*(Note: Keep the service name as `mailhog` or alias so existing `.env` `MAIL_HOST=mailhog` settings continue to work without changes).*

---

## 4. Production vs Development Architecture

When moving to a VPS for production:

### Development vs Production Differences
1. **Frontend Serving:**
   - **Current (Dev):** `frontend/Dockerfile.dev` runs the Vite dev server with volume mounts (`pnpm dev --host 0.0.0.0`).
   - **Recommended (Prod):** Use a multi-stage Dockerfile (`frontend/Dockerfile`) that runs `pnpm build` and serves static files directly through Nginx. This eliminates Node.js overhead in production (~150MB saved) and enables aggressive browser caching and HTTP/2 compression.
2. **Backend Execution:**
   - **Current (Dev):** Uses `uvicorn ... --reload` via `docker-compose.override.yml`.
   - **Recommended (Prod):** Run Uvicorn with multiple workers or behind Gunicorn (`uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`), without `--reload`.
3. **Email Handling:**
   - On a production server, Mailpit/MailHog is omitted, and transactional email providers (SendGrid, AWS SES, Resend, Postmark) are configured in `.env`.

---

## 5. Server Sizing & Multi-Provider Cost Comparison

### 5.1 PointQR Resource Footprint Baseline
The entire PointQR stack (Postgres + RabbitMQ + FastAPI + Celery + Nginx) requires:
- **PostgreSQL 16:** ~50–100 MB idle
- **RabbitMQ 3.13:** ~120–180 MB idle
- **FastAPI:** ~80–120 MB
- **Celery Worker (concurrency 2–4):** ~150–250 MB
- **Nginx:** ~15 MB
- **Total Base Footprint:** ~500 MB – 800 MB RAM
- **Recommended Minimum RAM:** **4 GB** (ensures smooth operation during peak bulk QR exports, database indexing, and OS caching without OOM risk; 2 GB is workable for staging).

---

### 5.2 Hetzner Cloud

| Plan | Arch | vCPU | RAM | Disk | Traffic | Hourly | Monthly (incl. IPv4) | Notes / Status |
|---|---|---|---|---|---|---|---|---|
| **CX23** | **x86-64** | 2 | 4 GB | 40 GB NVMe | 20 TB | $0.0114 | **$7.09** | 🌟 Runs 100% of containers out-of-the-box. Cheaper than CAX11! |
| **CAX11** | **ARM64** | 2 | 4 GB | 40 GB NVMe | 20 TB | $0.0122 | **$7.59** | Fully compatible once MailHog is swapped to Mailpit. |
| **CX33** | **x86-64** | 4 | 8 GB | 80 GB NVMe | 20 TB | $0.0170 | **$10.59** | Great upgrade for higher load / Celery batch processing. |

---

### 5.3 Netcup

*(Prices in EUR, incl. 0% VAT; contracts include traffic, snapshots, remote console)*

| Plan | Arch | vCore | RAM | Disk | Contract | Monthly | Approx USD | Suitability for PointQR |
|---|---|---|---|---|---|---|---|---|
| **VPS pico G11.5s** | **x86** | 1 | 1 GB | 30 GB SSD | 12 mo | **€1.85** | ~$2.00 | ⚠️ **Too small:** 1 GB risks OOM kills with Postgres + RabbitMQ + Celery. |
| **VPS nano G11.5s** | **x86** | 2 | 2 GB | 60 GB SSD | 6 mo | **€3.10** | ~$3.35 | ⚡ **Tight:** Sufficient for dev/staging, but leaves little margin during bulk jobs. |
| **VPS Lite 1 G12.5s**| **x86** | 2 | 4 GB | 80 GB SSD | 6 mo | **€4.92** | **~$5.35** | 🌟 **Top Budget Sweet Spot:** 4 GB RAM, 80 GB SSD, x86 native, under €5/mo! |
| **VPS Lite 2 G12.5s**| **x86** | 4 | 8 GB | 160 GB SSD| 3 mo | **€7.98** | **~$8.70** | 🚀 **Top Power Value:** 4 vCores, 8 GB RAM, 160 GB SSD for less than Hetzner CX33. |

---

### 5.4 Cross-Provider Comparison & Key Takeaways

#### The 4 GB RAM Sweet Spot (Recommended for PointQR):
1. **Netcup VPS Lite 1 (€4.92 / ~$5.35 mo)**:
   - **Cheapest 4 GB option overall** (saves ~$1.74/mo compared to Hetzner CX23 and ~$2.24/mo compared to Hetzner CAX11).
   - Gives **80 GB SSD** (2x the storage of Hetzner CX23).
   - **x86 architecture**: Runs 100% of existing PointQR containers (including MailHog) immediately with zero modifications.
   - *Trade-off*: 6-month contract commitment (vs Hetzner hourly billing).

2. **Hetzner CX23 ($7.09 mo)**:
   - **Best for hourly / month-to-month flexibility** (cancel anytime, pay per hour).
   - Fast NVMe drives.
   - **x86 architecture**: Runs 100% of existing containers out-of-the-box.
   - Cheaper than Hetzner ARM CAX11 ($7.59).

3. **Hetzner CAX11 ($7.59 mo)**:
   - ARM64 architecture (requires Mailpit migration).
   - More expensive than both Netcup Lite 1 and Hetzner CX23.

> [!TIP]
> **Summary Recommendation:**
> - If you want the **absolute lowest monthly price** with generous disk space: **Netcup VPS Lite 1** (€4.92/mo) is the clear winner.
> - If you want **hourly billing without contract lock-in**: **Hetzner CX23** ($7.09/mo) is the best choice.
> - In both cases, **both are x86**, meaning **you don't have to worry about ARM container incompatibilities or swapping MailHog right away!**

---

## 6. Action Items Checklist (When Ready for Production)

- [ ] Update `docker-compose.yml` to replace `mailhog/mailhog:latest` with `axllent/mailpit:latest`.
- [ ] Create `frontend/Dockerfile` for multi-stage static asset production build.
- [ ] Create `docker-compose.prod.yml` configured for production (no code volume mounts, production logging, multiple Uvicorn workers).
- [ ] Configure domain names, SSL certificates (e.g., Certbot / Let's Encrypt), and secure `.env` secrets on the ARM VPS.
