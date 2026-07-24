# Social Media Marketing Machine

Social media manager agent for **WebStaffr**. This repo is the
hands-on social media automation layer: it creates, approves,
schedules, publishes, and measures campaigns for the accounts
WebStaffr manages. Use it as the social-media sub-agent inside the
WebStaffr stack, not as a standalone SaaS.

> **Status (2026-07-24, commit `73b0f34`):** 155/155 backend tests passing,
> single Alembic head `e00c25c0041f`, app serving 32 paths. The WS3.3 intake
> bridge is in place, so campaign intent from WebStaffr3.3 now materializes as
> a reviewable campaign with posts, approvals, and an execution graph. See
> `SESSION_STATUS_2026-07-24.md` for the evidence, `TASKS.md` for live status,
> and `HANDOFF.md` to pick up the work.
>
> **Not yet true:** no post has ever been published to a real LinkedIn or
> Instagram account. Every platform adapter is faked in every test; all
> platform integration is `[Unverified]` against live vendor credentials.
>
> <details><summary>Prior status (superseded, kept for history)</summary>
>
> Production-grade scaffold, verified working end-to-end as of
> commit `6fb5dc3` — 46/46 backend tests passing against a live
> PostgreSQL database, backend server confirmed running (`/healthz` +
> auth-gated routes checked directly), frontend dev server confirmed
> running with working Clerk auth middleware. The previously-claimed
> "42/42 against real PostgreSQL" was never actually run; see the
> 2026-07-23 correction section in `BUILD_REPORT.md` for what was found
> and fixed, including a real frontend startup bug that had gone
> undetected. 9 pre-existing `tsc` errors remain open (also documented
> there) and are unrelated to auth/middleware.
>
> </details>

## Stack

- **Backend:** FastAPI (async), SQLAlchemy 2.0 (async), PostgreSQL, Alembic,
  Celery + Redis, Clerk (JWT auth), boto3/S3-compatible storage.
- **Frontend:** Next.js (App Router), TypeScript (strict), Tailwind CSS,
  shadcn/ui, TanStack Query, Clerk, Framer Motion.
- **AI:** pluggable provider abstraction (Ollama fully implemented locally;
  OpenAI/Claude/Gemini/Grok/Hermes typed stubs).
- **Social:** pluggable platform adapter abstraction at
  `backend/app/social/platforms/` (LinkedIn and Instagram fully
  implemented; Facebook/X/Threads/TikTok/Pinterest/YouTube/Google Business
  typed stubs).

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

## Handing this off to another agent (e.g. Hermes)

This repo is a real local git repository with full history — no hosted
remote required. Point the next agent at this directory and it can branch,
commit, and continue work immediately.

**Before handoff, read in this order:** `BUILD_REPORT.md` (what's built,
what's stubbed, exact verification output) → `docs/ARCHITECTURE.md` (module
boundaries and adapter patterns) → `docs/DEVELOPMENT.md` (local setup).

### Prompt given to the previous agent (historical — all 6 tracks now complete)

All six tracks below are done as of commit `6fb5dc3` (confirmed by
directly reading the code and running the tests, not by trusting old
commit messages — see `BUILD_REPORT.md`'s 2026-07-23 correction section
for what was actually verified). Kept here for history, not as an active
task list. The block was originally written to be run by an agent capable
of spawning sub-agents (parallel workers), splitting the six items into
independent tracks with no file overlap.

```
You are continuing work on **Social Media Marketing Machine**, the
social-media manager agent inside **WebStaffr**. It is not a standalone
SaaS here; it is the social media automation sub-agent for WebStaffr.
It creates, approves, schedules, publishes, and measures campaigns for
the accounts WebStaffr manages. Read `BUILD_REPORT.md`,
`docs/ARCHITECTURE.md`, and `docs/DEVELOPMENT.md` before touching
anything.

Ground rules for all work below (non-negotiable, matches the existing
codebase's standard):
- Clean architecture, SOLID, strong typing (Python type hints, TypeScript
  strict), real tests for anything you add, real docstrings.
- No demo-quality code, no "TODO: implement this" left behind — either
  finish it or leave a typed stub matching the existing stub pattern
  (see any of the 5 stubbed AI providers or 8 stubbed social adapters for
  the pattern to copy).
- Every task must end with the backend test suite still green
  (`pytest backend/tests`) and the frontend still building clean
  (`npx tsc --noEmit`, `npm run build`) before you consider it done.
- Commit each completed task separately with a clear message.

Spin up one sub-agent per track below — they touch disjoint files, so run
them in parallel:

TRACK A — Close the scheduled-publish loop
  Add a Celery beat schedule (celery_app.conf.beat_schedule) that polls due
  Schedule rows and enqueues PublishJobs. The immediate "publish now" path
  already works end-to-end (see app/services/publishing); this closes the
  "publish later" path. Add a unit test for the beat task's due-row query
  logic.

TRACK B — Second social platform adapter (DONE — see below)
  Instagram adapter is fully implemented at
  backend/app/social/platforms/instagram.py (not app/services/
  social_platforms/ as this prompt originally said — that path never
  existed). Mirrors the LinkedIn adapter's pattern and test structure
  (backend/tests/unit/test_instagram_adapter.py, 13 tests, all passing).
  Left here for historical reference only.

TRACK C — Media upload pipeline
  Add a pre-signed S3/MinIO upload URL generation endpoint to the media
  router (boto3 is already a dependency; MinIO is already wired in
  docker-compose.yml). Client requests a presigned PUT URL, uploads
  directly, then confirms via the existing media metadata endpoint. Add
  integration tests using the moto library or MinIO test container.

TRACK D — Frontend page wiring
  Wire the remaining page shells (Clients, Calendar, Media Library/AI
  Studio, Approvals, Analytics) to their backend endpoints, following the
  exact pattern established on the Campaigns page (useCampaigns hook →
  TanStack Query → shadcn table/card UI → loading/error/empty states). One
  page at a time, one commit per page. Add a Vitest component test per page
  matching the existing campaigns-table.test.tsx pattern.

TRACK E — Security hardening
  Add column-level encryption for PlatformAccount.access_token and
  refresh_token (currently plain strings — see the model's docstring for
  the known gap). Use a KMS-backed or Fernet-based encryption-at-rest
  approach appropriate for the deployment target. Add a migration and
  tests confirming tokens are encrypted in the DB and decrypted correctly
  on read.

TRACK F — PostgreSQL empirical verification
  Stand up a real PostgreSQL instance (docker compose up postgres is
  sufficient) and run alembic upgrade head against it — this was only
  validated against SQLite in the original build due to sandbox
  constraints. Confirm all 22 tables and constraints match the SQLite
  validation. Report any Postgres-specific issues found and fix them.

After all tracks complete and merge, do a final integration pass: run the
full backend + frontend verification suite together, update BUILD_REPORT.md
with the new state, and commit.
```

## License

Proprietary — internal scaffold, not licensed for external distribution.
