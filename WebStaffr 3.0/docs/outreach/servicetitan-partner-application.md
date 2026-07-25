# ServiceTitan Partnership Application — WebStaffr

## Program choice
- Primary: ServiceTitan App Marketplace / Technology Partner
- Secondary interest: Channel Partnerships

Keep this local in-repo only. Do not paste secrets, API keys, or tenant-specific credentials here.

---

## Company overview

WebStaffr is an operational revenue-recovery platform for home-service contractors, HVAC first. Contractors lose jobs they already paid to generate because they cannot answer every call. WebStaffr deploys always-on office staff: a Receptionist first, with a Lead Coordinator, Reputation Manager, and Website Operations Manager layered in over time, so no customer is lost to a missed call.

Core thesis: "The website is customer acquisition. The recurring staff is the business."
Positioning: Contractors hire staff, not software. "You stay on the tools. We run the office."
Core message: We don't sell technology. We recover revenue.

Beachhead: HVAC contractors, Phoenix AZ, 3 to 15 employees, $500K to $3M revenue.

Two confirmed pricing plans:
- Office Staff: $497/mo after a 30-day free trial with generated site
- Business Manager: $2,497/mo upgrade tier, plus the contractor's own ad spend (adds a Sales Consultant, a Marketing Coordinator managing paid ads across Meta and other platforms, and a Growth Manager; ad spend paid directly to each platform, never marked up)

Live and verified:
- Backend deployed and healthy
- Intake-to-tenant-site pipeline works end to end in production
- AI Receptionist answers real customer questions
- Automated tests passing
- Source code public on GitHub

---

## Integration overview

WebStaffr already has a ServiceTitan integration code package built and tested under `webstaffr/integrations/servicetitan/`. The current implementation is a read-first Python integration layer that can pull jobs, appointments, customers, invoices, payments, locations, technicians, and installed equipment through the ServiceTitan V2 API using OAuth2.

In the partner/marketplace context, the intended integration behavior is:
- Read ServiceTitan operational data to understand contractor activity
- Use that data to drive AI office-staff actions inside WebStaffr
- Keep ServiceTitan as the operational system of record
- Avoid replacing or disrupting ServiceTitan workflows
- Operate alongside ServiceTitan, not as an alternative

What market partners would see from the listing:
- An AI office-staff layer that works inside a contractor's existing ServiceTitan environment
- Lead and call-recovery behavior without changing how the office already runs
- A generated customer website plus AI Receptionist that can answer and qualify leads on the contractor's behalf
- A model where ServiceTitan is a qualification signal and operational backbone, not something to be replaced

---

## Customer value proposition

Contractors on ServiceTitan are already systematized operators. They have accepted SaaS costs, use structured workflows, and care about metrics like close rate, response time, and review growth.

WebStaffr adds value by:
- recovering missed revenue from unanswered calls and slow follow-up
- adding an AI Receptionist without adding a human hire
- cleaning up lead handoff after the job
- keeping the generated site and booking flow updated without extra staff time
- working with ServiceTitan as the operational backbone rather than against it

This matches the ServiceTitan Marketplace framing of partners that "empower our customers' success."

---

## Integration status

Current state: code-complete and test-covered, not yet live-activated against a real ServiceTitan tenant. The repo already contains:
- ServiceTitan OAuth2 client
- Mock client for testing
- Read-first sync runner
- Router endpoint harness

Next required steps for marketplace certification:
1. Real ServiceTitan developer/tenant credentials
2. Sandbox certification run against ServiceTitan's test environment
3. Production activation behind env-based enablement
4. Verified end-to-end run with real job/appointment/customer data

None of these require new architecture; they are configuration and certification steps.

---

## Why partner with ServiceTitan

- ServiceTitan users are WebStaffr's ideal Layer 1 leads: already paying for field-service software, already systematized, already SaaS-comfortable.
- WebStaffr is not building a competing dispatch or accounting tool; it is building the office layer around the existing operational stack.
- The fastest path to mutual growth is marketplace discoverability: ServiceTitan customers can find WebStaffr inside the platform they already use, and WebStaffr can demonstrate measurable revenue recovery without forcing migration or disruption.

---

## Ask from ServiceTitan

- Technology/marketplace partnership listing in the App Marketplace
- Access to developer support for certification
- Access to marketing and enablement resources for joint go-to-market
- Opportunity to sponsor or participate in Pantheon/community events when relevant
