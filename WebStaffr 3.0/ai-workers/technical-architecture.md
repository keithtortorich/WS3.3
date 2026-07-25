# Technical Architecture — AI Department on GoHighLevel + WebStaffr

## Guiding Principle
Keep GHL as the system of record for contacts, conversations, appointments, compliance state, and core messaging delivery. Replace only what GHL does not natively do.

## Architecture Principle: GHL as Source of Truth
GoHighLevel owns contacts, conversations, appointments, workflows, and compliance state.
- WebStaffr owns AI routing logic, orchestration, custom prompts, and any integration GHL does not natively support.

Each AI worker runs as a discrete service that talks to GHL via:
- REST API for reads/writes
- Webhooks for real-time events
- Workflow / automation triggers for actions inside GHL

## Data Ownership Rules
- All contact history, appointment status, and opt-out state lives in GHL.
- AI-generated message content and decisions are logged as notes or custom fields.
- Campaign attribution, lead source, and ad metadata live in GHL custom fields.
- Recurring billing, usage counters, and subscription tiers are managed outside GHL unless the agency already uses GHL SaaS mode.

## Event Bus: Unified Trigger Map
These are the events that start AI worker logic:

| GHL Event | Worker(s) Triggered |
|---|---|
| contact.created | Website Lead Follow-Up, Outreach Lead Nurturing, Paid Ad Nurturing |
| conversation.message.received | Website Lead Follow-Up, Outreach Lead Nurturing, Missed-Call Text-Back, Paid Ad Nurturing |
| appointment.created / updated | Reputation Management |
| appointment.completed | Reputation Management |
| missed_call.detected | Missed-Call Text-Back |
| inbound.call.ended (no answer) | Missed-Call Text-Back |
| review.created / updated | Reputation Management |
| ad_conversion.received | Paid Ad Nurturing |

These should be implemented as GHL workflows that fire webhooks to WebStaffr endpoints.

## AI Worker Integration Details

### Shared Primitives (All Workers)
- Resolve contact by phone or email across all GHL contacts before acting.
- Check shared `AI Worker` custom field to avoid duplicate outreach.
- Check `Do Not Contact` / opt-out fields before sending.
- Log every outbound action: channel, message_id, timestamp, worker_id.

### Website Lead Follow-Up
GHL-native pieces:
- Contact form submissions routed to a dedicated GHL pipeline and tag `website_new`.
- Existing GHL SMS and email conversation.

WebStaffr custom pieces:
- Webhook listener on `contact.created` with source `website`.
- Scoring logic: form fields + CRM history.
- First-response message generation and dispatch via GHL API.
- Calendar slot check via GHL appointments API or an external scheduler.
- Move lead to `website_hot`, `website_warm`, or `outreach_nurture` after first touch.

Minimal external integrations:
- Website form webhook to GHL (many sites already do this).
- Optional external calendar only if GHL booking is insufficient.

### Missed-Call Text-Back Recovery
GHL-native pieces:
- GHL Conversations SMS.
- Contact search and update.
- Tags for recovery status.

WebStaffr custom pieces:
- Native missed-call trigger from GHL or a call-status webhook to WebStaffr on `call.ended` unanswered.

- First-touch recovery SMS generated and sent via GHL Conversation API.
- Recovery outcome tags: `missed_call_recovered`, `missed_call_replied`, `missed_call_no_reply`.

Minimal external integrations:
- Phone system webhook provider: route missed-call webhooks to WebStaffr or directly into GHL via workflow.
- If GHL phone integration is used, missed-call events may already arrive as GHL conversations.

### Outreach Lead Nurturing
GHL-native pieces:
- Campaigns, tags, pipelines, workflows, SMS/email sequences.
- Contact custom fields for last outreach date, channel used, outcome.

WebStaffr custom pieces:
- Daily batch job: query contacts in `outreach_eligible` status.
- Score and choose channel + message template.
- Write outbound messages through GHL API.
- Update contact fields with `last_outreach_at`, `outreach_worker_id`, `outreach_count`.
- Stop conditions: reply, booking, opt-out.

Minimal external integrations:
- None if all messaging uses GHL native SMS/email.

### Reputation Management
GHL-native pieces:
- Contact and appointment records to trigger post-job requests.
- SMS and email for request delivery.
- Custom fields and notes for review case history.

WebStaffr custom pieces:
- Poll GBP API for new reviews; write results into GHL notes.
- Generate review responses via AI and queue them for human approval inside GHL.
- Post-completion survey workflow and testtimonial capture.
- Weekly GBP post and Q&A response logic.

External integrations:
- Google Business Profile API for reviews, Q&A, posts.
- Optional review monitoring aggregator if multi-platform coverage is required.

### Paid Ad Nurturing
GHL-native pieces:
- Contact source/campaign fields.
- SMS/email follow-up.
- Pipeline and tags for ad-origin leads.

WebStaffr custom pieces:
- Webhook or API poller for ad conversion events from Google Ads and Meta Ads.
- Lead scoring, routing, and fast-track booking logic.
- Weekly campaign performance report sent to owner via GHL conversation or email.
- Budget change recommendations. Do not auto-execute spend changes unless explicitly enabled.

External integrations:
- Google Ads API or Meta Marketing API.
- Offline conversion import if GHL cannot map calls/bookings directly.

## Communication Between Workers
Workers communicate through GHL contact state, not direct calls:

- Website Lead Follow-Up writes `website_handled_at`, `website_worker_id`.
- Missed-Call Text-Back writes `missed_call_handled_at`, `missed_call_worker_id`.
- Outreach Lead Nurturing reads those fields and skips active leads.
- Paid Ad Nurturing writes `ad_source`, `campaign_id`; other workers honor it.

If a worker needs to override another, it checks the most recent `worker_touch` timestamp and channel.

## Compliance and Safety
- All opt-outs are written to GHL global or contact-level suppression fields.
- All messages pass through a content policy filter before send:
  - no refund promises without human sign-off
  - no legal claims
  - no repeated near-duplicate content within 24 hours
- All worker actions are logged with worker_id, timestamp, result, and source trigger.

## Monitoring and Observability
- Per-worker daily metrics:
  - leads handled
  - first touch time
  - reply rate
  - booking rate
  - opt-out rate
- Weekly admin summary delivered into GHL owner inbox.
- Alerting channel for abnormal miss rate, API failure, or duplicate contact risk.

## Development Phases for WebStaffr
Phase 1: Foundation
- GHL webhook receiver + event router
- Contact dedup and suppression
- Website Lead Follow-Up + Missed-Call Text-Back only

Phase 2: Nurture and Reputation
- Outreach Lead Nurturing batch worker
- Reputation Management review response and GBP maintenance

Phase 3: Ads and Optimization
- Paid Ad Nurturing
- Campaign reporting and recommendation engine
- Usage/billing metering if SaaS mode is used

## Non-Goals For Initial Build
- Do not replace GHL UI layers.
- Do not reimplement GHL calendar or conversations.
- Do not build multi-tenant auth if GHL SaaS mode handles sub-accounts.
