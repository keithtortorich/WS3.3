# CLAUDE.md : WebStaffr 3.3 Operating Rules

## Why this repo exists
Reset of WebStaffr 3.0. The code was proven and tested; the multi-agent coordination process around it (Claude + Grok + an advisory reviewer) generated overhead without value : founder-decisions sat unresolved for sessions, tokens went into process debate instead of product. This repo starts clean on process. Only proven code and finished copy were migrated from WS3.0 : see the 2026-07-22 addendum below for what and why.

## Founder's Role
Founder is not a coder. Do not assume technical background to evaluate implementation tradeoffs. When multiple sound approaches exist, pick the one that best fits this repo's architecture, maintainability, security, and simplicity : don't present options for the founder to choose between. Escalate only for: product vision, business priorities, budget, legal/compliance, vendor selection, or material cost/schedule impact. Otherwise, decide and act.

## MVP Scope
Full flow: intake → generated customer site → Angel widget embedded and working, plus live voice via Retell.
- Frontend/site generation: delegated to Lovable (MCP). Iterate customer sites there, not token-by-token here.
- This repo's scope: backend logic : Angel (voice, GHL, booking), tenant isolation, the workflow/executor engine, attribution, tests, migration/architecture work.
- Out of scope until MVP ships: the other AI-employee roles, workflow builder UI, ops dashboard, billing/tier logic, ServiceTitan/Jobber sync (code exists, migrated, but wiring it live is post-MVP).

## Process
Claude-only. No multi-agent coordination protocol, no ownership-header comments on files, no advisory-reviewer loop. Short, single-purpose turns. Decisions get made once, logged, executed : not re-litigated. One task per turn; side-issues discovered mid-task get logged in TASKS.md, not fixed inline, unless trivially in-path.

## Self-Approval Scope
Self-approvable, no need to ask: any reversible local-only change (code edits, tests, docs, refactors), improvements following best practices (auth, rate limits, error handling, security scoping), anything that keeps tests passing and health check HEALTHY.

Requires explicit founder approval first: git push or any deploy, new dependency (package or SaaS vendor), architecture/data-model/DB schema changes, anything touching credentials/secrets/production systems/Lovable/Vercel/Supabase, high-ambiguity decisions with material cost or live-behavior impact.

When acting: summarize clearly, e.g. "Completed X. Tests: N/N passing. Health: HEALTHY. Ready for push?"

## Engineering Invariants
- Persistence: raw SQL via `webstaffr/db.py`'s `get_connection()`, `?` placeholders, `DB_ERRORS` for error wrapping. No ORM, ever. `migrate()` is a no-op under Postgres : schema is managed in Supabase out-of-band.
- Integrations: `Protocol` interface + `Null*` safe default + real implementation raising a `*NotConfiguredError` at construction when credentials are absent. Dependencies injected via constructor.
- Every query is tenant-scoped. `tenant_id` is public, never treated as a credential.
- CORS is per-path: browser-facing routes only (`/chat`, `/intake*`, `/sites/*`). Server-to-server routes (`/book`, `/webhooks/ghl`, `/retell/*`) carry no CORS headers.
- Hosting is Vercel serverless : nothing may assume a persistent process or a held-open connection.
- No fabrication: never generate placeholder ratings, reviews, testimonials, or credentials. Omit missing sections rather than inventing filler. Any change to the public site-data projection re-checks the never-leak list (internal-only fields like `lead_routing`, `approver`, `competitors`, `license_number`).
- Secrets: never asked for in chat. Set via Vercel env var (Sensitive) or a gitignored `.env`, verified with a pass/fail script that never echoes the value. New env var → update `CREDENTIALS.md` and `README.md` both.

## Token-Efficiency Rules
- Orientation: read the last CLAUDE.md addendum + TASKS.md only. Full history only when reconciling.
- Tests: run on code changes, skip on doc-only commits.
- Diffs: `git diff --stat` first, deep-read only implicated files.
- Third-party claims (Lovable agent, vendor docs): verify independently before trusting a "fixed" report.
- No subagents unless the founder asks for one.

## CLAUDE.md Hygiene
TASKS.md is the single source of truth for live status. CLAUDE.md addenda record durable decisions only, appended dated at the bottom, matching this file's existing style. When this file exceeds ~300 lines, move oldest addenda to CLAUDE_ARCHIVE.md.

## Security Baseline
- No secrets, credentials, or tokens committed at any point, including comments, examples, or fixtures.
- No new dependency (package or vendor) added without explicit approval tied to that specific choice.

## Git Mechanics
This sandbox's shell cannot write git objects for a repo mounted this way : commit/push via Desktop Commander on the founder's actual Mac, same as WS3.0. Stage specific files only, never `git add -A`.

---

## Session Addendum (2026-07-22) : migrated from WebStaffr 3.0

Founder-directed reset, per the WS3.3 migration/kickoff prompt. Scope gate applied first (per `webstaffr-mvp-guardrails`): the kickoff doc bundled three things : repo migration, a connector-strategy writeup, and a 20-file "engineering bible" doc suite. Asked the founder directly rather than doing all three; founder chose migration only. The 20-doc handbook was explicitly not built : it runs counter to this repo's own stated Token-Efficiency Rules and the reset's own stated goal ("tokens went into process debate instead of product"). Not revisited unless the founder asks again.

**What was migrated, reviewed not copy-pasted blind:** the migration prompt's file list was written against an earlier WS3.0 snapshot and had drifted from actual repo state by the time this session ran (no `OWNED_BY` headers existed to strip; no `docs/drive-mirrors/Angel_Package.md` existed to copy). Migrated by the prompt's actual intent : proven, tested code : rather than its literal (stale) list:
- Engine + persistence: `tenant.py`, `workflow.py`, `execution.py`, `executor.py`, `db.py`, `repository.py`, all migrations (`0001`-`0003`, `0005`, `0006`, plus `postgres_manual/`).
- Angel worker, complete: `angel.py`, `voice.py` (real xAI call intact), `ghl.py` (update/cancel methods intact), `booking.py`, `router.py`, `retell.py`, `retell_router.py`, `api_auth.py`, `widget/angel-widget.js`, `angel_prompt.md` (copied verbatim, founder-supplied, not regenerated).
- Also migrated beyond the prompt's original list, because it's equally proven/tested code that postdates when the prompt was written: `intake.py`/`intake_router.py`, `site_data.py`/`site_router.py`, `rate_limit.py`, `trade_presets.py`, `attribution.py`/`attribution_router.py`, and the `integrations/servicetitan/` package.
- Tests: all 11 test files (169 tests total, up from the prompt's stated 54 : the source repo had grown since the prompt was written). `scripts/health_check.py`, `requirements.txt`, `requirements-dev.txt`, `index.py` entrypoint.
- Not migrated, matching the prompt's explicit exclusion: the ownership-comment protocol (already absent from source), TASKS.md's old coordination-plan section, unresolved P0 decisions from the prior process, the `webstaffr-orchestrator/` Cowork/Hermes scaffolding, and all the investor/business-plan documents (those stay in WS3.0, not proven code).

**Verified this session:** full suite run against the migrated WS3.3 code (not the source repo) : **169/169 passing**. `scripts/health_check.py` : **HEALTHY** (all 8 checks: imports, smoke workflow, tenant isolation, graceful degradation, SQLite round-trip, Angel imports, Angel booking round-trip, Angel router smoke). Test run and health check were executed from a copy outside the mounted folder due to a sandbox permission quirk with `tempfile` cleanup on the mount (unrelated to the code itself, confirmed by the same tests passing cleanly once run outside the mount).

**Not yet done:** creating the actual GitHub repo for WS3.3 and connecting/pushing to it (founder-only step, this session only had local folder access). Committing this initial migration locally (self-approvable once a git repo is initialized here; not yet done this session : no `.git` exists in this folder yet). `PROJECT.md` : WS3.0's product-vision content is worth carrying forward, not yet copied into this repo as of this addendum.

---

## Session Addendum (2026-07-25 through 2026-07-26) : bridges, security fix, repo merges, planning doc

Covers TASKS.md #35-#62, none of which were previously reflected here. Founder flagged the repo as feeling "all fucked up" on 2026-07-26 after this stretch of work; audited via ADR-001 (in session outputs, not committed to repo). Conclusion: no rewind warranted : every checkpoint including the latest verifies clean, and the two real defects found below were caught and fixed, not left in. The actual problem was this addendum going stale while TASKS.md kept moving, so a cold read of CLAUDE.md alone no longer matched reality. This entry is the fix for that.

**Two new integration bridges added, each with its own migration/package/router/tests:**
- Social media mounts/intents (#37-#41): `migrations/0007_social_media_mounts.sql`, `integrations/social_media/`, `workers/angel/social_media_router.py`, wired into `create_app()`.
- Execution-trace graph (#46-#50): `migrations/0008_execution_nodes.sql`, `integrations/workflow_graph/`, `workers/angel/workflow_graph_router.py` with 4 endpoints, server-to-server only (no CORS, same pattern as `/book`/`/webhooks/ghl`).

**Real defects found and fixed, not self-reported without verification:**
- #44 : `X-API-Key` header wasn't binding via plain FastAPI param typing (`x_api_key: Optional[str] = None`) : silently received `None` on every request, so auth checks could never actually reject. Affected both new routers. Fixed with `Header(default=None, alias="X-API-Key")`; confirmed via `TestClient` (401 before, 200 after).
- #52 : Full-suite (not module-scoped) testing caught a constant (`SUPPORTED_EVENT_TYPES`) accidentally deleted during an unrelated edit, which had broken `/webhooks/ghl`. Restored.
- #53 : Two competing implementations of a workflow-graph data model collided (`webstaffr/graph.py` vs. `integrations/workflow_graph/`). Founder chose `integrations/workflow_graph/` as canonical; the other, plus its migration, was deleted.
- #51, #58 : Hardcoded local Mac paths in test files were fixed, then found to be incompletely fixed, then fixed again across three files. Now use `Path(__file__).resolve().parents[1]` per the portable convention already used elsewhere in `tests/`.
- #58 : `pyproject.toml`'s `requires-python` floor reflected the founder's local Python version, not an actual code requirement; relaxed from `>=3.13` to `>=3.10`, verified clean.
- #57 : Dead code removed (`SocialMediaMountRequest`/`SocialMediaIntentRequest` in `router.py` : defined, never referenced).

**Two other repos merged into this one by git history** (2026-07-25 `merge:` commits): `WebStaffr 3.0/` (full prior repo, kept for reference) and `social-media-marketing-machine/` (separate marketing-automation project, unrelated to WS3.3's MVP scope). Both now sit as subfolders inside this repo. Disposition (keep as-is / relocate out) is an open founder decision, not yet made.

**Founder decision (2026-07-25):** `social-media-marketing-machine` combined with the `marketing-director-gtm` skill becomes the future "Marketing Coordinator" AI-employee role : the upgrade path to the Business Manager Tier. Explicitly post-MVP per this file's MVP Scope section (other AI-employee roles and billing/tier logic stay out of scope until MVP ships). No implementation done against this decision; planning only, captured in `MARKETING_COORDINATOR_PLAN.md` (three revision rounds, #59-#62) and TASKS.md's Decisions Log. That plan file is currently untracked in git; committing it or marking it explicitly disposable is an open founder decision.

**Open founder decisions carried forward, not yet resolved:**
- Disposition of `WebStaffr 3.0/` and `social-media-marketing-machine/` subfolders.
- Whether to commit `MARKETING_COORDINATOR_PLAN.md`.
- D4 from TASKS.md's Decisions Log : SMS/email vendor for the planned two-way client comms channel (post-MVP, not blocking).
- #45 (Pending in TASKS.md): ServiceTitan socket workflow format, needed before the next ServiceTitan integration pass.

**Verified as of the last commit in this range (`904550a`, 2026-07-25):** **191/191 passing**, `scripts/health_check.py` **HEALTHY**. Pushed to `origin/main` with founder approval. (Test count differs from the 2026-07-22 addendum's 169 and TASKS.md #54's 213 because those reflect different working copies at different points, not a regression : #57 confirms 191 is the correct current count for this local `.venv`.)

**Process note for next session:** update this addendum at natural checkpoints going forward (a `merge:` commit landing, or a batch of TASKS.md entries closing out a phase) rather than only at the start of a new repo, so this file doesn't go stale again.
