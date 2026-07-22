# API.md

Endpoint reference, generated from the actual router code. If this doc and
a router disagree, the router is right.

All routes are mounted into one FastAPI app via `create_app()` in
`webstaffr/workers/angel/router.py`.

## CORS scoping

A custom `ScopedCORSMiddleware` (not FastAPI's built-in `CORSMiddleware`)
adds `Access-Control-Allow-Origin: *` only to: `/chat`, `/intake` (exact
matches), and anything prefixed with `/intake/presets`, `/sites/`, or
`/tenants/`. Every other route below carries **no CORS headers** --
listed explicitly per route.

## `router.py`

### `GET /health`
Liveness check. No DB touch. Auth: none. CORS: not scoped.
Response: `{"status": "ok"}`

### `POST /v1/audio/speech`
Only mounted if `KOKORO_TTS_URL` is set. Proxies an OpenAI-compatible TTS
request to an external Kokoro backend. Auth: none. CORS: not scoped.

### `POST /integrations/servicetitan/poll`
Only mounted if `SERVICETITAN_ENABLED=true`. Bounded read-only poll of
ServiceTitan resources. Auth: none. CORS: not scoped.
Response: `{"results": [...]}` with per-resource fetch/fail counts.

### `POST /chat`
Angel chat turn, called from the widget on a generated customer site.
Auth: none (protected by rate limiting instead). CORS: **scoped** (exact path).

Request (`ChatRequest`):
```json
{"tenant_id": "string", "message": "string (max 4000 chars)", "session_id": "string, optional"}
```
Response (`ChatResponse`): `{"reply": "string"}`

Rate-limited (see rate limiting section below). Oversized `message` is
rejected by pydantic with `422` before Angel/Grok is ever called.

### `POST /book`
Direct appointment booking, no conversation turn required. Auth: `X-API-Key`
header checked against `BOOK_API_KEY` env var -- `401` if configured and
mismatched; **open (no auth) if `BOOK_API_KEY` is unset**. CORS: not scoped.

Request (`BookAppointmentRequest`):
```json
{
  "tenant_id": "string",
  "contact_name": "string",
  "starts_at": "ISO 8601 string",
  "contact_phone": "string, optional",
  "contact_email": "string, optional",
  "notes": "string, optional",
  "sync_to_ghl": true,
  "ghl_contact_id": "string, optional"
}
```
Response (`BookAppointmentResponse`):
```json
{"appointment_id": 0, "tenant_id": "string", "contact_name": "string", "starts_at": "string", "ghl_synced": true}
```

### `POST /webhooks/ghl`
GoHighLevel webhook (website_lead / missed_call event) that starts an
Angel session. Auth: `X-Webhook-Secret` header checked against
`GHL_WEBHOOK_SECRET` env var -- `401` if configured and mismatched;
**open if unset**. CORS: not scoped.

Request (`GHLWebhookEvent`):
```json
{"tenant_id": "string", "event_type": "string", "contact_id": "string, optional", "contact_name": "string, optional", "message": "string, optional (max 4000 chars)"}
```
Response: `{"status": "handled", "reply": "string"}`

### Rate limiting (`/chat`, `/webhooks/ghl`)
Both call `check_and_increment(conn, tenant_id, endpoint)` before
processing. Over the limit → `429`, but the counter still increments (a
rejected request still "uses" its window slot). Fixed-window, not
sliding-window/token-bucket -- see DECISIONS.md for the tradeoff this
accepts.

## `retell_router.py` (mounted at prefix `/retell`)

Auth on both routes below: HMAC-SHA256 signature via the `x-retell-signature`
header, verified against `RETELL_WEBHOOK_SECRET`. `401` on a bad signature;
**accepts everything if `RETELL_WEBHOOK_SECRET` is unset.** CORS: not scoped
on either (server-to-server only).

### `POST /retell/webhook`
Call lifecycle events (`call_started`, `call_ended`, etc.). Logs
attribution `call_events` rows; logs a GHL note on call end if a summary
and contact ID are present.

Response: `{"status": "received"}` or `{"status": "ignored", "reason": "..."}`

### `POST /retell/function-call`
Mid-call tool invocation: `book_appointment`, `escalate_to_human`,
`get_availability`. Always returns `200`, even on internal failure --
degrades to a spoken fallback line rather than erroring the live call.

Response (`FunctionCallResult`): `{"result": "string"}`

Voice-booked appointments use `sync_to_ghl=False` (a fresh phone caller
has no existing GHL contact ID yet -- contact lookup/creation isn't
built). Tenant resolution is via `metadata.tenant_id` set by hand in each
tenant's Retell dashboard agent config, echoed back on every payload --
there is no phone-number-to-tenant lookup table.

## `intake_router.py`

### `POST /intake`
Submits the client intake form; creates the tenant and an idempotent
tracking number. Auth: none. CORS: **scoped** (exact path).

Request (`IntakeRequest`) -- required fields: `biz_name`, `phone`,
`email`, `industry`, `service_area`, `tagline`, `differentiator`,
`services` (list of strings), `license_number`, `plan`, `lead_routing`,
`approver`. Full field set mirrors `intake_submissions` -- see
DATABASE.md.

Response (`IntakeResponse`):
```json
{"submission_id": 0, "tenant_id": "string", "biz_name": "string", "industry": "string", "plan": "string"}
```

### `GET /intake/presets`
Lists supported industries. Auth: none. CORS: **scoped** (prefix match).
Response: `{"industries": [...]}`

### `GET /intake/presets/{industry}`
Per-trade hint text and field-service-management software options. Auth:
none. CORS: **scoped** (prefix match). Always resolves (falls back to
`'Other'` for an unrecognized industry).

## `site_router.py`

### `GET /sites/{tenant_id}`
Public site data consumed by the Lovable-hosted customer site frontend.
Auth: none. CORS: **scoped** (prefix match).

Response: curated projection from `build_public_site_data()`. Internal
fields (`lead_routing`, `approver`, `competitors`, `license_number`,
`notes`, and others) are never included; optional-but-empty fields are
omitted from the response entirely rather than sent as `null` (see the
"no fabrication" principle in DECISIONS.md).

`404` is returned identically for an invalid `tenant_id` shape and a
valid-shape-but-no-submission-yet tenant -- a public endpoint shouldn't
leak which tenant IDs are real. `503` on a database connection failure.

## `attribution_router.py`

Read-only by design. Writes to `call_events`/`tracking_numbers` only
happen in-process, from `intake_router.py` and `retell_router.py`, which
already hold an open tenant-resolved connection -- there is no public
ingestion endpoint for call events. All three routes below: auth none,
CORS **scoped** (`/tenants/` prefix). All return a non-leaking `404` on
invalid `tenant_id` shape, matching `site_router.py`'s pattern.

### `GET /tenants/{tenant_id}/tracking-number`
Response: `{"tenant_id": "string", "tracking_number": "string"}`

### `GET /tenants/{tenant_id}/metrics`
Response: aggregated call metrics, from `CallEventRepository.metrics_for_tenant()`.

### `GET /tenants/{tenant_id}/calls?limit=50`
`limit` is capped to `[1, 200]`.
Response:
```json
{"tenant_id": "string", "calls": [{"event_id": 0, "event_type": "string", "call_id": "string", "duration_seconds": 0, "outcome": "string", "created_at": "string"}]}
```

## Auth summary (quick reference)

| Route | Auth mechanism | Fails open if unconfigured? |
|---|---|---|
| `/chat`, `/intake*`, `/sites/*`, `/tenants/*` | none (public by design) | n/a |
| `/book` | `X-API-Key` vs `BOOK_API_KEY` | yes |
| `/webhooks/ghl` | `X-Webhook-Secret` vs `GHL_WEBHOOK_SECRET` | yes |
| `/retell/*` | HMAC signature vs `RETELL_WEBHOOK_SECRET` | yes |

"Fails open" is a documented, deliberate default (matches this repo's
Null-object pattern for every other integration) -- it means an
unconfigured deployment behaves exactly as it did before auth was added,
and the gap only actually closes once the relevant secret is set as a
real value. See CREDENTIALS.md for how to set each one.
