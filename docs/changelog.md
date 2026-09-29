# PointQR – Progress, Bugs & Feature Tracker

> Last Updated: 2026-09-29 · Phase 3 complete

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Completed |
| 🚧 | In Progress |
| ⏳ | Planned |
| 🐛 | Bug |
| 💡 | Feature Request |
| ❌ | Cancelled / Won't Fix |

---

## Phase 1 – Infrastructure & Auth ✅

### Completed

- ✅ **Monorepo structure** – `backend/`, `frontend/`, `nginx/`, `docs/` scaffold
- ✅ **Docker Compose orchestration** – PostgreSQL 16, RabbitMQ 3.13, FastAPI, Celery, Vue/Vite, Nginx, MailHog
- ✅ **Alembic migrations** – `001_initial_schema` (users, qr_codes, scan_events, batch_jobs), `002_add_scan_count`
- ✅ **JWT authentication** – `/v1/auth/register`, `/v1/auth/login`, `/v1/auth/refresh`, `/v1/auth/me`
- ✅ **Pinia auth store** – token management, refresh logic, login/logout
- ✅ **Login & Register views** – PrimeVue forms with validation
- ✅ **AppLayout / AuthLayout** – dual-layout SPA skeleton

---

## Phase 2 – Core QR Engine & Frontend Canvas ✅

### Completed

- ✅ **Vue 3 + PrimeVue setup** – Vite, Tailwind, PrimeVue 4, PrimeIcons wired up
- ✅ **`qrEditor` Pinia store** – `designConfig`, `title`, `qrType`, `targetUrl`, `save()`, `loadFromQRCode()`, `resetToDefaults()`
- ✅ **`QRCanvas.vue`** – `qr-code-styling` live preview, 50ms debounced watch, client-side PNG/SVG quick-download
- ✅ **`DesignPanel.vue`** – Dot style/color, corner square/dot style, background color, logo upload + slider
- ✅ **`ContentPanel.vue`** – URL/text content input wired to store
- ✅ **`QREditorView.vue`** – three-column editor layout
- ✅ **FastAPI QR CRUD** – `GET/POST/PATCH/DELETE /v1/qrcodes` with pagination
- ✅ **Server-side QR generator** – `segno` + `Pillow` for PNG, SVG, PDF, EPS export
- ✅ **Logo upload endpoint** – `POST /v1/qrcodes/{id}/logo`, stored in `/app/storage/logos/`
- ✅ **High-res export endpoint** – `POST /v1/qrcodes/{id}/export?format=png|svg|pdf|eps`
- ✅ **API client layer** – `src/api/client.ts` (Axios + interceptors), `src/api/qrcodes.ts`

---

## Phase 3 – Redirect Service, Async Scan Logging & Background Export ✅

> **Completed:** 2026-09-29

### Completed

- ✅ **`app/api/v1/redirect.py`** — `GET /r/{short_code}` redirect service; in-process TTL cache (60 s), DB indexed lookup on `short_code`, HTTP 302 response, fire-and-forget scan event dispatch
- ✅ **Dynamic QR content fix** — `create_qrcode` now encodes `{REDIRECT_BASE_URL}/r/{short_code}` into the QR matrix for dynamic codes
- ✅ **`app/config.py`** — new `redirect_base_url` setting
- ✅ **`app/tasks/__init__.py`** — tasks package created
- ✅ **`app/tasks/analytics.py`** — `log_scan_event` Celery task (queue: `scan_analytics`); UA parsing (device/OS/browser), SHA-256 IP hashing, `ScanEvent` insert + atomic `scan_count` increment; retry ×3 with 30 s backoff; GeoIP TODO for Phase 4+
- ✅ **`app/tasks/export.py`** — `export_qr_code` Celery task (queue: `qr_export`); PENDING → PROCESSING → COMPLETED/FAILED flow; writes to `/app/storage/exports/`; retry ×3 with exponential backoff
- ✅ **`app/schemas/batch_job.py`** — `BatchJobRead` Pydantic v2 schema
- ✅ **`app/api/v1/qrcodes.py`** — `POST /{qr_id}/export/async` (202 + BatchJob) and `GET /jobs/{job_id}` endpoints added
- ✅ **`app/celery_app.py`** — `include` list updated with `app.tasks.analytics` and `app.tasks.export`
- ✅ **`app/main.py`** — redirect router mounted at app root (`/r/{short_code}`)
- ✅ **Alembic migration `003`** — composite index `scan_events(qr_code_id, timestamp DESC)` + partial index `qr_codes(short_code) WHERE is_active = true`
- ✅ **`pyproject.toml`** — added `user-agents>=2.2.0`, `cachetools>=5.5.0`
- ✅ **`.env.example`** — `REDIRECT_BASE_URL=http://localhost` added
- ✅ **`src/api/qrcodes.ts`** — `BatchJobRead` interface, `startAsyncExport()`, `getExportJob()` added
- ✅ **`src/stores/qrEditor.ts`** — `exportJobId` and `exportStatus` refs added
- ✅ **`src/components/editor/QRCanvas.vue`** — server export buttons replaced with async-polling flow; toast on failure; 60 s timeout
- ✅ **`src/components/editor/ContentPanel.vue`** — dynamic QR helper text added
- ✅ **`src/views/QREditorView.vue`** — dynamic QR notice in live preview panel header

### Bug Fixes Applied During Phase 3

- 🐛 *(fixed)* `startAsyncExport` and `getExportJob` had double `/v1/v1/` URL prefix — corrected to relative paths matching `apiClient` base URL

---

## Phase 4 – Analytics Dashboard & Bulk Generation ⏳

> **Target:** Weeks 7–8

- ⏳ PrimeVue analytics dashboard with Chart.js
- ⏳ Scan metrics: totals, unique visitors, scans over time
- ⏳ Breakdown by OS, browser, device
- ⏳ Geographic distribution
- ⏳ CSV bulk QR generation pipeline via Celery `qr_batch` queue

---

## Phase 5 – Hardening, CI/CD & Docs ⏳

> **Target:** Weeks 9–10

- ⏳ Rate limiting (API-level, per user/IP)
- ⏳ Penetration testing / security audit
- ⏳ Automated CI/CD pipeline (GitHub Actions)
- ⏳ Full project documentation

---

## Bugs 🐛

> _No bugs logged yet._

---

## Feature Requests 💡

> _No feature requests logged yet._

---

## Notes

- Dynamic QR codes store a placeholder `content` during creation (Phase 2). Phase 3 updates this to the real redirect short URL once the redirect service is live.
- Celery workers share the same Docker image as the backend; task modules are auto-discovered via `include=` in `celery_app.py`.
- RabbitMQ Management UI available at `http://localhost:15672` in dev (user: `pointqr`, pass: `pointqr_dev_password`).
- MailHog web UI at `http://localhost:8025`.

