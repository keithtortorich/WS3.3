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

---

## Session Addendum (2026-07-25) : WS3.3 deployed to Vercel; dependency-install issue resolved

This addendum and the two that follow came from a parallel session working directly against `origin/main`, discovered via a rejected `git push` on 2026-07-26 and merged in (commit history preserved, no work discarded). One real conflict surfaced and was resolved: this session's `313fe94` raised `requires-python` to `>=3.13`; the local session above (#58) had independently lowered it to `>=3.10` after verifying the suite runs clean there. Kept at **`>=3.10`** post-merge — no `vercel.json` or platform config pins a runtime version, `313fe94`'s commit only changed that one line with no stated reason tied to the deploy fix, and `>=3.10` was the version actually verified against the passing suite. Flagging this explicitly in case there was deploy-environment context behind `>=3.13` that isn't visible from the commit alone.

WS3.3 is now deployed and live at `https://web-staffr3-3.vercel.app`.

WS3.3 is now deployed and live at `https://web-staffr3-3.vercel.app`.

**Verified:**
- `/health` returns `200 {"status":"ok"}` — the app boots, imports load, and routing is functional.
- Vercel project `web-staffr3-3` exists under the `web-staffr` team and is linked to this repo.
- `DATABASE_URL` is set on the Vercel project, scoped to Preview + Production.
- The original `500 FUNCTION_INVOCATION_FAILED`/`ModuleNotFoundError: No module named 'fastapi'` is resolved by adding `[project].dependencies` to `pyproject.toml`, sourced from existing `requirements.txt` pins, then pushing commit `313fe94` to `main`.

**Current observed behavior:**
- `/sites/desert_pro_plumbing_f22725f8` returns `503` with body `{"detail":"Site data temporarily unavailable"}`.
- In `site_router.py`, `get_site_data()` raises `HTTPException(503)` only when `get_connection()` fails at the DB layer (`DB_ERRORS`); a missing intake row would return `404`, not `503`.
- This means the app reaches the database layer and fails there; it is not an app-code regression introduced by the deploy fix.

**Not yet confirmed:** root cause of the 503. Working hypotheses, in order of precedence from prior incident shape:
1. Transient Supabase `ap-south-1` routing/pool behavior matching WS3.0's prior signature.
2. Stale or misconfigured credential, even though `DATABASE_URL` exists in Vercel.
3. Tenant `desert_pro_plumbing_f22725f8` not yet provisioned in Supabase for this project; expected to return `404`, not `503`, if that were the only issue.

**Next step:** run a direct DB diagnostic from the repo (`scripts/test_db_connection.py` or equivalent) to confirm whether the failure is connection-level or query-level, rather than changing anything until that result is in hand.

---

## Session Addendum (2026-07-26) : 503 root cause still unconfirmed; logging gap found and fixed

Root cause of the `/sites/{tenant_id}` 503 from the addendum above is **still not confirmed** as of this addendum -- the founder could not retrieve the live `DATABASE_URL` value from Vercel's dashboard to run `scripts/test_db_connection.py` (Vercel marks it Sensitive, which is write-only in the UI once set -- there is no "reveal" option, only overwrite). That diagnostic remains the concrete next step; it needs the value pulled from Supabase's own dashboard (Project Settings -> Database -> Connection string) instead of Vercel's.

**Real, separate bug found and fixed this session:** checked Vercel's live Logs view (`vercel.com/web-staffr/web-staffr3-3/logs`) for the specific request that produced the 503 (`fmbx8-1785067039061-6e9b519ec0e2`) and found nothing -- not a search/filter miss, confirmed by also checking the fully unfiltered log view for the same time window, which showed zero Warning/Error/Fatal entries at all. Root cause: `site_router.py`'s `_get_connection()` (and the identical pattern in `intake_router.py`, `attribution_router.py`, and `workers/angel/router.py`'s shared closure) caught `DB_ERRORS` and raised `HTTPException(503)` without ever calling `logger.error(...)` first -- so a DB-layer failure was, and always had been, completely silent in production logs. This wasn't specific to today's incident; every 503 from any of these four call sites since they were written would have been unobservable this same way.

**Fix:** added one `logger.error("<site>_db_connection_failed error_type=%s", type(exc).__name__)` call to each of the four connection-boundary functions, immediately before the existing `raise HTTPException(503, ...)`. Deliberately logs only `type(exc).__name__` (e.g. `OperationalError`), never `str(exc)` -- a psycopg2 error message can include the connection string (host, user), and this repo's Security Baseline prohibits that regardless of whether it's console output or committed text. Scoped to exactly the four router-level connection-opening call sites, not the ~30 other `except DB_ERRORS` sites across `repository.py`, `intake.py`, `attribution.py`, `booking.py`, etc. -- those catch at a different layer (raising `StorageError` back to an internal caller that already has its own context), and widening this fix to all of them would have been a larger, out-of-scope change for what this investigation needed.

**Verified this session:** full suite run from a copy outside the mount (same documented sandbox workaround as the 2026-07-22 addendum) -- **191/191 passing**. `scripts/health_check.py` : **HEALTHY** (all 8 checks). No behavior change to any response the client sees; this is additive logging only, same 503 status/body as before.

**Also added, not yet run:** `scripts/test_db_connection.py`, a throwaway diagnostic matching WS3.0's proven pattern (`getpass`-hidden input, `SUCCESS`/`SUCCESS_NO_DATA`/`FAILED: <reason>` output, never prints the URL or a raw exception message). Founder attempted to run it but could not retrieve the credential from Vercel to paste in (see above) -- not yet executed against the real value as of this addendum.

**Not yet done:** the actual root-cause determination this whole investigation was chasing. Once `DATABASE_URL` is retrieved from Supabase directly and `scripts/test_db_connection.py` is run, the next 503 (if any) will at least be visible in Vercel's logs with an exception type, which the ones investigated this session were not.

---

## Session Addendum (2026-07-26) : sessions reconciled, merge conflict resolved

The two addenda immediately above (this Vercel-deploy session) and the "bridges, security fix, repo merges" addendum before them were written in parallel, in separate sessions, against the same repo — one working locally, one pushed live to `origin/main`. Neither knew about the other until a routine `git push` was rejected. Merged via standard `git merge origin/main`; the only real conflict was the CLAUDE.md addendum text itself (both sessions appended here) plus the `requires-python` disagreement noted two addenda up, both resolved above. No commits were discarded on either side.

**Combined state after merge:** local integration-bridge work (#35-#62: social media + workflow graph bridges, auth header fix, dead code removal, repo merges) and the Vercel-deploy work (live deploy, DB-connection silent-failure logging fix, `scripts/test_db_connection.py`) are both now in one linear history on `main`.

**Still genuinely open, carried forward from both sides:**
- The `/sites/{tenant_id}` 503 root cause is **still unconfirmed**. Next concrete step, per the addendum above, is pulling `DATABASE_URL` from Supabase's dashboard directly (not Vercel's, which is write-only once set) and running `scripts/test_db_connection.py`.
- Disposition of `WebStaffr 3.0/` and `social-media-marketing-machine/` subfolders (unrelated to the Vercel session, still open).
- D4 : SMS/email vendor for the two-way client comms channel (post-MVP).
- #45 : ServiceTitan socket workflow format.

**Not yet verified:** the full suite has not been re-run against the merged tree as of this addendum. Do that before the next push, given both sides touched `pyproject.toml`, several router files, and `webstaffr/workers/angel/router.py`.

**Process note, reinforcing the one above:** this is the second time in two days this addendum has gone stale relative to actual repo state — this time because two sessions ran in parallel without either being aware of the other's remote pushes. Running `git fetch` at the start of a session (not just before a push) would have surfaced this sooner.
