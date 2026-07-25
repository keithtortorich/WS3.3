# WebStaffr Governance Manual
**Unified Source of Truth for Product, Strategy, Operations, and Brand**

Version 1.0 | Last Updated: 2026-07-18

---

## Table of Contents

1. [Core Doctrine](#core-doctrine)
2. [Market & Strategic Positioning](#market--strategic-positioning)
3. [Product Definition](#product-definition)
4. [Unit Economics & Financial Model](#unit-economics--financial-model)
5. [Go-to-Market & Customer Acquisition](#go-to-market--customer-acquisition)
6. [Brand & Communication Standards](#brand--communication-standards)
7. [Operational Governance](#operational-governance)
8. [Technical Architecture](#technical-architecture)
9. [Key Risks & Constraints](#key-risks--constraints)
10. [Team & Decision Authority](#team--decision-authority)

---

## Core Doctrine

### The Central Principle

**We Don't Sell Technology. We Recover Revenue.**

This statement governs every corporate, sales, and product decision. It is not a tagline; it is the decision-making filter.

### The Problem We Solve

Home-service businesses do not lose jobs because they lack technology. They lose jobs because they miss opportunities.

**The specific opportunity:** 27% of home-service calls go unanswered every day. Of those missed calls, 85% never call back—they call a competitor instead.

**The outcome contractors buy:** More booked jobs. Fewer missed calls. Revenue recovered from leads that would otherwise be lost.

### The Competitive Position

We compete on the *full handoff chain*, not on any single feature.

**The handoff chain:**
1. A lead lands on the website
2. The Service Advisor pre-qualifies it
3. The 24/7 Receptionist books the appointment (phone or chat)
4. The Lead Coordinator follows up with anyone who didn't book
5. The Reputation Manager closes the loop after the job
6. The Website Operations Manager keeps the site current

A contractor who trusts the Receptionist will trust the rest of the office. We earn the right to expand by solving one expensive problem first.

### The Complexity Principle

**We absorb complexity so customers experience clarity.**

Customers see clean outcomes: booked jobs, closed leads, automated follow-up. They do not see the infrastructure, orchestration, or AI machinery behind it. All technical complexity lives inside WebStaffr; none of it appears between WebStaffr and the customer.

---

## Market & Strategic Positioning

### Market Opportunity

- **Total Addressable Market (TAM):** $14.6 billion
- **Market Size:** Approximately 2.5 million United States home-service businesses
- **Serviceable Addressable Market (SAM):** $2.9 billion (digitally active segment)

### Beachhead Strategy

**Primary Beachhead:** HVAC contractors in Phoenix, Arizona

- **Company Size:** 3–15 employees
- **Annual Revenue:** $500K–$3M
- **Current Pain:** Missed calls, slow follow-up, manual lead management, outdated websites
- **Purchase Signal:** Already using ServiceTitan, Jobber, Housecall Pro, or similar field-service-management software (signals operational sophistication and SaaS adoption)

### Year-One Serviceable Obtainable Market (SOM)

Approximately $440,000 in addressable market within the Phoenix HVAC beachhead.

### Strategic Messaging

1. **For Contractors (Commercial Voice):**
   - "Your office staff, working 24/7"
   - "Answer every call. Close every lead."
   - "Stop losing work to voicemail"

2. **For Investors (Executive Voice):**
   - Operational revenue-recovery platform, not AI feature company
   - Proven unit economics: 87% gross margin, <1-month payback on acquisition
   - Free website is the lead hook; paid staff is the business
   - Beachhead plays directly into existing SaaS/field-service ecosystem

---

## Product Definition

### The Free Website Builder

**Purpose:** Lead hook. Customer acquisition mechanism.

**Economics:** The generated website is free to the contractor and costs WebStaffr nothing extra, since the underlying toolchain runs on free hosting and development tiers. A contractor claims a site, sees it live within minutes, and only afterward is offered the staff behind it.

**Principle:** The free site brings the contractor in. The paid plans are the business built on that relationship.

### Pricing Tiers

All tiers include the free generated website for 30 days. After 30 days, the contractor can keep the website and staff by subscribing to one of the plans below.

| **Tier** | **Monthly Price** | **Includes** | **Gross Profit** |
|---|---|---|---|
| **Office Staff** | $497/mo | Service Advisor, 24/7 Voice Receptionist, Lead Coordinator, Reputation Manager, Website Operations Manager | $432/mo (87%) |
| **Business Manager** | $2,497/mo, plus the contractor's own ad spend | Everything in Office Staff, plus Sales Consultant, Marketing Coordinator, Growth Manager | $2,148/mo (86%), before ad spend (ad spend is a pure pass-through, paid by the contractor directly to each ad platform, never marked up or included in WebStaffr's revenue or COGS) |
| **White-Glove** | $5,000+/mo custom | Siphony consulting, custom-fitted solutions, bespoke integrations | Negotiated per engagement |

**Business Manager tier, implied per-role value of the $2,000/mo delta over Office Staff:**

| **Role** | **Implied Value** | **Basis** |
|---|---|---|
| Marketing Coordinator | ~$1,000/mo | Market-anchored, managed-service portion only: standalone equivalents (part-time in-house hire, home-services agency retainer, contractor marketing SaaS) cluster $2,000-$4,000/mo for running paid ads across Meta and any other platforms the contractor uses; discounted for bundled/automated delivery. Excludes the contractor's own ad spend, which is a separate, additional cost the contractor pays directly to each platform. |
| Sales Consultant | ~$600/mo | Remaining delta, weighted above Growth Manager for direct revenue-attach responsibility (upsell/cross-sell identification) |
| Growth Manager | ~$400/mo | Remaining delta; analytics/reporting role, lower standalone market cost than active marketing or sales execution |

These per-role figures are an internal pricing rationale, not separately sold line items. Contractors buy the bundled tier, not individual roles. **Ad spend disclosure is non-negotiable in any customer-facing description of this tier:** the $2,497/mo price covers WebStaffr's managed marketing service (strategy, account management, multi-platform ad optimization), not the media cost itself. A contractor running ads on Meta and even one or two other platforms should expect to budget separately for that spend on top of the $2,497/mo fee.

**Acquisition Strategy:**
- **Office Staff** is the primary acquisition target. This is where founders spend acquisition effort and capital.
- **Business Manager** is an upgrade sold to an existing Office Staff customer, not separately acquired.
- **White-Glove** serves high-value customers with unique needs (multi-location operations, custom integrations, managed services).

### Product Roles & Responsibilities

Each role corresponds to a specific job the contractor is trying to accomplish:

1. **Service Advisor** – Pre-qualifies leads before they reach the Receptionist
2. **24/7 Receptionist** – Answers calls and chat; books appointments by phone or chat
3. **Lead Coordinator** – Follows up with anyone who didn't book
4. **Reputation Manager** – Closes the loop after the job (reviews, feedback, customer satisfaction)
5. **Website Operations Manager** – Keeps the website current, fresh, and accurate
6. **Sales Consultant** (Business Manager tier) – Identifies upsell and cross-sell opportunities within existing customers
7. **Marketing Coordinator** (Business Manager tier) – Runs paid social and search advertising (Meta/Facebook and Instagram ads at minimum, plus any other platforms the contractor already has a presence on, such as TikTok, LinkedIn, Nextdoor, YouTube, or Google), manages seasonal campaigns, and optimizes toward actual ROI (cost per booked job), not vanity metrics like impressions or clicks. **This is the most operationally complex role in the Business Manager tier**, not a lightweight add-on: running and optimizing paid ad accounts across multiple platforms is real, ongoing account-management work, materially heavier than the other two Business Manager roles. **Standalone market value: approximately $1,000/mo for WebStaffr's managed service**, on top of which the contractor separately pays their own ad spend directly to each platform (Meta, Google, etc.) — that spend is never included in the $2,497/mo price and scales with however many platforms and how aggressively the contractor wants to advertise. Real-world equivalents for the managed-service portion alone cluster $2,000-$4,000/mo (a part-time in-house marketing hire, a home-services marketing agency retainer, or ServiceTitan-style marketing add-ons layered with agency time); $1,000/mo reflects a conservative anchor since this role is automated and bundled rather than a dedicated human hire, and it explicitly excludes the ad spend itself. Source: 2026 market research on part-time marketing coordinator wages, home-services agency retainers, and contractor marketing SaaS add-ons (Salary.com, ZipRecruiter, Hook Agency, ClicksGeek, Arc4, ServiceTitan Marketing Pro pricing).
8. **Growth Manager** (Business Manager tier) – Analyzes operational metrics, identifies expansion opportunities, scales the contractor's operation

### Integration Ecosystem

WebStaffr operates inside the contractor's existing software stack. The baseline environmental signals are field-service-management tools already in daily use:

- **ServiceTitan** (HVAC, plumbing, electrical, roofing, landscaping)
- **Jobber** (HVAC, plumbing, electrical, roofing, landscaping, handyman)
- **Housecall Pro** (HVAC, plumbing, electrical, roofing, landscaping, handyman)

A contractor already paying for and operating inside one of these tools is a **warmer, faster-converting lead** than one with no field-service software at all, because tool adoption implies a business large enough to systemize and already comfortable with SaaS workflow costs.

---

## Unit Economics & Financial Model

### Gross Margin

- **Office Staff:** $497/mo revenue, $65/mo delivery cost = **$432/mo gross profit (87%)**
- **Business Manager:** $2,497/mo revenue, $349/mo delivery cost = **$2,148/mo gross profit (86%)**, excluding the contractor's own ad spend
- **White-Glove:** Custom, negotiated per engagement

Delivery cost includes AI inference (Grok), voice infrastructure (Retell), integrations (ServiceTitan, GoHighLevel), and operational overhead. **It does not include ad spend.** Business Manager customers running Meta ads (and any other platform) pay that media cost directly to the platform; it never flows through WebStaffr's revenue or COGS, so it does not affect this margin calculation in either direction.

### Customer Acquisition Cost (CAC)

- **Organic CAC (founder-led + referrals):** $100–$200 per paying customer
- **Paid Acquisition (future, not current):** Likely higher; current model is under-optimized for paid acquisition and should not scale there until the first 50 free builds confirm real conversion rate

**CAC Assumption Notes:**
- Current organic CAC is defensible because the free-website funnel converts warmer leads (ServiceTitan/Jobber users) at lower cost
- Paid ad spend would push CAC higher and change unit economics materially
- Gating paid acquisition spend on real conversion data from the first 50 free builds is a non-negotiable decision rule

### Customer Lifetime Value (LTV)

- **Average Customer Lifetime:** 16.7 months
- **Monthly Churn Rate:** 6% (structured onboarding at day 1, day 7, day 30 to track early engagement; early call activation is the leading indicator)
- **LTV:** $7,200 (based on Office Staff; Business Manager upgrades carry no separate CAC and extend LTV per customer)

### LTV:CAC Ratio

- **Strong:** 36x–72x payback ratio
- **Payback Period:** <1 month
- **Important caveat:** These figures are unproven past the first 50 free builds. They assume current organic acquisition and conversion rates hold. Treat them as planning estimates, not steady-state benchmarks, until the first 50 free-builds milestone is reached.

### Financial Projections

**Model Assumptions:**
- 100 free 30-day Office Staff trials in month 1; 50/month thereafter
- 10% conversion to paid (conservative; real rate may be higher)
- 6% monthly churn
- $150 CAC per paid customer (conservative, not current organic CAC)
- $3,000/month fixed costs
- $25,000 starting capital

**Year One (Phoenix HVAC):**
- Cash-positive by month 3
- Year-end: ~44 customers, ~$261K ARR, ~$115,325 cumulative cash

**Year Two (Phoenix + Tampa; Tampa launches month 13):**
- ~108 customers, ~$646K ARR, ~$489K cumulative cash

**Downside Case (5% conversion instead of 10%):**
- ~22 customers, ~$131K ARR, ~$52,163 cumulative cash
- Still cash-positive **if CAC holds at $100–$200**
- If the free-website funnel underperforms and paid acquisition becomes necessary, this case worsens materially

---

## Go-to-Market & Customer Acquisition

### The Free Website Lead Hook

The free generated website is the acquisition engine.

**How it works:**
1. Contractor discovers WebStaffr (founder outreach, referral, organic search)
2. Contractor signs up, provides business details via intake form
3. WebStaffr generates a live website within minutes (no payment required)
4. Contractor sees the site live, can show it to others, uses it immediately
5. After 30 days, contractor is offered the paid staff plans ($497 or $2,497/mo)

**Why it works:**
- **Low friction:** No payment upfront; see the value immediately
- **Warm lead qualification:** Only contractors motivated enough to build a site are prospects for the paid plans
- **Viral mechanics:** A live website is shareable; contractors show it to peers, creating organic referrals
- **Sticky:** Once a contractor has a live site and an answering Receptionist, switching costs are high

### Acquisition Channels

**Current (Organic, Founder-Led):**
- Direct outreach to HVAC contractors in Phoenix (via phone, email, LinkedIn)
- Referrals from existing customers
- Organic search (SEO on generated sites + WebStaffr.com positioning)

**Future (Paid, After First 50 Free Builds):**
- Only after real conversion data confirms 10%+ rate
- Likely channels: Google Local Services Ads, Facebook/Instagram for contractors, industry-specific marketplaces
- CAC likely $200–$400; only viable if LTV holds or improves

### Conversion Funnel Metrics

**Metrics that matter (no vanity metrics):**
- Phone answer rate (for inbound leads)
- Demo booking and attendance rate
- Trial (free 30-day) activation rate
- Free-to-paid conversion rate
- Monthly churn
- Net revenue retention (upgrades + cross-sell)
- Customer lifetime value

**Metrics that don't matter:**
- Email sends
- Website visits
- Total sign-ups (only paid conversions count)

### Sales Philosophy

**Target behavior, not demographics.** The best customers are successful but operationally under-optimized:
- Outdated website or no website at all
- No automated follow-up on leads
- An office overwhelmed by demand
- Already using field-service-management software (signals willingness to pay for operations tools)

**Earn the right to expand.** Solve one expensive problem first (the Receptionist). A customer who trusts the Receptionist will trust the rest of the office (the Business Manager tier and beyond).

---

## Brand & Communication Standards

### Visual Identity

**WebStaffr Logo & Typography:**
- Typeface: **Garamond Bold Italic**
- Sizing: **1 font size larger than surrounding text** (to compensate for Garamond's smaller visual weight)
- Color Options:
  - **Option 1 (Split):** "Web" in #999999 (gray), "Staffr" in #bf9000 (gold)
  - **Option 2 (Unified):** #1f4d78 (deep blue)
- Treatment: Always intentional. Never casual. Reflects premium positioning.

**Forbidden Punctuation:**
- **No em-dashes (—) anywhere in WebStaffr copy**, internal or external. Use hyphens or rewrite sentences instead.
- This applies to marketing, sales materials, investor decks, internal documentation, everything.

### Two Communication Styles

WebStaffr maintains two distinct but consistent communication voices, depending on audience.

#### Executive Voice
**Used for:** Leadership, investors, engineering, strategy, internal governance, white papers

**Characteristics:**
- Elevated vocabulary
- Precise language
- Calm authority
- Executive polish
- Accuracy before persuasion
- Assumes financial/technical sophistication

**Example (Investor Email):**
"Gross margin of 87% on the Office Staff tier, with a sub-one-month payback period on founder-led acquisition, reflects the economic efficiency of the handoff-chain model."

#### Commercial Voice
**Used for:** Contractors, marketing, advertising, websites, sales materials, onboarding

**Characteristics:**
- Simple language (~Grade 8 reading level)
- Outcome-focused, not feature-focused
- High readability (short sentences, ample spacing, large font)
- Tradesperson-friendly (respects contractor's time, speaks their operational language)
- Occasional premium metaphors or luxurious puns (never sacrificing clarity)
- Conversational authority (confident, not condescending)

**Example (Customer-Facing):**
"Your office staff, working 24/7. Answer every call. Close every lead. Stop leaving money on the voicemail."

### Brand Messaging Framework

**Core Value Proposition (Commercial):**
"WebStaffr is your office staff, working 24/7. We answer every call, book every job, and follow up on every lead so you don't miss another customer."

**Core Value Proposition (Executive):**
"WebStaffr is an operational revenue-recovery platform that deploys AI office staff into the home-service workflow, capturing missed-call opportunities and converting them into booked appointments and revenue recovery."

**What We Are NOT:**
- Not an AI feature company
- Not a chatbot
- Not a call center
- Not software-as-a-service for contractors (contractors don't buy features; they buy outcomes)

**What We Solve:**
- Customers want outcomes: more booked jobs, fewer missed calls, recovered revenue
- They do not want to hear about technology, AI, integrations, or infrastructure
- Complexity belongs inside WebStaffr; clarity belongs between WebStaffr and the customer

### Governing Principles for All Copy

Every sentence, design choice, and recommendation should:

1. **Reinforce the doctrine:** "We Don't Sell Technology. We Recover Revenue."
2. **Demonstrate the complexity principle:** Show that we absorb the hard work; the contractor just enjoys the results
3. **Focus on outcomes, not features:** Talk about booked jobs and recovered revenue, not chat widgets or voice AI
4. **Respect the contractor's time:** Be concise, clear, actionable
5. **Build confidence in operations:** Premium organizations communicate with confidence, restraint, and consistency

---

## Operational Governance

### Development Process

**Self-Approval Scope (Claude AI can execute without explicit founder approval):**
- Any reversible local-only change (code edits, tests, docs, small refactors)
- Improvements following best practices (auth, rate limits, error handling, test coverage, performance, security scoping)
- Any change that keeps tests passing and health check HEALTHY

**Requires Explicit Founder Approval:**
- Git push or any deploy
- New dependencies
- Architecture, data model, or database schema changes
- Anything involving credentials, secrets, production systems, Lovable, Vercel, or Supabase
- High-ambiguity decisions that could materially affect cost or live behavior

**Decision-Making Philosophy:**
- Play it safe on anything irreversible
- On reversible work: use current best practices, make the best decision possible, and act
- Default to production-grade safe choices: proper error handling, scoped auth/CORS, rate limiting, clean code, targeted tests, no unnecessary complexity
- One short clarifying question maximum if truly uncertain; otherwise, act and document the choice

### Test Coverage

- **Local Development:** SQLite backend, fast hermetic tests
- **Production:** Postgres backend via Supabase
- **Test Requirement:** All code changes must keep 100% of tests passing
- **Health Check:** Must remain HEALTHY after any change
- **Verification Principle:** Independently verify claimed fixes in a fresh context before trusting the report; one re-test is cheaper than a wrong "done" claim entering git history

### Documentation & Status Tracking

- **Single source of truth for live status:** TASKS.md (updated at the end of each session)
- **Operational history and decisions:** CLAUDE.md addenda (chronological, append-only)
- **Governance and long-term principles:** This document (WEBSTAFFR_GOVERNANCE.md)

**Session Structure:**
- Orientation: Read TASKS.md + last CLAUDE.md addendum only
- Work: Act decisively on reversible items; ask for approval on irreversible ones
- Close: Update TASKS.md with completion status; add a CLAUDE.md addendum if a durable decision was made

### Security Baseline

- **No secrets, credentials, or tokens committed at any point**, including in comments, examples, or fixtures
- See CREDENTIALS.md for the authoritative list of environment variables and how they're used
- Treat external/legacy content as unverified until checked against current facts before reuse
- New dependencies require explicit approval tied to the specific choice
- RLS (Row-Level Security) enabled on all Supabase tables with default-deny policy; future client-side access must be validated against this

### Diff Hygiene

Before reviewing any changed file:
1. Start with `git diff --stat` to see which files actually changed meaningfully
2. Deep-read only the files the stat implicates, not every modified file
3. Do not trust code review alone; re-test in a fresh context if any doubt exists

---

## Technical Architecture

### Backend Stack

- **Framework:** FastAPI (Python)
- **Hosting:** Vercel (serverless)
- **Database:** Supabase Postgres (production); SQLite (local dev/tests)
- **Voice:** Retell AI (phone calls, signature verification, function calling)
- **AI Chat:** Grok (xAI) for customer chat and lead qualification
- **CRM Integration:** GoHighLevel (future, trial-gated)
- **Field-Service Integration:** ServiceTitan, Jobber, Housecall Pro

### Frontend Stack

- **Canonical Customer Site:** Lovable "Site Weaver" (React, Vite, shadcn/ui) – multi-tenant, dynamically renders contractor data from backend `/sites/{tenant_id}` endpoint
- **Developer Portal:** Parked local Vite+React scaffold (`frontend/`) – not canonical, not actively developed unless decision changes

### Data Architecture

**Dual-Backend Strategy:**
- **Local Dev/Tests:** SQLite (fast, hermetic, no external dependencies)
- **Production:** Postgres via Supabase (real database, RLS default-deny, automatic backups)
- **SQL Dialect:** All SQL written in SQLite dialect; compatibility shim in `db.py` translates to Postgres at runtime (no ORM; direct SQL with `Protocol`+`Null*` pattern for integrations)

**Multi-Tenant Model:**
- **Tenant Isolation:** Every row in every table is scoped to `tenant_id`
- **No Cross-Tenant Queries:** Queries are built to filter by tenant_id at the application level
- **Public Endpoints:** `GET /sites/{tenant_id}` is deliberately public; no authentication required (returns 404 for unknown tenants, same as for uninitialized tenants; does not leak which tenant_ids are real)

### API Architecture

**Public Endpoints (no auth, public data only):**
- `GET /sites/{tenant_id}` – Returns curated contractor data for the Lovable site; no internal fields leak
- `GET /intake/presets` – Industry-specific form hints and software options
- `GET /intake/presets/{industry}` – Industry-specific presets

**Customer-Facing Endpoints (auth required or rate-limited):**
- `POST /intake` – Accept contractor intake submissions; generate tenant_id
- `POST /chat` – Customer chat with Receptionist; rate-limited (30 req/60s), message length-capped (4000 chars)

**Webhook Endpoints:**
- `POST /book` – External booking system callbacks; shared-secret auth via `X-API-Key`
- `POST /webhooks/ghl` – GoHighLevel lifecycle events; shared-secret auth via `X-Webhook-Secret`
- `POST /retell/webhook` – Retell voice call lifecycle; HMAC-SHA256 signature verification

**Health & Status:**
- `GET /health` – Simple health check, returns 200 if app boots cleanly (no DB connection required)

### Integration Patterns

All integrations follow the same pattern:

1. **Protocol Definition:** Interface that defines the integration contract
2. **Null Implementation:** No-op fallback that's safe to call; never crashes
3. **Real Implementation:** The actual vendor-specific code
4. **Dependency Injection:** Router accepts the integration instance as a parameter; tests inject Null version

This pattern makes integrations optional, testable, and safe to stub out before credentials are configured.

---

## Key Risks & Constraints

### Non-Negotiable Constraints

1. **Identify a problem, deliver an outcome.** Customers want booked jobs and fewer missed calls, not technology explanations.
2. **Measurable ROI only.** Every recommendation must answer: "Will this recover more revenue than it costs?"
3. **Operational dependence.** Marketing gets cut during downturns. Operations rarely do. We compete on the full handoff chain, not on a single feature.
4. **Earn the right to expand.** Solve one expensive problem first. A customer who trusts the Receptionist will trust the rest of the office.

### High-Level Risks

| **Risk** | **Impact** | **Mitigation** |
|---|---|---|
| Free-to-paid conversion below 10% | Unit economics collapse; CAC becomes unjustifiable | Gate paid acquisition spend on real conversion data from first 50 free builds |
| Organic CAC does not hold at $100–$200 | Shift to paid acquisition raises CAC materially; LTV:CAC deteriorates | Conservative financial modeling; paid spend only after proving organic conversion |
| Voice unproven on a live call | Lead quality and booking accuracy unclear; customer trust at risk | Retell integration built and unit-tested; live phone test is next milestone |
| Churn above 6% | LTV collapses; customer acquisition becomes uneconomical | Structured onboarding at day 1, day 7, day 30; early call activation tracked as leading indicator |
| Regulatory exposure (calling/texting) | Legal liability; service disruption; customer trust damage | Email-first outreach; consent-based contact; do-not-call scrubbing; 10DLC registration |
| Competition from single-feature tools | Price compression; loss of differentiation | We compete on the full handoff chain, not on any single feature. Switching costs are high once the Receptionist is trusted. |
| GoHighLevel integration delays | Calendar sync breaks; appointment data inconsistency | Integration scaffolding complete and tested; activation is a founder call (trial-timing decision) |
| Supabase availability or incident | Service disruption; data inaccessibility | Dual-backend strategy (SQLite fallback); status page monitoring; graceful 503s on DB failure |

### Strategic Risks

1. **Market Risk:** HVAC contractors may not be ready for AI-driven office staff (adoption lag, trust, training)
2. **Competitive Risk:** Larger players (e.g., field-service software incumbents) could build similar features
3. **Regulatory Risk:** State and federal regulations on AI-driven calling/texting could change
4. **Economic Risk:** Contractor spend on operations gets cut during economic downturns

---

## Team & Decision Authority

### Founder

**K. Michael Tortorich, MD**

**Authority:**
- Sets vision, strategy, and go-to-market direction
- Approves all irreversible changes (deploys, schema changes, new dependencies, credential configurations)
- Makes high-ambiguity decisions that materially affect cost or live behavior
- Makes personnel and contractor engagement decisions

**Decision Philosophy:**
- Founder is not a coder; minimize questions, reduce friction, keep momentum
- Clear one-sentence summary of any decision option; founder decides
- Do not ask for approval on reversible local changes; act and document

### Technical Contributors

**Patrick Bukowski** – Operations and client success as needed (not co-founder, not full-time)

**Wenjie Tong** – Product architecture and engineering as needed (not co-founder, not full-time)

**Claude AI (via Cowork/Claude Code)** – Backend logic, Angel worker, tests, migrations, architecture work (per Self-Approval Scope above)

### Decision Authority Matrix

| **Decision Type** | **Authority** | **Timeline** |
|---|---|---|
| Reversible code changes (tests, refactors, docs) | Claude AI (self-approve) | Immediate |
| Deployment to production | Founder (explicit approval) | Before push |
| New dependencies | Founder (explicit approval) | Before merge |
| Schema or data model changes | Founder (explicit approval) | Before merge |
| Credential configuration | Founder (direct action) | As needed |
| Go-to-market direction | Founder | Strategic |
| Customer acquisition spending | Founder | With data gate |
| Pricing or tier changes | Founder | Strategic |

---

## Final Notes

### This Document is the Source of Truth

This manual supersedes and consolidates:
- CLAUDE.md (operational history and session addenda) → Governance principles now live here
- TASKS.md (task status) → Remains the single source of truth for current task state
- Scattered project instructions → Unified here
- Investor email and business plan → Core positioning and economics locked in here

### How to Use This Document

1. **For Onboarding:** New contributors read this document for the full context
2. **For Decision-Making:** Before deciding, check Section 7 (Operational Governance) and Section 10 (Team & Decision Authority)
3. **For Brand Consistency:** Check Section 6 (Brand & Communication Standards) before writing any customer-facing copy
4. **For Roadmap Clarity:** Sections 2–3 show what we're building and for whom
5. **For Risk Assessment:** Section 9 lists known risks and constraints

### Maintenance

- Update this document when strategic decisions change (pricing, beachhead, team composition, architecture)
- Do NOT use this for session notes or daily status; that's TASKS.md
- Do NOT use this for operational history; that's CLAUDE.md addenda
- This document is for principles, governance, and decisions that persist

---

**End of WebStaffr Governance Manual**
