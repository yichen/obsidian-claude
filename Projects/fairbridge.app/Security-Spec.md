# FairBridge Security Specification — Section 11: Cross-Cutting Security

**Author**: security-eng
**Date**: 2026-03-17
**Version**: 1.0

---

## 11.1 Authentication & Session Management

FairBridge uses a passwordless, magic-link–based authentication system for V1. This eliminates the risk class of credential stuffing, password reuse attacks, and brute-force login — all of which are elevated concerns given that FairBridge users may include people fleeing abusive relationships who cannot afford a compromised account.

### 11.1.1 Magic Link Flow

```
POST /api/auth/magic-link  { email }
  → Generate cryptographically random token (32 bytes, hex-encoded = 64 chars)
  → Store SHA-256(token) in magic_link_tokens table with:
      - user_id (or null for new users pending registration)
      - expires_at = NOW() + 15 minutes
      - used_at = NULL
      - request_ip
  → Send email via Resend with link: https://app.fairbridge.app/auth/verify?token=<raw_token>
  → Return 200 { message: "Check your email" } — identical response whether email exists or not (prevents user enumeration)

GET /api/auth/verify?token=<raw_token>
  → Compute SHA-256(token), lookup in table
  → Reject if: not found, used_at IS NOT NULL, NOW() > expires_at
  → Mark used_at = NOW() (single-use enforcement)
  → Issue JWT access token + refresh token pair
  → Redirect to /dashboard (existing user) or /onboarding (new user)
```

**Rate limiting on magic link requests**: 3 requests per email per 10 minutes; 10 requests per IP per 10 minutes. Return 429 with `Retry-After` header. Do NOT reveal whether the email exists.

**Token storage**: Only the SHA-256 hash of the token is stored in the database. The raw token exists only in the email and is never logged.

### 11.1.2 Google OAuth (Secondary)

Google OAuth is offered as a secondary login path to reduce friction for users who prefer it.

```
GET /api/auth/google
  → Redirect to Google OAuth consent screen
  → Callback: GET /api/auth/google/callback?code=...
  → Exchange code for Google ID token
  → Verify ID token with Google public keys
  → Extract email from verified token
  → Create or match user by email
  → Issue JWT access token + refresh token pair
```

Google OAuth does NOT bypass 2FA if enabled. After OAuth verification, if TOTP is enrolled, issue intermediate session token and prompt for TOTP code.

### 11.1.3 JWT Token Lifecycle

FairBridge uses a two-token model: short-lived access tokens and long-lived refresh tokens.

| Token | Lifetime | Storage | Signing |
|-------|----------|---------|---------|
| Access token (JWT) | 15 minutes | Memory only (React state / Swift variable) | HMAC-SHA256, secret rotated quarterly |
| Refresh token | 30 days | httpOnly + Secure + SameSite=Strict cookie (web); iOS Keychain / Android Keystore (mobile) | Opaque random (64 bytes hex), stored as SHA-256 hash in DB |

**JWT payload** (access token — keep minimal, never include sensitive fields):
```json
{
  "sub": "<user_uuid>",
  "pair_id": "<coparent_pair_uuid>",
  "role": "payer|payee",
  "jti": "<unique_token_id>",
  "iat": 1742000000,
  "exp": 1742000900
}
```

**Refresh flow**: `POST /api/auth/refresh` with refresh token in httpOnly cookie → validate against DB hash → issue new access token → rotate refresh token (issue new one, revoke old). Sliding-window expiry.

**Access token is never stored on disk** — if the mobile app is killed, the next launch reads the refresh token from Keychain/Keystore and silently obtains a new access token before rendering the first screen.

### 11.1.4 Optional TOTP 2FA

2FA is optional in V1 but available for users who want it. Implementation uses TOTP (RFC 6238) via an authenticator app (Google Authenticator, Authy, 1Password, etc.).

**Why TOTP, not SMS**: SMS 2FA is vulnerable to SIM-swap attacks, SS7 interception, and social engineering of carrier support. For a co-parenting app where one parent may be actively adversarial, SMS 2FA is not acceptable.

**Enrollment flow**:
1. Settings → Security → Enable Two-Factor Authentication
2. Backend generates TOTP secret (20 bytes, base32-encoded): `speakeasy.generateSecret({ length: 20 })`
3. Display QR code + backup codes (8 × 8-digit codes, single-use)
4. User enters a 6-digit code to confirm enrollment before 2FA is activated
5. Store encrypted TOTP secret in DB (pgcrypto `encrypt()` with app-level key)
6. Store hashed backup codes (bcrypt, cost 10)

**2FA at login**: After magic link verification, if 2FA is enabled, issue a short-lived intermediate session token (5 minutes, single-use) and prompt for TOTP code before issuing full session tokens.

**Biometric app lock**: Deferred to V2. V1 uses platform Keystore biometric for token access only (not as a full app lock gate).

### 11.1.5 Session Revocation

Sessions must be revoked immediately on sensitive operations — not waiting for token expiry.

| Trigger | Action |
|---------|--------|
| User changes linked bank account | Revoke all sessions except current; require re-auth on other devices |
| User triggers silent deactivation | Revoke ALL sessions immediately; clear all push tokens |
| Admin suspends account | Revoke ALL sessions; add user_id to JWT blocklist in Redis (TTL = max remaining token lifetime) |
| User logs out | Revoke current refresh token |
| Suspicious login detected (new IP + new device in rapid succession) | Flag for review; optionally trigger forced re-auth |

**JWT blocklist**: Access tokens are stateless JWTs, so revocation requires a Redis blocklist. Key: `blocklist:jti:<jti>`, TTL = remaining token lifetime. On every authenticated request, check Redis before processing. Cost is a single Redis GET per request — acceptable.

---

## 11.2 Authorization & Data Isolation

### 11.2.1 Role Model

FairBridge has three roles:

| Role | Who | Capabilities |
|------|-----|-------------|
| `payer` | Parent who initiates ACH payments | Initiate payments, submit expenses, manage bank account, view own pair's data |
| `payee` | Parent who receives payments | Approve/decline expenses, manage bank account (Stripe Connect), view own pair's data |
| `admin` | FairBridge internal | Read-only audit access, dispute resolution, account suspension. Cannot initiate payments or impersonate users. |

Both payer and payee can submit expenses. The "payer" role means they are the ACH debit source for the pair's payment schedule.

### 11.2.2 Co-Parent Pair Isolation

**This is the most critical authorization control.** Every user belongs to exactly one co-parent pair (V1). Every API query that touches financial data MUST be scoped to the authenticated user's `pair_id`.

**Enforcement pattern** (Fastify middleware):

```typescript
async function pairScopeGuard(req: FastifyRequest, reply: FastifyReply) {
  const userId = req.user.id;
  const { pair_id } = req.params as any;

  if (pair_id) {
    const membership = await db.query(
      `SELECT id FROM coparent_pairs
       WHERE id = $1 AND (parent_a_id = $2 OR parent_b_id = $2)`,
      [pair_id, userId]
    );
    if (membership.rows.length === 0) {
      return reply.status(403).send({ error: 'Forbidden' });
    }
  }

  req.pairId = req.user.pair_id; // from JWT claim
}
```

Every SELECT on `payments`, `expenses`, `disputes`, `calendar_events`, `children`, `expense_events`, `payment_events` MUST include `WHERE pair_id = $<pair_id>`.

**IDOR prevention**: Resource IDs are globally unique UUIDs but the pair_id check ensures a user cannot access another pair's resource even if they guess the UUID.

### 11.2.3 PostgreSQL Row-Level Security (RLS)

RLS is a defense-in-depth measure. Even if application code has a bug that omits the `pair_id` filter, RLS prevents cross-pair data leakage.

```sql
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE disputes ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE expense_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY pair_isolation ON payments
  USING (pair_id = (
    SELECT id FROM coparent_pairs
    WHERE (parent_a_id = current_setting('app.current_user_id')::uuid
       OR parent_b_id = current_setting('app.current_user_id')::uuid)
      AND id = payments.pair_id
    LIMIT 1
  ));

-- Admin DB user has BYPASSRLS. Application DB user does NOT.
```

**Connection setup**: At the start of every DB transaction:
```sql
SET LOCAL app.current_user_id = '<uuid>';
```

### 11.2.4 API Endpoint Authorization Matrix

| Endpoint | payer | payee | admin | Notes |
|----------|-------|-------|-------|-------|
| `POST /api/payments` | ✓ | ✗ | ✗ | Only payer initiates ACH |
| `POST /api/payments/manual` | ✓ | ✗ | ✗ | Ad-hoc payment |
| `GET /api/payments` | ✓ | ✓ | ✓ (audit) | Scoped to own pair |
| `POST /api/expenses` | ✓ | ✓ | ✗ | Both parents submit |
| `POST /api/expenses/:id/approve` | ✓ | ✓ | ✗ | Only the non-submitter |
| `POST /api/expenses/:id/decline` | ✓ | ✓ | ✗ | Only the non-submitter |
| `POST /api/disputes` | ✓ | ✓ | ✗ | Either parent can file |
| `GET /api/schedule` | ✓ | ✓ | ✓ (audit) | Scoped to pair |
| `PUT /api/schedule` | ✓ | ✓ | ✗ | Requires both parents to confirm |
| `POST /api/stripe/connect/account` | ✗ | ✓ | ✗ | Payee Connect account only |
| `GET /api/stripe/subscription/status` | ✓ | ✗ | ✓ | Payer pays subscription |
| `POST /api/account/deactivate` | ✓ | ✓ | ✓ | Silent — never notifies co-parent |
| `GET /api/account/export` | ✓ | ✓ | ✗ | Own data only |
| `GET /api/reports/verify` | public | public | public | Hash verification, no auth |
| `POST /admin/suspend` | ✗ | ✗ | ✓ | Admin only |
| `POST /webhooks/stripe` | — | — | — | Stripe signature auth only |

---

## 11.3 DV Safety — System-Wide

**Domestic violence safety is the highest-priority non-functional requirement.** FairBridge users may be in situations where an abusive co-parent has physical access to their device, monitors their financial activity, or uses the app as a surveillance vector. Every feature must be designed with the assumption that the co-parent is a potential adversary.

### 11.3.1 Core DV Safety Requirements (V1 Non-Negotiable)

**R1 — No activity timestamp exposure**: The API must never expose `last_active`, `last_login`, `last_seen`, `last_opened`, or any field that reveals when the co-parent was active.

**R2 — Generic push notification payloads**: Push notification `title` and `body` fields must contain NO financial amounts, NO names, NO expense details, NO child names. Only generic action prompts are permitted on the lock screen.

**R3 — Silent deactivation**: Account deactivation must complete without sending any notification, email, or signal to the co-parent. Co-parent's app shows generic "unavailable" states.

**R4 — Data export before deletion**: Full GDPR-style data export (JSON + receipt images as ZIP) available before account deletion. Export delivered via email only (never push).

**R5 — Safety resources always accessible**: National DV Hotline (1-800-799-7233) and thehotline.org link in Settings → Safety Resources. Directly accessible, not buried in a help section.

**R6 — No read receipts, no online indicators**: Co-parent must never know whether their counterpart has read a notification or opened the app.

**R7 — Quick exit**: Safety exit button (web: fixed top-right; mobile: triple-tap or shake) redirects to weather.com, replacing history to prevent back-navigation.

**R8 — IP address hashing**: IP addresses stored as SHA-256 hash only, never raw. Geolocation data TTL: 24 hours maximum.

**R9 — Jailbreak/root detection**: Warning only, never blocking. DV users may legitimately use modified devices for safety apps.

### 11.3.2 Mandatory Push Notification Payload Standard

ALL push notifications from FairBridge MUST conform to this standard:

```json
{
  "aps": {
    "alert": {
      "title": "FairBridge",
      "body": "<generic_action_text>"
    },
    "sound": "default",
    "interruption-level": "active|time-sensitive",
    "badge": 1
  },
  "fairbridge_type": "<event_type>",
  "entity_id": "<uuid>"
}
```

**Permitted `body` strings** (exhaustive — no others allowed):

| Event | Body |
|-------|------|
| Expense pending review | "An expense is waiting for your review" |
| Expense approved | "An expense has been approved" |
| Expense declined | "An expense has been declined" |
| Payment processing | "A payment is being processed" |
| Payment succeeded | "A payment has been completed" |
| Payment failed | "A payment requires your attention" |
| Dispute opened | "A payment dispute needs your response" |
| Calendar update | "Your custody schedule has been updated" |
| General | "You have a new update in FairBridge" |

**Never permitted in push payloads**: dollar amounts, child names, co-parent names, expense categories, dates, account numbers, last-4 digits, or any identifying information.

Entity details (IDs, amounts, names) go only in the `data`/custom payload keys — readable by the app after unlock, invisible on the lock screen.

### 11.3.3 Silent Deactivation Flow

```
POST /api/account/deactivate  { reason?: string }

  Backend actions (all silent — no co-parent notification):
  1. Set users.deactivated_at = NOW()
  2. Revoke all active sessions (user_sessions.revoked_at = NOW())
  3. Delete all push tokens (push_tokens.revoked_at = NOW())
  4. Enqueue data export job (delivers ZIP via email only)
  5. Schedule hard delete: 30 days from now
  6. Return 200 { message: "Account deactivated" }

  Co-parent API behavior after deactivation:
  - GET /api/expenses → pending items show status "undeliverable"
  - POST /api/payments → 402 "Payee account unavailable" (generic)
  - No webhook, no email, no push to co-parent
  - 404 semantics for co-parent queries (no account existence signal)
```

**Data retention**:
- Days 0-30: Deactivated but data retained (user can reactivate)
- Day 30: Hard delete of all PII (name, email, phone, bank details)
- Financial records: anonymized and retained 6 years (Nacha/BSA)
- Receipt images: deleted from Cloudflare R2 at Day 30

---

## 11.4 Encryption

### 11.4.1 Encryption at Rest

**PostgreSQL column-level encryption** for PII using `pgcrypto`:

| Column | Table | Method |
|--------|-------|--------|
| `email` | `users` | AES-256-CBC via `pgp_sym_encrypt()` |
| `phone` | `users` | AES-256-CBC via `pgp_sym_encrypt()` |
| `display_name` | `users` | AES-256-CBC via `pgp_sym_encrypt()` |
| `stripe_customer_id` | `users` | AES-256-CBC via `pgp_sym_encrypt()` |
| `stripe_connect_account_id` | `users` | AES-256-CBC via `pgp_sym_encrypt()` |
| TOTP secret | `user_2fa` | AES-256-CBC via `pgp_sym_encrypt()` |
| `ip_address` | `user_sessions` | SHA-256 hash (one-way, not encrypted) |
| `user_agent` | `user_sessions` | AES-256-CBC |

**Key management**:
- Application-level encryption key stored in environment secret manager (Fly.io secrets), never in code or DB
- Annual key rotation with dual-key transition period
- Email lookups use a separate `email_hash` column (SHA-256 of normalized email) — encrypted columns cannot be indexed

**Cloudflare R2 receipt images**: AES-256 server-side encryption (R2 default). Access via signed URLs (15-minute expiry for downloads, 1-hour for court reports).

### 11.4.2 Encryption in Transit

- **TLS 1.3 minimum** on all endpoints. TLS 1.2 rejected. TLS 1.0/1.1 disabled.
- **HSTS**: `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- Submit `api.fairbridge.app` and `app.fairbridge.app` to HSTS preload list before launch
- Let's Encrypt or Cloudflare-managed TLS with auto-renewal
- TLS 1.3 enforces Perfect Forward Secrecy (mandatory ECDHE)

### 11.4.3 Stripe Token Handling

FairBridge never stores raw bank account numbers, routing numbers, or card numbers.

| What we store | What we never store |
|--------------|---------------------|
| `stripe_customer_id` (cus_...) | Raw card numbers |
| `stripe_connect_account_id` (acct_...) | Bank account numbers |
| `stripe_payment_method_id` (pm_...) | Routing numbers |
| `stripe_financial_connection_id` (fca_...) | CVV / SSN / EIN |
| Payment Intent ID (pi_...) | Full account details |

Stripe Financial Connections returns only `last4` and `institution_name` to FairBridge. All financial data remains within Stripe's PCI-DSS scope.

---

## 11.5 OWASP Top 10 Compliance

### A01 — Broken Access Control
- JWT `pair_id` claim scopes every query (Section 11.2.2)
- PostgreSQL RLS as defense-in-depth (Section 11.2.3)
- Admin endpoints require `admin` role — not derivable from normal user JWT
- Application DB user: no SUPERUSER, no BYPASSRLS, no DDL in production

### A02 — Cryptographic Failures
- TLS 1.3 minimum, HSTS preloading (Section 11.4.2)
- Column-level encryption for PII (Section 11.4.1)
- Tokens stored as SHA-256 hashes only — never raw in DB
- No weak algorithms: no MD5, SHA-1, DES, RC4

### A03 — Injection
- All queries use parameterized statements — no string concatenation in SQL
- Zod schema validation on ALL API request bodies; unknown fields stripped
- File uploads: MIME type validated via magic bytes (not Content-Type header). Accepted: `image/jpeg`, `image/png`, `image/webp`, `application/pdf`. 10MB limit enforced at Cloudflare WAF before the application
- No `eval()`, no `Function()` constructor, no dynamic code execution

### A04 — Insecure Design
- Threat model: co-parent treated as potential adversary
- DV safety requirements are design-level constraints (Section 11.3)
- Append-only data model prevents retroactive tampering
- Hash chain + Merkle anchors ensure tamper evidence

### A05 — Security Misconfiguration
- `NODE_ENV=production` enforced — no stack traces in error responses
- No debug endpoints (`/debug`, `/__dev__`) in production
- Fastify `trustProxy` scoped to Cloudflare IP ranges only
- CORS allows only `app.fairbridge.app` and `fairbridge.app`
- Error responses use codes, not raw DB errors or Stripe messages
- Stripe webhook endpoint uses signature auth only — not behind JWT middleware

### A06 — Vulnerable & Outdated Components
- Dependabot/Renovate for automated dependency PRs
- `npm audit --audit-level=high` in CI — fails build on high/critical findings
- Security-critical dependencies pinned to exact versions in `package-lock.json`
- Docker base images pinned by digest hash, not mutable tags

### A07 — Identification & Authentication Failures
- Magic link tokens: 32 bytes entropy, 15-minute expiry, single-use
- Rate limiting on auth endpoints (Section 11.6.1)
- Refresh token rotation on every use — detects token theft
- Session revocation on sensitive actions (Section 11.1.5)
- Optional TOTP 2FA (Section 11.1.4)
- Identical response whether email exists or not (no user enumeration)

### A08 — Software & Data Integrity Failures
- SHA-256 hash chain on all financial records
- Daily Merkle root anchors published to append-only external log
- Court export PDFs include SHA-256 content hash; public verification endpoint
- Stripe webhook signature verification prevents forged events (Section 11.6.3)
- CSP headers prevent unauthorized script injection

### A09 — Security Logging & Monitoring Failures
- Auth events logged: magic link request/verification, token refresh, 2FA, session revocation
- Payment state transitions logged to `payment_events` with hash chain
- Fraud signals logged to `fraud_signals` table
- **PII excluded from logs**: Pino `redact` config strips `email`, `phone`, `display_name`, `stripe_*_id`, `ip_address`
- **No financial data in error messages**: error codes only (`PAYMENT_FAILED`, not raw Stripe messages)
- Alert: Nacha return rate >0.3% → automated ops alert

### A10 — Server-Side Request Forgery (SSRF)
- No user-supplied URLs fetched by backend
- Receipt images uploaded client-to-R2 via presigned URLs (not through the backend)
- Stripe `redirect_uri` validated against FairBridge domain allowlist
- Application servers have no internal network access — external calls allowlisted to Stripe, Resend, FCM, APNs only

---

## 11.6 API Security

### 11.6.1 Rate Limiting

Two-tier enforcement: Cloudflare WAF (IP-based) + Fastify rate-limit plugin (user-based).

| Endpoint Group | Limit | Window | Scope |
|----------------|-------|--------|-------|
| `POST /api/auth/magic-link` | 3 requests | 10 min | Per email |
| `POST /api/auth/magic-link` | 10 requests | 10 min | Per IP |
| `GET /api/auth/verify` | 10 requests | 10 min | Per IP |
| `POST /api/auth/refresh` | 20 requests | 1 min | Per user |
| Payment initiation | 10 requests | 1 min | Per user |
| Expense submission | 20 requests | 1 min | Per user |
| File upload | 10 requests | 1 min | Per user |
| General authenticated | 100 requests | 1 min | Per user |
| `GET /api/reports/verify` (public) | 30 requests | 1 min | Per IP |

### 11.6.2 Input Validation

Fastify JSON Schema validation via `fastify-type-provider-zod`. Zod schema is the single source of truth shared between frontend and backend.

**Financial input rules**:
- `amount_cents`: integer, > 500 (minimum $5.00), ≤ 5,000,000 (max $50,000)
- `memo`: string, max 500 characters, HTML-stripped server-side
- `description`: string, min 3, max 200 characters, HTML-stripped
- `email`: RFC 5322-compliant regex + DNS MX lookup on registration
- UUID fields: UUID v4 format validated before DB lookup

`additionalProperties: false` on all schemas — unknown fields return 400.

### 11.6.3 Stripe Webhook Security

```typescript
async function handleStripeWebhook(req: FastifyRequest, reply: FastifyReply) {
  const sig = req.headers['stripe-signature'];
  if (!sig) return reply.status(400).send({ error: 'Missing stripe-signature header' });

  let event: Stripe.Event;
  try {
    // constructEvent uses timing-safe comparison internally
    event = stripe.webhooks.constructEvent(
      req.rawBody,  // MUST be raw Buffer, not parsed JSON
      sig,
      process.env.STRIPE_WEBHOOK_SECRET
    );
  } catch (err) {
    logger.warn({ sig }, 'Invalid Stripe webhook signature');
    return reply.status(400).send({ error: 'Invalid signature' });
    // Return 400 (not 500) — 500 would cause Stripe to retry
  }
  // ... idempotency check and processing
}
```

`req.rawBody` must be the raw Buffer — Fastify must preserve the raw body for this route only via a custom content-type parser.

**Secret rotation**: add new secret in Stripe dashboard → deploy dual-secret validation → verify → remove old.

### 11.6.4 CORS Policy

```typescript
fastify.register(cors, {
  origin: process.env.NODE_ENV === 'production'
    ? ['https://app.fairbridge.app', 'https://fairbridge.app']
    : ['http://localhost:3000', 'http://localhost:5173'],
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-CSRF-Token'],
  credentials: true,
  maxAge: 86400,
});
```

### 11.6.5 CSRF Protection

Double-Submit Cookie pattern + SameSite=Strict (web only; mobile apps are not CSRF-vulnerable).

- Refresh token cookie: `SameSite=Strict; HttpOnly; Secure; Path=/api/auth`
- CSRF token: 32-byte random in non-HttpOnly cookie `fairbridge_csrf`
- Client sends token in `X-CSRF-Token` header on all POST/PUT/DELETE
- Server validates header matches cookie value

---

## 11.7 Mobile Security

### 11.7.1 iOS Keychain

| Item | Key | Access Class | iCloud Sync |
|------|-----|-------------|------------|
| Access JWT | `fb_access_token` | `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` | No |
| Refresh token | `fb_refresh_token` | `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` | No |
| TOTP secret | `fb_totp_secret` | `kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly` | No |

`ThisDeviceOnly` prevents iCloud Keychain sync — tokens lost on device restore (re-auth required, acceptable).

**DV safety**: Silent deactivation clears all Keychain items with no UI prompt or dialog.

### 11.7.2 Android Keystore

```typescript
Keychain.setGenericPassword(key, value, {
  service: `com.fairbridge.${key}`,
  accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  securityLevel: Keychain.SECURITY_LEVEL.SECURE_HARDWARE,
  storage: Keychain.STORAGE_TYPE.RSA,
});
```

`allowBackup="false"` + `fullBackupContent="false"` in AndroidManifest.xml — no Google Drive backup of financial data.

Fallback: EncryptedSharedPreferences (AES-256-GCM) on API 24-27 devices without hardware Keystore.

### 11.7.3 Screen Protection

**Android** (`FLAG_SECURE`): Prevents screenshots, screen recording, and recents thumbnail on all financial screens. Exempt: login, custody calendar (no financial data), safety resources.

**iOS** (BlurView overlay): `AppState 'inactive'` fires before iOS takes the app-switcher screenshot. BlurView intensity=100 covers all content, shows FairBridge logo only. ON by default; user can disable in Settings → Privacy.

**Both platforms**: Crash reports configured to exclude financial data, email, and payment identifiers. Use `beforeSend` filter in Sentry/Crashlytics to scrub PII before transmission.

### 11.7.4 Certificate Pinning

`react-native-ssl-pinning` pins `api.fairbridge.app`. Prevents MITM on financial data even on networks with compromised CAs.

- Pin to intermediate CA certificate (not leaf) — survives leaf rotation without forced app update
- New certificate hash must ship in app update ≥30 days before old cert expires

**Jailbreak/root detection**: Warning only, never blocking. DV users may legitimately use modified devices for safety apps. Blocking would harm the people most in need of this app.

### 11.7.5 Notification Channel Security (Android)

- `payments` and `expenses` channels: `VISIBILITY_PRIVATE` — lock screen shows "FairBridge" only, never content
- `calendar` channel: `VISIBILITY_PUBLIC` — custody reminders contain no financial data
- High-priority FCM (`priority: "HIGH"`) for payment and expense notifications — ensures delivery through Doze mode

---

## 11.8 Regulatory Compliance Matrix

### 11.8.1 Regulation E (12 CFR Part 1005)

| Requirement | Implementation |
|-------------|---------------|
| ACH authorization disclosure | Displayed during payment schedule setup; `authorization_text` hash stored |
| Error resolution | 60-day dispute window; `POST /api/disputes`; provisional credit within 10 business days |
| Provisional credit | Issued from $5-10K reserve fund during investigation |
| Investigation timeline | 10 business days standard; 20 business days with provisional credit if needed |
| Written confirmation | Email within 3 business days of dispute receipt |
| Resolution notification | Email on close (won/lost) with reason |
| Return rate target | <0.5% unauthorized; velocity monitoring alerts at 0.3% |
| Record retention | 6 years |

### 11.8.2 Nacha Operating Rules

| Rule | Implementation |
|------|---------------|
| ACH authorization | Explicit consumer authorization for each debit; recurring for scheduled payments |
| Return rate monitoring | <0.5% unauthorized (fraud controls in Backend-Spec Section 10) |
| Bank verification | Stripe Financial Connections instant verification preferred; micro-deposit fallback |
| Company name on statement | "FairBridge" — not individual parent names |
| SEC code | `WEB` (internet-initiated consumer debit) |
| Ramp-up limits | $2,500/week first 6 payments; $5,000/week thereafter (internal fraud control — NOT exposed to users) |

### 11.8.3 CCPA/CPRA

| Right | Implementation |
|-------|---------------|
| Right to Know | `GET /api/account/export` — full JSON + receipts ZIP |
| Right to Delete | `POST /api/account/deactivate` → 30-day grace → hard delete |
| Right to Correct | Profile update endpoints; financial records corrected only via dispute process (append-only constraint) |
| Right to Opt Out of Sale | FairBridge does not sell data; stated explicitly in privacy policy |
| Sensitive PI | Financial data + children's data subject to enhanced protections |
| Data minimization | Name, email, phone (optional), Stripe last4 only |
| Privacy policy | Required before account creation; version-tracked; re-consent on material changes |

### 11.8.4 Children's Data

| Principle | Implementation |
|-----------|---------------|
| Data minimization | First name + last name hash for matching; birth year only (not full DOB) |
| No cross-parent exposure | Child's full name/DOB never returned by API after matching; only `display_name` (first name + last initial) |
| Hash-based matching | SHA-256 of normalized name + DOB — raw data never compared across parents |
| Deletion | Child records deleted at Day 30 of account deactivation |
| COPPA | FairBridge serves adults only; children are referenced data subjects, not users |

### 11.8.5 Record Retention Schedule

| Data Type | Retention | Basis |
|-----------|-----------|-------|
| Payment records (ledger) | 6 years from transaction | Nacha + BSA |
| Dispute records | 6 years from resolution | Nacha + Reg E |
| Stripe webhook events | 3 years | Internal audit |
| User PII (name, email, phone) | 30 days post-deactivation → hard delete | CCPA + data minimization |
| Receipt images | 30 days post-deactivation → deleted from R2 | No regulatory requirement |
| Auth logs | 1 year | Security audit |
| Fraud signals | 3 years | AML/BSA |
| Court export reports | 6 years (hash retained; PDF on request) | Potential litigation hold |

Whichever retention period is longest governs conflicting obligations. The 6-year Nacha/BSA period takes precedence for financial records.

### 11.8.6 AML/BSA Considerations

FairBridge is not a Money Services Business — Stripe is the licensed entity and handles primary KYC/AML obligations. FairBridge implements supporting controls:

- Velocity monitoring flags unusual patterns to `fraud_signals` table for human review
- All users must verify identity via Stripe (Stripe KYC covers FairBridge's obligation)
- SAR escalation: manual process for MVP when fraud signals indicate potential money laundering
- Stripe maintains primary BSA records; FairBridge retains payment metadata for 6 years

---

## 11.9 Infrastructure & Deployment Security

### 11.9.1 Environment Separation

| Environment | Database | Stripe Keys | Config |
|-------------|----------|-------------|--------|
| Development | Local PostgreSQL | Test keys | `.env.local` (gitignored) |
| Staging | Fly.io PostgreSQL (dedicated) | Test keys | Fly.io secrets |
| Production | Fly.io PostgreSQL (dedicated, encrypted at rest) | Live keys | Fly.io secrets |

Production and staging never share databases. Staging uses Stripe test keys — no real money movement.

### 11.9.2 Secret Management

- All secrets (Stripe keys, SMTP credentials, encryption keys, JWT signing secret) in Fly.io secrets or equivalent secret manager — never in code or committed files
- `.env` in `.gitignore`; `dotenv-safe` enforces all required variables defined in `.env.example`
- Rotation schedule: JWT signing secret quarterly; PII encryption key annually with dual-key transition

### 11.9.3 CI/CD Security

- All CI in isolated ephemeral containers — no persistent state between runs
- `npm audit --audit-level=high` on every PR — fails build on high/critical vulnerabilities
- SAST (CodeQL or Semgrep) on every PR — fails build on security findings
- Docker images built from pinned digest hashes (not mutable tags like `node:20-alpine`)
- Production deployments require approval from a second engineer (not the PR author)
- Stripe test keys in CI/CD; live keys only in production secrets

### 11.9.4 Monitoring & Incident Response

**Alert thresholds**:
- Auth failure spike → PagerDuty alert within 2 minutes
- Nacha return rate >0.3% → automated ops alert
- Fraud signal severity=critical → immediate alert + automatic payment suspension for affected pair

**Incident response**:
1. Isolate → assess blast radius
2. Contain → revoke sessions, disable affected endpoints if needed
3. Remediate → fix root cause, deploy patch
4. Post-mortem → within 72 hours of resolution

**Breach notification**:
- CCPA/CPRA: notify affected users within 72 hours if PII is involved
- Stripe: notify immediately if Stripe credentials or webhook secrets are compromised
- Nacha: report if unauthorized ACH transactions are detected beyond normal dispute handling

---

## Appendix D: DV Safety Checklist (Pre-Release Gate)

The following must be verified before each release. All items are blocking.

- [ ] No `last_active`, `last_login`, `last_seen` in any API response accessible to co-parent
- [ ] All push notification payloads conform to the permitted-body-strings list (Section 11.3.2)
- [ ] Silent deactivation: co-parent receives no notification, email, or error revealing deactivation
- [ ] Data export available and complete: ZIP contains all user data including receipts
- [ ] Safety exit button on every web page; keyboard shortcut (Escape × 3) functional
- [ ] National DV Hotline (1-800-799-7233) visible in Settings → Safety Resources
- [ ] App switcher masking active by default on iOS (BlurView on `AppState 'inactive'`)
- [ ] FLAG_SECURE active on all financial screens on Android
- [ ] `VISIBILITY_PRIVATE` on payment and expense notification channels on Android
- [ ] Crash reports scrubbed: no PII or financial data in Sentry/Crashlytics breadcrumbs
- [ ] `allowBackup="false"` confirmed in Android manifest
- [ ] Keychain/Keystore items configured `ThisDeviceOnly` — not synced to iCloud or Google Drive
- [ ] Co-parent's email, phone, and address never appear in any UI view
- [ ] IP addresses stored as SHA-256 hash only — no raw IP in any user-facing response
- [ ] Jailbreak/root detection: warning only, never blocks app access

---

## Appendix E: DV Safety Audit Findings

Audit conducted 2026-03-17 across: Backend-Spec.md, Web-Frontend-Spec.md, UX-Flows-Spec.md, iOS-Spec.md, Android-Spec.md, Backend-Test-Spec.md.

### Violations Found

**DV-001 — CRITICAL | iOS-Spec.md Section 3.2 lines 80-81**
APNs payload example exposes child name and dollar amount in visible alert body:
`"body": "Ruby's soccer registration ($185) — tap to review"`
Appears on iOS lock screen, Apple Watch, notification center without device unlock.
Fix: `"title": "FairBridge", "body": "An expense needs your review"` — entity details in `data` payload only.
Owner: ios-dev

**DV-002 — CRITICAL | iOS-Spec.md Section 3.2 lines 96-97**
Standard payment notification exposes dollar amount and co-parent first name:
`"body": "$185 sent to Sarah"`
Fix: `"title": "FairBridge", "body": "Payment update — tap to view"`
Owner: ios-dev

**DV-003 — HIGH | UX-Flows-Spec.md line 516**
Notification copy spec directs: "[Payee name] added an expense: $[X] for [category]. Review it."
Same lock-screen exposure risk as DV-001/002.
Fix: "A new expense has been submitted. Tap to review."
Owner: ux-engineer

**DV-004 — MEDIUM | UX-Flows-Spec.md line 865**
DV safety guidance states notifications "show amounts only, not sender name" — amounts are also a violation.
Fix: "Push notification body must contain NO financial amounts, NO names, NO categories."
Owner: ux-engineer

**DV-005 — LOW | Backend-Spec.md push_tokens table**
`last_used_at TIMESTAMPTZ` column could reveal approximate app usage timing if surfaced in any admin or user-facing view.
Fix: Add to API response exclusion list; document as internal-only.
Owner: backend-eng

### Compliant Items Verified

| Item | File | Status |
|------|------|--------|
| `VISIBILITY_PRIVATE` on notification channels | Android-Spec.md | COMPLIANT |
| `allowBackup="false"` | Android-Spec.md | COMPLIANT |
| App switcher BlurView masking | iOS-Spec.md | COMPLIANT |
| `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` | iOS-Spec.md | COMPLIANT |
| Safety exit button with `history.replace` | Web-Frontend-Spec.md | COMPLIANT |
| No "last seen" indicators | Web-Frontend-Spec.md | COMPLIANT |
| No read receipts | Web-Frontend-Spec.md | COMPLIANT |
| Opaque tokens in invite links | Web-Frontend-Spec.md | COMPLIANT |
| Silent deactivation — co-parent not notified | Backend-Spec.md | COMPLIANT |
| Child verification via SHA-256 hashing | Backend-Spec.md | COMPLIANT |
| Deactivation UX copy — co-parent not notified | UX-Flows-Spec.md | COMPLIANT |
| No `last_login`/`last_active` in API responses | Backend-Test-Spec.md (DV-001) | COMPLIANT |

---

*End of Security Specification — Section 11*
*Author: security-eng | Date: 2026-03-17 | Version: 1.0*
