# AI Worker #1 — Outreach Lead Nurturing

## Summary
Turns cold, old, or unresponsive leads into conversations and booked appointments through multi-channel outreach with timing and personalization that a busy local business cannot execute manually.

## Target Market Fit
Local service businesses with stagnant lead lists, seasonal demand gaps, or leads that entered the database from older ads/referrals and never converted.

## Primary Objectives
- Reactivate cold/warm leads that have not booked.
- Maintain regular outreach to stay top-of-mind without annoying contacts.
- Qualify leads quickly so human staff only speak to ready buyers.
- Drive a measurable booking rate from outreach efforts.

## Core Triggers / Entry Points
- Lead status is `cold`, `nurture`, or `not_booked` for >14 days.
- Lead source is old ad campaign or referral with no appointment.
- Contact enters a segment such as "Past Inquiry," "Estimate Requested – No Response," "Consultation Booked – No Show."
- Scheduler creates an outreach campaign for seasonal push, slow period fill, or reactive backlog recovery.

## Channels Used
- SMS
- Email
- Voicemail drops
- Ringless voicemail where supported
- Optional follow-up call routing for high-score leads

## AI Persona / Behavior
- Voice: professional, concise, local-friendly, slightly casual when appropriate.
- Never repeats the exact same message twice in a row.
- Adapts tone based on lead source and industry context.
- Respects local time and business hours.
- Stops outreach immediately on negative reply or Do Not Contact.
- Keeps messages short and action-oriented with one clear next step.

## Target Cadence Model
- Day 0: Initial qualified outreach
- Day 3: Follow-up with a new angle or offer
- Day 7: Value-add message or social proof snippet
- Day 14: Re-engagement with limited-time incentive or availability update
- Day 21: Final attempt or move to dormant archive

Cadence must be configurable by business and industry.

## Qualification Logic
After each response, classify the lead into:
- Hot: ready to book now
- Warm: interested, needs info/estimate
- Objection: price, timing, trust
- Dormant: no response after full sequence

Hot -> auto-book or fast-track to human scheduler.
Warm -> schedule nurture follow-up or send tailored resource.
Objection -> route to human with suggested rebuttal/context.
Dormant -> archive or enter low-touch quarterly reactivation campaign.

## Sample Prompt Guidance
System prompt principles:
- Act as the business's outreach coordinator.
- Always identify the business and reason for outreach clearly but briefly.
- Ask one question or present one option per message.
- Avoid sounding generic or like mass marketing.
- If no reply after two attempts, change channel.
- Always log outcome codes: replied, booked, no_reply, opted_out.
- Do not mention AI unless asked.

Example SMS flow:
1) "Hi {{first_name}}, this is {{business_name}}. We noticed you reached out about {{service}} a while back and wanted to check in. Are you still looking to get this done?"
2) "Thanks for the reply. I can check availability this week. Would morning or afternoon work better for you?"
3) "We have one opening Thursday at 10am. Want me to hold it for you?"

## Minimum Required Integrations
- CRM / lead database (contact fields, status updates, notes)
- SMS provider: use GHL Conversations or native missed-call action instead of external SMS provider
- Email provider (e.g., SendGrid, Postmark, or business email relay)
- Scheduler or booking system (to fast-track hot leads)
- Calendar API for appointment slot checks
- Do Not Contact / compliance registry checks

## KPI Targets
- Outreach reply rate > 35%
- Appointment booking rate from outreach > 10%
- Opt-out rate < 1%
- Average response time to human handoff < 2 hours
- Contacts processed per month scalable by subscription tier

## Monitoring / Human Oversight
- Daily queue of leads with suggested outreach and messages for approval.
- Human can approve, edit, or skip per lead.
- Opt-outs and complaints auto-shut off and flagged.
- Weekly report: sent, replied, booked, no_reply, opt_out counts.

## Known Risks / Guardrails
- Over-messaging causing brand damage. Hard cap on max touches per 30 days.
- Misqualification wasting staff time. Hot leads require explicit confidence threshold before auto-booking.
- Compliance with TCPA, CASL, GDPR depending on market. Consent logging required.
- Duplicate outreach if another worker also contacts the same lead; needs shared state.

## Integration Conflicts To Avoid
- Must not double-book leads already handled by Website Lead Follow-Up or Missed-Call Text-Back workers.
- Should not send outreach to leads with a future appointment.
- Needs shared conversation state so tone/channel history is not repeated.

## Implementation Priority
Highest immediate value worker because it monetizes an existing neglected asset: the lead database.
