# Deployment Checklist

**Owner:** Founder (approval gate before any push to production)

**Status:** Ready for pre-launch review as of 2026-07-25

---

## Repository Readiness

- [x] **Tests passing**: 191/191 tests passing (TASKS.md #54, #57)
- [x] **Health check**: 8/8 checks HEALTHY (imports, workflows, tenant isolation, SQLite/Postgres round-trip, Angel routing, booking flow)
- [x] **Tenant isolation verified**: All routes scoped by tenant_id, auth hardening complete (TASKS.md #44, #50)
- [x] **Database migrations**: 0001–0008 applied, no conflicts (TASKS.md #46–#53)
- [x] **Angel worker**: Code-complete, unit-tested (CLAUDE.md migration list, TASKS.md #42)
- [x] **GHL integration**: Implemented (create/update/cancel appointments, retries, error logging) — TASKS.md #39–#40, #44
- [x] **Retell voice wiring**: Code-complete, unit-tested, webhook verification implemented (TASKS.md #50)
- [x] **Env var reference**: Documented (CREDENTIALS.md, local setup instructions)
- [x] **Git hygiene**: No secrets committed (CLAUDE.md baseline, verified TASKS.md #54)
- [ ] **Secrets manager configured**: (awaiting Vercel/hosting decision)

---

## Pre-Launch Verification

**Before deploying to Vercel/production:**

- [ ] **Hosting decision made**: Vercel + Supabase Postgres configured
- [ ] **Environment variables set**: All 7 required vars in Vercel Sensitive settings
  - `GROK_API_KEY`
  - `GHL_API_KEY` + `GHL_LOCATION_ID`
  - `RETELL_WEBHOOK_SECRET`
  - `BOOK_API_KEY`
  - `DATABASE_URL` (Supabase Postgres connection string)
  - `GHL_WEBHOOK_SECRET`
- [ ] **Database initialized**: Supabase migrations 0001–0008 applied to production Postgres
- [ ] **Lovable site builder**: Published and reachable at production URL
- [ ] **CORS configured**: Verified `/chat`, `/intake*`, `/sites/*` allow browser requests; `/book`, `/webhooks/ghl`, `/retell/*` reject browser CORS
- [ ] **Intake form wired**: Frontend accepts contractor email, generates site, stores in tenant DB
- [ ] **Angel widget embedded**: JavaScript loads and connects to production `/chat` endpoint
- [ ] **GHL sync tested**: Booked appointment creates record in GoHighLevel (end-to-end verified with real tenant)
- [ ] **Retell voice tested**: Live inbound call received, webhook payload verified, Angel responds
- [ ] **SMS notifications wired**: Confirmation text sent after booking (GHL integration, not built separately)
- [ ] **Call history visible**: Owner can view past calls and transcripts (UI task, delegated to Lovable)

---

## Customer Readiness (Pilot 1)

**First paying tenant onboarding:**

- [ ] **Tenant created**: Record in `tenants` table with name, phone, hours, timezone
- [ ] **Site generated**: Lovable build complete, published to unique subdomain
- [ ] **Phone number assigned**: Retell agent created, phone number configured with tenant_id metadata
- [ ] **Knowledge base seeded**: FAQs uploaded for AI context (contractor-provided or defaults)
- [ ] **Appointment availability set**: Existing calendar or manual availability configured
- [ ] **GHL account connected**: Location ID and credentials set in env for tenant's workspace
- [ ] **Angel answers inbound call**: Live test call received and handled end-to-end
- [ ] **Appointment booked**: Test booking created in GHL and in WebStaffr DB
- [ ] **SMS confirmation sent**: Owner receives confirmation text
- [ ] **Call review**: Owner can listen to recording and review transcript
- [ ] **Handoff to customer**: Training call, documentation, support contact provided

---

## Post-Launch Monitoring (First 30 Days)

**Operational health checks (daily):**

- [ ] **Inbound call volume**: At least 1 call/day from genuine inquiries
- [ ] **Answer rate**: 100% of calls answered by Angel (no failures/timeouts)
- [ ] **Booking accuracy**: >90% of bookings correctly captured (name, phone, time, service)
- [ ] **GHL sync success**: 100% of booked appointments synced to GoHighLevel without error
- [ ] **Response latency**: Angel starts speaking within 3 seconds of call pickup
- [ ] **Escalation rate**: <5% of calls escalated to owner (low escalation = good qualification)
- [ ] **Transcription quality**: Spot-check transcripts for accuracy; >95% legible
- [ ] **SMS delivery**: 100% of confirmation texts delivered (not bounced)
- [ ] **Error logs**: No unhandled exceptions; all errors logged and investigated within 24h

**Customer satisfaction (weekly):**

- [ ] **Owner feedback**: Contacted for usage observations, issues, feature requests
- [ ] **System uptime**: 99.5%+ (Vercel/Supabase reliability)
- [ ] **First renewal decision**: By day 28, customer decides to renew or cancel (success = renewal)

---

## Rollback Triggers

If any of the following occur post-launch, roll back to last known-good commit:

1. More than 10% of inbound calls fail to connect or timeout
2. Any call data (names, phone numbers) appears in logs or public output
3. GHL sync fails for 3+ consecutive bookings
4. Retell webhook verification fails (customer config issue, but blocks calls)
5. More than 1 customer escalates an issue with answer quality or booking capture
6. Error rate >1% on any endpoint (monitored via Vercel logs)

**Rollback procedure:**
```bash
git revert <commit>
git push
Vercel auto-deploys; monitor logs for recovery
```

---

## Definition of "MVP Validated"

WebStaffr MVP is validated when:

1. At least 1 paying customer is live and answering calls
2. At least 1 inbound call has been successfully answered and booked
3. The customer renews after their first billing cycle (30 days)

All other metrics are operational. Retention is the success signal.

---

**Last Updated:** 2026-07-25
**Next Review:** Before any production deployment
