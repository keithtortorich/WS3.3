# Subagents

Scoped work blocks for Claude to execute in order. Each block is independent and has clear completion criteria.

## Block 1: WS3.3 Backend Review and Patch

**Input:** `WEBSTAFFR_BACKEND_REVIEW.md`, WS3.3 repo at `/Users/doc/Desktop/WebStaffr3.3/webstaffr/`
**Output:** Patched `main.py`, `auth.py`, `db.py`, `publish_tasks.py` with fixes applied, tests passing
**Acceptance:**
- No module-level mutable state in `main.py` or router startup
- Every DB connection is request-scoped with explicit `finally: conn.close()`
- Every Celery task accepts `tenant_id` as first arg, stays tenant-scoped, logs outcome, and re-raises after bounded retries
- All routers use `Depends(get_current_org)` directly, no custom auth parsing in route handlers
- `pytest` passes with no regressions

## Block 2: Integration Bridge Endpoints

**Input:** `INTEGRATION_PLAN.md`, patched WS3.3 backend from Block 1
**Output:** New `integrations/social-media-marketing/` router with mount and intent endpoints
**Acceptance:**
- `POST /integrations/social-media-marketing/mount` returns 204 with Location header
- `POST /integrations/social-media-marketing/mount/{mount_id}/intent` returns pending_review with workflow_instance_id
- Both endpoints are tenant-scoped, auth-gated, and reject requests for unknown tenant_ids
- Tests cover happy path, auth failure, and missing tenant

## Block 3: Retained Graph Model

**Input:** `RETAINED_GRAPH_MODEL.md`, patched WS3.3 backend from Block 1
**Output:** New `workflow_nodes` table, repository, and router endpoints for graph operations
**Acceptance:**
- Migration applied to both SQLite and Postgres test environments
- Root node written on campaign creation, child nodes on publish/approval/integration events
- Status transitions are atomic with business-logic writes
- Tests cover node creation, status updates, and parent-child linkage

## Block 4: TASKS.md Update and Completion Criteria

**Input:** All completed blocks above, current `TASKS.md` from WS3.3 repo
**Output:** Updated `TASKS.md` with new tasks #35–#38, completion dates, and verification evidence
**Acceptance:**
- Each new task has a clear "done" definition with test count and health check status
- No vague language; every claim is backed by a test or health check result
- Format matches existing TASKS.md style
