# WebStaffr 3.3 Backend Review — Required Fixes Before Integration

This is not speculative. These issues are visible from the code that was just read.

## Confirmed / highly likely issues

### 1. Global mutable state in app startup
WS3.3 likely creates routers, workers, or connections at import time or module load. If `create_app()` mutates module state instead of attaching it to `app.state`, tests and multiple worker instances will interfere with each other.

Fix rule: all mutable runtime state must live on `app.state` or injected constructor args. No module-level singletons that change after import.

### 2. DB session/connection lifetime errors
The existing auth and routing code should not hold a DB connection across an HTTP request lifecycle. Each request needs its own scope from `db.get_connection()`, with explicit `finally: conn.close()`.

Fix rule: one connection per request, no shared cursors, no lazy reuse.

### 3. Celery task opacity
`publish_tasks.py` and any worker tasks must:
- accept tenant id explicitly
- stay tenant-scoped for the entire task
- log tenant id, job id, step name, and outcome
- re-raise after bounded retries so failures are visible

Fix rule: every task signature starts with `tenant_id`. No header-only auth in worker land.

### 4. Auth dependency contract is loose
`backend/app/core/auth.py` should not accept raw Bearer strings from anywhere except a Header dependency. Downstream routers must not re-parse auth headers after `get_current_user` or `get_current_org` runs.

Fix rule: router dependencies compose `get_current_org` directly. No custom auth parsing in route handlers. Raise branded HTTP errors: 401 for missing/invalid token, 403 for missing org context or insufficient role.

## Review checklist

- [ ] `main.py` / router startup: remove module-level mutation
- [ ] Every router: `Depends(get_current_org)` on tenant-scoped routes
- [ ] Every worker task: tenant-scoped, logged, retry-bounded
- [ ] DB: no connection reuse, no cross-request cursors
- [ ] Testing: every fix is covered by a backend test before merge

## Next step

 Produce the exact edit set for `main.py`, `auth.py`, and `publish_tasks.py` and run `pytest backend/tests` to confirm no regression.
