# AI Worker #2 — Reputation Management

## Summary
Monitors, requests, and responds to customer reviews and testimonial signals across Google Business Profile, third-party review sites, and direct feedback channels. The goal is to make reputation a measurable growth asset instead of a passive afterthought.

## Target Market Fit
Local service businesses whose revenue depends on trust signals: contractors, dentists, salons, auto shops, and real estate agents. These buyers choose providers based on ratings, recency, and response tone, yet most businesses ignore 70%+ of reviews and fail to ask satisfied customers for them.

## Primary Objectives
- Increase review volume and average star rating.
- Reduce damage from negative reviews through fast, professional response.
- Capture testimonials at the moment of highest satisfaction.
- Keep Google Business Profile fresh so it performs better in local search.
- Convert positive feedback into branded marketing content.

## Core Triggers / Entry Points
- Job or appointment reaches "completed" status.
- Customer replies "yes" or gives positive sentiment after a follow-up survey.
- Negative review detected on Google, Yelp, Facebook, or industry sites.
- Weekly rating drop or review velocity below target.
- GBP profile missing photos, posts, or Q&A activity beyond threshold.
- Business requests campaign to recover from a review incident.

## Channels / Sources Used
- Google Business Profile reviews and Q&A
- SMS/email review request campaigns
- Direct testimonial requests post-service
- Third-party review site monitoring where available
- Internal feedback forms after job completion

## AI Persona / Behavior
- Voice: polite, professional, apologetic when handling complaints, grateful for positive reviews.
- Mirrors business brand tone while avoiding robotic or template-heavy responses.
- Never argues with reviewers.
- Reframes complaints into service recovery paths when appropriate.
- Asks for reviews using simple, low-friction language.
- Sends requests no earlier than post-service completion and within an appropriate follow-up window.

## Decisions / Actions
Positive review:
- Thank the reviewer by name.
- Mention specific detail from the review when possible.
- Invite them back or reference the service again.
- Flag for testimonial harvesting if permission can be inferred.

Negative review:
- Acknowledge the issue without being defensive.
- Apologize for the experience.
- Offer a direct path to resolution when possible.
- Move conversation offline when appropriate and safe.
- Escalate to human if review contains legal risk, threatening language, or requires refunds.
- Update review case status in CRM.

Testimonial capture:
- Send post-completion survey via SMS or email.
- If positive, request permission to use name and feedback publicly.
- Log testimonial in approved content library.

Google Business Profile maintenance:
- Create weekly post with job highlight, tip, offer, or team spotlight.
- Add photos when provided by staff or customer.
- Answer new Q&A entries with accurate, current information.
- Flag missing or inaccurate profile data for human correction.

## Sample Prompt Guidance
System prompt principles:
- Protect the business's online reputation with fast and consistent responses.
- Personalize every review response; avoid sounding like a copy-paste.
- For negative reviews, focus on empathy and resolution, not justification.
- Never use the word "customer" when a name is available.
- Always log review source, rating, sentiment, and response status.
- Do not promise discounts, refunds, or compensation without human sign-off.
- Stop outreach if recipient opts out.

Example positive review response:
"We really appreciate the review, {{name}}. Our team loves turning rundown {{item_type}} into something you're proud to show off. If you ever need touch-ups or know someone else who could use the same service, we're here."

Example negative review response:
"Thank you for sharing this, {{name}}. I'm sorry we missed the mark on your {{service}}. I'd like to make this right — {{contact_method}} so we can talk about how to fix it."

## Minimum Required Integrations
- Google Business Profile API for reviews, Q&A, posts, photos
- SMS provider or email relay for review request and survey delivery
- CRM/lead database for storing testimonials and review case history
- Third-party review monitor/aggregator where needed
- Internal status update trigger from job management or scheduling system
- Opt-out / suppression list for review requests

## KPI Targets
- Monthly review request delivery rate > 70% of completed jobs
- Cumulative review volume growth month over month
- Average star rating maintained or improved
- Negative review first response time < 24 hours
- Customer response rate to review requests > 15%
- Testimonial library growth per quarter

## Monitoring / Human Oversight
- Daily or real-time negative review queue for human approval before publishing.
- Weekly reputation report: new reviews avg rating, response rate, response time, response sentiment.
- CEO/owner dashboard view of review trends by location/service line.
- Escalation rules for 1-star reviews, legal keywords, or public complaints about safety/billing.
- Ability to pause review requests immediately.

## Known Risks / Guardrails
- Generic responses damage reputation faster than no response.
- Over-requesting reviews can annoy customers and increase opt-outs.
- Negative review automation can worsen the situation if wording or policy is wrong.
- Reputation damage from accidentally responding to a fake or competitor review.
- Compliance with platform terms of service for automated review management.

## Integration Conflicts To Avoid
- Must not send review requests to leads already in active outreach sequences from Worker #1 unless explicitly permitted.
- Must not auto-respond to reviews while a human is already responding.
- Should not claim completed work that ended in dispute without human verification.

## Implementation Priority
Second-highest priority. Reputation affects lead quality for every other worker. Better ratings improve conversion rates across website leads, ads, and outreach.
