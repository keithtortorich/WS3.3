# EXPERIMENTS.md

A log of real experiments as they actually run -- not a framework
document. Add an entry when you start one; fill in the result when it
ends. Nothing here is a process you have to follow, just a place to keep
what you tried and what happened from getting lost between sessions.

## Format

```
## [Date] Experiment name

**What we tried:**
**Why:**
**How we measured it:**
**Result:**
**Decision:** (keep / revert / iterate)
```

Skip sections that don't apply. A one-line entry is fine if that's all
there is to say.

---

No experiments logged yet. First candidates, based on what's already in
motion:

- Ad copy variants from `marketing-director-gtm` skill runs, once any go
  live.
- Pricing tier positioning, if/when tested against real leads.
- Rate limit threshold (`DEFAULT_MAX_REQUESTS_PER_WINDOW` in
  `webstaffr/rate_limit.py`) -- currently a placeholder, not derived from
  real traffic (see `docs/DECISIONS.md` ADR-009). Worth a real entry once
  actual usage data exists to tune it against.
