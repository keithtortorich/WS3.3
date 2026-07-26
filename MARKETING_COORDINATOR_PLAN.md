# Marketing Coordinator — Combination Plan

**Status: plan only. No implementation.** Execution is post-MVP gated per `CLAUDE.md` scope
and the 2026-07-25 entry in `TASKS.md` Decisions Log. Drafted 2026-07-25.

## What this is

One AI-employee role — the **Marketing Coordinator** — built by combining two proven pieces
already in hand, employed inside WebStaffr. It is the crux of the upgrade path to the
Business Manager Tier.

- **`marketing-director-gtm`** (Cowork skill; canonical copy: `~/Desktop/marketing-director-gtm.skill`,
  a single `SKILL.md`) — the **strategy brain**. Intake → live competitor/market research →
  positioning recommendation → 3–5 ad copy variants → platform-specific ad assembly
  (Meta / Google / LinkedIn) → weekly KPI monitoring with an optimization protocol.
  Human approval gate on ad copy only.
- **`social-media-marketing-machine`** (SMMM; canonical copy: `social-media-marketing-machine/`
  in this repo — the Desktop zip and `pre-merge-backup-2026-07-25` are pre-merge snapshots of
  the same code) — the **execution body**. Campaigns, posts with immutable version history,
  approval state machine (structurally enforced), calendar/scheduling, publishing adapters for
  9 organic platforms, analytics snapshots with DB-enforced dedup, audit log, multi-tenant
  orgs, Celery background workers, a multi-provider AI layer, and an execution-trace graph.
- **WebStaffr 3.3** (this repo) — the **employer**. Tenant identity, the customer intake
  record, Angel, attribution, and the already-built integration bridge
  (`social_media_mounts` / `social_media_intents` + `execution_nodes`, TASKS #37–#54).

## Why combining beats either piece alone

- The skill produces strategy and copy but **publishes nothing and measures manually**.
- SMMM publishes and measures but has **no strategy brain** deciding what to say.
- WebStaffr owns the two things neither has: **intake data** to seed strategy without
  re-interviewing the customer, and **attribution** to measure booked jobs — not clicks —
  so the weekly report can speak actual ROI. That closed loop is the Business Manager Tier
  value proposition.

## What already exists (verified in-repo, not assumed)

| Capability | Where | Status |
|---|---|---|
| Customer business data | WS3.3 `intake.py` | Covers most of the GTM skill's required intake (biz_name, industry, service_area, services, differentiator, tagline; optional competitors, tone, brand words/colors, years in biz, GBP link). Missing only: target customer profile, marketing budget, timeline. |
| Tenant ↔ SMMM-org bridge | WS3.3 `social_media_router.py`, migrations 0007/0008 | Built, auth hardened (#44), tested. |
| Approval workflow | SMMM `ApprovalStateMachine` + `Post` guard | Built; state changes are structurally enforced. |
| Organic publishing | SMMM `social/platforms/` | 9 adapters: facebook, instagram, linkedin, x, threads, tiktok, pinterest, youtube, google_business. |
| AI provider layer | SMMM `ai/providers/` | claude, openai, gemini, grok, ollama, hermes. |
| Long-running jobs | SMMM Celery workers | Built. |
| Execution trace | Both sides (`execution_nodes`) | Built both sides; recovery is deterministic from the graph. |
| Analytics snapshots | SMMM `analytics` | Built, dedup enforced by DB constraint. |
| Booked-job attribution | WS3.3 `attribution.py` | Built. |
| **Live web research** | — | **Not built anywhere yet; vendor decided (D1) — SearXNG.** See below. |
| **Paid-ads platform APIs** | — | **Not built anywhere.** Deliberately deferred (Phase 4). |
| **Two-way client comms channel** (SMS + email) | — | **Not built anywhere.** Checked `CREDENTIALS.md` and `webstaffr/attribution.py` directly — no Twilio, no email vendor, no re-contact mechanism exists in WS3.3 today. Founder-directed shared infrastructure (see below); only the vendor choice (D4) is still open. |

## Architecture (recommendation — approve at build start)

**Placement rule: WS3.3 stays the source of truth for tenants, workflow, and approval
routing; SMMM runs everything long-running.**

Why: WS3.3 is Vercel serverless — its own invariant forbids assuming a persistent process,
and the GTM research pipeline is a ~30–45 minute multi-stage job. SMMM already has exactly
the machinery that job needs (Celery, AI providers, agent/task/prompt-template models). So
the Marketing Coordinator's engine is an **SMMM agent pipeline**; WS3.3 triggers it through
the existing mount/intent bridge and both sides record the trace. Identity models stay
separate per `social-media-marketing-machine/INTEGRATION_PLAN.md` — the mount binds
tenant ↔ org once; no Clerk retrofit into WS3.3.

Per-customer flow:

```
1. Mount once            WS3.3 tenant  ->  SMMM org        (existing bridge)
2. Kickoff               WS3.3 intake + tier questionnaire (below) -> intent (existing endpoint)
3. Strategy run          SMMM pipeline: research -> positioning -> 5 copy variants
   3a. Gap hit            missing field -> WS3.3 re-interview request -> client (email/SMS,
                          per their preferred_contact_channel) -> field filled or omitted
4. Approval gate         SMMM approval workflow (human, copy only — matches the skill)
5a. Organic path         approved posts -> schedule -> publish via adapters (automated)
5b. Paid path            assembled ad packages, ready for manual posting (skill's own model)
6. Weekly loop           SMMM analytics + WS3.3 attribution -> weekly report + optimization
                         memo; autonomous pause/boost only post-approval, per skill protocol
```

The GTM `SKILL.md` stages become **versioned prompt templates** inside SMMM (the
`prompt_template` model exists for this). At build start the skill file is vendored into the
repo verbatim as the canonical prompt source — same treatment `angel_prompt.md` got.

### Research vendor: SearXNG (decided 2026-07-25 — open source, per founder direction)

**SearXNG** — a self-hosted, open-source metasearch engine (aggregates Google, Bing,
DuckDuckGo, Brave, and others behind one query, JSON output, no per-query API fee, no
usage tied to a third party's commercial terms). It runs as one more container next to the
ones SMMM already defines in `docker-compose.yml` (`postgres`, `redis`, `minio`, `backend`,
`celery_worker`) — no new hosting platform, just a new service in infrastructure that
already exists. The Phase 1 research module calls it the way it'd call any other internal
service.

Honest tradeoff, stated plainly: it's self-hosted, so it's WebStaffr's instance to run —
occasional tuning against upstream engines' own rate limits, no vendor support line to
call. That's the cost of open source over a paid search API; worth it given the founder's
explicit steer and the very small, controlled query volume a kickoff research run needs.

## Business Manager Tier kickoff questionnaire (decided 2026-07-25)

When a client chooses (or upgrades to) the Business Manager Tier, a marketing kickoff
questionnaire fires — separate from the base site intake, which stays unburdened. It
collects, per client:

- **Social presence audit** — for each major platform (Facebook, Instagram, LinkedIn,
  Google Business, plus the rest of SMMM's adapters as applicable): do they have an
  account, and what's their handle/page name on it?
- **Setup service opt-in** — for platforms they *don't* have: would they like WebStaffr to
  set the account up for them? (Connecting existing accounts happens via OAuth through
  SMMM's `platform_account` flow — credentials are never collected in a form or in chat,
  per the security baseline. Setup of brand-new accounts is an assisted onboarding
  service, scoped at build time.)
- **Google Business Profile** — URL and access status (base intake already collects
  `has_gbp`/`gbp_url`; the questionnaire confirms and fills gaps rather than re-asking).
- **Marketing fields the GTM engine needs** — target customer profile, marketing budget,
  timeline.
- **`preferred_contact_channel`** — `email` / `sms` / `either`, used by the comms channel
  below.

Answers land in WS3.3 through the same validated intake path (extending the existing
intake machinery, not a parallel store) and seed both the mount (which platforms) and the
strategy run (budget, audience, timeline).

## Phases (all post-MVP)

- **Phase 0 — Gate & prep.** MVP ships (hard gate). Commit/push SMMM's uncommitted working
  tree. Founder approves the two open vendor choices (D1, D4-vendor). No Marketing
  Coordinator code before this clears. *Note:* the comms channel itself is exempt from
  this gate per the founder's D4 timing decision — it's MVP-adjacent shared
  infrastructure and can be built as soon as its vendors are approved. *Size: S.*
- **Phase 1 — Strategy engine.** GTM stages 1–3 as an SMMM pipeline: intake mapper
  (WS3.3 intake → GTM intake form), research module (needs D1), assessment report,
  5 copy variants stored as campaign drafts wired to the approval workflow.
  *Done =* a real tenant's intake produces an assessment + variants awaiting approval, every
  step traced in `execution_nodes`. *Size: L — the largest phase.*
- **Phase 2 — Organic execution end-to-end.** Approved variants → schedule → publish via
  adapters → visible in calendar; trace on both sides; per-tenant weekly cadence config.
  *Done =* one approved post reaches a test platform account with a full trace. *Size: M.*
- **Phase 3 — Ads assembly + measurement loop.** GTM stage 4 (platform-specific paid-ad
  packages with manual-posting instructions) and stage 5 (weekly KPI report joining SMMM
  analytics with WS3.3 attribution; optimization memos; autonomous optimization strictly
  post-approval). *Done =* a weekly report generates for a live tenant with real numbers or
  explicit "unavailable" markers — never invented ones. *Size: M.*
- **Phase 4 — Business Manager Tier packaging.** Tier gating/billing, productized
  white-label report path, optional paid-ads API automation (each ads API is its own vendor
  decision). Deliberately not designed in detail here.

## Rules that override the skill

The GTM `SKILL.md` contains fallback behaviors that violate this repo's no-fabrication
invariant. **Where they conflict, `CLAUDE.md` wins:**

| `SKILL.md` says | This build does |
|---|---|
| No customer wins → invent social proof ("Trusted by 5,000+ homeowners") | Never invent. Trigger a re-interview request instead (below). Omit the claim only while the answer is still outstanding. |
| Ad matrix includes "estimated reach / estimated CTR" | Label as industry benchmark, never present as measured. |
| Research mines reviews for themes | Cite only reviews actually retrieved; no invented ratings or quotes. |
| Budget "not specified" → assume $500–2,000/month | Never assume. Same re-interview trigger as above. |

Also: `license_number`, `lead_routing`, `approver`, `competitors` remain on the never-leak
list — they may inform strategy internally but never appear in generated copy or reports.

### Client comms channel: two-way, shared, tenant-aware (founder-directed 2026-07-25)

Not just a re-interview mechanism — a **general two-way communication channel** between
each client and WebStaffr, covering everything: site-generator issues, ad-service issues,
missing-data questions, any problem whatsoever. Built once in WS3.3 as shared
infrastructure; the site generator, the Marketing Coordinator, and general support all use
the same channel.

**Outbound — re-interview instead of fabrication or silent omission.** Omission (WS3.3's
existing default) is the right *interim* state but not the end state — a client with a
real testimonial or a real budget shouldn't have that fact permanently missing because it
wasn't captured on the first pass:

1. A generation step hits a missing field it needs (no customer wins for social-proof
   copy, no budget for spend recommendations, no differentiator for positioning).
2. WS3.3 queues a **re-interview request** for that specific field — short, targeted, not
   a full re-intake — sent over the client's chosen channel (**email and/or SMS**, via a
   `preferred_contact_channel` field: `email` / `sms` / `either`).
3. Until answered, generation proceeds with the field omitted (never invented) — the
   no-fabrication default holds as the safe fallback; it's just no longer permanent.
4. The answer updates the intake record through the same validated path as the original
   intake, and anything already generated that depended on the field is flagged for
   regeneration or re-approval — never silently patched in.

**Inbound — a number they can just text.** A dedicated SMS number the client texts
directly, any time, about anything. WS3.3 recognizes the sender: the inbound `From` number
is matched against the tenant's intake `phone` (a required intake field, so every tenant
has one on record). Recognized → the message is logged as a problem/request against that
tenant and routed (and can answer an outstanding re-interview question if one is pending).
Unrecognized number → held in a general triage queue, never guessed into a tenant. Email
replies work the same way, keyed by sender address against the intake `email`.

**Implementation shape (for the build session, not decided in detail here):** an
intake-adjacent WS3.3 capability — outbound message record + inbound message record, keyed
to `tenant_id`/`submission_id`, raw-SQL per this repo's persistence idiom, vendor client
behind the usual `Protocol` + `Null*` + `*NotConfiguredError` pattern so everything stays
testable unconfigured. Webhook endpoints for inbound (server-to-server, no CORS, verified
sender — same treatment as `/webhooks/ghl`).

## Landmines carried forward (from SMMM `HANDOFF.md` — binding on all build sessions)

- Enum labels in SMMM's DB are UPPERCASE member names. `docs/sql/smm_gtm_bridge.sql` is
  design-intent only with known-wrong literals — never copy from it.
- A green SMMM suite proves less than you think — test the symptom, not the code just written.
- Each repo keeps its own persistence idiom (WS3.3 raw SQL, SMMM async ORM); the bridge API
  is the only crossing point. Neither idiom crosses over.
- Tenant/org scoping is enforced at the repository layer on both sides — the worst prior bug
  was a publish task looking up rows by primary key with no org filter.

## Founder decisions

**Decided 2026-07-25 (logged in `TASKS.md` Decisions Log; not re-litigated):**

- **D2 — Launch platforms: the majors, all of them.** Facebook, Instagram, LinkedIn,
  Google Business as the covered set; the remaining SMMM adapters (X, TikTok, Pinterest,
  Threads, YouTube) available per-client where the questionnaire shows they have or want
  them. Supersedes the earlier LinkedIn-only-if-B2B recommendation.
- **D3 — Tier kickoff questionnaire.** A separate marketing questionnaire at Business
  Manager Tier selection/upgrade, per the section above — not added to the base site
  intake. Scope grew from "3 missing fields" to the full social-presence audit +
  setup-service opt-in.
- **D4 (scope + timing) — Two-way client comms channel.** Founder-directed: a dedicated
  SMS number clients text directly (plus email), tenant-recognized, handling any problem
  or question across all WebStaffr services — including the site generator, which needs it
  already. Shared infrastructure, not gated behind the Marketing Coordinator build.
- **D1 — Web-research vendor: SearXNG.** Open source per founder direction; see rationale
  above. This approval (open-source category, self-hosted, no per-query fee) is the
  specific-choice sign-off `CLAUDE.md`'s security baseline requires for a new dependency.

**Still open before build (the only escalation):**

- **D4 (vendor) — SMS + email provider.** The comms channel still needs an SMS provider
  (e.g. Twilio) and an email provider (e.g. Resend/SendGrid) picked — new dependencies,
  each needing approval tied to the specific choice, per the security baseline. Left open
  on the founder's instruction; not decided here.
- Deferred to Phase 4: pricing/tier definition, paid-ads API vendors.

## Success criteria (adapted from the skill, made checkable)

- Assessment report identifies ≥1 genuine positioning gap vs. researched competitors, with
  sources cited.
- 5 copy variants generated per campaign; ≥2 meet service-industry benchmark CTR once live
  (>1.5% Meta, >3% Google Search).
- Organic posts flow intake → approval → published with zero manual steps besides approval.
- Weekly report ties spend to attributed calls/bookings via WS3.3 attribution, and every
  number in it is real or explicitly marked unavailable.
- Paid-ad packages pass platform validation (character limits, image specs) without edits.
- No generated copy or report ever contains an invented fact — a missing field either
  triggers a re-interview request or is omitted; it is never filled with plausible filler.
- A client texting the dedicated number from their intake phone number is recognized and
  their message logged against the right tenant; an unrecognized sender lands in triage,
  never mis-attributed.

## What this plan deliberately does not do

- No implementation now — the post-MVP gate holds.
- No detailed Phase 4 (billing/tier) design.
- No dependency choices made beyond D1 (SearXNG) — D4's SMS/email vendor stays open.
- No identity-model merge — the deliberate seam from `INTEGRATION_PLAN.md` stands.
