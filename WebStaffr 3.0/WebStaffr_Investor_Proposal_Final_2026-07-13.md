# WebStaffr
## Investment Proposal
### July 13, 2026 (updated July 24, 2026 : ServiceTitan integration and attribution/call-tracking status added, churn corrected to reconciled 8% planning base)

---

## Executive Summary

WebStaffr is an operational revenue recovery platform for home service contractors, built first for HVAC. Contractors lose jobs they already paid to generate because they cannot answer every call. WebStaffr deploys always on office staff, a Receptionist first, with a Lead Coordinator, Reputation Manager, and Website Operations Manager layered in over time, so no customer is lost to a missed call.

WebStaffr does not sell technology. It recovers revenue.

The platform is live today. The backend is deployed, tested, and answering real customer inquiries in production. This proposal covers current status, market opportunity, product and pricing, unit economics, financial projections, and the investment terms.

---

## Current Status

The core product is built and running, not a plan on paper.

The backend is deployed and healthy at a public production address, confirmed responding correctly at the time of writing. A contractor can submit intake information and have a live customer site generated from it end to end, verified this month with no leakage of internal or sensitive fields into public output. The Receptionist answers customer questions live in production with contextually relevant responses, not a scripted greeting. The full automated test suite passes: 136 of 136 tests. The complete build history is available in a public code repository.

Telephone voice service is built and tested in isolation but has not yet handled a live inbound call; a phone number has not yet been connected. The customer facing website builder renders real contractor data correctly when accessed directly, but the hosting project is not yet public; publishing it is a short remaining step, not unfinished engineering. Integration with a customer relationship management platform has not started, a deliberate sequencing choice tied to when the trial period on that platform should begin.

Two additional systems were completed since the platform first went live. A ServiceTitan integration, the field service management platform used by a large share of the HVAC beachhead, is code complete and covered by its own test suite. It is not yet activated against a live contractor account; that activation is a configuration step, not further engineering. An attribution and call tracking system is also built and tested: every tenant gets a tracking identifier, and every call and booking event is logged against it, producing real per tenant performance metrics. This is the foundation a future pays for itself guarantee will be built on, once enough tenants have run long enough to back that guarantee with real numbers rather than a model.

The core value loop, from incoming customer to answered call to qualified lead to booked appointment to team notification, is real and operating today for chat based interactions. Voice by telephone is the immediate next milestone.

---

## The Problem

Twenty-seven percent of home service calls go unanswered daily. Eighty-five percent of voicemail callers never call back; they call a competitor instead. Seventy-eight percent of homeowners hire whoever responds first.

Contractors lose jobs they already paid to generate because they cannot answer the phone, and labor shortages make hiring a human receptionist impractical at their scale.

---

## Market Opportunity

| Metric | Value | Basis |
|---|---|---|
| Total addressable market | $14.6B | Approximately 2.5 million United States home service businesses |
| Serviceable addressable market | $2.9B | Digitally active segment |
| Serviceable obtainable market, year one | Approximately $440K | Phoenix HVAC beachhead only |

The initial market is HVAC contractors in Phoenix, Arizona, with three to 15 employees and $500K to $3M in annual revenue. Demand and competitive gap in this market do not erode meaningfully over a short delay, and the product is materially further along today than when this beachhead was selected.

---

## Product and Pricing

WebStaffr sells staff, not software. Every plan is a Monthly Workforce Investment, not a subscription.

### Office Staff (Recommended), Monthly Workforce Investment $497
"Stop losing jobs you already paid to win." Includes the Service Advisor, 24/7 Receptionist, Lead Coordinator, Reputation Manager, and Website Operations Manager.

The handoff chain is the product. A lead lands on the website. The Service Advisor pre-qualifies the inquiry. The Receptionist books the appointment on the spot. The Lead Coordinator follows up with anyone who did not book. The Reputation Manager closes the loop after the job is complete. The Website Operations Manager keeps the site current.

### Business Manager, Monthly Workforce Investment $2,497, plus the contractor's own ad spend
"Grow past what your current customers can give you." Adds a Sales Consultant, Marketing Coordinator, and Growth Manager on top of the full Office Staff roster.

The Marketing Coordinator role runs paid social and search advertising, Meta at minimum plus any other platform the contractor has a presence on, and optimizes toward cost per booked job rather than vanity metrics. This is real, ongoing multi-platform ad account management, the most operationally complex role in this tier, priced accordingly. The $2,497 figure is WebStaffr's managed-service fee only. Ad spend itself is paid by the contractor directly to each platform and is never included in or marked up by this price.

These price points are locked, founder-confirmed figures, current as of the WebStaffr Governance Manual (2026-07-18), which supersedes the earlier $997 Business Manager figure found in prior drafts (see Section 12).

ServiceTitan, Jobber, Housecall Pro, and similar field-service or practice-management platforms are not add-ons: they are the baseline environment WebStaffr is built to operate inside. Every plan works alongside these tools from day one, and being on one of them is a qualification signal, not an upgrade trigger.

---

## Unit Economics

Figures below reflect the Office Staff plan, the primary growth plan.

| Metric | Value |
|---|---|
| Monthly revenue | $497 |
| Delivery cost | $65 |
| Gross profit | $432 |
| Gross margin | 87% |
| Customer acquisition cost | $100–$200 |
| Monthly churn | 8% (planning base) |
| Customer lifetime | 12.5 months |
| Lifetime value | $5,400 |
| Lifetime value to acquisition cost ratio | ~36x |
| Payback period | Under 30 days |

[Inference] This CAC range reflects the free-website-lead-hook, founder-led, organic channel the business is running today, not paid acquisition. A ratio this high signals that acquisition is currently cheap because it is founder-led and referral-driven, not a steady-state benchmark: treat it as unproven past the first 50 free builds. Churn is planned conservatively at 8% monthly until three or more months of real retention data exist; 5 to 6% is a target to earn, not the base case, and should not be presented as the planning assumption.

---

## Financial Projections

[Inference : planning estimate, not measured] Model assumptions: 225 free 30-day Office Staff trials in month 1, 115 per month thereafter, 10% free-to-paid conversion, 8% monthly churn (planning base), $150 acquisition cost per paid customer (midpoint of the $100–$200 range above), $3,000 in monthly fixed costs, $25,000 starting cash.

**Year one, Phoenix HVAC:** cash positive by month three. Year end results: approximately 100 customers, approximately $593K in annual recurring revenue.

**Year two, Phoenix and Tampa:** Tampa launches month 13 on the same ramp shape as Phoenix. Year end (month 24) results: approximately 245 customers, approximately $1.46M in annual recurring revenue.

Conversion rate and trial volume are both unproven past the first 50 free 30-day Office Staff trials. A lower conversion rate or a smaller trial funnel than modeled here would scale these results down proportionally; a stronger funnel or higher conversion would scale them up. Paid acquisition spend is scaled only after the first 50 free 30-day Office Staff trials establish the real conversion rate.

---

## Investment Terms

| Term | Value |
|---|---|
| Instrument | Post money Simple Agreement for Future Equity, Y Combinator standard form |
| Raise structure | $10,000 minimum close, $25,000 target raise, $50,000 maximum capacity |
| Valuation cap | $150,000 |
| Discount rate | 20% on the next priced round |
| Implied ownership at target raise ($25,000) | 16.7% |
| Conversion trigger | Next priced equity round, acquisition, or initial public offering |
| Pro rata rights | Investor may maintain percentage ownership in the next round |

### Capital Tiers and Use of Funds

| Tier | Amount | Milestone Unlocked |
|---|---|---|
| Minimum Close | $10,000 | Delaware C-Corp execution, legal reserves, outbound go to market tooling, and immediate live telephone validation. Includes a 40% operational buffer. Use of funds: Legal and United States operations $1,580, Product development $3,049, Go to market and acquisition $2,040, Operational reserve $3,331. |
| Target Raise | $25,000 | Everything in Minimum Close, plus native ServiceTitan and Jobber webhook integration, automated client instance builds within 2 minutes, and full multi-agent office infrastructure deployed across both Workforce Plans. |
| Maximum Capacity | $50,000 | Everything in Target Raise, plus an accelerated Tampa plumbing launch, pulled forward to Month 6-8 (from the baseline Month 13) with more aggressive paid marketing spend, a second founder-led acquisition hire, and an extended operational runway past Month 10. |

### Return Scenarios

Value of a $25,000 investment (target raise) converting at the $150,000 cap, before dilution from a triggering round.

| Company valuation at trigger | Investor stake value | Multiple on investment |
|---|---|---|
| $300,000 | $50,000 | 2.0x |
| $500,000 | $83,500 | 3.3x |
| $1,000,000 | $167,000 | 6.7x |
| $2,000,000 | $334,000 | 13.4x |

These scenarios are illustrations, not projections or guarantees of performance. If the company dissolves before a trigger event, the investor is entitled to repayment ahead of the founder from remaining assets. If no trigger event occurs, the agreement remains outstanding indefinitely.

---

## Team

**K. Michael Tortorich, MD.** Founder. Sets vision, strategy, and go to market direction.

Patrick Bukowski and Wenjie Tong are team members available on demand, not co-founders or equity partners. Patrick supports operations and client success work as needed. Wenjie supports product architecture and engineering work as needed.

---

## Key Risks

| Risk | Mitigation |
|---|---|
| Free to paid conversion below 10% | All paid acquisition spend is gated on real conversion data from the first 50 free 30-day Office Staff trials |
| Regulatory exposure from calling or texting leads | Email first outreach, consent based contact, do not call list scrubbing, and 10DLC registration |
| Churn above 8% planning base | Structured onboarding touches at day one, day seven, and day 30, with early call activation tracked as a leading indicator |
| Competition from single feature tools | WebStaffr competes on the full handoff chain and operating playbook, not on any single feature |
| Voice service unproven on a live call | Voice is code complete and unit tested; a live phone test is the next milestone, tracked openly, not concealed |

---

## Reference

Complete build history: github.com/keithtortorich/WebStaffr3.0
Live production backend: web-staffr3-0-snowy.vercel.app
