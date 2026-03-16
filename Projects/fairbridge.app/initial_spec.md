# FairBridge.app — Initial Implementation Spec

**Last Updated**: 2026-03-16
**Status**: Draft

---

## Product Summary

FairBridge is a co-parenting coordination app focused on expense tracking, reimbursement payments, and custody scheduling. It is NOT a full OFW replacement — it targets cooperative (non-court-ordered) parents who need financial coordination and schedule management. Communication is handled by partner app BestInterest.

---

## Implementation Requirements

### R1: Payment Architecture

#### R1.1: Stripe Connect Integration
- MUST use Stripe Connect with Express accounts and platform-held negative balance liability
- Platform operates under Stripe's money transmitter licenses — no separate MTL required
- MUST comply with Stripe's Terms of Service and Restricted Businesses list at all times
- MUST frame all payments as **expense reimbursements tied to documented expenses** — never as arbitrary P2P transfers
- Every payment MUST be linked to a specific expense record (receipt, description, category)
- MUST require every in-app payment to be linked to a documented expense record (receipt, description, category). No "send arbitrary amount" feature — this is what keeps the app in reimbursement-platform territory vs. money-transmitter territory.
- Marketing CAN reference child support and spousal maintenance as use cases for TRACKING (external payment logging, Plaid detection). The constraint is on the payment ARCHITECTURE (every ACH transfer must have a linked expense), not on marketing language.
- Stripe handles KYC/AML for connected accounts via Stripe Identity (government ID + selfie liveness detection)

#### R1.2: Transaction Limits
- No per-expense cap (Stripe/Nacha don't impose one; OFW has none)
- No monthly reimbursement cap (OFW has none)
- Minimum transaction amount: $5.00 (anti-harassment measure — see R4.5)
- First 6 payments: $2,500/week limit (fraud ramp-up period, consistent with OFW/Dwolla model)
- After 6 successful payments: $5,000/week limit
- Weekly ramp-up is a fraud control measure, not an artificial restriction — OFW implements the same pattern via Dwolla

#### R1.3: ACH Processing Rules
- Use Stripe ACH Direct Debit: 0.8% per transaction, capped at $5
- ACH settlement: 3-4 business days standard — no additional hold beyond normal settlement. The ACH settlement period itself serves as the review window. OFW does not add extra holds.
- Failed ACH fee: $4 per failure
- ACH dispute fee: $15 per dispute (final — no appeal on Stripe)
- MUST store authorization evidence for every debit: IP address, timestamp, device fingerprint, user confirmation action
- ACH disputes are FINAL on Stripe with zero appeal — design all flows assuming disputes cannot be contested

#### R1.4: Nacha Compliance (Third-Party Sender)
- MUST register as Third-Party Sender (TPS) with ODFI
- MUST implement fraud monitoring per Nacha Phase 1 (March 20, 2026) and Phase 2 (June 22, 2026)
- MUST monitor unauthorized return rate — stay below 0.5% threshold (return codes R05, R07, R10, R29, R51)
- MUST monitor administrative return rate — stay below 3%
- MUST monitor overall return rate — stay below 15%
- MUST conduct annual Rules Compliance Audit by December 31 each year
- MUST retain audit documentation for 6 years
- At 750 monthly debits, just 4 unauthorized returns hits the 0.5% threshold — design aggressively to prevent

#### R1.5: Regulation E Compliance
- MUST honor all consumer ACH disputes within the 60-day window from statement date
- MUST NOT penalize consumers for exercising dispute rights
- MUST provide clear authorization language before each ACH debit
- Consumer has zero liability for unauthorized transfers reported within 60 days

---

### R2: Expense Tracking and Documentation

#### R2.1: Expense Submission
- Every expense MUST include: amount and description. Date defaults to today if not provided. Category is optional (OFW doesn't force category selection).
- Receipts OPTIONAL but encouraged — support photo upload (camera + gallery), PDF upload, and screenshot upload
- The two-party confirmation workflow is the primary fraud check (payee can dispute), not mandatory receipts
- Expenses with receipts attached get a "documented" badge in court exports (incentivizes receipts without forcing them)
- All uploads stored as immutable, timestamped records (append-only — no edit/delete)

#### R2.2: Two-Party Confirmation Workflow
- Payer submits expense with receipt → Payee receives notification
- Payee can: Approve, Dispute (with explanation), or Mark as Paid (external payment)
- Confirmations are IRREVERSIBLE — warn users before confirming
- No response timeout — expenses stay pending until payee acts. The pending status itself is useful court documentation (matches OFW behavior).
- All actions timestamped server-side (not client-side)

#### R2.3: External Payment Tracking
- Support logging of payments made via external channels (Venmo, Zelle, check, cash, bank transfer)
- Payer logs: amount, date, payment method, optional screenshot/receipt
- Payee receives confirmation request
- Two-party confirmed external payment = strong court evidence
- This feature has ZERO regulatory burden (no money movement)

#### R2.4: Plaid Read-Only Bank Feed (Phase 2)
- Read-only data aggregation via Plaid Transactions API is NOT money transmission — no MTL required
- Phase 2a: One-sided Plaid — payer connects bank, app auto-detects outgoing payments matching configured criteria
- Phase 2b: Two-sided Plaid — both parents connected, automatic matching of outflow (payer) + inflow (payee)
- Plaid cost: ~$1.50/user/month, ~$500/month minimum
- Plaid provides up to 24 months of categorized, read-only transaction data
- Real-time webhook notifications for new transactions
- FIRST co-parenting app to implement automatic bank-feed payment detection

---

### R3: Court-Admissible Record Architecture

#### R3.1: Immutability Requirements
- ALL records (expenses, payments, confirmations, disputes, messages) are append-only
- No edit or delete capability for any user, including platform admins
- Server-side timestamps on all records (UTC, displayed in user's timezone)
- Every record gets a unique authentication code (verifiable against server)

#### R3.2: Certified Exports
- PDF exports with digital signatures
- Unique verification URL per export (third party can verify authenticity)
- Export includes: full transaction history, timestamps, both parties' actions, authentication codes
- CSV export for raw data (free tier)
- Court-formatted PDF reports (paid tier)

#### R3.3: Evidence Standards
- Records must satisfy FRE 803(6) business records exception: made in regular course of business, by person with knowledge, at/near time of event
- Platform MUST be able to provide records custodian affidavit if subpoenaed
- Build subpoena response process from day one
- MUST NOT guarantee "court admissibility" in marketing — admissibility is judge-specific. Instead: "court-ready records with unalterable timestamps and digital signatures"

---

### R4: Fraud Prevention

#### R4.1: Account Security
- Invite-only pairing: Parent A signs up, invites Parent B by email/phone
- Bank account linking via Stripe's native verification: microdeposits (free, 1-2 business days) or Stripe Financial Connections for instant verification. No separate Plaid contract needed. Stripe Identity (gov ID + selfie) available as optional upgrade, not required.
- No court order / parenting plan upload required (OFW doesn't require this; many cooperative parents don't have formal orders)
- 2FA available and encouraged, not mandatory (matches OFW)
- No cooling-off period for bank account changes (OFW doesn't have one). Alert both parties on any bank account change — notification is sufficient.
- Alert both parties on any sensitive account changes

#### R4.2: Expense Fraud Detection
- AI receipt verification (Veryfi, Taggun, or similar) — current detection accuracy >90% for manipulated receipts, 97.5% for AI-generated images
- Duplicate receipt detection via perceptual hashing
- Cross-reference expense amounts against known cost ranges (e.g., copay $20-75, not $500)
- Flag round-number expenses ($100, $200, $500 exactly) — correlate with fabricated claims
- Flag expenses submitted within 24 hours of hostile communication events

#### R4.3: Adversarial Behavior Detection
- Track dispute rate per co-parent pair — alert at 2+ disputes/month
- Monitor ACH returns: >1 unauthorized return (R07/R10) per parent per quarter triggers review
- Detect velocity anomalies: sudden spike in expense submissions or disputes
- NLP filtering on payment memo fields — block hostile language, log for court record
- If parent files >2 unauthorized ACH claims: suspend their ACH debit capability, require credit-push (they send money) instead

#### R4.4: Dispute Resolution Workflow
```
Expense submitted
  → Peer review (other parent approves/disputes — no timeout)
      → If disputed: explanation + counter-evidence exchange (5-day window)
          → If unresolved, escalation options:
              a) Platform AI-assisted review (expenses <$200)
              b) Professional review (flagged for linked attorney/mediator)
              c) Court record export (documented dispute for legal proceedings)
```

#### R4.5: Micropayment Harassment Prevention
- Minimum transaction amount: $5.00 (prevents micropayment harassment — repeated tiny expense submissions are a known coercive control tactic in co-parenting apps)
- No daily rate limits on expense submissions or payment requests (OFW has none — can be added later if abuse patterns are observed)
- Memo field character limit and content filtering

---

### R5: Custody Scheduling

#### R5.1: Shared Calendar
- Support common custody patterns (2-2-5-5, 2-2-3, week-on-week-off, custom)
- Visual calendar with color-coded parent time
- Parenting time percentage calculator
- Sync to Google Calendar, Outlook, Apple Calendar (export)
- Holiday and school break schedule overlay

#### R5.2: AI Schedule Swap Detection (Differentiator)
- Monitor messaging (if integrated with BestInterest) or in-app notes for schedule change agreements
- Detect when parents agree to swap days/weekends
- Auto-suggest calendar update based on detected agreement
- Both parents must confirm the swap for it to take effect
- All swap requests and confirmations logged as immutable records

#### R5.3: Jurisdiction Tracking
- Track which state's court order governs the custody arrangement
- Track current state of residence for each parent
- Flag when a parent relocates (address change) — surface UCCJEA implications
- Display which state's order controls in the app UI

---

### R6: Interstate Compliance

#### R6.1: Data Privacy
- Build to California CCPA/CPRA standard as baseline for ALL users regardless of state
- Privacy policy with all CCPA-required disclosures
- Consumer rights: access, deletion, correction, opt-out of sale/sharing
- Treat ALL children's data as sensitive personal information
- Data minimization for children's data (collect only what's needed)
- 20 states have comprehensive privacy laws as of 2026 — CCPA baseline covers all

#### R6.2: Recording Consent (if call features added)
- 13 states require all-party consent: CA, CT, DE, FL, IL, MD, MA, MI, MT, NV, NH, PA, WA
- If call recording is ever added: MUST require explicit opt-in before every recorded call (TalkingParents model)
- Display clear recording notification in UI
- Store consent records as part of the immutable record

#### R6.3: Court Record Portability
- Export formats must work across all state courts
- Do NOT guarantee admissibility — state evidence rules vary
- Build strong evidence integrity: immutable, timestamped, digitally signed, unique auth codes
- Maintain documented subpoena response process

#### R6.4: Governing Law
- Choose single governing state law for Terms of Service (incorporation state)
- Explicit disclaimer: app does not provide legal advice
- Payment disclaimer: expense reimbursement feature is not a substitute for court-ordered payment channels (wage garnishment, SDU)

---

### R7: Pricing Architecture

#### R7.1: Tier Structure (Proposed)
- **Free tier**: Expense logging, external payment tracking (manual entry + two-party confirmation), basic calendar, CSV exports. MANDATORY to solve the two-party adoption problem — one parent can start free and invite the other.
- **Paid tier ($5-10/mo per parent)**: In-app ACH payments via Stripe, AI expense categorization, court-formatted PDF exports, Plaid bank feed integration, priority support.
- **Family tier (annual)**: Covers both parents at discount.

#### R7.2: Pricing Constraints
- MUST undercut OFW ($12.50-25/mo) by 50%+
- MUST have a free tier (OFW has none, TalkingParents gates mobile behind paywall)
- Payment margin target: 75%+ gross margin on ACH feature (Stripe costs ~$19-24/yr for 24 payments at $200 avg)

---

### R8: Integration Architecture

#### R8.1: BestInterest Partnership
- FairBridge handles: scheduling, expenses, payments, financial records
- BestInterest handles: communication, AI coaching (Message Shield, Tone Guardian), Solo Mode
- Integration approach TBD: API-level embedding vs. deep linking vs. co-marketing
- Revenue share model TBD

#### R8.2: Professional Accounts
- Free read-only accounts for attorneys, mediators, parenting coordinators
- Professionals can view: expense history, payment records, calendar, dispute log
- Either parent can connect a professional; the other parent is notified (matches OFW model — requiring both-parent approval lets one parent block professional oversight)
- Court-formatted report generation for professionals
- This is table stakes — OFW's practitioner dashboard is a key driver of lawyer adoption

---

## Key Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| ACH dispute abuse (vindictive parent reverses payments) | HIGH | Authorization evidence, suspension after 2 unauthorized returns, credit-push fallback |
| Nacha 0.5% unauthorized return threshold | HIGH | Aggressive fraud detection, ramp-up limits, account suspension triggers |
| Fabricated receipts (14% AI-generated in 2025) | MEDIUM | AI receipt verification (>90% accuracy), perceptual hashing, cost range checks |
| Both parents must adopt (two-party problem) | HIGH | Generous free tier, one parent can start solo, external payment tracking works without payee signup |
| Stripe classifies app as high-risk | MEDIUM | Frame as expense reimbursement marketplace, not P2P payments. Precedent: OFW, DComply, AppClose all operate |
| Court admissibility challenged | LOW | Strong evidence integrity (immutable, timestamped, signed) — cannot guarantee but can make exclusion very difficult |

---

## Related Documents

- `Competitive-Landscape-and-Distribution.md` — full market analysis
- `Partnership-Strategy-BestInterest.md` — BestInterest partnership thesis
- `Interstate-Legal-Complexities.md` — interstate regulatory analysis
- `Payment-Tracking-Approaches.md` — 7 payment tracking methods ranked
- `Fraud-Risk-Analysis.md` — adversarial fraud deep dive
- `Market-Research-Brief.md` — original market research (2026-03-15)
- `market-research.md` — final composed market research
