# Development Onboarding

## Prerequisites

- Python 3.10+ (3.11 used in the backend Docker image)
- Node.js 20+
- Docker + Docker Compose (optional but recommended for the full stack)
- [Ollama](https://ollama.com) installed locally if you want to exercise
  real AI generation without any API key (`AI_PROVIDER=ollama`, the default)

## Option A: Docker Compose (fastest path to a running full stack)

```bash
cp .env.example .env
docker compose up --build
```

This brings up Postgres, Redis, MinIO, the FastAPI backend, a Celery
worker, and the Next.js frontend. Run migrations once the stack is up:

```bash
docker compose exec backend alembic upgrade head
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:3000
- MinIO console: http://localhost:9001

## Option B: Manual local dev (no Docker)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp ../.env.example ../.env
# Edit ../.env: point POSTGRES_HOST/REDIS_HOST at localhost if you're
# running Postgres/Redis locally instead of in Docker, e.g.:
#   POSTGRES_HOST=localhost
#   REDIS_HOST=localhost
#   DATABASE_URL=postgresql+asyncpg://smm_admin:smm_dev_password@localhost:5432/smm_platform
#   DATABASE_URL_SYNC=postgresql+psycopg://smm_admin:smm_dev_password@localhost:5432/smm_platform

alembic upgrade head
uvicorn app.main:app --reload
```

If you don't have Postgres running locally at all, you can still run the
test suite (it uses SQLite in-memory, no external DB required):

```bash
pytest tests -v
```

### Celery worker (optional, only needed to exercise publish/retry flows)

```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

Requires Redis running (`REDIS_HOST` / `CELERY_BROKER_URL` in `.env`).

### Frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local   # then trim to NEXT_PUBLIC_* vars you need
npm run dev
```

You'll need a real Clerk application (free tier works) for sign-in to
function — see https://dashboard.clerk.com. Set:
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`

in `frontend/.env.local`, matching the same Clerk app referenced by the
backend's `CLERK_JWKS_URL` / `CLERK_ISSUER`.

### Seeding starter prompt templates

Once you have at least one Organization row (created via your first sign-up
through Clerk, or inserted manually for local testing):

```bash
cd backend
source venv/bin/activate
python -m app.seed_templates --org-id <your-org-uuid>
```

## Running tests

```bash
# Backend
cd backend && pytest tests -v

# Frontend
cd frontend && npm run test        # Vitest
cd frontend && npx tsc --noEmit    # type-check
cd frontend && npm run build       # full production build (requires real Clerk keys)
```

## Project structure

See `docs/ARCHITECTURE.md` for the full module-boundary explanation.

## Platform adapter maturity

| Platform | Status |
|----------|--------|
| LinkedIn | Fully implemented: OAuth2, publish, schedule, delete, update, metrics, media validation |
| Instagram | Fully implemented: OAuth2, publish, schedule, delete, update, metrics, media validation |
| Facebook / X / Threads / TikTok / Pinterest / YouTube / Google Business | Typed stubs via `not_implemented()` — see `app/social/platforms/_stub_base.py` |

## Instagram adapter notes

The Instagram adapter (`app/social/platforms/instagram.py`) mirrors the LinkedIn adapter and supports:
- OAuth token exchange + long-lived token refresh against Meta’s Graph API
- media container creation + publish flow (`/{ig-user-id}/media`, `/{ig-user-id}/media_publish`)
- delete, update (delete + republish fallback), metrics via `/{ig-media-id}/insights`
- local media validation: image ≤ 8 MB, video ≤ 4 GB, JPEG/PNG images ≥ 320px, reels 3–90 seconds

Required environment variables:
- `INSTAGRAM_APP_ID`
- `INSTAGRAM_APP_SECRET`
- `INSTAGRAM_REDIRECT_URI`

Unit tests live under `tests/unit/test_instagram_adapter.py`.

## Code style

- Python: type hints everywhere, docstrings that explain *why* not *what*.
- TypeScript: `strict: true`, no `any` without justification.
- Commit messages: conventional-commit-ish prefixes (`feat:`, `fix:`,
  `docs:`, `test:`, `chore:`) are used throughout this repo's history.
