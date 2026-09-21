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
- **Caching & Rate Limiting:** In-memory LRU caching within FastAPI and database-backed rate limiting.

### Persistence & Storage

- **Primary Database:** PostgreSQL 16 for relational data (users, QR configurations, scan logs, tags).
- **File Storage:** Local filesystem storage (using persistent Docker volumes shared between FastAPI and Celery worker containers, served directly via FastAPI static file mounts or Nginx) for uploaded logos and generated export files.

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
- **Labels:** Call-to-action (CTA) frames and customizable banner labels (e.g., "SCAN ME").

### Asset Export Engine

- **Formats:** PNG (custom DPI/resolution), SVG (pure vector), PDF, and EPS (print-ready vector).
- **Batch Processing:** CSV upload functionality for hundreds of URLs/texts, returning a zipped archive of QR codes processed via Celery.

### Analytics & Reporting Dashboard

- **Traffic Metrics:** Total scans, unique visitors, and scans over time (hourly, daily, monthly).
- **User Breakdown:** Data segmented by operating system, browser, and device category (mobile vs. tablet vs. desktop).
- **Geographic Data:** Distribution by country, region, and city.
- **Data Export:** Exportable tables (CSV, Excel) powered by PrimeVue DataTable export features.

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

---

## 7. Project Implementation Milestones & Roadmap

| Phase | Timeline | Focus |
|---|---|---|
| **Phase 1** | Weeks 1–2 | Repository structure, Docker Compose orchestration, DB migrations with Alembic, JWT user authentication |
| **Phase 2** | Weeks 3–4 | Vue 3 + PrimeVue setup, interactive canvas editor with live preview, FastAPI QR rendering endpoints |
| **Phase 3** | Weeks 5–6 | URL shortening/redirect service (sub-10ms target), RabbitMQ/Celery async scan logging, background vector export |
| **Phase 4** | Weeks 7–8 | PrimeVue analytics dashboard with Chart.js, CSV bulk QR generation pipeline |
| **Phase 5** | Weeks 9–10 | Rate limiting, penetration testing, automated CI/CD pipelines, project documentation |

---

## 8. Non-Functional Requirements & Security

- **Performance:** Scan redirection latency under 15ms using indexed database lookups and in-memory routing; client-side preview re-render under 50ms.
- **Security:** Privacy-compliant IP anonymization (one-way cryptographic hashing), CORS policies, and strict input validation against SSRF for target URLs.
- **Scalability:** Stateless FastAPI containers and horizontally scalable Celery worker nodes.

