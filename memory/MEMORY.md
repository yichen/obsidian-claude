# Key Learnings

### Tax Document Ingestion Pipeline (2026-02-28)
- Created `/ingest-tax` slash command + Python script at `.claude/scripts/ingest_tax.py` (3,371 lines)
- Source PDFs: `~/Dropbox/1-Tax/2-prepare/<year>/` (CPA inputs) + `~/Dropbox/1-Tax/3-archive/<year>/` (filed returns)
- Output YAMLs: `Finance/tax/prepare/<year>/` and `Finance/tax/archive/<year>/`
- **49 YAMLs** generated across 2022–2025: 15 W-2s, 9 1099-Rs, 14 1098s, 2 1099-INTs, 3 5498-SAs, 5 5498s, 1 1099-SA, 2 Schedule Hs, 3 1040 summaries
- Processing log at `Finance/tax/processing_log.json` — idempotent re-runs skip already-processed files
- **W-2 parsers**: 5 format variants — Salesforce (Courier font extraction), Paylocity (ServiceTitan/Stripe), ADP (Airbnb/Meta), Lincoln Life, nanny (HomePay)
- **W-2 PDF gotcha**: Salesforce W-2 has 4 copies per page with values in Courier font overlaid on Arial form template — must filter by font, cluster chars by y-position (5pt tolerance), then group into tokens. The `_build_tokens()` function must cluster by y FIRST then sort by x within each line, otherwise interleaved y-positions cause merged tokens
- **W-2 false positive**: "renew-2024" contains "w-2" (rene**w-2**024) — must use word-boundary regex `(?:^|[\s_.-])w-?2(?:[\s_.-]|$)` instead of substring match
- **1099-R layout**: Fidelity 401k 1099-R has values on the line AFTER box labels (not inline) — use label line detection + `_find_amounts_near(label_line)` scanning ±2 lines
- **1040 parser**: Handles CPA-prepared returns (35-47 pages); 2022 format has values BEFORE labels (reversed from 2023/2024)
- **Cross-validation** (`--cross-validate` flag): 0 true mismatches across all years. Known expected gaps: spouse W-2s (MFJ), backdoor Roth (Form 8606), third-party sick pay overlap, brokerage 1099-INTs sent directly to CPA
- Schedule H ↔ nanny W-2: exact match both years; 2025 Salesforce W-2 fed withholding ↔ payslip DB: exact match ($160,668.34)
- **Team agents pattern**: Used 4 parallel agents (parser-1099int, parser-5498, parser-schedule-h, parser-1040) + 1 sequential (cross-validator). Each agent edits different functions in same file — minimal conflicts. TaskCreate with blockedBy for dependencies.

### Personal Finance Database & Analysis Skill (2026-03-01)
- Created `/finance` slash command + Python script at `.claude/scripts/finance_db.py`
- SQLite database at `Finance/finance.db` — schema: transactions, categories, accounts, categorization_rules, import_log, **amazon_orders**, **payslips, payslip_line_items**
- **5,620 CC transactions** imported from 163 CSVs (Dec 2022 – Feb 2026, 6 cards)
- **3,218 Amazon orders** imported from `~/Dropbox/0-FinancialStatements/amazon/*.csv` (2003–2026)
- **44 payslips + 1,032 line items** from `Finance/payslips/<employer>/*.yaml` (Salesforce + ServiceTitan)
- **100% CC transactions categorized**; **Amazon orders 88% categorized** (2,830/3,218 via 10 rounds of keyword rules + manual review)
- Dedup keys: transactions=`source_file + source_row`; amazon=`(order_id, asin)` + date watermark; payslips=`(employer, pay_date, period_start, period_end, gross_pay)`
- `is_transfer=1` flags payments, ACH, interest — excluded from spending queries
- Categories: 2-level hierarchy (~59 categories), top-level groups: Food & Drink, Shopping, Travel, Health & Wellness, Fees & Interest, Kids & Family, etc.
- **Amazon subcategories added (Mar 2026)**: Kids Books, Kids Toys and Games, Kids Food, Kids Gear, Baby and Infant, Tech and Electronics, Camping and Outdoor, Photography, Office, Supplements
- `backup_db()` creates `.db.bak` + auto-exports `Finance/categorization_rules.json` (1,239 rules) before every import
- `backup-rules` / `restore-rules` commands for manual export/import of categorization rules
- **Full rebuild**: `init` → `restore-rules` → `import` → `categorize` → `import-amazon` → `categorize-amazon` → `import-payslips` → `import-tax` → `import-fidelity` → `import-sofi` → `import-becu`
- `finance_db.py validate` — post-import balance validation against PDF balance summaries
- `/finance <question>` translates natural language to SQL queries — supports payslip/income/cash-flow queries
- matplotlib installed in venv for chart generation to `Finance/reports/`
- **Finance CLAUDE.md** at `Finance/CLAUDE.md` documents all data sources, schema, tax facts, query patterns; root CLAUDE.md routes to it

### Spending Analysis Insights (2026-03-01, updated)
- **2025 monthly avg**: ~$10K/mo CC spending
- **Travel**: $2,178/mo (2025) — Costco Travel, Chase Travel, Cathay Pacific
- **Legal**: $1,494/mo in 2025 — **eliminated** (divorce finalized, no more legal costs)
- **Hobby spending (2025)**: $1,230/mo — Photography ($323: B&H $3.5K), Camping & Outdoor ($466: REI $2K, Oztent $1.2K), Tech & Electronics ($442: Anker Solix $3K, FlexiSpot $867)
- **Amazon breakdown (now 88% categorized)**: Tech $239/mo, Camping $159/mo, Home Improvement $117/mo, Supplements $84/mo, Photography $71/mo, Kids (all) $129/mo
- **Food**: Groceries $595/mo, Restaurants $456/mo (La Casita 28 visits), Fast Food $141/mo (MOD Pizza $55, McDonald's $44)
- **Subscriptions**: $320/mo → ~$267/mo after cancellations (Windsurf, LeetCode, Quicken, Cursor). Apple billing $175/mo still needs audit.
- **Food delivery eliminated**: was $900/mo in 2023, now $0 since Mar 2024
- **W8TECH_*SA** on Apple Card = Windsurf AI coding tool ($130/mo) — cancelled

### W-4 Withholding & Tax Analysis (2026-02-28)
- W-4 history stored as YAML: `Finance/payslips/<employer>/w4-history.yaml`
- Dedup by `effective_date + last_updated` timestamp; ordered newest-first
- **Salesforce W-4** (current eff 1/15/2026): Single/MFS, Multiple Jobs=No, Extra=$800/check
- **ServiceTitan W-4** (current eff 1/3/2026): Single/MFS, Multiple Jobs=No, Extra=$100/check
- User does NOT want to check "Multiple Jobs" for privacy — prefers adjusting extra withholding
- 2025 tax: ~$164K (HoH) or ~$168K (Single); payroll withheld $165.7K + $25K IRS est. payment = **$190.7K total → ~$22-27K refund expected**
- 2026 projected gap: ~$19.7K under-withheld at current settings (two-employer problem + bonus at 22% flat rate)
- **Safe harbor strategy**: keep current withholding, re-evaluate in October, adjust W-4 or make Q4 payment; W-2 withholding counts as paid evenly across all quarters (unlike estimated payments)
- 110% of prior year tax safe harbor: need ~$180-185K in total 2026 withholding

### Cash Flow Analysis (2026-03-01, updated)
- **Full analysis saved to**: `Finance/Planning/2026-03-01-Cash-Flow-Analysis-and-Rental-Sale-Decision.md`
- **Monthly take-home (Feb 2026)**: SF $10,817 + ST $9,736 + rental $1,995 = $22,548
- **Monthly fixed obligations**: $23,833 (spousal $10K, primary mortgage $4,957, rental mortgage $1,780, SoFi $1,764, HELOC $1,358, child support $1,254, Tesla $1,000, rental HOA $620, insurance $550, kids ~$500, primary HOA $50)
- **After-tax 401k**: already $0 at both employers (confirmed from Feb 2026 payslips)
- **ESPP**: user stopped online Mar 2026, effective next paycheck (+$3,275/mo)
- **Divorce legal**: $0 going forward (finalized, no more costs)
- **Hobby freeze committed**: no more electronics/camping/photography purchases (+$1,230/mo)
- **New CC baseline**: ~$2,723/mo (down from $5,500 after legal eliminated + hobby freeze + subscription cuts)
- **Updated cash flow (Mar 2026+, post-ESPP)**: income $25,823 - fixed $23,833 - CC $2,723 = **-$733/mo** (near breakeven)
- **No longer need to sell rental** for survival — rental sale becomes optional deleveraging
- **HELOC**: $150,904 balance, 6.99%, $230K limit, $79K available — runway now ~19 months at -$733/mo (was ~Oct 2026)
- **Two mortgages via Mr. Cooper**: primary $4,957/mo + rental $1,780/mo
- **Tesla loan**: Wells Fargo, ~$45K balance, $1,000/mo via BECU auto-draft

### Rental Property (2026-03-01)
- **Address**: 2516 175th Ave NE
- **Purchased**: 2005 for $320,000
- **Rental since**: December 2014
- **Mortgage**: Mr. Cooper, Conventional 30-Year, Loan 694006164, balance $219,493
- **Estimated equity**: $702,507 (Mr. Cooper estimate), but poorly maintained → user estimates ~$760K sale, ~$500K net proceeds pre-tax
- **Monthly P&L**: income $1,995 - mortgage $1,780 - HOA $620 = **-$405/mo cash-flow negative**
- **Capital gains tax estimate** (if sold): ~$123,400 (depreciation recapture $25.1K + LTCG $79.4K + NIIT $18.9K)
- **Net after tax**: ~$374K → pay off HELOC ($151K) + SoFi ($41K) + Tesla ($45K) = **$137K cash reserve**
- **Post-sale cash flow (Jun 2026+)**: +$5,882/mo surplus; single-job runway 14-19 months with $137K reserve
- Depreciation basis: building $240K (75% of $320K) / 27.5yr × 11.5yr = $100,400 recapture

### BECU Statement Ingestion (2026-03-01)
- Created `/ingest-becu` slash command + Python script at `.claude/scripts/ingest_becu.py`
- Parses combined BECU statements (checking + HELOC) from `~/Dropbox/0-FinancialStatements/BECU/`
- Output YAMLs: `Finance/becu/YYYY-MM.yaml`, processing log: `Finance/becu/processing_log.json`
- **14 statements** (Jan 2025 – Feb 2026), **118 checking transactions**, **8 HELOC statements** (Jul 2025+)
- DB tables: `becu_checking_statements`, `becu_checking_transactions`, `becu_heloc_statements`
- **pdfminer column ordering is unpredictable**: Amount/Description columns may appear BEFORE Date columns depending on page layout. Parser extracts ALL dates, amounts, descriptions from transaction area and matches 1:1 by count; classifies by sign (positive=deposit, negative=withdrawal)
- **HELOC summary parsing**: Labels and values may be interleaved OR labels-first-then-values. Use purely positional approach: first amount = previous_balance, last 3 = new/limit/available, middle: negative=payments, larger positive=advances, smaller=interest
- **HELOC sub-accounts doubled by APR section**: "HE Variable Line of Credit" and "HE Fixed Rate Advance" appear in both APR rate listing AND detail sections. Filter by requiring `previous_balance` to exist.
- **Sub-account interest assignment**: Collect ALL "TOTAL INTEREST PAID THIS PERIOD" values; first = overall total. Remove duplicates of overall until count matches sub-accounts, then assign in order.
- **YTD fees/interest parsing**: Labels ("Total fees charged in YYYY" / "Total interest charged in YYYY") appear together, values follow. Take amounts[0]=fees, amounts[1]=interest after both labels.
- Import command: `finance_db.py import-becu`
- **Full rebuild** now includes: `import-becu` after `import-sofi`

### CMA Transaction Ingestion (2026-03-01)
- Added `parse_cma_activity()` + `categorize_cma_transaction()` to `.claude/scripts/ingest_fidelity_accounts.py`
- **481 transactions** parsed from 13 monthly statements (Jan 2025 – Jan 2026), 100% categorized
- Sections parsed: Deposits, Withdrawals, Checking Activity (checks), Exchanges In/Out
- **Sheri Martin's bank**: Capital One N.A. ******0615 — any transfer to this account = payment to Sheri
- Sheri payments auto-classified by amount: $1,254 → Child Support, $50K → Property Settlement, >= $3K → Spousal Maintenance, else → Divorce — Other
- **Spousal maintenance**: $10K/mo post-finalization (Jun 2025+), ~$3.1K biweekly pre-finalization — ~2.5 years remaining from Mar 2026
- **Child support**: $1,254/mo until twins turn 18 (Nov 9, 2035)
- **Property settlement**: $100K total in two $50K installments (Jun + Dec 2025) — completed
- **OFW (OurFamilyWizard)**: All OFW debits = Kids Cost, OFW deposits = Kids Cost (Reimbursement)
- DB table: `fidelity_cma_transactions` with `(source_file, source_row)` dedup
- **Page break artifacts**: Continuation lines must filter out "INVESTMENT REPORT", "Account #", "YI CHEN", single-letter artifacts, barcode strings, month names — these appear when a multi-line payee spans a page break
- Key patterns: "Apa treas" = Airbnb rental income, "Solium Inc" = RSU/ESPP proceeds, "4 Corners Fina" = legal/financial services

### Credit Card Statement Ingestion Pipeline (2026-03-01)
- Created `/ingest-cc` slash command + Python script at `.claude/scripts/ingest_cc_statements.py`
- Parses 163 PDFs across 6 cards: Apple Card, Chase Prime/Sapphire/Freedom, Fidelity Credit Card, BofA Atmos Rewards (7982)
- **Fidelity Rewards merged into Fidelity Credit Card** (Mar 2026) — duplicate statements, 450 txns deleted. Removed from card configs and seed data.
- Source PDFs: `~/Dropbox/0-FinancialStatements/credit-cards/`
- Output CSVs: `Finance/credit-card/<card-name>/YYYY-MM-DD.csv`
- Processing log at `Finance/credit-card/processing_log.json` tracks what's been processed + balance_summary per statement
- **Balance validation** (3-tier): (1) inline during PDF parse, (2) `verify_all_balances()` at end of `run_ingest()`, (3) `finance_db.py validate` post-import DB check
- **Balance formula**: `new_balance = previous_balance - sum(csv_txns) + installments` — payments are positive in CSV (reduce balance), charges negative (increase balance)
- **Apple Card installments**: Device payment plans (Monthly Installments) affect balance but aren't in transaction list — parsed separately via `extract_balance_summary()`
- **153/154 statements pass** balance validation; 1 Apple Card has $13.24 diff (device tax)
- **Chase PDF gotcha**: Headers render with doubled characters (`AACCCCOOUUNNTT` instead of `ACCOUNT`)
- **Fidelity gotcha**: Credit/debit adjustments use single-date format — need ALT_RE fallback regex
- **Apple Card gotcha**: Returns lack Daily Cash columns — need PAY_RE fallback
- venv at `Scripts/venv/`, Python 3.14

### Post-2018 Divorce Tax Rules (2026-02-26)
- Divorce finalized May 2025 — all spousal maintenance is **NOT deductible** (TCJA, post-12/31/2018)
- Applies to BOTH temporary support (pre-finalization) and post-finalization maintenance
- Sheri does not report maintenance as income either
- WA has no state income tax so no state deduction exists
- Child support ($1,254/mo) is also never deductible
- Property settlement transfers ($100k cash, QDRO 401k transfers) are non-taxable events
- **Dependent claims**: Yi claims Laurence, Sheri claims Ruby — every year (Section 19 of Child Support Order)
- May need IRS Form 8332 for non-custodial parent years (Sheri is custodian in even years, Yi in odd years)
- 2025 total spousal support paid: ~$95,000 ($5k/mo temp Jan-May + $10k/mo June-Dec)

### LeetCode Practice Skill (2026-02-26)
- Created `/leetcode` slash command at `.claude/commands/leetcode.md`
- Logs daily practice to `Work/LeetCode/YYYY-MM-DD.md`
- Supports multiple entries per day (appends with `---` separator)

## Weather Forecasting (CRITICAL)
**ALWAYS use forecast.weather.gov via WebFetch for weather forecasts. NEVER use WebSearch.**

- WebSearch returns unreliable, cached, or wrong-location weather data
- Made critical error giving user 70°F sunny forecast when actual was 45°F rainy
- Only trust official NWS data from forecast.weather.gov URLs
- Use WebFetch with specific NWS forecast URLs (format: `https://forecast.weather.gov/MapClick.php?lat=XX.XXX&lon=-XXX.XXX`)
- This is mandated in Trips/CLAUDE.md section 7

## Trip Planning
- See Trips/CLAUDE.md for full trip planning protocols
- Always check Trips/Lessons Learned.md before planning
- Validate all URLs before including in itineraries

## User Preferences

- Prefers concise financial analysis with tables over narrative
- Uses voice input — apply reasonable corrections for speech-to-text artifacts
- Prefers investigation and data before recommendations
- When asked to "drill down", show merchant-level and product-level detail
- Chart outputs go to `Finance/reports/`
- Timestamps in PST (America/Los_Angeles)
- **Tax documents**: When parsing hits a WARNING state (values extracted but can't be automatically verified), ask user to manually review the source PDF rather than guessing. Human-in-the-loop for ambiguous tax data.
- **File paths in output**: User runs Claude Code in **Warp terminal**, which auto-detects absolute file paths and makes them clickable. Markdown links do NOT render — just output bare absolute paths. **Spaces in paths break Warp's detection** — use hyphens instead of spaces in new directory/file names. Always output full absolute paths so Warp can detect them.
- **Obsidian file naming**: Use hyphens instead of spaces. Avoid `&` and other special characters — they break Obsidian wiki-links. Use `and` instead of `&`.

# Active Context

### Finance DB categorization rules backup (2026-03-01) `(COMPLETED)`
- **Resolved**: 751 rules now auto-exported to `Finance/categorization_rules.json` on every import
- `backup-rules` / `restore-rules` CLI commands added to `finance_db.py`
- Full rebuild procedure documented in `Finance/CLAUDE.md` under "Backup & Recovery"
- Only ~230 rules in Python seed; the remaining ~520 from `/finance review` sessions are preserved in the JSON backup

### Tax Ingestion Phase 4 Pending (2026-02-28) `(COMPLETED)`
- All phases complete including SQLite integration (`tax_documents`, `tax_line_items` tables)
- Remaining: consolidated 1099 parser (Fidelity/Morgan Stanley brokerage) — lower priority

### 2025 Tax Return (2026-02-28) `(active)`
- $25K estimated payment was unnecessary — expect ~$22-27K refund
- Need to decide HoH vs Single filing (HoH saves ~$4K but requires Laurence lived with Yi >50% of year)
- **Historical tax data now available** in `Finance/tax/archive/` — AGI: $544K (2024), $717K (2023), $664K (2022)

### Spring Break 2026 — Oahu with Kids (2026-03-01) `(active)`
- **Dates**: Apr 13–19, 2026 (6 nights). No school Apr 13–17.
- **Reservations**: `Trips/2026/2026-04-13_17 Spring Break with Kids/Reservations.md`
- Booked via Costco Travel (Jan 12, 2026)
- Flight: Hawaiian Airlines HA 899/990 (SEA↔HNL), Conf: ADGGWT
- Hotel: The Laylow, Autograph Collection (Waikiki), Conf: 76599630
- Car: Alamo intermediate (Toyota Corolla), Conf: 68668670
- Extras: $141 Costco shop card, $100 F&B credit, waived resort fee, free valet

### Cash Flow / Rental Sale Decision (2026-03-01) `(active)`
- **Revised Mar 2026**: After hobby freeze + legal eliminated + ESPP stopped + subscription cuts, deficit went from -$6,785/mo to **-$733/mo** (near breakeven)
- **HELOC runway**: $79K available / $733/mo = ~9 years (was ~Oct 2026) — no longer urgent
- **Rental sale**: still beneficial (+$5,882/mo surplus, $137K reserve) but **no longer required for survival**
- **Remaining levers**: cut dining 50% (+$300), audit Apple subs (+$50-100) → would flip to positive
- **Spousal maintenance ends ~late 2028**: +$10K/mo — everything becomes very comfortable
- Re-evaluate withholding in October per safe harbor strategy

### Olympic National Park Family Trip (2026-03-21) `(active)`
- Staying at Lake Quinault Lodge with kids, returning home March 22
- **Chase Sapphire card ends in 6904** — used for trip dining

### fairbridge.app (2026-03-18) `(active)`
- Moved `Projects/fairbridge.app/` specs out of Obsidian vault into its own repo
- 12 spec files removed (Android, iOS, Backend, Web Frontend, Security, UX Flows, MVP plan, software-spec)
