# Project Plan: PointQR – QR Code Generation Platform

## 1. Executive Summary & Project Objectives

### Project Purpose

The objective is to build a modern, scalable, and responsive web application for creating, customizing, managing, and tracking static and dynamic QR codes called **PointQR**.

### Core Goals

- **Interactive Design:** Real-time client-side interactive preview and custom styling including colors, shapes, logo embeds, and frames.
- **Performance:** High-throughput dynamic URL redirection engine with low latency.
- **Scalability:** Distributed background processing for high-resolution exports (PNG, SVG, PDF, EPS) and bulk batch generation.
- **Analytics:** Comprehensive scan analytics dashboard providing timestamps, locations, and device/browser statistics.

### Target Audience

Marketing professionals, businesses, event organizers, and individual creators requiring reliable QR solutions.

---

## 2. Technology Stack & Architectural Overview

### Frontend

- **Framework:** Vue 3 utilizing Composition API, `<script setup>`, and Vite build tooling.
- **UI Library:** PrimeVue, leveraging DataTables (sorting/filtering/export), built-in Chart.js wrappers via `<p-chart>`, and UI components for editor toolbars.
- **State & Routing:** Pinia for reactive store management and Vue Router for SPA routing.
- **Rendering:** HTML5 Canvas and SVG rendering libraries (e.g., `qrcode.vue`, Fabric.js / native canvas API) for live design preview.

### Backend API

- **Framework:** FastAPI (Python 3.12+ async) for high performance and native OpenAPI documentation.
- **Validation:** Pydantic v2.
- **Database ORM:** SQLAlchemy 2.0 (asyncio) / SQLModel.
- **Authentication:** OAuth2 with JWT access and refresh tokens.

### Distributed Task Queue & Asynchronous Processing

- **Task Queue:** Celery 5.x.
- **Message Broker & Result Backend:** RabbitMQ (AMQP protocol for robust task queuing, message routing, dead-letter exchanges, and RPC/AMQP task results). Task states and job completion records are stored directly in PostgreSQL (`BatchJobs` table), eliminating the need for Redis.
- **Task Scheduling & Periodic Maintenance:** Celery Beat daemon for automated recurring jobs (export file pruning, storage threshold monitoring, and periodic health checks).
- **Caching & Rate Limiting:** In-memory LRU caching within FastAPI and database-backed rate limiting.

### Persistence & Storage

- **Primary Database:** PostgreSQL 16 for relational data (users, QR configurations, scan logs, tags).
- **File Storage & Lifecycle:** Local filesystem storage (using persistent Docker volumes `pointqr_storage` shared between FastAPI, Celery worker, and Celery Beat containers, served directly via Nginx or FastAPI static mounts). Storage is partitioned into permanent user assets (`/storage/logos/`) and transient generated files (`/storage/exports/`, batch archives), managed with automated TTL cleanup and disk usage monitoring.

### Infrastructure

- Docker & Docker Compose for containerized local development and production orchestration.
- Reverse proxy & SSL termination via Nginx or Traefik.

---

## 3. High-Level System Architecture & Data Flow

### Interactive QR Generation Flow

1. The user adjusts design parameters in the Vue frontend which triggers a real-time canvas rendering.
2. For high-resolution rasterization or vector exports (SVG, EPS, PDF), the frontend requests an export from FastAPI.
3. FastAPI offloads heavy generation/export tasks to RabbitMQ.
4. Celery workers pick up the task, render the asset, write the file to the shared local storage directory, and notify the backend/frontend with the local file path/URL.

### Dynamic QR Code Redirection & Tracking Flow

1. The end user scans a dynamic QR code pointing to a short URL (e.g., `https://qr.domain.com/r/{short_code}`).
2. The FastAPI redirection service looks up the destination URL via an in-memory LRU cache or directly from PostgreSQL using indexed queries on `short_code`.
3. FastAPI responds immediately with an HTTP 302/307 redirect to maximize scanning speed.
4. A scan event payload (IP hash, User-Agent, referer, timestamp, geo data) is published asynchronously to RabbitMQ.
5. Celery workers consume the scan event, enrich geographic data via GeoIP lookup, parse user-agent details, and batch-insert records into PostgreSQL.

---

## 4. Core System Components & Feature Specifications

### QR Customization Engine

- **Patterns:** Customizable dot patterns, corner square styles, and corner dot styles.
- **Styling:** Solid colors, linear/radial gradients, and custom or transparent backgrounds.
- **Logo Embedding:** Center logo/icon embedding with automatic error correction level adjustment (Level H recommended).
- **Labels:** Call-to-action (CTA) frames and customizable banner labels (e.g., "SCAN ME"). Includes independently configurable top and bottom text labels with full typography controls (font family, font size, bold/italic, color, alignment, letter spacing, and padding) and composited client-side export.

### Asset Export Engine

- **Formats:** PNG (custom DPI/resolution and composite multi-layer client-side export), SVG (pure vector with integrated text labels), PDF, and EPS (print-ready vector).
- **Batch Processing:** CSV upload functionality for hundreds of URLs/texts, returning a zipped archive of QR codes processed via Celery.

### Analytics & Reporting Dashboard

- **Traffic Metrics:** Total scans, unique visitors, and scans over time (hourly, daily, monthly).
- **User Breakdown:** Data segmented by operating system, browser, and device category (mobile vs. tablet vs. desktop).
- **Geographic Data:** Distribution by country, region, and city.
- **Data Export:** Exportable tables (CSV, Excel) powered by PrimeVue DataTable export features.

### Storage Management & Disk Monitoring Engine

- **Automated Export Lifecycle & Cleanup:**
  - Configurable retention window (default: 24–48 hours via `EXPORT_RETENTION_HOURS`) for generated export files and bulk zip packages in `/storage/exports/`.
  - Periodic Celery Beat task sweeps `/storage/exports/`, deleting expired directories/files whose mtime exceeds the retention policy, and cleans up corresponding temporary batch artifacts.
  - Safeguard isolation: Permanent user assets in `/storage/logos/` are strictly excluded from automated cleanup.
- **Disk Usage & Capacity Monitoring:**
  - Periodic Celery Beat task monitors persistent storage volume utilization using `shutil.disk_usage()`.
  - Configurable warning (`80%`) and critical (`90%`) thresholds with structured log alerts and metric logging to prevent volume exhaustion.
  - Option to expose disk utilization metrics via system health endpoint / WebSocket for real-time operational visibility.

---

## 5. Database Schema & Data Models

| Table | Primary Fields |
|---|---|
| `Users` | `id`, `email`, `hashed_password`, `role`, `tier`, `created_at` |
| `QRCodes` | `id`, `user_id`, `title`, `type` (STATIC/DYNAMIC), `short_code`, `target_url`, `design_config` (JSONB), `is_active`, `created_at`, `updated_at` |
| `ScanEvents` | `id`, `qr_code_id`, `timestamp`, `ip_hash`, `country`, `city`, `device_type`, `os`, `browser`, `referer` |
| `BatchJobs` | `id`, `user_id`, `status` (PENDING, PROCESSING, COMPLETED, FAILED), `total_items`, `processed_items`, `result_url`, `created_at` |

---

## 6. Celery & RabbitMQ Queue Design

### Queue Topology

| Queue | Purpose |
|---|---|
| `default` | General lightweight async tasks (email notifications, password resets) |
| `qr_export` | High-priority image rendering and single-code vector export tasks |
| `qr_batch` | Lower-priority bulk batch generation jobs with concurrency limits |
| `scan_analytics` | High-throughput ingestion of scan logging events |

### Reliability & Worker Tuning

- Prefetch limits and ACK on completion.
- Dead-letter exchanges (DLX) for failed messages.
- Automatic retries with exponential backoff.

### Celery Beat Periodic Schedules

PointQR uses a dedicated Celery Beat scheduler daemon (`celery -A app.celery_app beat`) to dispatch recurring maintenance and monitoring tasks to the `default` queue:

| Task Name | Schedule | Target Queue | Purpose |
|---|---|---|---|
| `cleanup_expired_exports` | Hourly (`0 * * * *`) | `default` | Scan `/storage/exports/` and purge export files/folders older than `EXPORT_RETENTION_HOURS` (default 24h) |
| `monitor_storage_usage` | Every 15 min (`*/15 * * * *`) | `default` | Check storage volume free disk space and percentage usage; emit warnings if usage > 80% and critical alerts if > 90% |

---

## 7. Project Implementation Milestones & Roadmap

| Phase | Timeline | Focus | Status |
|---|---|---|---|
| **Phase 1** | Weeks 1–2 | Repository structure, Docker Compose orchestration, DB migrations with Alembic, JWT user authentication | ✅ Completed |
| **Phase 2** | Weeks 3–4 | Vue 3 + PrimeVue setup, interactive canvas editor with live preview, FastAPI QR rendering endpoints | ✅ Completed |
| **Phase 3** | Weeks 5–6 | URL shortening/redirect service (sub-10ms target), RabbitMQ/Celery async scan logging, background vector export, outer text labels | ✅ Completed |
| **Phase 4** | Weeks 7–8 | PrimeVue analytics dashboard (✅ Track A), CSV bulk QR generation pipeline (⏳ Track B), Storage lifecycle management & automated cleanup via Celery Beat (⏳ Track C) | 🚧 In Progress |
| **Phase 5** | Weeks 9–10 | Rate limiting, penetration testing, automated CI/CD pipelines, project documentation | ⏳ Planned |

### Phase 4 Detailed Breakdown: Analytics, Bulk Generation & Storage Operations

- **Track A: Scan Analytics Dashboard (✅ Completed)**
  - Aggregated metrics API (`/v1/analytics/*`), PrimeVue + Chart.js time-series, browser/OS/device doughnuts, and country breakdown.
- **Track B: CSV Bulk QR Generation Pipeline (⏳ Planned)**
  - CSV parser, batch rendering to ZIP archive on `qr_batch` queue, BatchJob tracking, drag-and-drop batch UI.
- **Track C: Storage Lifecycle Management & Celery Beat Automation (⏳ Planned)**
  - **Celery Beat Service:** Add `celery_beat` scheduler container to `docker-compose.yml` (`celery -A app.celery_app beat`).
  - **Automated Retention Cleanup:** Periodic task `cleanup_expired_exports` to purge `/storage/exports/` directories and batch zip packages exceeding retention TTL (default 24 hours), preventing export accumulation from both single exports (Phase 3) and batch archives (Track B).
  - **Disk Space Monitoring:** Periodic task `monitor_storage_usage` evaluating volume capacity via `shutil.disk_usage()`, warning on 80% usage and alerting at 90%.
  - **Asset Safeguards:** Strict path exclusion ensuring uploaded brand assets in `/storage/logos/` are protected from automated cleanup routines.


---

## 8. Non-Functional Requirements & Security

- **Performance:** Scan redirection latency under 15ms using indexed database lookups and in-memory routing; client-side preview re-render under 50ms.
- **Security:** Privacy-compliant IP anonymization (one-way cryptographic hashing), CORS policies, and strict input validation against SSRF for target URLs.
- **Scalability:** Stateless FastAPI containers and horizontally scalable Celery worker nodes.

