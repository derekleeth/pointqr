# Feedback & Issue Submission System

> Added: 2026-10-20

## Overview

PointQR includes a user-facing feedback system that allows logged-in users to submit bug reports, feature requests, questions, and general feedback directly from the application. Submissions are automatically routed to external services based on their type and are always persisted in the database for admin review.

## Architecture

```
User submits feedback → POST /v1/feedback
                            │
                            ├─ Always → Save to PostgreSQL (feedback_submissions table)
                            │
                            ├─ If bug/feature_request → Create GitHub Issue (via PAT)
                            │
                            └─ If feedback/question → Send Slack notification (via webhook)
```

## Submission Types

| Type | Routing | GitHub Label |
|------|---------|-------------|
| `bug` | GitHub Issues | `bug` |
| `feature_request` | GitHub Issues | `enhancement` |
| `feedback` | Slack Webhook | — |
| `question` | Slack Webhook | — |

## Status Workflow

Submissions start as `open` and can be managed by admins through the following statuses:

```
open → in_progress → resolved → closed
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# GitHub: Personal Access Token for creating issues
# Generate at: https://github.com/settings/tokens
# Requires 'repo' scope (classic) or Issues read/write (fine-grained)
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=derekleeth/pointqr

# Slack: Incoming Webhook URL
# Create at: https://api.slack.com/messaging/webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...
```

Both integrations are **optional** — if tokens are empty, the system gracefully skips the external service and only saves to the database.

## Database

### Table: `feedback_submissions`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK → users.id (CASCADE delete) |
| `type` | Enum | bug, feature_request, feedback, question |
| `subject` | String(255) | Brief summary |
| `message` | Text | Full description |
| `status` | Enum | open, in_progress, resolved, closed |
| `github_issue_url` | String(500) | URL to created GitHub issue (nullable) |
| `github_issue_number` | Integer | GitHub issue number (nullable) |
| `slack_notified` | Boolean | Whether Slack notification was sent |
| `admin_notes` | Text | Internal admin notes (nullable) |
| `created_at` | DateTime(tz) | Submission timestamp |
| `updated_at` | DateTime(tz) | Last update timestamp |

### Migration

Migration `007_add_feedback_submissions.py` creates the table and associated enum types.

```bash
docker compose exec backend alembic upgrade head
```

## API Endpoints

### User Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/feedback` | Submit feedback (rate limited: 5/min) |
| `GET` | `/v1/feedback` | List own submissions |

### Admin Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/feedback/admin` | List all submissions with user info |
| `PATCH` | `/v1/feedback/admin/{id}` | Update status & admin notes |
| `DELETE` | `/v1/feedback/admin/{id}` | Delete a submission |

## Frontend Pages

### `/feedback` — User Submission Page
- Accessible to all authenticated users
- Form with type selector, subject, message
- Shows info hint about GitHub routing for bugs/features
- Success state with GitHub issue link when applicable
- Submission history table with status tracking

### `/admin/feedback` — Admin Management
- Admin-only view (requires admin role)
- Full DataTable with search, type/status filters
- Inline status updates
- Detail dialog with message, GitHub links, admin notes
- Delete with confirmation

## Files Added/Modified

### New Files
- `backend/app/models/feedback.py` — SQLAlchemy model
- `backend/app/schemas/feedback.py` — Pydantic schemas
- `backend/app/services/feedback.py` — GitHub & Slack integrations
- `backend/app/api/v1/feedback.py` — API endpoints
- `backend/alembic/versions/007_add_feedback_submissions.py` — Migration
- `frontend/src/api/feedback.ts` — TypeScript API client
- `frontend/src/views/FeedbackView.vue` — User feedback page
- `frontend/src/views/AdminFeedbackView.vue` — Admin feedback panel

### Modified Files
- `backend/app/models/__init__.py` — Register FeedbackSubmission model
- `backend/app/config.py` — Add GitHub/Slack settings
- `backend/app/api/v1/router.py` — Register feedback router
- `frontend/src/router/index.ts` — Add /feedback and /admin/feedback routes
- `frontend/src/components/sidebar/AppSidebar.vue` — Add nav items
- `.env.example` / `.env` — Add config variables
- `docs/feedback-system.md` — This documentation

