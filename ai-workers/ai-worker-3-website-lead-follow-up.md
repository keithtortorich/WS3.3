# AI Worker #3 — Website Lead Follow-Up (Under 5 Minutes)

## Summary
Captures inbound website inquiries and responds within five minutes with a conversational, conversion-first follow-up across SMS and email. This worker turns raw website form fills into booked or qualified conversations while the lead is still warm and actively shopping.

## Target Market Fit
Businesses that already receive leads from their website but cannot reply fast enough because of staffing, after-hours gaps, or slow internal routing. Especially high-impact for contractors, dentists, salons, real estate, and auto shops where speed-to-first-contact directly predicts whether a lead books or goes elsewhere.

## Primary Objectives
- Contact every new website lead within five minutes during business hours.
- Initial outreach uses two channels in parallel: SMS and email.
- Qualify the lead in real time and route ready buyers into booking.
- Convert partial form data when available to enrich the conversation.
- Give staff a clean, prioritized queue instead of random system notifications.

## Core Triggers / Entry Points
- New lead from any website form: contact form, estimate request, appointment request, callback request, or chat widget handoff.
- Lead is tagged `website_new` and has no outbound touch within 300 seconds.
- Lead arrives while a human is unavailable, on another call, or outside working hours.
- Lead source is `website`, `site_chat`, `landing_page`, or similar digital origin field.

## Channels Used
- SMS
- Email
- Optional webchat/WhatsApp continuation when available

## AI Persona / Behavior
- Voice: helpful, fast, low-friction, and human enough that the lead does not realize they are talking to automation initially.
- Uses the lead's first name and the service or page they inquired about.
- Asks one clear next step per message.
- Avoids long forms or multiple qualifying questions in the first message.
- Detects out-of-office hours and switches to appointment-first framing for the next available time.
- Instantly stops and hands to human if the lead asks for a person, pricing details that require human review, or expresses frustration.

## Response Windows and Rules
- Business hours: first touch in under 5 minutes.
- Evening/weekend: send an instant acknowledgment saying real human follow-up happens next business morning, while still offering one simple next step.
- If no response after 30 minutes, send a second lightweight check-in.
- If no response after 60 minutes, move lead to Outreach Worker #1 sequence and flag for human assignment.

## Data Used and Enrichment
- Form fields: name, email, phone, service needed, preferred date/time, message.
- Page path or source campaign when available.
- CRM fields: existing customer status, past estimates, prior conversations.
- Calendar: live view of nearest available appointment slots.

## Routing Logic
After first response, classify the lead quickly into:
- Hot: mentions urgency, asks for pricing, or provides high-intent context. Send calendar link or fast-track to scheduler.
- Warm: interested but exploratory. Ask one qualifying question and offer a resource or short call.
- Duel-channel: strong fit for follow-up call. Send SMS saying a team member will call shortly.
- Out-of-scope or bot: mark as `needs_review` and alert human if traffic pattern looks suspicious.
- Existing customer: avoid generic "new customer" language and route appropriately.

## Sample First-Touch Messages
High-intent appointment request:
"Hi {{first_name}}, this is {{business_name}}. I see you're looking to get {{service}} scheduled. We still have one opening tomorrow at {{time}}. Want me to hold it?"

General inquiry:
"Hi {{first_name}}, thanks for reaching out to {{business_name}} about {{service}}. Do you have a few minutes today or tomorrow for a quick call?"

Evening or weekend:
"Hi {{first_name}}, thanks for contacting {{business_name}}. We're closed right now, but we'd love to help with {{service}}. Reply YES and we'll reach out first thing tomorrow with the next available time."

## Minimum Required Integrations
- Website form provider or direct form endpoint: WordPress, Webflow, Wix, HubSpot, Jotform, Typeform.
- SMS provider capable of sub-minute delivery.
- Scheduler or booking engine with real-time availability.
- CRM to update lead status, source, and conversation log.
- Calendar API for appointment slot checks.
- Optional live chat and webhook listeners for chat-widget handoff.

## KPI Targets
- First response time under 5 minutes during business hours
- Lead reply rate from first touch > 30%
- Booking rate from first touch > 8%
- Duplicate contact prevention with other workers
- Human assignment time for hot leads < 15 minutes after lead creation
- Unread SMS or email leads processed without dropping below service level

## Monitoring / Human Oversight
- Live queue view showing newest leads, response status, current worker owner, and lead intent.
- Slack or dashboard alert when leads exceed threshold without outbound contact.
- Daily summary: leads received, first-touch timing, replies, bookings, duplicates, errors.
- Ability to pause automation for a time window or specific campaign.

## Known Risks / Guardrails
- Sending messages to spam folders or triggering SMS compliance flags.
- Double contact when Outreach Worker #1 also owns the lead.
- Accidental booking or promise without checking human availability.
- Mishandling leads marked as customers vs prospects.
- Compliance with TCPA, CASL, GDPR for automated outreach.

## Integration Conflicts To Avoid
- Must not respond again if Missed-Call Text-Back or Outreach Worker already engaged the same lead.
- Must not auto-book during unstaffed maintenance windows unless explicitly enabled.
- Should not override human status if a staff member has already reached out manually.

## Implementation Priority
Highest operational priority because speed-to-lead is one of the strongest drivers of booking rate and directly affects the quality of leads that every other worker processes.
