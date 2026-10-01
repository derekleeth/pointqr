# ARM VPS Compatibility & Deployment Guide

> **Status:** Evaluated & Documented  
> **Target Architecture:** `ARM64` / `aarch64` (e.g., Hetzner CAX series, AWS Graviton `t4g`, Oracle Cloud Ampere A1, Scaleway ARM)  
> **Key Finding:** **PointQR can run natively on a cheaper ARM VPS with 30%–50% cost savings.** All core services run natively; only the local developer SMTP tool (`mailhog`) requires a modern drop-in replacement (`mailpit`).

---

## 1. Executive Summary

When deciding between an x86 server and an ARM server for hosting PointQR:
- **ARM VPS instances are significantly more cost-effective** (often 30%–50% cheaper for equivalent or better CPU and memory performance).
- **PointQR's core stack is 100% ARM-compatible** without requiring emulation:
  - **FastAPI Backend:** Multi-stage build on `python:3.12-slim`. Every single dependency (`asyncpg`, `pydantic-core`, `cryptography`, `bcrypt`, `pillow`, `uvloop`, `celery`) has pre-compiled `manylinux_2_17_aarch64` wheels on PyPI.
  - **PostgreSQL 16:** Official `postgres:16-alpine` multi-arch image (`linux/arm64`).
  - **RabbitMQ 3.13:** Official `rabbitmq:3.13-management-alpine` multi-arch image (`linux/arm64`).
  - **Nginx:** Official `nginx:alpine` multi-arch image (`linux/arm64`).
  - **Vue 3 Frontend:** `node:22-alpine` multi-arch image (`linux/arm64`) with Alpine musl binaries for Vite/Rollup.
- **The Only Blocker:** `mailhog/mailhog:latest` is an abandoned x86-only image that throws `exec format error` on ARM Linux. It must be replaced with **Mailpit** (`axllent/mailpit:latest`), which is a drop-in replacement, or disabled in production where a real SMTP provider is used.

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

## 5. ARM VPS Sizing & Cost Analysis

PointQR's total memory footprint:
- **PostgreSQL 16:** ~50–100 MB idle
- **RabbitMQ 3.13:** ~120–180 MB idle
- **FastAPI:** ~80–120 MB
- **Celery Worker (concurrency 2–4):** ~150–250 MB
- **Nginx:** ~15 MB
- **Total Base Footprint:** ~500 MB – 800 MB RAM

### Provider Comparison

| Provider | Plan | Cores / RAM / Storage | Architecture | Approx Cost | Recommendation |
|---|---|---|---|---|---|
| **Hetzner Cloud** | **CAX11** | 2 vCPU Ampere, 4 GB RAM, 40 GB NVMe | **ARM64** | **~€3.79 / mo** | 🌟 **Best Value** |
| **Hetzner Cloud** | **CAX21** | 4 vCPU Ampere, 8 GB RAM, 80 GB NVMe | **ARM64** | **~€6.49 / mo** | High load / heavy bulk QR generation |
| **Hetzner Cloud** | CX22 | 2 vCPU Intel, 4 GB RAM, 40 GB NVMe | x86-64 | ~€4.35 / mo | More expensive per unit of compute |
| **Oracle Cloud** | VM.Standard.A1.Flex | Up to 4 OCPU, 24 GB RAM | **ARM64** | **$0.00 (Free Tier)** | Completely free always-free tier |
| **AWS Lightsail** | Standard | 1 vCPU, 2 GB RAM, 60 GB SSD | x86-64 | ~$10.00 / mo | 2.5x more expensive than Hetzner ARM |

> **Conclusion:** An entry-level ARM server with 4 GB RAM (e.g. Hetzner CAX11 at under €4/month) is more than sufficient for PointQR with substantial headroom for PostgreSQL indexing and Celery concurrency.

---

## 6. Action Items Checklist (When Ready for Production)

- [ ] Update `docker-compose.yml` to replace `mailhog/mailhog:latest` with `axllent/mailpit:latest`.
- [ ] Create `frontend/Dockerfile` for multi-stage static asset production build.
- [ ] Create `docker-compose.prod.yml` configured for production (no code volume mounts, production logging, multiple Uvicorn workers).
- [ ] Configure domain names, SSL certificates (e.g., Certbot / Let's Encrypt), and secure `.env` secrets on the ARM VPS.
