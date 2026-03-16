# Your Two Users Might Be Trying to Destroy Each Other: Fraud Risks in a Co-Parenting Payment App

**Research Brief** | March 16, 2026 | Researcher: Claude Opus 4.6

---

## Executive Summary

A co-parenting expense reimbursement app faces a fraud risk profile unlike any other fintech product: its two users may be actively adversarial. While Venmo loses an estimated $725M annually to fraud across hundreds of millions of transactions at a sub-0.1% rate, a co-parenting app concentrates every known P2P fraud vector into a two-person relationship where 10-20% of cases involve high-conflict dynamics -- parents who have litigated for years at $15,000-$30,000 per custody modification. The most dangerous risk is not external hackers or identity thieves but "weaponized payments" -- legitimate-seeming app usage designed to harass, financially control, or build a court case against the other parent, exploiting the fact that nearly 99% of domestic abuse cases involve financial abuse. ACH Direct Debit compounds this: disputes are final with no appeal process, Stripe charges a $15 fee per dispute regardless of outcome, and consumers have a 60-day window to claim any debit was unauthorized -- meaning a vindictive co-parent could reverse months of legitimate payments with zero recourse for the platform. The good news: Stripe Radar now covers ACH with machine learning models that reduced ACH fraud 20% across early adopters, and the app's closed two-party structure (both users are known, identity-verified, and linked by a court order) creates natural fraud constraints that open marketplaces lack. The mitigation strategy must treat the adversarial co-parent as the primary threat model, not the anonymous internet fraudster.

---

## The Adversarial User: A Threat Model Unique to Co-Parenting

### Why This App's Fraud Profile Is Fundamentally Different

Traditional P2P and marketplace fraud assumes anonymous or semi-anonymous parties. A co-parenting app inverts this: both parties are fully identified, legally bound by a court order, and potentially motivated by spite rather than financial gain. The Kids First Center documents that financial abuse in co-parenting manifests as withholding child support, canceling shared accounts, and filing unnecessary legal motions to drain the other parent's resources [1].

This creates six distinct adversarial fraud patterns that conventional fraud detection systems are not designed to catch:

**1. Fabricated or Inflated Expense Submissions**
A parent submits receipts for expenses that never occurred, were for personal use, or had amounts inflated. In 2025, 14% of fraudulently submitted receipts were AI-generated using tools like ChatGPT, DALL-E, and Midjourney to produce pixel-perfect PDF replicas [2]. A co-parent with access to consumer AI tools can generate convincing receipts for children's medical visits, tutoring, or extracurricular activities that never happened. Unlike employee expense fraud (where the employer can audit against payroll records), the other parent has limited ability to independently verify whether an expense occurred.

**2. Strategic Dispute Weaponization**
A parent systematically disputes every legitimate expense submission, regardless of merit, to delay reimbursement and force the submitting parent into a financial squeeze. This mirrors the litigation pattern where abusers file "unnecessary motions, refuse to negotiate, or miss deadlines" to increase costs [1]. DComply's current dispute workflow -- where the disputing party provides an explanation and the sender responds -- has no mechanism to penalize systematic bad-faith disputes [3].

**3. Duplicate Expense Submission**
Submitting the same expense through multiple channels (once via the app, once via text/email demanding separate payment) or submitting the same receipt twice with minor modifications. AI receipt generation makes this easier to disguise.

**4. Payment Harassment via Micropayments**
Sending trivially small payments ($0.01, $0.69, $1.00) with hostile descriptions in the memo field. This is the digital equivalent of the documented pattern where abusers use financial transactions as a vector for continued contact and control [1]. At ACH transaction costs of $0.80 per debit (Stripe's standard rate, capped at $5), micropayment harassment would be cheap for the harasser but create real operational costs for the platform.

**5. ACH Dispute Abuse (Authorized Payment Reversal)**
After making a legitimate payment, a parent contacts their bank within the 60-day Regulation E window and claims the debit was unauthorized (return code R10). Under EFTA, the consumer has zero liability for unauthorized transfers reported within 60 days [4]. ACH disputes on Stripe are final with no appeal process -- the platform cannot submit evidence or contest the reversal [5]. The vindictive parent gets their money back, the receiving parent loses the funds, and the platform eats a $15 dispute fee. Unlike credit card chargebacks (where merchants win 45% of disputes), ACH disputes have a 0% merchant win rate on Stripe.

**6. Impersonation and Account Manipulation**
Creating a fake account pretending to be the co-parent, or gaining access to the co-parent's account to submit fraudulent expenses or authorize payments. In high-conflict divorces, parents may have extensive knowledge of each other's personal information (SSN, date of birth, prior addresses) that would pass basic identity verification.

### Quantifying the Adversarial Risk

| Risk Factor | Metric | Source |
|------------|--------|--------|
| High-conflict co-parenting households | 10-20% of all cases | Family court data [6] |
| Domestic abuse cases involving financial abuse | ~99% | Kids First Center [1] |
| DV survivors with $10K+/year coerced debt | >50% | Kids First Center [1] |
| P2P users targeted by scams | 17% | DFPI study [7] |
| Friendly fraud as % of all chargebacks | 70-79% | Chargeflow 2025 [8] |

The intersection of these factors suggests that a co-parenting payment app serving the high-conflict segment could see adversarial fraud attempt rates 10-50x higher than a general-purpose P2P app, though individual transaction values ($50-$2,000/month) limit absolute dollar exposure.

---

## ACH Direct Debit: Powerful but Asymmetrically Risky

### How ACH Disputes Actually Work (And Why They Favor the Payer)

ACH Direct Debit is structurally tilted toward the consumer (payer) in ways that create serious risk for a platform intermediating payments between two known parties.

**The Timeline Problem:**
- Consumer (personal account): 60 calendar days to dispute from statement date [4]
- Business account: 2 business days to dispute [5]
- Microdeposit verification: 10-day window for account confirmation [5]
- ACH settlement: 3-4 business days from initiation [3]

**The Finality Problem:**
All ACH Direct Debit disputes on Stripe are final. There is no evidence submission process, no appeal, and no arbitration [5]. This is fundamentally different from credit card chargebacks where merchants win 45% of cases and can submit compelling evidence [8]. For ACH, the only recourse is to resolve the dispute directly with the customer -- which, in a co-parenting context, means asking two potentially hostile parties to work it out.

**The Cost Problem:**
- Stripe ACH Direct Debit fee: 0.8% of transaction, capped at $5 [9]
- Failed ACH payment fee: $4 [9]
- ACH dispute fee: $15 (regardless of outcome) [9]
- For a $200 expense reimbursement that gets disputed: platform loses $200 + $15 fee = $215

### Nacha Compliance: The Third-Party Sender Question

If the platform initiates ACH debits on behalf of one parent to pay the other, it likely qualifies as a Third-Party Sender (TPS) under Nacha rules. This triggers significant compliance obligations effective in 2025-2026 [10]:

| Requirement | Deadline | Detail |
|------------|----------|--------|
| TPS Registration | Already in effect | ODFI must register all TPSs with Nacha; requires name, location, routing number, Company ID |
| Annual Rules Compliance Audit | December 31 each year | Must retain documentation for 6 years |
| Fraud Monitoring (Phase 1) | March 20, 2026 | Large originators/TPSs must implement risk-based fraud detection processes |
| Fraud Monitoring (Phase 2) | June 22, 2026 | ALL originators/TPSs must implement fraud monitoring |
| Unauthorized Return Rate | Ongoing | Must stay below 0.5% (return codes R05, R07, R10, R29, R51) |
| Administrative Return Rate | Ongoing | Must stay below 3% |
| Overall Return Rate | Ongoing | Must stay below 15% |

**Critical threshold**: The 0.5% unauthorized return rate means that for every 1,000 ACH debits, no more than 5 can be returned as unauthorized. In a co-parenting app with, say, 500 active households making 1-2 payments per month (750 debits/month), just 4 vindictive parents filing unauthorized claims would put the platform at the threshold. Exceeding it can result in Nacha enforcement actions against the ODFI, who may then terminate the platform's ACH access entirely [10].

### ACH Return Codes That Matter Most

| Code | Meaning | Risk to Platform | Timeframe |
|------|---------|-----------------|-----------|
| R01 | Insufficient funds | Low -- retry possible | 2 days |
| R02 | Account closed | Low -- account deactivation | 2 days |
| R03 | No account/unable to locate | Low -- bad data | 2 days |
| R07 | Authorization revoked | HIGH -- consumer revoked mandate | 60 days |
| R08 | Payment stopped | Medium -- one-time stop | 2 days |
| R10 | Customer advises unauthorized | HIGHEST -- counts toward 0.5% threshold | 60 days |
| R29 | Corporate customer advises not authorized | HIGH -- business accounts | 2 days |

R07 and R10 are the weaponizable codes. A co-parent who authorized a payment can later contact their bank and claim it was unauthorized (R10) or that they revoked authorization (R07). Both trigger the 60-day window, both are final on Stripe, and both count toward the Nacha unauthorized return rate threshold [10].

---

## What Stripe Connect Handles vs. What You Must Handle

### Stripe's Automatic Protections

| Protection | Coverage | Limitation |
|-----------|----------|-----------|
| **Stripe Radar for ACH** | ML models assess 1,000+ signals per transaction in <100ms; 20% ACH fraud reduction [11] | Trained on general payment patterns, not adversarial co-parenting dynamics |
| **KYC/Identity Verification** | Stripe collects and verifies identity documents, SSN, address for connected accounts [12] | Confirms identity is real, not that the person is who they claim to be in your app's context |
| **Sanctions Screening** | OFAC and international sanctions checks; auto-pauses payouts for flagged accounts [13] | Irrelevant to co-parenting fraud |
| **Bank Account Verification** | Plaid instant verification or microdeposits to confirm account ownership [5] | Confirms bank account exists, not that it belongs to the right co-parent |
| **Dispute Handling** | Automatic debit of disputed amounts from connected account or platform balance [14] | ACH disputes are final -- no appeal, no evidence submission |

### What You Must Build

| Risk | Your Responsibility | Why Stripe Cannot Help |
|------|-------------------|---------------------|
| **Adversarial expense fraud** | Receipt verification, expense policy enforcement, dispute mediation | Stripe processes payments, not expense claims |
| **Payment harassment** | Memo field filtering, minimum transaction amounts, rate limiting | Stripe has no concept of "hostile payment" |
| **Weaponized ACH disputes** | Authorization evidence collection, direct resolution with users, potential legal hold | ACH disputes are final on Stripe |
| **Impersonation within app** | Invite-only onboarding, court order verification, co-parent identity linking | Stripe verifies identity exists, not relationship context |
| **Duplicate expense detection** | Receipt deduplication, cross-channel tracking | Application-layer logic |
| **Systematic dispute abuse** | Bad-faith dispute tracking, escalation to mediator/court | Application-layer behavior analysis |

### Platform Liability Model

For a co-parenting app using Stripe Connect, the liability model depends on the account type [14]:

**If platform takes negative balance liability (Custom/Express accounts):**
- Platform pays for all disputes, chargebacks, and negative balances on connected accounts
- Platform can pause payouts, debit connected accounts, and set reserves
- Stripe debits connected account first, then platform balance if insufficient

**If Stripe takes negative balance liability (Standard accounts):**
- Stripe manages payments risk but connected accounts get full Stripe Dashboard access
- Less control over the user experience
- Stripe may freeze or close connected accounts independently

**Recommendation for co-parenting app:** Use Express accounts with platform-held liability. The transaction values are small ($50-$2,000/month) so absolute exposure is limited, but you need maximum control over the payment flow to implement co-parenting-specific fraud rules. Stripe recommends new platforms let Stripe take liability unless "confident in their ability to manage merchant risk" [13] -- for a co-parenting app, you understand the risk better than Stripe's generic models do.

---

## Lessons from P2P and Marketplace Platforms

### P2P Payment Fraud: The Numbers

The P2P payment fraud landscape provides useful benchmarks, though co-parenting apps face structural differences [7][15]:

| Platform | Fraud Rate | Key Fraud Type | Recovery Rate |
|----------|-----------|---------------|---------------|
| Zelle | <0.1% of transactions | Authorized push payment fraud | Banks reimburse 38% (down from 62% in 2019) |
| Venmo/Cash App | UNKNOWN (not published) | Account takeover, impersonation | Unauthorized only; authorized push = no refund |
| All P2P apps (FTC) | 90,571 reports in 2024 (2x YoY) | Impersonation, purchase scams | 90% of instant payment fraud cases not refunded |

**US authorized push payment fraud reached $8.3B in 2024**, growing at 95% annualized between 2020-2024, projected to reach $14.9B by 2028 [15]. However, the vast majority involves strangers -- investment scams ($4.6B) and imposter scams ($2.5B). Co-parenting fraud would be categorized as "authorized" because both parties genuinely intend to use the platform; the fraud is in the expense claims, not the payment authorization.

### Marketplace Dispute Resolution Models

| Platform | Approach | Relevance |
|----------|----------|-----------|
| **Airbnb** | AI behavior analysis + risk scoring for new accounts; platform mediates host-guest disputes with 72-hour resolution window; detected and removed 3,200+ phishing domains in 2024 [16] | Two-party relationship model is closest analog to co-parenting |
| **DoorDash** | Two-step verification for ownership changes; real-time monitoring with risk signals; merchants dispute errors through portal with hours-level resolution [17] | Rapid automated dispute resolution is applicable |
| **DComply** | Peer dispute workflow: recipient disputes with explanation, sender responds, no automated mediation or AI review [3] | Direct competitor; minimal fraud protection |

**Key insight from Airbnb:** The most successful dispute resolution in two-party platforms combines (1) a mandatory cooldown period before disputes escalate, (2) AI-based damage claim verification (Airbnb uses image analysis), and (3) a platform-mediated resolution step with human review for claims above a threshold. Airbnb's model of detecting "AI-generated fake damage claims" using image analysis directly parallels the co-parenting receipt fraud problem [16].

### Chargeback Economics for Low-Value Transactions

For transactions in the $50-$2,000 range, chargeback economics are unfavorable [8]:

- Average chargeback fee: $10-$50 per dispute (Stripe charges $15 for ACH)
- Total cost per chargeback: $3.35 for every $1 in dispute value (including admin costs)
- Merchant win rate drops to 27.64% for transactions over $300 (card chargebacks; ACH = 0%)
- Industry chargeback rate for financial services: 0.55%

For a $200 co-parenting expense reimbursement that gets disputed:
- Transaction revenue to platform: ~$1.60 (0.8% ACH fee)
- Dispute cost: $15 fee + $200 reversed + admin time
- **Net loss: ~$214 per disputed transaction**

This means a single fraudulent dispute wipes out the revenue from 134 successful transactions. With margins this thin, even a 1% dispute rate would make the payment processing unprofitable.

---

## Identity Fraud: Constrained but Not Eliminated

### The Closed-Loop Advantage

Unlike open marketplaces, a co-parenting app has a structural advantage: both users are known and linked. The app can require:

1. **Invite-only pairing**: Parent A signs up and invites Parent B by email/phone. Both must verify identity through Stripe Identity (government ID + selfie). Neither can use the payment feature until both are verified and linked.
2. **Court order upload**: Requiring a court order or parenting plan that names both parties provides a cross-reference against Stripe's KYC data.
3. **Professional attestation**: OFW allows attorneys, mediators, and judges to connect to a family's account with permission-controlled visibility [18]. A similar model creates a third-party identity anchor.

### Residual Identity Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Ex-spouse creates account pretending to be the other parent | Low (Stripe Identity requires government ID + selfie match) | High (could authorize payments from other parent's bank) | Require both parties to independently verify; cross-check names against court order |
| Account takeover (ex-spouse knows passwords, security questions) | Medium (intimate partners know each other's information) | High (could approve expenses, change bank details) | Mandatory 2FA; alert on bank account changes; cooling-off period for sensitive changes |
| Child or family member used as proxy | Low | Medium | Age verification; single account per role per family unit |

Stripe Identity's verification process -- which includes government-issued ID scanning and liveness detection (selfie matching) -- handles the heavy lifting [12]. The platform's job is to ensure the verified identity matches the person named in the co-parenting relationship, which Stripe cannot assess.

---

## Mitigation Strategy: Defense in Depth for Adversarial Users

### Tier 1: Structural Controls (Prevent Fraud by Design)

**Payment Architecture:**
- Use Stripe Connect with Express accounts and platform-held liability [KNOWN -- Stripe documentation]
- Set minimum transaction amount at $5.00 to prevent micropayment harassment [ASSUMED -- no industry standard exists]
- Cap individual expense submissions at the lesser of $2,000 or the agreed monthly reimbursement amount [ASSUMED]
- Implement a 48-72 hour hold on ACH debits before settlement to allow dispute/review window [KNOWN -- ACH settlement is 3-4 business days anyway]
- Store ACH authorization evidence (IP address, timestamp, device fingerprint, user confirmation screenshot) to support out-of-band dispute resolution even though Stripe disputes are final [KNOWN -- Stripe best practice]

**Account Architecture:**
- Invite-only pairing with dual Stripe Identity verification [KNOWN -- Stripe Identity available]
- Court order / parenting plan upload with name cross-referencing [ASSUMED -- no competitor does this today]
- Mandatory 2FA for both parents [KNOWN -- Stripe best practice]
- 72-hour cooling-off period for bank account changes [ASSUMED]
- Professional account linking (attorney, mediator, GAL) with read-only access [KNOWN -- OFW model]

### Tier 2: Detection Controls (Catch Fraud in Progress)

**Expense Claim Validation:**
- AI receipt verification using services like Veryfi, Taggun, or DetectX -- current detection accuracy exceeds 90% for manipulated receipts and 97.5% for AI-generated images [2]
- Duplicate receipt detection via perceptual hashing (detect near-identical images regardless of format/resolution changes)
- Cross-reference expense amounts against known cost ranges (e.g., pediatrician copay should be $20-$75, not $500)
- Flag expenses submitted within 24 hours of a hostile communication event (message with negative sentiment)
- Require receipts for all expenses above $25; mandate merchant name, date, and itemized list

**Payment Pattern Monitoring:**
- Track dispute rate per co-parent pair; alert at 2 disputes/month (well below Nacha's 0.5% unauthorized threshold but indicative of adversarial behavior)
- Monitor for ACH return patterns: more than 1 unauthorized return (R07/R10) per parent per quarter triggers review
- Detect velocity anomalies: sudden spike in expense submissions or disputes
- Flag round-number expenses (exactly $100, $200, $500) which correlate with fabricated claims in expense fraud data [19]

### Tier 3: Response Controls (Resolve and Recover)

**Dispute Resolution Workflow:**

```
Expense submitted → Peer review (other parent approves/disputes)
                         ↓ (if disputed)
                   Explanation + counter-evidence exchange (5-day window)
                         ↓ (if unresolved)
                   Escalation options:
                     a) Platform mediation (AI-assisted review for expenses <$200)
                     b) Professional review (flagged for linked attorney/mediator)
                     c) Court record export (documented dispute for legal proceedings)
```

**ACH Dispute Response (Since Stripe Disputes Are Final):**
1. Maintain comprehensive authorization records (mandate acceptance, IP, device, timestamp)
2. When a parent files an R10 (unauthorized), immediately flag the account and notify both parties
3. Provide authorization evidence to the claiming parent's bank directly (outside Stripe) -- while ACH disputes are final on Stripe, banks may reconsider with compelling evidence
4. If a parent files more than 2 unauthorized claims, suspend their ability to receive ACH debits; require credit-push (they send money) instead of debit-pull (app pulls money)
5. Generate court-admissible documentation of the dispute pattern for legal proceedings

**Escalation Triggers:**

| Trigger | Action |
|---------|--------|
| 3+ disputed expenses in 30 days from same parent | Flag for platform review; notify linked professionals |
| Any R10/R07 ACH return | Suspend ACH debit for that parent; require alternative payment |
| Hostile language in payment memos (detected via NLP) | Block memo, notify sender, log for court record |
| Expense submission >2x historical average | Hold for manual review before presenting to other parent |
| Same receipt image submitted twice (perceptual hash match) | Auto-reject with explanation |

### Tier 4: Regulatory Compliance

**Nacha Requirements (2026):**
- Register as Third-Party Sender with ODFI [KNOWN -- required if initiating debits]
- Implement fraud monitoring per Phase 1 (March 20, 2026) and Phase 2 (June 22, 2026) [KNOWN]
- Conduct annual Rules Compliance Audit by December 31 [KNOWN]
- Monitor unauthorized return rate against 0.5% threshold continuously [KNOWN]
- Retain audit documentation for 6 years [KNOWN]

**Regulation E Compliance:**
- Honor all consumer disputes within 60-day window [KNOWN -- federal law]
- Cannot penalize consumers for exercising dispute rights [KNOWN]
- Must provide clear authorization language before each ACH debit [KNOWN]

---

## Gap Analysis

| Category | Finding | Confidence |
|----------|---------|------------|
| **KNOWN** | ACH disputes are final on Stripe with no appeal -- $15 fee per dispute regardless of outcome | Stripe documentation [5] |
| **KNOWN** | Nacha unauthorized return threshold is 0.5%; exceeding it risks ACH access termination | Nacha rules [10] |
| **KNOWN** | Stripe Radar covers ACH with ML models, reducing fraud 20% | Stripe blog [11] |
| **KNOWN** | 14% of fake receipts are now AI-generated (2025 data) | ReceiptGuard [2] |
| **KNOWN** | Stripe Connect platforms with Express accounts bear negative balance liability | Stripe docs [14] |
| **KNOWN** | Consumers have 60 days to dispute ACH debits under Regulation E | CFPB/EFTA [4] |
| **ASSUMED** | Co-parenting apps will see higher adversarial fraud rates than general P2P (10-50x) | Extrapolation from high-conflict divorce data + financial abuse prevalence |
| **ASSUMED** | $5 minimum transaction prevents micropayment harassment effectively | No industry benchmark exists for this specific pattern |
| **ASSUMED** | Court order upload for identity cross-referencing is feasible at scale | No competitor implements this today |
| **UNKNOWN** | Actual ACH dispute rate for co-parenting payment apps | DComply does not publish this data |
| **UNKNOWN** | Whether Stripe would classify a co-parenting app as "high risk" during onboarding | Depends on Stripe's internal risk assessment |
| **UNKNOWN** | Legal enforceability of platform-mediated dispute resolution in family court | Varies by jurisdiction; needs legal review |
| **UNKNOWN** | Whether mandatory arbitration clauses in TOS are enforceable for co-parenting disputes | Intersection of contract law and family law; untested territory |
| **CONTESTED** | Optimal transaction hold period: too short = insufficient review time; too long = cash flow harm to receiving parent | No established best practice for adversarial two-party payments |

---

## Appendix

**[1]** Kids First Center, "Co-Parenting and Financial Abuse" -- https://www.kidsfirstcenter.org/siteglide-blog/co-parenting-and-financial-abuse ; TalkingParents, "What is Financial Abuse?" -- https://talkingparents.com/blog/what-is-financial-abuse ; DVIP Iowa, "Co-Parenting After Abuse" -- https://dvipiowa.org/co-parenting-after-abuse-what-survivors-need-to-know/

**[2]** ReceiptGuard, "2026 Guide to Fake Receipt Checker for Fraud Detection" -- https://www.receiptguard.io/blog/2026-guide-to-fake-receipt-checker-for-fraud-detection ; Veryfi, "AI-Generated Receipts Detection" -- https://www.veryfi.com/technology/ai-generated-receipts-detection/

**[3]** DComply FAQs -- https://www.dcomply.com/faqs/ ; DComply "Track Co-Parenting Expenses" -- https://www.dcomply.com/track-co-parenting-expenses/

**[4]** CFPB Regulation E, Section 1005.6, "Liability of consumer for unauthorized transfers" -- https://www.consumerfinance.gov/rules-policy/regulations/1005/6/ ; Philadelphia Fed, "Error Resolution Procedures and Consumer Liability Limits" -- https://www.consumercomplianceoutlook.org/2012/fourth-quarter/error-resolution-procedures-consumer-liability-limits-unauthorized-electronic-fund-transfers/ ; Nacha, "Which 60 Days is It?" -- https://www.nacha.org/news/which-60-days-it-understanding-different-periods-regulation-e-and-nacha-rules

**[5]** Stripe, "ACH Direct Debit" documentation -- https://docs.stripe.com/payments/ach-direct-debit ; Stripe Support, "Respond to or contest an ACH Direct Debit dispute" -- https://support.stripe.com/questions/respond-to-or-contest-an-ach-direct-debit-dispute-as-a-merchant

**[6]** Co-Parenting Technology Market Research Brief (this vault), March 16, 2026 -- family court data on high-conflict divorces consuming 80% of court time

**[7]** DFPI (California Department of Financial Protection and Innovation), "Tips to avoid peer-2-peer payment scams" -- https://dfpi.ca.gov/news/insights/tips-to-avoid-peer-2-peer-payment-scams/ ; Bank Policy Institute, "Fraud on P2P Payment Apps" -- https://bpi.com/fraud-on-p2p-payment-apps-like-zelle-and-venmo-a-primer/ ; Michael Ryan Money, "Payment Scams Defense Guide 2026" -- https://michaelryanmoney.com/payment-scams-zelle-cash-app-venmo/

**[8]** Chargeflow, "Ultimate Chargeback Statistics 2025" -- https://www.chargeflow.io/blog/chargeback-statistics-trends-costs-solutions ; Chargeback.io, "Chargeback Statistics 2026" -- https://www.chargeback.io/blog/chargeback-statistics ; Chargebacks911, "Chargeback Stats" -- https://chargebacks911.com/chargeback-stats/

**[9]** Stripe ACH Direct Debit pricing -- https://support.stripe.com/questions/ach-direct-debit-pricing ; Stripe fees guide -- https://wise.com/us/blog/stripe-fees ; Swipesum, "Stripe Fees Explained" -- https://www.swipesum.com/insights/guide-to-stripe-fees-rates-for-2025

**[10]** Nacha, "ACH Network Risk and Enforcement Topics" -- https://www.nacha.org/rules/ach-network-risk-and-enforcement-topics ; Nacha, "Third-Party Sender Registration" -- https://www.nacha.org/rules/third-party-sender-registration ; Nacha, "Fraud Monitoring Phase 1" -- https://www.nacha.org/rules/risk-management-topics-fraud-monitoring-phase-1 ; Forth, "ACH Return Rates" -- https://support.forthcrm.com/hc/en-us/articles/12854548866963-ACH-Return-Rates ; Sila Money, "Monitoring Your Return Rates" -- https://www.silamoney.com/ach/monitoring-your-return-rates-things-to-do-to-keep-your-return-codes-low-for-nacha

**[11]** Stripe, "Radar now protects ACH and SEPA payments" -- https://stripe.com/blog/radar-now-protects-ach-and-sepa-payments ; Financial IT, "Stripe Radar Now Protects ACH and SEPA Payments" -- https://financialit.net/news/data-protection/stripe-radar-now-protects-ach-and-sepa-payments-fraud ; Stripe Newsroom -- https://stripe.com/newsroom/news/radar-for-ach-sepa

**[12]** Stripe, "Identity verification for connected accounts" -- https://docs.stripe.com/connect/identity-verification ; Stripe, "KYC requirements for connected accounts" -- https://support.stripe.com/questions/know-your-customer-(kyc)-requirements-for-connected-accounts ; Stripe Identity product page -- https://stripe.com/identity

**[13]** Stripe, "Best practices for risk management" -- https://docs.stripe.com/connect/risk-management/best-practices ; Stripe, "New features to help SaaS platforms manage risk" -- https://stripe.com/blog/new-features-to-help-saas-platforms-manage-risk-and-stay-compliant

**[14]** Stripe, "Risk and liability management with Connect" -- https://docs.stripe.com/connect/risk-management ; Stripe, "Disputes on Connect platforms" -- https://docs.stripe.com/connect/disputes ; Stripe, "Handle refunds and disputes" -- https://docs.stripe.com/connect/saas/tasks/refunds-disputes

**[15]** Chargebacks911, "Push Payment Fraud Statistics" -- https://chargebacks911.com/push-payment-fraud-statistics/ ; FTC fraud report data (90,571 reports in 2024); Zelle fraud data via Consumer Reports -- https://innovation.consumerreports.org/peer-to-peer-services-policies/

**[16]** Autohost, "Airbnb 2025 Policy Changes" -- https://www.autohost.ai/blog/airbnb-2025-policy-changes-pms-impact ; Rental Scale-Up, "AI Airbnb Scams" -- https://www.rentalscaleup.com/ai-airbnb-scams-fake-damage-claims/ ; Privacy.com, "Airbnb Chargeback Process" -- https://www.privacy.com/blog/airbnb-chargeback

**[17]** DoorDash, "Merchant Fraud Protections" -- https://about.doordash.com/en-us/news/merchant-fraud-protections ; DoorDash, "Protecting Merchants and Combating Fraud" -- https://about.doordash.com/en-us/news/protecting-merchants-and-combating-fraud

**[18]** OurFamilyWizard Courts page -- https://www.ourfamilywizard.com/practitioners/courts ; Naro Law, "Co-Parenting Apps: Pros, Cons" -- https://narolaw.co/co-parenting-apps-like-our-family-wizard-pros-cons-and-what-you-should-know/

**[19]** Emburse, "Complete Guide to Expense Fraud Detection" -- https://www.emburse.com/resources/complete-guide-to-expense-fraud-detection ; Bonadio Group, "Expense Reimbursement Fraud" -- https://www.bonadio.com/article/expense-reimbursement-fraud-common-schemes-and-how-to-prevent-them/ ; Ramp, "What is Expense Fraud" -- https://ramp.com/blog/what-is-expense-fraud ; Rydoo, "Expense Fraud 2026" -- https://www.rydoo.com/cfo-corner/expense-fraud-companies/

---

**Research methodology**: 15 web searches across Stripe documentation, Nacha rules, P2P fraud statistics, marketplace dispute resolution, co-parenting app features, receipt fraud detection, and financial abuse literature. 8 deep-page fetches of Stripe docs, DComply FAQ, chargeback statistics, and push payment fraud data. Cross-referenced against existing co-parenting market research in this vault.
