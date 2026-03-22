# SendMe Technical Notes

This file collects implementation and engineering details. The main `README.md` focuses on product usage.

## Technical Highlights

- Reliable Realtime Sync
  - WebSocket with 3-second polling fallback for unstable networks.
- Automated Lifecycle Management
  - Redis-based TTL index for periodic cleanup of messages and files.
- High-Concurrency File I/O
  - Asynchronous chunked uploads/downloads to minimize memory footprint.
- Security & Auth
  - JWT access/refresh tokens and email OTP registration.
- Production-Ready DevOps
  - Dockerized backend, Alembic migrations, GitHub Actions CI/CD.

## Tech Stack

| Layer              | Technologies                                                            |
|:-------------------|:------------------------------------------------------------------------|
| **Backend**        | **FastAPI** (Python 3.11+), **SQLAlchemy 2.0**, **Pydantic v2**         |
| **Frontend**       | **React 18**, **TypeScript**, **Vite**, **Tailwind CSS**                |
| **Infrastructure** | **PostgreSQL** (Relational Data), **Redis** (Cache & TTL), **Docker**   |
| **DevOps / QA**    | **GitHub Actions**, **Alembic**, **Pytest**, **GHCR (GitHub Packages)** |

## Architecture Notes

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
