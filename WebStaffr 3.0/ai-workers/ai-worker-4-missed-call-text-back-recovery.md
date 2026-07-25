# AI Worker #4 — Missed-Call Text-Back Recovery

## Summary
Instantly detects unanswered inbound calls and texts the caller back within a minute with a human-sounding, action-oriented message that recovers the lost connection before the prospect dials a competitor.

## Target Market Fit
Local service businesses whose phone rings while staff are on another call, driving, in a meeting, or simply unavailable. Every missed call is usually an active buyer with immediate intent. This worker monetizes calls that would otherwise become dead air.

## Primary Objectives
- Recover missed calls with an SMS reply within 60 seconds of the call ending.
- Preserve the caller's intent and urgency.
- Offer a callback or next step that does not require the caller to redial or re-explain.
- Qualify new callers quickly and route high-value calls to the right team member.
- Track recovery rate so owners can see exactly how much revenue was saved.

## Core Triggers / Entry Points
- Inbound call ends without being answered.
- Caller ID is not blocked or suppressed.
- Call duration is near zero or short enough to indicate no live conversation occurred.
- Caller is not already in an active recovery sequence for the same missed call.
- Business receives a call outside a manual coverage window.

## Channels Used
- SMS
- Optional MMS with photo, link, or attachment if service avatar/branding supports it

## AI Persona / Behavior
- Voice: professional, brief, apologetic for missing the call, and locally branded.
- Sounds like a real team member rather than an automated campaign.
- Uses caller name when available from caller ID or CRM lookup.
- Offers one clear next step: callback now, schedule a time, or reply with details.
- Avoids long narrative messages.
- Adapts message if caller is already a known customer, leads in CRM, or a first-time prospect.

## Decisions / Actions
First-time prospect missed call:
- Acknowledge the missed call.
- Apologize briefly.
- Offer to call back now or schedule a time.
- Include a one-tap scheduling link if available.

Known customer missed call:
- Acknowledge missed call by name.
- Mention account or prior service context when relevant.
- Offer to redirect to the right person or team.
- Provide a callback or direct contact method.

High-frequency or suspicious missed calls:
- Flag for human review if calls are repeated, spoofed, or originate from known spam patterns.
- Suppress auto-reply after a threshold to avoid harassment or compliance risk.

Do Not Contact or opt-out:
- Immediately stop and suppress further recovery SMS if caller replies STOP, UNSUBSCRIBE, or equivalent.

## Sample First-Touch Messages
Prospect:
"Hi {{first_name_or_last_name}}, this is {{business_name}}. I'm sorry we missed your call. If you're still free, reply BACK and I'll connect you with someone now. If now is bad, you can book time here: {{link}}"

Known customer:
"Hey {{first_name}}, it's {{business_name}}. We missed your call. Can you reply with the best number to reach you, or would you like us to call you back at {{phone_on_file}}?"

Outside business hours:
"Hi, this is {{business_name}}. We missed your call and are closed right now. Reply with your question or book time online: {{link}} and we'll get back to you first thing tomorrow."

## Minimum Required Integrations
- Phone system or telephony platform that exposes missed-call events: use GHL native call tracking, or any provider that can POST to WebStaffr’s missed-call endpoint.
- SMS provider: use GHL Conversations API so GHL retains ownership of the message thread.
- Caller ID lookup or CRM association to identify known contacts.
- Scheduler or booking system with shareable links.
- CRM to log missed-call events and recovery outcomes.
- Do Not Contact list and SMS compliance checks.

## KPI Targets
- Missed-call recovery rate: percentage of missed calls converted into a conversation or booking > 25%
- Time from missed call to first recovery SMS < 60 seconds
- Opt-out or complaint rate < 1%
- Caller reply rate to recovery SMS > 20%
- Revenue saved or attributed to recovered calls per month
- Duplicate prevention: same missed call generates only one recovery attempt

## Monitoring / Human Oversight
- Real-time or near-real-time log of missed calls and recovery SMS status.
- Dashboard of recovery rate by time of day, day of week, and caller type.
- Weekly report: missed calls, texts sent, replies received, bookings created, opt-outs.
- Manual override to pause recovery for specific numbers, time windows, or campaigns.
- Alert spike if missed-call volume suddenly jumps and recovery rate drops.

## Known Risks / Guardrails
- Over-texting callers who redial or are already speaking to a human.
- Sending automated texts to numbers on Do Not Contact lists.
- Creating a negative first impression if message is canned, slow, or broken.
- Generating duplicate outreach when Website Lead Follow-Up or Outreach Worker is already handling the same lead.
- Legal and compliance exposure under TCPA and similar regulations.

## Integration Conflicts To Avoid
- Must not send recovery SMS if a human has already called back or if a call comes in again from the same number within a short window.
- Must not trigger if Website Lead Follow-Up already sent an SMS from the same form-triggered event.
- Should not send recovery messages to leads already in an outreach sequence unless clearly separated by service type and intent.
- Needs a shared event lock so the same missed call cannot spawn multiple workers.

## Implementation Priority
Third in priority. Missed-call recovery captures highest-intent demand but has a lower total volume than website leads or outreach. Strongly recommended for mobile-heavy local businesses such as contractors, towing, and home services.
