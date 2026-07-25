# TASKS — Social Media Marketing Machine

Single source of truth for live status. Every "done" below is backed by a command that was
actually run, not by a claim in a report. Narrative and rationale live in
`SESSION_STATUS_2026-07-24.md`; orientation for a new session lives in `HANDOFF.md`.

**Baseline as of 2026-07-24, commit `73b0f34`:** 155/155 tests passing, single Alembic head
`e00c25c0041f`, app serving 32 paths, remote `github.com/keithtortorich/smmm` in sync.

---

## Done

**#1 — Execution graph schema.** `execution_nodes` created by migration `412a32e37eb2`.
Root cause of the long-standing block was a missing import in `app/models/__init__.py`, not
a missing model. Verified: migration round-trips, table present, workflow tests pass.

**#2 — WS3.3/GTM intake bridge.** `POST /integrations/social-media-marketing/mount` (204 +
`Location`) and `.../mount/{mount_id}/intent`. One transaction produces Campaign → Post(s)
→ PostVersion v1 → PENDING Approval → execution graph → audit row, with complete rollback
on mid-ingest failure. Migration `11bbfaf5a443`. Verified: 10 integration tests including
cross-tenant isolation and full-rollback.

**#3 — Approval workflow hardening.** `post.status` structurally unwritable outside
`ApprovalStateMachine` (`ContextVar` + `@validates` guard), verified non-vacuous by direct
experiment. Orphan-`Approval` bug on illegal decisions fixed; version numbering
de-raced; `PostVersion` rows reject mutation.

**#4 — Publishing and scheduling reliability.** Tenant scoping added to all publish task
queries (they previously loaded rows by primary key with no `organization_id` — any job id
could publish any tenant's content). Exceptions now re-raise; retries settle correctly;
idempotence enforced by an atomic database claim; non-publishable posts can no longer be
enqueued; execution-graph status wired through `WorkflowService`.

**#5 — Analytics and weekly KPIs.** Duplicate snapshots rejected (409) behind a real unique
constraint. Weekly rollup as a dual-dialect ORM aggregation, verified against a real
throwaway PostgreSQL instance — which surfaced a session-time-zone bug in
`date_trunc('week', ...)`, now pinned to UTC.

**#6 — Calendar visibility defect.** Published posts silently disappeared from
`GET /api/v1/calendar` because the sweep overloaded `is_cancelled` to mean "consumed".
Fixed with `schedules.enqueued_at` (migration `e00c25c0041f`) plus a regression test that
queries with the same predicate the calendar router uses.

**#7 — Client binding at mount time.** `integration_mounts.default_client_id` lets an
operator bind the real customer once, instead of the intent path guessing per request.
Fallback placeholders are flagged `clients.is_placeholder` and logged, so they are a
listable cleanup queue rather than silent junk.

**#8 — Repo backed up.** Pushed to `github.com/keithtortorich/smmm` (private), branch
`main`, verified by reading the remote back. Local branch renamed `ws3.3` → `main` to stop
it being confused with the unrelated WebStaffr3.3 repo.

---

## Open — highest value first

**#9 — Connect WS3.3 to SMM over HTTP.** Both halves exist; nothing joins them. WS3.3's
`SocialMediaClient` writes intents to its own database and is explicitly a placeholder for
an HTTP client. Blocked on three contract mismatches (`mount_id` int vs UUID; `brand_id`
slug vs UUID; `"meta"` is not a `PlatformName`) and a service-to-service auth decision —
SMM uses Clerk `org_id`, WS3.3 has no Clerk identity. Do not retrofit Clerk into WS3.3 and
do not use a shared secret; see `INTEGRATION_PLAN.md`.

**#10 — Publish one real post.** Nothing has touched a live LinkedIn or Instagram account;
every adapter is faked and all platform work is `[Unverified]`. This is the gap between
"tests pass" and "it posted to a customer's page." Needs founder-supplied credentials —
Claude must not create vendor accounts or generate keys.

**#11 — Execution graph HTTP surface.** `app/routers/execution_nodes.py` is still an empty
`APIRouter()`. Its docstring defers until the model/repository/service/tests are stable;
that precondition is now met. Note `tests/integration/test_execution_nodes_api.py` tests the
repository directly and exercises no API despite its name.

**#12 — `WorkflowService.update_node_status` defects.** Sets `completed_at` for `RUNNING`,
so a node that has merely started looks finished; also unconditionally overwrites
`failure_reason` with `None` when none is passed.

**#13 — Remaining platform adapters.** Facebook, X, Threads, TikTok, Pinterest, YouTube,
Google Business are stubs. Only LinkedIn and Instagram are implemented.

**#14 — Placeholder client merge path.** `is_placeholder` rows have no operator UI to merge
them into real clients. Binding `default_client_id` at mount time prevents new ones.

**#15 — Frontend `tsc` errors.** 9 pre-existing, documented in `BUILD_REPORT.md`, unrelated
to backend work and untouched.

---

## Known traps (cost real time already — read before touching migrations)

1. A new model is invisible to Alembic **and** to the tests until imported in
   `app/models/__init__.py`. Skipping it yields an empty migration that looks like success.
2. Autogenerate omits `import app.core.db_types` while emitting `GUID()` → `NameError`.
3. Autogenerate proposes dropping `ix_execution_nodes_org_open` and
   `ix_execution_nodes_org_workflow_ref` **every time**. They are intentional. Delete that
   block from any generated migration.
4. A green suite has twice hidden a real bug here. Test the symptom, not the code you wrote.
5. Enum labels in the database are UPPERCASE member names. `docs/sql/smm_gtm_bridge.sql`
   gets this wrong in places — design intent only, never copy its literals.
