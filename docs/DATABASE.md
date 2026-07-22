# DATABASE.md

Schema reference, generated from the actual migration files in
`webstaffr/migrations/`. If this doc and a migration file disagree, the
migration file is right.

Two backends run the same schema: SQLite locally/in tests (default, no
config needed), Postgres/Supabase in whichever deployment has
`DATABASE_URL` set. See `docs/ARCHITECTURE.md`'s persistence section for
how `db.py` bridges the dialect difference. `migrate()` only ever runs
against SQLite -- the live Postgres schema is applied out-of-band, using
the hand-translated files in `webstaffr/migrations/postgres_manual/`.

## `tenants` (`0001_initial.sql`)

| Column | Type | Notes |
|---|---|---|
| `tenant_id` | TEXT | PRIMARY KEY |

The root of tenant isolation. Every other table either references this
directly via FK or scopes its queries by `tenant_id` in application code.
`tenant_id` is public -- never treated as a credential anywhere in this
codebase.

## `workflow_definitions` (`0001_initial.sql`)

| Column | Type | Notes |
|---|---|---|
| `tenant_id` | TEXT | NOT NULL, FK → `tenants(tenant_id)`, part of composite PK |
| `workflow_id` | TEXT | NOT NULL, part of composite PK |
| `step_names` | TEXT | NOT NULL, JSON array of step names in execution order |
| `created_at` | TEXT | NOT NULL |

PRIMARY KEY: `(tenant_id, workflow_id)`. Index: `idx_workflow_definitions_tenant`.

Step *functions* are never stored here, only their names -- see
ARCHITECTURE.md. Under Postgres, saves to this table use a hand-written
`ON CONFLICT (tenant_id, workflow_id) DO UPDATE` (the one non-generic
dialect translation in `db.py`), not the generic `INSERT OR IGNORE`
rewrite.

## `execution_records` (`0001_initial.sql`)

| Column | Type | Notes |
|---|---|---|
| `execution_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `tenant_id` | TEXT | NOT NULL |
| `workflow_id` | TEXT | NOT NULL |
| `status` | TEXT | NOT NULL |
| `started_at` | REAL | NOT NULL |
| `finished_at` | REAL | nullable |
| `steps_json` | TEXT | NOT NULL, JSON array of per-step traces |

FK: `(tenant_id, workflow_id) → workflow_definitions(tenant_id, workflow_id)`.
Indexes: `idx_execution_records_tenant`, `idx_execution_records_tenant_workflow`.

Full reconstructable trace of one `WorkflowExecutor.run()` call.

## `appointments` (`0002_angel_appointments.sql`)

| Column | Type | Notes |
|---|---|---|
| `appointment_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `tenant_id` | TEXT | NOT NULL, FK → `tenants(tenant_id)` |
| `contact_name` | TEXT | NOT NULL |
| `contact_phone` | TEXT | nullable |
| `contact_email` | TEXT | nullable |
| `starts_at` | TEXT | NOT NULL, ISO 8601 |
| `notes` | TEXT | nullable |
| `source` | TEXT | NOT NULL, DEFAULT `'angel'` |
| `ghl_synced` | INTEGER | NOT NULL, DEFAULT `0` (0/1 boolean) |
| `created_at` | TEXT | NOT NULL |

Index: `idx_appointments_tenant`. Created via `POST /book` or Angel's
`book_appointment` flow (chat or Retell function-call).

## `intake_submissions` (`0003_intake_submissions.sql`)

The 9-section intake form, ported from the legacy `webstaff` repo's
proven schema. Same fields for every industry -- per-trade variation is
presentation-only (`trade_presets.py`), not a schema difference.

| Column | Type | Notes |
|---|---|---|
| `submission_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `tenant_id` | TEXT | NOT NULL, FK → `tenants(tenant_id)` |
| `biz_name` | TEXT | NOT NULL |
| `phone` | TEXT | NOT NULL |
| `email` | TEXT | NOT NULL |
| `industry` | TEXT | NOT NULL |
| `service_area` | TEXT | NOT NULL |
| `years_in_biz` | INTEGER | |
| `emergency_service` | TEXT | 'Yes'/'No' |
| `has_site`, `site_url`, `site_platform`, `site_issues` | TEXT | Web presence |
| `has_gbp`, `gbp_url`, `google_review_link` | TEXT | Google Business Profile |
| `has_logo`, `brand_colors`, `brand_words`, `inspo_sites` | TEXT | Brand |
| `tagline` | TEXT | NOT NULL |
| `differentiator` | TEXT | NOT NULL |
| `competitors` | TEXT | **internal-only, never exposed publicly** |
| `tone` | TEXT | |
| `services_json` | TEXT | NOT NULL, JSON array |
| `pricing_shown`, `promos` | TEXT | |
| `license_number` | TEXT | NOT NULL in schema; **internal-only as of 2026-07-08, never exposed publicly** (founder decision -- see DECISIONS.md) |
| `rating_value` | REAL | |
| `review_count` | INTEGER | |
| `certifications`, `has_before_after`, `testimonials` | TEXT | |
| `facebook_url`, `instagram_url`, `fsm_system`, `booking_system` | TEXT | |
| `plan` | TEXT | NOT NULL, `'essentials'\|'growth'\|'pro'` |
| `lead_routing` | TEXT | NOT NULL, **internal-only** |
| `timeline` | TEXT | **internal-only** |
| `approver` | TEXT | NOT NULL, **internal-only** |
| `assets_status`, `keywords`, `extra_pages` | TEXT | |
| `notes` | TEXT | **internal-only** |
| `created_at` | TEXT | NOT NULL |

Index: `idx_intake_submissions_tenant`.

**Internal-only fields are a hard rule, not a suggestion**: `competitors`,
`license_number`, `lead_routing`, `timeline`, `approver`, and `notes` must
never appear in `site_data.py`'s public projection. A `competitors` leak
and a `license_number` inclusion were both found and fixed in WS3.0's
history (see DECISIONS.md) -- any future change to the public site-data
shape must re-check this list, not just re-derive it from the schema.

## `rate_limit_counters` (`0005_rate_limit_counters.sql`)

| Column | Type | Notes |
|---|---|---|
| `tenant_id` | TEXT | NOT NULL, part of composite PK |
| `endpoint` | TEXT | NOT NULL, part of composite PK |
| `window_start` | INTEGER | NOT NULL, unix timestamp floored to window size, part of composite PK |
| `request_count` | INTEGER | NOT NULL, DEFAULT `0` |

PRIMARY KEY: `(tenant_id, endpoint, window_start)`.

**Deliberately has no FK to `tenants`.** Rate limiting must work against a
guessed or never-registered `tenant_id` -- that's precisely the abuse
case it defends against, so a FK that could reject the write would
defeat the purpose.

## `tracking_numbers` (`0006_attribution.sql`)

| Column | Type | Notes |
|---|---|---|
| `tenant_id` | TEXT | PRIMARY KEY, FK → `tenants(tenant_id)` |
| `tracking_number` | TEXT | NOT NULL, UNIQUE |
| `created_at` | TEXT | NOT NULL |

`tracking_number` is a **logical identifier** (`trk_<tenant>_<random>`),
not a real phone number -- no DID has been provisioned yet. Created
idempotently on first successful `POST /intake` per tenant.

## `call_events` (`0006_attribution.sql`)

| Column | Type | Notes |
|---|---|---|
| `event_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `tenant_id` | TEXT | NOT NULL, FK → `tenants(tenant_id)` |
| `tracking_number` | TEXT | nullable |
| `call_id` | TEXT | nullable, external (Retell) call ID for correlating rows about the same call |
| `event_type` | TEXT | NOT NULL, `'call_received'\|'call_ended'\|'appointment_booked'` |
| `duration_seconds` | INTEGER | |
| `outcome` | TEXT | e.g. `'answered'`, `'voicemail'`, `'booked'`, `'escalated'` |
| `metadata_json` | TEXT | |
| `created_at` | TEXT | NOT NULL |

Indexes: `idx_call_events_tenant`, `idx_call_events_tenant_created`.
Append-only log. Written only by in-process callers (`intake_router.py`,
`retell_router.py`) that already hold an open, tenant-resolved
connection -- deliberately no public write endpoint, to avoid repeating
the unauthenticated-write-surface issue `/book` and `/webhooks/ghl` once
had (see DECISIONS.md).

## Postgres-only files (`webstaffr/migrations/postgres_manual/`)

Not run by the app's `migrate()` -- applied manually against the live
Supabase project. Live outside the main migrations directory specifically
so `migrate()`'s non-recursive glob never picks them up (they use
Postgres-only syntax that would break every local SQLite run and the
full test suite).

- **`0004_enable_rls_default_deny.sql`** -- `ENABLE ROW LEVEL SECURITY`
  on all 5 original tables, no policies (default-deny). A
  *reconstruction*, not a retrieval -- Supabase's migration history API
  doesn't return the original SQL body, so this file was rewritten and
  then verified against live `pg_tables`/`pg_policies` state before being
  committed. Nothing in this codebase uses PostgREST/anon-key access
  today (the backend connects via a direct Postgres connection, which
  bypasses RLS regardless of policy) -- RLS is a defense against a
  future client-side integration, not a currently-exploitable gap being
  closed.
- **`0005_rate_limit_counters.sql`**, **`0006_attribution.sql`** --
  Postgres-dialect twins of the SQLite files above (`GENERATED ALWAYS AS
  IDENTITY` instead of `AUTOINCREMENT`).

## Migration numbering

There is no `0004` file in the main `webstaffr/migrations/` directory --
that version number belongs to the RLS migration, which lives in
`postgres_manual/` instead (see above). This is intentional, not a gap to
fill.
