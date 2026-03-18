# FairBridge — What You Can Build Before Paying Anything

## Run 100% Locally (Docker)

```bash
# docker-compose.yml — replaces Railway entirely for local dev
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: fairbridge
  redis:
    image: redis:7
  mailpit:           # local SMTP + web UI to catch outgoing emails
    image: axllent/mailpit
    ports: ["8025:8025"]  # open browser to see sent emails
  minio:             # S3-compatible, replaces Cloudflare R2
    image: minio/minio
```

No Railway account needed. The append-only triggers, pgcrypto, hash chain, advisory locks — all identical on local Postgres 16.

## External Services with Free Local Alternatives

| Service | Local substitute | Notes |
|---------|-----------------|-------|
| Railway (Postgres + Redis) | Docker | Identical Postgres 16 + Redis 7 |
| Cloudflare R2 | MinIO or local filesystem | S3-compatible API, swap via env var |
| Resend (email) | Mailpit | Catches all outgoing mail, shows in browser |
| BetterStack (logs) | `pino-pretty` to console | No-op for local dev |
| Sentry | Console errors | Add `NODE_ENV=development` guard |

## Stripe — Free in Test Mode

Stripe test mode costs nothing. You get:
- Fake card numbers that simulate every payment scenario (success, decline, dispute, return)
- `stripe listen --forward-to localhost:3000/webhooks/stripe` — forwards real test webhooks to your local server
- stripe-mock for unit tests (no network call at all)

You never need to pay Stripe until real money moves.

## Mobile

- **iOS simulator**: no cost, no Apple account — runs Expo bare workflow locally
- **Android emulator**: no cost — Android Studio + AVD
- **Push notifications**: FCM is free (just create a Firebase project). APNs on simulator doesn't require a real Apple Developer account — you only need the $99/yr account when you want to test on a real iPhone or submit to TestFlight.

## Web Frontend

```bash
cd web && npm run dev   # Vite dev server, localhost:5173
```

No Vercel account needed until you want a preview URL to share.

## What You Can Build End-to-End Locally

- Full database schema with append-only enforcement, hash chain, Merkle anchors
- All 13 backend API sections (auth, expenses, payments, disputes, calendar, reports, webhooks)
- Stripe Connect Express onboarding flow (test mode)
- ACH payment lifecycle (test mode — Stripe simulates the full webhook sequence)
- BullMQ 2-queue architecture with priority ordering
- Web frontend — all screens, routing, Zustand state, React Query
- iOS simulator — full app including Stripe Financial Connections (opens Safari)
- Android emulator — same
- DV safety features, fraud controls, co-parent verification

## What Requires Paying (and When)

| Cost | When you need it |
|------|-----------------|
| Apple Developer — $99/yr | First time you want TestFlight or real-device APNs |
| Google Play — $25 one-time | First time you want internal test track |
| Railway — ~$5/mo | First deployment to a shared URL (could also use Fly.io free tier) |
| Stripe — 0% until live | Only when real users make real payments |
| Resend — free tier | 3K emails/mo free; enough for beta |
| A2P 10DLC registration | When you activate Twilio (SMS deferred until 100+ pairs) |

**Bottom line**: Build and fully test the entire backend, web, and mobile app with just Docker and a free Stripe account. The first dollar you spend should be Apple Developer ($99/yr) when you're ready to put the app on a real iPhone.
