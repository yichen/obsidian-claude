# FairBridge.app — MVP Software Specification

## Executive Summary

FairBridge is a co-parenting financial platform built on three pillars: ACH payments via Stripe Connect, append-only expense tracking with cryptographic integrity, and a shared custody calendar. The platform prioritizes domestic violence safety defaults, regulatory compliance (no MTL required via Stripe Connect), and a conversion-optimized payee onboarding funnel. This specification defines the complete MVP across backend, web, iOS, Android, and QA.

### Pricing Model

| Role | Price | Channel |
|------|-------|---------|
| Payer | $7/mo or $70/yr | Web-only (NOT Apple IAP) |
| Payee | Free forever | N/A |
| Transaction fee | 0.8% Stripe pass-through | No platform markup V1 |

### Key Success Metrics

| Metric | Target |
|--------|--------|
| Payee activation rate | >50% within 60 days |
| First ACH payment | <10 days from payer signup |
| Nacha unauthorized return rate | <0.5% |

### Pre-Launch Legal Cost

~$4-7K total: ACH authorization language, Reg E notice, AML policy, ToS addendum. Stripe is Nacha TPS; FairBridge is Originator. No MTL needed — launch all 50 states day one.

### Reg E Dispute Obligation

FairBridge must provide provisional credit within 10 business days. Losses absorbed from $5-10K reserve fund.

---

## Technical Stack Summary

| Layer | Technology | Beta Notes |
|-------|-----------|------------|
| Backend | Fastify (Node.js) + TypeScript + Zod validation | |
| Database | PostgreSQL 16 (append-only tables, hash-chained) | |
| Queue | Redis + BullMQ (2 queues for beta; 5 at scale) | Collapsed for beta (~50 pairs) |
| Object Storage | Cloudflare R2 | Free tier sufficient at beta volume |
| Email | Resend | Free tier (3K emails/mo); sufficient at beta |
| SMS | Twilio | **Deferred** — email fallback sufficient at 50 pairs |
| Payments | Stripe Connect Express + Financial Connections | |
| Mobile | React Native (Expo bare workflow) | |
| Mobile builds | EAS Build | Free tier (30 builds/mo) |
| Web | React 18 + TypeScript + Vite + Tailwind + shadcn/ui | |
| State (web) | Zustand (global) + React Query (server) | |
| Forms (web) | React Hook Form + Zod | |
| Calendar (web) | @fullcalendar/react | |
| PDF Export | @react-pdf/renderer (server-side) | |
| Testing | Vitest + React Testing Library + Playwright (E2E) | |
| Auth | Magic link (email) primary + Google OAuth | |
| Hosting (API + DB + Redis) | **Railway** (all-in-one) | ~$38/mo; replaces AWS ECS + RDS + ElastiCache |
| Hosting (web) | **Vercel Hobby** (free) | Sufficient for beta |

**Beta infrastructure cost: ~$38–68/mo** (Railway + optional BetterStack). Full production stack estimated at $845+/mo — scale up at 200+ pairs.

---

## Section Ownership and Status

| Section | Owner | Status | Full Spec File |
|---------|-------|--------|----------------|
| 2. Backend | backend-eng | **Complete** | `Backend-Spec.md` |
| 3. Web Frontend | web-dev | **Complete** | `Web-Frontend-Spec.md` |
| 4. UX Flows | ux-engineer | **Complete** | `UX-Flows-Spec.md` |
| 5. iOS | ios-dev | **Complete** | `iOS-Spec.md` |
| 6. Android | android-dev | **Complete** | `Android-Spec.md` |
| 7. Backend Tests | backend-tester | **Complete** | `Backend-Test-Spec.md` |
| 8. Web Frontend Tests | frontend-tester | **Complete** | `Web-Frontend-Test-Plan.md` |
| 9. iOS Tests | ios-tester | **Complete** | `iOS-Test-Plan.md` |
| 10. Android Tests | android-tester | **Complete** | `Android-Test-Plan.md` |
| 11. Cross-Cutting | security-eng + PM | **Complete** | Integrated in master spec |

All spec files are in `/Users/ychen2/Obsidian/Projects/fairbridge.app/`.

---

## Key Design Constraints (All Sections Must Respect)

1. **Append-Only Data Model**: No UPDATE or DELETE on financial records. Every record includes SHA-256 hash of previous record. Daily Merkle root anchor at 00:05 UTC.
2. **DV Safety Defaults**: No activity timestamps exposed to co-parent. No sensitive content in push payloads. Silent deactivation. Data export/delete. Safety resources link (DV hotline). These are V1 non-negotiable.
3. **Stripe as TPS**: FairBridge is the Originator, Stripe is the Nacha Third-Party Sender. No independent TPS registration. No Money Transmitter Licenses needed.
4. **Web-Only Subscription Purchase**: Mobile apps do NOT sell subscriptions (avoids Apple 30% IAP cut). Subscription management is web-only.
5. **Payee Conversion is #1 Product Risk**: The "money waiting" invite flow must minimize steps. Target >50% conversion.
6. **Asymmetric Verification**: Co-parents independently enter child name + birth year. System matches without exposing one parent's data to the other.
7. **$5 Minimum Transaction**: No payments below $5.
8. **Fraud Ramp-Up**: $2,500/week first 6 payments, $5,000/week after — internal only, NOT published to users.
9. **Notification Architecture**: Push (FCM/APNs) → 15-min email fallback → in-app inbox guaranteed delivery.

---

## RESOLVED CONFLICTS

The following conflicts were identified across agent specs and are resolved here. All agents must use these canonical decisions.

### C1: Pricing

- **Conflict**: Web-dev spec listed $9.99/mo or $79/yr. MVP definition says $7/mo or $70/yr.
- **Resolution**: **$7/mo or $70/yr** per MVP definition. Web-dev spec must be updated.

### C2: Notification Channel IDs (Android)

- **Conflict**: Android-Spec.md uses `payments`, `expenses`, `calendar`. Android-Test-Plan.md uses `fairbridge_payments`, `fairbridge_expenses`, `fairbridge_calendar`.
- **Resolution**: **Use prefixed IDs** (`fairbridge_payments`, `fairbridge_expenses`, `fairbridge_calendar`) to avoid collision with other apps on shared devices. Android-Spec.md must be updated.

### C3: Authentication Strategy

- **Conflict**: Web-dev spec proposes magic link (email) primary + Google OAuth. UX spec proposes email+password + social login.
- **Resolution**: **Magic link primary + Google OAuth secondary**. No password-based auth for MVP. Rationale: magic links eliminate password management complexity, reduce support burden, and are more secure for users who may share devices (DV safety consideration — no password to be coerced into sharing).

### C4: Notification Permission Gate — Block vs Allow

- **Conflict**: iOS spec says notification permission **blocks pairing** (hard gate). Android spec says "do not block onboarding" (soft gate). UX spec needs to reconcile.
- **Resolution**: **Soft gate on both platforms**. Show full-screen pre-prompt and strongly encourage, but allow "Continue without notifications" after one denial. Rationale: hard-blocking alienates users; the email fallback + in-app inbox ensures delivery. However, show persistent in-app banner warning until enabled.

### C5: Biometric App Lock

- **Resolution**: **Deferred to V2** on both platforms. V1 uses platform keystore biometric for token access only.

### C6: Receipt Upload Endpoint

- **Conflict**: iOS spec says `POST /api/expenses/:id/receipt`. Backend spec needs to confirm.
- **Resolution**: **`POST /api/expenses/:id/receipt`** with multipart form data. Backend must implement.

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
│  ┌──────────┐   ┌────────────────┐   ┌────────────────┐     │
│  │ React Web│   │ iOS (RN/Expo)  │   │ Android (RN/   │     │
│  │ (Vite)   │   │ Bare Workflow  │   │ Expo) Bare     │     │
│  └────┬─────┘   └───────┬────────┘   └──────┬─────────┘     │
│       └─────────────────┼───────────────────┘               │
│                         │ HTTPS REST API                     │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  Fastify API Server                          │
│           (Node.js, TypeScript, Zod validation)             │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
┌──────▼──────┐  ┌────────▼────────┐  ┌─────▼──────────┐
│ PostgreSQL  │  │ Redis (BullMQ)  │  │ Cloudflare R2  │
│ Append-only │  │ 2 job queues    │  │ Receipts/Docs  │
│             │  │ (beta; 5 at     │  │                │
│             │  │  scale)         │  │                │
│ Hash-chained│  │                 │  │                │
└─────────────┘  └────────┬────────┘  └────────────────┘
                          │
       ┌──────────────────┼────────────────────┐
       │                  │                    │
┌──────▼──────┐  ┌────────▼────────┐  ┌───────▼────────┐
│   Stripe    │  │  Resend (Email) │  │ Twilio (SMS)   │
│  Connect +  │  │  FCM / APNs    │  │ Highest-stakes │
│  Financial  │  │                 │  │ events only    │
│  Connections│  │                 │  │                │
└─────────────┘  └─────────────────┘  └────────────────┘
```

**BullMQ Queues (beta)**: `operations` (priority-ordered: webhooks→payments→disputes→fraud), `notification` (push→email→in-app). Collapse back to 5 queues at ~500 jobs/day (~200+ pairs).

---

## 2. Backend Specification

> Full spec: `Backend-Spec.md` (60KB, 13 sections)

### 2.1 Database Schema (PostgreSQL 16)

Append-only tables with SHA-256 hash chain: `users`, `co_parent_pairs`, `children`, `expenses`, `payments`, `payment_intents`, `disputes`, `ledger_entries`, `merkle_anchors`, `stripe_processed_events`, `devices`, `user_notifications`.

**Hash computation**: `SHA-256(table_name | record_id | account_id | amount_cents | currency | created_at | prev_hash)`. First record: prev_hash = `'0' * 64` (genesis).

**Append-only enforcement**: PostgreSQL RULEs + triggers prevent UPDATE/DELETE on financial tables. Corrections via compensating entries only.

### 2.2 Stripe Connect + ACH Payment Flow

1. Payer links bank via Stripe Financial Connections (OAuth)
2. Payee creates Stripe Connect Express account
3. Expense confirmed → PaymentIntent created (ACH debit from payer)
4. Webhook lifecycle: `payment_intent.created` → `processing` → `succeeded` / `payment_failed`
5. Dispute lifecycle: `charge.dispute.created` → `updated` → `closed`

### 2.3 Webhook Idempotency

- Check `stripe_event_id` in `stripe_processed_events` table before processing
- PostgreSQL advisory locks per event ID prevent race conditions
- Dead-letter queue via BullMQ: 5 retries with exponential backoff (1s, 2s, 4s, 8s, 16s)
- Failed after 5 retries → alerting (PagerDuty/equivalent)

### 2.4 REST API Endpoints

Key endpoints (see Backend-Spec.md Section 7 for full catalog):

- **Auth**: `POST /auth/magic-link`, `GET /auth/verify`, `POST /auth/google`
- **Devices**: `POST /api/devices` `{ token, platform: 'ios'|'android' }` (user_id from JWT)
- **Expenses**: CRUD + `POST /expenses/:id/confirm`, `POST /expenses/:id/receipt`
- **Payments**: `GET /payments`, `POST /payments/initiate`, `POST /payments/:id/retry`
- **Calendar**: `GET /schedule`, `PUT /schedule/override`, `GET /events`
- **Reports**: `POST /reports/generate` (async), `GET /reports/:id/download`, `GET /reports/verify?hash=`
- **Stripe**: `POST /stripe/financial-connections/session`, `POST /stripe/connect/account`, `POST /stripe/checkout/session`
- **Onboarding**: `POST /onboarding/invite`, `GET /onboarding/invite/:token`, `POST /onboarding/accept/:token`

### 2.5 Notification Dispatch Pipeline

Push (FCM/APNs) → 15-min fallback → Email (Resend) → In-app inbox (guaranteed). **SMS (Twilio) deferred for beta** — email handles payment failures and dispute deadlines at 50-pair scale. Begin A2P 10DLC carrier registration now (4-week lead time) so Twilio is ready to activate when pairs exceed 100.

### 2.6 Fraud Controls

- **Ramp-up**: $2,500/week first 6 payments, $5,000/week after (internal)
- **Velocity**: 3+ failures in 7 days → fraud flag; $500+ expenses in 24h → alert; 10+ expenses/hr → rate limit
- **Cross-account**: same bank → 3+ pairs = flag; same device fingerprint → 5+ accounts = flag
- **IP**: OFAC check; same IP → 5+ pairs = flag; Tor exit → MFA required; IP stored as SHA-256 hash only (DV safety)
- **Return rate dashboard**: per-user ACH return tracking; >15% → auto-suspension

### 2.7 Co-Parent Verification (Asymmetric)

Both parents independently enter child name + birth year. Server-side matching with:
- Case-insensitive, whitespace-trimmed, NFC Unicode normalization
- Apostrophe variant normalization (`O'Brien` = `O'Brien`)
- 3 failed attempts → 15-min cooldown
- API never returns other parent's entered values

### 2.8 DV Safety (Backend)

- No activity timestamps in API responses (no last_login, last_active, read_at, seen_at)
- No sensitive content in push payloads
- Silent deactivation: `POST /account/deactivate?silent=true` — co-parent sees generic "unavailable"
- Data export: `GET /account/export` → ZIP within 72 hours
- Data deletion: PII tombstoned within 30 days; financial records anonymized (user_id = NULL) but retained for legal compliance
- IP stored as SHA-256 hash; geolocation data TTL 24h

---

## 3. Web Frontend Specification

> Full spec: `Web-Frontend-Spec.md` (763 lines, 21 sections)

### Key Decisions

- **Stack**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **State**: Zustand (global) + React Query (server)
- **Auth**: Magic link primary + Google OAuth (no password)
- **Routing**: React Router v6 (`createBrowserRouter`)
- **Hosting**: Vercel (preferred) or Netlify

### 3.1 Architecture

Feature-module organization: `src/{app,pages,features,components,hooks,lib,types}/`. Pages are thin route wrappers; business logic lives in `features/`.

### 3.2 Subscription Management (Web-Only)

**CANONICAL PRICING**: $7/mo or $70/yr (NOT $9.99/$79 — web spec needs update). Stripe Checkout session → redirect to `stripe.com/pay/...` → success/cancel redirect. Mobile deep-links to web for subscription.

### 3.3 Onboarding Flows

- **Payer**: Welcome → Bank link (Stripe Financial Connections) → Invite co-parent → Payment schedule → Review
- **Payee**: "Money waiting" landing page → Create account → Bank link → Confirm → Dashboard
- **Payee invite landing page** (`/invite/:token`): Shows amount, schedule, payer first name + masked surname. Token expires 7 days. Must be <1s LCP.

### 3.4 Calendar View

@fullcalendar/react with custody color-coding (blue = Parent A, green = Parent B, stripe = transition). Week + month views. Client-side pattern engine for 2-2-5-5 and 2-2-3 patterns.

### 3.5 PDF Court Export

Server-side generation via @react-pdf/renderer. SHA-256 hash embedded in every page footer. Verification at `fairbridge.app/verify` (public, no auth). Signed S3 URL download, 1-hour expiry.

### 3.6 DV Safety (Web)

- **Safety Exit Button**: Fixed top-right on every page. `window.location.replace('https://weather.com')` (replaces history). Keyboard shortcut: Escape x3.
- **No in-app messaging** (reduces conflict surface)
- **No read receipts, no "last seen"**
- **Information hiding**: Never show co-parent email/phone/address. Invite links use opaque tokens.

### 3.7 Performance Targets

| Metric | Target |
|--------|--------|
| LCP (invite landing) | <1.0s |
| LCP (dashboard) | <2.5s |
| TTI | <3.5s |
| Bundle (initial) | <200KB gzipped |

---

## 4. UX Flows

> Full spec: `UX-Flows-Spec.md` (54KB, comprehensive screen-by-screen flows)

### 4.1 Payer Onboarding Journey

Welcome → Role Selection → Account Creation (magic link / Google) → Email Verification → Notification Permission (soft gate) → Bank Linking (Stripe Financial Connections) → Invite Co-Parent → Payment Schedule Setup → Custody Calendar Setup → Dashboard.

### 4.2 Payee "Money Waiting" Invite Funnel

This is the #1 conversion-critical flow. Payee receives email with "You have money waiting" → Landing page shows amount + schedule → "Get My Money" CTA → Account creation (email pre-filled) → Bank linking → Confirm → First payment.

**Target**: >50% completion from invite open to bank linked.

### 4.3 Expense Lifecycle

Submit (category, amount, description, receipt, split ratio) → Co-parent notification → Two-party confirmation (Approve & Pay / Decline with reason) → Payment initiated → Settlement.

### 4.4 External Payment Logging

For payments made outside FairBridge (Venmo, Zelle, check, cash): log amount + method + date. No Stripe PaymentIntent created. Hash chain entry appended for audit trail.

### 4.5 Calendar Setup

Preset custody patterns (2-2-5-5, 2-2-3, week-on/week-off, custom). Color-coded parent time. Co-parent confirms pattern independently. Holiday/vacation overrides.

### 4.6 Dispute Workflow

Decline expense → Required reason (10+ chars) → Submitter notified → Counter-evidence flow (future, not V1 full implementation). Reg E ACH disputes handled separately via backend intake.

### 4.7 DV Safety Flows

Silent deactivation (no co-parent notification), data export/delete, safety resources link, exit button on every screen, no activity timestamps.

### 4.8 Notification Permission Gates

**iOS**: Full-screen pre-prompt after email verification. Request `.timeSensitive` entitlement. Soft gate — allow "Continue without notifications" after one denial.

**Android**: Runtime `POST_NOTIFICATIONS` on API 33+. Battery optimization exemption prompt immediately after. OEM-specific handling (Xiaomi Autostart, Samsung Sleeping Apps). Soft gate with persistent warning banner.

### 4.9 Error States

- **Offline**: Expenses queued locally with `client_created_at`. Payments blocked with clear error. Offline banner.
- **Payment failed**: Dashboard banner + retry. 2 automatic retries (D+1, D+3) then manual.
- **Bank linking failed**: Retry prompt + manual routing/account fallback.
- **Notification denied**: In-app inbox fallback. Persistent re-enable banner.

---

## 5. iOS Specification

> Full spec: `iOS-Spec.md` (600 lines, 13 sections)

**Platform**: iOS 16.0+ | **Framework**: React Native (Expo bare workflow)

Key decisions:
- **Expo bare workflow mandatory** (native module access for Keychain biometric, APNs time-sensitive, EventKit write-only, app-switcher masking)
- **APNs time-sensitive notifications** for expense confirmation, payment failure, disputes
- **PHPickerViewController** for receipt photos (no photo library permission needed)
- **Dual calendar export**: direct EventKit write (iOS 17+ write-only) + .ics share sheet fallback
- **Keychain**: `kSecAttrAccessibleWhenUnlockedThisDeviceOnly`, no iCloud sync
- **App switcher masking**: BlurView on `AppState 'inactive'`, ON by default
- **App Store**: P2P exempt from IAP (3.1.3(b)), subscription web-only, test keys for review
- **Biometric app lock**: V2 (deferred)
- **Certificate pinning**: `react-native-ssl-pinning`
- **Jailbreak detection**: Warning only (DV users may need jailbroken devices)

---

## 6. Android Specification

> Full spec: `Android-Spec.md` (1025 lines, 12 sections)

**Platform**: Android 7.0+ (API 24) | **Target**: API 35 | **Framework**: React Native (Expo bare workflow)

Key decisions:
- **FCM high-priority messages** with `PRIORITY_HIGH` notification channels
- **Notification channels**: `fairbridge_payments` (HIGH), `fairbridge_expenses` (DEFAULT), `fairbridge_calendar` (LOW). All use `VISIBILITY_PRIVATE` on lock screen (DV safety).
- **Collapse keys** for expense batching (prevent notification flooding)
- **Battery optimization exemption**: `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` prompt during onboarding. Play Store permits for financial apps.
- **FLAG_SECURE** on all financial screens (payments, expenses, bank linking). Prevents screenshots, screen recording, and recent apps thumbnails.
- **Android Keystore** via `react-native-keychain`. Hardware-backed on API 28+. `EncryptedSharedPreferences` fallback.
- **WorkManager**: 15-min periodic payment status sync as FCM fallback
- **CalendarContract**: Native calendar export with FairBridge-dedicated calendar
- **No cloud backup**: `allowBackup="false"`, `fullBackupContent="false"`, `dataExtractionRules` excludes all
- **ProGuard/R8**: Keep rules for Stripe SDK, React Native, Firebase, react-native-keychain, WorkManager
- **Google Play**: Financial Services declaration, Data Safety form, target API 35
- **Network security**: `cleartextTrafficPermitted="false"` globally (TLS only)

---

## 7. Backend Test Plan

> Full spec: `Backend-Test-Spec.md` (652 lines, 12 sections + appendices)

**Stack**: Vitest + testcontainers-node (PostgreSQL, Redis) + Supertest + stripe-mock + k6

**112 named test cases** across 9 domains:

| Domain | Test IDs | Key Coverage |
|--------|----------|-------------|
| Hash chain | HASH-*, VERIFY-*, CHAIN-INT-* | Computation, verification, tamper detection |
| Merkle root | MERKLE-001→008 | Daily anchor, idempotency, immutability |
| Webhook handlers | SIG-*, IDEM-*, PI-*, DISPUTE-*, CUST-*, ACCT-*, DEAUTH-* | All Stripe events, idempotency race conditions |
| Dead-letter queue | DLQ-001→007 | 5-retry exponential backoff, escalation |
| ACH payment E2E | ACH-HAPPY-*, ACH-FAIL-*, REGE-* | Happy path, 6 failure modes, Reg E provisional credit |
| Fraud controls | FRAUD-VEL/CROSS/IP/RET-* | Velocity, cross-account, OFAC, return rate |
| Co-parent verification | VERIFY-PAIR-001→012 | Unicode, apostrophe normalization, cooldown |
| Notification pipeline | NOTIF-PUSH/EMAIL/INBOX/INT-* | Push → email → inbox fallback, dedup |
| Append-only constraints | APPEND-001→012 | Direct SQL, ORM, superuser — all blocked |
| DV safety | DV-001→011 | Timestamp leakage, silent deactivation, deletion |
| Load testing (k6) | LOAD-001→007, LOAD-FAIL-001→003 | 1000 VUs, per-endpoint thresholds |

**Key risk flags**: Hash chain serialization under concurrent inserts, Reg E 10-business-day holiday calendar, ORM bypass of append-only constraints.

### Load Test Thresholds

| Endpoint | p95 | p99 | Error Rate |
|----------|-----|-----|------------|
| POST /expenses | <200ms | <500ms | <0.1% |
| POST /payments/initiate | <500ms | <1000ms | <0.5% |
| Webhook handler | <100ms | <300ms | <0.01% |
| GET /notifications | <50ms | <100ms | <0.1% |

---

## 8. Web Frontend Test Plan

> Full spec: `Web-Frontend-Test-Plan.md`

**Stack**: Playwright (E2E, multi-browser) + React Testing Library + Vitest (unit) + axe-core (accessibility) + Lighthouse CI (performance) + MSW (API mocks)

**Browser matrix**: Chrome 132-133, Safari 17-18, Firefox 134-135, Edge 132-133. Mobile web: Safari iOS 18, Chrome Android 14.

**Responsive breakpoints**: Mobile (375-767px), Tablet (768-1023px), Desktop (1024px+).

Key test areas:
- **Onboarding flows**: Payer signup, payee invite accept, magic link verification, Google OAuth
- **Expense workflow**: Submit, two-party confirm, decline with reason, receipt upload
- **Payment flows**: Initiate, failure + retry, history display
- **Calendar**: Custody pattern rendering, color-coding, week/month toggle
- **PDF export**: SHA-256 hash verification, download via signed URL
- **Stripe integration**: Financial Connections modal, Connect Express onboarding, Checkout session
- **Subscription**: Web-only purchase, plan display, cancellation
- **DV safety**: Safety exit button (history replacement), no PII in URLs, no activity timestamps
- **Accessibility**: WCAG 2.1 AA, keyboard navigation, screen reader (NVDA, VoiceOver)
- **Visual regression**: Playwright screenshots + Percy/Chromatic

---

## 9. iOS Test Plan

> Full spec: `iOS-Test-Plan.md` (753 lines, 13 sections)

**Device matrix**: iPhone SE 3rd (4.7") through iPhone 15 (6.1" Dynamic Island). iOS 16, 17, 18. Physical devices required for APNs, Keychain biometric, camera.

Key test areas:
- **APNs delivery**: Normal mode, all Focus modes (DND, Sleep, Work, Personal), time-sensitive bypass
- **Notification permission denied**: In-app inbox fallback verification
- **PHPicker**: Zero-permission photo selection, HEIC→JPEG conversion, EXIF GPS stripping
- **Camera**: Blur detection with keep/retake option
- **Calendar**: EventKit write-only (iOS 17+), fallback to .ics share sheet, duplicate prevention
- **Keychain**: Access flags verification, biometric protection, persistence after reinstall
- **App switcher masking**: All financial screens masked
- **Offline**: Expense queued, payment blocked, cached data display
- **Stripe**: Financial Connections OAuth in SFSafariViewController, Connect Express onboarding
- **App Store compliance**: No IAP, P2P exemption, Privacy Manifest

---

## 10. Android Test Plan

> Full spec: `Android-Test-Plan.md` (666 lines, 13 sections + appendices)

**Device matrix**: 10 devices across 4 OEM families (Pixel, Samsung, Xiaomi, OnePlus), API 24-34.

Key test areas:
- **FCM delivery**: Per-OEM testing (stock, One UI, MIUI/HyperOS, OxygenOS). With and without battery exemption.
- **Battery optimization**: Exemption prompt lifecycle, OEM-specific deep links (Xiaomi Autostart)
- **Notification channels**: Correct importance levels, collapse key batching, user customization persistence
- **FLAG_SECURE**: Screenshot blocked, recent apps masked, screen recording blocked, Samsung DeX
- **Android Keystore**: Hardware-backed verification, biometric authentication, token cleared on uninstall
- **Receipt photos**: Per-device-tier quality testing (low-end, mid-range, flagship)
- **Calendar**: CalendarContract export to Google Calendar and Samsung Calendar, duplicate prevention
- **Offline**: Expense queuing, WorkManager sync on reconnection, payment blocking
- **Stripe**: Chrome Custom Tab bank linking, Samsung Internet fallback
- **Google Play compliance**: Financial Services declaration, Data Safety form, permissions audit

---

## 11. Cross-Cutting Concerns

**Owner**: security-eng + program-manager | **Status**: Complete

### 11.1 Authentication and Authorization

**Authentication flow**:
- **Primary**: Magic link (email). User enters email → `POST /auth/magic-link` → Resend delivers email with signed token (HMAC-SHA256, 15-min expiry) → User clicks link → `GET /auth/verify?token=...` → Server validates signature + expiry → Issues JWT access + refresh tokens.
- **Secondary**: Google OAuth via `POST /auth/google` (OAuth 2.0 authorization code flow). No password-based auth for MVP.

**Token architecture**:

| Token | Lifetime | Storage (Web) | Storage (iOS) | Storage (Android) |
|-------|----------|---------------|---------------|-------------------|
| Access JWT | 15 min | httpOnly SameSite=Strict cookie | Keychain (`kSecAttrAccessibleWhenUnlockedThisDeviceOnly`) | Android Keystore (hardware-backed) |
| Refresh token | 30 days | httpOnly SameSite=Strict cookie | Keychain (same) | Android Keystore (same) |

- **No localStorage** for tokens on web (XSS protection)
- **No iCloud Keychain sync** on iOS (DV safety — tokens must not migrate to shared devices)
- **No Google Drive backup** on Android (`allowBackup=false`)
- Refresh token rotation: each refresh issues new refresh token; old token invalidated
- Token revocation: `POST /auth/logout` invalidates all active sessions for user

**Authorization model**:
- Role-based: `payer` and `payee` per co-parent pair (a user can be payer in one pair and payee in another)
- Pair-scoped access: all expense/payment/calendar queries scoped to `pair_id` from JWT claims
- Admin role: separate admin JWT with elevated claims for fraud dashboard, DLQ management
- Rate limiting: 100 req/min per user (general), 10 req/min for auth endpoints (brute-force protection)

### 11.2 Encryption

**In transit**:
- TLS 1.2+ required for all connections (cleartext disabled globally — Android: `cleartextTrafficPermitted="false"`, web: HSTS headers)
- Certificate pinning: `react-native-ssl-pinning` on mobile for `api.fairbridge.app` and `stripe.com`
- CSP headers on web: `script-src 'self' js.stripe.com; connect-src 'self' api.fairbridge.app *.stripe.com`

**At rest**:
- PostgreSQL: encrypted at rest via hosting provider (AWS RDS / equivalent) with AES-256
- Cloudflare R2: server-side encryption (SSE-S3) for receipt images
- Redis: in-memory only; no persistence of sensitive data (BullMQ jobs contain IDs, not PII)
- Backups: encrypted with separate key; tested monthly restore

**Sensitive field handling**:
- IP addresses: stored as SHA-256 hash only (never plaintext)
- Bank account numbers: never stored by FairBridge (Stripe handles via Financial Connections)
- Magic link tokens: HMAC-SHA256 signed, single-use, 15-min TTL
- Stripe webhook signing secret: stored in environment variables, never in code

### 11.3 DV Safety Audit Results

**CRITICAL — Fixed before finalization**:

| ID | Violation | Location | Fix Applied |
|----|-----------|----------|-------------|
| DV-CRIT-1 | iOS APNs example payload contained child name + dollar amount (`"Ruby's soccer registration ($185)"`) in `alert.body` | `iOS-Spec.md` Section 3.2 | Replaced with generic text: `"An expense is waiting for your review in FairBridge."` |
| DV-CRIT-2 | iOS APNs standard payload contained co-parent name + amount (`"$185 sent to Sarah"`) in `alert.body` | `iOS-Spec.md` Section 3.2 | Replaced with: `"A payment has been processed. Tap to view details."` |

**HIGH — Fixed**:

| ID | Violation | Location | Fix Applied |
|----|-----------|----------|-------------|
| DV-HIGH-1 | Android FCM payload missing visible notification title/body (would use data payload which contains `amount_cents`) | `Android-Spec.md` Section 2.1 | Added DV-safe `title: "Payment update"`, `body: "Tap to view details in FairBridge"` to notification block |
| DV-HIGH-2 | Web payee invite landing page shows payer name + payment amount before authentication | `Web-Frontend-Spec.md` Section 5.3 | Acceptable — this is a deliberate conversion decision; payee has opted in by clicking invite link. First name + last initial only (no full name). Amount is necessary for conversion. |
| DV-HIGH-3 | Web frontend test plan references email+password signup (TC-ONB-001) but auth is magic link only | `Web-Frontend-Test-Plan.md` Section 2.1 | Noted for test plan update — no password fields exist |

**DV-safe push notification templates (canonical)**:

| Event | Title | Body |
|-------|-------|------|
| Expense submitted | "Action needed" | "An expense is waiting for your review in FairBridge." |
| Expense approved | "Expense update" | "An expense has been approved. Tap to view." |
| Expense declined | "Expense update" | "An expense needs your attention. Tap to view." |
| Payment initiated | "Payment update" | "A payment is being processed." |
| Payment succeeded | "Payment update" | "A payment has been completed. Tap to view details." |
| Payment failed | "Action needed" | "A payment needs your attention. Tap to review." |
| Dispute filed | "Action needed" | "You have a new item to review in FairBridge." |
| Calendar reminder | "Schedule reminder" | "You have an upcoming schedule event." |

### 11.4 OWASP Top 10 Compliance

| Risk | Mitigation |
|------|-----------|
| A01: Broken Access Control | Pair-scoped queries; JWT claims validated per request; no IDOR (IDs are UUIDs, access checked against pair_id) |
| A02: Cryptographic Failures | TLS 1.2+, AES-256 at rest, SHA-256 hash chain, no plaintext secrets in code |
| A03: Injection | Zod schema validation on all inputs; parameterized SQL queries (no string concatenation); DOMPurify on web |
| A04: Insecure Design | Append-only ledger; DV safety defaults; asymmetric verification; threat modeling in this section |
| A05: Security Misconfiguration | HSTS, CSP, CORS restricted, `X-Frame-Options: DENY`, no default credentials |
| A06: Vulnerable Components | Dependabot/Renovate for dependency updates; Snyk or Socket for supply chain monitoring |
| A07: Auth Failures | Magic link (no passwords to steal); rate limiting on auth endpoints; refresh token rotation |
| A08: Software/Data Integrity | SHA-256 hash chain on all financial records; Stripe webhook signature verification; daily Merkle root |
| A09: Logging/Monitoring | Structured logging (Pino); PII redacted from logs; alerting on DLQ failures, fraud flags, high return rates |
| A10: SSRF | No user-controlled URLs fetched server-side; Stripe webhooks verified by signature |

### 11.5 Regulatory Compliance Matrix

| Regulation | Applicability | FairBridge Obligations |
|------------|--------------|----------------------|
| **Reg E (EFTA)** | ACH transfers are EFTs | Provisional credit within 10 business days; error resolution within 45 days; written disclosure before first transfer; $5-10K reserve |
| **Nacha Operating Rules** | ACH network rules | Maintain <0.5% unauthorized return rate; proper authorization language; FairBridge = Originator, Stripe = TPS |
| **State MTL** | Money transmission | NOT REQUIRED — Stripe Connect handles money movement under Stripe's licenses |
| **CCPA/CPRA** | CA residents | Data access/deletion requests within 45 days; no sale of personal info; privacy policy disclosure |
| **CAN-SPAM** | Marketing emails | Unsubscribe mechanism; physical address in footer; no deceptive subject lines |
| **COPPA** | Children's data | Children's names/DOB stored for verification only; no direct collection from children; parental consent implicit |
| **PCI DSS** | Card data | NOT APPLICABLE — FairBridge never handles card data; Stripe Checkout handles all PCI scope |

### 11.6 Deployment and Infrastructure

#### Beta Stack (~$38–68/mo, sufficient for 0–100 pairs)

| Service | Provider | Cost | Notes |
|---------|----------|------|-------|
| API + PostgreSQL 16 + Redis | **Railway** | ~$5–20/mo | All-in-one; one `railway.toml` replaces ECS + RDS + ElastiCache |
| Web hosting | **Vercel Hobby** | Free | React SPA; upgrade to Pro when custom domain config needed |
| Email | **Resend free tier** | Free | 3K emails/mo; sufficient at beta volume |
| Object storage | **Cloudflare R2** | ~$0 | Free tier covers beta receipt/doc volume |
| Error tracking | **Sentry free tier** | Free | 5K errors/mo; beta generates ~20/mo at 50 pairs |
| Logs + uptime | **BetterStack** | $0–30/mo | Structured logs + uptime monitors + Slack/email alerts |
| Mobile crash reporting | **Firebase Crashlytics** | Free | Unchanged |
| Mobile builds | **EAS Build free tier** | Free | 30 builds/mo; sufficient for initial iteration pace |
| SMS | **Twilio — deferred** | $0 | Email fallback sufficient; start A2P 10DLC registration now |

**Railway notes**: PostgreSQL 16 on Railway is standard Postgres — append-only triggers, pgcrypto, RLS, and `pg_advisory_xact_lock` all work identically. BullMQ connects to Railway Redis (requires Redis 7+, which Railway provides). One `railway.toml` replaces all ECS task definitions.

**CI/CD**: GitHub Actions → lint + test + build → `railway up` deploy.

**Secrets management**: Environment variables via Railway dashboard and Vercel project settings. No `.env` files in repo.

#### Upgrade Path

| Trigger | Upgrade |
|---------|---------|
| 50 paying pairs | Railway Pro ($20/mo flat) |
| 100 pairs | Activate Twilio (A2P 10DLC should be pre-registered) |
| 100 pairs | Migrate PostgreSQL to Neon ($19/mo — serverless, auto-scaling, instant branching for staging) |
| 200 pairs | Add Honeycomb APM (free up to 20M events/mo) |
| 200 pairs + queue backlog | Split `operations` back to 5 BullMQ queues per original 5-queue design |
| Hire 2nd engineer | Add PagerDuty ($42/mo) for on-call rotation |
| 500 pairs | Upgrade EAS Build to Production ($99/mo) |
| Scale | Migrate API to AWS ECS + RDS + ElastiCache per original full-scale design |

### 11.7 Monitoring and Observability

#### Beta Stack (sufficient for 0–100 pairs)

| Signal | Tool | Alerting | Cost |
|--------|------|----------|------|
| Application logs | Pino (structured JSON) → **BetterStack** | Error rate >1% | $0–30/mo |
| Uptime monitors | **BetterStack** | Any downtime → Slack/email | Included above |
| Error tracking | **Sentry free tier** (web + mobile) | New error types | Free (5K errors/mo) |
| Crash reporting | **Firebase Crashlytics** (mobile) | Crash rate >0.5% | Free |
| Fraud alerts | Custom BullMQ → Slack webhook | Any fraud flag | Free |
| DLQ monitoring | BullMQ dashboard | Queue depth >10 → Slack | Free |
| Nacha return rate | Custom dashboard | Rate >0.3% (warn), >0.5% (critical) | Free |
| Financial reconciliation | Daily automated check | Any discrepancy | Free |

**Not included at beta** (add when needed):
- APM (Honeycomb/Datadog) — no load to optimize at 50 pairs; add at 200+ pairs
- PagerDuty — solo founder uses Slack/email alerts; add when hiring 2nd engineer

**PII in logs**: All PII (email, name, bank details) MUST be redacted before logging. Log user_id (UUID) only. IP addresses logged as SHA-256 hash.

### 11.8 Incident Response Plan

1. **Detection**: Automated alerts (Section 11.7) or user report
2. **Triage**: Classify severity (P0: data breach/financial loss, P1: service down, P2: degraded, P3: cosmetic)
3. **Response**: P0/P1 = immediate page to on-call; P2 = next business day; P3 = backlog
4. **Communication**: P0 = user notification within 72 hours (GDPR/CCPA); P1 = status page update
5. **Resolution**: Fix, deploy, verify
6. **Post-mortem**: Blameless; document root cause + prevention measures
7. **DV-specific**: If a DV safety violation is discovered in production (timestamp leakage, name exposure), treat as P0 regardless of scale

---

## Appendix

### A. Spec File Index

| File | Content | Lines |
|------|---------|-------|
| `software-spec.md` | This master spec (integrated) | — |
| `Backend-Spec.md` | Full backend specification | ~600 |
| `Web-Frontend-Spec.md` | Full web frontend specification | 763 |
| `UX-Flows-Spec.md` | Complete UX flows | ~550 |
| `iOS-Spec.md` | iOS implementation spec | 600 |
| `Android-Spec.md` | Android implementation spec | 1025 |
| `Backend-Test-Spec.md` | Backend test plan (~166 test cases) | 652 |
| `iOS-Test-Plan.md` | iOS test plan | 753 |
| `Web-Frontend-Test-Plan.md` | Web frontend test plan | ~500 |
| `Android-Test-Plan.md` | Android test plan | 666 |

### B. Open Items (Pre-Implementation)

1. **Free tier limits**: Define what free tier includes (web-dev spec shows "Expenses: 3/mo, History: 3mo" — needs product owner confirmation).
2. **Real-time updates**: SSE recommended for payment status (resolved — SSE over WebSocket for simplicity).
3. **Web-dev pricing update**: Web-Frontend-Spec.md Section 10.1 still shows $9.99/mo — must be updated to $7/mo per MVP definition (Conflict C1).
4. **Web frontend test plan auth tests**: TC-ONB-001 references password signup but auth is magic link only (DV-HIGH-3). Test plan needs update.
5. **Hash chain serialization**: Backend must implement row-level locking or serializable transactions for concurrent expense inserts (flagged by backend-tester).
6. **Reg E holiday calendar**: 10-business-day provisional credit calculation must exclude federal holidays — holiday list must be maintained.

### C. DV Safety Checklist (System-Wide)

- [ ] No activity timestamps in ANY API response
- [ ] No sensitive content in push notification payloads (no amounts, no names on lock screen)
- [ ] Silent account deactivation without co-parent notification
- [ ] Full data export within 72 hours
- [ ] PII deletion within 30 days (financial records anonymized, retained)
- [ ] Safety Exit Button on every web page (replaces history)
- [ ] App switcher masking on iOS (BlurView) and Android (FLAG_SECURE)
- [ ] IP stored as SHA-256 hash only
- [ ] Geolocation data TTL 24 hours
- [ ] No in-app messaging (reduces conflict surface)
- [ ] No read receipts or "last seen" indicators
- [ ] Jailbreak/root detection: warning only (DV users may need modified devices)
- [ ] Safety resources link (DV hotline) in app settings

### D. API Contract Summary

See `Backend-Spec.md` Section 7 for full endpoint catalog and `Web-Frontend-Spec.md` Section 15 for frontend-required API contracts.
