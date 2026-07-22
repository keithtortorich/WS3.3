# SECURITY.md

Findings from a real code + live-infrastructure audit, not a policy
template. Dated so it's clear when each claim was actually checked.

## Audit — 2026-07-22

Scope: all Python source in `webstaffr/`, `.github/workflows/ci.yml`,
`requirements.txt`, and the live Supabase project (`ntbnenymyqiautaqhyhe`)
via `get_advisors`. WS3.3's own repo only -- WS3.0 is a separate codebase
and was not re-audited here.

### Checked, no issue found

- **No hardcoded secrets.** Grepped for key/secret/password/token
  assignments to string literals across `webstaffr/`; every match was
  either an `os.environ.get(...)` read, a docstring, or a function
  parameter -- nothing that looks like a committed credential.
- **No SQL injection surface.** Every `.execute()` call parameterizes
  user-supplied values with `?` placeholders. The one place a query
  string is built with an f-string (`intake.py`'s `INSERT INTO
  intake_submissions (...)`) interpolates a fixed, code-controlled column
  name list (`_COLUMNS`), not user data -- actual values still go through
  `?` placeholders as a separate parameter tuple. Verified by reading the
  call site directly, not assumed from the pattern looking risky.
- **Bearer tokens sourced correctly.** Both `ghl.py` and `voice.py` build
  their `Authorization: Bearer <token>` header from `os.environ.get(...)`
  only -- no default, no fallback literal.
- **Signature/secret verification is constant-time and fails closed.**
  `RetellSignatureVerifier` (`retell.py`) and `StaticSecretVerifier`
  (`api_auth.py`) both use `hmac.compare_digest()`, not `==`, and both
  return `False` (never raise) on a missing or malformed header -- callers
  have one code path for "reject," not two.
- **RLS is live and matches documented state.** `get_advisors` against
  the live Supabase project returns RLS enabled on all 7 public tables
  (`tenants`, `workflow_definitions`, `execution_records`, `appointments`,
  `intake_submissions`, `rate_limit_counters`, `tracking_numbers`,
  `call_events` -- 8 total, all confirmed), zero policies (default-deny),
  only INFO-level "RLS enabled, no policy" notices -- no ERROR-level
  findings. Matches `docs/DATABASE.md`'s description exactly; checked live
  rather than trusted from that doc.
- **CI doesn't leak secrets.** `.github/workflows/ci.yml` runs tests and
  the health check against no real credentials (everything defaults to
  the Null-object path) -- nothing in the workflow references a secret
  that could appear in logs.

### Real gap found and fixed this session

- **No Dependabot config existed.** Added `.github/dependabot.yml`
  (weekly `pip` and `github-actions` update checks, capped at 5 open PRs).
  Before this, a CVE in a pinned dependency (`fastapi`, `starlette`,
  `pydantic`, etc.) would never surface automatically.

### Known, accepted gaps (not bugs -- documented tradeoffs, see DECISIONS.md)

- **`/book`, `/webhooks/ghl`, `/retell/*` fail open when unconfigured.**
  Each checks a shared secret (`BOOK_API_KEY`, `GHL_WEBHOOK_SECRET`,
  `RETELL_WEBHOOK_SECRET`) against a request header, but falls back to a
  Null verifier that accepts everything if the relevant env var is unset.
  This is a deliberate, repo-wide convention (matches every other
  Protocol+Null pattern in this codebase), not an oversight -- but it
  means **an unconfigured deployment has zero auth on these three
  routes**, not reduced auth. As of this audit, WS3.3's Vercel deployment
  has no environment variables set at all (see `CLAUDE.md`/`TASKS.md` for
  current status) -- if that deployment goes live before those three
  secrets are set, those routes are open. This is not a code fix; it's an
  operational step (setting the env vars) that hasn't happened yet.
- **Retell signature format is `[Unverified]`.** `retell.py`'s header-name
  and prefix-stripping logic are implemented from Retell's publicly
  documented convention, never exercised against a real Retell-signed
  request. Confirm against Retell's actual dashboard/docs before this
  matters in production.
- **`rate_limit_counters` has no pruning.** Rows accumulate forever. Not a
  practical problem at MVP volume; add a cleanup job before it is one.
- **Postgres dialect shim (`db.py`) has no live-Postgres test coverage.**
  Covered by unit tests against a fake driver (`tests/test_db_pg_shim.py`),
  never exercised against a real running Postgres server from within this
  repo's test suite.
- **`license_number` is collected but not publicly exposed** -- a
  deliberate founder decision (ADR-006 in `docs/DECISIONS.md`), not a
  gap, noted here only because it's the kind of thing a security review
  would otherwise flag as an open question.

### Not covered by this audit

- Dependency CVE scan results themselves (Dependabot will surface these
  going forward; none were manually checked against a CVE database this
  session).
- Vercel/hosting-platform-level security (access controls on the Vercel
  team, GitHub App permissions) -- covered informally during the earlier
  Vercel project setup, not re-audited here.
- Anything in WS3.0 -- separate codebase, separate deployment, out of
  scope for this repo's audit.

## How to keep this current

This file reflects a point-in-time check. Before trusting a claim above,
verify it's still true rather than assuming -- especially the "no
hardcoded secrets" and "no SQL injection surface" findings, which need
re-checking any time new code touches secret handling or raw SQL
construction. Add a new dated section for future audits rather than
editing this one in place.
