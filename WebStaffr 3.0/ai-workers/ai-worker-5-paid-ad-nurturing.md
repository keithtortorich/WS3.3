# AI Worker #5 — Paid Ad Nurturing (ROAS / Cost-Per-Lead Optimization)

## Summary
Connects paid advertising spend to revenue outcomes by grading ad leads in real time, routing high-intent ad traffic immediately, and running tailored nurture flows so ad spend does not become wasted lead inventory.

## Target Market Fit
Businesses running Google Ads, Meta Ads, or other paid channels that get clicks and form submissions but cannot tell which campaigns, ad sets, or keywords are producing booked revenue versus junk leads. Especially important when ad spend represents a large share of customer acquisition cost and needs CFO-level accountability.

## Primary Objectives
- Increase return on ad spend by connecting ads, leads, and CRM outcomes.
- Reduce cost per booked appointment from paid channels.
- Surface underperforming campaigns before they burn budget.
- Turn cold ad leads into recurring revenue through nurture.
- Give owners clear, explainable metrics on advertising efficiency.

## Core Triggers / Entry Points
- New lead or conversion event tagged with ad source, campaign, ad set, keyword, or placement.
- Weekly or monthly performance review period for ad accounts.
- ROAS or cost-per-lead threshold breached for a campaign or time window.
- Ad account reports show low lead quality or low conversion value.
- Business requests campaign audit or bid adjustment recommendation.

## Channels Used
- SMS
- Email
- Native ad follow-up where supported: Google lead form extensions, Meta lead forms
- CRM status updates and custom fields
- Dashboard or reporting outputs for human review

## AI Persona / Behavior
- Voice: analytical, direct, ROI-focused, but still conversational for lead interactions.
- Separates two modes: lead-nurturing messages to ad leads, and recommendation messages to business owners.
- Uses campaign or ad creative context when messaging ad leads so language feels aligned with what they just clicked.
- Stops outreach immediately on negative reply, opt-out, or booked status.
- Flags suspicious lead patterns such as disposable emails, fake names, or repeated form spam.

## Real-Time Lead Routing and Grading
On every ad conversion event, automatically:
- Score the lead using CRM lookups: prior contact status, location fit, service requested.
- Compare lead quality to recent campaign benchmarks and historical KPIs.
- Route hot leads to human assignment or self-booking within minutes.
- Send the lead a short, ad-contextual SMS or email follow-up so the channel is consistent with the lead's original intent.
- Pause low-performing campaigns when accuracy and volume thresholds support it; present the recommendation to a human if risky to change live spend.

## Nurture Logic for Cold Ad Leads
For ad leads that do not book immediately:
- Segment ad origin by campaign, source, or offer type.
- Deliver nurture series that references the specific ad context or offer.
- Replace irrelevant creative with reply-driven follow-up until the lead converts or opts out.
- Move leads into standard Outreach Worker if nurture cadence does not convert after defined steps.

## Business Recommendation Logic
Weekly or monthly analysis:
- Identify campaigns whose cost per booked appointment exceeds target.
- Detect landing page or form problems masquerading as ad problems.
- Recommend budget reallocations instead of manual bid changes when possible.
- Present ROAS, CPA, conversion rate, and lead quality trends in simple business language.
- Ask for human decision on spend increases only when confidence is high.

## Decisions / Actions
High-intent ad lead:
- Fast-track to human assignment or calendar booking.
- Send SMS confirming the team has received their request and will follow up shortly.
- Log real-time so revenue can be attributed back to ad source.

Low-intent or low-quality ad lead:
- Enter paid-ad nurture sequence.
- Do not spend high-touch resources until lead shows later-stage intent.

Underperforming campaign:
- Pause or reduce budget with human confirmation when required by policy.
- Document reason with data: high CPA, low lead quality, weak conversion rate.
- Suggest creative or landing page variants when data supports it.

Compliance and fraud:
- Flag repeated test submissions, duplicate emails, or bot-like behavior.
- Recommend IP or device exclusions if supported.
- Stop outreach or reporting actions that conflict with platform policies.

## Sample Prompt Guidance
System prompt principles:
- Treat advertising as an investment requiring measurable outcomes.
- Use ad metadata to personalize follow-up to the lead.
- Default to actions that improve profitability, not vanity metrics.
- Attribute revenue back to campaigns in a way owners understand.
- Use clear explanations when recommending budget changes.

Example ad lead SMS:
"Hi {{first_name}}, thanks for checking out {{offer_or_campaign}}. We got your request for {{service}}. I can check availability now — would {{time_window}} work for a quick call?"

Example owner-facing weekly summary:
"{{business_name}} ad review: 4 campaigns, 12 leads, 3 booked. Google Search performed at $48 CPA and $210 per booked appointment. Meta lead forms dropped to 1.1% conversion rate; recommend pausing for the next 7 days or testing a new creative."

## Minimum Required Integrations
- Google Ads API or Meta Marketing API for campaign, ad set, and lead data.
- Conversion import: offline conversions, CRM bookings mapped back to click or lead source.
- Website form or landing page webhook.
- CRM with ad source fields, lead status, revenue or appointment value.
- SMS provider and email provider for ad-lead follow-up.
- Calendar or scheduling system for hot lead booking.
- Reporting or dashboarding tool for owner-facing insights.

## KPI Targets
- Cost per booked appointment from paid channels reduced over time
- ROAS or cost-per-revenue-dollar at or above target for active campaigns
- Ad lead reply rate > 30%
- Ad lead booking rate > 10%
- Weekly recommendation accuracy: changes made from suggestions improve metrics
- Attribution accuracy: revenue mapped to correct campaign or keyword
- Lead quality score stability or improvement month over month

## Monitoring / Human Oversight
- Daily ad lead queue sorted by campaign, status, and conversion likelihood.
- Weekly or biweekly campaign review presented in plain language.
- Owner can approve, reject, or modify automation actions such as pausing campaigns or budget reallocations.
- Alert when CPA spikes, lead volume drops, or campaign changes cause performance shifts.
- Full log of source, action, result, and explanation retained for audits.

## Known Risks / Guardrails
- Automating spend changes without human sign-off can cause budget surprises.
- Misattribution from delayed CRM values or offline conversions.
- Over-optimizing for clicks or low-cost leads instead of bookings.
- Violating ad platform policies via prohibited automated account actions.
- Poor ad leads contaminating the CRM and confusing other workers.

## Integration Conflicts To Avoid
- Must not change ad spend if Outreach Worker is also changing the same campaign unless central state confirms no conflict.
- Must not import duplicate leads from different ad sources without identity resolution.
- Should not pause campaigns while a seasonal uplift or manual override is active.
- Must preserve original ad creatives and metadata for other workers to use in contextual messaging.

## Implementation Priority
Lowest initial priority but highest long-term leverage once leads are flowing. Becomes essential once the business scales paid acquisition and CFO-style accountability around ad spend matters.
