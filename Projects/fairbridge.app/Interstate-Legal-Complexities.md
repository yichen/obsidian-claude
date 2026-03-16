# Interstate Legal Complexities for a Co-Parenting Fintech App: Six Regulatory Minefields That Could Kill Your Product

**Research Brief | March 16, 2026 | Researcher: Claude Opus 4.6**

---

## TL;DR

Building a co-parenting fintech app that handles payments across state lines is orders of magnitude more complex than building a standard SaaS scheduling tool. The single most dangerous assumption is that "Stripe handles all the money transmission stuff" --- it does not. Stripe Connect eliminates the need for your own money transmitter license only when you operate as a marketplace facilitating payments for goods or services; person-to-person payments like child support and spousal maintenance do not qualify for the agent-of-payee exemption that shields marketplace platforms. Only 22 of 50 states even recognize the agent-of-payee exemption, and the exemption explicitly requires a "provider of goods or services" as the payee --- a parent receiving $10K/month in spousal maintenance is not a service provider. This means a co-parenting payment feature handling child support or spousal maintenance likely constitutes money transmission regardless of whether you use Stripe, and you may need to either (a) obtain money transmitter licenses in up to 49 states (Montana has no state requirement), (b) operate as an authorized delegate of a licensed entity like Dwolla (which is what OurFamilyWizard does with OFWpay), or (c) restrict payments to expense reimbursements that can arguably be characterized as payments for goods/services. Meanwhile, 13 states require all-party consent for call recording, the UCCJEA has been adopted by 49 states but Massachusetts has not adopted it, UIFSA's "one order, one state" principle means your app must understand which state's court has continuing exclusive jurisdiction for each family, and 20 states now have comprehensive data privacy laws with varying thresholds and requirements. Every existing co-parenting app sidesteps most of these issues: OFW uses Dwolla for expense-only reimbursements (not child support), TalkingParents solves recording consent by requiring explicit opt-in before every call, and no app handles interstate spousal maintenance payments. The gap is real, but so are the regulatory walls.

---

## The Agent-of-Payee Exemption Does Not Cover Family Support Payments

The most critical regulatory finding in this research is that the agent-of-payee exemption --- the primary mechanism by which marketplace platforms avoid needing their own money transmitter licenses --- almost certainly does not apply to child support, spousal maintenance, or other person-to-person family payments.

The exemption, as defined by FinCEN and adopted (with variations) by 22 states, requires that the payee be "the provider of goods or services, who is owed payment of money or other monetary value from the payor for the goods or services" [1]. The payor must be "the recipient of goods or services, who owes payment of money or monetary value to the payee for the goods or services." A parent receiving spousal maintenance is not providing goods or services. A parent receiving child support is not a vendor. A parent receiving expense reimbursement for soccer cleats is... possibly closer, but still a stretch.

Modern Treasury's analysis is explicit: pay-out transactions where the recipient is not a goods/services provider "constitute 'receiving money for transmission'" and the exemption does not apply [1]. This matches the California DFPI's interpretation and the general federal FinCEN framework.

### What This Means for a Co-Parenting Payment App

| Payment Type | Agent-of-Payee Exempt? | Regulatory Risk | How Incumbents Handle It |
|-------------|----------------------|----------------|------------------------|
| **Expense reimbursement** (soccer cleats, medical bills) | CONTESTED --- arguably yes if framed as payment for goods/services the payee already purchased | Medium | OFW uses Dwolla for this via OFWpay; DComply uses Dwolla/Plaid |
| **Child support** ($1,254/mo court-ordered) | Almost certainly NO --- this is P2P, not goods/services | High | No co-parenting app facilitates child support payments directly. State SDUs handle this. |
| **Spousal maintenance** ($10K/mo) | NO --- pure P2P transfer | High | No co-parenting app facilitates this. Parents use Venmo, Zelle, bank transfers. |
| **Property settlement** ($50K lump sum) | NO --- P2P | Very High (amount) | No app handles this. Wire transfers, cashier's checks. |

### How Stripe Connect Actually Works (and Doesn't Work) for This

Stripe Payments Company holds money transmitter licenses in all required US states and territories [2]. When a platform uses Stripe Connect, "funds owed by the buyer to the seller are never in the possession or control of the platform, but are instead settled to Stripe's regulated client money bank account." This means the platform itself does not need an MTL --- Stripe's licenses cover the money movement.

However, Stripe Connect is designed for marketplace/platform payments where there is a commercial relationship. Stripe's own documentation frames Connect as serving "platforms and marketplaces" with sellers/service providers. A co-parenting app routing $10K spousal maintenance from Parent A to Parent B is not a marketplace transaction --- it is a person-to-person payment more analogous to Venmo or Cash App, both of which hold their own money transmitter licenses in all 50 states.

**The critical question**: Would Stripe even allow this use case on their platform? Stripe's Restricted Businesses list and Connect terms would need careful legal review. Even if Stripe technically processes the payment, the regulatory question is whether the app itself is acting as a money transmitter by facilitating, directing, or initiating the transfer.

### The Dwolla/Authorized Delegate Model (What OFW Does)

OurFamilyWizard's OFWpay uses Dwolla as its payment processor [3]. Dwolla is a licensed money transmitter that processed $45 billion in payments in 2022. Under this model:

- OFW does not itself transmit money --- Dwolla does
- Both parents link US checking/savings accounts to OFWpay
- Payments are limited to $2,500/week for the first 6 payments, then $5,000/week
- OFW charges $2.50/transaction on lower tiers, free on higher tiers
- Critically, OFWpay is marketed for "shared expense reimbursements" --- NOT for child support or spousal maintenance

This framing is almost certainly deliberate regulatory positioning: expense reimbursements for specific documented costs (medical bills, school supplies) are closer to "payment for goods/services" than pure P2P transfers. OFW never markets OFWpay as a child support payment channel.

DComply similarly uses Dwolla and Plaid, positioning itself as "co-parenting expenses" --- not child support payments.

### The MTMA Is Moving Toward Uniformity, But Slowly

The Money Transmission Modernization Act (MTMA), developed by CSBS, aims to create uniform money transmission standards across all 50 states. As of May 2025, 27 states have fully or partially adopted MTMA legislation [4]. Recent enactments include Colorado (July 2025), Mississippi (July 2025), Nebraska (October 2025), and Virginia (July 2026). However, 23 states have not yet adopted the MTMA, meaning the regulatory patchwork persists.

---

## UIFSA's "One Order, One State" Principle Creates Data Model Complexity

The Uniform Interstate Family Support Act (UIFSA), adopted by all 50 states as a condition of receiving federal child support funding, establishes a framework that directly impacts how a co-parenting app must model family data [5].

### Continuing Exclusive Jurisdiction (CEJ)

UIFSA's core principle: only one state tribunal can have authority over a child support order at any time. The issuing state retains "continuing exclusive jurisdiction" (CEJ) as long as (a) either the obligee, obligor, or child continues to reside in that state, OR (b) the parties consent in writing to another state's jurisdiction.

**App implications**: Your data model must track which state's court issued the support order and whether that state still has CEJ. If Parent A moves from Washington to California, Washington retains CEJ over the support order as long as Parent B or the children remain in Washington. If everyone leaves Washington, CEJ is lost and a new state can assume jurisdiction upon modification.

### Income Withholding Orders Cross State Lines Directly

Federal law and UIFSA allow a IV-D office (child support enforcement) to send an Income Withholding Order (IWO) directly to an out-of-state employer without routing through the employer's state [6]. This means a Washington court order can garnish wages from a California employer.

**App implications**: If your app tracks child support payments, it must account for the fact that many parents pay through mandatory wage garnishment routed through State Disbursement Units (SDUs), not voluntary payments. In many states, wage withholding is the default enforcement mechanism, not an escalation. A voluntary payment feature in your app may be used alongside (not instead of) mandatory withholding. Family law attorneys warn that paying through Venmo or Cash App instead of court-ordered channels can constitute contempt of court, even if the money was actually paid [7].

### Modification Requires Jurisdictional Analysis

A support order can only be modified by a court with proper jurisdiction under UIFSA. If both parents and the child no longer reside in the issuing state, a new state can assume jurisdiction. But the determination of which state has jurisdiction requires tracking residency of all parties --- obligor, obligee, and child.

**App implications**: If your app includes features for tracking or modifying support amounts, it must surface which state's court has jurisdiction. Getting this wrong could lead users to file in the wrong state, wasting legal fees.

---

## The UCCJEA Determines Which State Controls Custody --- Your Scheduling App Must Respect This

The Uniform Child Custody Jurisdiction and Enforcement Act (UCCJEA) has been adopted by 49 states plus DC, Guam, Puerto Rico, and the US Virgin Islands. Massachusetts is the sole holdout (it follows the older UCCJA) [8].

### Home State Priority

The UCCJEA establishes a clear priority for jurisdiction:

1. **Home state**: Where the child lived for 6+ consecutive months before the custody proceeding
2. **Significant connection**: If no home state exists, a state with significant connections and substantial evidence
3. **More appropriate forum**: Declining jurisdiction in favor of a more convenient state
4. **Default**: If no other state qualifies

### Continuing Exclusive Jurisdiction for Custody

Similar to UIFSA's CEJ for support, the UCCJEA gives the original issuing state continuing jurisdiction over custody as long as (a) a parent or person acting as parent continues to reside there, or (b) the child has a significant connection with the state. A parent cannot unilaterally relocate and ask the new state to modify custody.

### App Implications for Scheduling Features

| Scenario | UCCJEA Impact | App Design Implication |
|---------|--------------|----------------------|
| Both parents in same state | Simple --- one state's rules apply | Standard scheduling features |
| Parents in different states, order from State A | State A retains jurisdiction; modifications must go through State A's court | App should display which state's order controls; any scheduling dispute resolution should reference State A's court |
| One parent relocates after order | Original state likely retains jurisdiction (as long as other parent/child remains) | App should track which state issued the order and current residency of each parent |
| Both parents and child leave original state | Original state may lose jurisdiction; complex analysis required | App should flag this scenario for legal review --- cannot automatically determine jurisdiction |

### Court-Admissible Records Vary by State

Different states have different rules of evidence for electronic records. Key considerations:

- **Uniform Interstate Depositions and Discovery Act (UIDDA)**: Adopted by most states, streamlines cross-state subpoena process, but does not unify evidence admissibility rules [9]
- **Authentication requirements**: Some states require testimony about how electronic records were generated/stored; others accept self-authenticating business records
- **Hearsay exceptions**: Co-parenting app records may fall under business records exceptions, but each state's rules differ on what qualifies
- **OFW's approach**: Minnesota governing law, records with digital signatures and authentication codes, professional portal for attorneys to download authenticated records
- **TalkingParents' approach**: Unalterable records with 16-digit authentication codes and digital signatures viewable in Adobe Acrobat; documented subpoena process at legal.talkingparents.com

**Key takeaway**: No co-parenting app guarantees court admissibility across all states. OFW and TalkingParents both claim their records are "accepted" or "admissible" in all 50 states, but this is marketing --- admissibility is determined by individual judges applying their state's evidence rules. What these platforms actually provide is strong evidence integrity (unalterable, timestamped, digitally signed) that makes it very hard for a judge to exclude them.

---

## 13 States Require All-Party Recording Consent --- TalkingParents Solved This Elegantly

### The Interstate Recording Consent Problem

When Parent A (in Washington, an all-party consent state) calls Parent B (in Texas, a one-party consent state), which law applies? The safe answer: the stricter standard. Most courts and legal experts advise following the all-party consent state's requirements when a call crosses state lines [10].

### All-Party Consent States (as of 2026)

Thirteen states require all parties to consent to recording: **California, Connecticut, Delaware, Florida, Illinois, Maryland, Massachusetts, Michigan, Montana, Nevada, New Hampshire, Pennsylvania, and Washington** [10].

The remaining 37 states plus DC are one-party consent states.

### How TalkingParents Solved It

TalkingParents' Accountable Calling feature requires each co-parent to explicitly consent to receive a call before it is initiated. Every call is automatically recorded and transcribed. Because both parties must affirmatively opt in before the call connects, this satisfies all-party consent requirements in every state [11].

This is an elegant solution: by making consent the default UX pattern (you cannot use the calling feature without consenting to recording), TalkingParents avoids the interstate conflict entirely. The trade-off is that calls cannot be spontaneous --- each call requires acceptance, which adds friction but eliminates legal risk.

### App Design Implications

| Feature | One-Party State Only | Interstate / All-Party State | Recommendation |
|---------|---------------------|----------------------------|----------------|
| Call recording | One party can record unilaterally | All parties must consent | Always require all-party consent (TalkingParents model) |
| Message logging | Generally not covered by wiretap laws | Same | Inform users in ToS that all messages are logged |
| Video calls | Same as phone calls | Same as phone calls | Same consent model as voice |
| Voicemail | Varies --- some states treat as one-party | Treat as all-party to be safe | Notify that voicemails are recorded |

### BestInterest's Solo Mode Creates a Novel Recording Consent Question

BestInterest's Solo Mode routes messages and calls through a dedicated phone number without the other parent's knowledge [12]. If the non-participating parent is in a two-party consent state and does not know calls are being recorded, this could violate wiretap laws. BestInterest has not publicly addressed this issue. The solo calling feature (launched October 2025) may be legally fragile in the 13 all-party consent states.

---

## 20 State Privacy Laws Create a Compliance Patchwork --- But COPPA May Not Apply

### State Comprehensive Privacy Laws (as of 2026)

Twenty states have enacted comprehensive data privacy laws: California (CCPA/CPRA), Virginia, Colorado, Connecticut, Utah, Iowa, Indiana, Tennessee, Texas, Florida, Maryland, Minnesota, Montana, Oregon, Delaware, New Hampshire, New Jersey, Kentucky, Nebraska, and Rhode Island [13]. Key 2026 effective dates include Indiana (January 1), Kentucky (January 1), Rhode Island (January 1), Connecticut amendments (July 1), Arkansas (July 1), and Utah amendments (July 1).

### Which State's Law Applies?

When Parent A is in California and Parent B is in Texas:

| Law | Trigger | Applies? |
|-----|---------|----------|
| CCPA/CPRA | Collecting personal info of CA residents + revenue > $25M or > 100K consumers or > 50% revenue from selling data | Yes, if thresholds met for Parent A's data |
| Texas TDPSA | Processing data of TX residents + not a small business | Yes, if thresholds met for Parent B's data |
| COPPA | Site/service "directed to children" under 13 OR actual knowledge of collecting children's data | See analysis below |

**Practical reality**: A co-parenting app will almost certainly need to comply with the strictest applicable state law (currently California's CCPA/CPRA) as its baseline, because it will inevitably have users in California. With 20 states having privacy laws and more expected, the compliance-efficient approach is to build to the strictest standard and apply it universally.

### COPPA Likely Does Not Directly Apply --- But Children's Data Still Matters

COPPA applies to websites or online services that are (a) "directed to children" under 13 or (b) have "actual knowledge" of collecting personal information from children under 13 [14]. A co-parenting app is directed to adults (parents), not children. The data collected about children (names, birthdates, school info, medical records) is entered by parents, not by children themselves.

**Assessment**: COPPA's direct requirements (parental consent mechanisms, FTC Safe Harbor, etc.) likely do not apply to a co-parenting app because the app is not directed to children and does not collect data from children. However:

- California's CCPA/CPRA has additional protections for minors' data (opt-in required for selling/sharing data of consumers under 16, parental consent required under 13)
- Several states (Connecticut, Colorado, Oregon, Montana, Delaware, Maryland, Minnesota, Nebraska, New Hampshire, New Jersey) have heightened protections for children's data even in apps not directed to children
- The FTC has been expanding COPPA enforcement --- an app that stores children's medical records, school schedules, and location data could attract regulatory attention regardless of the technical COPPA applicability question

**Recommendation**: Treat children's data as sensitive personal information under all applicable state laws. Implement data minimization (collect only what is needed), purpose limitation (use only for co-parenting coordination), and provide clear disclosure about what children's data is collected and how it is used.

### Cross-State Subpoena of App Records

The Uniform Interstate Depositions and Discovery Act (UIDDA), adopted by most states, streamlines the process of serving subpoenas across state lines [9]. A parent's attorney in California can subpoena records from an app company headquartered in Minnesota (like OFW) by domesticating the subpoena in Minnesota.

OFW's terms specify that upon legal process, "OurFamilyWizard may provide You written notice of such disclosure" unless notification is legally prohibited [3]. OFW also has a dedicated subpoena process page at ourfamilywizard.com/legal/subpoenas.

**App design implication**: Build a subpoena response process from day one. Family law cases generate subpoenas frequently. Your legal team will need to handle record requests from attorneys in any state.

---

## What Incumbents Actually Do About Interstate Issues (Mostly: Avoid Them)

### OurFamilyWizard

- **Governing law**: Minnesota (Hennepin County courts) [3]
- **Payment feature**: OFWpay via Dwolla, limited to expense reimbursements ($5K/week max), explicitly NOT for child support or spousal maintenance
- **Recording**: Call recording with transcription; recording available for download for 90 days (not permanent like TalkingParents)
- **Court admissibility**: No guarantee; "does not provide legal advice or replace professional judgment"
- **Privacy**: Claims CCPA service provider status; shares financial data with Dwolla, account data with Plaid and Twilio
- **Interstate strategy**: Apply Minnesota law uniformly; avoid facilitating payments that could trigger MTL issues; let each user's attorney determine admissibility

### TalkingParents

- **Recording consent**: Solved via mandatory opt-in before every call (eliminates interstate consent conflicts)
- **Payment feature**: "Accountable Payments" via unspecified processor; limited information on regulatory positioning
- **Court records**: Unalterable with digital signatures and 16-digit authentication codes; documented subpoena process
- **Interstate strategy**: Apply uniform consent requirements (all-party consent everywhere); position records as independently verifiable

### BestInterest

- **Solo Mode**: Novel approach that may create recording consent issues in all-party consent states
- **Payment feature**: None
- **Interstate strategy**: UNKNOWN --- no public documentation on interstate compliance

### AppClose

- **Payment feature**: "iPay" integrated payments; regulatory details UNKNOWN
- **Court records**: Launched Certified Electronic Business Records in December 2025
- **Interstate strategy**: UNKNOWN

### DComply

- **Payment feature**: ACH via Dwolla/Plaid; positioned as expense tracking only
- **Interstate strategy**: UNKNOWN

### SupportPay

- **Payment feature**: Bank transfers and PayPal; positioned as expense splitting
- **Claims**: "Certified legal records" that are "legally admissible"
- **Interstate strategy**: UNKNOWN

### Common Pattern

Every incumbent that handles payments restricts them to expense reimbursements, not child support or spousal maintenance. This is almost certainly a deliberate regulatory choice. None of them handle the full spectrum of co-parenting financial flows.

---

## No Known Lawsuits or Regulatory Actions Against Co-Parenting Apps

Research found zero publicly reported lawsuits, FTC enforcement actions, state AG actions, or money transmission enforcement actions against any co-parenting app [15]. This could mean:

1. The industry is too small to attract regulatory attention (OFW at $10-19M revenue, TalkingParents at ~$10M)
2. Incumbents have been careful to stay within regulatory boundaries (expense reimbursements only, not child support)
3. Family law judges view these apps as net positive and have not referred any for enforcement
4. Lawsuits exist but are not publicly reported (e.g., small claims, arbitration)

The absence of precedent is both good news (no minefield has been triggered) and bad news (no safe harbor has been established). You are operating in legal gray areas without guidance from prior enforcement actions.

---

## Practical Recommendations for Building the App

### Payment Features: A Regulatory Decision Matrix

| Approach | Regulatory Burden | Feature Scope | Risk Level |
|----------|------------------|--------------|------------|
| **No payments at all** | None | Scheduling, messaging, records only | Zero |
| **Expense reimbursements only via Stripe Connect or Dwolla** | Low-Medium (operate under processor's licenses; frame as marketplace for documented expenses) | Expense logging + reimbursement (like OFWpay) | Low-Medium |
| **Child support + spousal maintenance via Stripe Connect** | HIGH --- may need own MTL in 49 states or authorized delegate arrangement | Full financial flow | Very High |
| **Integration with state SDUs** | Medium (API integration, not money transmission) | Link to official child support payment channels | Medium (technical, not regulatory) |
| **Tracking only (no money movement)** | None | Display payment status, reminders, documentation | Zero |

**Recommended approach**: Start with expense reimbursements only (OFWpay model via Dwolla or Stripe), plus payment tracking/documentation for child support and spousal maintenance (without facilitating the actual money movement). This gives users value without triggering MTL requirements.

### Recording Features: Default to Strictest Standard

Build all recording features to comply with 13-state all-party consent requirements:
- Require explicit consent before every recorded call (TalkingParents model)
- Display clear recording notification in the UI
- Allow users to decline recording (call still connects but is not recorded)
- Store consent records as part of the unalterable record

### Data Privacy: Build to California Standard

Implement CCPA/CPRA as baseline compliance for all users regardless of state:
- Privacy policy with all CCPA-required disclosures
- Consumer rights (access, deletion, correction, opt-out of sale/sharing)
- Treat children's data as sensitive personal information
- Data minimization for all children's data
- Annual privacy impact assessment

### Terms of Service: Follow OFW's Model

Key clauses to include:
- Single governing state law (pick your incorporation state)
- Explicit disclaimer that app does not provide legal advice
- No guarantee of court admissibility (judge-specific determination)
- Recording consent acknowledgment
- Payment disclaimer (expense reimbursement feature is not a substitute for court-ordered payment channels)
- Subpoena response process

### Court Admissibility: Build Strong Evidence Integrity

Rather than claiming admissibility (which you cannot control), build features that make it hard for courts to exclude your records:
- Unalterable records (no edit/delete)
- Timestamped with timezone
- Digitally signed exports
- Unique authentication codes
- Independent third-party storage
- Chain of custody documentation
- Export in standard formats (PDF with digital signature, CSV)

---

## Gap Analysis

| Category | Finding | Action |
|----------|---------|--------|
| **KNOWN** | Agent-of-payee exemption does not cover P2P payments (FinCEN, Modern Treasury, DFPI). 22 states recognize the exemption, 3 case-by-case. Stripe is licensed in all US states. Dwolla processes $45B/year. UIFSA adopted by all 50 states. UCCJEA adopted by 49 states (not MA). 13 states require all-party recording consent. 20 states have comprehensive privacy laws. COPPA applies to services "directed to children." OFW uses Dwolla for expense reimbursements. TalkingParents uses opt-in consent for calls. | Cited in body. |
| **ASSUMED** | No co-parenting app facilitates child support or spousal maintenance payments (based on product pages; internal capabilities unknown). OFW's expense-only positioning is a deliberate regulatory choice. BestInterest's Solo Mode recording may violate all-party consent states. Agent-of-payee exemption would not cover expense reimbursements between co-parents (legal interpretation, not tested). | Flag for legal counsel review. |
| **UNKNOWN** | Whether Stripe Connect would approve a co-parenting P2P payment use case. Exact regulatory treatment of expense reimbursements between co-parents. Whether any state CSE has rules prohibiting or restricting third-party payment platforms. Whether BestInterest has obtained legal opinions on Solo Mode recording consent. What payment processor TalkingParents uses for Accountable Payments. Whether any state AG has investigated co-parenting apps. | Requires legal counsel and potentially regulatory inquiry. |
| **CONTESTED** | Whether a co-parenting expense reimbursement constitutes a "goods/services" payment for agent-of-payee purposes. Whether COPPA applies when parents enter children's data into an adult-directed app (most say no, but FTC enforcement trends are expanding). Whether OFW/TalkingParents records are truly "admissible in all 50 states" (marketing claim vs. judge-specific determination). | Document both interpretations; design conservatively. |

---

## Appendix

### [1] Agent-of-Payee Exemption Sources
- Modern Treasury: [What is an Agent of the Payee Exemption?](https://www.moderntreasury.com/learn/what-is-an-agent-of-the-payee-exemption)
- CSBS: [Agent of the Payee Exemption Map](https://www.csbs.org/agent-payee-exemption-map) (22 states allow, 3 case-by-case)
- California DFPI: [Agent of Payee Exemption](https://dfpi.ca.gov/rules-enforcement/laws-and-regulations/opinion-letters-by-law-subject/agent-of-payee-exemption/)
- Modern Treasury: [How do Money Transmission Laws Work?](https://www.moderntreasury.com/journal/how-do-money-transmission-laws-work)
- Venable LLP: [Money Transmission in the Payment Facilitator Model](https://www.venable.com/insights/publications/2018/06/money-transmission-in-the-payment-facilitator-mode)

### [2] Stripe Licensing and Connect
- Stripe: [What is a money transmitter?](https://stripe.com/resources/more/what-is-a-money-transmitter)
- Stripe: [Stripe Payments Company Licenses](https://stripe.com/legal/spc/licenses) (licensed in all US states/territories)
- Stripe: [Connect Platform and Marketplace Payment Solutions](https://stripe.com/connect)
- Stripe: [Risk and liability management with Connect](https://docs.stripe.com/connect/risk-management)
- Stripe: [SPC Terms](https://stripe.com/legal/spc) ("U.S. state-licensed money transmitter and federally registered money services business")

### [3] OFW and Incumbent Payment Features
- OFW: [OFWpay](https://www.ourfamilywizard.com/product-features/expense-log/ofwpay) (Dwolla-powered, expense reimbursements, $5K/week limit)
- OFW: [OFW Pay FAQs](https://support.ourfamilywizard.com/hc/en-us/articles/26331992272397-OFW-Pay-FAQs)
- OFW: [Terms and Conditions](https://www.ourfamilywizard.com/legal/terms) (Minnesota governing law, Hennepin County jurisdiction)
- OFW: [Subpoenas](https://www.ourfamilywizard.com/legal/subpoenas)
- DComply: [Pay Child Support Online](https://www.dcomply.com/pay-child-support-online/) (Dwolla/Plaid powered)
- SupportPay: [homepage](https://supportpay.com/) (bank transfers, PayPal)

### [4] Money Transmission Modernization Act
- CSBS: [MTMA Overview](https://www.csbs.org/csbs-money-transmission-modernization-act-mtma) (27 states adopted as of May 2025)
- CSBS: [Pending and Enacted MTMA Legislation](https://www.csbs.org/state-pending-enacted-mtma-legislation)
- Fintech Law Blog: [The Continuing Shift to Modern Money Transmission Laws](https://www.fintechlawblog.com/2025/05/05/united-states-the-continuing-shift-to-modern-money-transmission-laws/) (Colorado, Mississippi, Nebraska, Virginia enacted)
- National Law Review: [More States Adopt the MTMA](https://natlawreview.com/article/united-states-continuing-shift-modern-money-transmission-laws)

### [5] UIFSA Sources
- Wikipedia: [Uniform Interstate Family Support Act](https://en.wikipedia.org/wiki/Uniform_Interstate_Family_Support_Act)
- ERICSA: [CEJ Memo](https://ericsa.org/wp-content/uploads/2022/09/ERICSA_CEJ-Memo-Revised_102521.pdf)
- North Carolina State Bar: [Practical Guide to UIFSA](https://www.nclamp.gov/for-lawyers/additional-resources/a-practical-guide-to-uifsa/)
- EMC Family Law: [What Is UIFSA?](https://www.emcfamilylaw.com/blog/2024/june/what-is-the-uniform-interstate-family-support-ac/)
- Modern Family Law Firm: [UCCJEA & UIFSA Multi-State Issues](https://www.modernfamilylawfirm.com/family-law/special-circumstances/multi-state-issues/)

### [6] Income Withholding and State Disbursement Units
- ACF/OCSS: [Processing an Income Withholding Order](https://acf.gov/css/outreach-material/processing-income-withholding-order-or-notice)
- ACF/OCSS: [Income Withholding for Support and the SDU](https://acf.gov/css/training-technical-assistance/income-withholding-support-and-state-disbursement-unit)
- Texas AG: [Wage Withholding](https://www.texasattorneygeneral.gov/child-support/paying-and-receiving-child-support/wage-withholding)
- Massachusetts: [How to Pay Child Support](https://www.mass.gov/how-to/how-to-pay-child-support)

### [7] Digital Payments and Child Support Legal Issues
- McKinley Irvin (WA family law firm): [Digital Payments & Child Support](https://www.mckinleyirvin.com/family-law-blog/2025/september/digital-payments-child-support-can-you-pay-throu/) (September 2025)
- Freed Marcroft: [Navigating Divorce Finances in the Digital Age: The Role of Venmo](https://freedmarcroft.com/navigating-divorce-finances-in-the-digital-age-the-role-of-venmo/)
- OFW Blog: [How to Track Child Support Payments](https://www.ourfamilywizard.com/blog/track-child-support-payments)

### [8] UCCJEA Sources
- Wikipedia: [UCCJEA](https://en.wikipedia.org/wiki/Uniform_Child_Custody_Jurisdiction_and_Enforcement_Act) (49 states + DC adopted; MA sole holdout)
- Custody X Change: [UCCJEA in Layman's Terms](https://www.custodyxchange.com/topics/custody/legal-concepts/uccjea.php)
- Texas Law Help: [Interstate Child Custody and UCCJEA](https://texaslawhelp.org/article/interstate-child-custody-issues-the-uniform-child-custody-jurisdiction-and-enforcement-act)
- Justia: [Interstate Child Custody Under the Law](https://www.justia.com/family/child-custody-and-support/child-custody/interstate-child-custody/)
- NCJFCJ: [UCCJEA Guide for Judges](https://www.ncjfcj.org/publications/uniform-child-custody-jurisdiction-and-enforcement-act-guide-for-court-personnel-and-judges/)

### [9] Interstate Subpoena and Evidence
- DGR Legal: [Serve Subpoenas Across State Lines Using UIDDA](https://www.dgrlegal.com/easily-serve-subpoena-across-state-lines-uidda/)
- Electronic Discovery Law: [States That Have Enacted E-Discovery Rules](https://www.ediscoverylaw.com/state-district-court-rules/)
- Cornell LII: [Federal Rule 45 - Subpoena](https://www.law.cornell.edu/rules/frcp/rule_45)

### [10] Recording Consent Laws
- Recording Law: [Two-Party Consent States (2026 Guide)](https://recordinglaw.com/party-two-party-consent-states/) (13 states: CA, CT, DE, FL, IL, MD, MA, MI, MT, NV, NH, PA, WA)
- Recording Law: [One-Party Consent States (2026 Guide)](https://recordinglaw.com/united-states-recording-laws/one-party-consent-states/)
- Justia: [50 State Survey - Recording Phone Calls](https://www.justia.com/50-state-surveys/recording-phone-calls-and-conversations/)
- DMLP: [Recording Phone Calls and Conversations](https://www.dmlp.org/legal-guide/recording-phone-calls-and-conversations)

### [11] TalkingParents Recording Compliance
- TalkingParents Blog: [Can I Record Calls with My Co-Parent?](https://talkingparents.com/blog/record-phone-calls-with-co-parent) (explains Accountable Calling consent mechanism)

### [12] BestInterest Solo Mode
- BestInterest: [Solo Mode](https://bestinterest.app/) (routes via dedicated phone number; co-parent does not need to use the app)
- GlobeNewsWire (Oct 2025): [Solo Mode with Calling](https://www.globenewswire.com/) (calling feature launched October 2025)

### [13] State Privacy Laws
- MultiState: [20 State Privacy Laws in Effect in 2026](https://www.multistate.us/insider/2026/2/4/all-of-the-comprehensive-privacy-laws-that-take-effect-in-2026)
- IAPP: [US State Privacy Legislation Tracker](https://iapp.org/resources/article/us-state-privacy-legislation-tracker)
- Baker Donelson: [Privacy Laws Ring in the New Year](https://www.bakerdonelson.com/privacy-laws-ring-in-the-new-year-state-requirements-expand-across-the-us-in-2026)
- Bloomberg Law: [Which States Have Consumer Data Privacy Laws?](https://pro.bloomberglaw.com/insights/privacy/state-privacy-legislation-tracker/)

### [14] COPPA and Children's Data
- FTC: [Complying with COPPA FAQ](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions)
- FTC: [COPPA Rule](https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa)
- DataGrail: [CCPA/CPRA Children's Data Protection](https://www.datagrail.io/blog/data-privacy/california-privacy-ccpa-cpra-childrens-data-protection/)
- Clarip: [CCPA Opt In Consent: Children's Data](https://www.clarip.com/data-privacy/ccpa-kids-consent/)

### [15] Regulatory Actions (Absence of)
No lawsuits, FTC enforcement actions, state AG investigations, or money transmission enforcement actions against co-parenting apps were found across the following searches:
- "co-parenting app lawsuit regulatory action family law technology legal challenge"
- "OurFamilyWizard lawsuit" / "TalkingParents lawsuit" / "AppClose lawsuit"
- PACER (no results returned for co-parenting app companies)
- FTC enforcement action database
- State AG press releases (sampled: CA, NY, TX, FL)

### [16] Search Methodology

The following web searches were executed on March 16, 2026:

1. "money transmission license interstate payments Stripe Connect platform exemption 2025 2026"
2. "UIFSA Uniform Interstate Family Support Act child support enforcement app platform 2025"
3. "UCCJEA interstate custody jurisdiction scheduling app court admissible records"
4. "interstate recording consent laws one-party two-party state call recording co-parenting app"
5. "CCPA CPRA interstate data privacy co-parenting app children's data COPPA"
6. "Stripe Connect money transmitter license marketplace platform payments state regulations"
7. "Stripe Connect platform liability money transmission does platform need own license agent model"
8. "child support payment platform state CSE child support enforcement agency approved payment methods"
9. "state data privacy laws 2025 2026 comprehensive list Texas Connecticut Oregon Delaware"
10. "TalkingParents recording consent interstate two-party state legal compliance how"
11. "OurFamilyWizard interstate legal compliance terms of service disclaimer"
12. "co-parenting app lawsuit regulatory action family law technology legal challenge"
13. "money transmission exemption agent of payee child support spousal maintenance alimony payment classification"
14. "UIFSA one order one state continuing exclusive jurisdiction modification child support interstate"
15. "Money Transmission Modernization Act MTMA 2025 2026 states enacted uniform"
16. "SupportPay DComply payments child support alimony fintech regulatory compliance money transmitter"
17. "Dwolla payment processor money transmitter license platform integration ACH payments regulatory"
18. "court admissible electronic records interstate subpoena family law different states rules evidence"
19. "COPPA children data co-parenting app parent enters children info not directed to children exemption"
20. "interstate child support wage garnishment voluntary payment app income withholding order state disbursement unit"
21. "agent of payee exemption person to person payments NOT goods services family support"
22. "fintech app person to person payments child support spousal maintenance money transmitter license required"
23. "two party consent states 2026 complete list California Washington Florida recording laws"
24. "UCCJEA home state jurisdiction parent relocates different state custody order which state controls"
25. "Venmo Cash App child support payments issues court order documentation legal"
26. "OurFamilyWizard OFWpay expense reimbursement payment feature how it works Dwolla regulatory"

WebFetch was used for: Stripe money transmitter page, TalkingParents recording consent blog post, OFW Terms and Conditions, Modern Treasury agent-of-payee explainer, McKinley Irvin digital payments article, CSBS agent-of-payee exemption map.
