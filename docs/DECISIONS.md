# DECISIONS.md

Architectural decisions actually made in this codebase's history, with
real reasoning and real consequences -- not a hypothetical ADR template.
Sourced from WebStaffr 3.0's `CLAUDE.md` session addenda (2026-07-05
through 2026-07-19), migrated forward because the decisions and their
reasoning still apply to this repo's code, even though the coordination
process that produced them is not being carried forward.

New decisions belong at the bottom, dated, in the same format. Don't
rewrite history here -- if a decision is later reversed, add a new entry
that says so and link back to the one it reverses.

---

## ADR-001: Raw SQL over an ORM

**Decision**: Every repository and route handler is written against a
`sqlite3.Connection`-shaped interface using raw SQL (`?` placeholders),
with a hand-written translation shim (`db.py`) making the identical SQL
text work against Postgres too. No SQLAlchemy, no ORM, anywhere.

**Why**: Established early and never revisited because it's kept working.
An ORM would need its own dialect-abstraction layer anyway to support
both SQLite (dev/test) and Postgres (production) -- writing the
translation shim once, by hand, in one file (`db.py`), is simpler than
adopting a general-purpose ORM and configuring it for the same dual-backend
requirement.

**Consequences**: SQL is visible and auditable at every call site, at the
cost of writing dialect-aware code by hand instead of relying on a
library to handle it. `db.py`'s shim is deliberately narrow -- it
translates only the specific SQL patterns this codebase actually uses
(`INSERT OR IGNORE`, one hardcoded `INSERT OR REPLACE`, `PRAGMA`,
`RETURNING`-injection for lastrowid emulation), not general SQLite-to-Postgres
translation. Adding a new query pattern that needs dialect translation
means updating `db.py`, not just writing the query.

## ADR-002: Protocol + Null-object + real-implementation for every integration

**Decision**: Every external dependency (voice/AI backend, CRM, webhook
signature verification, shared-secret auth) is defined as a `Protocol`,
with a `Null*` implementation that's always safe to construct and a real
implementation that raises a `*NotConfiguredError` at construction time
if credentials are missing.

**Why**: The app needs to run safely with zero credentials configured --
for local dev, for CI, and for any tenant that hasn't been fully set up
yet. A pattern where "missing credential" means "silent no-op" or
"fabricated success" was rejected in favor of one where it means either
"safe, deterministic default behavior" (the Null object) or "loud failure
at startup" (the real implementation refusing to construct) -- never a
silent partial failure discovered later at request time.

**Consequences**: Adding a new integration means adding all three parts,
not just a client class. Tests exercise the real implementation's logic
by passing an explicit fake credential and mocking only the actual
network call -- no test in this suite makes a real network call, and none
are conditionally skipped based on whether real credentials are present
in the environment.

## ADR-003: `tenant_id` is public, never a credential

**Decision**: `tenant_id` appears in URLs (`/sites/{tenant_id}`,
`/tenants/{tenant_id}/...`) and is treated as a public routing identifier,
never as proof of authorization on its own.

**Why**: Originally, `/book` and `/webhooks/ghl` had no authentication
beyond accepting whatever `tenant_id` was passed in the request --
`CODE_REVIEW.md` (WS3.0) flagged this as a real gap, since a guessable or
enumerable `tenant_id` would let anyone book appointments or trigger
webhook handling for any tenant. Fixed by adding shared-secret auth
(`X-API-Key` / `X-Webhook-Secret` headers) on top, without ever making
`tenant_id` itself secret -- the fix was "add a real credential," not
"make the identifier harder to guess."

**Consequences**: Any new endpoint that accepts a `tenant_id` and
performs a write or exposes non-public data must be evaluated for whether
it needs its own auth, the same way `/book` and `/webhooks/ghl` needed it
added after the fact. `attribution_router.py`'s write path avoided this
problem entirely by not exposing a public write endpoint in the first
place (see ADR-007).

## ADR-004: CORS is scoped per-path, not app-wide

**Decision**: A custom `ScopedCORSMiddleware` adds CORS headers only to
browser-facing routes (`/chat`, `/intake*`, `/sites/*`, `/tenants/*`).
Server-to-server routes (`/book`, `/webhooks/ghl`, `/retell/*`) carry no
CORS headers at all.

**Why**: The original implementation used FastAPI's built-in
`CORSMiddleware` with `allow_origins=["*"]` applied app-wide -- which
meant `/book` and `/webhooks/ghl`, not just the intentionally-public
`/chat`, were callable cross-origin from any website. This was broader
than intended and was caught during a reconciliation pass, not designed
in from the start.

**Consequences**: Any new route needs an explicit decision about whether
it belongs in `_CORS_SCOPED_PATHS`/`_CORS_SCOPED_PREFIXES` -- the default
for a new route is *no* CORS headers, which is safe-by-default for
server-to-server endpoints but must be deliberately added for anything a
browser widget needs to call directly.

## ADR-005: No fabricated content, ever ("perfect-site principle")

**Decision**: The public site-data projection (`site_data.py`) omits a
field entirely when its underlying data is absent, rather than
substituting a placeholder, a default rating, a fake testimonial, or any
other invented content.

**Why**: Ported forward from a data-integrity standard applied to an even
earlier version of this codebase, which caught two real bugs at the
time: a lead-capture form silently posting to a dead route, and three
hardcoded fake testimonials rendered on every generated customer site
regardless of whether the business actually had any. The principle --
never fabricate, omit instead -- outlived that specific incident and
became a standing rule.

**Consequences**: Every change to `build_public_site_data()`'s field set
must re-check which fields are internal-only (see DATABASE.md's
`intake_submissions` table) -- getting this wrong is a privacy leak, not
just a display bug. Two real leaks were caught this way: `competitors`
(an internal field that leaked into the public response, caught by an
onboarding smoke test whose own leak-check list hadn't been updated to
match) and `license_number` (included in every response until a founder
decision on 2026-07-08 removed it -- see ADR-006).

## ADR-006: `license_number` removed from public site data

**Decision**: `license_number` is collected at intake (required field)
but never included in `GET /sites/{tenant_id}`'s response.

**Why**: A founder decision, not a technical necessity -- contractor
license numbers are a common trust signal on real trade-business
websites, but Supabase's own security advisor had already flagged the
`license_number` column as sensitive at the database layer. Given that
signal, the founder chose not to carry the exposure forward to the
application layer too, even though nothing technically required removing
it.

**Consequences**: If a future business need calls for showing license
numbers publicly again, that's a new founder decision to make explicitly,
not a default to silently restore.

## ADR-007: Attribution events are written in-process, not via a public endpoint

**Decision**: `call_events` rows are written only by code that already
holds an open, tenant-resolved database connection (`intake_router.py`,
`retell_router.py`) -- there is no `POST /events` or similar public
ingestion endpoint.

**Why**: Given this repo's own history with `/book` and `/webhooks/ghl`
needing shared-secret auth bolted on after the fact (ADR-003), the
attribution feature avoided repeating that pattern by not adding a new
unauthenticated write surface in the first place, rather than adding one
and then having to secure it later.

**Consequences**: Any future integration that wants to log a call event
from outside this codebase (e.g. a different telephony provider) needs a
real design decision about how it authenticates -- there is no existing
endpoint to simply reuse.

## ADR-008: Retell over native Grok Voice for telephony

**Decision**: Live phone-call voice is built on Retell AI (webhook +
function-call integration), not xAI's native Grok Voice Agent API, even
though Grok is already the vendor used for text chat.

**Why**: Native Grok Voice's SIP integration requires this application's
own backend to hold a live WebSocket connection open for the full
duration of every call. That's incompatible with this app's Vercel
serverless hosting model (see ARCHITECTURE.md) without standing up a
second, always-on service just for voice. Retell (like the
also-considered Vapi) hosts that persistent connection on its own
infrastructure instead, which fits the existing hosting model with no
new infrastructure. Retell was chosen over Vapi specifically because it
bundles telephony (no separate Twilio-style account needed) and has less
operational overhead for a small team, accepting a somewhat higher
per-minute cost as the tradeoff.

**Consequences**: Any future voice-related decision needs to account for
the serverless hosting constraint first -- a vendor that requires a
persistent connection held by *this* backend is disqualified by
construction, not by preference.

## ADR-009: Rate limiting via a DB-backed fixed-window counter, not in-memory or Redis

**Decision**: `/chat` and `/webhooks/ghl` are rate-limited using a
counter table (`rate_limit_counters`) in the existing database, not an
in-process dict and not a dedicated cache/store like Redis or Upstash.

**Why**: Given the serverless hosting model, an in-memory counter would
only be enforced within a single warm function instance -- Vercel's
multiple and cold-started instances would each keep their own counter,
giving no real ceiling on total request volume in production. A
DB-backed counter is correctly shared across every instance without
introducing a new external vendor relationship. A fixed-window
(not sliding-window/token-bucket) algorithm was chosen for simplicity,
accepting that a client could send up to roughly 2x the nominal limit
right at a window boundary -- judged precise enough for the actual risk
being bounded (unbounded billed API usage), not a hard security control.

**Consequences**: The counter table has no automated pruning yet -- a
known, accepted gap, not an oversight. A future high-traffic scenario
might justify moving to a real cache-backed limiter; that would be a new
decision, not an emergency fix, since the current approach was chosen
deliberately with this limitation understood upfront.

## ADR-010: Lovable is the canonical frontend, not the local `frontend/` scaffold

**Decision**: Customer-site generation and the Angel widget embed happen
in a Lovable-hosted project ("Site Weaver"), not the `frontend/`
Vite+React scaffold that existed early in this codebase's history.

**Why**: A pros/cons comparison came down to cost and control favoring
the local scaffold, but widget-embed readiness and hosting favoring
Lovable -- Lovable already had the Angel widget embedded and verified
working end-to-end against real backend data before the local scaffold
had either. Once that was true, continuing to invest in the local
scaffold would have meant maintaining two frontends for the same MVP
flow.

**Consequences**: `frontend/` is out of scope for further work unless
this decision is explicitly reversed -- this repo does not carry a
`frontend/` directory at all (see the migration note in `CLAUDE.md`).
Any new customer-facing site UI work happens in the Lovable project, not
in this repo.

## ADR-011: Attribution was prioritized over an immediate HVAC launch

**Decision**: Given a choice between (a) launching in the HVAC vertical
immediately, (b) building call-attribution/tracking infrastructure first,
or (c) a risk-mitigation pass first, the founder chose attribution first.

**Why**: The reasoning was that a "pays for itself" money-back guarantee
-- part of the intended go-to-market pitch -- needs proof-of-performance
data behind it before the guarantee is made, not retrofitted after
customers are already being told about it.

**Consequences**: `tracking_numbers`/`call_events` (see DATABASE.md) and
the read-only `attribution_router.py` endpoints exist specifically to
support that guarantee, not as generic analytics. `estimated_value_usd`
in the metrics response is explicitly labeled a placeholder
(`appointments_booked × $250`), not a measured figure -- treat it as
provisional until real conversion data replaces the placeholder
multiplier.

---

## 2026-07-22: WS3.3 reset -- Claude-only process, no multi-agent coordination

**Decision**: This repository (WS3.3) starts a fresh process on top of
WS3.0's proven code: Claude-only, no Grok/ChatGPT-advisory coordination
loop, no per-file ownership-header protocol.

**Why**: The multi-agent coordination process around WS3.0's code
generated overhead without corresponding value -- founder-decisions sat
unresolved across sessions, and token spend went into process debate
rather than product work.

**Consequences**: Only proven, tested code and finished copy were
migrated (see `CLAUDE.md`'s 2026-07-22 addendum for the full list and
what was deliberately left behind). This documentation suite itself
(`docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `docs/API.md`, and this
file) was scoped down from an originally-proposed 20-file "engineering
bible" specifically because the full version would have reintroduced the
same category of overhead this reset was meant to remove -- see this
repo's `CLAUDE.md` Token-Efficiency Rules.
