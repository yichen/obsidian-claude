# FairBridge Backend Test Specification

**Version**: 1.2
**Author**: backend-tester
**Date**: 2026-03-17
**Status**: Draft — for program-manager integration

**v1.1 changes**: Co-parent verification updated from full DOB to birth year only. Fraud section updated with $2,500/$5,000 ramp-up limits, $5 minimum transaction, and Nacha 0.5% return rate threshold tests. SMS added to notification architecture.

**v1.2 changes** (from backend-eng coordination):
- HASH-001: genesis is `'0'.repeat(64)`, not `SHA256("GENESIS")`
- HASH-002/003: hash input is pipe-delimited positional string, not JSON.stringify
- HASH-006: Unicode test updated (amount is bigint cents, no float precision concern)
- HASH-007 removed (float precision n/a — amounts are bigint cents)
- SIG-* tests: use `stripe.webhooks.generateTestHeaderString()` pattern
- IDEM-004: advisory lock is `pg_advisory_xact_lock` (transaction-scoped, auto-releases) — no `finally` needed for lock
- APPEND-001/003: RULE replaced by trigger DDL; SQLSTATE `restrict_violation` (23001)
- APPEND-013: new test for `advance_payment_status()` SECURITY DEFINER exemption
- CHAIN-INT-005: PDF export test (unchanged); CHAIN-INT-006 (new): concurrent insert race via `hash_chain_heads` sentinel table
- DV-001: expanded timestamp suppression list
- Fraud FRAUD_CONFIG constants imported from source for test setup

---

## Executive Summary

FairBridge's backend handles financial transactions between co-parents, court-admissible expense records, and sensitive personal data for potentially vulnerable users (domestic violence survivors). This test specification ensures the system meets correctness, idempotency, legal auditability, fraud resistance, and DV safety requirements before launch.

The test plan is organized into eight domains: (1) hash chain integrity, (2) Stripe webhook handlers, (3) ACH payment flows, (4) fraud controls, (5) co-parent verification, (6) notification delivery, (7) database constraints, and (8) load/performance. Each domain includes unit, integration, and end-to-end tests as appropriate.

---

## 1. Test Infrastructure & Tooling

### 1.1 Stack

| Layer | Tool |
|-------|------|
| Unit tests | Vitest (co-located with source) |
| Integration tests | Vitest + testcontainers-node (PostgreSQL, Redis) |
| E2E API tests | Supertest against Fastify app in test mode |
| Stripe mocking | `stripe-mock` (official Docker image) + Stripe test mode webhooks |
| Load testing | k6 with custom thresholds |
| DB assertion helpers | Custom `pg-assert` utility — queries raw SQL against test DB |

### 1.2 Test Database Policy

- Integration tests spin up a throwaway PostgreSQL 15 container via testcontainers-node
- Each test file gets its own schema, torn down after the suite
- No mocking of the database layer — all DB tests hit real PostgreSQL
- Append-only constraints tested against a real DB with `RULE` and trigger DDL applied

### 1.3 Stripe Test Mode

- Webhook signature tests use `stripe.webhooks.constructEvent()` with test signing secrets
- `stripe-mock` used for unit tests of webhook handler logic in isolation
- Stripe test mode (not mock) used for integration/E2E ACH flow tests
- All test Stripe accounts use `acct_test_*` Connect Express accounts

### 1.4 Seed Data

```typescript
// seeds/co-parent-pair.ts
export const PAYER = { userId: 'usr_payer_001', stripeCustomerId: 'cus_test_payer' };
export const PAYEE = { userId: 'usr_payee_001', stripeConnectAccountId: 'acct_test_payee' };
export const CHILD = { name: 'Emma Chen', birthYear: 2019 }; // birth year only, not full DOB
export const PAIR_ID = 'pair_test_001';
```

---

## 2. SHA-256 Hash Chain Integrity Tests

The expense ledger is append-only with a SHA-256 chain: each record's hash covers `(record_data || prev_hash)`. A daily Merkle root anchors the chain.

### 2.1 Unit Tests — Hash Computation

**File**: `src/ledger/hash-chain.test.ts`

**Hash function signature** (from backend-eng):
```typescript
computeEntryHash(tableName, recordId, scopeKey, amountCents: bigint,
                 currency, createdAt: string, prevHash: string): string
// Input: [tableName, recordId, scopeKey, amountCents.toString(), currency, createdAt, prevHash].join('|')
// Output: SHA-256 hex digest (64 chars)
// createdAt: always microsecond ISO-8601 UTC, e.g. "2026-03-17T00:05:00.000000Z"
```

```
HASH-001: Genesis record has prev_hash = '0'.repeat(64) (64 zero chars — not SHA256("GENESIS"))

HASH-002: Record hash = SHA256("expenses|<uuid>|<pair_id>|500|USD|2026-03-17T00:05:00.000000Z|<prevHash>")
          Input is pipe-delimited positional string — NOT JSON.stringify with alphabetical key sort

HASH-003: Field order is fixed and positional: tableName|recordId|scopeKey|amountCents|currency|createdAt|prevHash
          Swapping any two adjacent fields produces a different hash

HASH-004: computeEntryHash() is pure — same 7 inputs always produce same 64-char hex output

HASH-005: Two records with identical fields but different prevHash produce different hashes

HASH-006: Unicode in a description field has NO effect on hash — description is not an input field;
          hash covers only the 7 positional fields (all scalar, no free-text)

HASH-007: amountCents is bigint — no floating-point representation;
          computeEntryHash(... 199999999n ...) produces same hash on every call (no precision loss)
```

### 2.2 Unit Tests — Chain Verification

**File**: `src/ledger/verify-chain.test.ts`

```
VERIFY-001: verifyChain([]) returns { valid: true, chainLength: 0 }
VERIFY-002: verifyChain([single_record]) returns { valid: true, chainLength: 1 }
VERIFY-003: Valid chain of 100 records passes verification
VERIFY-004: Tampered amount in record 50 of 100 fails at position 50 with record ID
VERIFY-005: Tampered prev_hash in record 50 fails at position 50
VERIFY-006: Deleted record (gap in sequence) detected by seq number discontinuity
VERIFY-007: verifyChain returns { valid: false, firstFailedAt: <record_id> } on failure
VERIFY-008: Chain spanning multiple days verifies correctly (daily anchor is included)
```

### 2.3 Integration Tests — Append and Verify

**File**: `src/ledger/hash-chain.integration.test.ts`

```
CHAIN-INT-001: POST /expenses creates record; DB entry_hash matches computeEntryHash() output

CHAIN-INT-002: 10 sequential expense inserts for same pair produce valid chain
               (SELECT entry_hash, prev_hash ORDER BY created_at → verifyChain() passes)

CHAIN-INT-003: Direct SQL UPDATE on expenses table raises SQLSTATE 23001 (restrict_violation)

CHAIN-INT-004: After DB restore from backup, chain still verifies (hash is self-contained;
               no external state needed)

CHAIN-INT-005: PDF export includes per-record entry_hash; verifyChain on exported data
               matches stored DB hashes

CHAIN-INT-006 (RACE): 50 concurrent expense inserts for same pair via hash_chain_heads sentinel
  Setup: 50 concurrent transactions each calling insertWithHashChain()
  Assert: SELECT COUNT(*) = 50 (no lost inserts)
  Assert: verifyChain() returns { valid: true, chainLength: 50 }
  Assert: each row's prev_hash equals the entry_hash of the chronologically prior row
  Assert: hash_chain_heads row for pair has last_hash = entry_hash of final insert
  Pattern:
    await Promise.all(
      Array.from({ length: 50 }, () =>
        db.transaction(trx => insertWithHashChain(trx, 'expenses', PAIR_ID, makeExpense()))
      )
    );

CHAIN-INT-007: Cross-pair inserts are fully parallel — 100 concurrent inserts across 10 pairs
               (10 per pair) complete without deadlock; all 10 chains verify independently
```

**Concurrent insert design** (confirmed by backend-eng): serialization via `SELECT ... FOR UPDATE` on `hash_chain_heads(table_name, scope_key)` sentinel table — one row per pair acts as a mutex and prev_hash cache. Transaction-scoped lock; auto-releases on commit/rollback. NOT advisory locks (those are for webhook idempotency) and NOT SERIALIZABLE isolation (too broad).

### 2.4 Daily Merkle Root Tests

**File**: `src/ledger/merkle-anchor.test.ts`

```
MERKLE-001: Merkle root of 0 records for a day = SHA256("EMPTY_DAY")
MERKLE-002: Merkle root of 1 record = SHA256(record_hash)
MERKLE-003: Merkle root of 2 records = SHA256(hash_1 + hash_2)
MERKLE-004: Merkle root of odd count (3 records) — last hash duplicated per standard spec
MERKLE-005: anchor_merkle_root cron job inserts exactly 1 row per day into merkle_anchors table
MERKLE-006: Re-running anchor job on same day is idempotent (no duplicate row)
MERKLE-007: merkle_anchors row for prior day cannot be updated (trigger check)
MERKLE-008: Verification API GET /ledger/verify?from=DATE&to=DATE returns per-day pass/fail
```

---

## 3. Stripe Webhook Handler Tests

All webhook events listed in MVP Appendix [15] must be handled. Each handler must be idempotent, protected by advisory locks, and route failures to the dead-letter queue.

### 3.1 Webhook Signature Verification

**File**: `src/webhooks/stripe/signature.test.ts`

```
SIG-001: Valid signature + correct secret → handler invoked
SIG-002: Invalid signature → 400 returned, event not processed
SIG-003: Expired timestamp (>5 min old) → 400 returned
SIG-004: Missing stripe-signature header → 400 returned
SIG-005: Replayed event with valid signature but stale timestamp → 400 rejected
```

### 3.2 Idempotency — Duplicate Event Handling

**File**: `src/webhooks/stripe/idempotency.test.ts`

```
IDEM-001: Processing stripe_event_id twice — second invocation returns 200 without side effects

IDEM-002: stripe_processed_events table has UNIQUE constraint on stripe_event_id

IDEM-003: Race condition — 2 concurrent workers receive same event; only 1 processes it
           Lock: pg_advisory_xact_lock(stripeEventToLockKey(event.id)) — transaction-scoped
           Worker-2 acquires lock after worker-1 commits → finds event in stripe_processed_events
           → exits immediately without processing any side effects

IDEM-004: Advisory lock is pg_advisory_xact_lock (transaction-scoped) — auto-releases on
           commit or rollback. NO explicit finally block needed for lock release.
           Test: handler that throws mid-processing → transaction rolls back → lock released →
           next worker can acquire lock and reprocess

IDEM-005: Idempotency check (SELECT from stripe_processed_events) happens BEFORE any
           business logic mutations, inside the same transaction as the advisory lock
```

**Race Condition Test Pattern (IDEM-003)**:
```typescript
const [result1, result2] = await Promise.all([
  handleWebhook(event, db),
  handleWebhook(event, db),
]);
const processedCount = await db.query(
  'SELECT COUNT(*) FROM stripe_processed_events WHERE stripe_event_id = $1',
  [event.id]
);
expect(processedCount.rows[0].count).toBe('1');
```

**Advisory lock key derivation** (IDEM-003 setup):
```typescript
// SHA-256 of event ID → first 8 bytes → signed int64 (PostgreSQL bigint range)
stripeEventToLockKey('evt_test_abc123') → BigInt value used in pg_advisory_xact_lock($1)
```

**SIG-* test pattern** (use `generateTestHeaderString`, not `constructEvent` with real signing):
```typescript
const payload = JSON.stringify(stripeEvent);
const header = stripe.webhooks.generateTestHeaderString({
  payload, secret: TEST_WEBHOOK_SECRET
});
const response = await app.inject({
  method: 'POST', url: '/v1/webhooks/stripe',
  headers: { 'stripe-signature': header, 'content-type': 'application/json' },
  body: payload,
});
```

**Webhook route config** (for test setup): `POST /v1/webhooks/stripe` — no JWT auth, no rate limiting, no CSRF. Raw body captured by `@fastify/rawbody` before JSON parser.

### 3.3 payment_intent.created

```
PI-CREATED-001: Payment intent record inserted into payment_intents table
PI-CREATED-002: Status set to 'created'; associated expense_id linked
PI-CREATED-003: Notification queued: payer receives "payment initiated" push
PI-CREATED-004: Duplicate event → no second record inserted
```

### 3.4 payment_intent.processing

```
PI-PROC-001: Status updated from 'created' → 'processing'
PI-PROC-002: processing_started_at timestamp recorded
PI-PROC-003: Payee receives "payment on its way" push notification
PI-PROC-004: Duplicate event → status remains 'processing', no duplicate notification
PI-PROC-005: Event received out-of-order (processing before created) → handled gracefully (upsert)
```

### 3.5 payment_intent.succeeded

```
PI-SUC-001: Status updated to 'succeeded'; settled_at timestamp recorded
PI-SUC-002: Expense record marked as settled
PI-SUC-003: Payee receives "payment arrived" push; payer receives "payment sent" push
PI-SUC-004: Stripe transfer amount matches expected split amount (within $0.01 tolerance)
PI-SUC-005: Hash chain record appended for settlement event
PI-SUC-006: Duplicate event → no second settlement, no duplicate notifications
```

### 3.6 payment_intent.payment_failed

```
PI-FAIL-001: Status updated to 'failed'; failure_reason populated from Stripe error code
PI-FAIL-002: Payer notified of failure with actionable message ("Update bank account")
PI-FAIL-003: Expense reverts to 'pending_payment' status
PI-FAIL-004: Insufficient funds → failure_reason = 'insufficient_funds'
PI-FAIL-005: Account closed → failure_reason = 'account_closed'
PI-FAIL-006: return_rate_dashboard incremented for payer's account
PI-FAIL-007: Duplicate event → single failure record, single notification
```

### 3.7 charge.dispute.created

```
DISPUTE-001: Dispute record inserted into disputes table; dispute_id from Stripe
DISPUTE-002: Payment intent status updated to 'disputed'
DISPUTE-003: Both parents notified of dispute opening
DISPUTE-004: Reg E provisional credit record created: payee credited within 10 business days
             (provisional_credit_due_by = created_at + 10 business days)
DISPUTE-005: Dispute evidence collection deadline recorded (Stripe 7-day window)
DISPUTE-006: Fraud flag added to payer profile if dispute_reason in FRAUD_REASONS list
```

### 3.8 charge.dispute.updated

```
DISPUTE-UPD-001: Dispute status updated (pending → under_review → etc.)
DISPUTE-UPD-002: Evidence submission recorded when status changes to 'evidence_submitted'
DISPUTE-UPD-003: No duplicate status transitions on replay
```

### 3.9 charge.dispute.closed

```
DISPUTE-CLS-001: Dispute closed with 'won' → payment reinstated; payee provisional credit reversed
DISPUTE-CLS-002: Dispute closed with 'lost' → payer charged; dispute_loss fee recorded
DISPUTE-CLS-003: Both parents notified of outcome
DISPUTE-CLS-004: Hash chain record appended for dispute resolution
```

### 3.10 customer.updated

```
CUST-UPD-001: Bank account change detected → Financial Connections re-verification required
CUST-UPD-002: Email change propagated to users table
CUST-UPD-003: No-op update (unrelated fields changed) → no side effects
```

### 3.11 account.updated (Connect Express)

```
ACCT-UPD-001: charges_enabled changes false→true → payee marked as 'verified'; payee notified
ACCT-UPD-002: payouts_enabled changes false→true → payout capability recorded
ACCT-UPD-003: requirements.currently_due populated → payee prompted to complete onboarding
ACCT-UPD-004: account.disabled → payee marked inactive; payments blocked; payee notified
```

### 3.12 account.application.deauthorized

```
DEAUTH-001: Connect account deauthorized → payee bank linking status set to 'deauthorized'
DEAUTH-002: Pending payments for this payee moved to 'blocked' status
DEAUTH-003: Payer notified: "Your co-parent has disconnected their bank account"
DEAUTH-004: Payee prompted to re-link bank account on next app open
DEAUTH-005: Hash chain record appended: deauthorization event with timestamp
```

### 3.13 Dead-Letter Queue Tests

**File**: `src/webhooks/stripe/dlq.test.ts`

```
DLQ-001: Handler that throws on first attempt → event enqueued in BullMQ DLQ
DLQ-002: BullMQ retries with exponential backoff: delays = [1s, 2s, 4s, 8s, 16s] (5 retries)
DLQ-003: After 5 failed retries → event moved to 'failed' queue; PagerDuty/alert triggered
DLQ-004: Successful retry on attempt 3 → event removed from retry queue; processed once
DLQ-005: DLQ worker processes events sequentially per pair_id (no parallel processing of same pair)
DLQ-006: Dead-letter event older than 72 hours → escalation notification to ops
DLQ-007: GET /admin/webhooks/dlq returns count of failed events (admin auth required)
```

---

## 4. ACH Payment Flow End-to-End Tests

### 4.1 Happy Path

**File**: `src/payments/ach-flow.e2e.test.ts`

```
ACH-HAPPY-001: Full flow — expense created → confirmed → payment initiated → processing → settled
  Steps:
  1. POST /expenses (payer) → expense_id returned
  2. POST /expenses/:id/confirm (payee) → status = 'confirmed'
  3. POST /payments/initiate → PaymentIntent created; status = 'created'
  4. Stripe webhook: payment_intent.processing → status = 'processing'
  5. Stripe webhook: payment_intent.succeeded → status = 'settled'
  6. GET /expenses/:id → settled_at populated; hash chain entry present
  Assert: entire flow < 3 business days (T+1 ACH next-day standard)

ACH-HAPPY-002: Payer receives payment receipt notification at each status transition
ACH-HAPPY-003: Payee receives "money incoming" notification at processing; "arrived" at succeeded
ACH-HAPPY-004: Split calculation correct: 60/40 split on $100 → payer pays $60, payee receives $40
ACH-HAPPY-005: Multiple expenses batched into single PaymentIntent (weekly sweep)
ACH-HAPPY-006: External payment logged (Venmo): no Stripe PaymentIntent created; hash chain entry appended
```

### 4.2 ACH Failure Paths

```
ACH-FAIL-001: Insufficient funds → payment_failed webhook → expense back to pending_payment
ACH-FAIL-002: Invalid bank account → payment_failed → payer prompted to re-link
ACH-FAIL-003: Bank account closed → payment_failed → failure_reason = 'account_closed'
ACH-FAIL-004: Stripe Financial Connections revoked mid-payment → graceful failure with re-link prompt
ACH-FAIL-005: Network timeout during PaymentIntent creation → retry with same idempotency key
ACH-FAIL-006: Idempotency key reuse: same expense initiated twice → only 1 PaymentIntent created
```

### 4.3 Reg E Dispute Flow

```
REGE-001: Payer files dispute via POST /disputes/intake
  Body: { payment_intent_id, reason, description }
  Assert: dispute record created; Stripe dispute opened via API

REGE-002: Provisional credit to payee within 10 business days
  Assert: provisional_credit record with due_by date = created_at + 10 business days

REGE-003: FairBridge submits evidence to Stripe within 7 days
  Assert: GET /disputes/:id → evidence_submitted_at populated within 7 days

REGE-004: Dispute won → provisional credit reversed; payee balance restored
REGE-005: Dispute lost → payer charged; dispute_fee applied
REGE-006: Dispute intake requires Reg E disclosure acknowledgment (boolean field in request)
REGE-007: Dispute intake rate-limited: max 3 disputes per user per 30-day period
```

---

## 5. Fraud Control Tests

**File**: `src/fraud/fraud-controls.test.ts`

### 5.1 Velocity Spike Detection

```
FRAUD-VEL-001: 3+ payment_failed events in 7 days for same payer → fraud_flag created; account review
FRAUD-VEL-002: $500+ in expenses within 24 hours for a pair → velocity alert queued
FRAUD-VEL-003: 10-15 expenses/day soft rate limit — above 15 triggers 429; 10-15 triggers warning log
FRAUD-VEL-004: Velocity check happens synchronously before PaymentIntent creation
FRAUD-VEL-005: Velocity counters reset at rolling 7-day window (not calendar week)
FRAUD-VEL-006: Payment below $5 minimum (FRAUD_CONFIG.MIN_PAYMENT_CENTS = 500n) → HTTP 422
               before PaymentIntent creation

FRAUD-VEL-007: Weeks 1-6 ramp-up: weekly ACH total > FRAUD_CONFIG.RAMPUP_PHASE1_MAX_CENTS
               ($2,500 = 250_000n cents) → payment blocked; generic error returned to user
               (threshold value NOT in error message, NOT in any API response field)

FRAUD-VEL-008: After 6 settled payments: weekly ACH total > FRAUD_CONFIG.RAMPUP_PHASE2_MAX_CENTS
               ($5,000 = 500_000n cents) → payment blocked with same generic error

FRAUD-VEL-009: Ramp-up counter based on settled payments only (status='succeeded');
               failed/pending/initiated payments do NOT advance the 6-payment counter

FRAUD-VEL-010: Ramp-up limits are hardcoded constants (not config table) — no API endpoint,
               schema introspection, or error message reveals the $2,500/$5,000 values
```

**Test setup note**: import constants directly from source to stay in sync with implementation:
```typescript
import { FRAUD_CONFIG } from 'src/services/fraud';
// Use FRAUD_CONFIG.RAMPUP_PHASE1_MAX_CENTS rather than hardcoding 250000 in tests
```
```

### 5.5 Nacha Return Rate Compliance

```
FRAUD-NACHA-001: Unauthorized ACH return rate monitored; alert triggered when rate approaches 0.5%
                 threshold (Nacha limit for unauthorized returns)
FRAUD-NACHA-002: Return rate = unauthorized returns / total originations over rolling 60-day window
FRAUD-NACHA-003: At 0.4% rate → ops alert + automatic review of recent originations
FRAUD-NACHA-004: Admin dashboard displays current return rate with 60-day trend chart
```

### 5.2 Cross-Account Flagging

```
FRAUD-CROSS-001: Same bank account linked to 3+ distinct co-parent pairs → fraud alert
FRAUD-CROSS-002: Same device fingerprint across 5+ accounts → flag for review
FRAUD-CROSS-003: Payee account receiving from 10+ distinct payers → flag (potential money mule)
FRAUD-CROSS-004: Cross-account check runs asynchronously (does not block payment initiation)
```

### 5.3 IP Geolocation

```
FRAUD-IP-001: Login from IP in OFAC-sanctioned country → account locked; event logged
FRAUD-IP-002: Same IP initiating payments for 5+ distinct pairs → velocity flag
FRAUD-IP-003: Tor exit node IP detected → require MFA re-verification
FRAUD-IP-004: IP check uses MaxMind GeoLite2 (or equivalent); stale DB (>30 days) triggers alert
FRAUD-IP-005: IP stored as hash, not plaintext (DV safety — cannot be used to locate user)
```

### 5.4 Return Rate Dashboard

```
FRAUD-RET-001: return_rate_dashboard shows per-user ACH return counts (R01, R02, R03 codes)
FRAUD-RET-002: Return rate > 15% for any user → automatic account suspension
FRAUD-RET-003: Admin GET /admin/fraud/return-rates returns paginated list sorted by rate desc
FRAUD-RET-004: Return rate resets on a 90-day rolling window
```

---

## 6. Asymmetric Co-Parent Verification Tests

Both parents independently enter child name and birth year (NOT full DOB — birth year only). System matches without showing either parent's entry to the other.

**File**: `src/pairing/verification.test.ts`

```
VERIFY-PAIR-001: Exact match — "Emma Chen" + birth year 2019 → pair confirmed
VERIFY-PAIR-002: Case-insensitive match — "emma chen" + 2019 matches "Emma Chen" + 2019
VERIFY-PAIR-003: Trailing whitespace — "Emma Chen  " matches "Emma Chen"
VERIFY-PAIR-004: Mismatch on name — "Emma Chen" vs "Emily Chen" → pair rejected; neither sees other's entry
VERIFY-PAIR-005: Birth year mismatch — same name, wrong year (e.g., 2018 vs 2019) → pair rejected
VERIFY-PAIR-006: Unicode name — "Zoë Müller-García" matches "Zoë Müller-García" (NFC normalization)
VERIFY-PAIR-007: Special chars — "O'Brien" matches "O'Brien" (apostrophe variants normalized)
VERIFY-PAIR-008: Arabic name — "محمد" matches "محمد" (RTL text handled)
VERIFY-PAIR-009: Very long name (255 chars) — handled without truncation error
VERIFY-PAIR-010: Matching is server-side only; API never returns other parent's entered values
VERIFY-PAIR-011: After 3 failed verification attempts → cooldown period (15 min) enforced
VERIFY-PAIR-012: Verification tokens expire after 48 hours (prevent stale invite abuse)
```

---

## 7. Notification Delivery Pipeline Tests

**File**: `src/notifications/delivery.test.ts`

### 7.1 Push Notification (FCM/APNs)

```
NOTIF-PUSH-001: Successful FCM delivery → notification_log status = 'delivered'
NOTIF-PUSH-002: Successful APNs delivery → notification_log status = 'delivered'
NOTIF-PUSH-003: Push to device with no token → skip push; proceed to email fallback immediately
NOTIF-PUSH-004: Push payload size ≤ 4KB (FCM limit enforced)
NOTIF-PUSH-005: APNs time-sensitive notification flag set for payment-related events
NOTIF-PUSH-006: DV safety — push notification body contains NO amounts, NO names, NO sensitive content
                visible on lock screen; body text is generic (e.g., "You have a FairBridge update")
NOTIF-PUSH-007: Full notification detail only revealed after unlock + app open
```

### 7.2 Email Fallback (15-minute window)

```
NOTIF-EMAIL-001: FCM returns 'NotRegistered' error → email sent via Resend within 15 minutes
NOTIF-EMAIL-002: APNs returns 'BadDeviceToken' → email fallback triggered
NOTIF-EMAIL-003: FCM timeout (>10s) → email fallback triggered
NOTIF-EMAIL-004: Email sent successfully → notification_log updated to 'email_delivered'
NOTIF-EMAIL-005: Email to invalid address → in-app inbox fallback triggered
NOTIF-EMAIL-006: No email on file → skip email; go directly to in-app inbox
```

### 7.3 In-App Inbox (Final Fallback)

```
NOTIF-INBOX-001: All delivery channels failed → notification created in user_notifications table
NOTIF-INBOX-002: GET /notifications returns unread inbox items for authenticated user
NOTIF-INBOX-003: POST /notifications/:id/read marks notification as read
NOTIF-INBOX-004: Inbox items persist for 90 days; older items pruned by nightly cron
NOTIF-INBOX-005: Inbox items never contain activity timestamps (DV safety — see §9)
```

### 7.4 SMS (Highest-Stakes Events Only)

SMS via Twilio is reserved for payment failure and dispute deadline events only.

```
NOTIF-SMS-001: payment_intent.payment_failed → SMS sent to payer within 60 seconds
NOTIF-SMS-002: Dispute evidence deadline approaching (24h before) → SMS sent to both parents
NOTIF-SMS-003: SMS NOT sent for routine events (expense added, calendar update, etc.)
NOTIF-SMS-004: SMS body contains no sensitive data (no amounts, no names) — DV safety
NOTIF-SMS-005: Invalid/missing phone number → SMS skipped silently; in-app inbox fallback
NOTIF-SMS-006: SMS delivery tracked in notification_log; failure logged but does not block other channels
```

### 7.5 Delivery Pipeline Integration

```
NOTIF-INT-001: Full pipeline test — push fails → email fallback → in-app fallback, all within 15 min
NOTIF-INT-002: Notification deduplication — same event triggers only 1 notification per user per 5 min
NOTIF-INT-003: Notification queue survives Redis restart (BullMQ persistent job store)
NOTIF-INT-004: High priority payment notifications bypass throttle limits
NOTIF-INT-005: SMS and push can fire simultaneously for payment failure (independent channels)
```

---

## 8. Append-Only Database Constraint Tests

**File**: `src/db/append-only.test.ts`

The `expenses`, `payments`, `disputes`, `merkle_anchors`, `payment_events`, and `expense_events` tables are append-only. Enforced by **BEFORE triggers** (not RULE — RULE silently swallows ops and returns success, which would make these tests pass vacuously). Triggers raise SQLSTATE `restrict_violation` (23001).

```
APPEND-001: Direct SQL UPDATE on expenses → raises PostgreSQL exception with SQLSTATE 23001
            Assert: error message contains 'append-only' and table name 'expenses'

APPEND-002: Direct SQL DELETE on expenses → raises SQLSTATE 23001

APPEND-003: ORM UPDATE on expenses (e.g. drizzle .update().set()) → SQLSTATE 23001 propagated
            to application layer as a catchable database error (NOT silent success)

APPEND-004: ORM DELETE on expenses → SQLSTATE 23001 propagated

APPEND-005: UPDATE on payments → exception (note: status advancement via advance_payment_status()
            SECURITY DEFINER function is the only permitted exception — see APPEND-013)

APPEND-006: DELETE on payments → exception

APPEND-007: UPDATE on merkle_anchors → exception

APPEND-008: DELETE on merkle_anchors → exception

APPEND-009: INSERT on expenses → succeeds (triggers are BEFORE UPDATE/DELETE only)

APPEND-010: Soft-delete: voiding an expense inserts a new record with type='void' referencing
            original record_id; does NOT UPDATE the original row

APPEND-011: DB superuser also blocked — triggers fire for ALL roles (trigger function does NOT
            check current_user, except for the fairbridge.allow_status_update session variable)

APPEND-012: pg_dump + restore preserves triggers (triggers are schema objects)

APPEND-013: advance_payment_status(payment_id, new_status) SECURITY DEFINER function
            succeeds in advancing payment status (sets fairbridge.allow_status_update = 'true'
            locally before UPDATE)
            Assert: direct UPDATE on payments still raises 23001 (session var not set)
            Assert: advance_payment_status() succeeds and status is updated
```

**Trigger DDL** (do NOT use RULE):
```sql
CREATE OR REPLACE FUNCTION enforce_append_only() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF current_setting('fairbridge.allow_status_update', true) = 'true' THEN
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'Table "%" is append-only. Operation "%" is not permitted.',
    TG_TABLE_NAME, TG_OP
  USING ERRCODE = 'restrict_violation';
END;
$$;
-- Applied as BEFORE UPDATE / BEFORE DELETE trigger on each append-only table
```

---

## 9. DV Safety Tests

**File**: `src/safety/dv-safety.test.ts`

```
DV-001: No activity timestamps in API responses (all users have dv_safe_mode=true by default in V1)
  Assert: GET /expenses/:id response does NOT contain any of:
    last_login, last_active, read_at, seen_at,      // (original list)
    updated_at, processed_at, initiated_at,          // payments table fields
    sent_at, last_used_at, revoked_at               // notification/token fields
  Assert: initiated_at and settled_at appear as date-only strings ("2026-03-17"),
          NOT as full timestamps ("2026-03-17T14:23:00Z")

DV-002: No activity timestamps in push notification payloads
  Assert: FCM/APNs payload does not include any timestamp beyond payment date

DV-003: No activity timestamps in email content
  Assert: Email body does not include "last seen", "active X minutes ago" etc.

DV-004: Silent deactivation — user deactivates account without notifying co-parent
  POST /account/deactivate (with silent=true) →
    - Account deactivated
    - Co-parent receives NO notification
    - Co-parent's app shows generic "co-parent unavailable" state

DV-005: Silent deactivation — co-parent API calls return 404 (not 403) to avoid revealing account exists

DV-006: Data export — GET /account/export returns ZIP with all user data within 72 hours

DV-007: Data deletion — DELETE /account/me triggers:
  - User PII replaced with tombstone values within 30 days
  - Financial records (expenses, payments) anonymized but NOT deleted (legal retention)
  - Stripe customer deleted via Stripe API
  - All push tokens revoked

DV-008: Data deletion completeness check:
  Assert: After deletion, GET /users/:id returns 404
  Assert: expenses table retains records but with user_id = NULL (anonymized)
  Assert: No PII fields (name, email, phone) remain linked to deleted user_id

DV-009: Safety exit — pressing 5-tap safety gesture clears app from recents and opens browser
  (Backend: POST /session/emergency-exit → all active sessions invalidated immediately)

DV-010: IP addresses stored as SHA-256 hash only; raw IP never persisted to DB

DV-011: Geolocation data (city/region from IP) not stored beyond fraud check window (24h TTL)
```

---

## 10. Load Testing Thresholds

**Tool**: k6
**Target**: 1,000 concurrent users
**File**: `load-tests/k6-scenarios.js`

### 10.1 Baseline Thresholds

| Endpoint | p95 Latency | p99 Latency | Error Rate |
|----------|-------------|-------------|------------|
| POST /expenses | < 200ms | < 500ms | < 0.1% |
| GET /expenses | < 100ms | < 200ms | < 0.1% |
| POST /payments/initiate | < 500ms | < 1000ms | < 0.5% |
| Webhook handler (any) | < 100ms | < 300ms | < 0.01% |
| GET /calendar | < 100ms | < 200ms | < 0.1% |
| GET /notifications | < 50ms | < 100ms | < 0.1% |

### 10.2 Load Test Scenarios

```
LOAD-001: Ramp test — 0 → 1000 VUs over 5 minutes; hold 10 minutes; ramp down
  Assert: No error rate spike during ramp; p99 latency stays within threshold

LOAD-002: Spike test — instant 1000 VU spike for 2 minutes
  Assert: System recovers within 60 seconds of spike end; no data corruption

LOAD-003: Webhook flood — 500 webhook events/second for 60 seconds (simulating end-of-month ACH batch)
  Assert: All events processed within 5 minutes; no events lost; DLQ empty after processing

LOAD-004: Concurrent pair verification — 500 concurrent co-parent pairs completing verification simultaneously
  Assert: No cross-contamination of verification data between pairs

LOAD-005: Notification flood — 10,000 notifications dispatched simultaneously
  Assert: All delivered within 15 minutes; no duplicate deliveries

LOAD-006: Hash chain integrity under load — 1000 concurrent expense inserts
  Assert: After load test, verifyChain() passes for all 1000 pairs' chains

LOAD-007: DB connection pool — confirm pool of 20 connections handles 1000 concurrent requests via queueing
  Assert: No 'connection pool exhausted' errors; p99 wait time < 50ms
```

### 10.3 Failure Mode Tests

```
LOAD-FAIL-001: Redis unavailable — BullMQ jobs fail gracefully; HTTP endpoints continue serving
LOAD-FAIL-002: PostgreSQL primary goes down — read replicas serve GET requests; writes queue
LOAD-FAIL-003: Stripe API timeout — webhook processing retries; payment initiation returns 503
```

---

## 11. Coordination with backend-eng

The following interfaces must be finalized before integration tests can be written:

| Test Area | Required from backend-eng |
|-----------|--------------------------|
| Hash chain | `computeHash(record, prevHash)` function signature + field ordering spec |
| Webhook handlers | Fastify route paths + auth middleware for webhook endpoint |
| Advisory lock implementation | PostgreSQL advisory lock key derivation (by stripe_event_id) |
| Append-only rules | DDL for rules/triggers on append-only tables |
| DV safety fields | List of ALL timestamp fields excluded from API responses |
| Fraud thresholds | Exact velocity thresholds (configurable vs hardcoded) |
| Notification queue | BullMQ queue name + job schema for push/email/inbox jobs |

---

## 12. Test Coverage Targets

| Domain | Unit | Integration | E2E |
|--------|------|-------------|-----|
| Hash chain | 100% | 95% | — |
| Webhook handlers | 95% | 100% | — |
| ACH flow | — | 90% | 100% |
| Fraud controls | 90% | 80% | — |
| Co-parent verification | 100% | 95% | — |
| Notifications | 85% | 90% | 80% |
| DB constraints | — | 100% | — |
| DV safety | 85% | 90% | — |
| Load | — | — | See §10 |

---

## Appendix A: Test File Structure

```
src/
  ledger/
    hash-chain.test.ts              # HASH-001 through HASH-007
    verify-chain.test.ts            # VERIFY-001 through VERIFY-008
    merkle-anchor.test.ts           # MERKLE-001 through MERKLE-008
    hash-chain.integration.test.ts  # CHAIN-INT-001 through CHAIN-INT-007 (incl. RACE)
  webhooks/stripe/
    signature.test.ts               # SIG-001 through SIG-005
    idempotency.test.ts             # IDEM-001 through IDEM-005
    payment-intent.test.ts          # PI-CREATED-*, PI-PROC-*, PI-SUC-*, PI-FAIL-*
    dispute.test.ts                 # DISPUTE-001 through DISPUTE-CLS-004
    customer.test.ts                # CUST-UPD-001 through CUST-UPD-003
    account.test.ts                 # ACCT-UPD-001 through DEAUTH-005
    dlq.test.ts                     # DLQ-001 through DLQ-007
  payments/
    ach-flow.e2e.test.ts            # ACH-HAPPY-*, ACH-FAIL-*, REGE-*
  fraud/
    fraud-controls.test.ts          # FRAUD-VEL-*, FRAUD-CROSS-*, FRAUD-IP-*, FRAUD-RET-*, FRAUD-NACHA-*
  pairing/
    verification.test.ts            # VERIFY-PAIR-001 through VERIFY-PAIR-012
  notifications/
    delivery.test.ts                # NOTIF-PUSH-*, NOTIF-EMAIL-*, NOTIF-INBOX-*, NOTIF-SMS-*, NOTIF-INT-*
  db/
    append-only.test.ts             # APPEND-001 through APPEND-013
  safety/
    dv-safety.test.ts               # DV-001 through DV-011
load-tests/
  k6-scenarios.js                   # LOAD-001 through LOAD-FAIL-003
```

---

## Appendix B: Key Risk Areas

1. **Hash chain race conditions** (RESOLVED): Concurrent inserts serialized via `SELECT ... FOR UPDATE` on `hash_chain_heads(table_name, scope_key)` sentinel table. One row per pair acts as mutex. Cross-pair inserts remain fully parallel. CHAIN-INT-006 and LOAD-006 validate correctness under concurrency.

2. **Webhook idempotency under load**: `pg_advisory_xact_lock` (transaction-scoped) + UNIQUE constraint on `stripe_processed_events.stripe_event_id`. Lock auto-releases on rollback — no finally block needed. IDEM-003 validates the race condition with concurrent `Promise.all`.

3. **Reg E timeline compliance**: 10-business-day provisional credit window is legally mandated. `provisional_credit_due_by` calculation must exclude weekends and US federal holidays. REGE-002 must use a date arithmetic library that handles this correctly (e.g., `date-fns` with a holiday calendar).

4. **DV timestamp leakage**: Three leakage vectors: (a) API responses — 11 field names suppressed entirely, 3 truncated to date-only (DV-001), (b) push notification payloads — no amounts/names/timestamps in lock-screen-visible body (NOTIF-PUSH-006/007), (c) email content — no "last seen" language (DV-003). Email `Date:` transport header is acceptable.

5. **Append-only bypass via ORM**: PostgreSQL RULE silently swallows ops and returns success — tests would pass vacuously. Using BEFORE triggers with SQLSTATE 23001 instead. ORM exceptions (APPEND-003/004) are raised by PostgreSQL and propagated through the ORM's error channel.

6. **`advance_payment_status()` exemption**: SECURITY DEFINER function sets `fairbridge.allow_status_update` session variable to bypass trigger for status-only advances. Test APPEND-013 validates both directions: the function succeeds; direct UPDATE still fails.
