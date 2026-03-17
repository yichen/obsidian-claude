# FairBridge.app — MVP Definition

**Date**: 2026-03-16
**Status**: Draft
**Source**: 7-expert panel review + 3-agent MVP scoping session

---

## TL;DR: A $4-7K Compliance Bill to Launch ACH Payments in All 50 States

A 7-expert panel initially recommended deferring ACH payments to V2, estimating **$30-50K/year in compliance overhead** and a tiered state rollout blocking 28% of the US market [1]. That estimate was wrong. Stripe Connect eliminates the two largest cost items: Nacha Third-Party Sender registration (**$0** — Stripe is the TPS, FairBridge is the Originator [2]) and state Money Transmitter Licenses (**$0** — FairBridge never possesses funds, triggering three independent federal/state exemptions [3]).

The actual pre-launch compliance cost is **$4-7K** (one-time legal drafting), the annual overhead is **~$1K** (subpoena process + AML policy maintenance), and the app launches in **all 50 states from day one**. The regulatory barrier to ACH is not the wall the panel described — it's a speed bump.

The MVP ships three features — ACH payments, expense tracking, and a custody calendar — stripped to their minimum viable forms. Everything else is cut. **One parent pays $7/mo (83% cheaper than OFW per family [4]); the other parent receives money for free.** This asymmetric pricing solves the two-party adoption problem that kills most co-parenting apps: the payee signs up because they have money waiting, not because someone asked them to download software.

---

## "Pay, Track, Prove" — Three Pillars, Each Stripped to the Minimum

### Pillar 1: ACH Payments That Settle in 3-4 Days via Stripe Connect

| Feature | Detail |
|---------|--------|
| Stripe Connect Express accounts | Both parents create connected accounts |
| Stripe Financial Connections | Instant bank linking via OAuth — NOT microdeposits (payee funnel dies without instant verification [5]) |
| Payment initiation | Payer submits expense → links payment → payee approves → ACH settles (3-4 business days) |
| "Money waiting" invite | Payee invite email shows amount waiting — reframes "join app" as "claim payment" |
| Progressive KYC | Email+phone at signup; bank+identity at first payout |
| Transaction fee | **0.8%** Stripe pass-through to payer (~$1.60/mo on a typical $200 monthly payment), no platform markup at V1 |
| Authorization evidence | IP, timestamp, device fingerprint, confirmation action stored per debit [6] |
| Ramp-up limits | $2,500/week first 6 payments, $5,000/week after — internal control, NOT published in UI or marketing [7] |
| $5 minimum | Anti-harassment floor (prevents micropayment flooding [8]) |
| Reg E dispute intake | Email-based consumer dispute channel + provisional credit within 10 business days [9] |
| Reserve fund | ~$5,000-10,000 operating reserve (~1-3% of projected Year 1 transaction volume) for Reg E provisional credits |

**Cut for V2+:** Plaid bank feed ($500/mo minimum [4]), AI receipt verification (~$200-500/mo), biometric re-auth, platform transaction fee markup, credit-push fallback for abusive disputers, Custom Stripe accounts.

### Pillar 2: Expense Records That Can't Be Tampered With

| Feature | Detail |
|---------|--------|
| Expense submission | Amount + description required; date defaults to today; category optional |
| Receipt upload | Photo (camera + gallery) and PDF — optional but badged as "documented" in court exports |
| Two-party confirmation | Approve / Dispute (with explanation) / Mark as Paid Externally |
| External payment logging | Log Venmo/Zelle/check/cash with two-party confirmation — zero regulatory burden [10] |
| Append-only records | INSERT-only schema, no UPDATE/DELETE, server-side UTC timestamps |
| SHA-256 hash chain | Each record's hash includes the previous record's hash — created at write time, **cannot be backfilled retroactively** [11] |
| Daily hash anchor | Daily Merkle root committed to a public log (GitHub commit — free, verifiable by any third party) |
| Soft rate limit | 10-15 expense submissions/day with admin override (prevents expense-flooding harassment [8]) |
| CSV export | Free tier |
| Memo field | 500 char limit, manual report button (no NLP filtering — coded hostile language bypasses NLP anyway [12]) |

**Cut for V2+:** AI duplicate/fraud detection, round-number flagging, cost-range cross-referencing, NLP memo filtering, perceptual hashing. Court-formatted PDF export added at week 6+ as $3/export paid feature.

### Pillar 3: A Custody Calendar Both Parents Actually Open Every Week

| Feature | Detail |
|---------|--------|
| Custody pattern presets | 2-2-5-5, 2-2-3, alternating weeks, custom |
| Visual calendar | Week + month view, color-coded parent time |
| Parenting time % calculator | Simple percentage display |
| Holiday overlay | US federal holidays + common school break types |
| Calendar export | .ics export to Google/Apple/Outlook |
| Setup flow | One parent configures; co-parent confirms |

**Cut for V2+:** AI schedule swap detection, UCCJEA jurisdiction display (flagged as unauthorized practice of law [12]), school calendar integration, handoff logging with GPS, bi-directional sync (export-only preserves immutability).

The calendar is the **retention mechanism**, not the acquisition hook. ACH gets Parent B to sign up; the calendar makes both parents open the app every week. It must be genuinely useful — not a placeholder.

---

## 4 Non-Negotiable Cross-Cutting Requirements — ~5 Days of Engineering Total

### Domestic Violence Safety Defaults (3-5 days)

These are implementation defaults, not features. The 7-expert panel's divorce lawyer and angel investor — who disagreed on nearly everything else — reached consensus that these are **launch preconditions, not V2 features** [8]. The cost of getting them wrong: negligence liability when the first abuser uses the app as a surveillance tool. The cost of getting them right: 3 days.

- No cross-parent activity timestamps (never show "last active")
- No sensitive content in push payloads ("New activity in FairBridge" — not "$500 expense from Parent A")
- Silent account deactivation without alerting co-parent
- Full data export + deletion on account close
- Safety resources link (DV hotline) in app settings
- Screen content masking in app switcher (`FLAG_SECURE` on Android, iOS equivalent)

### Notification Architecture — The Core Workflow Depends on This

**~35-40% of Android devices** (Samsung/Xiaomi/Oppo OEM skins) will silently kill push notifications even for high-priority messages [13]. Without a fallback chain, the two-party confirmation workflow — the product's core mechanic — silently fails for over a third of users.

- **Primary**: FCM (Android) + APNs (iOS) — high-priority messages
- **Fallback**: Email at 15-minute delay for undelivered push
- **SMS**: Highest-stakes events only (first payment, ACH debit initiated) — ~$0.008/SMS via Twilio
- **In-app inbox**: Guaranteed fallback for users who deny push permission
- **Android-specific**: Battery optimization exemption prompt during onboarding
- **Gate**: Mandatory notification permission before pairing is allowed

### Asymmetric Co-Parent Verification — $0 AML Control

Both parents independently enter child's name + birth year at onboarding. The system matches without showing either parent what the other entered. Mismatch = pair blocked from ACH until manual review. This was co-developed by the AML lawyer and divorce lawyer during the panel debate [7] — it costs real parents nothing and adds **wire fraud exposure** (18 U.S.C. § 1343) for criminal pairs attempting to launder through fake co-parent accounts.

### V1 Fraud Controls (Engineering Only, No Third-Party Costs)

- Velocity monitoring: flag pairs where payment frequency/amounts spike >3x baseline
- Connected account cross-check: same bank account across different pairs = immediate flag
- IP geolocation: same-IP pairs flagged for manual review (separated co-parents shouldn't share an IP)
- Return rate dashboard: automated monitoring against Nacha's **0.5% unauthorized return threshold** [6]
- OFAC: Stripe handles SDN screening on connected accounts natively [3]

---

## $4-7K to Launch — Not the $30-50K the Panel Estimated

### What the Panel Got Wrong

The 7-expert panel estimated **$20-50K/year** in ongoing compliance costs [1]. Two findings collapsed that estimate:

1. **Nacha TPS registration ($5-15K/yr in audits)**: Not needed. Stripe's ACH Payment Terms explicitly state: *"Stripe is operating as a Third Party Sender... you understand and accept your role as the Originator"* [2]. Stripe handles TPS registration, annual audits, and ODFI relationship.

2. **State Money Transmitter Licenses ($9-15K in legal opinions)**: Not needed. FairBridge never possesses or controls funds. Three independent exemptions apply: (a) architectural — funds flow payer → Stripe → payee, never through FairBridge; (b) FinCEN Payment Processor Exemption — all four prongs satisfied; (c) Agent of Payee Exemption — 25+ states including NY and CA [3].

### What's Actually Required Before the First ACH Transaction

| Item | Cost | Timeline |
|------|------|----------|
| ACH Authorization Language (Nacha-compliant, per-transaction) | ~$800-1,500 | 1-2 weeks |
| Reg E Error Resolution Notice (12 CFR 1005.7 compliant) | Bundled above | 1-2 weeks |
| Terms of Service (ACH addendum) | ~$1,500-2,500 | 2-3 weeks |
| Written AML/BSA Policy (Stripe-reliance model, founder as BSA contact) | ~$1,500-2,500 | 2-3 weeks |
| 1099-K Tax Disclosure (Stripe Express may issue 1099-Ks to payees above $600) | ~$500 | 1 week |
| DV Safety Defaults | $0 (engineering) | 3-5 days |
| **Total** | **~$4,300-7,500** | **2-4 weeks** |

### Year 1 Scaling Costs

| Item | Cost | Notes |
|------|------|-------|
| Subpoena response process | ~$0-1,000 | Founder-drafted, attorney reviewed |
| Full BSA Officer designation | $0 | Founder is point of contact at this scale |
| SAR filing workflow | $0 | Add when volume exceeds ~$1M/year processed |

**One remaining open question**: Does the March 2026 Nacha "PURCHASE" Company Entry Description label apply to expense reimbursement ACH debits? The rule targets *"online purchase of physical or digital goods"* — reimbursements may or may not fit [14].

---

## All 50 States from Day One — No Tiered Rollout

FairBridge does **not** need a Money Transmitter License in any state [3]. The platform never possesses or controls funds — Stripe does. Three independent protections:

1. **Architectural**: All funds flow through Stripe Connect. FairBridge only sends instructions; Stripe transmits money.
2. **FinCEN Payment Processor Exemption**: Satisfies all four prongs — facilitates payment, uses BSA-regulated ACH, operates under formal agreement with Stripe, has agreement with payee.
3. **Agent of Payee Exemption**: 25+ states (including NY, CA) recognize this under the Model Money Transmission Modernization Act.

**The one rule that must never be broken**: Every payment flows through Stripe Connect. The moment FairBridge holds, receives, or controls funds outside Stripe's infrastructure, the entire exemption analysis collapses. The spec's R1.1 requirement — every payment linked to a documented expense — further strengthens the "facilitation, not transmission" position.

---

## One Parent Pays $7/mo — 83% Cheaper Than OFW per Family

| Tier | Who | Price | What's Included |
|------|-----|-------|-----------------|
| **Free** | Payee (receiving parent) | $0 forever | Receive payments, view expenses, shared calendar (read-only), CSV export |
| **Paid** | Payer (initiating parent) | $7/mo or $70/yr | Initiate ACH payments, submit expenses, calendar setup/editing |
| **Transaction** | Payer | 0.8% per ACH | Stripe cost pass-through (~$1.60/mo at $200 avg payment) |
| **Court PDF** | Either parent | $3/export | Court-formatted PDF with hash verification (added at week 6+) |

### Mental Model: Why Asymmetric Pricing Solves the Cold-Start Problem

OFW charges **both** parents $12.50-25/mo ($300-600/yr per family [4]). FairBridge charges **one** parent $7/mo ($70/yr per family). The payee is free forever.

This works because:
- The **payer** self-selects and is motivated (wants documentation + convenience)
- The **payee** signs up because they have money waiting — not because someone asked them to join an app
- The invite email says "You have a $180 reimbursement from [Parent A] — claim it in 2 minutes, free" — this is a **payment notification**, not a software download request
- If Venmo's growth proved anything, it's that "you have money waiting" converts better than any feature pitch

---

## 20 Weeks to Soft Launch with 2 Devs — 9-12 Months Solo

### Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React Native (Expo) | ~80% code sharing iOS/Android, official Stripe SDK [13] |
| Backend | Fastify (Node.js) | Faster than Express, built-in schema validation |
| Database | PostgreSQL + Redis (BullMQ) | Append-only tables + job queues for webhooks and notification fallback |
| Hosting | Railway | ~$50-150/mo at launch scale (covers backend + DB + Redis) |
| File storage | Cloudflare R2 | Receipt images + PDF exports (30% cheaper than S3) |
| Email | Resend | ~$20/mo up to 100K emails |
| SMS | Twilio | Pay-as-you-go (~$0.008/SMS), high-stakes events only |
| Push | FCM + APNs via Firebase | Single server-side integration fans out to both platforms |

**Monthly infrastructure at launch: ~$100-200/mo.** At 500 paying payers ($7/mo = $3,500/mo revenue), infrastructure is ~4% of revenue.

### Timeline (2 Devs)

| Phase | Weeks | What Ships |
|-------|-------|-----------|
| Foundation | 1-4 | Auth, invite/pairing, DB schema (ACH-ready + hash chain), push notification stack |
| Core features | 3-10 | Expense tracking, two-party confirmation, calendar, external payment tracking, DV defaults |
| ACH integration | 8-16 | Stripe Connect onboarding, payment flow, webhook handlers [15], dispute intake |
| Polish + submit | 14-18 | App Store / Play Store submission (expect **4-6 week** review for financial apps [13]) |
| **Soft launch** | **~20** | **10 curated pairs, invite-only** |
| Beta | 20-32 | 50 pairs, 90 days, measure payee activation |

**Solo dev**: Add 50-70%. Realistic: **9-12 months** to soft launch.

**Hard blocker**: Apply for Stripe Connect platform account on **day 1**. Approval takes 1-3 weeks. ACH development cannot start without a test-mode platform account.

### Recommended: Ship Incrementally (Option A)

1. **Weeks 1-12**: Build expense tracking + calendar + external payment tracking + notifications
2. **Week 1**: Start Stripe Connect application + legal engagement
3. **Weeks 10-12**: Ship V1a (no ACH) to App Store — expense tracking + calendar + external payments
4. **Weeks 12-20**: Build ACH integration while V1a users validate pairing/adoption
5. **Weeks 16-20**: Ship V1b update with ACH enabled
6. **Week 20**: Soft launch with 10 curated pairs

**Why incremental**: Legal drafting takes 2-4 weeks. App Store financial review takes 4-6 weeks. V1a gets you to market while those processes run. If payee activation rate is <50% in V1a, you know to fix calendar/UX before ACH adds complexity.

---

## The Only Metrics That Matter for the First 90 Days

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Payee activation rate** | **>50%** of invited payees link bank within 60 days | If <30%, the payee friction is disqualifying — fix invite flow before scaling [5] |
| First completed ACH payment | <10 days from payer signup | Measures time-to-value; >14 days signals onboarding friction |
| ACH vs. "mark as paid externally" | >50% choose ACH | If most users prefer external logging, ACH isn't solving a real problem |
| Nacha unauthorized return rate | <0.5% | At 50 pairs / ~100 monthly debits, **1 single unauthorized return = 1%** — curate beta cohort carefully [6] |
| Mediator referral partners | 3+ committed pre-launch | Primary acquisition channel; validates distribution thesis |
| Payee NPS | >30 at day 30 | The payee experience determines word-of-mouth; payer NPS is necessary but not sufficient |

---

## This Week: 6 Actions Before Writing a Line of Code

1. ~~Email Stripe about Nacha TPS~~ — **Resolved**: Stripe is the TPS, FairBridge is the Originator [2].
2. **Verify**: Does the March 2026 "PURCHASE" Company Entry Description label apply to expense reimbursement ACH debits? [14]
3. **Apply** for Stripe Connect platform account (test mode) — hard blocker, 1-3 week approval.
4. **Engage** fintech attorney ($300-450/hr) for ACH authorization language + Reg E notice + AML policy — ~$4-7K total.
5. **Set up** $5-10K operating reserve (~1-3% of projected Year 1 volume) for Reg E provisional credits.
6. **Begin** React Native project scaffold.

---

## What's Explicitly NOT in V1

Professional accounts (R8.2), Plaid bank feed (R2.4), AI receipt verification (R4.2), NLP memo filtering (R4.3), AI schedule swap detection (R5.2), UCCJEA jurisdiction display (R5.3), BestInterest integration (R8.1), RFC 3161 timestamping, PKI/X.509 PDF signatures, Custom Stripe accounts, biometric re-auth for payments.

---

## Appendix

### [1] 7-Expert Panel Review

Panel of web developer, iOS developer, Android developer, high-conflict divorce lawyer, financial regulator, AML/BSA lawyer, and angel investor. Voted 5-2 to defer ACH to V2. Key concern: estimated $20-50K/year compliance overhead. Full report: `Spec-Review-Panel-Report.md` (2026-03-16).

### [2] Stripe ACH Payment Terms — TPS Classification

Stripe's ACH Payment Terms at [stripe.com/legal/ACH](https://stripe.com/legal/ACH): *"Stripe is operating as a Third Party Sender (as defined in the Nacha Operating Rules) and you understand and accept your role as the Originator."* Stripe also prohibits nested TPS: *"You must not submit ACH Network Transactions as a Nested Third Party Sender."* Full analysis: `Stripe-Connect-Nacha-TPS-Analysis.md`.

### [3] Money Transmitter License Exemptions

Three independent layers: (a) Architectural — FairBridge never possesses funds per Stripe Services Agreement; (b) FinCEN Payment Processor Exemption per FIN-2013-G001 — all four prongs satisfied; (c) Agent of Payee Exemption under Model Money Transmission Modernization Act — 25+ states including NY Banking Law Section 641 and CA CMTA. Full analysis: `Money-Transmission-License-Analysis.md`.

### [4] Competitive Pricing Data

OFW: **$12.50-25/mo per parent** ($300-600/yr per family). TalkingParents: **$8.99-19.99/mo**. Plaid Transactions API: **~$1.50/user/month, ~$500/month minimum**. Sources: OFW product pages, TalkingParents pricing page, Plaid developer documentation. Full competitive analysis: `market-research.md`.

### [5] Payee Funnel and Financial Connections

Stripe Financial Connections enables instant bank verification via OAuth (login to bank, confirm account). Microdeposits require 1-2 business day wait for two small deposits + user returns to app to confirm amounts. Marketing agent estimated microdeposit payee completion rate at **~15-25%** vs. Financial Connections at **~40-60%** based on industry benchmarks for two-sided payment platforms.

### [6] Nacha Originator Obligations

Per Nacha Operating Rules and Stripe ACH Payment Terms, the Originator must: (a) obtain written authorization before each WEB debit, (b) ensure accuracy of transaction data, (c) monitor return rates — unauthorized returns (R05, R07, R10, R29, R51) must stay below **0.5%**, administrative returns below **3%**, overall below **15%**. At 100 monthly debits, a single unauthorized return = 1.0%, double the threshold.

### [7] AML Controls — Panel Co-Development

The asymmetric co-parent verification was developed during real-time debate between the AML lawyer and divorce lawyer on the 7-expert panel. The AML lawyer proposed document-based verification; the divorce lawyer objected that cooperative parents often lack formal documentation. The compromise — independent child name/DOB entry — emerged from the debate. The $5,000/week limit is implemented as an internal risk control; the AML lawyer recommended against publishing specific thresholds in marketing materials to avoid structuring facilitation.

### [8] Domestic Violence and Harassment Controls

Expense flooding attack vector identified by divorce-lawyer panelist: Parent A submits 50-100 expenses at $5.01 each — 100 notifications requiring individual review. The $5 minimum prevents sub-dollar harassment; the 10-15/day soft rate limit prevents volume harassment. DV safety defaults (no activity timestamps, silent deactivation, screen masking) were consensus between the angel investor and divorce lawyer — the investor initially classified these as "scope creep" but conceded after reframing as "implementation defaults with a safe or unsafe behavior either way."

### [9] Regulation E Dispute Process

12 CFR Part 1005 (Regulation E) gives consumers absolute right to dispute unauthorized ACH debits within 60 days of statement date. Financial institutions must provide provisional credit within **10 business days**. Stripe's internal dispute finality (no appeal for platforms) does NOT extinguish FairBridge's Reg E obligations to consumers — these are parallel obligations. FairBridge must eat losses from its own reserve when Stripe finalizes a dispute that Reg E requires crediting. Expected loss rate: ~0.1-0.2% of transaction volume (~$150-300/month at 1,000 monthly debits averaging $150).

### [10] External Payment Tracking — Zero Regulatory Burden

Logging payments made via external channels (Venmo, Zelle, check, cash) with two-party confirmation involves zero money movement through the platform. No MTL, no Nacha, no Reg E, no BSA/AML obligations apply. This feature provides court-documentation value at zero compliance cost and is the fallback that keeps payer engagement alive while payee completes bank linking.

### [11] Hash Chain Immutability — Cannot Be Backfilled

The angel investor initially recommended deferring the hash chain to V2, then conceded post-debate: *"The SHA-256 hash must be created at record write time or it doesn't exist. You cannot backfill integrity onto V1 records in V2. This means your earliest, longest-tenured users — highest escalation risk, longest paper trail — would have permanently second-class evidence."* Implementation: SHA-256 hash per record at write time (computationally free), daily Merkle root to a public log (free). ~2-3 weeks of backend work. PKI/X.509 and RFC 3161 timestamping deferred to V2.

### [12] Panel Legal Findings — Items Removed from MVP

UCCJEA jurisdiction display (R5.3): Displaying "which state's order controls" is a legal conclusion. Panel divorce lawyer flagged as **unauthorized practice of law** — if the app gets it wrong, it creates an exhibit for opposing counsel. Replaced with factual data only (residence states, order issuing state). NLP memo filtering: Family court practitioners have documented the shift to coded hostile language — "per our agreement," passive-aggressive affirmations, emoji-based hostility. NLP catches explicit hostility but misses coded language, creating false security.

### [13] Mobile Platform Constraints

Android notification reliability: ~35-40% of Android devices run custom OEM skins (Samsung One UI, Xiaomi MIUI, Oppo ColorOS) with aggressive background process killing that blocks FCM delivery even for high-priority messages. Source: Android developer panelist, corroborated by dontkillmyapp.com device database. App Store / Play Store: Google Play Financial Services policy requires declaration + extended review (4-6 weeks vs. standard 2-3 days). iOS subscription must be web-only purchase to avoid Apple's 30% IAP commission on the $7/mo subscription.

### [14] Nacha PURCHASE Label Rule (March 2026)

Nacha's rule effective March 20, 2026 requires WEB debit entries for *"online purchase of physical or digital goods"* to use the Company Entry Description "PURCHASE." Whether expense reimbursements between co-parents qualify as "purchases" is ambiguous. Stripe documentation: [docs.stripe.com/payments/ach-direct-debit/nacha-purchase-rule](https://docs.stripe.com/payments/ach-direct-debit/nacha-purchase-rule).

### [15] Stripe Webhook Events — Required Handlers

Critical ACH webhook events: `payment_intent.created`, `payment_intent.processing`, `payment_intent.succeeded`, `payment_intent.payment_failed`, `charge.dispute.created` (starts Reg E 10-day clock), `charge.dispute.updated`, `charge.dispute.closed`, `customer.updated`, `account.updated` (Connect), `account.application.deauthorized`. All handlers must be idempotent (check `webhook_events` table for `stripe_event_id` before processing). Dead-letter queue required: BullMQ with 5 retries + exponential backoff. Missing `charge.dispute.created` is existential — Reg E clock ticks whether you know about it or not. Daily reconciliation against Stripe API as backup.

---

## Related Documents

- `initial_spec.md` — full spec (pre-MVP scoping)
- `Spec-Review-Panel-Report.md` — 7-expert panel review findings
- `Stripe-Connect-Nacha-TPS-Analysis.md` — Nacha TPS analysis with Stripe sources
- `Money-Transmission-License-Analysis.md` — MTL exemption analysis with federal/state sources
- `market-research.md` — market research and competitive landscape
- `Fraud-Risk-Analysis.md` — adversarial fraud deep dive
