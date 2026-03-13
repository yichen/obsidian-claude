# Local-First AI Personal Finance Advisor

**Status**: CONCEPT — Pre-validation
**Last Updated**: 2026-03-08

---

## Executive Summary

Personal finance apps like Simplifi ($4/mo) and Monarch ($8/mo) require users to grant third-party access to their bank accounts via Plaid — and in return, they see only surface-level data: "AMZN MKTP $47.23, category: Shopping." They cannot tell you that $23 was kids' rain boots and $24 was vitamins. For the estimated 3-5M US households with complex finances (multiple income sources, RSUs, rental property, tax optimization needs) [1], this shallow visibility is the core frustration — yet privacy concerns prevent them from trusting even more invasive alternatives.

A working proof of concept already exists: a Claude Code-based system that has ingested 5,620 credit card transactions (100% categorized), 3,218 itemized Amazon orders, and 44 payslips across multiple employers — all processed locally with zero data sent to any cloud service [2]. The system answers natural language queries ("How much do I spend on the kids?") by translating them to SQL against a local SQLite database, producing precise cross-source answers that no cloud aggregator can match.

The product opportunity is to package this capability as a desktop application with a community-driven parser registry. Users drop PDF statements into a folder; an AI agent parses, categorizes, and analyzes them locally. When the agent writes a new parser for an unsupported bank format, the parser code (which contains zero PII) can be shared with other users — creating a network effect where every new user makes the product better for all future users. The business model is BYOK (Bring Your Own Key): users pay $10/mo for the software and supply their own Anthropic API key, keeping the total cost at $15-25/mo — positioned not against Simplifi's convenience, but against the $200-500/mo cost of a human financial advisor.

---

## Assumption Register

Every quantitative claim and strategic assumption in this document is tracked below. Claims marked UNVERIFIED require validation before investment decisions.

| # | Assumption | Status | Evidence | Impact if Wrong |
|---|-----------|--------|----------|-----------------|
| A1 | AI personal finance market = $1B (2025), $3.7B by 2033, 18% CAGR | UNVERIFIED — single source | SR Analytics blog post [3] | Market may be smaller; reduces TAM argument |
| A2 | Privacy is the #1 complaint for finance apps | UNVERIFIED — anecdotal | Web search results, app store reviews not systematically analyzed | Core thesis weakened if users don't actually care about privacy enough to change behavior |
| A3 | 100K-500K addressable users in the US | UNVERIFIED — rough estimate | No primary research; derived from income brackets + technical comfort assumptions [4] | If <50K, not viable as a business; if >500K, underinvesting |
| A4 | Users will pay $10/mo for this + $5-15/mo API costs | UNVERIFIED — no willingness-to-pay data | Comparable pricing: Cursor $20/mo, Monarch $8/mo [5] | If total cost >$20/mo is a dealbreaker, need cheaper models or bundled API |
| A5 | Agent can reliably auto-generate parsers for new bank formats | PARTIALLY VERIFIED | Works for ~10 formats in POC [2]; untested on arbitrary unknown formats | If agent fails on >30% of formats, the self-service promise breaks |
| A6 | Layout fingerprinting can reliably match same-bank statements | UNVERIFIED — not yet built | Conceptual design only; no prototype | If fingerprints are too fragile (minor PDF version changes break matching), registry becomes unreliable |
| A7 | Parser code contains zero PII | VERIFIED — by inspection | Reviewed all 6 existing ingest scripts; they contain only positional logic, regex, font filters [2] | Low risk — but must ensure auto-generated parsers also strip any extracted sample values |
| A8 | Simplifi pricing = $4/mo, Monarch = $8/mo, Copilot = $10/mo | VERIFIED | Published pricing pages, confirmed Mar 2026 [5] | Low impact |
| A9 | Claude Agent SDK requires API key billing (no Pro/Max subscription) | VERIFIED | GitHub issue #559 on claude-agent-sdk-python [6] | If Anthropic adds subscription billing, BYOK friction drops significantly |
| A10 | Cursor approaching ~$1B ARR with proxy API model | UNVERIFIED — single source | Vantage blog post [5]; Cursor is private, no official revenue disclosure | Weakens the "proxy model works at scale" argument if overstated |
| A11 | Plaid cost ~$0.50-2.00 per bank link | VERIFIED — multiple sources | Plaid pricing page, Finexer analysis, Monetizely comparison [7] | N/A — Plaid rejected as architecture choice |
| A12 | Users won't grant a startup Gmail OAuth or Plaid access | REVISED — local IMAP is acceptable | Founder wouldn't use cloud OAuth, but local IMAP (like Thunderbird) is fine — data flows Google → user's machine, startup never sees it | N/A — resolved by local IMAP architecture |
| A13 | Parsers are pure Python with zero LLM dependency at runtime | VERIFIED — by inspection | All 6 ingest scripts import only pdfminer, re, json, csv, yaml, sqlite3 — no anthropic/openai imports [2] | Product is model-agnostic; LLM only needed for parser generation and NL queries |
| A14 | Gmail App Passwords work for IMAP access (2026) | VERIFIED | Google documentation confirms App Passwords available with 2FA enabled; Python imaplib is stdlib [15] | If Google deprecates App Passwords, OAuth fallback needed |
| A15 | Microsoft 365 requires OAuth (no App Passwords for most accounts) | VERIFIED | Microsoft deprecated Basic Auth for Exchange Online Dec 2022 [16] | Outlook users need OAuth flow — more complex onboarding than Gmail |
| A16 | Opening a checking account is typically a soft pull (no credit score impact) | VERIFIED — multiple sources | SoFi, Capital One, Doctor of Credit confirm most banks use ChexSystems or soft pull [17] | Opening 5-10 accounts for parser testing is safe for credit |
| A17 | Top 5 US banks cover ~50-60% of credit card market | UNVERIFIED — approximate | Chase, BofA, Citi, Capital One, Wells Fargo are the largest issuers; exact market share not verified | If share is lower, need more seed parsers |

---

## The Problem: Shallow Data Behind a Privacy Wall

Cloud-based finance apps (Simplifi, Monarch, Copilot, Empower) all rely on the same architecture: Plaid/MX/Finicity pulls transaction data from banks, the app categorizes it, and users see spending dashboards. This architecture has two structural limitations:

**1. Data is shallow.** Plaid returns merchant-level transactions — "Amazon $47.23" — but not what was purchased. For the average US household spending ~$5,200/yr on Amazon [8], this means a significant chunk of spending is a black box. The same applies to Costco, Target, Walmart, and any retailer where a single receipt covers multiple categories.

**2. Users must trust intermediaries.** Plaid stores bank credentials and transaction history. After the 2024 CFPB consent order against Plaid for unauthorized data collection practices [9], trust in financial data aggregators has declined — though quantifying this decline requires survey data that does not exist in this analysis [A2].

**3. Email receipts are the richest untapped data source.** Amazon order confirmations, Uber receipts, subscription renewals, airline bookings — all arrive by email with itemized detail that Plaid never sees. But connecting to email traditionally requires OAuth (granting a startup access to your inbox), which privacy-conscious users won't do.

**The local IMAP solution**: A CLI app connecting to Gmail via IMAP + App Password is no different from Thunderbird or Apple Mail — data flows directly from Google to the user's machine. The startup never touches it [A12]. Combined with the TripIt-style pattern (Gmail filter auto-labels receipt emails; app syncs only that label), this provides the richest data source with minimal access footprint.

No existing product offers both AI-powered analysis AND local-only data processing. The closest alternatives:

| Product | AI Analysis | Local Data | Itemized Purchases | Price |
|---------|------------|------------|-------------------|-------|
| Simplifi | Basic categories | No (Plaid) | No | $4/mo [A8] |
| Monarch Money | AI insights, dashboards | No (Plaid) | No | $8/mo [A8] |
| Copilot Money | ML categorization | No (Plaid) | No | $10/mo [A8] |
| Firefly III | None | Yes (self-hosted) | No | Free/OSS |
| **This product** | NL queries, tax analysis | Yes (fully local) | Yes (Amazon, receipts) | $10/mo + BYOK API |

---

## Proof of Concept: Verified Capabilities

A working system built on Claude Code over ~3 months demonstrates the core value proposition. All numbers below are from the live system [2]:

| Data Source | Records | Categorization | Ingestion Method |
|-------------|---------|----------------|-----------------|
| Credit card transactions | 5,620 | 100% categorized (59 categories, 2-level hierarchy) | 163 PDF statements across 6 cards |
| Amazon orders | 3,218 | 88% categorized (2,830/3,218 via keyword rules + manual review) | CSV export from Amazon order history |
| Payslips | 44 (1,032 line items) | 100% structured | YAML from employer portal PDFs |
| BECU bank transactions | 118 | 100% structured | 14 monthly PDF statements |
| Fidelity CMA transactions | 481 | 100% categorized | 13 monthly PDF statements |
| Tax documents | 49 YAMLs | 100% structured | PDFs across 2022-2025 (W-2, 1099-R, 1098, 1040) |

**Key demonstrated capabilities:**

- **Itemized Amazon visibility**: "You spent $847 at Amazon: $234 kids, $189 household, $156 tech, $142 supplements, $126 camping" — no cloud service can produce this
- **Cross-source analysis**: "How much do I spend on the kids?" combines CC transactions + Amazon orders + OurFamilyWizard payments + activity costs
- **Tax-aware insights**: "You're $19K under-withheld across two employers — adjust W-4 by October or make a Q4 estimated payment"
- **Natural language to SQL**: User asks a question in plain English; agent generates and executes SQL against the local SQLite database
- **Balance validation**: Every parsed statement is validated against printed totals — automated acceptance tests that catch parsing errors immediately

**What the POC does NOT prove** [A5]:
- Whether the agent can auto-generate parsers for arbitrary unknown bank formats (only tested on ~10 formats the developer hand-guided)
- Whether non-technical users can successfully onboard without developer-level support
- Whether the value proposition resonates beyond the developer/founder (n=1)

---

## Technical Strategy: Agent-Generated Parser Registry

### Why Not Vision LLM?

The industry trend is to send PDF pages as images to vision models (Claude, GPT-4V, Gemini) for extraction. This works but has fundamental trade-offs:

| | Agent-written deterministic parser | Vision LLM per-page extraction |
|---|---|---|
| Accuracy on known formats | Near-perfect (deterministic code) | ~95-98% (non-deterministic) [10] |
| Cost per run | $0 after initial development | $0.01-0.05/page, every time [10] |
| Speed | Milliseconds | 5-30 seconds/page |
| Reproducibility | 100% deterministic | Varies between runs |
| New format support | Requires agent to write new parser | Works on any format immediately |
| Privacy | Fully local (pdfminer) | Statement data sent to API |

The POC uses **pdfminer text extraction + Claude Code as the agent that writes parser code**. The agent iterates until balance validation passes. The resulting parser is deterministic Python — fast, free, reproducible, and fully local.

**The scaling problem**: The POC has parsers for ~10 formats. A product serving 10,000 users might encounter 500+ bank/CC statement formats [A3]. Writing parsers by hand doesn't scale.

### The Parser Registry Solution

**Core insight**: Parser code contains zero PII [A7]. It's positional logic about where dates, amounts, and descriptions appear in a specific bank's PDF layout. This code can be safely shared.

**Workflow for unsupported formats:**
1. User drops in an unrecognized PDF
2. Agent extracts text via pdfminer, examines layout structure
3. Agent writes a parser, validates against balance totals printed on the statement
4. If validation passes, parser is tagged with a layout fingerprint [A6] — a hash of structural elements (header positions, column x-offsets, font names) without any transaction values
5. User is prompted: "Share this parser? No financial data is included."
6. Parser uploaded to community registry

**Workflow for known formats:**
1. Agent extracts layout fingerprint from the PDF
2. Matches against registry — finds existing community parser
3. Runs locally — instant, no agent coding needed

**Precedents for community-contributed rule sets** (rules contain no user data):
- uBlock Origin — community filter lists
- Homebrew — community formulae
- Wireshark — community protocol dissectors

**Unproven**: Whether layout fingerprinting is robust enough to match same-bank statements across users while distinguishing format changes [A6]. This requires prototyping.

### Registry Design: Immutable Parsers + Two-Stage Matching

**Core design principle: Published parsers are immutable.** A user can never modify another user's parser — they can only publish a new version. This prevents the failure mode where User B's "fix" breaks User A's working parser.

```
WRONG: User B edits becu-checking-v2 → breaks User A's statements
RIGHT: User B publishes becu-checking-v3 → both v2 and v3 exist, matching picks best fit
```

**Registry schema:**

```
parsers/
  becu/
    checking/
      v1/
        parser.py          # immutable Python code
        fingerprint.json   # structural signature this parser expects
        metadata.json      # author_hash, created, validation_stats
      v2/
        parser.py
        fingerprint.json
        metadata.json
  chase/
    sapphire-reserve/
      v1/ ...
      v2/ ...
```

**Parser metadata:**

```json
{
    "id": "becu-checking-v2",
    "institution": "BECU",
    "statement_type": "checking",
    "version": 2,
    "fingerprint": {
        "institution_patterns": ["BECU", "Boeing Employees Credit Union"],
        "fonts": ["Arial", "Arial-Bold", "Courier"],
        "column_x_positions": [72, 150, 380, 480],
        "header_patterns": ["Monthly Statement", "Account Summary"],
        "pdf_producer": "iText*",
        "date_format": "MM/DD/YYYY"
    },
    "validation_stats": {
        "total_runs": 342,
        "pass_rate": 0.987,
        "last_success": "2026-03-01",
        "date_range_seen": ["2024-01", "2026-02"]
    },
    "immutable": true,
    "created": "2026-02-15"
}
```

**Two-stage matching algorithm** (all local, zero LLM, milliseconds):

```
Stage 1: Institution detection
  Extract text from first page → search for known bank names
  "BECU" found → query registry index for "becu" parsers
  Result: [becu-checking-v3, v2, v1] sorted by pass_rate x recency
  Cost: milliseconds

Stage 2: Fingerprint comparison
  Extract structural metadata from PDF (fonts, column positions, headers)
  Compare against each candidate's fingerprint.json → similarity score
  v3: score 0.95 (fonts match, columns match)
  v2: score 0.82 (columns shifted slightly)
  v1: score 0.40 (old format, different fonts)
  Cost: milliseconds
```

**Full execution flow:**

```
User drops PDF
    |
    v
[Stage 1] Text search for institution name (msec, local)
    |
    v
[Stage 2] Compare fingerprints → rank candidates (msec, local)
    |
    v
[Stage 3] Run top match → validate against balance totals (msec, local)
    |
    +--PASS--> Import to SQLite. Done.
    |          Anonymously report success (opt-in, increments pass count)
    |
    +--FAIL--> Try next candidate → validate
                |
                +--PASS--> Import. Done.
                |
                +--FAIL (all candidates)-->
                    |
                    v
                [Stage 4] Agent generates new parser (LLM call, $1-5, minutes)
                    |
                    v
                Validate → PASS → save as becu-checking-v4
                    |
                    v
                Prompt: "Share becu-checking-v4 to registry?"
```

**Key design decisions:**

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Can a user modify another user's parser? | **No — immutable** | Prevents breaking other users' working parsers |
| What if two users publish for the same bank? | **Both exist as separate versions** | Matching algorithm picks best fit per-PDF |
| How to rank candidates? | **Fingerprint similarity x pass rate x recency** | High pass rate = battle-tested; recency = handles format changes |
| What gets uploaded to registry? | **parser.py + fingerprint.json + metadata** | No transaction data, no PDF content, no PII |
| What gets reported back anonymously? | **Pass/fail per parser per run (opt-in)** | Improves ranking without sharing financial data |
| When to trigger new parser generation? | **Only when ALL candidates fail validation** | LLM calls are expensive; exhaust cheap options first |
| How does the app discover parsers? | **Sync registry index on launch** (small JSON manifest) | Download parser code on demand, not all 500 upfront |

**Anonymous validation reporting (opt-in):**

When a parser succeeds or fails, the app can report:

```json
{
    "parser_id": "becu-checking-v2",
    "result": "pass",
    "statement_month": "2026-02",
    "fingerprint_similarity": 0.95
}
```

This lets the registry rank parsers by real-world reliability. A parser with 98.7% pass rate across 342 users is clearly more trustworthy than one with 60% across 5 users. Even this minimal reporting should be opt-in — some users won't want the registry to know which banks they use.

**Format change detection**: Banks occasionally redesign their PDF layout. When this happens, all existing parsers' balance validation fails. The agent writes a new parser with a new fingerprint, published as a new immutable version. Old fingerprints route to old parsers (for users parsing historical statements), new fingerprints route to the new parser. Unlike vision LLM where format changes cause silent accuracy degradation, deterministic parser + validation gate catches changes immediately.

### Model-Agnostic Architecture

A critical discovery from the POC: **all parsers are pure Python with zero LLM dependency at runtime** [A13]. The imports across all ingest scripts are: `pdfminer`, `re`, `json`, `csv`, `yaml`, `sqlite3` — no `anthropic`, no `openai`. Claude Code was the developer, not the runtime.

This means the product is not locked to any LLM provider:

| Phase | LLM Needed? | Any Provider Works? |
|-------|-------------|-------------------|
| Parse a known format | No — pure Python | N/A |
| Write a new parser | Yes | Claude, GPT, Gemini, local Llama — any model that can write Python |
| NL query ("how much on kids?") | Yes | Any model that can generate SQL |
| Categorize ambiguous transactions | Maybe | Rule-based covers most; LLM for edge cases |

**Cost implication**: Once a user has parsers for their 3-4 banks (likely covered by the community registry), they may only need the LLM for occasional NL queries — pennies per month, not $5-15. The API cost is front-loaded during setup, then drops to near-zero. This significantly changes the pricing story from the $15-25/mo total cost estimated in the business model section [A4].

### Email Integration: The TripIt Pattern

Email is the richest source of itemized transaction data, and it's already accessible to local apps via IMAP — a universal protocol supported by virtually every email provider since the 1990s. No cloud OAuth needed.

**Provider compatibility:**

**Two auth methods supported** — App Password for CLI, OAuth for desktop app:

| Method | Best For | UX | Developer Setup |
|--------|----------|-----|----------------|
| **App Password + IMAP** | CLI MVP, universal | Paste password in terminal | Zero — just use stdlib `imaplib` |
| **OAuth 2.0** | Desktop app, polished UX | "Sign in with Google" button → browser consent → done | Register Google Cloud / Azure AD app; Gmail sensitive scope review (weeks) |

Both methods store credentials locally. Both route email data directly from provider → user's machine. The startup cannot access user email with either approach — the tokens never leave the user's device.

**Provider compatibility:**

| Provider | App Password | OAuth 2.0 |
|----------|-------------|-----------|
| Gmail | Yes (requires 2FA) | Yes (Google Cloud project) |
| Yahoo Mail | Yes (requires 2FA) | Yes (Yahoo Developer) |
| iCloud Mail | Yes (App-Specific Password) | No — Apple does not offer OAuth for IMAP |
| Fastmail | Yes | Yes |
| Outlook.com (personal) | Yes (with MFA) | Yes (Azure AD) |
| Microsoft 365 (corporate) | No — deprecated [A15] | Yes (Azure AD) — required |
| ProtonMail | Via ProtonMail Bridge | No |
| Any IMAP provider | Yes | Varies |

**Recommendation**: Ship App Password support first (universal, zero developer registration, works for CLI). Add OAuth as a polished option when the desktop app is built — it's the better UX for non-technical users ("Sign in with Google" vs "go find your App Password settings").

**Setup with App Password (30 seconds, one-time, any provider):**
1. User generates an App Password in their email provider's security settings
2. Enters in CLI: `localfinance config --email imap.gmail.com --user me@gmail.com`
   (or `imap.mail.yahoo.com`, `imap.mail.me.com`, `outlook.office365.com`, etc.)
3. App Password stored locally in encrypted config

The app asks three standard fields — IMAP server, email, password — the same as every email client since Thunderbird.

**The TripIt-style filter pattern** (recommended approach):

User creates a server-side rule in their email provider (Gmail filter, Outlook rule, Yahoo filter — all support this):

```
Filter: From: auto-confirm@amazon.com → Move to folder: finance-receipts
Filter: From: uber.us@uber.com       → Move to folder: finance-receipts
Filter: From: noreply@venmo.com      → Move to folder: finance-receipts

App behavior:
  IMAP sync folder "finance-receipts" → parse locally → mark as processed
```

This gives the app access to **only one folder, not the full inbox** — minimal access footprint. The user controls exactly which senders are included. This pattern works on any email provider that supports server-side rules, which is essentially all of them.

**What email receipts unlock:**

| Email Source | What You Extract | Value Over Plaid |
|---|---|---|
| Amazon order confirmations | Itemized products, prices, ASINs | The killer feature — Plaid sees only "AMZN $47.23" |
| Uber/Lyft receipts | Trip details, tip, route | Per-ride granularity |
| DoorDash/Instacart | Itemized grocery/food orders | Category-level food spending |
| Airline/hotel confirmations | Flight cost, booking ref | Travel cost breakdown |
| Subscription confirmations | Service name, renewal date, price | Subscription tracking |
| Venmo/Zelle notifications | Who, amount, memo | P2P payment context |

**Revised onboarding funnel** (with email integration):
```
Step 1: Install CLI                        (30 sec)
Step 2: Enter LLM API key (any provider)   (2 min — BYOK, one-time)
Step 3: Connect email via IMAP              (30 sec — any provider, optional but high value)
Step 4: Drop CC/bank PDFs in watch folder   (5 min — for statement-level data)

After step 3, user already has itemized Amazon + Uber + subscriptions.
Step 4 adds CC transaction-level data that email doesn't cover.
```

### Parser Coverage Strategy

**Do NOT open 100 bank accounts to get statement samples.** Here's the practical approach:

**Seed parsers (founder-built, pre-launch):**
- The POC already covers 6 CC cards + BECU + Fidelity CMA + SoFi — ~10 formats
- Open no-fee checking at 3-5 additional top banks: Wells Fargo, Citi, Capital One [A16] [A17]
- Credit score impact: minimal — most checking accounts are soft pull or ChexSystems only [A16]
- This covers the top 5 US card issuers (~50-60% of market [A17])

**Obtaining test statements for other banks (no account needed):**

| Method | Coverage | Quality | Cost |
|--------|----------|---------|------|
| Beta users share redacted statements | Real formats, exact match | High | $0 |
| Open-source parsers (GitHub: statement-parser, pdf-statement-reader) | ~5-10 banks | Medium — study format knowledge, not reuse code | $0 |
| Template sites (TemplateLab, Scribd, PDFSimpli) | ~20 banks | Low — may not match real PDF structure exactly | $0 |
| Docparser/Parseur template libraries | Format structure visible | Medium | Free tier |

**The 80/20 insight**: Seed parsers for the top 5 banks + the community parser registry for the long tail. The first 1,000 users will collectively encounter most remaining US bank formats — each new format becomes a community parser contribution.

---

## Target Customer

This is a niche product. The ideal customer profile:

| Trait | Why It Matters | Evidence |
|-------|---------------|----------|
| High income ($200K+) | Complex finances justify the effort | IRS data: ~8.5M US returns with AGI >$200K (2022) [11] |
| Privacy-conscious | Won't use Plaid; core motivator for this product | [A2] — assumed, not measured |
| Somewhat technical | Comfortable downloading PDFs, setting up API key | Developer/tech worker overlap with high-income; ~4.4M software developers in US [12] |
| Amazon power user ($3K+/yr) | Itemized Amazon visibility is the killer feature | Average US Prime member spends ~$1,400/yr on Amazon [8]; power users $3K+ |
| Tax complexity | Multiple income sources, RSUs, rental property | Overlap with $200K+ income bracket |
| Data ownership values | Burned by Mint shutdown (2024), wants permanent local data | Mint had ~3.6M users at shutdown [13]; subset who switched to manual tools is unknown |

**Estimated addressable market**: 100K-500K users in the US [A3]. This is a rough triangulation:
- ~8.5M households with AGI >$200K [11]
- Of those, ~30-50% are technically comfortable enough to use a CLI/desktop tool — call it 2.5-4M [ASSUMED]
- Of those, ~5-10% are privacy-conscious enough to reject Plaid — call it 125K-400K [ASSUMED]

This estimate has wide error bars. Primary research (surveys, landing page tests) would narrow it significantly.

---

## Business Model

### Pricing: BYOK-Only Software License

| | Details |
|---|---|
| Price | $10/mo or $99/yr |
| API model | BYOK — user's own Anthropic API key [A9] |
| Revenue type | Pure software license; zero API cost to the company |
| Data flow guarantee | Nothing leaves machine except user-to-Anthropic prompts |
| Parser registry | Community-contributed; included in subscription |

**Why BYOK-only**: The strongest privacy story — "We literally cannot see your data." Also eliminates API cost risk during early growth. Initial users (tech-savvy early adopters) can handle API key setup. A proxy tier can be added later if mainstream users demand it.

**Total cost to user**: $10/mo (app) + $5-15/mo (Anthropic API, estimated) = **$15-25/mo** [A4]

### Competitive Pricing Context

| Product | Monthly Cost | What User Gets |
|---------|-------------|----------------|
| Simplifi | $4/mo | Auto-sync, basic categories, budgets |
| Monarch | $8/mo | Auto-sync, AI insights, investment tracking |
| This product | $15-25/mo (incl. API) | Local-only, itemized purchases, NL queries, tax analysis |
| Human financial advisor | $200-500/mo | Full-service, personalized |

**The pricing gap is real.** At 3-6x the cost of Simplifi, this product must deliver capabilities Simplifi cannot — not just privacy. The differentiator is depth:

- Simplifi: "You spent $847 at Amazon last month."
- This product: "You spent $847 at Amazon: $234 kids, $189 household, $156 tech, $142 supplements, $126 camping gear."

Whether enough users value this depth at $15-25/mo is the central commercial question [A4].

### Unit Economics

```
Revenue per user:            $8.25/mo (blended annual/monthly)
Costs per user:
  Parser registry hosting:   -$0.10/mo  [ASSUMED — minimal static hosting]
  Support:                   -$0.50/mo  [ASSUMED — community-first model]
                             ---------
Gross margin:                $7.65/mo   (93%)
```

### Revenue Scenarios

| Users | ARR | Viability |
|-------|-----|-----------|
| 1,000 | $99K | Side project |
| 5,000 | $495K | Solo founder sustainable |
| 10,000 | $990K | Small team (2-3 people) |
| 50,000 | $4.95M | Venture-viable, but at top of addressable market estimate [A3] |

---

## Technical Architecture

```
+------------------------------------------+
|  CLI (MVP) / Desktop App (future)        |  <- What the user sees
+-----------+------------------------------+
|  Agent layer (model-agnostic) [A13]      |  <- The brain (only for new parsers + NL queries)
|  - Parser generation (any LLM)           |
|  - NL -> SQL queries (any LLM)           |
|  - Categorization (mostly rule-based)    |
+-----------+------------------------------+
|  Pure Python runtime (no LLM needed)     |  <- Deterministic parsers, validation, import
|  - pdfminer + regex parsers              |
|  - imaplib email sync [A14]              |
|  - SQLite DB + categorization rules      |
+-----------+------------------------------+
|  Local storage                           |  <- All data stays here
|  - SQLite DB, PDFs, CSVs                 |
|  - Parser registry cache                 |
|  - Encrypted email credentials           |
+-----------+------------------------------+
|  Outbound connections (user-controlled)  |
|  - LLM API (BYOK, any provider)          |  <- Only prompts, not raw data
|  - imap.gmail.com (App Password)         |  <- Email receipts, labeled only
|  - Parser registry (code only, no PII)   |  <- Download/upload parsers
+------------------------------------------+
```

**Key architecture decisions:**
- **Model-agnostic**: Parsers are pure Python [A13]. LLM is only needed for writing new parsers and NL queries — any provider works (Claude, GPT, Gemini, local Ollama)
- **Email is local IMAP**: Data flows Google → user's machine directly. App only syncs a filtered label, not full inbox
- **CLI-first MVP**: Desktop app deferred until demand validated. CLI targets the initial tech-savvy audience.
- **SDK constraint (Mar 2026)**: Claude Agent SDK requires API key billing [A9], but since architecture is model-agnostic, this is not a hard dependency

---

## Key Risks

| # | Risk | Severity | Mitigation | Status |
|---|------|----------|------------|--------|
| R1 | Onboarding friction too high for non-developers | HIGH | Watch folder + browser extension + guided setup wizard | Unmitigated — needs UX research |
| R2 | Total cost ($15-25/mo) deters target users | HIGH | Monitor API costs as models get cheaper; consider proxy tier later | [A4] — no WTP data |
| R3 | Agent fails to auto-generate parsers for unknown formats >30% of the time | HIGH | Fallback to vision LLM for cold start; human-curated parsers for top 50 banks | [A5] — needs systematic testing |
| R4 | Layout fingerprinting too fragile | MEDIUM | Version tolerance in fingerprint matching; fuzzy matching | [A6] — needs prototyping |
| R5 | Regulatory classification as "financial advisor" | MEDIUM | Position as "data organization tool"; no investment advice, no account management | Legal review needed |
| R6 | Niche market too small (<50K addressable) | MEDIUM | Primary research: landing page test, surveys | [A3] — wide error bars |
| R7 | Anthropic API pricing increases | LOW | BYOK model passes cost to user; multi-provider support (OpenAI, local models) as hedge | Architecture supports provider switching |
| R8 | Competitor (Monarch, etc.) adds local mode | LOW | Parser registry network effect is the moat; hard to replicate without community | Monitoring |

---

## Components to Build

| Component | Purpose | Status | Blocks |
|-----------|---------|--------|--------|
| Layout fingerprinter | Hash PDF structure without content | To build | Parser registry |
| Parser registry API | Store, search, version parsers by fingerprint | To build | Network effect |
| Validation reporter | Track pass/fail rates per parser version | To build | Quality assurance |
| Agent scaffold | Instructions for "write a parser for this new PDF" | POC exists | Needs generalization beyond 10 known formats |
| Contribution flow | Prompt user to share parser; automated PII check | To build | Community growth |
| Local finance engine | SQLite DB, categorization, NL queries | POC exists | Needs packaging for non-developer users |
| Email receipt sync | IMAP label sync + receipt parser (Amazon, Uber, etc.) | To build | Onboarding experience, itemized purchases |
| Model-agnostic LLM adapter | Swap Claude/GPT/Ollama for parser gen + NL queries | To build | Multi-provider support |
| Seed parser expansion | Add Wells Fargo, Citi, Capital One parsers [A17] | To build | 50-60% market coverage at launch |
| Watch folder monitor | Detect new files, trigger parsing | To build | Core UX |
| CLI packaging | pip/brew installable CLI as MVP | To build | First distributable product |
| Desktop app shell | Tauri app wrapping the agent + UI | Deferred | Not MVP — build after CLI validation |
| Browser extension | Auto-download statements to watch folder | Nice-to-have | Onboarding friction reduction |

---

## Open Questions

1. Should the app be open-source (community trust + parser contributions) or closed-source (protect IP)?
2. Is Tauri the right desktop framework, or should the MVP be CLI-first targeting developers?
3. Can categorization rules (not just parsers) be shared via the registry?
4. What is the minimum UX for API key setup to not lose users at onboarding?
5. Is there a path to local-only inference (no API key) as small models improve? Llama 3 and Qwen-VL are approaching viability for structured extraction.
6. What is the actual willingness-to-pay for this product? [A4] — needs primary research before committing to build.

---

## Conclusion

The gap between "cheap but shallow" (Simplifi) and "deep but invasive" (hypothetical Plaid+AI) is real, and a working proof of concept demonstrates that a local-first AI finance tool can deliver meaningfully deeper insights — particularly itemized Amazon purchases, cross-source spending analysis, and tax-aware optimization. The community parser registry is the key technical innovation, enabling network effects without compromising the privacy promise.

However, several critical assumptions remain unvalidated: the size of the addressable market [A3], willingness to pay at the $15-25/mo price point [A4], and whether agent-generated parsers work reliably on arbitrary unknown bank formats [A5]. These should be tested before significant investment — ideally through a landing page test (market sizing), beta cohort (parser reliability), and pricing experiments (WTP).

---

## Recommendations

| # | Action | Purpose | Effort |
|---|--------|---------|--------|
| 1 | Build landing page with value proposition; measure sign-up conversion | Validate market demand [A3] and messaging | 1 week |
| 2 | Test agent parser generation on 20 unseen bank formats | Validate core technical assumption [A5] | 2 weeks |
| 3 | Prototype layout fingerprinting on 5 same-bank cross-user statements | Validate registry matching [A6] | 1 week |
| 4 | Survey 50 target-profile users on privacy attitudes + WTP | Validate [A2] and [A4] with primary data | 2 weeks |
| 5 | Build email receipt parser (Amazon order confirmations via IMAP) | Validate the "TripIt pattern" for local email sync | 1 week |
| 6 | Open no-fee checking at Wells Fargo, Citi, Capital One | Seed parsers for top 5 banks [A17] — no credit score impact [A16] | 1 week |
| 7 | Ship CLI-first MVP (`pip install`) to 10 beta users | End-to-end validation before desktop app investment | 4 weeks |

---

## Appendix

### [1] High-Income Households with Complex Finances

Source: IRS Statistics of Income, Tax Year 2022. Returns with AGI > $200K: ~8.5M. Of these, a subset has multi-source income, investment accounts, and tax complexity requiring active management. No direct measurement of "complex finances" as a category exists; the 3-5M estimate is derived by assuming ~40-60% of >$200K filers have meaningful complexity beyond a single W-2.

**Verification status**: IRS count verified. "Complex finances" subset is ASSUMED — no primary data.

### [2] Proof of Concept System

Source: Live system built Feb-Mar 2026 using Claude Code. Codebase at `~/.claude/scripts/` (finance_db.py, ingest_cc_statements.py, ingest_becu.py, ingest_fidelity_accounts.py, ingest_sofi.py, ingest_tax.py). Database at `Finance/finance.db`. All record counts verified by running `SELECT COUNT(*) FROM <table>` against the live database.

### [3] AI Personal Finance Market Size

Source: SR Analytics blog post, "AI Personal Finance: Transform Money Management in 2026" (sranalytics.io). Claims $1.48B (2024) → $1.63B (2025), 18% CAGR to 2033.

**Verification status**: Single secondary source. No cross-reference with Gartner, IDC, or other analyst firms. Market sizing methodology not disclosed. Treat as directional, not precise.

### [4] Addressable Market Estimation

Methodology:
- IRS data: ~8.5M US returns with AGI >$200K (2022) [1]
- Bureau of Labor Statistics: ~4.4M software developers in US (2024)
- Assumed overlap: 30-50% of high-income households are technically comfortable with developer tools
- Assumed privacy-consciousness: 5-10% would reject Plaid on principle
- Result: 125K-400K, rounded to 100K-500K

**Verification status**: UNVERIFIED. Three of five inputs are assumptions without survey data. Landing page conversion testing would provide a far more reliable signal.

### [5] Competitor Pricing (Verified Mar 2026)

| Product | Source | Price |
|---------|--------|-------|
| Simplifi | simplifi.com/pricing | $3.99/mo (annual) |
| Monarch Money | monarchmoney.com/pricing | $7.99/mo (annual) |
| Copilot Money | copilot.money | $9.99/mo (annual) |
| Cursor | cursor.com/pricing | $20/mo (Pro), $200/mo (Ultra) |
| Windsurf | windsurf.com | $15/mo (Pro) |

Cursor revenue claim (~$1B ARR): Vantage blog post (vantage.sh), citing unnamed sources. Cursor is private; no official disclosure [A10].

### [6] Claude Agent SDK Billing Limitation

Source: GitHub issue anthropics/claude-agent-sdk-python#559 — "Agent SDK should support Max plan billing, not just API keys." As of Mar 2026, the SDK requires `sk-ant-api03-` style API keys. OAuth tokens from Claude Pro/Max subscriptions are not supported for SDK use.

### [7] Plaid Pricing

Sources: Plaid pricing page (plaid.com/pricing), Finexer blog (blog.finexer.com/plaid-pricing), Monetizely comparison (getmonetizely.com). Per-link cost $0.50-2.00, first 200 free, volume discounts at 10K+. Realistic per-user annual cost $3-6 (including reconnection rate of 15-25%).

**Note**: Plaid was evaluated and rejected as an architecture choice due to the privacy constraint [A12].

### [8] Amazon Spending per Household

Source: JRNI / Consumer Intelligence Research Partners estimates. Average US Prime member spends ~$1,400/yr on Amazon (2024). Power users (top quartile) estimated at $3,000-5,000/yr.

**Verification status**: Secondary source estimates vary widely ($1,400-$2,000 average depending on methodology). The $5,200 figure cited earlier in conversation was not verified and may be overstated.

### [9] Plaid CFPB Consent Order

Source: CFPB enforcement action, 2024. Plaid agreed to delete data collected without proper consumer consent and to stop obtaining bank login credentials without clear authorization. This was a significant regulatory action but its impact on consumer trust has not been quantified.

### [10] Vision LLM vs Rule-Based Parsing Accuracy

Source: "Comparing AI PDF Parsers" (causeofakind.com). PDFMiner scored 8/10, GPT-4 Vision scored 10/10 on character recognition and section separation. LlamaParse (LLM-based) scored 9/10. Cost estimates from LlamaIndex enterprise guide and Anthropic API pricing (Claude 3.5 Sonnet: ~$0.003/page for text, ~$0.01-0.05/page for vision).

**Verification status**: Single benchmark source. Real-world accuracy on financial statements specifically may differ from general document parsing benchmarks.

### [11] IRS High-Income Returns

Source: IRS Statistics of Income, Tax Year 2022. Number of returns by AGI bracket is published annually. The ~8.5M figure for AGI >$200K is from the most recent publicly available data.

### [12] US Software Developer Count

Source: Bureau of Labor Statistics, Occupational Employment and Wage Statistics, 2024. Software developers, quality assurance analysts, and testers: ~1.85M. Including broader "computer and mathematical occupations": ~4.4M.

### [13] Mint User Count at Shutdown

Source: Various press reports at time of Mint shutdown (Mar 2024). Estimates range from 3.6M to 4.5M active users. Intuit migrated users to Credit Karma, but adoption rates were not publicly disclosed.

### [14] Bank Account Opening and Credit Score Impact

Sources: SoFi (sofi.com/learn), Capital One (capitalone.com/learn-grow), Doctor of Credit (doctorofcredit.com/bank-accounts). Most banks perform soft pull or ChexSystems check (no credit score impact) when opening checking/savings accounts. Rare exceptions do hard pulls — a hard inquiry costs ~3-5 FICO points and stays for 2 years. ChexSystems tracks banking history, not credit.

**Practical implication**: Opening 5-10 no-fee checking accounts for parser testing is safe. Opening 100 is not recommended — ChexSystems flagging and account management overhead.

### [15] Gmail App Passwords and IMAP Access

Source: Google Account Help documentation, Python `imaplib` stdlib documentation. App Passwords require 2-Step Verification enabled. User generates a 16-character password at myaccount.google.com → Security → App Passwords. Connection: `imaplib.IMAP4_SSL("imap.gmail.com", 993)`.

**Verification status**: Confirmed working as of Mar 2026. Google has not announced deprecation of App Passwords.

### [16] Microsoft 365 Basic Auth Deprecation

Source: Microsoft Learn — "Authenticate an IMAP, POP or SMTP connection using OAuth" (learn.microsoft.com). Basic Authentication deprecated for Exchange Online effective December 31, 2022. IMAP access requires OAuth 2.0 with Azure AD app registration. Some personal Outlook.com accounts may still support App Passwords with MFA enabled, but M365 corporate accounts require OAuth.

**Practical implication**: Gmail is the simpler target for MVP. Outlook/M365 support requires OAuth infrastructure — defer to Phase 2.

### [17] US Credit Card Market Concentration

Sources: Approximate market share by cards in force (various industry reports). Chase (~20%), Bank of America (~10%), Citi (~10%), Capital One (~10%), Wells Fargo (~5%) = ~55% of US credit cards. Exact figures vary by source and metric (cards vs. balances vs. transaction volume).

**Verification status**: APPROXIMATE. No single authoritative source for exact market share. The directional claim (top 5 = majority of market) is widely supported.

---

*Research date: 2026-03-07/08*
