# FairBridge Backend Specification

**Version**: 1.0
**Date**: 2026-03-17
**Author**: Backend Engineer
**Stack**: Fastify (Node.js) + PostgreSQL + Redis (BullMQ) + Cloudflare R2 + Resend + Twilio

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [PostgreSQL Schema — Append-Only with Hash Chain](#2-postgresql-schema)
3. [Stripe Connect Express Integration](#3-stripe-connect-express-integration)
4. [ACH Payment Flow](#4-ach-payment-flow)
5. [Webhook Handlers](#5-webhook-handlers)
6. [BullMQ Job Queue Architecture](#6-bullmq-job-queue-architecture)
7. [REST API Endpoints](#7-rest-api-endpoints)
8. [Notification Dispatch System](#8-notification-dispatch-system)
9. [Reg E Dispute Intake](#9-reg-e-dispute-intake)
10. [Fraud Controls](#10-fraud-controls)
11. [Co-Parent Verification (Asymmetric)](#11-co-parent-verification)
12. [DV Safety Features](#12-dv-safety-features)
13. [Infrastructure & Config](#13-infrastructure--config)

---

## 1. Architecture Overview

```
                          ┌─────────────────────────────────────────┐
                          │           Fastify API Server             │
                          │  (Node.js, TypeScript, Zod validation)  │
                          └──────────┬──────────────────────────────┘
                                     │
              ┌──────────────────────┼─────────────────────────────┐
              │                      │                              │
     ┌────────▼─────────┐  ┌─────────▼─────────┐      ┌──────────▼─────────┐
     │   PostgreSQL 16  │  │  Redis (BullMQ)   │      │   Cloudflare R2    │
     │  Append-only DB  │  │  Job Queue        │      │  Document/Receipt  │
     │  Hash-chained    │  │  5 queues         │      │  Storage           │
     └──────────────────┘  └───────────────────┘      └────────────────────┘
              │
     ┌────────▼──────────────────────────────────────────┐
     │           External Services                        │
     │  Stripe Connect │ Resend │ Twilio │ FCM │ APNs    │
     └───────────────────────────────────────────────────┘
```

### Key Design Principles

- **Append-only ledger**: No UPDATE/DELETE on financial records. Corrections via compensating entries.
- **SHA-256 hash chain**: Every record hashes its content + previous record hash. Daily Merkle root anchored externally.
- **Idempotency everywhere**: Stripe webhooks, API mutations, job queue processing.
- **DV-safety by default**: No activity timestamps exposed; silent deactivation path available.
- **Reg E compliance**: Full dispute intake, provisional credit, 10-business-day resolution.

---

## 2. PostgreSQL Schema

### 2.1 Hash Chain Implementation

Every table with financial or audit data includes:

```sql
-- Hash chain columns (on all append-only tables)
entry_hash      TEXT NOT NULL,   -- SHA-256 of this row's canonical fields
prev_hash       TEXT NOT NULL,   -- entry_hash of immediately prior row (same table+account scope)
                                 -- First row in scope: prev_hash = '0' * 64 (genesis)
```

**Hash computation (canonical)**:
```
entry_hash = SHA-256(
  table_name || '|' ||
  record_id   || '|' ||
  account_id  || '|' ||       -- scoping key
  amount_cents || '|' ||
  currency    || '|' ||
  created_at  || '|' ||       -- ISO-8601 UTC
  prev_hash
)
```

**Daily Merkle Root Anchor** (job runs at 00:05 UTC):
```sql
CREATE TABLE merkle_anchors (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  anchor_date   DATE NOT NULL UNIQUE,
  table_name    TEXT NOT NULL,
  root_hash     TEXT NOT NULL,   -- Merkle root of all entry_hashes for that day
  leaf_count    INTEGER NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Merkle root is published to an append-only public log (Cloudflare R2 public bucket + optional blockchain anchor via Chainlink Functions — deferred to post-MVP).

### 2.2 Core Schema

```sql
-- ============================================================
-- USERS & AUTH
-- ============================================================

CREATE TABLE users (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email             TEXT NOT NULL UNIQUE,
  phone             TEXT,                          -- E.164 format
  display_name      TEXT NOT NULL,
  avatar_url        TEXT,
  stripe_customer_id TEXT UNIQUE,
  stripe_connect_account_id TEXT UNIQUE,          -- NULL until onboarded
  onboarding_status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (onboarding_status IN ('pending','identity_submitted',
                           'active','restricted','deauthorized')),
  dv_safe_mode      BOOLEAN NOT NULL DEFAULT FALSE, -- DV safety feature flag
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ                    -- soft-delete only
);

CREATE TABLE user_sessions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id),
  token_hash    TEXT NOT NULL UNIQUE,             -- SHA-256 of bearer token
  device_id     TEXT,
  user_agent    TEXT,
  ip_address    TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at    TIMESTAMPTZ NOT NULL,
  revoked_at    TIMESTAMPTZ
);

CREATE TABLE push_tokens (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id),
  platform    TEXT NOT NULL CHECK (platform IN ('fcm','apns')),
  token       TEXT NOT NULL,
  device_id   TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,
  revoked_at  TIMESTAMPTZ,
  UNIQUE (platform, token)
);

-- ============================================================
-- CO-PARENT RELATIONSHIPS
-- ============================================================

CREATE TABLE coparent_pairs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_a_id   UUID NOT NULL REFERENCES users(id),
  parent_b_id   UUID NOT NULL REFERENCES users(id),
  status        TEXT NOT NULL DEFAULT 'invited'
                CHECK (status IN ('invited','active','suspended','dissolved')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  activated_at  TIMESTAMPTZ,
  UNIQUE (parent_a_id, parent_b_id),
  CHECK (parent_a_id <> parent_b_id)
);

-- Asymmetric child verification (each parent enters independently, system matches)
CREATE TABLE child_verifications (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id),
  pair_id         UUID REFERENCES coparent_pairs(id),
  child_name_hash TEXT NOT NULL,  -- SHA-256(normalized_first_name || '|' || normalized_last_name)
  dob_hash        TEXT NOT NULL,  -- SHA-256(YYYY-MM-DD)
  child_display_name TEXT NOT NULL, -- stored in plaintext for UI
  dob_year        INTEGER NOT NULL, -- year only, for age display
  match_status    TEXT NOT NULL DEFAULT 'pending'
                  CHECK (match_status IN ('pending','matched','failed')),
  matched_at      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE children (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pair_id         UUID NOT NULL REFERENCES coparent_pairs(id),
  display_name    TEXT NOT NULL,
  birth_year      INTEGER NOT NULL,
  verification_a  UUID NOT NULL REFERENCES child_verifications(id),
  verification_b  UUID NOT NULL REFERENCES child_verifications(id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- EXPENSES (APPEND-ONLY LEDGER)
-- ============================================================

CREATE TABLE expenses (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pair_id         UUID NOT NULL REFERENCES coparent_pairs(id),
  submitted_by    UUID NOT NULL REFERENCES users(id),
  child_id        UUID REFERENCES children(id),
  category        TEXT NOT NULL,
  description     TEXT NOT NULL,
  amount_cents    BIGINT NOT NULL CHECK (amount_cents > 0),
  currency        TEXT NOT NULL DEFAULT 'USD',
  expense_date    DATE NOT NULL,
  receipt_r2_key  TEXT,                           -- Cloudflare R2 object key
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','approved','disputed','settled')),
  split_pct_a     NUMERIC(5,2) NOT NULL,          -- parent_a share percentage
  split_pct_b     NUMERIC(5,2) NOT NULL,          -- parent_b share percentage
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- Hash chain
  entry_hash      TEXT NOT NULL,
  prev_hash       TEXT NOT NULL,
  CONSTRAINT split_pct_sum CHECK (split_pct_a + split_pct_b = 100.00)
);

CREATE TABLE expense_events (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  expense_id    UUID NOT NULL REFERENCES expenses(id),
  actor_id      UUID NOT NULL REFERENCES users(id),
  event_type    TEXT NOT NULL
                CHECK (event_type IN ('submitted','approved','disputed',
                       'settled','receipt_uploaded','comment_added')),
  payload       JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  entry_hash    TEXT NOT NULL,
  prev_hash     TEXT NOT NULL
);

-- ============================================================
-- PAYMENTS (APPEND-ONLY LEDGER)
-- ============================================================

CREATE TABLE payment_accounts (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id),
  stripe_bank_account_id TEXT NOT NULL UNIQUE,    -- from Financial Connections
  stripe_financial_connection_id TEXT,
  institution_name      TEXT,
  last4                 TEXT NOT NULL,
  account_type          TEXT,                     -- 'checking' | 'savings'
  status                TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','detached','errored')),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE payments (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pair_id                 UUID NOT NULL REFERENCES coparent_pairs(id),
  payer_id                UUID NOT NULL REFERENCES users(id),
  payee_id                UUID NOT NULL REFERENCES users(id),
  expense_id              UUID REFERENCES expenses(id),     -- NULL = ad-hoc payment
  amount_cents            BIGINT NOT NULL CHECK (amount_cents > 0),
  currency                TEXT NOT NULL DEFAULT 'USD',
  memo                    TEXT,
  stripe_payment_intent_id TEXT UNIQUE,
  stripe_charge_id        TEXT UNIQUE,
  stripe_transfer_id      TEXT,                            -- to payee Connect account
  from_account_id         UUID REFERENCES payment_accounts(id),
  status                  TEXT NOT NULL DEFAULT 'initiated'
                          CHECK (status IN ('initiated','processing','succeeded',
                                 'failed','disputed','refunded','cancelled')),
  initiated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at            TIMESTAMPTZ,
  settled_at              TIMESTAMPTZ,
  failure_code            TEXT,
  failure_message         TEXT,
  -- Hash chain
  entry_hash              TEXT NOT NULL,
  prev_hash               TEXT NOT NULL
);

CREATE TABLE payment_events (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  payment_id            UUID NOT NULL REFERENCES payments(id),
  stripe_event_id       TEXT,                      -- for idempotency
  event_type            TEXT NOT NULL,
  payload               JSONB,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  entry_hash            TEXT NOT NULL,
  prev_hash             TEXT NOT NULL
);

-- ============================================================
-- STRIPE WEBHOOK EVENTS (idempotency store)
-- ============================================================

CREATE TABLE stripe_events (
  id              TEXT PRIMARY KEY,               -- stripe event ID (evt_...)
  event_type      TEXT NOT NULL,
  payload         JSONB NOT NULL,
  processed_at    TIMESTAMPTZ,
  processing_error TEXT,
  retry_count     INTEGER NOT NULL DEFAULT 0,
  dead_lettered   BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- DISPUTES (Reg E)
-- ============================================================

CREATE TABLE disputes (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  payment_id            UUID NOT NULL REFERENCES payments(id),
  reporter_id           UUID NOT NULL REFERENCES users(id),
  stripe_dispute_id     TEXT UNIQUE,
  dispute_type          TEXT NOT NULL
                        CHECK (dispute_type IN ('unauthorized','incorrect_amount',
                               'duplicate','quality','reg_e')),
  description           TEXT NOT NULL,
  amount_cents          BIGINT NOT NULL,
  status                TEXT NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open','provisional_credit_issued',
                               'under_review','won','lost','closed')),
  provisional_credit_at TIMESTAMPTZ,
  resolution_due_by     DATE,                     -- 10 business days from open
  resolved_at           TIMESTAMPTZ,
  resolution_note       TEXT,
  evidence_r2_keys      TEXT[],                   -- uploaded docs
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  entry_hash            TEXT NOT NULL,
  prev_hash             TEXT NOT NULL
);

CREATE TABLE dispute_events (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dispute_id    UUID NOT NULL REFERENCES disputes(id),
  stripe_event_id TEXT,
  event_type    TEXT NOT NULL
                CHECK (event_type IN ('opened','stripe_received','evidence_submitted',
                       'provisional_credit_issued','won','lost','closed')),
  payload       JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  entry_hash    TEXT NOT NULL,
  prev_hash     TEXT NOT NULL
);

-- ============================================================
-- CALENDAR
-- ============================================================

CREATE TABLE calendar_events (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pair_id       UUID NOT NULL REFERENCES coparent_pairs(id),
  created_by    UUID NOT NULL REFERENCES users(id),
  child_id      UUID REFERENCES children(id),
  title         TEXT NOT NULL,
  event_type    TEXT NOT NULL
                CHECK (event_type IN ('custody_exchange','medical','school',
                       'activity','holiday','other')),
  start_ts      TIMESTAMPTZ NOT NULL,
  end_ts        TIMESTAMPTZ NOT NULL,
  location      TEXT,
  notes         TEXT,
  rrule         TEXT,                             -- iCal RRULE for recurring
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  cancelled_at  TIMESTAMPTZ
);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================

CREATE TABLE notification_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id),
  channel         TEXT NOT NULL CHECK (channel IN ('push','email','sms','in_app')),
  template        TEXT NOT NULL,
  payload         JSONB,
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','sent','failed','suppressed')),
  external_id     TEXT,                           -- FCM message ID, Resend ID, etc.
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  sent_at         TIMESTAMPTZ,
  failure_reason  TEXT
);

CREATE TABLE in_app_notifications (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id),
  category    TEXT NOT NULL,
  title       TEXT NOT NULL,
  body        TEXT NOT NULL,
  action_url  TEXT,
  read_at     TIMESTAMPTZ,
  dismissed_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- FRAUD MONITORING
-- ============================================================

CREATE TABLE fraud_signals (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id),
  signal_type   TEXT NOT NULL
                CHECK (signal_type IN ('velocity_exceeded','cross_account_match',
                       'ip_geo_mismatch','high_return_rate','suspicious_pattern')),
  severity      TEXT NOT NULL CHECK (severity IN ('low','medium','high','critical')),
  details       JSONB,
  reviewed      BOOLEAN NOT NULL DEFAULT FALSE,
  reviewed_by   TEXT,
  reviewed_at   TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_payments_pair_id ON payments(pair_id);
CREATE INDEX idx_payments_payer_id ON payments(payer_id);
CREATE INDEX idx_payments_stripe_pi ON payments(stripe_payment_intent_id);
CREATE INDEX idx_payment_events_payment_id ON payment_events(payment_id);
CREATE INDEX idx_expenses_pair_id ON expenses(pair_id);
CREATE INDEX idx_expense_events_expense_id ON expense_events(expense_id);
CREATE INDEX idx_stripe_events_type ON stripe_events(event_type);
CREATE INDEX idx_disputes_payment_id ON disputes(payment_id);
CREATE INDEX idx_in_app_notifications_user_unread ON in_app_notifications(user_id) WHERE read_at IS NULL;
CREATE INDEX idx_fraud_signals_user_id ON fraud_signals(user_id, created_at DESC);
CREATE INDEX idx_calendar_events_pair ON calendar_events(pair_id, start_ts);
```

### 2.3 Append-Only Enforcement

```sql
-- Trigger: block UPDATE/DELETE on ledger tables
CREATE OR REPLACE FUNCTION enforce_append_only()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Table % is append-only. Use compensating entries.',
    TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER expenses_append_only
  BEFORE UPDATE OR DELETE ON expenses
  FOR EACH ROW EXECUTE FUNCTION enforce_append_only();

CREATE TRIGGER payments_append_only
  BEFORE UPDATE OR DELETE ON payments
  FOR EACH ROW EXECUTE FUNCTION enforce_append_only();

CREATE TRIGGER disputes_append_only
  BEFORE UPDATE OR DELETE ON disputes
  FOR EACH ROW EXECUTE FUNCTION enforce_append_only();
```

**Exception**: `status` columns need to advance through state machine. Solution: use a separate events table (already designed above) rather than mutating the parent row. Status on the parent table is a **materialized view** of the latest event — updated via a dedicated DB function that is the only path allowed to change it (bypasses trigger via security definer).

---

## 3. Stripe Connect Express Integration

### 3.1 Account Onboarding Flow

```
User signs up
     │
     ▼
POST /v1/auth/register
     │ creates users row + Stripe Customer
     ▼
POST /v1/connect/onboard
     │ creates Stripe Connect Express account
     │ stripe.accounts.create({ type: 'express', capabilities: { transfers: {requested: true} } })
     ▼
Redirect user to Stripe-hosted onboarding URL
     │ stripe.accountLinks.create({ type: 'account_onboarding', ... })
     ▼
Stripe redirects back to /connect/return?account=acct_xxx
     │ update users.onboarding_status = 'identity_submitted'
     ▼
account.updated webhook fires when Stripe approves
     │ update users.onboarding_status = 'active'
     ▼
User can now receive payments
```

### 3.2 Financial Connections (Bank Linking)

```
POST /v1/payment-accounts/link-session
  → stripe.financialConnections.sessions.create({
      account_holder: { type: 'customer', customer: stripe_customer_id },
      permissions: ['payment_method'],
      filters: { countries: ['US'] }
    })
  → return { client_secret }

Client completes Stripe.js Financial Connections flow
  → client_secret resolved → linked_account id available

POST /v1/payment-accounts/attach
  body: { financial_connection_account_id }
  → stripe.paymentMethods.create({
      type: 'us_bank_account',
      us_bank_account: { financial_connections_account: fc_account_id },
      billing_details: { ... }
    })
  → stripe.paymentMethods.attach(pm_id, { customer: customer_id })
  → store in payment_accounts table
```

### 3.3 Express Dashboard Link

```
GET /v1/connect/dashboard-link
  → stripe.accounts.createLoginLink(connect_account_id)
  → return { url }  (single-use, 60s expiry)
```

---

## 4. ACH Payment Flow

### 4.1 State Machine

```
initiated
    │
    ├─ stripe PaymentIntent created (payment_intent.created webhook)
    │
    ▼
processing
    │
    ├─ bank initiated ACH debit (payment_intent.processing)
    │
    ├─── SUCCESS ──────────────────────────────────────────────┐
    │                                                          │
    ▼                                                          ▼
failed                                                    succeeded
    │                                                          │
    │ (retry / notify)                              Transfer to payee Connect
    │                                               account via stripe.transfers.create
    │                                                          │
    ▼                                                          ▼
cancelled                                                   settled
                                                               │
                                              ┌────────────────┴──────────┐
                                              │                           │
                                           disputed                   (terminal)
                                              │
                                    Reg E intake opens
```

### 4.2 Payment Initiation

```typescript
// POST /v1/payments
async function initiatePayment(req: FastifyRequest) {
  const { pair_id, expense_id, amount_cents, memo, from_account_id } = req.body;

  // 1. Validate pair, payer membership, payee Connect account active
  const pair = await getPair(pair_id);
  const payee = getOtherParent(pair, req.user.id);
  assertConnectAccountActive(payee.stripe_connect_account_id);

  // 2. Fraud pre-check
  await fraudPreCheck(req.user.id, amount_cents, req.ip);

  // 3. Compute prev_hash for ledger entry
  const prevHash = await getLatestHash('payments', pair_id);

  // 4. Create PaymentIntent with ACH
  const pi = await stripe.paymentIntents.create({
    amount: amount_cents,
    currency: 'usd',
    customer: req.user.stripe_customer_id,
    payment_method_types: ['us_bank_account'],
    payment_method: fromAccount.stripe_payment_method_id,
    confirm: true,
    transfer_data: {
      destination: payee.stripe_connect_account_id,
    },
    application_fee_amount: computeFee(amount_cents), // platform revenue
    metadata: { pair_id, payment_id: newId, user_id: req.user.id }
  });

  // 5. Insert payment row with hash
  const payment = await db.insertPayment({
    id: newId,
    pair_id,
    payer_id: req.user.id,
    payee_id: payee.id,
    expense_id,
    amount_cents,
    memo,
    stripe_payment_intent_id: pi.id,
    from_account_id,
    status: 'initiated',
    entry_hash: computeHash(/* fields */, prevHash),
    prev_hash: prevHash,
  });

  // 6. Enqueue fraud post-check job
  await fraudQueue.add('post-check', { payment_id: payment.id });

  return payment;
}
```

### 4.3 ACH Timing

| Stage | Timing |
|-------|--------|
| Initiation → Processing | Immediate (next business day batch) |
| ACH debit settles | T+1 to T+2 business days |
| Funds available to payee | T+2 to T+3 business days |
| Return window (insufficient funds, etc.) | Up to T+4 business days |
| Reg E dispute window | 60 days from statement |

---

## 5. Webhook Handlers

### 5.1 Webhook Infrastructure

```typescript
// Fastify route: POST /webhooks/stripe
// Uses stripe.webhooks.constructEvent() for signature verification

async function handleStripeWebhook(req: FastifyRequest) {
  const sig = req.headers['stripe-signature'];
  const event = stripe.webhooks.constructEvent(req.rawBody, sig, WEBHOOK_SECRET);

  // Idempotency check
  const existing = await db.getStripeEvent(event.id);
  if (existing?.processed_at) {
    return { received: true }; // already processed
  }

  // Store event immediately (before processing)
  await db.upsertStripeEvent({
    id: event.id,
    event_type: event.type,
    payload: event.data,
    processed_at: null,
  });

  // Enqueue for async processing
  await webhookQueue.add(event.type, { event_id: event.id }, {
    jobId: event.id,  // BullMQ dedup by jobId
    attempts: 5,
    backoff: { type: 'exponential', delay: 2000 },
  });

  return { received: true };
}
```

### 5.2 All Webhook Event Handlers

```typescript
// webhookQueue processor
const HANDLERS: Record<string, WebhookHandler> = {

  // ── Payment Intent ──────────────────────────────────────────
  'payment_intent.created': async (event) => {
    const pi = event.data.object;
    await db.updatePaymentByStripePI(pi.id, {
      status: 'processing',
    });
    await appendPaymentEvent(pi.id, 'payment_intent.created', pi);
  },

  'payment_intent.processing': async (event) => {
    const pi = event.data.object;
    await db.updatePaymentStatusByStripePI(pi.id, 'processing');
    await appendPaymentEvent(pi.id, 'processing', pi);
    await notificationQueue.add('payment-processing', {
      payment_stripe_pi: pi.id
    });
  },

  'payment_intent.succeeded': async (event) => {
    const pi = event.data.object;
    const payment = await db.updatePaymentStatusByStripePI(pi.id, 'succeeded', {
      processed_at: new Date(),
      stripe_charge_id: pi.latest_charge,
    });
    await appendPaymentEvent(pi.id, 'succeeded', pi);

    // Initiate transfer to payee Connect account
    await transferQueue.add('initiate-transfer', {
      payment_id: payment.id,
      amount: pi.amount - pi.application_fee_amount,
      destination: payment.payee_connect_account_id,
      stripe_pi_id: pi.id,
    });

    await notificationQueue.add('payment-succeeded', { payment_id: payment.id });
    await expenseQueue.add('maybe-settle-expense', { payment_id: payment.id });
  },

  'payment_intent.payment_failed': async (event) => {
    const pi = event.data.object;
    const lastError = pi.last_payment_error;
    await db.updatePaymentStatusByStripePI(pi.id, 'failed', {
      failure_code: lastError?.code,
      failure_message: lastError?.message,
    });
    await appendPaymentEvent(pi.id, 'failed', pi);
    await notificationQueue.add('payment-failed', {
      payment_stripe_pi: pi.id,
      failure_code: lastError?.code,
    });
    await fraudQueue.add('check-return', { stripe_pi_id: pi.id });
  },

  // ── Charge Dispute (Reg E) ──────────────────────────────────
  'charge.dispute.created': async (event) => {
    const dispute = event.data.object;
    const charge = await stripe.charges.retrieve(dispute.charge as string);
    const payment = await db.getPaymentByStripeCharge(charge.id);

    const prevHash = await getLatestHash('disputes', payment.pair_id);
    await db.insertDispute({
      payment_id: payment.id,
      reporter_id: payment.payer_id,
      stripe_dispute_id: dispute.id,
      dispute_type: 'reg_e',
      description: dispute.reason,
      amount_cents: dispute.amount,
      status: 'open',
      resolution_due_by: addBusinessDays(new Date(), 10),
      entry_hash: computeHash(/* fields */, prevHash),
      prev_hash: prevHash,
    });

    await notificationQueue.add('dispute-opened', { stripe_dispute_id: dispute.id });
    await disputeQueue.add('issue-provisional-credit', { stripe_dispute_id: dispute.id });
  },

  'charge.dispute.updated': async (event) => {
    const dispute = event.data.object;
    await appendDisputeEvent(dispute.id, 'stripe_received', dispute);
    // No status change until closed
  },

  'charge.dispute.closed': async (event) => {
    const dispute = event.data.object;
    const status = dispute.status === 'won' ? 'won' : 'lost';
    await db.updateDisputeByStripeId(dispute.id, {
      status,
      resolved_at: new Date(),
    });
    await appendDisputeEvent(dispute.id, status, dispute);
    await notificationQueue.add('dispute-closed', {
      stripe_dispute_id: dispute.id,
      outcome: status,
    });
  },

  // ── Customer ────────────────────────────────────────────────
  'customer.updated': async (event) => {
    const customer = event.data.object;
    // Sync any relevant fields (email, name) if changed via Stripe dashboard
    const user = await db.getUserByStripeCustomerId(customer.id);
    if (!user) return;
    // Log only — source of truth is our DB for most fields
    await db.logCustomerSync(customer.id, event.data.previous_attributes);
  },

  // ── Connect Account ─────────────────────────────────────────
  'account.updated': async (event) => {
    const account = event.data.object;
    const user = await db.getUserByConnectAccount(account.id);
    if (!user) return;

    let newStatus = user.onboarding_status;
    if (account.charges_enabled && account.payouts_enabled) {
      newStatus = 'active';
    } else if (account.requirements?.disabled_reason) {
      newStatus = 'restricted';
    }

    if (newStatus !== user.onboarding_status) {
      await db.updateUserOnboardingStatus(user.id, newStatus);
      await notificationQueue.add('connect-status-changed', {
        user_id: user.id,
        new_status: newStatus,
      });
    }
  },

  'account.application.deauthorized': async (event) => {
    const account = event.data.object;
    const user = await db.getUserByConnectAccount(account.id);
    if (!user) return;
    await db.updateUserOnboardingStatus(user.id, 'deauthorized');
    await notificationQueue.add('connect-deauthorized', { user_id: user.id });
    // Suspend pending payments involving this user
    await paymentQueue.add('suspend-pending-for-user', { user_id: user.id });
  },
};
```

### 5.3 PostgreSQL Advisory Locks (Concurrent Webhook Safety)

```typescript
async function processWithLock(eventId: string, handler: () => Promise<void>) {
  const lockKey = hashToInt64(eventId);  // deterministic lock key
  await db.transaction(async (trx) => {
    // Acquire advisory lock — blocks concurrent processing of same event
    await trx.raw('SELECT pg_advisory_xact_lock(?)', [lockKey]);

    // Re-check idempotency inside lock
    const event = await trx('stripe_events').where({ id: eventId }).first();
    if (event.processed_at) return;

    await handler();

    await trx('stripe_events')
      .where({ id: eventId })
      .update({ processed_at: new Date() });
  });
}
```

---

## 6. BullMQ Job Queue Architecture

### 6.1 Queue Definitions

| Queue | Workers | Purpose |
|-------|---------|---------|
| `webhook` | 3 | Stripe webhook event processing |
| `notification` | 5 | FCM/APNs push → email fallback → in-app |
| `payment` | 2 | Transfer initiation, suspension |
| `fraud` | 2 | Velocity checks, return rate analysis |
| `dispute` | 1 | Provisional credit, evidence collection |

### 6.2 Queue Configuration

```typescript
const BASE_JOB_OPTIONS: JobsOptions = {
  attempts: 5,
  backoff: {
    type: 'exponential',
    delay: 2000,    // 2s, 4s, 8s, 16s, 32s
  },
  removeOnComplete: { count: 1000 },
  removeOnFail: false,   // keep failed jobs for DLQ inspection
};

// Dead-letter queue: jobs that exhaust retries are moved here
const dlq = new Queue('dead-letter', { connection: redisClient });

// On job failure after all retries:
webhookQueue.on('failed', async (job, err) => {
  if (job.attemptsMade >= job.opts.attempts) {
    await dlq.add('dead-letter', {
      originalQueue: job.queueName,
      jobData: job.data,
      error: err.message,
      failedAt: new Date().toISOString(),
    });
    // Alert on-call if critical event type
    if (CRITICAL_EVENT_TYPES.includes(job.data.event_type)) {
      await alertOncall(job, err);
    }
  }
});
```

### 6.3 Merkle Anchor Job (Daily)

```typescript
// Runs at 00:05 UTC via BullMQ cron
await merkleQueue.add('anchor', {}, {
  repeat: { pattern: '5 0 * * *' },
});

async function computeMerkleAnchor(date: string) {
  const rows = await db.raw(`
    SELECT entry_hash FROM payments
    WHERE DATE(created_at AT TIME ZONE 'UTC') = ?
    ORDER BY created_at
    UNION ALL
    SELECT entry_hash FROM expenses
    WHERE DATE(created_at AT TIME ZONE 'UTC') = ?
    ORDER BY created_at
  `, [date, date]);

  const root = merkleRoot(rows.map(r => r.entry_hash));
  await db('merkle_anchors').insert({
    anchor_date: date,
    table_name: 'payments+expenses',
    root_hash: root,
    leaf_count: rows.length,
  });

  // Publish to R2 public bucket
  await r2.put(`merkle/${date}.json`, JSON.stringify({ date, root, leaf_count: rows.length }));
}
```

---

## 7. REST API Endpoints

### 7.1 Base URL & Conventions

```
Base URL: https://api.fairbridge.app/v1
Auth:     Authorization: Bearer <JWT>
Content:  application/json
Versioning: URL path (v1, v2, ...)
Errors:   { error: { code, message, details? } }
Pagination: ?limit=20&cursor=<opaque_cursor>
```

### 7.2 Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account (email + phone) |
| POST | `/auth/login` | Get JWT via magic link / OTP |
| POST | `/auth/otp/send` | Send OTP to phone/email |
| POST | `/auth/otp/verify` | Verify OTP, return JWT |
| POST | `/auth/logout` | Revoke session |
| GET | `/auth/me` | Current user profile |
| PUT | `/auth/me` | Update profile (display_name, avatar) |

### 7.3 Co-Parent Pair & Children

| Method | Path | Description |
|--------|------|-------------|
| POST | `/pairs/invite` | Invite co-parent by email/phone |
| POST | `/pairs/accept` | Accept invite (creates pair) |
| GET | `/pairs/:pair_id` | Get pair details |
| POST | `/pairs/:pair_id/children` | Submit child verification entry |
| GET | `/pairs/:pair_id/children` | List matched children |

### 7.4 Expenses

| Method | Path | Description |
|--------|------|-------------|
| GET | `/expenses` | List expenses for all user's pairs |
| POST | `/expenses` | Submit new expense |
| GET | `/expenses/:id` | Get expense detail + events |
| POST | `/expenses/:id/approve` | Approve expense |
| POST | `/expenses/:id/dispute` | Dispute expense |
| POST | `/expenses/:id/receipt` | Upload receipt → presigned R2 URL |
| GET | `/expenses/summary` | Aggregated totals by category/period |

### 7.5 Payments

| Method | Path | Description |
|--------|------|-------------|
| POST | `/payment-accounts/link-session` | Get Stripe FC client_secret |
| POST | `/payment-accounts/attach` | Attach FC account as payment method |
| DELETE | `/payment-accounts/:id` | Detach bank account |
| GET | `/payment-accounts` | List user's linked accounts |
| POST | `/payments` | Initiate ACH payment |
| GET | `/payments` | List payments (filterable by pair, status) |
| GET | `/payments/:id` | Get payment detail + events |
| GET | `/payments/:id/receipt` | Get tamper-evident payment record |

### 7.6 Calendar

| Method | Path | Description |
|--------|------|-------------|
| GET | `/calendar` | List events (date range) |
| POST | `/calendar/events` | Create calendar event |
| PUT | `/calendar/events/:id` | Update event |
| DELETE | `/calendar/events/:id` | Cancel event (soft) |
| GET | `/calendar/events/:id` | Get event detail |

### 7.7 Notifications

| Method | Path | Description |
|--------|------|-------------|
| GET | `/notifications` | List in-app notifications (unread first) |
| POST | `/notifications/:id/read` | Mark as read |
| POST | `/notifications/read-all` | Mark all as read |
| POST | `/push-tokens` | Register FCM/APNs token |
| DELETE | `/push-tokens/:token` | Deregister token |
| GET | `/notification-preferences` | Get preferences |
| PUT | `/notification-preferences` | Update preferences |

### 7.8 Connect & Stripe

| Method | Path | Description |
|--------|------|-------------|
| POST | `/connect/onboard` | Start Express onboarding |
| GET | `/connect/status` | Get onboarding status |
| GET | `/connect/dashboard-link` | Get Stripe Express dashboard link |

### 7.9 Disputes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/disputes` | Open Reg E dispute |
| GET | `/disputes/:id` | Get dispute status + events |
| POST | `/disputes/:id/evidence` | Upload supporting document |
| GET | `/disputes` | List user's disputes |

### 7.10 Admin / Internal

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/fraud-signals` | Review fraud signals |
| POST | `/admin/fraud-signals/:id/review` | Mark reviewed |
| GET | `/admin/return-rate` | Return rate dashboard |
| GET | `/admin/merkle/:date` | Get Merkle anchor for date |

---

## 8. Notification Dispatch System

### 8.1 Three-Channel Cascade

```
Event occurs
    │
    ▼
notificationQueue.add(template, payload)
    │
    ▼
Worker picks up job
    │
    ├─ 1. Try PUSH (FCM/APNs)
    │       │
    │       ├─ SUCCESS → log sent, set timer for 15-min email fallback check
    │       │            (if user doesn't open: email still sends for critical events)
    │       └─ FAIL (no token, unregistered, etc.) → skip to email
    │
    ├─ 2. Try EMAIL (Resend)
    │       │
    │       ├─ if user has email + event is email-eligible
    │       └─ use templated Resend transactional email
    │
    └─ 3. IN-APP (always)
            → insert into in_app_notifications table
```

### 8.2 Notification Templates

| Template | Push | Email | In-App |
|----------|------|-------|--------|
| `payment-processing` | Yes | No | Yes |
| `payment-succeeded` | Yes | Yes | Yes |
| `payment-failed` | Yes | Yes | Yes |
| `expense-submitted` | Yes | No | Yes |
| `expense-approved` | Yes | No | Yes |
| `expense-disputed` | Yes | Yes | Yes |
| `dispute-opened` | Yes | Yes | Yes |
| `dispute-closed` | Yes | Yes | Yes |
| `connect-status-changed` | Yes | Yes | Yes |
| `connect-deauthorized` | No | Yes | Yes |
| `calendar-event-created` | Yes | No | Yes |
| `pair-invite` | No | Yes | Yes |

### 8.3 FCM / APNs Implementation

```typescript
async function sendPush(userId: string, template: string, payload: object) {
  const tokens = await db.getActivePushTokens(userId);
  if (!tokens.length) return false;

  const results = await Promise.allSettled(
    tokens.map(async (t) => {
      if (t.platform === 'fcm') {
        return fcmAdmin.messaging().send({
          token: t.token,
          notification: buildNotificationBody(template, payload),
          data: { template, ...stringifyPayload(payload) },
          android: { priority: 'high' },
        });
      } else {
        return apnProvider.send(buildApnsNotification(template, payload), t.token);
      }
    })
  );

  // Clean up expired/invalid tokens
  results.forEach((r, i) => {
    if (r.status === 'rejected' && isTokenInvalid(r.reason)) {
      db.revokePushToken(tokens[i].id);
    }
  });

  return results.some(r => r.status === 'fulfilled');
}
```

### 8.4 Email Fallback (15-Minute Window)

```typescript
// After successful push, schedule delayed email for critical events
if (pushSent && CRITICAL_TEMPLATES.includes(template)) {
  await notificationQueue.add(
    'email-fallback',
    { userId, template, payload },
    { delay: 15 * 60 * 1000 }  // 15 minutes
  );
}

// email-fallback handler checks if user opened the push
async function handleEmailFallback({ userId, template, payload }) {
  const pushLog = await db.getRecentPushLog(userId, template, 20 * 60 * 1000);
  if (pushLog?.opened_at) return;  // user saw the push, skip email
  await sendEmail(userId, template, payload);
}
```

---

## 9. Reg E Dispute Intake

### 9.1 Reg E Compliance Timeline

| Requirement | Deadline | Implementation |
|-------------|----------|----------------|
| Acknowledge dispute | Immediately | `dispute-opened` notification + email |
| Provisional credit | Within 10 business days | `issue-provisional-credit` queue job |
| Investigation complete | Within 45 days (90 for POS) | `resolution_due_by` tracked in DB |
| Notify of resolution | Within 3 business days of resolution | `dispute-closed` notification |
| Written explanation if denied | 3 business days | Email template with reason |

### 9.2 Dispute Intake Flow

```typescript
// POST /v1/disputes
async function openDispute(req) {
  const { payment_id, dispute_type, description, amount_cents } = req.body;

  const payment = await db.getPayment(payment_id);
  assertUserInvolvedInPayment(req.user.id, payment);

  // Can user open a dispute? (within 60-day Reg E window)
  const daysSincePayment = daysBetween(payment.settled_at, new Date());
  if (daysSincePayment > 60 && dispute_type === 'reg_e') {
    throw new AppError('DISPUTE_WINDOW_EXPIRED', 'Reg E dispute window is 60 days');
  }

  const dispute = await db.insertDispute({
    payment_id,
    reporter_id: req.user.id,
    dispute_type,
    description,
    amount_cents,
    status: 'open',
    resolution_due_by: addBusinessDays(new Date(), 10),
    entry_hash: computeHash(/* ... */),
    prev_hash: await getLatestHash('disputes', payment.pair_id),
  });

  // Notify both parties
  await notificationQueue.add('dispute-opened', { dispute_id: dispute.id });

  // Schedule provisional credit within 10 business days
  await disputeQueue.add('issue-provisional-credit', { dispute_id: dispute.id }, {
    delay: businessDaysToMs(10),
  });

  return dispute;
}
```

### 9.3 Evidence Upload

```typescript
// POST /v1/disputes/:id/evidence
// Returns a presigned R2 URL; client uploads directly

async function getEvidenceUploadUrl(req) {
  const { dispute_id } = req.params;
  const { filename, content_type } = req.body;

  const key = `disputes/${dispute_id}/evidence/${uuid()}-${sanitize(filename)}`;
  const presignedUrl = await r2.getSignedUrl('putObject', {
    Bucket: R2_BUCKET,
    Key: key,
    ContentType: content_type,
    Expires: 3600,
  });

  // After upload confirmed, record in disputes.evidence_r2_keys
  return { upload_url: presignedUrl, key };
}
```

---

## 10. Fraud Controls

### 10.1 Velocity Monitoring

```typescript
// Runs before payment initiation AND as async post-check
async function checkVelocity(userId: string, amountCents: number) {
  const windows = [
    { label: '1h',  seconds: 3600,   maxCount: 3,  maxAmount: 200000 },
    { label: '24h', seconds: 86400,  maxCount: 10, maxAmount: 1000000 },
    { label: '7d',  seconds: 604800, maxCount: 25, maxAmount: 2500000 },
  ];

  for (const w of windows) {
    const { count, total } = await db.raw(`
      SELECT COUNT(*) as count, COALESCE(SUM(amount_cents),0) as total
      FROM payments
      WHERE payer_id = ? AND initiated_at > NOW() - INTERVAL '${w.seconds} seconds'
      AND status NOT IN ('failed','cancelled')
    `, [userId]);

    if (count >= w.maxCount || (total + amountCents) > w.maxAmount) {
      await recordFraudSignal(userId, 'velocity_exceeded', 'high', {
        window: w.label, count, total, attempted: amountCents
      });
      throw new AppError('PAYMENT_VELOCITY_LIMIT', 'Payment velocity limit exceeded');
    }
  }
}
```

### 10.2 Cross-Account Checks

```typescript
// Detect if same bank account linked to multiple identities
async function checkCrossAccount(userId: string, bankAccountLast4: string) {
  const otherUsers = await db.raw(`
    SELECT pa.user_id, COUNT(*) as count
    FROM payment_accounts pa
    JOIN users u ON pa.user_id = u.id
    WHERE pa.last4 = ? AND pa.user_id <> ?
    AND pa.status = 'active'
    GROUP BY pa.user_id
  `, [bankAccountLast4, userId]);

  if (otherUsers.length > 0) {
    await recordFraudSignal(userId, 'cross_account_match', 'medium', {
      last4: bankAccountLast4,
      other_user_count: otherUsers.length,
    });
    // Don't block — flag for review (legitimate: shared household account)
  }
}
```

### 10.3 IP Geolocation

```typescript
async function checkIPGeolocation(userId: string, ipAddress: string) {
  const geoResult = await geoip.lookup(ipAddress);  // MaxMind GeoLite2
  const userHistory = await db.getRecentLoginLocations(userId, 5);

  const isAnomalous = userHistory.every(h =>
    haversineDistance(h.lat, h.lon, geoResult.lat, geoResult.lon) > 2000  // 2000km
  );

  if (isAnomalous) {
    await recordFraudSignal(userId, 'ip_geo_mismatch', 'medium', {
      ip: ipAddress,
      country: geoResult.country,
      city: geoResult.city,
    });
  }
}
```

### 10.4 Return Rate Dashboard

```sql
-- Admin query: return rate per user (last 90 days)
SELECT
  u.id,
  u.email,
  COUNT(*) FILTER (WHERE p.status = 'failed') as failed_count,
  COUNT(*) as total_count,
  ROUND(
    COUNT(*) FILTER (WHERE p.status = 'failed')::numeric / NULLIF(COUNT(*), 0) * 100,
    2
  ) as return_rate_pct,
  SUM(p.amount_cents) FILTER (WHERE p.status = 'failed') as failed_amount_cents
FROM payments p
JOIN users u ON p.payer_id = u.id
WHERE p.initiated_at > NOW() - INTERVAL '90 days'
GROUP BY u.id, u.email
HAVING COUNT(*) > 2
ORDER BY return_rate_pct DESC;
```

If `return_rate_pct > 15%` after 5+ payments, automatically create `high_return_rate` fraud signal.

---

## 11. Co-Parent Verification

### 11.1 Asymmetric Child Matching

Neither parent sees the other's raw input. The system matches on hashed values:

```typescript
async function submitChildVerification(userId: string, pairId: string, input: {
  firstName: string;
  lastName: string;
  dateOfBirth: string;  // YYYY-MM-DD
  displayName: string;
  dobYear: number;
}) {
  // Normalize and hash
  const nameHash = sha256(
    normalizeString(input.firstName) + '|' + normalizeString(input.lastName)
  );
  const dobHash = sha256(input.dateOfBirth);

  await db.insertChildVerification({
    user_id: userId,
    pair_id: pairId,
    child_name_hash: nameHash,
    dob_hash: dobHash,
    child_display_name: input.displayName,
    dob_year: input.dobYear,
    match_status: 'pending',
  });

  // Check if co-parent already submitted matching entry
  const pair = await db.getPair(pairId);
  const otherUserId = pair.parent_a_id === userId ? pair.parent_b_id : pair.parent_a_id;
  const otherVerification = await db.findChildVerification(otherUserId, pairId, nameHash, dobHash);

  if (otherVerification) {
    // Match found — create verified child record
    await db.createMatchedChild({ pairId, nameHash, dobHash, ...input });
    await db.updateVerificationStatus([userId, otherUserId], pairId, nameHash, 'matched');
    await notificationQueue.add('child-verified', { pair_id: pairId });
  }
}
```

**Privacy**: Raw names and full DOBs never stored in DB. Only hashes + display name (user-provided label) + birth year for age display.

---

## 12. DV Safety Features

### 12.1 No Activity Timestamps Exposed

API responses for payments and expenses **never** include:
- Exact `created_at` timestamps (use relative: "2 days ago" or date-only)
- IP addresses
- Device identifiers
- Login history

`dv_safe_mode` flag on users table: when `true`, strips all timestamp precision from API responses (date only, no time).

### 12.2 Silent Deactivation

```typescript
// DV user requests to deactivate without alerting co-parent
// POST /v1/auth/silent-deactivate

async function silentDeactivate(userId: string) {
  // 1. Soft-delete user (sets deleted_at)
  await db.softDeleteUser(userId);

  // 2. Detach all bank accounts
  await db.detachAllPaymentAccounts(userId);

  // 3. Deauthorize Connect account (does NOT send webhook to co-parent)
  if (user.stripe_connect_account_id) {
    await stripe.accounts.del(user.stripe_connect_account_id);
  }

  // 4. Cancel pending payments
  await db.cancelPendingPaymentsForUser(userId);

  // 5. NO notification to co-parent — they will see "Account unavailable" generically
  // 6. Data export kicked off automatically
  await dataExportQueue.add('export-user-data', { userId, reason: 'silent_deactivate' });
}
```

### 12.3 Data Export / Right to Delete

```typescript
// GDPR/CCPA: user can request full data export
// POST /v1/auth/data-export

// Generates ZIP in R2 with:
// - All expenses (PDF + JSON)
// - All payments (with hash chain proof)
// - All calendar events
// - All notifications
// - Account info
// Sends download link via email (no push — account may be deactivated)

// DELETE /v1/auth/me
// Anonymizes: email → hash, phone → null, display_name → "Deleted User"
// Preserves: payment records (legal requirement), hash chain integrity
```

---

## 13. Infrastructure & Config

### 13.1 Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/fairbridge

# Redis
REDIS_URL=redis://host:6379

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_CONNECT_CLIENT_ID=ca_...

# Cloudflare R2
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=fairbridge-docs

# Resend (email)
RESEND_API_KEY=re_...
RESEND_FROM=noreply@fairbridge.app

# Twilio (SMS)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# FCM
FCM_PROJECT_ID=...
FCM_SERVICE_ACCOUNT_JSON=...

# APNs
APNS_KEY_ID=...
APNS_TEAM_ID=...
APNS_KEY_PATH=/secrets/apns.p8

# GeoIP
MAXMIND_LICENSE_KEY=...
```

### 13.2 Fastify Plugin Structure

```
src/
├── app.ts                    # Fastify instance, plugin registration
├── plugins/
│   ├── auth.ts               # JWT verification plugin
│   ├── stripe.ts             # Stripe client singleton
│   ├── db.ts                 # PostgreSQL pool (node-postgres)
│   ├── redis.ts              # Redis client + BullMQ setup
│   └── r2.ts                 # Cloudflare R2 S3-compatible client
├── routes/
│   ├── auth/
│   ├── expenses/
│   ├── payments/
│   ├── calendar/
│   ├── notifications/
│   ├── disputes/
│   ├── connect/
│   └── webhooks/
│       └── stripe.ts         # POST /webhooks/stripe
├── workers/
│   ├── webhook.worker.ts     # Stripe event handlers
│   ├── notification.worker.ts
│   ├── payment.worker.ts
│   ├── fraud.worker.ts
│   └── dispute.worker.ts
├── services/
│   ├── hash-chain.ts         # SHA-256 hash chain helpers
│   ├── fraud.ts              # Velocity, cross-account, geo checks
│   ├── notification.ts       # FCM/APNs/email dispatch
│   ├── merkle.ts             # Merkle root computation
│   └── child-verify.ts       # Asymmetric child matching
└── types/
    └── index.ts              # Shared TypeScript types / Zod schemas
```

### 13.3 Rate Limits

| Endpoint Category | Limit |
|-------------------|-------|
| Auth (OTP send) | 5/hour per phone |
| Auth (login) | 10/hour per IP |
| Payment initiation | 3/minute per user |
| Expense submission | 20/hour per pair |
| Webhook endpoint | No limit (Stripe IPs only, verified by sig) |
| General API | 100/minute per JWT |

---

## API Contract Summary (for Web & Mobile Teams)

- All timestamps returned as ISO-8601 UTC strings (`2026-03-17T00:00:00Z`)
- Money amounts always in **integer cents** (`amount_cents: 10000` = $100.00)
- Currency always `"USD"` for MVP
- Pagination via opaque cursor: `{ data: [...], next_cursor: "...", has_more: bool }`
- Error format: `{ error: { code: "PAYMENT_VELOCITY_LIMIT", message: "...", http_status: 429 } }`
- Auth: `Authorization: Bearer <jwt>` on all protected routes
- Idempotency: POST endpoints accept `Idempotency-Key` header (stored, replayed on duplicate)
