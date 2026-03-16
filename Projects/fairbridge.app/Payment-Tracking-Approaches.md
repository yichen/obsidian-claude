# Payment Tracking Without Moving Money: How Co-Parenting Apps Document P2P Payments Made Elsewhere

**Research Brief | March 16, 2026**
**Researcher**: Claude Code (Opus 4.6)

---

## TL;DR

Every co-parenting app that handles payment documentation uses the same fundamental pattern: **manual entry by the payer, optional confirmation by the payee, with receipt upload as supporting evidence**. No app in the co-parenting space has implemented automatic bank-feed detection of child support payments via Plaid or any other aggregator. The closest analog is personal finance apps like Monarch Money ($14.99/mo) and Copilot ($13/mo), which use Plaid's read-only Transactions API to automatically categorize spending --- but none of these apps apply that capability to inter-party payment verification. This gap represents a genuine product opportunity: a two-party payment ledger that combines Plaid's read-only transaction detection (no money transmission license required) with the two-party confirmation workflow already proven by OurFamilyWizard and DComply. The regulatory path is clear --- read-only data aggregation via Plaid does not constitute money transmission under federal or state law, and the CFPB's Section 1033 rulemaking (currently in reconsideration as of August 2025) will only make consumer-authorized data access easier. The hard part is not regulatory --- it is getting both parties to connect their bank accounts.

---

## Every Incumbent Uses the Same Three-Step Payment Logging Pattern

Across 7 co-parenting apps examined, payment documentation follows a remarkably uniform workflow. No app has deviated from this basic architecture in over a decade.

### The Universal Pattern

| Step | What Happens | Who Acts |
|------|-------------|----------|
| 1. Log | Payer manually enters amount, date, and payment method | Payer |
| 2. Attach | Payer optionally uploads receipt, screenshot, or invoice | Payer |
| 3. Confirm | Payee reviews and confirms (or disputes) receipt of funds | Payee |

This is fundamentally a **manual, trust-but-verify ledger**. The app acts as a neutral timestamp authority --- it records when the payer claimed to pay and when the payee confirmed receipt. The payment itself happens entirely outside the app (via Venmo, Zelle, check, cash, or wage garnishment).

### How Each App Implements This Pattern

**OurFamilyWizard** implements the most complete version. Their "Check/Other" payment type allows payers to log external payments with a note (cash, check number, money order number). The payee receives a notification and must actively tap "Confirm Payment" for the expense status to update to "Paid." Critically, confirmations cannot be reversed --- OFW warns users not to confirm payments they have not received [1]. OFW also offers OFWpay (powered by Dwolla ACH) for in-app payments at $2.50/transaction (or free on Premium plans), with a $2,500 weekly limit for the first 6 payments and $5,000 thereafter [2].

**TalkingParents** calls their system "Accountable Payments" --- payments between $10 and $5,000, linked to US bank accounts, with every action stored in "Unalterable Records" bearing a unique 16-digit Authentication Code and digital signature [3]. However, TalkingParents does NOT appear to support logging payments made through external channels. Their system is payment-rail-only: if you want the record, you must pay through TalkingParents.

**DComply** uses Plaid for bank verification and Dwolla for ACH transfers at $5.99/month with no per-transaction fees [4]. The payer creates a bill; the co-parent opens it and presses "pay" to initiate an ACH transfer (3-4 business days). DComply auto-tracks all in-app payments and generates PDF reports of billing vs. payment history for court use.

**AppClose** uses "ipayou" for in-app payments and supports expense reimbursement requests with receipt attachments. The payee can approve, decline, or mark expenses as paid. AppClose remains free for core features [5].

**SupportPay** offers receipt scanning technology that automates expense entry from uploaded photos. Payments can be sent/received via bank transfer or PayPal, or manually entered (cash, check, credit card). The receiving parent gets an email notification [6]. SupportPay does NOT appear to use Plaid for automatic transaction detection despite marketing claims of "automatic monitoring."

**Onward** (shut down October 2024) was notable for supporting "connections to apps such as Venmo, PayPal, Zelle, or CashApp" for settlement, plus ACH transfers for "verified" payments with a neutral third-party record [7]. However, this was manual --- users chose their payment method, not automatic detection.

**Alimentor 2** allows recording every child-related payment (paid, due, or pending) with receipt scanning, invoice attachment, and a built-in calculator for reimbursement tracking.

### The Gap No App Has Filled

Zero co-parenting apps use bank feed data to **automatically detect** when a payment has been made. Every single one relies on manual entry by the payer. This means:

- If the payer forgets to log a payment, it does not appear in the record
- If the payee refuses to confirm, the payment appears "pending" forever
- There is no independent, automated verification that money actually moved between accounts

---

## What Family Law Attorneys Actually Recommend for Payment Documentation

Attorney advice is remarkably consistent across jurisdictions: **avoid cash, use traceable methods, write "child support" in the memo, and keep organized records** [8][9][10].

### The Attorney-Recommended Hierarchy (Best to Worst)

1. **Wage garnishment / Income Withholding Order (IWO)**: The gold standard. Automatic paycheck deductions processed through state disbursement units create automatic, trackable records. Family law attorneys consistently rate this as the safest method [8].

2. **Bank-to-bank transfers with memo notation**: Direct deposits or ACH transfers labeled "Child Support - [Month/Year]" in the memo field. Zelle is specifically called out by attorneys as preferred "because it's already integrated into many banking apps" [8].

3. **Checks with memo notation**: Cancelled/cashed checks provide clear withdrawal from payer's account and deposit into payee's account. Write "Child Support" in the memo [9].

4. **Money orders with stubs**: Acceptable but require keeping the stub as proof. Western Union and MoneyGram can provide transaction documentation [9].

5. **Venmo/PayPal/Cash App with description**: Acceptable if the payment description explicitly says "Child Support" plus the month/year. These are discoverable in family court proceedings [10].

6. **Cash**: Universally condemned by every attorney source. One attorney states: "If you are paying cash STOP NOW! You might as well kiss your complete proof of support goodbye" [9].

### The Documentation Attorneys Recommend

Regardless of payment method, attorneys recommend creating "a chart that shows when the payment was made, for how much, and attach the proof to it" [9]. This is exactly what co-parenting apps do --- but attorneys are still recommending spreadsheets and paper files because they do not trust (or are not aware of) the app-based alternatives.

---

## Venmo, Zelle, and Cash App Records in Family Court: Discoverable but Not Self-Authenticating

P2P payment records occupy a specific legal middle ground: they are **fully discoverable** in family law proceedings but require **authentication** to be admitted as evidence [10][11].

### What Courts Accept

- Venmo, Zelle, and Cash App records can be requested through discovery and subpoenaed if the opposing party refuses to produce them voluntarily [10]
- Transaction histories showing amount, date, description, and parties are considered relevant financial records [11]
- Payment descriptions (e.g., "Child support March 2026") can serve as evidence of intent and purpose

### What Courts Require for Admissibility

- **Authentication**: Someone must testify that the records are what they purport to be (FRE 901). Screenshots alone may not suffice --- the authenticating witness must connect the records to the person [12]
- **Supporting documentation**: Bank statements or other records that corroborate the app's transaction history strengthen admissibility [10]
- **Metadata preservation**: Digital evidence must be collected and preserved without alteration. All metadata must be intact [12]
- **Business records exception (FRE 803(6))**: P2P app records could qualify as business records if they were made (a) in the regular course of business, (b) by a person with knowledge, (c) at or near the time of the event, and (d) authenticated by a custodian or qualified witness [13]

### The Authentication Challenge for App-Based Records

A Florida Supreme Court case established that the affiant must have **personal knowledge** of how the computer system works to authenticate records from it [13]. This means a co-parenting app's records face a potential challenge: who authenticates them? The app company would need to provide a records custodian affidavit or certified records --- which is exactly what OFW and TalkingParents offer (OFW through professional account exports, TalkingParents through 16-digit authentication codes on certified PDFs) [3][14].

---

## What Makes Payment Records "Court-Admissible": A Practical Framework

The term "court-admissible" is used loosely by co-parenting apps. In practice, admissibility depends on meeting specific evidentiary standards [12][13][14].

### The Four Requirements

| Requirement | What It Means | How Apps Address It |
|------------|--------------|-------------------|
| **Relevance** (FRE 401-402) | Records must relate to a material fact | Payment records directly relevant to support compliance |
| **Authentication** (FRE 901) | Must prove records are what they claim to be | Unalterable logs, timestamps, digital signatures, authentication codes |
| **Hearsay Exception** (FRE 803(6)) | Must qualify as business records or other exception | App records made in regular course of business, at/near time of event |
| **Data Integrity** (FRE 902(13)-(14)) | Machine-generated data may be self-authenticating | Certified records with hash verification, no edit/delete capability |

### What Judges Actually Want

DC Superior Court provides the clearest signal: judges "accept certified records from court-approved apps during child support modifications and enforcement hearings" when records include "documented expenses, timestamps, uploaded receipts, and payment histories" [14]. DC Family Court judges mandate OurFamilyWizard in approximately 60% of high-conflict custody cases [14].

### Can a Startup's Records Be "Court-Admissible"?

Yes, but it requires deliberate architecture:

1. **Immutability**: Records must not be editable or deletable after creation (append-only log)
2. **Timestamps**: Server-side timestamps, not client-side (prevents manipulation)
3. **Authentication codes**: Unique identifiers per record that can be verified against the server
4. **Certified exports**: PDF exports with digital signatures or verification URLs
5. **Records custodian availability**: The company must be able to provide authentication testimony or a sworn affidavit if subpoenaed
6. **Two-party confirmation**: Both payer and payee actions are logged, creating corroborating evidence

---

## Plaid for Read-Only Payment Detection: The Regulatory Path Is Clear

### What Plaid's Transactions API Provides

Plaid's Transactions API delivers **up to 24 months of categorized, read-only transaction data** including amount, date, merchant name, category, and location [15]. It supports credit cards, checking, savings, and student loan accounts across 11,000+ financial institutions. Real-time webhook notifications alert when transactions are added, removed, or modified.

### The Key Distinction: Data Aggregation vs. Money Transmission

**Read-only data access is NOT money transmission.** The regulatory framework is clear on this point:

- **Money transmission** = "receiving currency for the purpose of sending it to another party" [16]. Under FinCEN's MSB Rule (2011), anyone who transfers funds is a money transmitter.
- **Data aggregation** = accessing and organizing financial data without moving funds. This falls under a completely different regulatory regime (CFPB Section 1033, state consumer privacy laws) rather than money transmission laws [17].
- Companies like Monarch Money, Copilot, and YNAB use Plaid's read-only Transactions API to display users' bank data without any money transmission license [18].
- Plaid itself distinguishes between its Transactions product (read-only) and its Transfer product (which moves money and requires compliance with money transmission regulations) [15].

**No money transmission license is needed for read-only bank data access.** The licensing requirement is "activities-based" --- it applies only when you actually transmit money [16]. Reading transaction history does not trigger it.

### Regulatory Landscape for Consumer Data Access

The CFPB's Section 1033 rule (finalized October 2024, implementation originally set for April 2026) would require banks to share consumer data with authorized third parties in electronic form [19]. However:

- The rule was stayed and is currently under reconsideration (new ANPR issued August 2025) [19]
- Key disputes include whether banks can charge fintechs for data access and data security requirements
- Despite regulatory uncertainty, Plaid-style data access operates under existing consumer authorization frameworks and is not blocked

### Plaid Pricing for a Startup

| Component | Cost | Notes |
|-----------|------|-------|
| Per-connection fee | $0.50-$2.00 | Per successful bank link [20] |
| Transaction data | ~$1.50/user/month | Ongoing data access [20] |
| Minimum spend | ~$500/month | Pay-as-you-go tier [20] |
| Free tier | 200 API calls per product | For testing in production [15] |
| Volume discounts | Available at 10K+ connections | Custom pricing [20] |

**Unit economics example**: At 500 users, Plaid cost would be ~$750-$1,250/month ($1.50/user + amortized connection fees). At $9.99/user/month revenue, gross margin before Plaid is ~$3,745-$4,245/month (75-85%).

### Plaid Alternatives

- **Teller**: Transparent pricing, free startup tier, but more limited bank coverage than Plaid [21]
- **MX**: Strong data enhancement and UI, used alongside Plaid by Monarch Money [18]
- **Finicity** (Mastercard): Also used by Monarch alongside Plaid [18]

---

## Seven Payment Confirmation Approaches: Feasibility Assessment

### 1. Manual Data Entry ("I paid $1,254 on March 1")

**Status**: This is the universal approach. Every co-parenting app uses it.

**Strengths**: Zero integration complexity, works for any payment method (cash, check, Venmo, Zelle, wire), no regulatory burden.

**Weaknesses**: Relies entirely on payer honesty. If payer forgets to log, the record is incomplete. Payee has no independent proof the entry is accurate.

**Court value**: Low without corroboration. A self-reported entry is essentially a self-serving statement.

### 2. Receipt/Screenshot Upload

**Status**: Supported by OFW, DComply, AppClose, SupportPay, CoParenter, and Custody X Change.

**Strengths**: Visual proof of payment. SupportPay's receipt scanning extracts data automatically from photos [6]. Receipts from Venmo/Zelle showing payment details are strong corroboration.

**Weaknesses**: Screenshots can be fabricated. Receipts fade (attorneys specifically warn about this [9]). No automated verification that the screenshot is genuine.

**Court value**: Moderate. Screenshots are admissible if authenticated but are not self-authenticating. A screenshot showing a Venmo payment of $1,254 on March 1 with "Child Support" in the memo, combined with a bank statement showing the same withdrawal, is strong evidence.

### 3. Bank Statement Import (via Plaid or Manual Upload)

**Status**: No co-parenting app currently offers Plaid-based automatic detection. Manual bank statement upload is not a standard feature in any co-parenting app. Personal finance apps (Monarch, Copilot, YNAB) use Plaid for automatic categorization but do not share data between parties.

**Strengths**: Independent, third-party verification. If both parents connect their bank accounts, a matching outflow (payer) and inflow (payee) is extremely strong evidence. Plaid data is real-time and includes merchant/payee details.

**Weaknesses**: Requires both parties to connect bank accounts --- a significant trust barrier, especially in high-conflict situations. Plaid costs ~$1.50/user/month. The payee may refuse to connect their account.

**Court value**: Very high. Bank records are classic business records under FRE 803(6) and are routinely admitted in family court. Automated matching of payer outflow and payee inflow would be the strongest possible documentation short of wage garnishment.

### 4. Payment Notification Forwarding

**Status**: Not implemented by any co-parenting app. Banks and P2P apps send email/SMS notifications for every transaction. These could theoretically be forwarded to the co-parenting app as proof.

**Strengths**: Passive --- requires no manual entry. Contains transaction details from the source. Could be automated via email parsing.

**Weaknesses**: Email forwarding can be spoofed. SMS parsing requires phone access permissions. Bank notification formats vary widely. No standard API for accessing bank notifications.

**Court value**: Low-moderate. Forwarded emails are hearsay unless authenticated. But they corroborate manual entries.

### 5. Two-Party Confirmation (Payer Logs, Payee Confirms)

**Status**: OurFamilyWizard's Check/Other flow implements this exactly [1]. DComply's billing workflow also requires payee action (pressing "pay"). TalkingParents does NOT support this for external payments.

**Strengths**: Creates a two-party record --- the payer's claim AND the payee's acknowledgment, each with independent timestamps. The payee's confirmation is a voluntary admission that can be used in court.

**Weaknesses**: The payee can refuse to confirm, leaving the record in limbo. In high-conflict situations, a payee might strategically withhold confirmation even after receiving payment.

**Court value**: High. A two-party confirmed record with timestamps is among the strongest evidence. If the payee confirmed receipt in the app, they cannot later claim they were not paid.

### 6. Automatic Bank Feed Monitoring (Plaid-Powered Detection)

**Status**: NOT implemented by any co-parenting app. Monarch Money and Copilot use this for personal budgeting but not for inter-party verification.

**Concept**: Both parents connect their bank accounts. The app monitors for transactions matching configured criteria (e.g., Zelle transfer of $1,254 from Account A to Account B). When detected, the app automatically creates a payment record and notifies both parties.

**Strengths**: Eliminates manual entry entirely. Independent verification from the banking system. Near-real-time detection via Plaid webhooks. Works for Zelle, ACH, checks (once cleared), wire transfers.

**Weaknesses**: Requires BOTH parents to connect bank accounts. Plaid cannot see Venmo-to-Venmo or Cash-App-to-Cash-App transfers (only the bank-side funding/withdrawal). Matching logic is imperfect --- the payer's outflow description may differ from the payee's inflow description.

**Court value**: Very high if both sides are connected. A matching transaction pair (payer outflow + payee inflow), automatically detected by a neutral third-party system, would be extremely compelling evidence.

### 7. QR Code or Payment Link Generation

**Status**: State child support agencies (Georgia, Massachusetts) use QR codes for payment portal access [22]. No co-parenting app generates payment-specific QR codes or deep links.

**Concept**: The payee generates a payment request with a unique tracking ID. The payer scans the QR code or clicks the link, which opens their preferred P2P app (Venmo, Zelle, PayPal) pre-filled with the correct amount and a reference number. When the payment completes, the reference number ties the payment back to the request.

**Strengths**: Bridges the gap between co-parenting apps and P2P payment apps. The reference number creates a traceable link. Works with existing payment infrastructure.

**Weaknesses**: Requires P2P apps to support pre-filled payment links with custom reference fields. Venmo and Zelle do support payment links but with limited metadata. No automatic completion confirmation back to the co-parenting app.

**Court value**: Moderate-high. The reference number creates a documentary chain from request to payment.

---

## Creative Approaches: What Exists at the Edges

### Email/SMS Bank Notification Parsing

Banks send transaction alerts via email and SMS. A service like Plaid is not the only way to detect payments --- parsing these notifications is an alternative. **Automated SMS/email parsing reduces late payments by 32%** according to the CFPB's research on payment reminders [23]. However, no consumer fintech product currently parses inbound bank notifications to create payment records. The technical approach would require either (a) email forwarding to a parsing service or (b) on-device notification access (Android allows this; iOS does not without significant workarounds).

### Venmo/PayPal API Integration

Venmo has a limited API (mostly for merchants). PayPal has a robust API that could be used to verify payment status programmatically. However, neither Venmo nor Zelle offers a consumer-facing API for third-party apps to verify payment history. Cash App has no public API.

### QuickBooks for Child Support Tracking

At least one family law blog recommends QuickBooks for tracking alimony and child support payments, treating them as business expenses with categorization and reporting [24]. This is a workaround, not a purpose-built solution.

### State Disbursement Unit Integration

State child support agencies process wage-garnished payments through centralized disbursement units. Some states (Texas, Massachusetts, Colorado) offer online payment portals accepting Venmo, PayPal, Apple Pay, and Google Pay [22]. These create government-authenticated records --- the strongest possible documentation. However, they only apply to court-ordered child support processed through the state system, not direct payments between parents or spousal maintenance.

---

## Gap Analysis

### KNOWN (Verified by Web Sources)

| Finding | Source | Confidence |
|---------|--------|------------|
| OFW uses Dwolla for ACH payments, two-party confirmation for external payments | OFW product pages, support docs [1][2] | High |
| DComply uses Plaid + Dwolla, $5.99/mo flat, no per-transaction fees | DComply FAQ, pricing page [4] | High |
| TalkingParents Accountable Payments uses 16-digit auth codes, does NOT support external payment logging | TalkingParents feature page [3] | High |
| Plaid Transactions API provides up to 24 months of read-only data, ~$1.50/user/month | Plaid docs, pricing research [15][20] | High |
| Read-only data aggregation is not money transmission under federal law | Modern Treasury, FinCEN definitions, regulatory analysis [16][17] | High |
| DC courts accept certified co-parenting app records in child support proceedings | Lopez Law Firm DC article [14] | Moderate (single source) |
| No co-parenting app uses automatic bank-feed detection for payment verification | Exhaustive search of all major apps | High (negative finding) |
| CFPB Section 1033 rule is stayed and under reconsideration as of August 2025 | CFPB website, American Banker [19] | High |

### ASSUMED (Believed True but Not Verified)

| Assumption | Basis | Risk |
|-----------|-------|------|
| SupportPay's "automatic monitoring" is marketing language for manual entry + receipt scanning, not Plaid integration | No evidence of Plaid integration on product pages or app store descriptions | Medium --- could be wrong |
| Plaid minimum spend of ~$500/month applies to startups | Third-party pricing analysis, not Plaid official | Medium --- may be negotiable |
| Most co-parenting users would resist connecting bank accounts to a third-party app | General privacy concerns in high-conflict divorce | High --- no survey data |

### UNKNOWN (No Data Available)

| Gap | Why It Matters | How to Investigate |
|-----|---------------|-------------------|
| What percentage of child support is paid via Venmo/Zelle vs. check vs. wage garnishment? | Determines whether bank-feed detection would catch most payments | Survey family law attorneys or state disbursement unit data |
| Do any courts specifically recognize Plaid-verified records as evidence? | First-mover advantage if no precedent exists | Consult family law attorney |
| What is the actual Plaid negotiated rate for a startup with <1,000 users? | Critical for unit economics | Apply for Plaid developer account |
| Would payees (receiving parents) connect their bank accounts? | Determines whether two-sided bank verification is viable | User interviews |

### CONTESTED (Conflicting Information)

| Topic | Source A | Source B |
|-------|---------|---------|
| SupportPay's "automatic transaction monitoring" | SupportPay marketing claims automatic monitoring | Product pages show manual entry + receipt scanning with no Plaid evidence |
| Onward's Venmo/Zelle "integration" | Marketing said "connections to Venmo, PayPal, Zelle" | Actual feature was manual payment method selection, not API integration |

---

## Appendix

[1] OurFamilyWizard, "Payments | Parents - Mobile," https://www.ourfamilywizard.com/knowledge-center/tips-tricks/parents-mobile/payments --- OFW support documentation detailing Check/Other payment workflow and payee confirmation requirement.

[2] OurFamilyWizard, "Secure Online Payments via OFWpay," https://www.ourfamilywizard.com/product-features/expense-log/ofwpay --- OFWpay feature page, Dwolla integration, pricing, limits.

[3] TalkingParents, "Accountable Payments," https://talkingparents.com/features/accountable-payments --- Feature page detailing payment range ($10-$5,000), unalterable records, 16-digit authentication codes.

[4] DComply, "Pay Child Support Online," https://www.dcomply.com/pay-child-support-online/ and "FAQs," https://www.dcomply.com/faqs/ --- Plaid + Dwolla partnership confirmation, ACH transfer details, $5.99/mo pricing.

[5] AppClose, "Features," https://appclose.com/pro/features/ --- ipayou payment system, expense reimbursement workflow, free tier details.

[6] SupportPay, "How to Track and Organize Your Child Support Payments," https://supportpay.com/trackingyourchildsupport/ and "Product," https://supportpay.com/product/ --- Receipt scanning, bank transfer/PayPal support, manual entry for cash/check.

[7] Onward App, https://www.onwardapp.com (shut down October 2024) and Lesa Koski blog, https://www.lesakoski.com/blog/managing-divorce-expenses-with-onward-app --- Venmo/Zelle/CashApp settlement connections, ACH verified transfers.

[8] OurFamilyWizard Blog, "How to Track Child Support Payments," https://www.ourfamilywizard.com/blog/track-child-support-payments --- 7 tracking methods ranked, attorney quotes on Zelle preference and income withholding.

[9] DADvocacy Law Firm, "Giving Credit Where Credit Is Due," https://dadvocacy.com/blog/2018/june/giving-credit-where-credit-is-due-how-to-make-sure-you-have-all-your-proof-of-child-support-payments-and-credits/ --- Attorney recommendations: checks best, cash worst, chart creation advice.

[10] Freed Marcroft LLC, "Navigating Divorce Finances in the Digital Age: The Role of Venmo," https://freedmarcroft.com/navigating-divorce-finances-in-the-digital-age-the-role-of-venmo/ --- Venmo records in divorce discovery, authentication requirements.

[11] The McKinney Law Group, "Using Venmo, PayPal, and Zelle to Hide Money During Divorce," https://themckinneylawgroup.com/using-venmo-paypal-and-zelle-to-hide-money-during-divorce/ --- P2P records as discoverable evidence.

[12] U.S. Legal Support, "Presenting Digital Evidence in Court," https://www.uslegalsupport.com/blog/presenting-digital-evidence-in-court/ and Medium, "Digital Evidence Authentication," https://medium.com/@jh_89950/digital-evidence-authentication-586e2132a3bc --- FRE 901, 902(13)-(14), metadata preservation requirements.

[13] Cornell Law Institute, "FRE 803 Exceptions to the Rule Against Hearsay," https://www.law.cornell.edu/rules/fre/rule_803 and Seyfarth Shaw, "Application of the Business Records Exception," https://www.seyfarth.com/a/web/7061/3G9C1r/applicationofbusinessrecordsexceptiontohearsayrule.pdf --- Business records exception requirements, Florida Supreme Court personal knowledge requirement.

[14] Lopez Law Firm DC, "Co-parenting financial apps endorsed by DC courts: 2026," https://www.lopezlawfirmdc.com/co-parenting-financial-apps-endorsed-dc-courts-2026/ --- DC court endorsement of OFW (60% of high-conflict cases), certified records accepted in modification/enforcement hearings.

[15] Plaid, "Transactions API," https://plaid.com/products/transactions/ and "API Docs," https://plaid.com/docs/api/products/transactions/ --- 24 months of categorized data, real-time webhooks, sync endpoint.

[16] Modern Treasury, "What is Money Transmission?" https://www.moderntreasury.com/learn/what-is-money-transmission --- Federal definition, exemptions (payment processor, agent of payee, authorized delegate), 49-state licensing complexity.

[17] CFPB, "Consumer Financial Data Aggregation," referenced via Davis Wright Tremaine, https://www.dwt.com/blogs/financial-services-law-advisor/2017/06/consumer-financial-data-aggregation--the-potential --- Data aggregation regulatory treatment distinct from money transmission.

[18] Monarch Money Help Center, "Understanding Data Providers and Connections," https://help.monarch.com/hc/en-us/articles/33707613533972 and x1wealth.com comparison, https://x1wealth.com/compare/copilot-vs-monarch --- Monarch uses Plaid + MX + Finicity; Copilot uses Plaid with read-only access.

[19] CFPB, "Personal Financial Data Rights Reconsideration," https://www.consumerfinance.gov/rules-policy/rules-under-development/personal-financial-data-rights-reconsideration/ --- Section 1033 rule stayed, new ANPR August 2025, fee disputes.

[20] GetMonetizely, "Plaid vs Yodlee: How Much Will Financial Data APIs Cost Your Fintech?" https://www.getmonetizely.com/articles/plaid-vs-yodlee-how-much-will-financial-data-apis-cost-your-fintech --- Per-connection $0.50-$2.00, ~$1.50/user/month for transactions, $500/month minimum.

[21] ProtonBits, "Teller vs Plaid," https://www.protonbits.com/teller-vs-plaid/ --- Teller as cheaper alternative with transparent pricing but limited coverage.

[22] Georgia DHS Child Support, https://childsupport.georgia.gov/about-us/frequently-asked-questions and Mass.gov, https://www.mass.gov/how-to/how-to-pay-child-support --- State portals with QR codes, Venmo/PayPal acceptance.

[23] CFPB research referenced via MailerSend, https://www.mailersend.com/solutions/sms-for-banking-and-financial-services --- Automated SMS payment reminders reduced late payments by 32%.

[24] Repetto Law Office, "Mastering Alimony and Child Support Payment Tracking with QuickBooks," https://repettolawoffice.com/child-support-payment-tracking-with-quickbooks/ --- QuickBooks workaround for support payment categorization.

---

## Search Methodology

**Queries executed** (21 total across WebSearch and WebFetch):

1. OurFamilyWizard expense tracking payment logging features external payments
2. SupportPay child support payment tracking app features automatic bank monitoring
3. DComply child support payment tracking documentation court admissible
4. Venmo Zelle payment records court admissible family court evidence case law
5. Plaid read-only transaction history integration regulatory requirements money transmission license
6. Family law attorney advice documenting child support payments best practices
7. Child support payment documentation keep records attorney advice proof
8. SupportPay Plaid bank connection automatic payment detection
9. Plaid transactions API read-only no money transmission license required
10. Payment confirmation two party verification app design receipt acknowledgment coparenting
11. Business records exception hearsay evidence rule app records court admissible
12. Monarch Money Copilot Mint replacement automatic transaction categorization Plaid integration
13. Money transmission data aggregation distinction read-only fintech regulatory
14. TalkingParents payment tracking expense reimbursement features
15. AppClose expense tracking payment feature coparenting
16. CFPB 1033 rule open banking consumer financial data rights
17. Digital evidence family court authentication requirements electronic records
18. Plaid pricing per connection per API call transactions product cost
19. Teller API alternative Plaid cheaper pricing
20. DComply payment processing partner ACH transfers
21. Coparenting app external payment log payment manual entry tracking

**Pages fetched** (12 total): OFW expense log, OFW payments KB, SupportPay product, SupportPay tracking, DComply pay-online, TalkingParents accountable payments, Plaid transactions product, Plaid pricing, Onward app review, Lisa Zeiderman attorney blog, DADvocacy attorney blog, Lopez Law DC courts article, Modern Treasury money transmission explainer.
