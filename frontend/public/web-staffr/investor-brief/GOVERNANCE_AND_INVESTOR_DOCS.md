# WebStaffr Governance and Investor Document Source

**Status:** Canonical source. Use this document to recreate every investor-facing artifact from a single governance source.
**Written:** 2026-07-24

---

## Part 1: Governance Rules

### Tier Definitions and Pricing (Hard Rules)
- Office Staff: $497/mo
- Business Manager: $2,497/mo
- Office Staff is the primary acquisition entry point with a 30-day free trial.
- Business Manager is an upgrade tier only, not a trial-tier product.
- ServiceTitan, Jobber, and Housecall Pro are baseline qualification signals, not add-ons, upgrades, or upgrade paths.

### Identity and Integration Boundaries
- SMM (Social Media Marketing Machine) is intended to become the social media manager agent inside WebStaffr, but there is currently no functional integration between them.
- There is no shared network call path, no shared database, and no shared auth.
- SMM tenants use Clerk organization_id from a verified JWT. WebStaffr tenants use bare public strings with shared-secret header auth. Nothing currently maps one to the other.
- Do not write code, routes, or docs that imply a live SMM <> WS3.3 integration exists.

### Investor-Facing Language Rules
- No em dashes. Use colons, commas, or periods.
- Default to conservative anchors: 8% churn planning base, founder-led CAC caveat.
- Always label ramps and accelerated paths as illustrative, not forecasts.
- Do not present retention tooling or templates as current practice; frame as planned/post-validation scaffolding.
- Ad spend is paid directly by the contractor to each platform. WebStaffr does not resell media.

### Technical Integrity Claims
- The platform is live in production. Automated tests passing.
- Do not overstate integration status. ServiceTitan/Jobber/Housecall Pro integration is code-complete/test-covered where applicable, but not live-activated unless explicitly stated.

---

## Part 2: Investor Communication Protocol

### Core Principles
- Transparency first: explicitly flag assumptions, risks, and unproven elements.
- Data beats narrative: prioritize real metrics from trials over illustrative models.
- Cadence and predictability: monthly or bi-monthly updates build confidence.
- Action-oriented: always include clear next steps and offers of help.
- Brevity: scannable updates with bullet points and short paragraphs.
- Tone: confident but humble.

### Cadence
- Monthly updates after milestones or key learnings.
- Quarterly deep dives for full model/churn/CAC review.
- Ad-hoc for major wins or material plan changes.
- Pre-raise / major ask: detailed memo plus call.

### Email/Update Structure
- Subject: specific and positive.
- Opening: warm and purposeful.
- Body: 2-4 bullets for wins, key metrics, honest adjustments, integration/product status.
- Forward look: concrete next milestones.
- Close: grateful and actionable.

### WebStaffr-Specific Rules
- Always caveat optimism when referencing deck numbers.
- Use conservative anchors in all comms: 8% churn planning base, founder-led CAC caveat.
- Highlight ServiceTitan/Jobber integration as de-risking, not decoration.
- Do not present forward-looking templates as current reality.
- Lead with domain credibility; make updates personal and specific.

---

## Part 3: Conservative Planning Baseline

### Market and Product Validation
- Problem stats align with cited investor proposal and investment summary.
- ServiceTitan/Jobber/Housecall Pro as baseline qualification signals is a sound positioning choice.
- Early-stage reality: limited paying customers. Phoenix HVAC beachhead must be proven before multi-city expansion.

### Unit Economics
- 87% gross margin and sub-30-day payback are compelling if assumptions hold.
- CAC is founder-led/organic, unproven past first 50 free builds.
- Planning churn is 8% monthly until real retention data exists. 5-6% is target to earn, not base case.

### Churn Sensitivity (8% Planning Base)
- 8%: ~$5,400 net LTV, ~36x LTV:CAC
- 6%: $7,200 net LTV, ~48x
- 5%: $8,640 net LTV, ~58x
- 10%+: ~$4,320 net LTV, compressed

### ServiceTitan Integration
- Code-complete and test-covered, but not yet live-activated against a real tenant.
- Phased: near-term webhooks/sandbox, interim Zapier/Pipedream, medium-term full sync + Marketplace certification.

### Capital Tiers
- Minimum $10K: legal, validation, live telephone proving, operational buffer.
- Target $25K: ServiceTitan/Jobber integration, automated builds, multi-agent infrastructure.
- Maximum $50K: accelerated Tampa launch, additional hire, extended runway.
- Valuation cap: $150K post-money SAFE, 20% discount on next priced round.

### Growth Trajectory
- Baseline and accelerated models are illustrative and unproven past first 50 free trials.
- Baseline: ~100 customers at Month 12, ~205 customers / ~$1.22M ARR at Month 24 under conservative 8% churn inputs.
- Accelerated: proportional scale-up, not independent cohort model. Can reach 245+ customers faster and scale toward 350-430 customers by Month 24 with higher marketing spend, better conversion, and improved retention.
- Universal disclaimer: all ramps, customer counts, and ARR figures are illustrative curve shapes between modeled milestones, not monthly forecasts.

### Return Scenarios (Illustrative Only)
- $25K investment at $150K cap:
  - $300K trigger: $50K stake value, 2.0x
  - $500K trigger: $83.5K stake value, 3.3x
  - $1M trigger: $167K stake value, 6.7x
  - $2M trigger: $334K stake value, 13.4x

---

## Part 4: HVAC Retention Tactics (Research Source)

### Core Levers
- Maintenance agreements: #1 retention tool. Top performers derive 25-40% of revenue from plans.
- Rapid response: 78% of homeowners hire the first responder.
- Personalization: service history for tailored recommendations, technician continuity.
- Review management: automated requests, reputation monitoring.
- Loyalty: referral programs, membership perks, seasonal promotions.

### Technology-Enabled Tactics
- CRM/FSM integration automates booking and follow-ups.
- Virtual receptionist addresses missed calls, a major churn driver.
- Data-driven insights predict maintenance needs.
- Online booking/self-service reduces friction.

### Metrics
- Maintenance plan members: 70-85% annual retention.
- One-off customers: 30-50% annual retention.
- Well-run maintenance programs increase CLV by 2-3x.

### Implementation Roadmap
1. Foundation: FSM/CRM + automated communications.
2. Offer plans: 2-3 tiered maintenance agreements.
3. Automate retention: surveys, review requests, check-ins.
4. Measure: retention rate, renewal rate, NPS quarterly.
5. WebStaffr synergy: virtual staff for 24/7 coverage and follow-up automation.

### Risks
- Seasonality causes perceived churn.
- Price sensitivity: plans must show clear value.
- Competition from big-box/new entrants.

---

## Part 5: Source Bibliography

### Industry Reports & Market Data
- CallRail. (2025-2026). Home Services Benchmark Reports. Missed call rates, response times, lead conversion.
- Invoca. (2025-2026). The Cost of Missed Calls. 27% average missed call rate, revenue impact.
- ServiceTitan. (2025-2026). Benchmarks and case studies. Maintenance agreements, 20-25% revenue lifts, retention via FSM.
- Angi / HomeAdvisor. (2025-2026). Consumer behavior. 78% hire first responder, review impact.
- Jobber. (2026). Home Service Trends Report. Operations, retention, technology adoption.

### Financial & Operational Benchmarks
- Profitability Partners. (2026). HVAC financial analyses. Maintenance plans 25-40% revenue for top performers.
- IBISWorld, Mordor Intelligence. (2025-2026). Market size, fragmentation, recurring revenue.

### Platform & Integration References
- ServiceTitan Developer Documentation. (2026). V2 API, Webhooks, Leads Integration Platform, App Marketplace Program Guide. developer.servicetitan.io, marketplace.servicetitan.com.

### Additional Supporting Sources
- Recurly and CustomerGauge. (2025-2026). SaaS churn benchmarks.
- Contractor magazine, online forums, profitability guides. Technician continuity, personalization, loyalty programs.

### Methodology Notes
All figures drawn from publicly available 2025-2026 reports, platform benchmarks, and aggregated practitioner data. Ranges reflect top-quartile outcomes, not universal averages. Primary sources prioritized.

---

## Part 6: Recreation Rules for Investor-Facing Documents

When recreating any investor-facing document from this source:

1. **Tier pricing:** Office Staff $497/mo, Business Manager $2,497/mo. Do not use old lower-priced figures.
2. **Churn:** Default to 8% planning base in all investor communications. 5-6% is aspirational.
3. **CAC:** Always caveat as founder-led/organic, unproven past first 50 builds.
4. **Ad spend:** State clearly that contractor pays directly to platforms. WebStaffr does not resell.
5. **SMM agent:** Position as bundled inside Business Manager, not a separate add-on.
6. **Illustrative labeling:** All growth charts and ramps must carry "illustrative only" labels.
7. **No em dashes:** Use colons, commas, or periods in all investor-facing text.
8. **Integration status:** Do not imply live SMM <> WS3.3 integration. Describe as intended future architecture only.
9. **Retention tooling:** Describe as planned/post-validation, not current practice.
10. **Sources:** Cite this document or BIBLIOGRAPHY.md when pressed for backing.

---

## Part 7: One-Page Investor Brief Template

### Header
- WebStaffr Investor Brief
- Confidential
- Operational revenue recovery for home service contractors. Live product, tested stack, $150K SAFE cap.

### Metrics Grid
- Listing price: $497 / $2,497
- Ad spend: separate, paid by contractor
- Gross margin: ~87%
- Technical status: live + tested
- TAM: ~$14.6B
- Beachhead: Phoenix HVAC
- Planning churn: 8% monthly
- Planning CAC: founder-led, unproven past 50 builds

### Model Section
- Baseline vs accelerated chart
- Baseline Month 12: ~100 customers
- Baseline Month 24: ~205 customers / ~$1.22M ARR
- Accelerated: 245+ customers faster, 350-430 by Month 24
- Status: illustrative, not forecast

### Tier Table
- Office Staff $497/mo: receptionist, advisor, lead coordinator, reputation, website ops
- Business Manager $2,497/mo: above plus sales consultant, marketing coordinator, ops manager, social media manager agent
- Note: flat platform fee, no ad markup

### Churn Sensitivity
- 8% planning base: ~$5,400 LTV, ~36x
- 6% target: $7,200 LTV, ~48x
- 5% stretch: $8,640 LTV, ~58x
- 10%+ risk: compressed

### Capital Tiers
- Minimum $10K
- Target $25K
- Maximum $50K
- Valuation cap $150K

### Return Scenarios
- 2.0x to 13.4x on $25K investment

### Close
- Next step: validate first 50 trials with rigorous metrics
