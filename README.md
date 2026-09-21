# pointqr
# PointQR 📱

A modern, scalable QR Code Generation Platform — create, customize, manage, and track static and dynamic QR codes.

## Features

- 🎨 **Interactive QR Editor** — Real-time canvas preview with dot patterns, gradients, and logo embedding
- ⚡ **Dynamic Redirects** — Update link destinations anytime; sub-15ms redirect latency
- 📊 **Scan Analytics** — Track scans by location, device, OS, browser, and time
- 🗂️ **Bulk Generation** — Upload CSV → receive ZIP of QR codes via async Celery workers
- 🔐 **JWT Authentication** — Secure OAuth2 access/refresh token flow

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 + Vite + PrimeVue 4 + Pinia + TypeScript |
| Backend | FastAPI (Python 3.12) + SQLAlchemy 2.0 async |
| Database | PostgreSQL 16 |
| Task Queue | Celery 5 + RabbitMQ 3.13 |
| Infrastructure | Docker Compose + Nginx |

## Project Structure

```
pointqr/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/v1/       # REST endpoints
│   │   ├── core/         # Security, dependencies
│   │   ├── models/       # SQLAlchemy ORM models
│   │   └── schemas/      # Pydantic schemas
│   ├── alembic/          # Database migrations
│   └── tests/
├── frontend/             # Vue 3 SPA
│   └── src/
│       ├── api/          # Axios client with JWT interceptor
│       ├── components/   # Shared components
│       ├── router/       # Vue Router (auth guards)
│       ├── stores/       # Pinia stores
│       └── views/        # Page components
├── nginx/                # Reverse proxy config
├── docs/                 # Project documentation
├── docker-compose.yml
└── .env.example
```

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24+)
- [Git](https://git-scm.com/)

### 1. Clone & configure

```bash
git clone https://github.com/your-org/pointqr.git
cd pointqr

# Copy and edit environment variables
cp .env.example .env
# Edit SECRET_KEY with a strong random value:
# python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Start all services

```bash
docker compose up --build
```

### 3. Access the app

| Service | URL |
|---|---|
| 🌐 Frontend | http://localhost |
| 📖 API Docs (Swagger) | http://localhost/api/docs |
| 🐰 RabbitMQ Management | http://localhost:15672 |
| 📧 MailHog (dev email) | http://localhost:8025 |

> **Default RabbitMQ credentials:** `pointqr` / `pointqr_dev_password` (from `.env`)

### 4. Register & login

1. Open http://localhost/register
2. Create an account
3. You'll be redirected to the Dashboard

## Development

### Running backend tests

```bash
docker compose exec backend pytest tests/ -v
```

### Database migrations

```bash
# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Create a new migration (auto-generate from model changes)
docker compose exec backend alembic revision --autogenerate -m "description"

# Rollback one migration
docker compose exec backend alembic downgrade -1
```

### Hot reload

Both the backend (Uvicorn `--reload`) and frontend (Vite HMR) support hot reload automatically via the `docker-compose.override.yml` volume mounts.

## Environment Variables

See [`.env.example`](.env.example) for all available configuration options.

Key variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key — **must be changed in production** |
| `DATABASE_URL` | PostgreSQL async connection string |
| `CELERY_BROKER_URL` | RabbitMQ AMQP URL |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |

## Roadmap

| Phase | Status | Focus |
|---|---|---|
| Phase 1 | ✅ In Progress | Foundation: Docker, DB migrations, JWT auth |
| Phase 2 | 🔜 Planned | QR canvas editor + FastAPI rendering endpoints |
| Phase 3 | 🔜 Planned | Dynamic redirects + async scan logging |
| Phase 4 | 🔜 Planned | Analytics dashboard + bulk CSV generation |
| Phase 5 | 🔜 Planned | Security hardening, CI/CD, production launch |

See [`docs/project-plan.md`](docs/project-plan.md) for the full project plan.

## License

MIT
