Subject: WebStaffr status + what it'll take to launch

Status: MVP is live and working.

- Backend deployed on Vercel, Supabase Postgres connected, health check green (verified just now: 200 OK).
- Full flow proven end-to-end in production: intake form leads to generated tenant site, Angel widget, and chat replies via Grok.
- 169/169 tests passing.
- Auth, rate limiting, and RLS are in place on the backend.
- Attribution/call-tracking system built (tracks bookings per tenant). This is what lets us eventually back a "pays for itself" guarantee with real numbers.

Still open:
- GoHighLevel isn't wired in yet. Waiting on your call on when to start the 30-day trial clock.
- No real phone number yet — call tracking exists but points to a placeholder ID, not a live line.
- No paying customers, no CAC data yet — the $150–500 CAC figure in our planning docs is still a placeholder, not measured.

What it'll take to get the show on the road:
1. Form the LLC — cheapest state filing, ~$200.
2. GHL trial started + wired in (free, just needs your go-ahead).
3. A real phone number provisioned through Retell (~$1–3/mo per number plus per-minute usage, roughly $0.07–0.15/min).
4. First round of Meta ads to get HVAC pilot customers in Phoenix — ~$100 to start.

Total to get from here to "first paying customer live": ~$500
- LLC formation: $200
- Meta ads (first round): $100
- Infrastructure (Vercel, Supabase, Retell, xAI usage): ~$200/mo
