---
name: webstaffr-analyze
description: Compress full context for sessions into minimal actionable state—founder (non-coder) experiences low friction and few questions
---

# webstaffr-analyze

## Purpose
At the start of every session, compress the full codebase, git history, and documentation state into a minimal, actionable summary. Goal: founder reads one-page orientation and knows exactly what's blocked, what's done, and what the next move is—without needing to ask Claude for clarification.

## Behavior (Triggered on Session Start)

### Step 1: Read the Essential State
1. **TASKS.md** — read fully. This is the single source of truth for live status (blocks, progress, next actions).
2. **CLAUDE.md** — read ONLY the most recent 1–2 addenda (the last section(s) of the file), not the full history.
3. **CREDENTIALS.md** — skim only if relevant to active tasks (don't re-verify every env var, just check which ones are known-live vs. pending).
4. **git status / git log --oneline -5** — confirm local main matches origin/main, check last 5 commits.

### Step 2: Compress and Output

Deliver this exact format (keep output under 150 lines total):

```
## CURRENT STATE

**Blocks (per TASKS.md):**
- [List active blockers in priority order, e.g., "Task #12: GHL trial timing (founder decision)"]

**Completed This Session:**
- [List items marked complete since last addendum]

**Next (prioritized):**
- [Concrete action item #1, should be self-approvable per CLAUDE.md Self-Approval Scope]
- [Concrete action item #2, flag if needs founder approval]

**Last Verified:**
- Tests: [X/X passing, or "not run this session"]
- Health: [HEALTHY or status]
- Commit: [hash], origin/main: [hash], [match/diverged?]

## LAST ADDENDA SUMMARY
[Bullet list of most recent 1–2 addendum highlights only, max 10 lines. Skip full historical detail.]

## RECOMMENDED ACTIONS
1. [Action matching Self-Approval Scope — do this without asking]
2. [Action requiring founder approval — flag clearly]
3. [Next concrete step after above]
```

### Step 3: Act on Scope

After delivering the above:

- **If the next action is reversible local work** (code fix, test, doc, small refactor): ACT per founder preferences in CLAUDE.md. Don't ask "should I...?". Do it, document in commit message, report status.
- **If the next action is a hard gate** (push, deploy, new dependency, credential, architecture change): FLAG CLEARLY. Example: "Ready for push? [hash]. Tests 136/136, Health HEALTHY."
- **If truly uncertain** (ambiguity, conflicting guidance, or a tie): Ask ONE short clarifying question max. Then decide + act.

## Rules

- Never include full CLAUDE.md historical text in the summary.
- Skip re-reading full files unless explicitly needed for a specific decision.
- Default to best-practice decisions (secure, clean, tested) over asking. Founder trusts the judgment.
- Flag founder-approval gates clearly and concisely.
- Keep the compressed orientation to under 150 lines total.

## Triggers

- **Session start** — run automatically
- **"Re-compact orientation"** or **"Analyze current state"** — run on request
- **Before any push/deploy** — re-run to confirm state matches expectation

## Example Output

```
## CURRENT STATE

**Blocks:**
- Task #12: GHL trial timing (founder decision, no action needed yet)
- Supabase ap-south-1 incident (external, wait-and-retry)

**Completed This Session:**
- CODE_REVIEW.md fixes #1–#5 all pushed to origin/main

**Next (prioritized):**
- Test real `/chat` with Grok credentials live (no external blocker, self-approvable)
- Monitor Supabase status daily for incident clear, then retry DATABASE_URL auth

**Last Verified:**
- Tests: 136/136 passing
- Health: HEALTHY
- Commit: e0088f0, origin/main: e0088f0 [match]

## LAST ADDENDA SUMMARY
- 2026-07-13: Lovable is canonical frontend, MVP flow complete and live
- 2026-07-12: Supabase incident resolved, E2E intake→site→widget verified working

## RECOMMENDED ACTIONS
1. Make a real `/chat` call against live backend and log result (self-approvable, no credential risk)
2. Monitor Supabase incident status for resolution, then re-test DATABASE_URL if not already passing
3. If GHL trial clock starts, complete GHL wiring (GHL_API_KEY, GHL_LOCATION_ID, Vercel deploy)
```

---

**How to invoke:**
- At session start, Claude auto-invokes this.
- Or manually: "Analyze current state" or "Re-compact orientation"
