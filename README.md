# WS3.3
Production repository for the WebStaffr AI workforce platform.

## Quick Start

### Local Development Setup
```bash
# 1. Set up environment variables
cp .env.example .env  # or create .env with required vars (see CREDENTIALS.md)

# 2. Run tests
python -m pytest tests/

# 3. Health check
python scripts/health_check.py
```

### Environment Variables
See `CREDENTIALS.md` for a complete list of required env vars:
- `GROK_API_KEY` (xAI chat backend)
- `GHL_API_KEY` + `GHL_LOCATION_ID` (GoHighLevel sync)
- `RETELL_WEBHOOK_SECRET` (Retell voice webhooks)
- `BOOK_API_KEY` (internal booking endpoint auth)
- `WEBSTAFFR_DB_PATH` or `DATABASE_URL` (database)

## Folder Structure

- **`/webstaffr`** — Core backend: Angel worker, integrations, database, routers
- **`/tests`** — Test suite (191 tests, all passing)
- **`/scripts`** — Utilities: health_check.py, migrations
- **`/integrations`** — Third-party: social_media, workflow_graph, servicetitan
- **`/docs`** — Architecture and reference docs
- **`/.github`** — CI/CD workflows

## Key Entry Points

- **Main app**: `webstaffr/workers/angel/router.py` (FastAPI app)
- **CLI entry**: `index.py` (startup point)
- **Tests**: `python -m pytest tests/` (run all, or target a module)
- **Health check**: `python scripts/health_check.py` (8 checks: imports, workflows, tenant isolation, etc.)

## Repository Rules & Process

See `CLAUDE.md` for:
- Founder's role and approval boundaries
- Engineering invariants (tenant scoping, auth, CORS, secrets)
- Token efficiency rules
- Self-approval scope vs. founder approval required

## Current Status

- **Code**: 191/191 tests passing, health_check HEALTHY
- **Backend**: Complete (Angel, GHL, Retell wiring)
- **Voice**: Code-complete, unit-tested; pending live call test
- **Site Builder**: Delegated to Lovable; not yet published
- **Deployment**: Not yet configured (awaiting hosting decision)

## Next Steps

See `TASKS.md` for live work status and `DEPLOYMENT_CHECKLIST.md` for pre-launch criteria.

## Documentation

- `PROJECT.md` — Pointer to canonical product spec
- `CLAUDE.md` — Process, scope, engineering rules
- `CREDENTIALS.md` — Env var reference, security baseline
- `TASKS.md` — Live work status, decisions log
- `DEPLOYMENT_CHECKLIST.md` — Launch gate criteria
