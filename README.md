# SendMe

SendMe is a cross-device file/message transfer app:
- Backend: FastAPI + PostgreSQL + Redis
- Frontend: React + Vite + TypeScript
- Auth: username/password login + email OTP registration
- Messaging: text + file/image upload, history, download/view, delete

## 1. Architecture

- `frontend/`: React UI (`http://localhost:3000` or Vite port)
- `app/`: FastAPI backend (`http://localhost:8000`)
- `db`: PostgreSQL for users/messages
- `redis`: OTP state + message TTL index
- `uploads/`: local file storage

Backend layers:
- API layer: `app/api/auth.py`, `app/api/router.py`
- Service layer: `app/services/*`
- Repository layer: `app/storage/*`
- DI wiring: `app/core/dependencies.py`

## 2. Quick Start (Docker)

### 2.1 Prerequisites
- Docker Desktop running
- Node.js 18+ (frontend local dev)

### 2.2 Start backend + infra
```bash
docker compose up -d db redis backend
```

Backend docs:
- Swagger UI: `http://0.0.0.0:8000/docs`
- OpenAPI JSON: `http://0.0.0.0:8000/openapi.json`

### 2.3 Start frontend
```bash
cd frontend
npm install
npm run dev -- --port 3000
```

## 3. Environment Variables

Main `.env` keys:
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `UPLOAD_DIR`
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_EMAIL`
- `SMTP_CODE`

Notes:
- Inside Docker backend, DB host should be `db`.
- On host scripts, DB/Redis host is usually `localhost`.

## 4. Migrations (Alembic)

```bash
alembic revision --autogenerate -m "your message"
alembic upgrade head
```

If host migration reports `could not translate host name "db"`:
- use a host DB URL (e.g. `localhost`) for that command, or
- run migration inside backend container.

## 5. API Overview

Base path: `/api/v1`

Auth:
- `POST /auth/request-otp`
- `POST /auth/register-with-otp`
- `POST /auth/login`
- `POST /auth/refresh`

Messages:
- `POST /messages/text`
- `GET /messages/history`
- `POST /messages/upload`
- `GET /messages/{message_id}/download`
- `GET /messages/{message_id}/view` (image only)
- `DELETE /messages/{message_id}`
- `WS /ws/messages?token=<access_token>` (real-time updates)

Detailed API doc: `docs/API.md`

## 6. Recommended End-to-End Flow

1. Request OTP: `POST /auth/request-otp`
2. Register with OTP: `POST /auth/register-with-otp`
3. Login to get access token: `POST /auth/login`
4. Open WebSocket for real-time sync: `WS /ws/messages?token=...`
5. Send text: `POST /messages/text`
6. Upload file/image: `POST /messages/upload`
7. Pull history: `GET /messages/history`
8. Download/view/delete by message id

## 7. TTL & Capacity

- `MESSAGE_TTL_SECONDS` (default `86400`) controls expiration.
- New messages are indexed in Redis for TTL cleanup.
- Background cleanup removes expired messages (including files) periodically.
- Capacity is tracked per user with `used_quota_bytes`.
- Frontend strategy:
  - Primary: WebSocket event-driven refresh
  - Fallback: polling every 3 seconds when WS disconnects

## 8. Testing

Backend (container):
```bash
docker compose run --rm backend pytest
```

Backend (host):
```bash
pytest
```

Frontend build check:
```bash
cd frontend
npm run build
```

## 9. Common Issues

- `401 Unauthorized` on `/messages/history` at startup:
  - clear stale `authToken` in localStorage and login again.
- Browser CORS error after request:
  - backend may actually be `500`; inspect backend logs first.
- OTP send returns `503`:
  - verify SMTP config and provider limits.

## 10. CI/CD (GitHub Actions)

### CI
- Workflow file: `.github/workflows/ci.yml`
- Trigger: push/pull request to `main` or `master`
- Jobs:
  - Backend tests: install Python dependencies and run `pytest -q`
  - Frontend build: run `npm ci` + `npm run build`

### CD
- Workflow file: `.github/workflows/cd.yml`
- Trigger: push to `main`/`master` (or manual dispatch)
- Jobs:
  - Build and push backend Docker image to GHCR:
    - `ghcr.io/<owner>/<repo>/backend`
    - tags include branch, commit SHA, and `latest` on default branch
  - Optional deploy webhook:
    - If `DEPLOY_WEBHOOK_URL` secret is configured, CD triggers it after image publish.

Required repository settings:
- Actions permissions: allow `GITHUB_TOKEN` to write packages (for GHCR push)
- Optional secret:
  - `DEPLOY_WEBHOOK_URL` (for Render/Railway/Fly/other webhook-based deployment)
