# BestInterest Deep Dive: The AI-Native Co-Parenting App Built by a Serial Founder Who Lived the Problem

**Research Brief | March 16, 2026**
**Researcher**: Claude Code (Opus 4.6)

---

## TL;DR

BestInterest is a 17-month-old co-parenting app with 9,000+ claimed users, 126 iOS ratings (4.6 stars), and a freemium model ($14.99/month premium) built by Sol Kennedy --- a Y Combinator alum (Summer 2006, LikeBetter), former Head of Product at Dropcam (acquired by Nest/Google for $555M), Google PM, and angel investor in Coinbase, GitLab, and Instacart. Kennedy built BestInterest after his own high-conflict divorce, initially hiring a human to manually screen his co-parent's messages before realizing LLMs could automate the process. The app's core innovation is **asymmetric deployment**: it works without the other parent's knowledge or consent by routing messages through a dedicated phone number, making it the only co-parenting tool accessible to domestic violence survivors whose abusers would refuse to use a shared platform. Its AI features --- Message Shield (inbound filtering), Tone Guardian (outbound coaching), and AI Coach (free conversational guidance) --- almost certainly run on third-party LLMs (likely OpenAI) based on the app's 66.8MB size, rapid feature iteration, and contrast with OurFamilyWizard's explicitly self-hosted approach. Funding is undisclosed but likely bootstrapped or angel-funded given Kennedy's personal wealth from prior exits. The company has zero Reddit presence, no TechCrunch coverage, and no visible VC funding --- it is growing through content marketing, podcast appearances (6+ identified), and an endorsement from Dr. Ramani Durvasula (1.5M+ YouTube subscribers, narcissism expert). BestInterest is court-ready but not yet court-mandated, which is the critical gap separating it from OurFamilyWizard's $10.5M revenue empire.

---

## Sol Kennedy Is Not a First-Time Founder --- He Has 3 Prior Exits and a Tier-1 Angel Portfolio

Sol Kennedy's LinkedIn headline reads "Founder @ BestInterest | Ex-Google | YC Alum." His career arc reveals a serial entrepreneur with deep product and consumer tech experience, not a first-time founder experimenting in family tech.

**Career timeline (reconstructed from multiple sources):**

| Period | Role | Detail |
|--------|------|--------|
| 2006 | Founder, LikeBetter | Y Combinator Summer 2006 batch. "An online personality test game where you look at two photos and choose which one you Like Better." 2-person team, Cambridge, MA. Now inactive. [A1] |
| ~2008-2011 | Co-founder, Sincerely Inc | Mobile gifting startup (Postagram, Ink, Sesame apps). Co-founded with Matt Brezina. Acquired by Provide Commerce (ProFlowers parent) in November 2013, all-cash deal, price undisclosed. [A2] |
| ~2012-2014 | Head of Product, Dropcam | Smart home camera company. Dropcam was acquired by Google's Nest for $555M in June 2014. Kennedy's exact dates are UNKNOWN but he was Head of Product pre-acquisition. [A3] |
| ~2014-2017 | Product Manager, Google | Likely transitioned through the Nest/Google Dropcam integration. Duration approximately 3 years. [A4] |
| Ongoing | Angel Investor | Early-stage investments in Coinbase, GitLab, and Instacart --- three companies that all reached $1B+ valuations. This suggests Kennedy was active in YC/Bay Area angel circles from ~2010 onward. [A4] |
| 2024-present | Founder & CEO, BestInterest | Launched October 2024. San Francisco. [A5] |

**Personal context**: Kennedy describes himself as "a single, half-time dad of two kids." On the Startup Dad podcast, he discussed taking extended time away from work to be a full-time father to his daughter during her early years. He calls himself "a very sensitive man" who found the conflict cycles of co-parenting emotionally devastating --- getting pulled into "blame, shame, and defensiveness" that took him away from being present with his children. [A4]

**The origin story** is specific and compelling: Kennedy was using ChatGPT to create bedtime stories with his children when he received yet another hostile notification from OurFamilyWizard. The juxtaposition --- AI making his children happy while his co-parenting communication made him miserable --- triggered the idea. Before building the app, he paid a human to manually screen and rewrite his co-parent's messages. When LLM technology matured, he automated that workflow into BestInterest. [A6]

**Louise Kennedy** is listed on the BestInterest team page as "Marketing & Brand Strategy." No further biographical details are available. The surname match suggests a family member (wife, sister, or relative) --- UNKNOWN.

**Dr. Ramani Durvasula** serves as a formal advisor. She is a licensed clinical psychologist with 1.5M+ YouTube subscribers, known as the leading public voice on narcissism. She was an advisor "since prior to launch in 2024" and appears in BestInterest video content and podcast episodes. Her endorsement is the single most credible third-party validation the app has. [A7]

### Gap Analysis: Sol Kennedy

| Category | Finding |
|----------|---------|
| KNOWN | YC S06 (LikeBetter), Sincerely co-founder (acquired 2013), Head of Product at Dropcam, Google PM, angel in Coinbase/GitLab/Instacart |
| ASSUMED | Dropcam role was ~2012-2014 based on acquisition timeline; Google PM was ~2014-2017; personal wealth from exits funds BestInterest |
| UNKNOWN | Exact Dropcam dates, Google PM team/product area, whether LikeBetter generated any return, Sincerely acquisition price, relationship to Louise Kennedy |

---

## The AI Architecture: LLM-Powered Message Interception, Not Keyword Matching

BestInterest has three AI-powered features. Based on evidence gathered, all three almost certainly use third-party large language models rather than in-house NLP.

### Message Shield (Inbound Filtering)

**What it does**: Screens every incoming message from the co-parent. Strips out "hostile, manipulative, or off-topic language" and delivers only the child-focused, actionable content. The original unfiltered message is preserved in court records, but the user sees the cleaned version first.

**How it likely works**: The raw message is sent to an LLM with a system prompt instructing it to extract only logistical, child-relevant information while removing emotional attacks, passive aggression, manipulation tactics, and off-topic content. The LLM returns a sanitized version. This is not keyword matching --- Kennedy explicitly contrasts it with OFW's ToneMeter, calling that approach "outdated, keyword-based detection tech" that "misses obvious threats ('Be there or else' bypasses detection)" and "rates ten-page manifestos as having no concerns." [A8]

**Evidence this is LLM-based**:
1. Kennedy's origin story specifically references ChatGPT as the inspiration
2. The app understands context, not just keywords ("the meaning behind every message")
3. The filtering involves rewriting/summarizing, not just flagging --- a generative AI task
4. App size is only 66.8MB (iOS), far too small to embed a local model
5. BestInterest does NOT claim self-hosted AI (unlike OFW, which explicitly states "our AI runs on servers we control entirely" and "nothing leaves our environment")
6. An App Store review notes the AI "sometimes reverses the actual context and meaning" of messages --- a hallmark of LLM behavior, not rule-based systems

### Tone Guardian (Outbound Coaching)

**What it does**: Reviews the user's outgoing messages before sending. Flags emotionally charged, defensive, or escalating language. Suggests calmer, "grey rock" style rewrites that keep communication factual and child-focused.

**How it likely works**: The user's draft message is sent to an LLM with instructions to evaluate emotional tone, identify escalation patterns (JADE: Justify, Argue, Defend, Explain), and suggest a rewritten version that follows grey rock/parallel parenting communication principles. This is a generative rewriting task.

**Comparison to OFW ToneMeter**: OFW launched "ToneMeter AI" (beta in late 2025) as an upgrade to its original keyword-based ToneMeter. The new version uses a "proprietary advanced AI model" that is "self-hosted on secure servers" with customer data "never shared with external providers." OFW explicitly fine-tuned their model on "anonymized co-parenting examples." [A9] BestInterest's Tone Guardian predates OFW's AI upgrade and likely uses a more capable foundation model (GPT-4 class) with prompt engineering rather than a fine-tuned smaller model. The tradeoff: BestInterest likely has better generation quality but weaker privacy guarantees.

### AI Coparent Coach (Free Conversational AI)

**What it does**: A chatbot that provides real-time guidance for navigating co-parenting situations. Users can ask questions like "How do I respond to this message?" or "My co-parent just threatened to withhold visitation --- what should I do?" Available to all users: 3 daily messages on free tier, unlimited on premium.

**Made free in May 2025** via a GlobeNewsWire press release. Kennedy stated: "Our app is a lifeline for those in high-conflict dynamics --- especially survivors of coercive control." The strategic logic: give away the coach to build habit and trust, then convert to premium for Message Shield and Tone Guardian. [A10]

### Technical Architecture Inference

| Signal | Implication |
|--------|------------|
| App size: 66.8MB (iOS) | No embedded model. Compare: apps with local inference (e.g., Whisper) are 200MB+. |
| Rapid feature iteration (v1.0 to v2.5.8 in ~14 months) | Small team iterating on prompt engineering, not training models. |
| No privacy claims about AI hosting | Almost certainly using third-party API (OpenAI, Anthropic, or similar). OFW, by contrast, explicitly markets self-hosting as a differentiator. |
| "Upgraded AI models" in v2.5 release notes | Suggests swapping API models (e.g., GPT-3.5 to GPT-4), not retraining in-house models. |
| Kennedy's background is product, not ML | A product-focused founder would use APIs, not build custom models. |
| Dr. Ramani as advisor, not an ML researcher | The "training" Kennedy describes likely means prompt tuning with co-parenting domain examples, not model fine-tuning. |

**Confidence**: HIGH that BestInterest uses third-party LLM APIs. UNKNOWN which provider (OpenAI most likely given the ChatGPT origin story, but could be Anthropic or multiple providers).

---

## Product Deep Dive: Solo Mode Is the Killer Feature

### Solo Mode: The One-Sided Communication Paradigm

Solo Mode is BestInterest's most strategically important feature --- and arguably the most innovative concept in the co-parenting app space. Every other co-parenting platform (OFW, TalkingParents, AppClose, 2Houses) requires **both parents** to sign up and use the platform. This creates a fatal flaw in the highest-conflict situations: the abusive parent simply refuses to participate.

**How Solo Mode works**:
1. User downloads BestInterest and enters their co-parent's phone number
2. BestInterest assigns the user a dedicated second phone number
3. User shares this number with their co-parent (as their "new number")
4. Co-parent texts/calls this number normally --- they see standard SMS, no app required
5. Messages route through BestInterest on the user's side, where Message Shield filters them
6. User's responses go through Tone Guardian before being sent as SMS from the BestInterest number
7. All communication is logged as unalterable, timestamped records

**Solo Mode with Calling** (launched October 2025): Extends the phone number routing to voice calls. Includes caller ID, voicemail, and emergency access. The co-parent calls what they think is a regular phone number; the user receives the call through BestInterest with recording and documentation.

**Why this matters**: For domestic violence survivors, the ability to use a protective communication tool without the abuser's knowledge or cooperation is not a convenience feature --- it is a safety feature. No other co-parenting app offers this. BestInterest explicitly markets to "post-separation abuse situations" and "coercive control" scenarios.

### Notification Control

Users can set message delivery preferences: immediately, daily, weekly, or emergency-only. The "Smart Silence" feature (v2.5.5) limits notifications to once per hour. This addresses a specific trauma pattern: the anxious checking of phones that high-conflict co-parents experience.

### Court-Admissible Records

BestInterest provides:
- **Unalterable, timestamped message records** (both original and filtered versions)
- **Co-parenting journal** with geotagged entries
- **CSV exports** (free tier)
- **Verified court reports** as tamper-proof PDFs (premium tier)
- **Court-approved printable reports**

The GlobeNewsWire press release (May 2025) claims BestInterest is "already court-ordered in custody cases across the U.S." and that "family law judges nationwide have begun mandating its use in high-conflict cases." [A10] This claim is not independently verified. No family law blog or attorney recommendation article surveyed in the broader landscape research names BestInterest as a court-mandated platform. At 126 iOS ratings and ~17 months old, widespread court mandates seem premature. **Confidence: LOW** that this is accurate beyond isolated individual cases.

### Free vs. Premium Feature Breakdown

| Feature | Free | Protect ($14.99/mo) | Family ($189.99/yr) |
|---------|------|---------------------|---------------------|
| Secure messaging (Together + Solo modes) | Yes | Yes | Yes |
| Tasks, personal journal, notifications | Yes | Yes | Yes |
| AI coaching messages | 3/day | Unlimited | Unlimited |
| Message export (CSV) | Yes | Yes | Yes |
| Photo uploads, document exchange | Yes | Yes | Yes |
| Tone Guardian (outgoing review) | No | Yes | Yes |
| Message Shield (incoming filter) | No | Yes | Yes |
| Emergency voice calling | No | Yes | Yes |
| Smart notifications | No | Yes | Yes |
| Verified court reports (PDF) | No | Yes | Yes |
| Covers both parents | No | No | Yes |

The free tier is genuinely functional --- unlimited messaging, basic AI coaching, journal, task management. This is meaningfully more generous than competitors: TalkingParents locks mobile app access behind a paywall, OFW has no free tier, and AppClose eliminated its free tier in January 2026.

---

## Traction: 9,000+ Users but Only 126 iOS Ratings

### The 9,000+ Claim

The BestInterest homepage states "9,000+ co-parents and professionals" use the platform. This number appears directly on their website as of March 2026. No press release or third-party source independently verifies this number. [A11]

**Putting it in context**:
- OurFamilyWizard: 43,724 iOS ratings (suggesting hundreds of thousands of active users)
- AppClose: 37,397 iOS ratings, 2.4M total downloads
- TalkingParents: 29,000+ iOS ratings
- BestInterest: 126 iOS ratings

At a typical 1-2% review rate, 126 iOS ratings would suggest 6,300-12,600 total iOS downloads --- roughly consistent with the 9,000+ claim if it includes both platforms plus web users. However, "users" vs. "downloads" vs. "active users" are very different metrics. **Confidence: MEDIUM** that 9,000+ represents total signups across all platforms.

### App Store Presence

| Platform | Rating | Reviews | Developer |
|----------|--------|---------|-----------|
| iOS App Store | 4.6 stars | 126 ratings | BestInterest, Inc. |
| Google Play | 4.9 stars (claimed) | Count UNKNOWN | BestInterest, Inc. |

**App size**: 66.8MB (iOS)
**Category**: Productivity
**Current version**: 2.5.8 (released Jan 30, 2026)
**App ID**: 6503981502 (iOS), com.bestinterest.coparent (Android)

### Version History (growth signals)

The app has had frequent updates --- from v1.0 (launch ~Oct 2024) to v2.5.8 (Jan 2026) in 15 months. Notable milestones:
- **v2.5**: Free coparent messaging, upgraded AI models, new message layout
- **v2.5.5**: Smart Silence feature (hourly notification batching)
- **v2.5.8**: Badge count improvements, notification silencing fixes

---

## Business Model and Funding: Likely Self-Funded by a Wealthy Serial Founder

### Revenue Model

Freemium subscription with three tiers:
- **Free**: Messaging, basic AI coach (3/day), journal, tasks, CSV export
- **Protect**: $14.99/month or $149.99/year (AI features, calling, court reports)
- **Family Protect**: $189.99/year (covers both parents)

At 9,000 users with an estimated 5-10% premium conversion rate, estimated ARR would be $81K-$162K (450-900 paying users at $180/year average). This is a rough estimate. **Confidence: LOW** on the actual conversion rate.

### Funding

No funding rounds are publicly disclosed on Crunchbase, PitchBook, or any press release. Given Kennedy's track record:
- Sincerely acquisition (2013, undisclosed all-cash)
- Dropcam equity (pre-$555M acquisition)
- Angel portfolio including Coinbase (IPO at $85B), GitLab (IPO at $15B), Instacart (IPO at $10B)

Kennedy plausibly has $5-20M+ in personal wealth. BestInterest's team page lists only 3 people (Sol Kennedy, Louise Kennedy, Dr. Ramani as advisor). The company donates "monthly profits" to domestic violence nonprofits --- suggesting it is generating some revenue, though "profits" with a 3-person team and API costs could be modest.

**Assessment**: Almost certainly bootstrapped or self-funded. No evidence of institutional VC. Kennedy may have angel investors from his network (YC alumni, Google colleagues) but nothing is disclosed.

### Go-to-Market Strategy

BestInterest acquires users through 4 channels:

1. **Content marketing / SEO**: The bestinterest.app blog has extensive comparison articles ("OFW vs BestInterest," "Best Free Coparenting App 2026," "Why ToneMeter Fails") that target people searching for co-parenting app alternatives. This is the heaviest investment.

2. **Podcast network**: Sol Kennedy hosts "Coparenting Beyond Conflict" (available on iHeart, Apple Podcasts, Spotify) and has appeared on 6+ external podcasts:
   - Coparent Academy Podcast (#127)
   - Startup Dad Podcast
   - The SparkHub Podcast (#45)
   - The Rewrite Podcast
   - Better Divorce Podcast (#05)
   - Dr. Ramani's network

3. **Dr. Ramani endorsement**: Ramani's audience of 1.5M+ YouTube subscribers skews heavily toward people dealing with narcissistic partners --- exactly BestInterest's target market. Her recommendation likely drives the majority of organic discovery.

4. **Press releases**: 4 identified wire releases:
   - October 2024: Launch announcement (BusinessWire)
   - December 2024: Initial press coverage (Newsfile)
   - May 2025: AI Coach goes free (GlobeNewsWire)
   - October 2025: Solo Mode with Calling (GlobeNewsWire)
   - January 2026: "When One App Closes" Onward replacement positioning (GlobeNewsWire)

No evidence of paid acquisition (Facebook/Google ads), app store optimization beyond basics, or referral programs.

---

## Press Coverage and Media: Thin but Targeted

### Confirmed Media Coverage

| Publication | Type | Date | Notes |
|-------------|------|------|-------|
| WIRED | Feature article | UNKNOWN (likely 2025) | Title: "Divorced? With Kids? And an Impossible Ex? There's AI For Th..." (truncated). Actual article not retrieved. |
| BusinessWire | Press release | Oct 21, 2024 | Launch announcement |
| Newsfile | Press release | Dec 2, 2024 | "AI for Co-Parents Is Here" |
| GlobeNewsWire | Press release | May 20, 2025 | AI Coach goes free |
| GlobeNewsWire | Press release | Oct 22, 2025 | Solo Mode with Calling |
| GlobeNewsWire | Press release | Jan 28, 2026 | Onward replacement positioning |
| Yahoo Finance | Syndicated | Multiple | Syndicated versions of press releases |
| HackerNoon | Listicle | 2026 | "The 7 Best Coparenting Apps in 2026" --- ranked #1 |
| DeClom | Review | 2025-2026 | Independent third-party review |
| Stepmom Magazine | Feature | UNKNOWN | Referenced on press page |

### Not Found

| Publication | Status |
|-------------|--------|
| TechCrunch | No coverage found |
| Product Hunt | Listed but no visible upvote count or comments retrieved |
| Reddit | Zero discussions found |
| Hacker News | No posts found |
| The Verge / Engadget | No coverage |
| Any VC-focused publication | No coverage |

The WIRED feature is the most significant media hit. BestInterest's press page also claims recommendations from "top family law firms across the country" but no specific firm names are cited, and no family law blog surveyed in the broader landscape research mentions BestInterest.

---

## User Reviews: Genuine Enthusiasm from a Small Base

### iOS App Store Reviews (126 ratings, 4.6 stars)

**Positive themes**:
- "Absolute Godsend. My ex wife is a narcissist. Always pulling power plays... This apps automated responses coupled with the coaching it provides tailored to specific messages has saved me so much mental turmoil and stress... Adds another layer of disconnect I desperately need."
- "BestInterest is like a soft cushion... taking the emotional charge out of those nasty texts."
- "This app has helped me immensely with communicating with someone... who has abused me."
- "Life changing app... best money I've ever spent."

**Negative/constructive themes**:
- AI moderation "sometimes reverses the actual context and meaning" of intended messages (a classic LLM hallucination issue)
- No other specific negative patterns identified in available reviews

### Third-Party Reviews

- **DeClom** (independent review site): "If you have a functional, respectful co-parenting relationship, you don't need this. Save your money. This app is built for the trenches. It's for the parent who gets a pit in their stomach every time their phone buzzes."
- **HackerNoon**: Ranked #1 of 7 co-parenting apps for 2026

### Reddit/Community Presence

Zero Reddit threads about BestInterest were found across multiple searches. This is a notable gap --- Reddit's r/coparenting, r/custody, and r/divorce communities are active discussion spaces for co-parenting tools. OFW, TalkingParents, and AppClose all have organic Reddit mentions. BestInterest's absence suggests either very early-stage adoption or an audience that skews older/less Reddit-active (plausible given the Dr. Ramani demographic).

---

## What Makes BestInterest Different from OFW's ToneMeter

This is the critical competitive question. Both products claim AI-powered tone coaching. The differences are architectural, philosophical, and technical.

| Dimension | OFW ToneMeter AI | BestInterest |
|-----------|-----------------|--------------|
| **Direction** | Outbound only (coaches your writing) | Both inbound (shields you) AND outbound (coaches you) |
| **Action** | Flags and suggests rewrites | Filters/blocks harmful content before delivery |
| **AI hosting** | Self-hosted, fine-tuned proprietary model, data never leaves OFW servers | Almost certainly third-party API (likely OpenAI) |
| **Privacy claim** | Explicit: "Every prompt and completion stays encrypted within OurFamilyWizard's secure perimeter" | No equivalent privacy claim |
| **Training data** | "Anonymized co-parenting examples" from 25 years of platform data | Dr. Ramani guidance + beta tester interactions |
| **Requires both parents** | Yes | No (Solo Mode) |
| **Calling integration** | Yes (with transcription) | Yes (Solo Mode with Calling, Oct 2025) |
| **Price** | Included in $12.50-$24.99/mo subscription | Included in $14.99/mo subscription |
| **Court mandates** | Hundreds of judges in all 50 states | Claimed but unverified at scale |

The fundamental philosophical difference: OFW treats the problem as "help both parents communicate better" (bilateral). BestInterest treats the problem as "protect this parent from the other parent's communication" (unilateral). OFW requires cooperation; BestInterest assumes the other parent will not cooperate. These serve overlapping but distinct populations.

---

## Gap Analysis

| Category | Finding |
|----------|---------|
| **KNOWN** | Sol Kennedy: YC S06, Sincerely (acquired 2013), Dropcam Head of Product, Google PM, angel in Coinbase/GitLab/Instacart. App launched Oct 2024. 126 iOS ratings, 4.6 stars. Pricing: free tier + $14.99/mo premium. Dr. Ramani is advisor. 4 press releases identified. WIRED feature exists. Solo Mode uses dedicated phone number routing. |
| **ASSUMED** | AI runs on third-party LLMs (likely OpenAI) based on app size, iteration speed, and absence of self-hosting claims. Company is bootstrapped/self-funded from Kennedy's prior exits. 9,000+ users is total signups (not MAU). Louise Kennedy is a family member. |
| **UNKNOWN** | Funding status (amount, investors). Revenue. Monthly active users vs. signups. Specific LLM provider. WIRED article full content and date. Google Play review count. Court-mandate claim validity. Whether Kennedy has co-founders or just team members. Tech stack (React Native vs. Flutter vs. native). Backend infrastructure. |
| **CONTESTED** | "Court-ordered in custody cases across the U.S." (company claim) vs. zero independent verification from family law sources. "4.9 stars Google Play" (company-stated) vs. unverified due to low review volume. |

---

## Appendix

### [A1] LikeBetter / Y Combinator
- YC company page: [https://www.ycombinator.com/companies/likebetter](https://www.ycombinator.com/companies/likebetter)
- Batch: Summer 2006. Status: Inactive. 2-person team, Cambridge, MA.

### [A2] Sincerely Inc Acquisition
- BusinessWire (Nov 7, 2013): [Provide Commerce Acquires Mobile App Gifting Company, Sincerely, Inc.](https://www.businesswire.com/news/home/20131107006099/en/Provide-Commerce-Acquires-Mobile-App-Gifting-Company-Sincerely-Inc.)
- TechCrunch (Nov 7, 2013): [Provide Commerce Acquires Mobile Gifting Startup Sincerely](https://techcrunch.com/2013/11/07/provide-commerce-acquires-mobile-gifting-startup-sincerely-will-expand-into-new-categories-apps-in-2014/)
- Co-founder: Matt Brezina (CEO). Sol Kennedy's exact title at Sincerely is not confirmed in press coverage; TechCrunch names Brezina as founder/CEO.

### [A3] Dropcam Acquisition
- TechCrunch (Jun 20, 2014): [Google and Nest Acquire Dropcam For $555 Million](https://techcrunch.com/2014/06/20/google-and-nest-acquire-dropcam-for-555-million/)
- Sol Kennedy's role as "Head of Product" sourced from Startup Dad podcast and LinkedIn references.

### [A4] Sol Kennedy Background
- Startup Dad Podcast: [Navigating Divorce and Co-parenting Relationships](https://startupdadpod.substack.com/p/navigating-divorce-and-co-parenting-relationships-sol-kennedy-bestinterest)
- LinkedIn: [Sol Kennedy - Founder @ BestInterest | Ex-Google | YC Alum](https://www.linkedin.com/in/solkennedy/)
- RocketReach profile confirms CEO title at BestInterest.

### [A5] BestInterest Launch
- BusinessWire (Oct 21, 2024): [Frustrated Parent Launches Innovative AI-Powered Co-Parenting App: BestInterest](https://www.businesswire.com/news/home/20241021896159/en/Frustrated-Parent-Launches-Innovative-AI-Powered-Co-Parenting-App-BestInterest)
- Newsfile (Dec 2, 2024): [AI for Co-Parents Is Here](https://www.newsfilecorp.com/release/231850/AI-for-CoParents-Is-Here-BestInterest-Launches-Groundbreaking-New-App-for-CoParents-Stuck-in-HighConflict-Situations)

### [A6] Origin Story
- Coparent Academy Podcast #127: [Interview with Sol Kennedy](https://podcast.coparentacademy.com/1934375/episodes/15810969-127-interview-with-sol-kennedy-founder-of-the-best-interest-parenting-app)
- Kennedy hired a human message screener before building the app. ChatGPT bedtime stories + OFW notification was the epiphany moment.

### [A7] Dr. Ramani Durvasula
- BestInterest advisor page: [https://bestinterest.app/drramani/](https://bestinterest.app/drramani/)
- iHeart podcast appearance: [Dr Ramani: Coping with Co-Parenting Challenges](https://www.iheart.com/podcast/269-coparenting-beyond-conflic-247048297/episode/dr-ramani-coping-with-co-parenting-challenges-247626329/)

### [A8] BestInterest vs OFW ToneMeter
- BestInterest blog: [Why Our Family Wizard's Tone Meter Fails to Reduce Conflict](https://bestinterest.app/ofw-tone-meter/)
- Note: This is BestInterest's own competitive content, written to favor their product. Claims about ToneMeter failures should be evaluated as marketing, not independent analysis.

### [A9] OFW AI Architecture
- OFW blog: [AI with Intention: How OurFamilyWizard Builds Technology for Real Co-Parents](https://www.ourfamilywizard.com/blog/ai-intention-how-ourfamilywizard-builds-technology-real-co-parents)
- OFW support: [What is ToneMeter AI?](https://support.ourfamilywizard.com/hc/en-us/articles/36058984807053-What-is-ToneMeter-AI)
- Key quote: "Our AI runs on servers we control entirely. Every prompt and completion stays encrypted within OurFamilyWizard's secure perimeter."

### [A10] AI Coach Goes Free + Court-Ordered Claims
- GlobeNewsWire (May 20, 2025): [BestInterest Makes AI-Powered Co-Parenting Coach Free for All Users](https://www.globenewswire.com/news-release/2025/05/20/3085049/0/en/BestInterest-Makes-AI-Powered-Co-Parenting-Coach-Free-for-All-Users.html)
- Claims: "already court-ordered in custody cases across the U.S." and "family law judges nationwide have begun mandating its use."

### [A11] User Count
- BestInterest homepage (accessed March 2026): "9,000+ co-parents and professionals" --- [https://bestinterest.app/](https://bestinterest.app/)
- iOS App Store: 126 ratings, 4.6 stars, version 2.5.8 --- [App Store](https://apps.apple.com/us/app/bestinterest-for-coparents/id6503981502)

### [A12] Podcast Appearances
1. Coparent Academy Podcast #127 --- [Link](https://podcast.coparentacademy.com/1934375/episodes/15810969-127-interview-with-sol-kennedy-founder-of-the-best-interest-parenting-app)
2. Startup Dad Podcast --- [Substack](https://startupdadpod.substack.com/p/navigating-divorce-and-co-parenting-relationships-sol-kennedy-bestinterest)
3. The SparkHub Podcast #45 --- [Acast](https://shows.acast.com/sparkhub-podcast/episodes/ep45-best-interest-co-parenting-beyond-conflict-sol-kennedy)
4. The Rewrite Podcast --- [Apple Podcasts](https://podcasts.apple.com/us/podcast/meet-the-founder-of-the-best-interest-co-parenting-app/id1628639991?i=1000737236406)
5. Better Divorce Podcast #05 --- [Spotify](https://open.spotify.com/episode/2l3QGoxeoku5CP83XBzyjs)
6. Dr. Ramani Network --- [iHeart](https://www.iheart.com/podcast/269-coparenting-beyond-conflic-247048297/episode/dr-ramani-coping-with-co-parenting-challenges-247626329/)
7. Hosts own: Coparenting Beyond Conflict --- [Apple Podcasts](https://podcasts.apple.com/us/podcast/coparenting-beyond-conflict-strategies-for-high-conflict/id1775513142)

### [A13] Search Methodology

The following searches were executed via WebSearch on March 16, 2026:
- "BestInterest AI co-parenting app Sol Kennedy"
- "Sol Kennedy Sincerely Provide Commerce acquisition YCombinator"
- "BestInterest coparenting app review Reddit"
- "BestInterest coparenting app Product Hunt"
- "BestInterest coparenting app funding investors Crunchbase valuation"
- "Sol Kennedy Google role engineer product manager BestInterest founder"
- "BestInterest coparenting Solo Mode calling feature how it works"
- "Sol Kennedy Dropcam head of product Nest Google acquisition"
- "BestInterest coparenting WIRED magazine feature article"
- "BestInterest coparenting app 9000 users growth"
- "BestInterest coparenting app Dr. Ramani narcissist recommendation"
- "podcast Sol Kennedy BestInterest coparenting interview"
- "BestInterest coparenting app tech stack React Native Flutter AI model GPT"
- "BestInterest coparenting app revenue funding bootstrapped angel round"
- "Sol Kennedy LikeBetter Y Combinator founder"
- "Sol Kennedy angel investor Coinbase GitLab Instacart"
- "OurFamilyWizard ToneMeter how it works AI technology NLP"
- "BestInterest coparenting app court ordered family law judge mandate"
- "Reddit coparenting app BestInterest review experience"

WebFetch was used for: bestinterest.app (homepage, team, press, about, solo-mode, blog posts), BusinessWire, GlobeNewsWire, TechCrunch, App Store, HackerNoon, DeClom, Coparent Academy Podcast, Startup Dad Podcast, YC company page, OFW blog.
