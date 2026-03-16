# FairBridge.app — 7-Expert Spec Review Panel Report

**Date**: 2026-03-16
**Spec Reviewed**: `initial_spec.md` (draft, post-OFW-relaxation pass)
**Process**: 7 domain experts reviewed independently, then debated in real-time

---

## Panel Members

| Role | Focus Area |
|------|-----------|
| **Web App Developer** | Stripe Connect, ACH flows, DB architecture, webhooks |
| **iOS Developer** | App Store guidelines, push notifications, biometrics, camera |
| **Android Developer** | Google Play policy, notification reliability, device fragmentation |
| **High-Conflict Divorce Lawyer** | Abuse vectors, court admissibility, DV protocols |
| **Financial Regulator** | MTL classification, Reg E, Nacha, CFPB |
| **AML/BSA Lawyer** | Money laundering vectors, FinCEN, SAR obligations |
| **Angel Investor** | MVP scope, time-to-market, funding readiness |

---

## Consensus Decision: ACH in V2, Not V1

**Vote: 5-2 in favor of deferring ACH payments to V2.**

| V2 (defer ACH) | V1 (ship ACH) |
|-----------------|----------------|
| Investor | Divorce Lawyer (with preconditions) |
| Web Dev | iOS Dev (gated behind onboarding) |
| Android Dev | |
| Financial Regulator | |
| AML Lawyer | |

**Rationale**: Cutting ACH from V1 eliminates 4 of 8 regulatory findings (MTL, Reg E, Nacha TPS, OFAC/transaction monitoring), removes $20-50K/year compliance overhead, and reduces build time from 12-18 months to 3-4 months. The residual V1 compliance cost (CCPA + subpoena process) is trivial.

**V1 scope (consensus)**:
- Expense logging + two-party confirmation (R2.1-R2.2)
- External payment tracking with two-party confirmation (R2.3)
- Basic custody calendar — must be genuinely useful, not a placeholder (R5.1)
- Free tier + paid court-formatted PDF export (R7)
- Append-only data model from day one (schema designed for ACH addition in V2)

**V2 scope** (after 500+ active pairs):
- ACH payments via Stripe Connect
- Nacha TPS registration + AML program
- Professional accounts (R8.2)
- Plaid bank feed (R2.4)
- AI receipt verification (R4.2)

**Critical V2 caveat (aml-lawyer + web-dev)**: Collect child profile data and leave KYC schema slots in the V1 data model so V2 AML activation is additive, not a rewrite.

---

## Top Priority Fixes — Unanimous or Near-Unanimous

### 1. Add R9: Notification Architecture (all 3 developers)

The spec says "payee receives notification" as if delivery is guaranteed. It is not.

**The problem**:
- iOS: Focus mode blocks notifications; users can deny permission entirely; no Critical Alerts entitlement for financial apps
- Android: ~35-40% of devices (Samsung/Xiaomi/Oppo) aggressively kill FCM delivery even for high-priority messages
- Combined: the core two-party confirmation workflow silently fails for a significant portion of users

**Required spec additions**:
- Three-layer delivery: FCM/APNs push (primary) → email (15-minute fallback) → SMS (highest-stakes events only)
- In-app notification inbox as guaranteed fallback (badge + banner on app open)
- Mandatory notification permission gate during onboarding — before pairing is possible
- Android-specific: battery optimization exemption prompt during onboarding
- Server-side delivery tracking + reminder schedule for pending expenses
- WebSocket/SSE for real-time foreground updates only (not reliable for background)

### 2. DV/Safety Protocols — Non-Negotiable for V1 (investor + divorce-lawyer consensus)

These are not features — they are implementation defaults with a safe or unsafe behavior either way. Getting them wrong costs 3 days to fix but creates negligence exposure.

**Required V1 defaults**:
- No cross-parent activity timestamps (never show "last active" to the other parent)
- No sensitive content in push notification payloads (show "New activity in FairBridge" not "Parent A submitted $500 expense")
- Silent account deactivation without alerting the co-parent
- Full data export + deletion on account close
- Safety resources link (DV hotline) in app settings
- Screen content masking in app switcher (iOS + Android `FLAG_SECURE`)

**V2 additions**: DVPO-aware notification suspension, emergency account freeze, confidential safety exit flow.

### 3. Professional Account Data Boundaries — R8.2 (divorce-lawyer, supported by fin-regulator)

**Current spec**: "Either parent can connect a professional; the other parent is notified."

**The problem**: As written, Parent A can unilaterally expose Parent B's complete financial history to opposing counsel with nothing more than a notification. "Notification is not consent" under CCPA (fin-regulator's framing).

**Required fix**: Professionals see only:
- Records submitted or confirmed by the connecting parent
- Mutually confirmed shared records (approved expenses, confirmed payments)
- NOT: the other parent's private account details, dispute reasoning, private notes, bank account info

The non-connecting parent must affirmatively consent to broader access. This can be deferred to V2 if professional accounts are cut from V1 (investor recommends cutting).

### 4. Expense Submission Rate Limits (divorce-lawyer, supported by all)

**The attack**: Parent A submits 100 expenses at $5.01 each in one day — 100 notifications, 100 items requiring individual review. This is documented coercive control behavior.

**Required fix**: Soft daily limit (10-15/day) with admin override for legitimate bulk submissions (e.g., medical bills). Android-dev noted that FCM collapse keys + notification channel priority levels can mitigate harassment amplification at the OS level, so the limit can be a soft limit rather than a hard architectural constraint.

---

## Critical Findings by Domain

### Regulatory (fin-regulator + aml-lawyer — 18 combined findings)

**If/when ACH is added (V2), these become mandatory:**

1. **"Stripe handles AML" is factually wrong** — FairBridge has independent BSA/AML obligations if classified as an MSB. Cannot delegate to Stripe. Must build: AML Policy, BSA Officer, SAR filing workflow, OFAC screening, transaction monitoring.

2. **Multi-state MTL opinion required** — "Stripe's licenses cover us" is a business decision presented as a legal conclusion. Must commission state-specific analysis for top 10 states (NY, CA, TX, FL, IL at minimum) before enabling ACH.

3. **Reg E vs. Stripe finality conflict** — R1.3 says "ACH disputes are FINAL on Stripe" but R1.5 requires honoring Reg E consumer dispute rights. These conflict. FairBridge must eat losses on Reg E disputes that Stripe finalizes. Needs: reserve fund, consumer-facing dispute intake channel, provisional credit process within 10 business days.

4. **Fake co-parent laundering vector** — Two criminals can pair as fake co-parents, submit fabricated expenses, and move $260K/year through the platform. Mitigation: independent child name/birth year entry by both parents at onboarding (asymmetric friction — costs real parents nothing, adds wire fraud exposure for criminals).

5. **$5K/week limit is a structuring beacon** — Don't publish specific transaction limits in marketing materials. Implement as internal risk controls with range disclosures only.

6. **Marketing language creates regulatory exposure** — "Track your child support" in marketing + "expense reimbursement only" in legal filings = evidence of bad faith. Technical enforcement needed: detect and flag recurring payment patterns matching support amounts.

7. **1099-K tax problem** (web-dev discovery) — Stripe Express accounts may issue 1099-Ks to payee parents, misclassifying reimbursements as income. Needs disclosure in R1.1 and potentially Custom accounts for V2.

### Legal/Family Law (divorce-lawyer — 8 findings)

1. **FRE 803(6) framing is wrong** — Drop business records exception language. Focus on: cryptographic hash verification for integrity, server-side timestamps with no client modification, records custodian process. Judges care about "can this be tampered with?" not hearsay exceptions.

2. **UCCJEA display is unauthorized practice of law** — R5.3 must NOT display "which state's order controls." Display factual data only (residence states, order issuing state). Link to disclaimer that jurisdiction analysis requires an attorney.

3. **AI dispute "review" is a legal minefield** — R4.4's "Platform AI-assisted review" must produce recommendations, not determinations. "Based on submitted documentation, the expense appears consistent/inconsistent with typical costs" — never "dispute resolved in favor of Parent A."

4. **NLP memo filtering creates false security** — Coded hostile language ("per our agreement," passive-aggressive affirmations) will bypass NLP detection. Log memos and include in court exports, but don't promise detection of adversarial communication.

5. **Missing features judges expect**: handoff logging with GPS timestamp, medical/educational decision logging, parenting plan upload (optional), third-party access audit log.

### Technical Architecture (3 developers — 10+ findings each)

1. **Stripe Connect account type**: Express is acceptable for MVP (wrapped in full-screen modal). Custom for V2 when revenue justifies engineering cost. Stripe Financial Connections (bank linking) is native regardless of account type.

2. **Immutable records architecture**: Append-only PostgreSQL tables with tamper-evident hash chains (each row's hash includes previous row's hash). SHA-256 minimum. **Must be in V1** — the investor conceded post-debate that hash integrity cannot be backfilled retroactively; V1 records without hashes would be permanently second-class evidence for your earliest, highest-risk users. Implementation: SHA-256 hash per record at write time (free), daily anchor to a public timestamped log (free — public GitHub commit works), hash included in PDF exports. ~2-3 weeks of backend work. Third-party timestamp authority (RFC 3161) and PKI/X.509 can wait for V2.

3. **Offline behavior policy**: Expense viewing = fully offline (cache 90 days). Expense submission = offline queue with dual timestamps (`client_created_at` + `server_received_at`). Payment initiation = require online. Spec must state this explicitly for court-record integrity.

4. **Webhook idempotency**: Every Stripe webhook handler must be idempotent. Webhook delivery failure for `charge.dispute.created` means the platform doesn't know a dispute occurred. Needs dead-letter queue and reconciliation job.

5. **Tech stack**: React Native recommended for MVP (official Stripe SDK, native push, native camera, ~80% code sharing). PWA rejected — notification reliability, camera quality, and credential storage all fall below acceptable thresholds for a financial product. The delta is 2-3 months, not 6-12.

6. **App Store / Play Store**: iOS subscription must be web-only purchase (avoid 30% Apple IAP cut). Google Play Financial Services declaration required — expect 4-6 week initial review, not standard 2-3 days.

7. **Missing R9: Mobile Architecture section**: Notification permission gates, FCM+APNs stack, offline queue policy, screen content masking, biometric re-auth for payment initiation (V2).

---

## Unresolved Disagreements

| Topic | Position A | Position B |
|-------|-----------|-----------|
| **ACH timing** | V1 with preconditions (divorce-lawyer, ios-dev) — "without payments, you're a prettier spreadsheet" | V2 after PMF proven (investor, web-dev, android-dev, fin-regulator, aml-lawyer) |
| **$5 minimum** | Keep (divorce-lawyer: anti-harassment) | Raise to $25 (divorce-lawyer secondary position: $5 is trivially low for real harassment) |
| **Rate limits** | Hard limit 10-25/day (divorce-lawyer) | Soft limit with notification batching (android-dev: OS-level collapse keys may suffice) |
| **Court admissibility depth** | ~~Hash chain + RFC 3161 in V1 (divorce-lawyer) vs. V2 (investor)~~ **RESOLVED**: Hash chain in V1 (investor conceded), PKI/RFC 3161 in V2 |
| **Professional accounts** | Cut from V1 entirely (investor) | Keep but fix data boundaries first (divorce-lawyer) |

---

## V1 Success Metrics (investor + web-dev consensus)

- 500 active co-parent pairs
- 50 paying for PDF court export
- 3 mediator referral partners
- **Payee activation rate > 50%** within 60 days of payer signup (critical — if below 50%, either accelerate ACH or improve calendar before concluding PMF is absent)
- If payee activation is low, the calendar is the lever, not ACH

---

## Action Items for Founder

| # | Action | Source | Timeline |
|---|--------|--------|----------|
| 1 | Cut ACH from V1 scope | Panel consensus (5-2) | Now |
| 2 | Add Notification Architecture section (R9) | All 3 developers | Before sprint 1 |
| 3 | Implement DV safety defaults | Investor + divorce-lawyer | Before launch |
| 4 | Add expense submission rate limits (soft, 10-15/day) | Divorce-lawyer | Before launch |
| 5 | Fix R8.2 professional account data boundaries OR cut from V1 | Divorce-lawyer + fin-regulator | Before launch |
| 6 | Remove UCCJEA "which state controls" display from R5.3 | Divorce-lawyer | Now (spec fix) |
| 7 | Drop FRE 803(6) language, focus on cryptographic integrity | Divorce-lawyer + web-dev | Now (spec fix) |
| 8 | Change R4.4 AI "review" to "recommendation" | Divorce-lawyer | Now (spec fix) |
| 9 | Add 1099-K disclosure for Stripe Express payees | Web-dev | Before V2 ACH |
| 10 | Commission multi-state MTL legal opinion | Fin-regulator + AML-lawyer | Before V2 ACH |
| 11 | Build AML/BSA program (policy, BSA officer, SAR workflow, OFAC) | AML-lawyer + fin-regulator | Before V2 ACH |
| 12 | Add asymmetric co-parent verification (independent child name/DOB entry) | AML-lawyer + divorce-lawyer | V1 onboarding |
| 13 | Choose tech stack (React Native recommended) | All 3 developers | Before sprint 1 |
| 14 | Design DB schema with ACH-ready slots from day one | Web-dev + AML-lawyer | Sprint 1 |
| 15 | Resolve Reg E vs. Stripe finality conflict in spec | Fin-regulator | Before V2 ACH |

---

## Related Documents

- `initial_spec.md` — the spec under review
- `market-research.md` — market research informing the spec
- `Fraud-Risk-Analysis.md` — adversarial fraud analysis
