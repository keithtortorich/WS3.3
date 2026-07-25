# TASKS.md — WebStaffr 3.3

## Completed

- #35 : Actively inspect real WS3.3 repo instead of copying SMM docs into it. Files read: `router.py`, `db.py`, `intake_router.py`, `attribution_router.py`, `tenant.py`, `attribution.py`, `integrations/servicetitan/{client,sync,mocks}.py`, `workers/angel/api_auth.py`.
- #36 : Delete misleading SMM doc copies from WS3.3 (`docs/smm-integration-reference/`, near-duplicate set under `integrations/servicetitan/`). All references remain authoritative only in the SMM repo.
- #37 : Add WS3.3-native social media integration schema (`migrations/0007_social_media_mounts.sql`: `social_media_mounts`, `social_media_intents`, indexes).
- #38 : Add `integrations/social_media/` package with local client/sync/mocks.
- #39 : Add `workers/angel/social_media_router.py` with mount/intent endpoints and auth.
- #40 : Mount/social-media router wired into `create_app()` in `workers/angel/router.py`.
- #41 : Ad-hoc verification of new social media persistence layer passes (imports, mocks, SQLite round-trip).
- #42 : FastAPI route smoke verification passes via `TestClient`.
- #43 : Add `pyproject.toml` + `tests/test_social_media_integration.py`; `pytest` reports 6 passed against the focused social media test module.
- #46 : Add WS3.3-native execution-trace graph schema (`migrations/0008_execution_nodes.sql`: execution_nodes table, indexes).
- #47 : Add `integrations/workflow_graph/` package with local client/sync/mocks/repository aligned to `RETAINED_GRAPH_MODEL.md` execution-trace model.
- #48 : Add `tests/test_workflow_graph.py`; `pytest` reports 6 passed against the focused workflow graph test module.
- #49 : End-to-end pytest across focused modules reports 12 passed.
- #44 : Auth hardening done for both integration bridge routers, not just the one originally scoped. Found via independent verification, not by inspection: `x_api_key: Optional[str] = None` as a plain FastAPI parameter never binds to the real `X-API-Key` header — it silently receives `None` on every request, so `_require_auth()` was checking the caller's key against a value that could never be present. This affected `social_media_router.py` (#39, already-shipped) and `workflow_graph_router.py` alike. Fixed both by switching to `Header(default=None, alias="X-API-Key")`. Confirmed via `TestClient` with a real key: 401 before the fix, 200 after.
- #50 : `workers/angel/workflow_graph_router.py` built and wired into `create_app()` (`workflow_graph_verifier` param, same factory/DI shape as `retell_verifier`/`ghl_webhook_verifier`/`book_api_verifier`). Endpoints: `POST /workflow-graph/nodes`, `GET /workflow-graph/nodes/{workflow_instance_id}/{node_id}`, `GET /workflow-graph/nodes/{workflow_instance_id}`, `POST /workflow-graph/nodes/{workflow_instance_id}/{node_id}/status`. Server-to-server only (not in `ScopedCORSMiddleware`), same reasoning as `/book`/`/webhooks/ghl`. `tests/test_workflow_graph_router.py` added: 10/10 passing (route registration, create/get/list/update-status happy paths, bad-type/bad-tenant 400s, not-found 404, auth reject + unconfigured-open).
- #51 : Correction to this entry's own prior "188/191, 3 failures are path-portability-only, not a code defect" note above: two of those three were real bugs, not sandbox artifacts. (a) `test_social_media_integration.py`'s `test_sqlite_sync_round_trip` did hardcode the founder's Mac path — that part was accurate, and is now fixed by reading the migration file relative to the repo root instead. (b) The other two failures (`test_workflow_graph.py`'s `test_sqlite_execution_trace_round_trip`, `test_tenant_and_instance_scoping`) were mischaracterized as the same path issue but were actually a real `sqlite3.OperationalError: no such table: tenants` — caused by an FK-safety fix added to `integrations/workflow_graph/sync.py`'s `create_node()` (an `INSERT OR IGNORE INTO tenants` guard, needed so a tenant's first node doesn't hit an `IntegrityError` against `execution_nodes.tenant_id`'s FK) that assumed a `tenants` table always exists. It doesn't in these two tests, which deliberately apply only `0008_execution_nodes.sql` to an isolated in-memory connection to test the persistence layer in genuine isolation — a real, intentional test design, not something to route around by forcing every caller onto the full migration set. Fixed by checking `sqlite_master` for the table's existence before inserting: a no-op for the real app (which always runs the full migration set) and safe for the isolated unit tests. Flagging the correction explicitly per this repo's own convention of not silently overwriting a prior entry's claim.
- #52 : Fixed a real regression accidentally introduced during #39/#40's edit, found only via full-suite (not module-scoped) regression testing: `SUPPORTED_EVENT_TYPES = {"website_lead", "missed_call"}` was deleted from `router.py` in the same diff hunk that added `SocialMediaMountRequest`/`SocialMediaIntentRequest`, breaking `/webhooks/ghl` with a `NameError` and failing 7 tests in `test_router.py`. Restored the constant.
- #53 : Data-model collision resolved between two competing Block 3 candidates (`webstaffr/graph.py`'s workflow-definition/auto-increment-int-id shape vs. `integrations/workflow_graph/`'s execution-trace/caller-supplied-text-id shape). Founder chose `integrations/workflow_graph/` as canonical; `graph.py` and its `0008_workflow_nodes.sql` migration were deleted, leaving one `0008_execution_nodes.sql`.
- #54 : Full suite verified clean after all of the above, including the corrections in #51/#52: **213/213 passing**, `scripts/health_check.py` reports **HEALTHY** (all 8 checks). Verified in a sandbox copy with sandbox-appropriate paths substituted only in test files (never in application code) — not taken on report from either agent's own claim.

## In Progress

(none)

## Pending

- #45 : Decide ServiceTitan socket workflow format before next integration pass.
- #55 : Delete the `*_sandboxcheck.py` test files (`test_workflow_graph_sandboxcheck.py`, `test_workflow_graph_router_sandboxcheck.py`, `test_social_media_integration_sandboxcheck.py`) if still present, and the stray duplicate-named files, before committing — sandbox-path throwaway copies / accidental duplicates, not meant to ship.
- #56 : Three save-conflict duplicate files remain from concurrent-session edits and are lock-protected as of this entry — could not be diffed or deleted: `tests/test_workflow_graph 2.py`, `webstaffr/integrations/workflow_graph/__init__ 2.py`, `webstaffr/TASKS 2.md`. Once the lock clears: confirm each is byte-identical to its non-" 2" counterpart, then delete.
- #57 : `SocialMediaMountRequest`/`SocialMediaIntentRequest` in `router.py` may now be dead code — `social_media_router.py` defines its own `MountRequest`/`IntentRequest` and doesn't import the `router.py` versions. Not confirmed unused, not removed; flagged for a follow-up pass.
- Re-run the full suite directly on the founder's Mac (not this sandbox mount) as a final cross-check before calling this fully verified end-to-end.
- Commit + push (local commit self-approvable; push needs explicit approval per CLAUDE.md).

## Blocked

- No canonical `pytest` config/test suite historically present in WS3.3; the new `pyproject.toml` + `tests/` folder is a minimal addition and may need review before treating it as canonical project-wide test infrastructure.
