# WebStaffr — AI Department Build Plan

## Overall Principles
- WebStaffr owns:
  - AI orchestration
  - webhook receivers
  - prompt management
  - routing logic
  - reporting/observability hooks
- GHL owns:
  - contacts
  - conversations
  - appointments
  - compliance state
  - core messaging delivery

Do not reimplement anything GHL already does.

## Phase 1: Platform Foundation

### 1.1 Webhook Receiver and Event Router
Endpoint shape:
```
POST /api/ghl/webhook
Headers: x-ghl-signature
Body: GHL standard webhook payload
```
Normalize into internal event:
```json
{
  "event_id": "evt_123",
  "type": "contact.created | conversation.message.received | ...",
  "timestamp": "2026-06-11T...",
  "contact": { "id": "...", "phone": "...", "email": "...", "dnd": false },
  "payload": { /* raw GHL event */ }
}
```

Router rules:
- Deduplicate by `event_id` using Redis or in-memory store with TTL.
- Resolve contact identity: prefer phone, fall back email.
- Check DND/suppression before passing to any worker.
- Write event to job queue (BullMQ or equivalent) for async processing.

### 1.2 Shared AI Client / Prompt Loader
- Load prompts from `/prompts/{worker}.md` or equivalent.
- Wrap LLM calls with:
  - retry policy (exponential backoff)
  - timeout (configurable per worker)
  - token budget guard
  - content policy pre-check
- Maintain worker-specific system prompts with injected GHL context.

### 1.3 GHL API Client
Abstractions needed:
- `contacts.getById(id)`
- `contacts.update(id, fields)`
- `conversations.sendSMS(contactId, message)`
- `conversations.sendEmail(contactId, subject, body)`
- `appointments.search(contactId)` 
- `notes.create(contactId, body)`

All writes must include `worker_id` and `source_event_id` in notes for traceability.

## Phase 2: Website Lead Follow-Up + Missed-Call Text-Back

### 2.1 Website Lead Follow-Up Worker
Trigger: `contact.created` with `source=website` or tag `website_new`.

Prompt scaffolding:
Use `/prompts/website-follow-up/system.md`:
```
You are the website lead coordinator for {{business_name}}.
Lead context:
- Name: {{contact.first_name}}
- Service requested: {{contact.custom_fields.service_requested}}
- Page source: {{contact.source}}
- CRM history: {{crm_summary}}

Rules:
- Reply within 5 minutes during business hours.
- Use SMS first, then email.
- Ask one clear next step.
- If lead asks for human, stop and tag `needs_human`.
- Log outcome as note after each reply.
```

Action flow:
1. Score lead. If hot -> send calendar link.
2. Send SMS via GHL conversation API.
3. Update contact tag: `website_contacted`, `website_hot|warm|cold`.
4. Set follow-up timer via GHL workflow or internal cron.

API contract (internal):
```json
{
  "worker": "website_follow_up",
  "inputs": { "contact_id": "...", "event": "..." },
  "outputs": { "status": "sent|scheduled|needs_human", "next_action_at": "..." }
}
```

### 2.2 Missed-Call Text-Back Worker
Trigger: GHL native `Call Status Changed` event filtered to `no-answer`.

Prompt scaffolding:
```
You are the receptionist for {{business_name}}.
Context:
- Caller name: {{contact.first_name || "there"}}
- Known customer: {{is_existing_customer}}
- Best callback time: {{if available}}

Rules:
- Acknowledge missed call.
- Offer callback or booking link.
- Keep message under 160 chars if possible.
- Do not send if same contact was already texted within 5 minutes by another worker.
```

Action flow:
1. Wait for GHL native missed-call event.
2. Resolve contact by phone using GHL contact lookup.
3. Check last missed-call text timestamp in custom field `last_missed_call_text_at`.
4. Generate and send SMS via GHL Conversations API.
5. Write `last_missed_call_text_at` and add tag `missed_call_recovered`.
6. If reply received within 15 min, fast-track to human.

## Phase 3: Outreach Lead Nurturing

### 3.1 Batch Scheduler
Nightly or every 4 hours:
- Query GHL contacts with `outreach_eligible=true`.
- Exclude contacts with active appointment, active website flow, or `dnd=true`.
- Sort by `last_outreach_at` ascending.
- Process up to batch size per run.

### 3.2 Outreach Worker Prompt
```
You are the outreach coordinator for {{business_name}}.
Lead:
- Name: {{contact.first_name}}
- Segment: {{contact.segment}}
- Last contact: {{contact.last_contact_summary}}
- Days since inquiry: {{days_since}}

Rules:
- One message, one ask.
- Do not repeat topics from the last 2 messages.
- Vary channel: alternate SMS/email if possible.
- If reply, route to correct disposition.
```

Dispositions:
- hot: tag `outreach_hot`, send calendar, alert human
- warm: tag `outreach_warm`, queue next step in +3 days
- objection: tag `outreach_objection`, write note with suggested rebuttal
- no_reply: increment `outreach_count`, schedule next step
- opted_out: tag `dnd`, stop

### 3.3 State Machine
```
nurture_start → day3 → day7 → day14 → day21 → dormant
  ↑               ↑      |       |       |
  └─── reply ←────────┘      |       |
        └── booked ──────────┘       |
              └── opted_out ─────────┘
```

All transitions update:
- `last_outreach_at`
- `outreach_stage`
- `outreach_worker_id`
- append to `outreach_history` custom field or note

## Phase 4: Reputation Management

### 4.1 Review Poller
Schedule: every 30 minutes.
- Call GBP API for reviews modified since last poll.
- For new reviews:
  - Write note into GHL contact record if reviewer is identifiable.
  - Create review case: custom object or tagged note.
  - Queue AI response draft.

### 4.2 Review Response Prompt
```
You are the reputation manager for {{business_name}}.
Review:
- Rating: {{review.rating}}
- Text: {{review.text}}
- Reviewer: {{review.reviewer_name || "Guest"}}
- Business context: {{business.memory}}

Rules:
- Positive: thank personally, invite return.
- Negative: apologize, offer resolution offline, do not argue.
- Never promise refund/discount without approval.
- Tone must match brand.
```

Human approval flow:
- Draft response saved as note with status `draft`.
- GHL workflow notifies staff via SMS/email.
- Staff publishes via API or GHL UI.

### 4.3 Post-Job Review Request
Trigger: `appointment.completed`.
- Send SMS/email 1–2 days later unless `dnd=true`.
- If positive reply, request testimonial permission.
- Log testimonial to `testimonials` custom field or linked document.

### 4.4 GBP Maintenance
Weekly cron:
- Create post: `posts.create` via GBP API.
- Answer Q&A: fetch unanswered Q&A, generate responses, queue for approval.

## Phase 5: Paid Ad Nurturing

### 5.1 Ad Ingestion
Two patterns:
1. Webhook from Google Ads/Meta lead form to WebStaffr.
2. Periodic API poll of conversion events and lead form submissions.

Normalize into:
```json
{
  "ad_event_id": "g-12345",
  "campaign": "summer_AC_google",
  "adset": "...",
  "keyword": "...",
  "lead_value_estimate": 250,
  "contact_id": "..."
}
```

### 5.2 Ad Lead Prompt and Routing
```
You are the ad operations specialist for {{business_name}}.
Lead:
- Name: {{contact.first_name}}
- Campaign: {{ad_event.campaign}}
- Service: {{contact.service_requested}}
- CRM history: {{summary}}

Rules:
- Reference campaign/offer in first message.
- Hot leads get calendar link within minutes.
- Cold leads enter paid_ad_nurture sequence.
- Update ad lead quality score after interaction.
```

Quality scoring fields:
- `ad_lead_score` (1–10)
- `ad_mql` boolean
- `ad_booking_value` after appointment

### 5.3 Campaign Reporting
Weekly job:
- Query leads and outcomes grouped by `campaign`.
- Calculate: CPA, cost per booking, conversion rate, reply rate.
- Write report into owner-facing GHL conversation as formatted message.
- Flag campaigns where CPA > threshold and recommend `pause | reduce_budget | test_new_creative`.

Do not auto-execute budget changes unless explicitly enabled by contract.

## Deployment and Hosting
- Host WebStaffr as a containerized service.
- Environment variables for GHL API keys, ad API credentials.
- Secrets in WebStaffr secret store; never in repo.
- Webhook endpoints must use HTTPS with valid TLS.
- Webhook verification using GHL signature headers.

## Observability
- Structured logging per worker action.
- Daily email/SMS digest to agency owner:
  - unreadly contacted
  - reply rates per worker
  - error rate and failed sends
  - hot leads requiring human attention
- Alerting thresholds:
  - GHL API error rate > 2%
  - webhook duplicate rate spike
  - worker processing latency > 30s

## Zapier Dependency Audit & Native Replacements

The original plan contained several implicit Zapier bridges between ad platforms, form providers, telephony, and GHL. This section removes those assumptions by replacing each bridge with a native GHL integration, a direct webhook to WebStaffr/GHL, or a GHL form integration.

### A. Ad Lead Form → GHL Contact + Custom Fields
**Assumed Zapier bridge:** Receive Meta Lead Ads / Google Ads lead form webhook, parse the payload, find or create the GHL contact, and populate campaign-level custom fields (`campaign`, `adset`, `keyword`, `lead_value_estimate`, `utm_source`).

**Native replacement — Two options (use A1 or A2):**

**A1. Direct webhook to WebStaffr (recommended for full control)**
1. Configure Meta Lead Ads / Google Ads to send form submissions to `POST https://web-staffr3-0-snowy.vercel.app/api/ads/ingest`.
2. WebStaffr verifies the webhook signature, normalizes the payload into internal ad_event format, and resolves the contact by email or phone.
3. WebStaffr calls GHL Contacts API:
   - `contacts.getById` or `contacts.search` to find existing contact.
   - If new: `contacts.create` with standard fields + custom fields mapped from the ad payload.
   - If existing: `contacts.update` with `custom_fields` backfill.
4. WebStaffr tags the contact with `ad_new`, `ad_meta` or `ad_google`, and the campaign name.
5. WebStaffr enqueues the contact for the Ad Lead Nurturing worker (Phase 3 / Section 5.2).

**A2. GHL Native Form + Hidden UTM Fields (lowest code)**
1. Create a GHL Form for each active campaign or use a single “Universal Ad Lead” form.
2. Add hidden fields for `utm_source`, `utm_campaign`, `utm_adset`, `utm_term` and visible fields for name/email/phone/service.
3. Use Meta Lead Ads’ “Instant Form” bridge to push raw lead data into a simple endpoint, OR use a lightweight redirect page that auto-submits to the GHL Form via POST, preserving hidden UTM values from the landing page.
4. GHL natively creates the contact, applies the form tags, and fires `contact.created` with `source=form`.
5. WebStaffr receives `contact.created`, reads the populated custom fields from the contact record, and proceeds directly to Section 5.2 routing.

**Fallback (only if direct HTTPS webhook is blocked):** Self-hosted n8n receives the ad platform webhook, normalizes the payload, and calls GHL API. Do not make this the primary path.

### B. Custom Website Form → GHL Contact Creation / Tagging
**Assumed Zapier bridge:** A non-GHL website form submits to Zapier, which creates the GHL contact and applies `website_new` / `website_contacted` tags.

**Native replacement:**
1. Replace the custom site form with a **GHL Native Form** embedded via iframe or script.
2. Configure the GHL Form to:
   - Auto-assign the tag `website_new` on submission.
   - Map the “Service Requested” dropdown to a GHL custom field.
   - Set the contact `source` to `website`.
3. On `contact.created` with `source=website` or tag `website_new`, the Website Lead Follow-Up Worker (Section 2.1) auto-triggers.
4. If the website form must remain custom-styled and outside GHL:
   - Point the form `POST` directly to `POST https://web-staffr3-0-snowy.vercel.app/api/website/lead`.
   - WebStaffr validates the payload and calls `contacts.create` or `contacts.update` via GHL API with the required tags and custom fields.
   - No Zapier involved.

### C. Missed-Call SMS Trigger (GHL Native)
**Assumed Zapier bridge:** An external webhook from a carrier/automation tool checks GHL and fires an outbound SMS.

**Native replacement:**
1. **Preferred — GHL Native Calling Workflow:**
   - Use GHL’s native Conversations / Call tracking.
   - In GHL Workflows, use the native **“Call Status Changed”** trigger filtered to `no-answer`.
   - Action: **Send SMS** directly inside GHL Workflows.
   - Add a condition to check custom field `last_missed_call_text_at`.
   - If missing/cold, send the SMS and update `last_missed_call_text_at` via the workflow action.

2. **If using a third-party call tracking provider:**
   - Configure the provider to POST the call-status webhook to `POST https://web-staffr3-0-snowy.vercel.app/api/calls/missed`.
   - WebStaffr:
     - Verifies the signature.
     - Resolves the contact by `From` phone number via GHL `contacts.search`.
     - Checks DND and `last_missed_call_text_at`.
     - Calls `conversations.sendSMS(contactId, message)` via GHL API so GHL retains conversation ownership.
     - Writes back `last_missed_call_text_at` and tags `missed_call_recovered` using `contacts.update`.
   - Do not send SMS directly from WebStaffr or an external provider; always route delivery through GHL conversations to satisfy the non-negotiable rule that GHL owns conversation state.

### D. UTM / Campaign Attribution Stitching
**Assumed Zapier bridge:** Zapier enriches GHL contacts with `utm_source`, `utm_medium`, `utm_campaign`, and inbound route after the fact.

**Native replacement:**
1. **Forms and landing pages:** Add hidden fields to GHL Forms or custom forms that POST to WebStaffr.
2. Store UTM parameters in GHL custom fields at creation time.
3. For organic website visits tracked before a form submission, capture UTM in a first-party cookie and inject them into the form POST payload.
4. WebStaffr or GHL Workflows read these fields to drive the `campaign` and `source` tagging in Phase 3 and Phase 5.

### E. Reviewer Identity Resolution (GBP → GHL)
**Assumed Zapier bridge:** Zapier matches GBP reviewer name/email to GHL contacts to attach the review note.

**Native replacement:**
1. The GBP Review Poller (Section 4.1) runs inside WebStaffr on a cron.
2. For each new review, WebStaffr queries GHL `contacts.search` by the reviewer’s email or phone if available.
3. If a match is found, WebStaffr uses `notes.create(contactId, body)` to attach the review context to the contact record.
4. If no match, create a review case note in GHL and alert staff via GHL Workflow notification.
5. No external automation tool required.

### Recommended Primary Architecture Summary
- **Forms:** GHL Native Forms + direct POST to WebStaffr for custom forms.
- **Ad Platforms:** Direct webhook → WebStaffr → GHL API backfill.
- **Telephony:** GHL native missed-call workflows, or third-party call provider → WebStaffr → GHL Conversations API.
- **Attribution:** Hidden form fields and first-party parameter capture at form submission time.
- **Data routing:** WebStaffr `/api/ghl/webhook` and `/api/ads/ingest` normalize every external event before writing to GHL.
- **Fallback only if needed:** Self-hosted n8n can normalize ad/web/telephony webhooks to GHL API calls if a corporate firewall blocks direct webhooks to WebStaffr.

### Implementation Checklist
- [ ] Replace every Zapier “Zap” reference with a WebStaffr endpoint or GHL Workflow.
- [ ] Audit all form submissions to ensure they POST to GHL or WebStaffr directly.
- [ ] Verify GHL custom fields exist for: `service_requested`, `last_missed_call_text_at`, `ad_lead_score`, `ad_mql`, `outreach_stage`, `utm_source`, `utm_campaign`, `utm_adset`, `utm_term`.
- [ ] Confirm webhook signatures for Meta, Google, third-party call provider, and GHL are validated in WebStaffr.
- [ ] Document the WebStaffr endpoint URLs and expected payload shapes for the ad platform and call-provider configurations.
