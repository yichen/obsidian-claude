# Stripe Connect and Nacha Third-Party Sender Compliance for FairBridge

**Date**: 2026-03-16
**Status**: Complete
**Confidence**: HIGH (based on Stripe's own legal terms + Nacha rules)

---

## TL;DR

**You do NOT need to independently register as a Nacha Third-Party Sender.** Stripe is the registered TPS. Your platform (FairBridge) is the **Originator** under Nacha rules. This is explicitly stated in Stripe's ACH Payment Terms: "Stripe is operating as a Third Party Sender (as defined in the Nacha Operating Rules) and you understand and accept your role as the Originator." The Originator role carries real compliance obligations (authorization, record-keeping, return rate monitoring) but does NOT require Nacha TPS registration. Stripe also explicitly prohibits you from acting as a Nested TPS through their services.

---

## The Definitive Answer: Three-Party Chain

Under the Nacha Operating Rules, the ACH transaction chain for a Stripe Connect platform works like this:

| Role | Entity | Registration Required? |
|------|--------|----------------------|
| **ODFI** (Originating Depository Financial Institution) | Stripe's partner banks (e.g., Goldman Sachs, Cross River Bank) | Yes — bank charter |
| **Third-Party Sender** | **Stripe** | Yes — registered with ODFI, conducts annual risk assessments and compliance audits |
| **Originator** | **FairBridge (your platform)** | **No TPS registration** — but must comply with Originator obligations |
| Customer | Parent whose bank account is debited | N/A |

This chain is documented verbatim in Stripe's ACH Payment Terms [1]: Stripe operates as the TPS, the ODFI banks submit transactions on your behalf, and you are the Originator.

---

## What "Originator" Means: Your Actual Obligations

Being the Originator is not a free pass. Stripe's ACH Payment Terms [1] impose these specific obligations:

### Authorization Requirements
- You MUST obtain the customer's authorization to debit or credit their bank account before initiating any ACH transaction
- Authorizations MUST comply with Nacha Operating Rules (for WEB entries: consumer must authorize via internet, you must use commercially reasonable methods to authenticate identity)
- You MUST maintain records sufficient to reconstruct any authorization and provide evidence to Stripe or the ODFI on request

### Data Accuracy
- You represent that all transaction information provided to Stripe is "accurate, timely and complete"
- You warrant no transaction will cause Stripe or the ODFI to violate any regulation or sanction

### Return Rate Monitoring
- If 0.5% or more of your debits are disputed/returned, Nacha triggers a compliance review [3]
- Stripe may suspend ACH access if return rates exceed thresholds

### Nacha Purchase Rule (Effective March 20, 2026)
- For e-commerce ACH debits using WEB or TEL SEC codes, you must include "PURCHASE" in the Company Entry Description field [4]
- FairBridge expense reimbursements likely qualify as "purchases of services" — verify with Stripe whether reimbursement payments need the PURCHASE label

---

## Why FairBridge Is NOT a TPS (and Cannot Become One via Stripe)

### The Nacha Definition Test

A Third-Party Sender is an entity that "acts on behalf of an Originator to transmit entries through an ODFI without a direct agreement between the Originator and the ODFI" [5]. The key test: does your entity sit BETWEEN the Originator and the ODFI, transmitting ACH entries on behalf of someone else?

In the FairBridge model:
- FairBridge instructs Stripe to initiate ACH debits from Parent A's bank account
- Stripe (the TPS) submits those entries to its ODFI partner banks
- FairBridge is the entity initiating the payment — it IS the Originator, not an intermediary

FairBridge does not transmit ACH entries to an ODFI. Stripe does. FairBridge does not have (or need) an agreement with the ODFI. Stripe has that agreement.

### The "Nested TPS" Prohibition

Stripe's ACH Payment Terms explicitly state [1]:

> "You must not submit ACH Network Transactions as a Nested Third Party Sender (as defined in the Nacha Operating Rules) through the Stripe Payments Services."

This means:
1. Stripe recognizes the risk that platforms might accidentally become Nested TPSs
2. Stripe contractually prohibits it
3. If your platform were somehow acting as a TPS (transmitting ACH entries on behalf of OTHER originators through Stripe), you would violate Stripe's terms

### When Would a Platform Become a TPS?

A platform crosses from Originator to TPS when it acts as an intermediary for ANOTHER entity's ACH transactions — specifically, when:
- Entity A wants to debit a bank account
- Entity A doesn't have a direct relationship with a TPS or ODFI
- Your platform submits the ACH entry on Entity A's behalf

In FairBridge's case, the platform IS the entity initiating payments. Parent A authorizes FairBridge to debit their account. FairBridge is not acting "on behalf of" Parent A in the Nacha sense — FairBridge is the Originator of the debit, collecting money owed for a documented expense.

---

## The Connect Architecture Question: Who Is Originator in Connect?

This depends on the charge type used [6]:

| Charge Type | Originator | Use Case |
|-------------|-----------|----------|
| **Direct Charges** | Connected Account | Customer transacts directly with connected account (e.g., Shopify merchant) |
| **Destination Charges** | Platform Account | Platform collects payment, transfers to connected account (e.g., Airbnb) |
| **Separate Charges and Transfers** | Platform Account | Platform collects, then manually transfers (most flexibility) |

**For FairBridge**: The platform collects a debit from Parent A and transfers funds to Parent B. This is a **destination charge** or **separate charge + transfer** model. The platform account is the Originator (the entity that has the ACH mandate from the customer).

Each connected account (each parent) has their own Stripe Express account for receiving payouts, but the ACH debit from Parent A's bank is originated by the platform.

---

## What Stripe Handles vs. What You Handle

| Responsibility | Stripe (TPS) | FairBridge (Originator) |
|---------------|-------------|------------------------|
| ODFI relationship | YES — maintains agreements with partner banks | NO |
| TPS registration with Nacha | YES — registered through ODFI | NO |
| Annual TPS risk assessment | YES | NO (not a TPS) |
| Annual TPS compliance audit | YES | NO (not a TPS) |
| KYC/AML on connected accounts | YES — via Stripe Identity | Collect info, Stripe verifies |
| ACH entry submission to ODFI | YES | NO |
| Customer authorization (mandates) | Provides tools (Financial Connections) | MUST obtain and maintain |
| Transaction accuracy | Transmits what you provide | MUST ensure accuracy |
| Return rate monitoring | Monitors and may suspend | MUST keep below 0.5% |
| Fraud monitoring (2026 rules) | Monitors at network level | Must have risk-based processes [3] |
| Money transmitter licensing | YES — Stripe holds state licenses | NO — operating under Stripe's licenses |
| Nacha Operating Rules compliance | Responsible as TPS | Responsible as Originator |

---

## Confidence Assessment

| Claim | Confidence | Source |
|-------|-----------|--------|
| Stripe is the TPS, platform is the Originator | **KNOWN** — verbatim in Stripe legal terms | [1] |
| Platform does NOT need TPS registration | **KNOWN** — Originators are not TPSs by Nacha definition | [1][5] |
| Nested TPS is prohibited via Stripe | **KNOWN** — verbatim in Stripe legal terms | [1] |
| Platform must maintain ACH authorization records | **KNOWN** — Stripe legal terms | [1] |
| 0.5% return rate threshold triggers review | **KNOWN** — Nacha Operating Rules | [3] |
| PURCHASE label required for WEB debits (Mar 2026) | **KNOWN** — Nacha rule, Stripe docs | [4] |
| Platform Originator obligations are sufficient for FairBridge model | **HIGH CONFIDENCE** — based on Stripe terms + Nacha definitions, but not legal advice |
| No edge case where reimbursement model creates TPS status | **ASSUMED** — logical analysis, not verified with Nacha or compliance counsel |

---

## One Risk to Monitor

If FairBridge ever allows Parent A to instruct the platform to "pay Parent B $X from my bank account" without FairBridge being the entity with a business reason to collect the funds (i.e., it becomes pure P2P pass-through), the Nacha classification could shift. The current spec's requirement that every payment is tied to a documented expense reimbursement keeps FairBridge firmly in Originator territory — the platform has a legitimate business reason to collect the funds (reimbursement for a verified expense).

This is consistent with the spec's existing requirement in R1.1: "MUST require every in-app payment to be linked to a documented expense record."

---

## Sources

1. [Stripe ACH Payment Terms](https://stripe.com/legal/ACH) — Legal terms defining Stripe as TPS, platform as Originator, and prohibiting Nested TPS
2. [Stripe: Nacha Preferred Partner](https://www.nacha.org/content/stripe) — Nacha's recognition of Stripe for ACH Experience, Open Banking, Risk and Fraud Prevention (Oct 2024)
3. [Nacha Rules and Compliance Guide (Stripe)](https://stripe.com/resources/more/nacha-rules-explained) — Return rate thresholds, 2026 fraud monitoring rules
4. [Nacha Compliance for Online Consumer Purchases (Stripe Docs)](https://docs.stripe.com/payments/ach-direct-debit/nacha-purchase-rule) — PURCHASE label requirement effective March 20, 2026
5. [Third Parties in the ACH Network (Nacha)](https://www.nacha.org/content/third-parties-ach-network) — Definitions of TPS, TPSP, Nested TPS
6. [Stripe Connect Charge Types](https://docs.stripe.com/connect/charges) — Destination vs. Direct vs. Separate charges and transfers
7. [Third-Party Sender Roles and Responsibilities (Nacha)](https://www.nacha.org/rules/third-party-sender-roles-and-responsibilities) — TPS risk assessment and audit requirements
8. [Nested Third-Party Sender Rules (Modern Treasury)](https://www.moderntreasury.com/journal/new-nacha-rule-nested-third-party-sender) — Explanation of nested TPS compliance chain
9. [TPS vs TPSP Differences (Modern Treasury)](https://www.moderntreasury.com/journal/the-difference-between-a-third-party-sender-and-a-third-party-service-provider-in-payments) — Key distinction: TPS holds/moves funds, TPSP does not
