# GoHighLevel Setup Guide — AI Department

## Goal
Configure GHL once as the operating system for the AI department. Everything stateful (contacts, conversations, appointments, compliance, routing) lives in GHL. AI logic runs on top of that via webhooks and custom fields.

## Setup Order
1. Custom fields and tags
2. Pipelines and opportunity stages
3. Workflows for each worker
4. Webhook configurations
5. Permission and SaaS setup if reselling to clients

## Custom Fields
Create these at the sub-account or SaaS level.

Contact level:
- ai_worker_last_touch (datetime)
- ai_worker_last_channel (single line text)
- ai_outreach_count (number)
- ai_outreach_stage (single line text)
- ai_outreach_history (single line text or long text)
- last_missed_call_text_at (datetime)
- missed_call_recovered (yes/no)
- website_worker_id (single line text)
- website_handled_at (datetime)
- ad_source (single line text)
- campaign_id (single line text)
- ad_lead_score (number)
- ad_mql (yes/no)
- review_request_sent (yes/no)
- testimonial_captured (yes/no)
- opt_out_reason (single line text)

Optional company level:
- ai_monthly_volume (number)
- ai_workers_active (multi-select)

## Tags
Organize outcomes and worker ownership so any human can see what is happening.

Worker routing tags:
- website_new
- website_hot
- website_warm
- website_contacted
- outreach_eligible
- outreach_hot
- outreach_warm
- outreach_objection
- outreach_dormant
- missed_call_recovered
- missed_call_replied
- missed_call_no_reply
- ad_nurture
- ad_hot
- reputation_review_pending
- reputation_review_published
- reputation_approved
- reputation_escalate
- needs_human
- dnd

Status tags:
- ai_onboarding
- ai_active
- ai_paused
- ai_churned

## Pipelines

### Pipeline 1: AI Lead Flow
Stages:
- New Lead
- Contacted
- Qualified
- Booking Attempt
- Booked
- Not Interested
- Dormant

Used for:
- website_new
- ad leads
- outreach leads

Map pipeline stages to worker tags automatically via workflow.

### Pipeline 2: Reputation Cases
Stages:
- Review Detected
- Response Drafted
- Awaiting Approval
- Published
- Escalated

Used for:
- review response management
- testimonial harvesting

## Workflows

### WF-01: Website Lead First Touch
Trigger:
- Tag added `website_new`
- Contact created with source = website

Actions:
1. Wait 10 seconds (debounce).
2. If `dnd=true`, stop.
3. Send SMS using prewritten simple intro or call WebStaffr webhook to generate dynamic message before sending.
4. Add tag `website_contacted`.
5. Custom field: `website_handled_at = now`, `website_worker_id = website_follow_up`.
6. If no reply in 30 minutes, move to `outreach_eligible`.

Recommendation: for real `<5` minute follow-up, this workflow should call a WebStaffr webhook to generate a personalized message before sending.

### WF-02: Missed Call Recovery
Trigger:
- Inbound call ended with no answer (requires phone integration or workflow trigger from phone provider).
- Caller phone exists in GHL contact lookup.

Actions:
1. Send SMS: missed-call recovery message.
2. Add tag `missed_call_replied` or `missed_call_no_reply`.
3. Custom field: `last_missed_call_text_at = now`.
4. If reply received, add `needs_human` and notify staff.

### WF-03: Outreach Batch Eligibility
Trigger:
- Manual run or scheduled once per day.

Actions:
1. Search contacts with:
   - `outreach_eligible = true` (or no `outreach_stage`)
   - `ai_outreach_count < 6`
   - no future appointments
   - `dnd = false`
2. For each, call WebStaffr webhook or directly queue outreach SMS/email.
3. Update `outreach_stage`, `outreach_count`, `ai_worker_last_touch`.

### WF-04: Post-Appointment Review Request
Trigger:
- Appointment updated to `completed`.

Actions:
1. Wait 24–48 hours.
2. If `review_request_sent` is not true and `dnd` is false:
   - Send SMS/email review request.
   - Set `review_request_sent = true`.
3. If reply is positive, add tag `testimonial_candidate`.

### WF-05: Negative Review Alert
Trigger:
- New review detected on GBP or review monitoring.

Actions:
1. If rating <= 2:
   - Create note on contact record.
   - Add tag `reputation_escalate`.
   - Send internal alert via SMS/email/Slack webhook.
2. Queue AI response draft for approval.

### WF-06: Ad Lead Routing
Trigger:
- Contact created with `ad_source` populated.

Actions:
1. Call WebStaffr ad routing webhook.
2. Add tag `ad_hot` or `ad_nurture`.
3. If hot: send calendar link and notify staff.

### WF-07: Opt-Out Handler
Trigger:
- SMS reply = STOP, UNSUBSCRIBE, or equivalent.
- Manual `dnd` checkbox change.

Actions:
1. Set `dnd = true`.
2. Set `opt_out_reason = inbound` if reply, else manual.
3. Remove from all active workflows using GHL built-in workflow filters if possible.
4. Log event to notes.

## Webhook Configuration

### Inbound to GHL
- Website forms must push `contact.created` events into GHL.
- If your site is custom, use `POST /v1/contacts/` or webhook integrations.
- Ensure `source`, `tags`, and custom fields are set so GHL routing works.

### Outbound from GHL to WebStaffr
Recommended WebStaffr endpoints:
- `POST /api/ghl/webhook` — generic event router
- `POST /api/workers/website-follow-up` — optional worker-specific endpoint
- `POST /api/workers/missed-call-text-back` — optional
- `POST /api/workers/outreach` — optional
- `POST /api/workers/reputation` — optional
- `POST /api/workers/ad-nurture` — optional

GHL workflow HTTP request action:
```
POST https://<webstaffr-domain>/api/workers/{worker}
Headers:
  Authorization: Bearer <webstaffr-api-key>
  X-GHL-Subaccount: <subaccount_id>
Body:
  {
    "event": "contact.created",
    "contact_id": "...",
    "payload": {{JSON payload}}
  }
```

### Authentication
- Verify inbound webhook signatures using GHL secret.
- Verify outbound requests to WebStaffr with Bearer token.
- Include subaccount/tenant identifier in every request.

## SOPs for Each Client Onboarding

1. Import or connect CRM:
   - Existing contacts: tag `ai_onboarding`.
   - Set custom field defaults.
2. Map pipelines and calendars:
   - Confirm booking calendar in GHL.
   - Map phone number to GHL call product or native missed-call call flow.
3. Define worker settings:
   - Website Lead Follow-Up: enable, set first-touch template.
   - Missed Call: connect phone integration, enable missed-call workflow.
   - Outreach: set eligibility rules and cadence.
   - Reputation: connect GBP, set review request template.
   - Ads: connect ad accounts if paid-ad worker is active.
4. Run test leads:
   - Submit website form.
   - Simulate missed call.
   - Send test opt-out.
   - Create test review.
5. Weekly cadence:
   - Review missed-call recovery rate.
   - Review first touch timing.
   - Review outreach reply/booking rate.
   - Adjust prompts and rules based on previous week.

## Common GHL Pitfalls
- SMS permission fields must be set accurately; TCPA depends on it.
- SLA windows depend on business hours config; set this in GHL calendar settings.
- Duplicate workflows cause double sends; audit before enabling.
- Ad custom fields only populate if form or zapier populates them.
- Phone provider missed-call triggers may require a third-party bridge if GHL native telephony does not expose `no-answer` events.
