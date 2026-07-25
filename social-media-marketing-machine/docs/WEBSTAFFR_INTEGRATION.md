# WebStaffr Integration Contract

## What this document is

SMM (Social Media Marketing Machine) is positioned as WebStaffr's social
media manager agent, not a standalone SaaS product — see `README.md`'s
status line and `docs/ARCHITECTURE.md`. This document states, honestly,
what that means in code today versus what it will require to actually be
true. As of commit `26a07f1`, **there is live bridge code** between this repo and
WebStaffr (`WebStaffr 3.3`, at `/Users/doc/Desktop/WebStaffr3.3`), but the
two systems are not yet wired over HTTP. The intake contract is implemented
in this repo at `backend/app/routers/integrations.py` and
`backend/app/services/integration_service.py`, and the resulting WS3.3 seam
is at `webstaffr/integrations/social_media/*`. The contract has known
mismatches that must be resolved before going over the network: `mount_id`
is UUID here and `int` in WS3.3; `brand_id`/`default_brand_id` are UUID FKs
here and slugs in WS3.3's current plan JSON; WS3.3 currently sends
`"platforms": ["meta"]`, but `"meta"` is not a valid `PlatformName` member.
SMM also requires a service-to-service auth decision: it uses Clerk JWTs
with `org_id`, while WS3.3 has no Clerk identity. Do not retrofit Clerk
into WS3.3 and do not paper over this with a shared secret.

## The core mismatch: two incompatible tenant/identity models

This is the most important fact in this document — everything else
follows from it.

**SMM's tenant model:** every tenant-scoped table carries an indexed
`organization_id` foreign key resolved from a verified **Clerk JWT**
(`backend/app/core/auth.py`). A request is only ever scoped to an
organization because Clerk issued a session token containing an `org_id`
claim. There is no other way into a tenant-scoped endpoint — see the
`401`s returned by `/api/v1/clients` and `/api/v1/agents` with no bearer
token, confirmed directly against a live server this session.

**WS3.3's tenant model:** `webstaffr/tenant.py`'s `Tenant` is a bare
string identifier (`tenant_id`), validated only for character shape
(1-64 chars, `[a-zA-Z0-9_-]`). Per WS3.3's own `docs/DECISIONS.md`
(ADR-003), `tenant_id` is **deliberately public, never a credential** —
it appears directly in URLs (`/sites/{tenant_id}`), and authorization on
the few routes that need it is a separate shared-secret header
(`X-API-Key`, `X-Webhook-Secret`), not tied to any user-identity system.
WS3.3 has no Clerk integration, no JWT verification, and no concept of
an "organization" — it has flat `tenant_id` strings tied to a WS3.3-side
`intake_submissions` row.

**Consequence:** an `organization_id` in SMM and a `tenant_id` in WS3.3
are not the same kind of thing and cannot be compared, joined, or mapped
1:1 without a new piece of state recording that mapping. Neither
codebase currently has that mapping. Any integration design has to start
by answering: when a WS3.3 tenant needs an SMM organization, who creates
it, and where does the `tenant_id ↔ organization_id` pairing live?

## What actually exists today

- **SMM exposes bridge endpoints, but nothing calls them at runtime.** No
  shared network calls are currently in flight between the two systems at
  runtime. WS3.3 does not yet call SMM's bridge routes, and SMM does not
  call back into WS3.3. Confirmed by inspection: WS3.3's router/service
  layers do not reference SMM URLs, env vars, or identifiers, and SMM's
  bridge endpoints exist but are not wired into any active call path yet.
  The remaining gaps are contract alignment (`mount_id`, `brand_id`,
  `platforms`) and a service-to-service auth decision.
- **SMM's API surface is real and documented** — see `docs/API.md`-style
  detail already covered by the live `openapi.json` (15 router files,
  32 paths, auto-served at `/docs` when the backend is running). Every
  tenant-scoped route requires a Clerk bearer token.
- **The WS3.3 integration bridge exists as code, but is not yet live over
  HTTP.** `POST /integrations/social-media-marketing/mount` and
  `POST /integrations/social-media-marketing/mount/{mount_id}/intent` are
  implemented in this repo and create Campaign → Post(s) → PostVersion v1
  → PENDING Approval → execution graph + audit row in one transaction.
  The remaining gap is network wiring plus contract/auth alignment with
  WS3.3.
- **WS3.3's API surface is real and documented** — see WS3.3's own
  `docs/API.md`. Every route requires either nothing (public-by-design,
  matching WS3.3's ADR-003/ADR-004), a shared-secret header, or (for
  `/retell/*`) an HMAC signature.
- **Both are independently deployable and independently correct** for
  what they each already do — this isn't a "one is broken" situation,
  it's a "they were never wired together" situation.

## What a real integration would require (not yet built, not yet decided)

These are the open design questions, listed so a future session doesn't
have to rediscover them from scratch. None of the following exists in
either codebase yet:

1. **Identity bridging.** Something needs to map a WS3.3 `tenant_id` to
   an SMM `organization_id` (and, likely, a Clerk user/service-account
   that can obtain a JWT scoped to that org). The cleanest fit with
   WS3.3's existing patterns (per its ADR-002, Protocol + Null-object +
   real-impl for every integration) would be a new `SMMClient` Protocol
   in WS3.3 with a real implementation that authenticates as a
   service-level Clerk identity — not per-end-customer Clerk accounts,
   since WS3.3's actual customers (HVAC business owners) have no reason
   to ever see or use Clerk directly.
2. **Direction of the call.** Two plausible shapes, not decided:
   - WS3.3 calls SMM (e.g., after intake, WS3.3 provisions an SMM
     organization + a starter campaign) — fits WS3.3's existing
     in-process-caller-only pattern for sensitive writes (ADR-007), but
     requires SMM to expose a machine-to-machine auth path that isn't
     Clerk-session-based, which doesn't exist today (SMM's only auth
     path is a Clerk JWT — there's no API-key/service-account mode).
   - SMM calls WS3.3 (e.g., to look up a tenant's brand voice, business
     details, or attribution data via WS3.3's existing `/sites/{tenant_id}`
     or `/tenants/{tenant_id}/*` public/scoped endpoints) — more
     naturally fits WS3.3's existing public-data-projection pattern, but
     would need SMM's `AIProvider`/prompt-template layer to actually
     consume that data, which no code currently does.
   - Realistically, a working integration likely needs both directions
     eventually. Neither is built.
3. **A shared or bridged auth mechanism.** SMM would need a way to
   authenticate WS3.3 as a caller without a human Clerk session — Clerk
   supports machine-to-machine tokens/service accounts, but this
   codebase's `auth.py` only implements the user-JWT path. This is real,
   scoped work, not a config change.
4. **Data ownership boundaries.** Which system is the source of truth
   for brand voice/tone, business description, and service area — WS3.3
   already collects this at intake (`intake_submissions`) and projects a
   public subset (`site_data.py`). SMM has its own `Brand` model
   (`backend/app/models/brand.py`) with an unrelated schema. Duplicating
   this by hand invites drift; a decision is needed on which system owns
   it and how the other reads it (sync job vs. live call vs. one-time
   copy at provisioning).
5. **Where campaign/post approval surfaces to the actual customer.**
   SMM's approval workflow (Draft → Internal Review → Client Review →
   ...) assumes a "client" role reviewing content inside SMM's own
   frontend. It's not yet decided whether WS3.3's end customers ever see
   SMM's UI directly, or whether approval happens through a WS3.3-owned
   surface that calls SMM's approval endpoints on the customer's behalf.

## What NOT to assume

- Do not assume `organization_id == tenant_id` anywhere in either
  codebase — no code currently enforces or even suggests this, and doing
  so silently (e.g., passing a WS3.3 `tenant_id` string as if it were a
  Clerk `org_id`) would fail the moment SMM tries to verify a JWT that
  was never actually issued by Clerk for that string.
- Do not assume WS3.3's end customers have or need Clerk accounts. Per
  WS3.3's own `docs/DECISIONS.md`, its entire customer-facing surface
  (Lovable-hosted sites, the Angel voice/chat widget) is intentionally
  Clerk-free and low-friction. Any integration should keep Clerk on the
  SMM/internal-operator side, not push it onto WS3.3's actual customers.
- Do not assume this document describes a plan that's been approved —
  it describes options and open questions only. The actual approach is
  a product/architecture decision for the founder, consistent with both
  repos' stated decision-escalation rules (WS3.3's `CLAUDE.md` Founder's
  Role section; this repo has no equivalent document yet).

## Verification note

Every concrete claim above (Clerk-only auth in SMM, bare-string
`tenant_id` in WS3.3, no cross-references between the two codebases) was
checked directly against the current code on 2026-07-23, not inferred
from either repo's documentation. If this file is read in a future
session, re-verify before trusting it — both repos change quickly and
this doc will go stale the same way `BUILD_REPORT.md` and `README.md`
did (see their 2026-07-23 correction sections for what that looked like
in practice).
