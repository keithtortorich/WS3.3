# Social Media Marketing Machine

A multi-tenant SaaS platform that lets marketing agencies manage multiple
clients and use AI to create, approve, schedule, and publish social media
campaigns across platforms.

> **Status:** production-grade scaffold. See `BUILD_REPORT.md` (once the
> build is complete) for exactly what is implemented vs. stubbed.

## Stack

- **Backend:** FastAPI (async), SQLAlchemy 2.0 (async), PostgreSQL, Alembic,
  Celery + Redis, Clerk (JWT auth), boto3/S3-compatible storage.
- **Frontend:** Next.js (App Router), TypeScript (strict), Tailwind CSS,
  shadcn/ui, TanStack Query, Clerk, Framer Motion.
- **AI:** pluggable provider abstraction (Ollama fully implemented locally;
  OpenAI/Claude/Gemini/Grok/Hermes typed stubs).
- **Social:** pluggable platform adapter abstraction (LinkedIn fully
  implemented; Facebook/Instagram/X/Threads/TikTok/Pinterest/YouTube/Google
  Business typed stubs).

## Quick start (Docker Compose)

```bash
cp .env.example .env
# edit .env with real secrets as needed (defaults work for local dev)
docker compose up --build
```

- Backend API: http://localhost:8000 (docs at `/docs`, `/redoc`)
- Frontend: http://localhost:3000
- MinIO console: http://localhost:9001

## Quick start (manual dev, no Docker)

See `docs/DEVELOPMENT.md` for full onboarding steps. Summary:

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # edit as needed
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Repository layout

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations, Celery workers, tests
frontend/   Next.js App Router frontend
docs/       Architecture, ERD, development, and troubleshooting docs
```

## Documentation

- `docs/ARCHITECTURE.md` — module boundaries, adapter patterns, event-driven design
- `docs/ERD.md` — entity-relationship diagram (Mermaid)
- `docs/DEVELOPMENT.md` — local onboarding steps
- `docs/TROUBLESHOOTING.md` — common local dev issues
- API reference: FastAPI auto-serves OpenAPI docs at `/docs` and `/redoc` once running.

## License

Proprietary — internal scaffold, not licensed for external distribution.
