# WebStaffr 3.3 / SMM Integration Plan

This plan is grounded in the actual code read so far, not in assumed architecture. The integration boundary is the WS3.3 intake/node flow, not GHL.

## Actual boundary found

- WS3.3 uses bare public tenant ids in `tenant.py`
- WS3.3 intake generates a tenant id from business name and stores intake submissions
- SMM uses Clerk JWT with `org_id` claims
- There is currently no SMM-facing route, queue, or webhook in WS3.3

This means integration requires an explicit tenant/bridge mapping. Do not paper over it with shared-secret hacks.

## Chosen direction

Add a deliberate integration seam in WS3.3 rather than retrofitting Clerk into WS3.3’s current local tenant flow. That keeps each system’s identity model intact.

## Proposed schema and API contract

### POST /integrations/social-media-marketing/mount

Request body:
```json
{
  "tenant_id": "acme-hvac",
  "social_tenant_id": "org_ABC",
  "platforms": ["facebook", "instagram"],
  "default_brand_id": "00000000-0000-0000-0000-000000000000",
  "mode": "agent_managed"
}
```

Response: `204` with `Location: /integrations/social-media-marketing/mount/{mount_id}`

Rules:
- `tenant_id` must already exist in WS3.3 intake records
- `social_tenant_id` is the SMM org/Clerk identity and must match the
  authenticated caller's org — the server rejects mismatches
- `mode` controls whether the SMM agent can act unattended or requires approval
- `platforms` must use valid `PlatformName` values (`linkedin`, `facebook`,
  `instagram`, `x`, `threads`, `tiktok`, `pinterest`, `youtube`,
  `google_business`); `"meta"` is not valid and will not match any adapter

### POST /integrations/social-media-marketing/mount/{mount_id}/intent

Request body:
```json
{
  "campaign_intent": {
    "objective": "bookings",
    "budget_cents": 50000,
    "platforms": ["facebook", "instagram"],
    "start": "2026-08-01",
    "end": "2026-08-31",
    "brand_id": "00000000-0000-0000-0000-000000000000"
  },
  "post_draft": {
    "headline": "Phoenix HVAC checkup special",
    "body": "...",
    "media_refs": []
  }
}
```

Response:
```json
{
  "status": "pending_review",
  "workflow_instance_id": "wf_123",
  "approval_url": "/approvals/wf_123"
}
```

Notes:
- `brand_id` must be a real SMM brand UUID, not a slug. The server looks it
  up org-scoped and returns `404` if it does not belong to the caller's org.
- `platforms` must use valid `PlatformName` values; unknown values are
  rejected before any rows are created.

This makes WS3.3 the source of truth for workflows/approvals, while SMM owns creative and platform execution.

## Backend review requirements

Before wiring anything, review `backend/app/main.py`, `backend/app/core/auth.py`, `backend/app/db.py`, and `backend/app/workers/tasks/publish_tasks.py` for these known bad patterns:
- global mutable state in `main.py` or router startup
- DB sessions or connections held open across requests
- Celery tasks that swallow exceptions or skip tenant scoping
- auth checks that rely on headers instead of verified bearer tokens

## Retained graph model

A retained workflow graph is required after every session or campaign change:
- node id
- node type: `intake`, `campaign`, `post`, `publish_job`, `approval`, `integration_event`
- status
- parent/workflow instance id
- tenant id
- created_at
- completed_at or failure reason

This replaces in-memory session state and makes recovery deterministic.

## Sub-blocks

Delegate the above as four scoped blocks. See `SUBAGENTS.md`.
