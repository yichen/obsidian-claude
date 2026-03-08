# Local-First AI Personal Finance Advisor

## The Problem

Current personal finance tools fall into two camps, and neither serves privacy-conscious users who want full AI capabilities:

**Cloud-based aggregators** (Monarch Money, Copilot Money, Simplifi, Empower):
- Rely on Plaid/MX/Finicity to pull bank data — user must grant third-party access
- See transaction-level CC data but NOT itemized purchases (e.g., what you actually bought on Amazon)
- Privacy is the #1 complaint in reviews
- Simplifi is only $4/mo, Monarch $8/mo — cheap, but shallow

**Local open-source tools** (Firefly III, GnuCash, Actual Budget):
- Manual data entry or basic CSV import
- No AI, no natural language queries, no adaptive parsing
- Tech-savvy users only

**Nobody occupies the middle**: local-first + AI-powered + privacy-preserving + adaptive ingestion + itemized purchase visibility.

## The Opportunity

The AI personal finance market was valued at $1B in 2025, projected to $3.7B by 2033 (18% CAGR). The "private AI" pattern — users want AI capabilities but won't send data to the cloud — is a major trend across industries:

| Industry | Privacy Concern | Current Solutions |
|----------|----------------|-------------------|
| Healthcare | Medical records, HIPAA | On-device models, federated learning |
| Legal | Attorney-client privilege | Self-hosted LLMs (Harvey AI on-prem) |
| Enterprise code | Source code is IP | GitHub Copilot Enterprise (VPC), Claude Code (local) |
| Personal notes | Journals, private data | Obsidian (local-first response to Notion/Evernote) |

Technical approaches in the industry: local inference (Ollama, llama.cpp), hybrid architecture (local storage + API calls with only prompts leaving machine), confidential computing / TEEs, zero-knowledge architectures.

## The Privacy Constraint (Non-Negotiable)

**Core principle: No Plaid. No Gmail OAuth. No cloud data aggregation.**

The moment you add Plaid + Gmail OAuth, you become exactly what Simplifi is. Privacy-conscious users (the target market) won't let a startup access their Gmail or bank accounts — even the founder wouldn't. If the founder wouldn't use his own product with those integrations, don't build them.

All data comes from **user-initiated local actions only**:

| Source | How User Gets It | Privacy |
|---|---|---|
| CC statement PDFs | Download from bank website | Fully local |
| Bank statement PDFs | Download from bank website | Fully local |
| Amazon order export | Amazon "Request My Data" or order history CSV | Fully local |
| Email receipts | User forwards or exports `.eml` files manually | Fully local |
| Payslips | Download from employer portal | Fully local |
| Tax docs | Download from CPA or IRS | Fully local |

**Data flow guarantee:** Nothing leaves the user's machine except LLM prompts (via user's own API key) that contain structured extraction requests, never raw financial data.

## Product Vision

> "Your finances are too important to trust to a startup's servers. [Product] runs entirely on your machine. Drop your statements in a folder — our AI parses, categorizes, and analyzes everything locally. You see exactly what you bought, where your money goes, and what to do about taxes. Your data never leaves your computer."

### The Real Differentiator: Depth Over Convenience

This product does NOT compete with Simplifi on convenience. It competes on **capabilities Simplifi literally cannot offer**:

| Capability | Simplifi ($4/mo) | This Product |
|---|---|---|
| Auto bank sync | Yes (Plaid) | No — manual PDF drops |
| Itemized Amazon purchases | No — sees "AMZN $47.23" | Yes — "Kids rain boots $23, vitamins $24" |
| "How much do I spend on the kids?" | Rough category only | Precise — CC + Amazon + activities combined |
| Tax-aware analysis | No | "You're $19K under-withheld, adjust W-4 by October" |
| Custom NL queries | No | "Compare restaurant spending this year vs last" |
| Payslip/income analysis | No | "What's my effective tax rate across both employers?" |
| Data survives if company dies | No (Mint proved this) | Yes — it's your SQLite file |
| Works with any document | No — Plaid-connected only | Yes — any PDF, CSV, email export |

**The pitch isn't "Simplifi but private." It's "a personal CFO that understands your full financial picture — and you own every byte of it."**

### Reducing Friction Without Compromising Privacy

Instead of OAuth/Plaid, make the manual process as painless as possible:

**1. Watch folder pattern**
```
~/Finance/inbox/        <- user drops PDFs here
  chase-feb-2026.pdf
  becu-feb-2026.pdf
  amazon-orders.csv

App detects new files -> auto-parses -> notifies user
```

**2. Browser extension (fully local, no server)**
- User clicks "Export" on their Chase account page
- Extension auto-saves PDF to the watch folder
- Zero data leaves the browser — extension just automates the download
- Same pattern as 1Password/Bitwarden — local extension, no server

**3. Periodic email export**
- User does `.mbox` export from Gmail, drops it in inbox folder
- Agent extracts Amazon order confirmations, receipts locally
- More realistic than OAuth and equally powerful

## Proof of Concept: What Already Exists

The current personal finance system built with Claude Code demonstrates the concept works:

- **5,620 CC transactions** across 6 cards, 100% categorized
- **3,218 Amazon orders** with itemized detail (the killer feature no competitor has)
- **44 payslips** with line-item detail across multiple employers
- **Natural language queries** that generate SQL via `/finance`
- **Balance validation** — automated acceptance tests that catch parsing errors
- **Multi-source ingestion**: CC statements (`/ingest-cc`), BECU bank statements (`/ingest-becu`), Fidelity accounts (`/ingest-fidelity`), SoFi loans (`/ingest-sofi`), tax documents (`/ingest-tax`), Amazon orders, payslips

## PDF Parsing Strategy

### Current Approach: Agent-Written Deterministic Parsers

The existing pipeline uses **pdfminer text extraction + Claude Code as the agent that writes and debugs parser code**:

1. pdfminer extracts raw text and character coordinates from the PDF
2. Claude Code (the agent) writes Python parser code with regex, positional logic, font filtering
3. Balance validation serves as automated acceptance tests — if totals don't match, iterate
4. The resulting parser is deterministic and reusable — once written, runs instantly

This approach is superior for known, recurring formats:

| | Agent-written deterministic parser | Vision LLM (send page as image) |
|---|---|---|
| **Accuracy on known formats** | Near-perfect (deterministic code) | ~95-98% (non-deterministic) |
| **Cost per run** | Free after initial development | $0.01-0.05/page every time |
| **Speed** | Milliseconds | 5-30 seconds per page |
| **Reproducibility** | 100% deterministic | Can vary between runs |
| **New format support** | Needs agent to write new parser | Works on any format immediately |
| **Privacy** | Fully local | Data sent to API |

### The Scaling Problem

For personal use, deterministic parsers are clearly better. The problem is productizing:

- Current system has parsers for ~10 specific formats (5 W-2 variants, 6 CC cards, BECU, Fidelity CMA, SoFi)
- A product serving 10,000 users might face 500+ bank/CC statement formats
- Writing deterministic parsers for each by hand is the bottleneck

### The Hybrid Solution: Agent-Generated Parser Registry

The key insight: **have the agent write parsers automatically, validate them, then share the parser code (not user data) with a community registry.**

1. User drops in an unsupported PDF
2. Agent examines the text extraction output, writes a parser, validates against balance totals
3. If validation passes, parser is fingerprinted by PDF layout signature (not content)
4. User is prompted: "Share this parser with the community? (No financial data is included)"
5. Parser uploaded to registry with the layout fingerprint

For the next user with the same bank:
1. Agent extracts the layout fingerprint from their PDF
2. Matches against registry — finds existing parser
3. Downloads and runs it locally — no agent coding needed, instant

**Parser code contains zero PII.** It's just logic about where dates, amounts, and descriptions appear in a particular bank's PDF layout. Perfectly safe to share.

### Layout Fingerprinting

The layout fingerprint is a hash of structural elements without any actual values:
- Header text patterns and positions
- Column x-positions and widths
- Font names and sizes used
- Page layout structure (margins, sections)

Two BECU statements from different users have the same fingerprint even though the transactions are completely different.

### Federated Parser Improvement

Parsers get better over time without sharing data:

1. User A's BECU parser works on 95% of their statements (one edge case fails)
2. User B's agent fixes that edge case for their statements
3. The code diff (no data) is submitted back to the registry
4. User A gets the improved parser on next sync

This is **federated learning but for code, not models**. The shared artifact is deterministic Python, not weights or data.

### Format Change Detection

Banks occasionally redesign their statement format. The system handles this naturally:

- When a format changes, the old parser's balance validation **immediately fails** (unlike vision LLM where accuracy silently degrades)
- The agent writes a new parser, which gets a new layout fingerprint
- Published as `becu-checking-v3`, old fingerprint routes to old parser, new fingerprint routes to new one

## Competitive Landscape

### Consumer Finance Apps

| Company | Price | Approach | Gap |
|---------|-------|----------|-----|
| Simplifi | $4/mo | Plaid auto-sync, basic categories | No itemized purchases, shallow analysis |
| Monarch Money | $8/mo | Plaid + AI insights, dashboards | Same Plaid limitations, cloud-only |
| Copilot Money | $10/mo | Plaid + AI, Apple-only | No Android, no itemization |
| Empower | Free | Plaid + upsells advisory services | Aggressive sales tactics |
| Firefly III | Free/OSS | Self-hosted, manual entry | No AI, no parsing |

### Enterprise Document Parsing

Several funded companies do LLM-based document parsing, but all are cloud B2B — not local-first consumer:

| Company | What They Do | Model |
|---------|-------------|-------|
| Unstract | Open-source LLM-powered ETL for unstructured docs. "LLMWhisperer" handles bank statements. | Cloud API, open-source core |
| Sensible.so | Document extraction API with validation and audit trails | Cloud API, $5.7M seed |
| Docsumo | 99% accuracy doc AI, custom APIs per document type | Cloud SaaS |
| Veryfi | Real-time receipt/invoice OCR with mobile SDK | Cloud + on-device SDK |
| Sparrow | Open-source universal doc processor — vision LLM + traditional parsing | Self-hosted |

**None of them do the agent-writes-deterministic-parsers approach.** They either use vision LLM for every extraction (costly, non-deterministic) or require manual template configuration.

## Target Customer

This is a niche product, not a Simplifi competitor. The ideal customer:

- **High income** ($200K+) — complex enough finances to need this
- **Privacy-conscious** — actively distrusts Plaid and cloud aggregators
- **Somewhat technical** — comfortable downloading PDFs monthly
- **Amazon power user** — $3K+/yr on Amazon, wants to know where it goes
- **Tax complexity** — multiple income sources, RSUs, rental property, divorce
- **Burned by Mint shutdown** — wants to own their data permanently

Estimated addressable market: **100K-500K people in the US**. Not millions, but they'd pay for something that actually works for them because nothing else does.

## Business Model

### Pricing: BYOK-Only, Charge for Software

| | Details |
|---|---|
| **Price** | $10/mo or $99/yr |
| **API** | BYOK only — user's own Anthropic API key |
| **Your revenue** | Pure software license, zero API cost |
| **Data flow** | Nothing leaves machine except user-to-Anthropic API prompts |
| **Parser registry** | Community-contributed, anonymized parser code only |
| **Moat** | Parser library + agent instructions + financial domain knowledge |

### Why BYOK-Only

1. **Strongest privacy story** — "We literally cannot see your data"
2. **No API cost risk** while finding product-market fit
3. Initial users will be tech-savvy — they can handle getting an API key
4. Add a proxy tier later if needed to reach mainstream users

### Unit Economics

```
Revenue per user:          $8.25/mo (blended annual/monthly)
Costs per user:
  Parser registry hosting: -$0.10/mo
  Support:                 -$0.50/mo
                           ---------
Gross margin:              $7.65/mo  (93%)
```

Near-zero marginal cost because users pay their own API costs (~$5-15/mo to Anthropic directly).

### Revenue Projections

| Users | ARR |
|-------|-----|
| 1,000 | $99K |
| 10,000 | $990K |
| 50,000 | $4.95M |

### Why Not Compete on Price with Simplifi

Simplifi is $4/mo for basic auto-sync budgeting. Competing on price is a losing strategy because:

1. You can't match their convenience (Plaid auto-sync vs manual PDF drops)
2. Your cost floor is higher (users pay API costs on top)
3. Their audience (simple finances, wants a pie chart) doesn't need your product

Instead, compete on **depth and ownership**:
- Simplifi: "You spent $847 at Amazon last month."
- This app: "You spent $847 at Amazon: $234 kids, $189 household, $156 tech, $142 supplements, $126 camping."

That granularity is worth $10/mo to someone who cares. The person who doesn't care was never your customer.

## Network Effects and Defensibility

The parser registry creates a **network effect**: every new user who encounters a new bank format makes the product better for all future users. After 1,000 users contributing parsers, coverage of most US banks and credit cards becomes comprehensive. That parser library is the moat — hard for competitors to replicate without the same user base.

Precedents for community-contributed rule sets where rules contain no user data:
- **uBlock Origin** — community filter lists
- **Homebrew** — community formulae
- **Wireshark** — community protocol dissectors
- **Pi-hole** — community blocklists

## Technical Architecture

```
+-------------------------------------+
|  Desktop App (Tauri)                |  <- What the user sees
+-----------+-------------------------+
|  Claude Agent SDK (Python)          |  <- The brain
|  - Parser agent (writes/runs code)  |
|  - Query agent (NL -> SQL)          |
|  - Categorization agent             |
+-----------+-------------------------+
|  Local SQLite DB                    |  <- All data stays here
|  Local PDF/CSV storage              |
|  Parser registry cache              |
+-----------+-------------------------+
|  Outbound API (user's BYOK key)    |  <- Only prompts leave machine
|  User -> Anthropic directly         |
+-------------------------------------+
```

**SDK constraint (as of Mar 2026):** Claude Agent SDK requires API key billing — does NOT support Claude Pro/Max subscription billing. Users need a separate Anthropic API key.

## Key Risks

1. **Onboarding friction** — Users must download PDFs monthly and set up an API key. The watch folder + browser extension mitigate this but don't eliminate it.
2. **API key cost** — Users pay ~$5-15/mo to Anthropic on top of the app subscription. Total cost $15-25/mo. Some users will resist.
3. **Regulatory** — Must position as "financial data organization tool" not "financial advisor." Stay on the "tool" side.
4. **Bank format diversity** — Long tail of small banks/credit unions. Community parser registry addresses this but needs critical mass.
5. **Niche market** — 100K-500K addressable users. Profitable as a small business, unlikely to be a venture-scale outcome.

## Components to Build

| Component | Purpose | Status |
|-----------|---------|--------|
| Layout fingerprinter | Hash PDF structure without content | To build |
| Parser registry API | Store, search, version parsers by fingerprint | To build |
| Validation reporter | Track pass/fail rates per parser version | To build |
| Agent scaffold | Instructions for "write a parser for this PDF" | Already built (proof of concept) |
| Contribution flow | Prompt user to share parser, strip any PII | To build |
| Local finance engine | SQLite DB, categorization, NL queries | Already built (proof of concept) |
| Desktop app shell | Tauri app wrapping the agent | To build |
| Browser extension | Auto-download statements to watch folder | To build (nice-to-have) |
| Watch folder monitor | Detect new files, trigger parsing | To build |

## Open Questions

1. Should the app be open-source (community trust + contributions) or closed-source (protect IP)?
2. Is Tauri the right framework, or should it be a CLI-first product targeting developers?
3. Can categorization rules also be shared via the registry (alongside parsers)?
4. How to handle the API key setup UX to minimize friction?
5. Is there a path to local-only inference (no API key needed) as small models improve?

## Research Date

2026-03-07
