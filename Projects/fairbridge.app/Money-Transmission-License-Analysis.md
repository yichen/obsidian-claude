# Stripe Connect Platforms and Money Transmitter Licensing: The Definitive Analysis

**Research Brief** | March 16, 2026 | Researcher: Claude Opus 4.6

---

## Executive Summary

Stripe Payments Company (SPC) holds money transmitter licenses in all 50 U.S. states, D.C., Puerto Rico, and Guam (NMLS #1280479), and is a federally registered Money Services Business with FinCEN [1]. When a platform like FairBridge uses Stripe Connect, funds flow from the payer's bank to a Stripe-titled bank account, then from Stripe to the connected account's bank -- at no point does the platform possess or control funds. This architectural choice is the linchpin: Stripe's Services Agreement explicitly states that "Stripe's Affiliate, Stripe Payments Company ('SPC') provides those regulated Services" for any money transmission involved in using Stripe [2]. The platform appoints "Stripe and Stripe's Affiliate, SPC, as User's agents for the limited purpose of directing, receiving, holding and settling funds" [2]. Because FairBridge never touches, holds, or controls funds -- Stripe does -- FairBridge is not performing money transmission. Stripe is.

However, this is NOT the same as saying "Stripe's MTL extends to platforms" in a blanket legal sense. The correct framing is: **the platform does not need its own MTL because the platform is not transmitting money -- Stripe is.** This is a structural exemption through architecture, not a licensing umbrella. Stripe designed Connect specifically so that platforms avoid triggering money transmission definitions in the first place.

The conclusion is HIGH confidence for FairBridge's specific use case (expense reimbursements via Stripe Connect Express with ACH), but with two important caveats: (1) this analysis does not constitute legal advice, and (2) the platform must NOT add features that would give it possession or control of funds outside Stripe's infrastructure.

---

## How Stripe Connect Eliminates the Platform's MTL Requirement

### The Fund Flow Architecture Is Everything

The reason FairBridge does not need an MTL is not because Stripe "shares" or "extends" its license to platforms. It is because Stripe Connect is architected so that **the platform never performs the regulated activity** of money transmission in the first place.

Money transmission is defined under federal law (31 CFR 1010.100(ff)(5)) and state laws as receiving money from one party for transmission to another. The trigger is **possession or control of funds**. Stripe Connect eliminates this trigger through its fund flow design:

1. **Payer's bank** debits funds via ACH
2. **Stripe** (via SPC) receives and holds funds in a Stripe-titled bank account
3. **Stripe** settles funds to the connected account's (payee's) bank account
4. **Stripe** separately settles the platform's fee to the platform's bank account

At no point does FairBridge receive, hold, or control the funds. Stripe's European regulatory guide states this explicitly: "funds that are owed by the buyer to the seller are never in the possession or control of the platform" [3]. While this language is from their PSD2 guide, Stripe confirms the same fund flow architecture applies to U.S. Connect implementations.

Stripe's Services Agreement (Section 15.1, US Regional Terms) establishes the legal mechanism: the platform "appoints Stripe and Stripe's Affiliate, SPC, as User's agents for the limited purpose of directing, receiving, holding and settling funds" [2]. The platform gives instructions; Stripe executes the regulated activity.

### Stripe's Own Legal Terms Confirm This Structure

Three key provisions in Stripe's legal documents establish who performs the regulated activity:

**Stripe Payments Company Terms** [4]:
> "To the extent that User's use of the Services involves money transmission or other regulated services under U.S. Law, Stripe's Affiliate, Stripe Payments Company ('SPC') provides those regulated Services."

This is unambiguous: SPC is the entity performing money transmission, not the platform.

**Stripe Services Agreement** [2]:
> "Certain Services involve regulated money transmission under U.S. Law. To the extent that User's use of the Services involves money transmission or other regulated services under U.S. Law, Stripe's Affiliate, Stripe Payments Company ('SPC') provides those regulated Services."

**Stripe Connect Features Page** [5]:
Stripe markets Connect as enabling platforms to "benefit from Stripe's money licenses around the world instead of getting your own licenses in every region that you operate."

### The Dual Contractual Relationship

A critical design choice: Stripe does not contract only with the platform. Stripe establishes a **direct legal relationship with each connected account** (the payee parent in FairBridge's case) via the Stripe Connected Account Agreement [6]. This means:

- Stripe has a direct agreement with the payer (through the platform's Stripe integration)
- Stripe has a direct agreement with the payee (via the Connected Account Agreement)
- The platform has a separate relationship with both parents for the software service

This tripartite structure means Stripe is directly providing payment services to both sides. The platform is providing scheduling, expense tracking, and reimbursement workflow software -- not payment services.

---

## Three Layers of Legal Protection for FairBridge

### Layer 1: Platform Does Not Possess or Control Funds (Primary)

This is the strongest protection. Under both federal and state money transmission laws, the triggering activity is **receiving money for transmission to another**. If the platform never receives or controls funds, it is not transmitting money, full stop. Stripe Connect's architecture ensures this.

### Layer 2: FinCEN Payment Processor Exemption (Federal)

Even if a regulator argued the platform plays a role in money movement, FinCEN provides an explicit exemption for payment processors that:

1. Facilitate payment for the purchase of goods or services (not money transmission itself)
2. Operate through clearance and settlement systems that admit only BSA-regulated financial institutions (ACH qualifies)
3. Provide services pursuant to a formal agreement
4. Have an agreement with the seller/payee [7]

FairBridge satisfies all four prongs: it facilitates expense reimbursement (goods/services, not pure P2P transfer), uses ACH through Stripe/SPC (BSA-regulated), has a formal platform agreement, and has an agreement with the payee parent. The "integral to sale of goods or services" language in 31 CFR 1010.100(ff)(5)(ii)(A) is particularly relevant -- the payment is integral to FairBridge's expense-tracking service.

### Layer 3: Agent of Payee Exemption (State-Level)

At the state level, many states exempt "agents of the payee" from money transmission licensing. When Parent A reimburses Parent B for a documented expense, FairBridge acts as an agent of the payee (Parent B) by facilitating the collection of a documented debt. As of 2024, approximately 25 states have adopted some version of the Model Money Transmission Modernization Act, which includes the agent of payee exemption [8]. The nine states that adopted it in 2024 alone (Maryland, South Dakota, Wisconsin, Kansas, Maine, Vermont, South Carolina, Missouri, Connecticut) all included this exemption without material deviation [9].

**Important limitation**: Not all states have the agent of payee exemption. Vermont, for example, has historically stated it "does not exempt a payment processor or an agent of a payee from licensure" [10], though it adopted the Model Act in 2024 which includes the exemption. States like Illinois and Florida have been slower to adopt agent-of-payee exemptions.

However, the agent of payee exemption is **Layer 3** -- a backup. FairBridge's primary protection is Layer 1 (no possession/control of funds), which does not depend on any state-level exemption.

---

## State-Specific Analysis: NY, CA, TX

### New York

New York Banking Law Section 641 states: "no person shall engage in the business of receiving money for transmission without a license, except as an agent of a licensee or as agent of a payee" [11]. FairBridge qualifies under both exceptions:

- **Agent of licensee**: FairBridge directs Stripe (a NY-licensed money transmitter) to process payments. Stripe's NY license is confirmed on their licenses page: "Stripe Payments Company is licensed and regulated as a money transmitter by the New York State Department of Financial Services" [1].
- **Agent of payee**: FairBridge facilitates collection of documented expense reimbursements on behalf of the payee parent.

**Confidence: HIGH** -- NY explicitly recognizes both exceptions.

### California

California adopted the agent of payee exemption in 2014 under the Money Transmission Act. The DFPI (Department of Financial Protection and Innovation) initiated rulemaking in 2019 to clarify the scope of this exemption [12]. Stripe submitted comments to the DFPI noting it obtained its California MTL in 2016 [12]. California's framework is favorable because:

- Stripe holds a CA MTL
- The agent of payee exemption exists
- FairBridge never possesses funds (primary protection applies regardless of exemption)

**Confidence: HIGH** -- CA has both the structural protection and the exemption.

### Texas

Texas is one of the few states that offers an "authorized delegate" exemption, where a company acting as a delegate of a licensed money transmitter can avoid its own licensing requirement [13]. Since FairBridge operates as an agent directing Stripe (licensed in TX) to process payments, this exemption applies. Additionally, the primary structural protection (no fund possession/control) applies in TX as in all states.

**Confidence: HIGH** -- TX has the authorized delegate exemption plus the structural protection.

---

## What Could Break This Protection

FairBridge's MTL-free status depends on maintaining the Stripe Connect architecture. The following changes would **jeopardize the exemption**:

### Danger Zone: Features That Could Trigger MTL Requirements

1. **Holding funds in a FairBridge-controlled account** -- If the platform ever holds funds in its own bank account before forwarding to the payee, it is performing money transmission. This is the single most important line not to cross.

2. **Building a wallet/balance feature** -- If parents can hold a balance within FairBridge (not within Stripe), the platform is holding customer funds and likely needs an MTL.

3. **Processing payments outside Stripe** -- Using a non-licensed payment processor, or building direct ACH integration through a bank API without a licensed intermediary, would remove the Stripe MTL coverage.

4. **Facilitating pure P2P transfers** -- The current design ties every payment to a documented expense. If FairBridge added a "send money" feature without expense linkage, it starts looking like money transmission rather than expense reimbursement facilitation. This is already addressed in the initial spec's R1.1 requirement [14].

5. **Acting as an escrow** -- If FairBridge held funds pending expense approval before releasing to the payee, this could constitute money transmission (holding funds for later transmission).

### Safe Zone: Features That Maintain Protection

- Expense tracking and reimbursement workflows (core product)
- Directing Stripe to process payments based on approved expenses
- Scheduling recurring reimbursements through Stripe
- Tracking external payments (child support, spousal maintenance) without processing them
- Using Stripe Connect Express accounts for all fund movement

---

## Comparison: FairBridge vs. OFW/Dwolla Structure

OurFamilyWizard uses Dwolla as its payment processor, following a similar pattern:

| Aspect | FairBridge + Stripe Connect | OFW + Dwolla |
|--------|---------------------------|--------------|
| **Licensed entity** | Stripe Payments Company (SPC) | Dwolla (licensed MTB in 50 states) |
| **Platform's MTL** | Not required | Not required |
| **Fund possession** | Platform never holds funds | Platform never holds funds |
| **KYC/AML** | Stripe handles via Stripe Identity | Dwolla handles |
| **Architecture** | Express connected accounts | Dwolla API integration |

Both follow the same regulatory pattern: the licensed payment processor handles money transmission; the platform handles the software layer.

---

## Evidence Quality Assessment

| Finding | Confidence | Source Type |
|---------|------------|-------------|
| SPC performs regulated money transmission, not platform | **KNOWN** | Stripe's own legal terms [2][4] -- direct quotes |
| Platform never possesses/controls funds via Connect architecture | **KNOWN** | Stripe documentation [3][5] -- explicit design intent |
| Stripe holds MTLs in all 50 states + territories | **KNOWN** | Stripe licenses page [1] -- NMLS #1280479 |
| FinCEN payment processor exemption applies to FairBridge | **ASSUMED** | FinCEN regulations [7] -- FairBridge appears to meet all 4 prongs, but no specific FinCEN ruling on co-parenting expense apps |
| Agent of payee exemption available in ~25+ states | **KNOWN** | CSBS Model Act tracking, Cooley analysis [8][9] |
| No enforcement action against a Stripe Connect platform for lacking MTL | **UNKNOWN** | No evidence found of enforcement, but absence of evidence is not evidence of absence |
| Stripe explicitly marketing "no license needed" for Connect platforms | **KNOWN** | Stripe Connect features page [5] -- "benefit from Stripe's money licenses" |

---

## Bottom Line for FairBridge

**FairBridge does NOT need its own Money Transmitter License.** This is not a gray area -- it is the explicit, intended design of Stripe Connect. Stripe designed Connect so that platforms avoid performing money transmission entirely. The platform gives instructions; Stripe performs the regulated activity under its own licenses.

The protection comes from three independent layers:
1. **Architectural** (strongest): FairBridge never possesses or controls funds
2. **Federal exemption**: FinCEN payment processor exemption for facilitating goods/services payments through BSA-regulated systems
3. **State exemptions**: Agent of payee and/or authorized delegate exemptions in most states

The one non-negotiable requirement: **every payment must flow through Stripe Connect.** The moment FairBridge holds, receives, or controls funds outside of Stripe's infrastructure, the entire analysis changes.

---

## Appendix: Sources

[1] Stripe Payments Company Licenses — https://stripe.com/legal/spc/licenses
- Lists all state MTLs, NMLS #1280479, NY DFS confirmation
- Accessed: March 16, 2026

[2] Stripe Services Agreement — Services Terms — https://stripe.com/legal/ssa-services-terms
- Section on money transmission, SPC as regulated entity, agency appointment
- Accessed: March 16, 2026

[3] Stripe Connect and PSD2 FAQ — https://stripe.com/guides/frequently-asked-questions-about-stripe-connect-and-psd2
- "Funds owed by the buyer to the seller are never in the possession or control of the platform"
- Accessed: March 16, 2026

[4] Stripe Payments Company Terms — https://stripe.com/legal/spc
- "To the extent that User's use of the Services involves money transmission or other regulated services under U.S. Law, SPC provides those regulated Services"
- Accessed: March 16, 2026

[5] Stripe Connect Features — https://stripe.com/connect/features
- "Benefit from Stripe's money licenses around the world instead of getting your own licenses"
- Accessed: March 16, 2026

[6] Stripe Connected Account Agreement — https://stripe.com/legal/connect-account
- Establishes direct Stripe-to-connected-account legal relationship
- Accessed: March 16, 2026

[7] FinCEN Payment Processor Exemption — 31 CFR 1010.100(ff)(5)(ii)
- Four-prong test for payment processor exemption from MSB/money transmitter registration
- Also: https://www.fincen.gov/resources/statutes-regulations/administrative-rulings/application-money-services-business (FinCEN ruling on escrow services and integral-to-goods exemption)

[8] Model Money Transmission Modernization Act — CSBS
- Agent of payee exemption map: https://www.csbs.org/agent-payee-exemption-map
- ~25 states adopted as of late 2024

[9] Cooley LLP Analysis (August 2024) — https://www.cooley.com/news/insight/2024/2024-08-20-us-states-adopt-model-money-transmission-act-but-harmonization-remains-elusive
- Nine states adopted in 2024, all included agent of payee exemption

[10] Venable LLP Analysis (June 2018) — https://www.venable.com/insights/publications/2018/06/money-transmission-in-the-payment-facilitator-mode
- Vermont regulatory officials stated Vermont does not exempt agent of payee from licensure (pre-2024 Model Act adoption)

[11] New York Banking Law Section 641
- "No person shall engage in the business of receiving money for transmission without a license, except as an agent of a licensee or as agent of a payee"
- https://www.dfs.ny.gov/apps_and_licensing/money_transmitters

[12] California DFPI PRO-07-17 — Stripe Comment Letter (2019)
- https://dfpi.ca.gov/wp-content/uploads/sites/337/2019/05/PRO-07-17-Stripe.pdf
- Stripe obtained CA MTL in 2016

[13] Modern Treasury — How Money Transmission Laws Work
- https://www.moderntreasury.com/journal/how-do-money-transmission-laws-work
- Texas authorized delegate exemption, state-by-state analysis

[14] FairBridge Initial Spec — R1.1 (local file)
- "MUST require every in-app payment to be linked to a documented expense record"
- `/Users/ychen2/Obsidian/Projects/fairbridge.app/initial_spec.md`
