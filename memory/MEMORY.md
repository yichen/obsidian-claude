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
- **100% CC transactions categorized**; Amazon orders 8% categorized (product names too specific for keyword rules)
- Dedup keys: transactions=`source_file + source_row`; amazon=`(order_id, asin)` + date watermark; payslips=`(employer, pay_date, period_start, period_end, gross_pay)`
- `is_transfer=1` flags payments, ACH, interest — excluded from spending queries
- Categories: 2-level hierarchy (~49 categories), top-level groups: Food & Drink, Shopping, Travel, Health & Wellness, Fees & Interest, etc.
- Shopping subcategories include: Camping & Outdoor, Photography, Office (for hobby/work tracking)
- `backup_db()` creates `.db.bak` + auto-exports `Finance/categorization_rules.json` (751+ rules) before every import
- `backup-rules` / `restore-rules` commands for manual export/import of categorization rules
- **Full rebuild**: `init` → `restore-rules` → `import` → `categorize` → `import-amazon` → `import-payslips` → `import-tax` → `import-fidelity`
- `finance_db.py validate` — post-import balance validation against PDF balance summaries
- `/finance <question>` translates natural language to SQL queries — supports payslip/income/cash-flow queries
- matplotlib installed in venv for chart generation to `Finance/reports/`
- **Finance CLAUDE.md** at `Finance/CLAUDE.md` documents all data sources, schema, tax facts, query patterns; root CLAUDE.md routes to it

### Spending Analysis Insights (2026-02-28)
- **2025+ monthly avg**: $9,826/mo ($137.6K over 14 months); baseline without travel/legal: ~$5-6K/mo
- **Travel is #1**: $40.6K ($3.1K/mo, 30% of spend) — Costco Travel ($15K), Chase Travel ($5.9K), Cathay Pacific ($4.5K)
- **Legal dropped to zero**: $18K in 2025 (divorce), only $7 in 2026
- **Shopping**: $20.5K — Amazon $8.4K (camping/tech gear), B&H Photo $3.7K, Costco.com $930
- **Food delivery eliminated**: was $900/mo in 2023, now $0 since Mar 2024
- **Groceries are lean**: $536/mo, Costco ($3K) + QFC ($2.1K) + Trader Joe's ($852)
- **Fast food modest**: $134/mo — MOD Pizza ($677), McDonald's ($696)
- **Restaurants**: $401/mo — La Casita is go-to (28 visits, $30 avg)
- **Subscriptions audit (Feb 2026)**: cancelled Quicken ($79/yr), LeetCode ($468/yr), confirmed Windsurf already cancelled ($1,560/yr), cancelled Cursor ($264/yr) = **$2,371/yr savings**
- Neetcode was a lifetime purchase ($297 one-time), not a subscription
- Apple billing is ~$165/mo ($2K/yr) — bundled charges, hard to audit from CC data, needs Apple ID review
- **W8TECH_*SA** on Apple Card = Windsurf AI coding tool ($130/mo)

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

### Cash Flow Crisis (2026-02-28)
- **Only 31% of gross pay reaches the bank** — 32% taxes, 33% post-tax deductions, 4% pre-tax
- Post-tax deductions: 401(k) after-tax ~$7K/mo, RSU offset ~$4.7K/mo, ESPP ~$3.4K/mo
- Monthly fixed obligations ~$21.3K: spousal maintenance ($10K), mortgage ($6.7K), SoFi loan ($1.8K), child support ($1.3K), insurance ($550), HOA ($600), nanny ($350)
- Net deposits ~$14.4K/mo vs obligations + CC spending ~$33K/mo = **~$19K/month structural deficit**
- **HELOC draws: $155K net in 5 months** (Oct 2025 – Feb 2026)
- Checking account data: `Finance/checking-accounts/fidelity-cma-4983/` (quarterly CSVs)
- "TRANSFERRED FROM MINIMUM TRANSFER VS. Z31-859340-1" = automatic Fidelity margin/LOC sweep
- "NSM DBAMR.COOP" = mortgage payments ($4,957 + $1,780 = $6,737/mo)
- Rental income: $1,995/mo from "Apartments.c APTS Smoth"
- **ESPP suspended** for next period (Jun 2026+): only $3,864/yr true benefit vs $40.8K/yr cash freed
- User considering whether to also reduce after-tax 401(k) ($7K/mo = biggest discretionary lever)

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

### Cash Flow / HELOC Monitoring (2026-02-28) `(active)`
- HELOC balance/limit unknown — need to check; determines urgency of cash flow fix
- $40K tender offer expected next month — provides one-time cash relief
- Re-evaluate withholding in October per safe harbor strategy
- ESPP suspended starting next period (Jun 2026)
