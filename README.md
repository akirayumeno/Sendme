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

## 6. Realtime Sync (WebSocket)

WebSocket endpoint:
- `WS /api/v1/ws/messages?token=<access_token>`

How it works:
- Login first to get `access_token`
- Frontend connects WS with token in query
- Backend pushes events when message changes:
  - `message.updated`
  - `message.deleted`
- Frontend receives event and refreshes history

Fallback strategy:
- If websocket disconnects, frontend falls back to 3-second polling
- When websocket reconnects, polling stops

## 7. Recommended End-to-End Flow

1. Request OTP: `POST /auth/request-otp`
2. Register with OTP: `POST /auth/register-with-otp`
3. Login to get access token: `POST /auth/login`
4. Open WebSocket for real-time sync: `WS /ws/messages?token=...`
5. Send text: `POST /messages/text`
6. Upload file/image: `POST /messages/upload`
7. Pull history: `GET /messages/history`
8. Download/view/delete by message id

## 8. TTL & Capacity

- `MESSAGE_TTL_SECONDS` (default `86400`) controls expiration.
- New messages are indexed in Redis for TTL cleanup.
- Background cleanup removes expired messages (including files) periodically.
- Capacity is tracked per user with `used_quota_bytes`.
- Frontend strategy:
  - Primary: WebSocket event-driven refresh
  - Fallback: polling every 3 seconds when WS disconnects

## 9. Testing

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

## 10. Release Guide

Recommended release style: semantic version tags (`vX.Y.Z`)

### 10.1 Prepare release branch state
```bash
git checkout main
git pull origin main
```

### 10.2 Run local verification
```bash
docker compose run --rm backend pytest -q
cd frontend && npm run build
```

### 10.3 Create and push tag
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin main
git push origin v1.0.0
```

### 10.4 Create GitHub Release
- Open GitHub repository -> Releases -> Draft a new release
- Select tag (`v1.0.0`)
- Add release notes:
  - Features
  - Fixes
  - Breaking changes (if any)

## 11. Deployment Guide

Current CD workflow:
- Push to `main/master` triggers `.github/workflows/cd.yml`
- Build backend image and push to GHCR:
  - `ghcr.io/<owner>/<repo>/backend:<tag>`

### 11.1 Required GitHub settings
- Repository Actions enabled
- Workflow permissions allow package write
- Optional secret:
  - `DEPLOY_WEBHOOK_URL` (if you want auto deploy trigger)

### 11.2 Deploy options

Option A: Webhook-based platform (Render/Railway/Fly with webhook)
- Configure platform to pull latest image tag
- Add `DEPLOY_WEBHOOK_URL` in GitHub secrets
- CD will call webhook after image push

Option B: Manual Docker deploy on server
```bash
docker pull ghcr.io/<owner>/<repo>/backend:latest
docker stop sendme-backend || true
docker rm sendme-backend || true
docker run -d --name sendme-backend \
  -p 8000:8000 \
  --env-file .env \
  ghcr.io/<owner>/<repo>/backend:latest
```

## 12. Common Issues

- `401 Unauthorized` on `/messages/history` at startup:
  - clear stale `authToken` in localStorage and login again.
- Browser CORS error after request:
  - backend may actually be `500`; inspect backend logs first.
- OTP send returns `503`:
  - verify SMTP config and provider limits.

## 13. CI/CD (GitHub Actions)

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
