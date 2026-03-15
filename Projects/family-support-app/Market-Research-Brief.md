# Market Research Brief: AI-Powered Coparenting App

**Date**: 2026-03-15
**Researcher**: Claude (Opus)
**Status**: COMPLETE

---

## Executive Summary

OurFamilyWizard generates $10.5M in annual revenue from roughly 1 million cumulative users while charging $150-$300 per parent per year -- yet it holds a 1.5-star rating on SiteJabber across 110 reviews. That gap between institutional entrenchment and user dissatisfaction is the opening. The coparenting app market was valued at $440M in 2024 and is projected to reach $1.12B by 2032 (12.4% CAGR), driven by roughly 660K-1.1M US divorces per year, 12.2M children in the child support system, and courts in all 50 states that increasingly mandate documented co-parent communication. The incumbent leaders -- OurFamilyWizard and TalkingParents -- have locked in distribution through family court relationships built over 20+ years but have been slow to adopt AI. OFW only launched its first AI feature (ToneMeter) in May 2025 after 12 months of development, and it does nothing beyond tone-checking outgoing messages. No incumbent offers AI-assisted schedule swap detection, smart expense splitting, or AI conflict resolution. Meanwhile, three AI-native startups (BestInterest, DivorceX, Parent Copilot) have entered the market since late 2024, validating demand but none combining AI communication + payments + scheduling in a single low-cost product. The payment feature is the highest-margin opportunity: OFW charges $150-$300/year per parent partly to subsidize OFPay, which runs on Dwolla ACH (standard processing: 3-4 business days). The actual cost of ACH via Stripe is $0.80 per transfer capped at $5, or $1 flat for ACH credit -- meaning a parent making 12 payments per year pays roughly $12-$60 in real processing costs, not $300. A product priced at $5-10/month per parent ($60-$120/year) with AI features the incumbents lack, faster payment processing via Stripe Connect, and court-admissible records would undercut OFW by 60-80% while maintaining healthy margins. The regulatory risk is manageable: Stripe Connect allows platforms to operate under Stripe's money transmission licenses, avoiding the need for state-by-state MTL registration.

---

## Competitive Landscape

### The Incumbents are Entrenched but Vulnerable

Two companies dominate the coparenting app market through institutional relationships, not product quality. OurFamilyWizard has spent 25 years (founded 2001) building court adoption across all 50 states, and TalkingParents has carved out the budget-conscious segment with a free tier. Both have significant moats -- court order language frequently names these platforms by name -- but both exhibit the classic signs of incumbent complacency: outdated UIs, slow feature development, and pricing that reflects monopoly positioning rather than underlying costs.

#### Direct Competitors

| Product | Pricing (per parent/yr) | Key Differentiator | Traction | AI Features | Source |
|---------|------------------------|-------------------|----------|-------------|--------|
| **OurFamilyWizard** | $150-$300 (3 tiers) | Court adoption in all 50 states, OFPay payments, Spectrum Equity backing | ~1M cumulative users, $10.5M revenue, 77-132 employees | ToneMeter AI (launched May 2025) -- tone checking only | [OFW Pricing](https://www.ourfamilywizard.com/plans-and-pricing), [Latka](https://getlatka.com/companies/ourfamilywizard) |
| **TalkingParents** | $0-$324 (4 tiers: Free/$72/$144/$324) | Free tier with ads, unalterable records, call recording | 17,161 App Store reviews (4.4 stars) | "Sentiment Scanner + Writing Assist" in Ultimate tier ($27/mo) | [TP Pricing](https://talkingparents.com/pricing) |
| **AppClose** | $108/yr ($8.99/mo, was free until Jan 2026) | Was the only free full-featured app; "iPay" expense tracker | "Tens of thousands" of users; gave 12,900 free accounts to hardship cases | AI Assistant for legal professionals (AppClose Pro) | [AppClose](https://appclose.com/) |
| **coParenter** | $120-$200/yr ($12.99/mo or $119.99/yr single, $199.99/yr shared) | On-demand human mediators + AI dispute resolution | TechCrunch covered in 2019; still operational | AI + ML sentiment analysis to flag inflammatory language | [TechCrunch](https://techcrunch.com/2019/03/15/coparenter-helps-divorced-parents-settle-disputes-using-a-i-and-human-mediation/) |
| **2Houses** | $170/yr for both parents ($14.17/mo total) | Multilingual, single subscription covers both parents | Active, Belgium-based | None identified | [2Houses Pricing](https://www.2houses.com/en/pricing) |
| **Custody X Change** | $72-$240/yr ($6-$20/mo) | Best-in-class schedule/parenting plan builder | Active, recommended by lawyers | Hostile language detection in messaging | [CXC Pricing](https://app.custodyxchange.com/pricing-parents) |
| **DComply** | $36-$72/yr ($2.99-$5.99/mo) | Specialized expense/payment platform ("Venmo for co-parents") | Active, niche | None identified | [DComply Pricing](https://www.dcomply.com/pricing-security/) |
| **SupportPay** | Unknown (free tier exists) | Expense splitting with legal-grade records | "Tens of thousands of users" | None identified | [SupportPay](https://supportpay.com/) |

#### AI-Native Entrants (Post-2024)

These startups validate the thesis that AI + coparenting is an emerging category:

| Product | Pricing | AI Features | Stage | Key Detail | Source |
|---------|---------|-------------|-------|------------|--------|
| **BestInterest** | Free tier + premium (price undisclosed) | Message Shield (incoming filter), Tone Guardian (outgoing coach), Solo Mode (works without co-parent) | Launched Sep 2024; 9,000+ active users | Founded by ex-Google PM Sol Kennedy. Works even if co-parent refuses to use it. | [BusinessWire](https://www.businesswire.com/news/home/20241021896159/en/Frustrated-Parent-Launches-Innovative-AI-Powered-Co-Parenting-App-BestInterest) |
| **DivorceX** | $0/$20/$36 per month | MessageX (draft replies), CaseX (record-keeping), DocX (legal doc analysis), AdvisorX (AI guidance) | Active, priced at premium tier | Built specifically for high-conflict situations. $36/mo premium = $432/yr, more expensive than OFW. | [DivorceX Pricing](https://divorcex.ai/pricing/) |
| **Parent Copilot** | Undisclosed (beta/waitlist) | AI message filtering (lawyer-vetted), smart custody reminders, agreement sync | Beta phase, not yet launched | Created by Renee Bauer, family law attorney in CT | [MissPoppins](https://misspoppins.io/articles/the-ai-co-parenting-app-made-by-a-divorce-attorney) |

#### Open Source Alternatives

No meaningful open-source coparenting apps were found on GitHub. The category is entirely proprietary. This represents both a barrier (no existing codebase to fork) and an opportunity (no free open-source product competing on price).

---

## Market Sizing

### A $440M Market Growing at 12% with Clear TAM Proxies

| Metric | Value | Source | Date | Confidence |
|--------|-------|--------|------|-----------|
| Coparenting apps market (2024) | $440M globally | [Verified Market Research](https://www.verifiedmarketresearch.com/product/co-parenting-apps-coparenting-apps-market/) | 2024 | ASSUMED -- market research firm estimates vary widely |
| Coparenting apps market (2024, alt estimate) | $1.2B globally | [Verified Market Reports](https://www.verifiedmarketreports.com/product/co-parenting-apps-coparenting-apps-market/) | 2024 | CONTESTED -- 2.7x higher than VMR estimate |
| Projected market (2032) | $1.12B | Verified Market Research | 2024 | ASSUMED |
| CAGR | 12.4-12.5% | Multiple sources | 2024 | KNOWN |
| North America share | ~40% of global revenue | VMR | 2024 | ASSUMED |
| US divorces per year | 663K-1.1M | [CDC](https://www.cdc.gov/nchs/fastats/marriage-divorce.htm), [Divorce.com](https://divorce.com/blog/divorce-statistics/) | 2023-2024 | KNOWN (range reflects different reporting methods) |
| Children in child support system | 12.2M | Census/HHS | 2024 | KNOWN |
| Single mothers in US | 7.3M | Census | 2023 | KNOWN |
| Single fathers in US | 1.6M | Census | 2023 | KNOWN |
| OFW revenue | $10.5M | [Latka](https://getlatka.com/companies/ourfamilywizard) | 2024 | ASSUMED (third-party estimate) |
| OFW cumulative users | ~1M | OFW press releases | 2024 | KNOWN (company-stated) |
| OFW employees | 77-132 | Multiple sources | 2024-2025 | CONTESTED |
| Dual-household segment growth | 15% per annum | Market reports | 2025 | ASSUMED |

### Sizing Methodology

**TAM (Total Addressable Market)**: ~8.9M single-parent households in the US (7.3M mothers + 1.6M fathers). If each household represents a co-parenting pair, that is roughly 4.45M co-parenting pairs. At the proposed price of $120-$240/year per pair ($5-10/mo per parent x 2 parents), TAM = $534M - $1.07B.

**SAM (Serviceable Addressable Market)**: Not all co-parents need or want a dedicated app. Court-mandated users are the highest-intent segment. With 72% of family law cases involving at least one self-represented litigant (per NCSC), and courts increasingly recommending documented communication platforms, an estimated 20-30% of co-parenting pairs (890K-1.34M pairs) are reasonable near-term targets. SAM = $107M - $321M.

**SOM (Serviceable Obtainable Market)**: A realistic Year 3 target of 10,000-50,000 paying pairs at $120-$240/year = $1.2M - $12M ARR.

### Caveats

- The $440M vs $1.2B global market estimates are irreconcilable without access to full methodology. The $440M figure is more conservative and likely more reliable.
- "Cumulative users" (OFW's 1M) overstates active paying users. If OFW generates $10.5M at ~$200/user avg, that implies only ~52,500 active paying subscribers -- not 1M.
- Market reports bundle "parenting apps" (Cozi, baby trackers) with "coparenting apps" (OFW, TalkingParents), inflating estimates.
- The 663K vs 1.1M divorce figure discrepancy likely reflects CDC reporting lag vs. state-level aggregation differences.

---

## Target Segments and Pain Points

### Three Distinct User Personas

**Persona 1: Court-Mandated High-Conflict Parent**
- Ordered by a judge to use a documented communication platform
- Currently paying $150-$300/year for OFW because the court order names it
- Would switch if an alternative is explicitly court-approved and cheaper
- Highest willingness to pay; lowest price sensitivity (court requires it)
- Estimated segment: 20-30% of co-parenting app users

**Persona 2: Cost-Conscious Cooperative Co-Parent**
- Uses a free or cheap tool (TalkingParents Free, previously AppClose Free, or just text/email)
- Needs basic scheduling, expense tracking, and payment features
- Very price-sensitive -- AppClose's move from free to $8.99/mo in Jan 2026 displaced thousands of users
- Would pay $5/mo but not $15+
- Estimated segment: 40-50% of co-parenting app users

**Persona 3: Frequent-Payment Power User (Founder's Persona)**
- Makes multiple co-parent payments per month for child expenses
- Currently on OFW Premium ($216/yr) or Max ($300/yr) specifically to get unlimited OFPay
- Frustrated by OFW's slow ACH transfers (3-4 business days via Dwolla) and high cost
- Would pay $5-10/mo for faster, cheaper payments with better AI features
- Estimated segment: 10-20% of co-parenting app users

### Pain Point Evidence

| Pain Point | Evidence Source | Severity Signal |
|-----------|---------------|-----------------|
| OFW is too expensive for what it offers | SiteJabber: 1.5/5 stars, 110 reviews. Users call it "a 3rd rate TXT/email service" at $100+/yr | HIGH -- pricing is the #1 complaint across review sites |
| Payments take 3-5 business days | OFW uses Dwolla with standard ACH (3-4 biz days debit + 1-2 days credit). Users report "almost a full week" for payments. | HIGH -- delays cause disputes between co-parents |
| Per-transaction payment fees on lower tiers | OFW charges $2.50/transaction on lower tiers; Essentials limits to 12 payments/year | MEDIUM -- drives upgrades to Premium |
| Outdated UI, crashes, slow performance | Multiple review sites mention "outdated and cumbersome" design, crashes, failed notifications | MEDIUM -- but users stay because courts require it |
| Customer service is poor | BBB complaints, SiteJabber reviews cite unanswered emails, slow response | MEDIUM |
| AppClose going paid displaced free users | AppClose moved from free to $8.99/mo in Jan 2026; BestInterest launched free tier to capture displaced users | HIGH -- validated by BestInterest's Jan 2026 press release |
| No AI help with drafting messages | Users manually rewrite messages to avoid conflict; OFW's ToneMeter only launched May 2025 | MEDIUM -- AI entrants are addressing this gap |
| Hostile messages from co-parent cause stress | BestInterest's "Message Shield" concept resonated enough to gain 9,000 users in 6 months | HIGH -- emotional pain drives adoption |

Sources: [SiteJabber OFW Reviews](https://www.sitejabber.com/reviews/ourfamilywizard.com), [Trustpilot OFW](https://www.trustpilot.com/review/www.ourfamilywizard.com), [BestInterest Launch](https://www.businesswire.com/news/home/20241021896159/en/), [BestInterest Gap Press Release](https://www.globenewswire.com/news-release/2026/01/28/3227775/0/en/)

### Willingness to Pay

The market shows clear price segmentation:
- **$0/mo**: TalkingParents Free (ad-supported, website-only) captures budget users
- **$3-6/mo**: DComply ($2.99-$5.99) and TalkingParents Essentials ($6) serve cost-conscious users
- **$9-13/mo**: AppClose ($8.99), coParenter ($12.99), and TalkingParents Enhanced ($12) serve mid-market
- **$12-25/mo per parent**: OFW ($12.50-$25) and TalkingParents Ultimate ($27) serve court-mandated/power users
- **$20-36/mo**: DivorceX ($20-$36) tests willingness to pay for premium AI features

The proposed $5-10/mo per parent positions directly in the gap between budget tools and the OFW/TalkingParents premium tiers, while offering AI features that only the $20-36/mo DivorceX tier currently provides.

---

## Differentiation and White Space

### No Product Combines AI + Payments + Scheduling at Low Cost

| Capability | OFW | TalkingParents | BestInterest | DivorceX | **Proposed Product** |
|-----------|-----|---------------|-------------|---------|---------------------|
| Court-admissible messaging | Yes | Yes | Yes | Yes (CaseX) | Yes |
| In-app payments (ACH) | Yes (Dwolla, 3-4 day) | Yes (3% fee Enhanced, Express in Ultimate) | No | No | **Yes (Stripe, same-day possible)** |
| Shared calendar | Yes | Yes | Yes | No | Yes |
| Expense tracking/splitting | Yes | Limited | Yes | No | **Yes (AI-categorized)** |
| AI tone checking (outgoing) | Yes (ToneMeter, May 2025) | Yes (Writing Assist, Ultimate only) | Yes (Tone Guardian) | Yes (MessageX) | Yes |
| AI message filtering (incoming) | No | No | **Yes (Message Shield)** | No | **Yes** |
| AI schedule swap detection | No | No | No | No | **Yes (proposed)** |
| AI expense categorization | No | No | No | No | **Yes (proposed)** |
| AI conflict detection | No | No | Partial | Partial (AdvisorX) | **Yes (proposed)** |
| Works without co-parent install | No | No | **Yes (Solo Mode)** | Yes | Possible |
| Call recording | Yes (Max tier) | Yes (all paid tiers) | No | No | Future |
| Price per parent/month | $12.50-$25 | $0-$27 | Free-premium | $0-$36 | **$5-$10** |

### The Payment Feature is the Highest-Margin Wedge

OFW's pricing structure reveals that payments are a profit center, not a cost center:

- **OFW's cost structure**: Dwolla ACH historically charged ~$0.25/transaction. Even at Stripe's higher rate of $0.80 (capped at $5), 12 payments/year costs $9.60-$60 in processing.
- **OFW charges**: $150-$300/year per parent, with OFPay included at Premium+ tiers. The Essentials tier limits to 12 payments/year.
- **Margin implication**: OFW collects $300-$600/year per couple while spending <$60 on payment processing -- a 90%+ gross margin on the payment feature.

A product that charges $120-$240/year per couple with unlimited payments via Stripe ACH ($0.80-$1.00 per transfer) would:
1. Undercut OFW by 60-80%
2. Maintain 75%+ gross margins on payments (assuming 24 payments/year at $1 each = $24 cost vs $120-$240 revenue)
3. Offer faster settlement (Stripe same-day ACH available vs Dwolla's 3-4 day standard)

### Underserved Segments

1. **AppClose refugees**: Thousands of users displaced by AppClose's Jan 2026 paywall. BestInterest captured some, but BestInterest has no payment feature.
2. **Power payment users**: Parents making 5+ payments/month who are locked into OFW Premium/Max purely for unlimited OFPay.
3. **AI-curious moderate-conflict parents**: Not high-conflict enough to need DivorceX's $36/mo, but want more than basic messaging. No product serves this segment at $5-10/mo.

### Technology Enablers

1. **LLM APIs are cheap and capable**: Claude/GPT-4 class models can detect schedule agreements in chat, rewrite hostile messages, and categorize expenses. Cost per API call is negligible at scale (<$0.01 per message analysis).
2. **Stripe Connect eliminates regulatory burden**: Platforms can operate under Stripe's money transmission licenses rather than obtaining state-by-state MTLs [Appendix 1].
3. **AI-assisted development (Claude Code, Cursor)**: A solo founder can build a production app that would have required a 5-10 person team 3 years ago, radically changing the minimum viable investment.
4. **OFW's self-hosted AI is a weakness**: OFW explicitly avoids third-party AI APIs for privacy reasons, limiting their AI capabilities. A startup using state-of-the-art models via API (with proper data handling) will ship better AI features faster.

---

## Trends and Tailwinds

### Courts are Digitizing and Standardizing

Family courts are accelerating technology adoption. Per the National Center for State Courts, cloud-based court management systems saw increased adoption in 2025, and 72% of family law cases involve self-represented litigants who benefit from structured digital tools. Court orders increasingly include boilerplate language requiring "a court-approved co-parenting communication platform" rather than naming OFW specifically -- this is the wedge for new entrants to become "court-approved."

Source: [NCSC Trends 2025](https://www.ncsc.org/sites/default/files/media/document/NCSC-Trends-2025.pdf), [Clio Family Law Statistics](https://www.clio.com/blog/family-law-statistics/)

### AI Adoption in Legal Tech is Accelerating

The broader legal tech market is embracing AI rapidly. Clio, the dominant legal practice management platform, has integrated AI across its product. Family law specifically is seeing AI applied to document analysis, communication, and dispute resolution. OFW's own May 2025 ToneMeter launch validates that even the most conservative incumbent recognizes AI is table stakes.

Source: [OFW AI Blog](https://www.ourfamilywizard.com/blog/ai-intention-how-ourfamilywizard-builds-technology-real-co-parents)

### The "AppClose Paywall" Created a Market Disruption

AppClose's transition from free to $8.99/mo in January 2026 displaced its entire free user base. BestInterest explicitly launched a free tier in response (January 28, 2026 press release). This created a one-time wave of users actively seeking alternatives -- a market moment that won't repeat but signals ongoing price sensitivity in the segment.

Source: [BestInterest Press Release](https://www.globenewswire.com/news-release/2026/01/28/3227775/0/en/)

### Payment Speed is a Competitive Weapon

Stripe's same-day ACH and next-day ACH capabilities represent a meaningful upgrade over Dwolla's standard 3-4 day processing that OFW uses. In a market where payment delays cause real interpersonal conflict (late child support, disputed reimbursements), faster payments are a feature, not just an infrastructure choice.

Source: [Dwolla Transfer Times](https://www.dwolla.com/resources/understanding-payment-transfer-timelines), [Stripe ACH Pricing](https://support.stripe.com/questions/ach-direct-debit-pricing)

### The Divorce Rate is Stabilizing, but the Installed Base Keeps Growing

The US divorce rate has declined to 2.4 per 1,000 people (historic low), but the cumulative installed base of co-parenting households grows every year. With 663K-1.1M new divorces annually and 12.2M children in the child support system, the market grows through accumulation even if the inflow rate is flat. Co-parenting relationships typically last 18 years (until the youngest child turns 18), creating long customer lifetimes.

Source: [CDC FastStats](https://www.cdc.gov/nchs/fastats/marriage-divorce.htm), [Divorce.com Statistics](https://divorce.com/blog/divorce-statistics/)

---

## Regulatory and Risk Considerations

### Money Transmission: Stripe Connect is the Path

The highest regulatory risk is money transmission licensing. Operating a payment feature between co-parents technically involves "accepting funds from one person and transmitting them to another," which triggers MTL requirements in 49 states (all except Montana). However, **Stripe Connect allows platforms to operate under Stripe's existing licenses**, avoiding the need for the startup to obtain its own MTLs. This is the same model used by thousands of marketplace platforms.

Key requirements when using Stripe Connect:
- Must comply with Stripe's terms of service and platform guidelines
- KYC/AML requirements are handled by Stripe
- FinCEN MSB registration may still be required (consult legal counsel)
- Agent-of-the-payee exemption may apply in some states

Source: [Stripe MTL Explainer](https://stripe.com/resources/more/what-is-a-money-transmitter), [Modern Treasury MTL Guide](https://www.moderntreasury.com/journal/how-do-money-transmission-laws-work)

### COPPA Compliance for Children's Data

If the app stores any information about children under 13 (names, schedules, medical records), COPPA applies. Requirements include: verifiable parental consent before collecting children's data, clear privacy notices, and data minimization. This is manageable but must be designed into the product from day one.

Source: [FTC COPPA FAQ](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions)

### Court Approval is Not a License -- It is a Relationship

There is no formal "court-approved" certification for coparenting apps. OFW's court adoption comes from 20+ years of building relationships with family law judges, providing sample court order language, and offering practitioner portals. A new entrant must invest in similar relationship-building: attending family law conferences, providing sample order language, and potentially offering free practitioner accounts.

Source: [OFW Courts Page](https://www.ourfamilywizard.com/practitioners/courts), [OFW Judges Page](https://www.ourfamilywizard.com/practitioners/judges)

### Privacy and Data Security

OFW's explicit decision to self-host AI models rather than use third-party APIs reflects the sensitivity of co-parenting data. A startup using OpenAI/Anthropic APIs must have clear data processing agreements, user consent for AI processing, and potentially the ability to opt out of AI features while retaining core functionality. This is a marketing and trust challenge, not a technical barrier.

Source: [OFW AI Blog](https://www.ourfamilywizard.com/blog/ai-intention-how-ourfamilywizard-builds-technology-real-co-parents)

---

## Evidence Gaps

| Question | Why It Matters | How to Verify | Status |
|----------|---------------|---------------|--------|
| What is OFW's actual active subscriber count (not cumulative)? | TAM/market share calculations depend on this. The ~52K implied figure (from $10.5M / ~$200 avg) needs validation. | Survey OFW users, check app store active install data, or look for SEC/state filings | UNKNOWN |
| What percentage of court orders name OFW specifically vs. "a co-parenting platform"? | Determines how locked-in OFW's court moat really is | Review sample court orders from 10+ states; interview family law attorneys | UNKNOWN |
| What is BestInterest's funding and burn rate? | Determines if the most relevant AI competitor can sustain and scale | Check Crunchbase (currently no data), reach out to founder Sol Kennedy | UNKNOWN |
| What is the churn rate for coparenting apps? | LTV calculations require churn data; co-parenting relationships last 18 years but app switching is easy | No public data exists; would need to infer from app store review patterns | UNKNOWN |
| How many OFW users are on Premium/Max specifically for unlimited OFPay? | Validates the payment-user wedge strategy | Survey, or analyze OFW pricing page traffic patterns | UNKNOWN |
| What is TalkingParents' revenue and user count? | Second-largest competitor financial health is unknown | They have 17K App Store reviews suggesting substantial user base; company is private | UNKNOWN |
| Do courts accept records from new/unknown apps as evidence? | Core risk: if courts don't trust the app's records, the product fails for high-conflict users | Interview family law attorneys; review court evidentiary standards for electronic records | ASSUMED (yes, if records are unalterable and timestamped) |
| What is the actual cost of Stripe Connect for ACH transfers at scale? | Margin calculations assume published rates; volume discounts may apply | Contact Stripe sales for custom pricing | KNOWN (published: 0.8% capped at $5 for debit, $1 flat for credit) |
| What are OFW's Spectrum Equity investment terms? | Understanding OFW's capitalization and growth obligations could reveal strategic constraints | Undisclosed; Spectrum Equity typically invests $25M-$250M in growth-stage companies | UNKNOWN |

---

## Appendix

### [1] Money Transmission Licensing via Stripe Connect

Stripe Connect allows platforms to benefit from Stripe's money transmission licenses in all required US states. The platform acts as a facilitator, not a money transmitter, because Stripe handles the actual movement of funds. This structure has been validated by thousands of marketplace platforms (DoorDash, Lyft, Instacart at scale; smaller platforms at startup stage). Key considerations:

- **No MTL required for the platform** when using Stripe Connect in "destination charges" or "separate charges and transfers" mode
- **FinCEN MSB registration** may still be advisable (consult legal counsel)
- **Stripe handles KYC/AML** for connected accounts
- **Cost**: 0.8% capped at $5 per ACH debit, $1 per ACH credit, $4 per ACH return
- **Settlement**: Standard 2 business days for card payments; 1-4 business days for ACH (same-day ACH available for additional fee)

Sources: [Stripe Connect Features](https://stripe.com/connect/features), [Stripe MTL Info](https://stripe.com/resources/more/what-is-a-money-transmitter), [Venable MTL Analysis](https://www.venable.com/insights/publications/2018/06/money-transmission-in-the-payment-facilitator-mode)

### [2] OFW Pricing Tier Detail

| Tier | Monthly | Annual | 2-Year | OFPay Limit | Key Additions |
|------|---------|--------|--------|------------|---------------|
| Choose Your Own | $9.17+ | $110+ | $220+ | Add-on | 1GB storage, ToneMeter |
| Essentials | $11.50 | $150 | $276 | 12 payments/yr (no fee) | 5GB, 45 min calls, schedule tools |
| Premium | $16.50 | $216 | $396 | Unlimited (no fee) | Unlimited calls, unlimited storage |
| Max | $22.99 | $300 | $552 | Unlimited (no fee) | Call recordings + transcription |

Lower-tier users who exceed OFPay limits pay $2.50 per transaction. The $25 returned payment fee (NSF) is a significant penalty.

Source: [OFW Pricing](https://www.ourfamilywizard.com/plans-and-pricing), [OFW OFPay FAQ](https://support.ourfamilywizard.com/hc/en-us/articles/26331992272397-OFW-Pay-FAQs)

### [3] ACH Cost Comparison

| Provider | Per-Transaction Cost | Speed | Max Fee | Notes |
|----------|---------------------|-------|---------|-------|
| Stripe ACH Debit | 0.8% of amount | 3-5 biz days | $5 cap | Cheapest for transfers >$625 |
| Stripe ACH Credit | $1 flat | 1-2 biz days | $1 | Best for known-amount transfers |
| Stripe Same-Day ACH | 0.8% + $1.50 | 0-1 biz days | $5 cap + $1.50 | Premium option for fast settlement |
| Dwolla Standard | ~$0.25 (historical) | 3-4 biz days | Custom | Now custom pricing; OFW's current provider |
| ACH return fee (Stripe) | $4 flat | N/A | N/A | NSF/insufficient funds |

For a typical $100 child expense reimbursement: Stripe ACH Debit = $0.80, Stripe ACH Credit = $1.00. For $1,000 child support: Stripe ACH Debit = $5.00 (capped). Annual cost for 24 payments averaging $200: ~$19-$24.

Sources: [Stripe ACH Pricing](https://support.stripe.com/questions/ach-direct-debit-pricing), [Swipesum Stripe Fee Guide](https://www.swipesum.com/insights/guide-to-stripe-fees-rates-for-2025), [Dwolla Pricing](https://www.dwolla.com/pricing)

### [4] Search Methodology

The following web searches were conducted on 2026-03-15:

1. OurFamilyWizard pricing, features, funding, revenue, AI roadmap
2. TalkingParents pricing, features, tier comparison
3. Coparenting app competitor landscape (AppClose, 2Houses, coParenter, WeParent, Custody X Change, DComply, SupportPay)
4. AI coparenting apps (BestInterest, DivorceX, Parent Copilot)
5. US divorce statistics, children in custody, market sizing
6. Coparenting app market size and growth forecasts
7. Stripe/Dwolla ACH pricing and settlement times
8. Money transmission licensing for fintech apps
9. Court-mandated coparenting app requirements
10. COPPA/privacy requirements for children's data
11. Reddit and review site complaints about OFW
12. OFW Spectrum Equity investment details
13. AppClose shutdown/paywall transition
14. Open source coparenting alternatives (none found)

Primary data sources: Company websites (direct), market research reports (third-party), review platforms (user-generated), press releases (company-stated), app store listings (platform data).
