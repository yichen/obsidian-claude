# FairBridge.app — MVP Definition

**Date**: 2026-03-16
**Status**: Draft
**Source**: 7-expert panel review + 3-agent MVP scoping session
**Founder decision**: ACH + Expense Tracking + Calendar are ALL in V1.

---

## V1 Scope Summary

Three pillars, stripped to minimum viable versions. Everything else is cut.

---

## Pillar 1: ACH Payments

### In Scope

| Feature | Detail |
|---------|--------|
| Stripe Connect Express accounts | Both parents create connected accounts |
| Stripe Financial Connections | Instant bank linking via OAuth — NOT microdeposits (payee funnel dies without instant verification) |
| Payment initiation | Payer submits expense → links payment → payee approves → ACH settles |
| "Money waiting" invite | Payee invite email shows amount waiting — reframes "join app" as "claim payment" |
| Progressive KYC | Email+phone at signup; bank+identity at first payout |
| Transaction fee | 0.8% Stripe pass-through to payer, no platform markup at V1 |
| Authorization evidence | IP, timestamp, device fingerprint, confirmation action stored per debit |
| Ramp-up limits | $2,500/week first 6 payments, $5,000/week after — internal control, NOT shown in UI |
| $5 minimum | Anti-harassment measure |
| Reg E dispute intake | Email-based consumer dispute channel + provisional credit process |
| Reserve fund | $5,000-10,000 operating reserve for Reg E provisional credits |

### Out of Scope (V2+)

- Plaid bank feed / auto-detection (R2.4)
- AI receipt verification (Veryfi/Taggun)
- Biometric re-auth for payment initiation
- Platform transaction fee markup
- Credit-push fallback for abusive disputers
- Custom Stripe accounts (Express is sufficient)

---

## Pillar 2: Expense Tracking

### In Scope

| Feature | Detail |
|---------|--------|
| Expense submission | Amount + description required; date defaults to today; category optional |
| Receipt upload | Photo (camera + gallery) and PDF — optional but badged as "documented" |
| Two-party confirmation | Approve / Dispute (with explanation) / Mark as Paid Externally |
| External payment logging | Log Venmo/Zelle/check/cash payments with two-party confirmation |
| Append-only records | Every record is INSERT-only, no UPDATE/DELETE, server-side timestamps |
| SHA-256 hash chain | Each record's hash includes previous record's hash — created at write time, non-negotiable |
| Daily hash anchor | Daily Merkle root committed to a public log (GitHub commit is sufficient) |
| Soft rate limit | 10-15 expense submissions per day, admin override for legitimate bulk |
| CSV export | Free tier |
| Memo field | 500 character limit, manual report button (no NLP filtering) |

### Out of Scope (V2+)

- AI duplicate/fraud detection
- Round-number flagging
- Cost-range cross-referencing
- NLP memo filtering
- Court-formatted PDF export (add as $3/export paid feature at week 6)
- Perceptual hashing on receipt images

---

## Pillar 3: Custody Calendar

### In Scope

| Feature | Detail |
|---------|--------|
| Custody pattern presets | 2-2-5-5, 2-2-3, alternating weeks, custom |
| Visual calendar | Week + month view, color-coded parent time |
| Parenting time % calculator | Simple percentage display |
| Holiday overlay | US federal holidays + common school break types |
| Calendar export | .ics export for Google/Apple/Outlook |
| Setup flow | One parent configures; co-parent confirms |

### Out of Scope (V2+)

- AI schedule swap detection (R5.2)
- UCCJEA jurisdiction display (R5.3) — panel flagged as unauthorized practice of law
- School calendar integration
- Handoff logging with GPS
- Bi-directional calendar sync (export-only is correct for immutability)

---

## Cross-Cutting Requirements (Non-Negotiable V1)

### DV Safety Defaults (3-5 days build)

These are implementation defaults, not features. Getting them wrong is a negligence risk.

- No cross-parent activity timestamps (never show "last active" to the other parent)
- No sensitive content in push notification payloads ("New activity in FairBridge" not "$500 expense from Parent A")
- Silent account deactivation without alerting co-parent
- Full data export + deletion on account close
- Safety resources link (DV hotline) in app settings
- Screen content masking in app switcher (`FLAG_SECURE` on Android, iOS equivalent)

### Notification Architecture

- Primary: FCM (Android) + APNs (iOS) — high-priority messages
- Fallback: Email at 15-minute delay for undelivered push
- SMS: Highest-stakes events only (first payment, ACH debit initiated)
- In-app inbox: Guaranteed fallback for users who deny push permission
- Android: Battery optimization exemption prompt during onboarding
- Mandatory notification permission gate before pairing is allowed

### Asymmetric Co-Parent Verification

- Both parents independently enter child's name + birth year at onboarding
- System matches without showing either parent what the other entered
- Mismatch = pair blocked from ACH until manual review
- Costs real parents nothing; adds wire fraud exposure for fake pairs

### Fraud Controls (V1 Minimum)

- Velocity monitoring: flag pairs where payment frequency/amounts spike >3x baseline
- Connected account cross-check: same bank account across different pairs = flag
- IP geolocation: same-IP pairs flagged for manual review (co-parents should be separated)
- Return rate dashboard: automated monitoring against Nacha 0.5% threshold
- OFAC: Stripe handles SDN screening on connected accounts natively

---

## Compliance Stack

### Required Before First ACH Transaction

| Item | Cost | Timeline | Notes |
|------|------|----------|-------|
| ~~Nacha TPS registration~~ | ~~$0-1,000~~ | **NOT NEEDED.** Stripe is the TPS; FairBridge is the Originator per [Stripe ACH Payment Terms](https://stripe.com/legal/ACH). Stripe handles TPS registration, annual audits, and ODFI relationship. FairBridge's Originator obligations: store authorization evidence, ensure data accuracy, monitor return rates. | Resolved |
| ACH Authorization Language | $800-1,500 | 1-2 weeks | Nacha-compliant, displayed per transaction |
| Reg E Error Resolution Notice | Bundled above | 1-2 weeks | 12 CFR 1005.7 compliant |
| Terms of Service (ACH addendum) | $1,500-2,500 | 2-3 weeks | ACH-specific terms |
| Written AML/BSA Policy | $1,500-2,500 | 2-3 weeks | Stripe-reliance model, founder as BSA point of contact |
| 1099-K Tax Disclosure | $500 | 1 week | In ToS and UI — Stripe Express may issue 1099-Ks to payees |
| DV Safety Defaults | $0 (engineering) | 3-5 days | Implementation decisions, not legal docs |
| **Total pre-launch legal** | **$5,000-8,500** | **2-4 weeks** | |

### Required Before Scaling (Year 1)

| Item | Cost | Timeline |
|------|------|----------|
| ~~Multi-state MTL opinions (NY, CA, TX)~~ | ~~$9,000-15,000~~ | **NOT NEEDED.** FairBridge is not a money transmitter — Stripe handles regulated money transmission. Launch all 50 states. |
| ~~First Nacha Rules Compliance Audit~~ | ~~$5,000-15,000~~ | **Stripe's obligation as TPS, not FairBridge's** |
| Subpoena response process | $0-1,000 | Founder-drafted, attorney reviewed |

### NOT Required for V1

- Full BSA Officer designation (founder is point of contact)
- SAR filing workflow (add if/when volume exceeds $1M/year)
- RFC 3161 third-party timestamping (hash chain is sufficient)
- Annual AML training (add when you have employees)

---

## State Launch Strategy

### Launch in All 50 States from Day One

**FairBridge does NOT need a Money Transmitter License.** The platform never possesses or controls funds — Stripe does. Three independent protections:

1. **Architectural**: All funds flow through Stripe Connect. FairBridge only instructs; Stripe transmits.
2. **FinCEN Payment Processor Exemption**: FairBridge meets all four prongs of the federal exemption.
3. **Agent of Payee Exemption**: 25+ states (including NY, CA) recognize this under the Model Money Transmission Modernization Act.

**Non-negotiable requirement**: Every payment MUST flow through Stripe Connect. Never hold, receive, or control funds outside Stripe's infrastructure. The spec's R1.1 requirement (every payment linked to a documented expense) further strengthens this position.

~~No tiered state rollout needed. No $9-15K in state MTL legal opinions. No blocking NY/CA/TX.~~

---

## Pricing

| Tier | Who | Price | What's Included |
|------|-----|-------|-----------------|
| **Free** | Payee (receiving parent) | $0 forever | Receive payments, view expenses, shared calendar (read-only), CSV export |
| **Paid** | Payer (initiating parent) | $7/mo or $70/yr | Initiate ACH payments, submit expenses, calendar setup/editing |
| **Transaction** | Payer | 0.8% per ACH | Stripe cost pass-through, no platform markup at V1 |
| **Court PDF** | Either parent | $3/export | Court-formatted PDF with hash verification (add at week 6+) |

Payer pays. Payee is free. This solves the two-party problem — one motivated payer funding the product beats two reluctant payers killing conversion.

---

## Engineering Plan

### Tech Stack

- **Frontend**: React Native (Expo managed workflow) — ~80% code sharing iOS/Android
- **Backend**: Fastify (Node.js) + PostgreSQL + Redis (BullMQ for job queues)
- **Hosting**: Railway ($50-150/mo at launch scale)
- **File storage**: Cloudflare R2 (receipt images, PDF exports)
- **Email**: Resend ($20/mo)
- **SMS**: Twilio (pay-as-you-go, high-stakes events only)
- **Push**: FCM + APNs via Firebase

### Timeline (2 devs)

| Phase | Weeks | What Ships |
|-------|-------|-----------|
| Foundation | 1-4 | Auth, invite/pairing, DB schema (ACH-ready + hash chain), push notification stack |
| Core features | 3-10 | Expense tracking, two-party confirmation, calendar, external payment tracking, DV defaults |
| ACH integration | 8-16 | Stripe Connect onboarding, payment flow, webhook handlers, dispute intake |
| Polish + submit | 14-18 | App Store / Play Store submission (4-6 week review for financial app) |
| **Soft launch** | **~20** | **10 curated pairs, invite-only** |
| Beta | 20-32 | 50 pairs, 90 days, measure payee activation |

### Timeline (solo dev)

Add 50-70% to above. Realistic: 9-12 months to soft launch.

### Critical: Stripe Connect approval timeline

Apply for Stripe Connect platform account on day 1. Approval takes 1-3 weeks. This is a hard blocker for ACH development — you need a test-mode platform account to build against.

---

## Launch Sequence

### Option A: Incremental (Recommended)

1. **Weeks 1-12**: Build expense tracking + calendar + external payment tracking + notifications
2. **Week 1**: Start Stripe Connect application + legal engagement + Nacha verification with Stripe
3. **Weeks 10-12**: Ship V1a (no ACH) to App Store — expense tracking + calendar + external payments
4. **Weeks 12-20**: Build ACH integration while V1a users validate pairing/adoption
5. **Weeks 16-20**: Ship V1b update with ACH enabled
6. **Week 20**: Soft launch with 10 curated pairs

**Why Option A**: Nacha/Stripe/legal processes take 4-8 weeks regardless. V1a gets you to market while those run. If payee activation rate is <50% in V1a, you know to fix calendar/UX before ACH adds complexity.

### Option B: Ship Together

1. **Weeks 1-18**: Build everything
2. **Week 18-22**: App Store submission + review
3. **Week 22**: Soft launch with 10 curated pairs

**Why not Option B**: One App Store rejection or Stripe delay pushes the entire launch. No user data until month 5+.

---

## Success Metrics

| Metric | Target | Timeframe |
|--------|--------|-----------|
| Payee activation rate | >50% of invited payees link bank | 60 days post-invite |
| First completed ACH payment | <10 days from payer signup | Per-user |
| ACH vs. "mark as paid externally" | >50% choose ACH | 90-day beta |
| Nacha unauthorized return rate | <0.5% | Monthly |
| Mediator referral partners | 3+ committed | Pre-launch |
| Active co-parent pairs | 50 (beta), 500 (Year 1) | Cumulative |
| Payee NPS | >30 | 30 days post-activation |

---

## Immediate Action Items (This Week)

1. ~~Email Stripe about Nacha TPS~~ — **Resolved: Stripe is the TPS, FairBridge is the Originator.** No independent registration needed.
2. Verify with Stripe docs: does the March 2026 "PURCHASE" Company Entry Description label apply to expense reimbursement ACH debits? See [Stripe Nacha Purchase Rule docs](https://docs.stripe.com/payments/ach-direct-debit/nacha-purchase-rule).
3. Apply for Stripe Connect platform account (test mode)
4. Engage fintech attorney ($300-450/hr) for ACH authorization language + Reg E notice + AML policy
5. Set up $5-10K operating reserve for Reg E provisional credits
6. Begin React Native project scaffold

---

## What's Explicitly NOT in V1

- Professional accounts (R8.2)
- Plaid bank feed (R2.4)
- AI receipt verification (R4.2)
- NLP memo filtering (R4.3)
- AI schedule swap detection (R5.2)
- UCCJEA jurisdiction display (R5.3)
- BestInterest integration (R8.1)
- RFC 3161 timestamping
- PKI/X.509 digital signatures on PDFs
- Custom Stripe accounts
- Biometric re-auth for payments

---

## Related Documents

- `initial_spec.md` — full spec (pre-MVP scoping)
- `Spec-Review-Panel-Report.md` — 7-expert panel review findings
- `market-research.md` — market research
- `Fraud-Risk-Analysis.md` — adversarial fraud analysis
