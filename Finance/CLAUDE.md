# Finance Data

## Database

**SQLite**: `Finance/finance.db`
**Script**: `.claude/scripts/finance_db.py`
**Run with**: `Scripts/venv/bin/python3 .claude/scripts/finance_db.py <command>`
**Slash command**: `/finance`

## Data Sources

### Credit Card Transactions (`transactions` table)
- **Source CSVs**: `Finance/credit-card/<card-name>/YYYY-MM-DD.csv`
- **Cards**: Apple Card, Chase Prime/Sapphire/Freedom, Fidelity Rewards/Credit Card, BofA Atmos Rewards (7982)
- **Range**: Dec 2022 – Feb 2026 (~4,900 transactions)
- **Categorization**: ~500 keyword rules, 99.7% categorized
- **Key fields**: date, description, amount (negative = charge), is_transfer, category_id
- **Import command**: `finance_db.py import`

### Amazon Orders (`amazon_orders` table)
- **Source CSVs**: `~/Dropbox/0-FinancialStatements/amazon/*.csv`
- **Import command**: `finance_db.py import-amazon`

### Payslips (`payslips` + `payslip_line_items` tables)
- **Source YAMLs**: `Finance/payslips/<employer>/*.yaml`
- **Employers**: Salesforce (Jan 2025–present), ServiceTitan (Dec 2025–present)
- **44 payslips**, ~1,032 line items across 5 sections
- **Pay types**: salary, bonus, rsu, void
- **Line item sections**: earnings, employee_taxes, pre_tax_deductions, post_tax_deductions, employer_paid_benefits
- **Dedup key**: (employer, pay_date, pay_period_start, pay_period_end, gross_pay)
- **Import command**: `finance_db.py import-payslips`

### W-4 Withholding Election History
- **Location**: `Finance/payslips/<employer>/w4-history.yaml`
- **Format**: List of elections ordered newest-first, each with effective_date, marital_status, extra_withholding, multiple_jobs_or_spouse_works, last_updated
- **Dedup key**: effective_date + last_updated timestamp
- **Current files**: Salesforce (`salesforce/w4-history.yaml`), ServiceTitan (`servicetitan/w4-history.yaml`)
- **Update workflow**: User provides screenshot of election history → extract new records → append only records not already present

### Tax Documents (`tax_documents` + `tax_line_items` tables)
- **Source YAMLs**: `Finance/tax/prepare/<year>/` (CPA inputs) and `Finance/tax/archive/<year>/` (filed returns)
- **Ingestion script**: `.claude/scripts/ingest_tax.py` — parses PDFs from `~/Dropbox/1-Tax/`
- **Slash command**: `/ingest-tax` (scan, run, cross-validate)
- **68 documents**, ~851 line items across 2022–2025
- **Form types**: W-2, 1099-R, 1098, 1099-INT, 1099-CONSOLIDATED, 5498-SA, 5498, 1099-SA, Schedule-H, 1040
- **1099-CONSOLIDATED**: Fidelity & Morgan Stanley brokerage accounts — contains 1099-DIV, 1099-INT, 1099-B, 1099-MISC sub-forms
- **Key fields**: `tax_documents.form_type`, `tax_year`, `payer_name`, `source_folder` (prepare/archive)
- **Line items**: `tax_line_items.box_name` (e.g., `1_wages`, `2_fed_tax_withheld`, `summary.adjusted_gross_income`), `box_value` (numeric), `box_text` (string), `box_bool` (0/1)
- **Consolidated 1099 line items**: `1099-DIV.1a_total_ordinary_dividends`, `1099-INT.1_interest_income`, `1099-B.total.gain_loss`, `1099-B.short_term.proceeds`, etc.
- **Dedup key**: `yaml_file` (path relative to vault root)
- **Import command**: `finance_db.py import-tax`
- **Cross-validation**: `ingest_tax.py --cross-validate` — compares prepare-folder W-2s/1099s against archive 1040

### Fidelity Accounts (`fidelity_accounts` + `fidelity_portfolio_snapshots` + `fidelity_monthly_snapshots` + `fidelity_holdings` + `fidelity_cma_transactions` tables)
- **Source YAMLs**: `Finance/fidelity-accounts/YYYY-MM-DD.yaml`
- **Ingestion script**: `.claude/scripts/ingest_fidelity_accounts.py` — parses PDFs from `~/Dropbox/0-FinancialStatements/fidelity-accounts/`
- **Slash command**: `/ingest-fidelity` (scan, run, chain, reconcile)
- **13 monthly statements** (Jan 2025 – Jan 2026), 9 accounts, 96 monthly snapshots, 274 holdings records
- **481 CMA transactions** parsed from Z26-474983 activity sections (deposits, withdrawals, checks, exchanges)
- **Import command**: `finance_db.py import-fidelity`

**Account inventory:**

| Account # | Type | Tax Status | Beneficiary | Notes |
|-----------|------|------------|-------------|-------|
| X86-610887 | individual_brokerage | taxable | Yi | Liquidated mid-2025 |
| Z26-474983 | cash_management | taxable | Yi | Primary cash/checking — has transaction-level activity |
| Z31-859340 | individual_brokerage | taxable | Yi | New mid-2025 |
| 249-729024 | traditional_ira | tax_deferred | Yi | Rolled over, closed mid-2025 |
| 249-733354 | roth_ira | tax_free | Yi | Closed mid-2025 |
| 413-189729 | self_employed_401k | tax_deferred | Yi | |
| Z06-592753 | utma | taxable | Ruby | Sheri claims Ruby |
| Z08-759437 | utma | taxable | Laurence | Yi claims Laurence |
| 231-574209 | hsa | tax_free | Yi | Largest growth account |

**CMA Transaction Categories:**
- **Sheri Martin** (Capital One ******0615): Spousal Maintenance ($95.5K), Child Support ($11.3K), Property Settlement ($100K), Divorce — Other ($6.9K) = **$213.7K total**
- **OFW (OurFamilyWizard)**: Kids Cost (debits) + Kids Cost (Reimbursement) (credits)
- **CC Payments**: Apple Card, Chase, Fidelity, BofA — all flagged `is_transfer=1`
- **Transfers**: BECU, Fidelity exchanges, Morgan Stanley — all flagged `is_transfer=1`
- **Fixed Obligations**: Mortgage, HELOC, SoFi Loan, HOA, Insurance, Phone/Internet
- **Other**: Payroll, Rental Income, IRS Estimated Tax, Venmo, Checks

**Key queries:**
- Net worth trajectory: `SELECT statement_date, ending_value FROM fidelity_portfolio_snapshots ORDER BY statement_date`
- Per-account trend: `SELECT fa.account_number, fms.statement_date, fms.ending_value FROM fidelity_monthly_snapshots fms JOIN fidelity_accounts fa ON fa.id=fms.account_id ORDER BY fms.statement_date`
- Holdings snapshot: `SELECT fh.symbol, fh.market_value, fh.cost_basis, fh.unrealized_gain_loss FROM fidelity_holdings fh JOIN fidelity_monthly_snapshots fms ON fms.id=fh.snapshot_id WHERE fms.statement_date='2025-12-31' AND fms.account_id=(SELECT id FROM fidelity_accounts WHERE account_number='231-574209')`
- Income by tax status: `SELECT statement_date, income_taxable, income_tax_deferred, income_tax_free, income_total FROM fidelity_portfolio_snapshots ORDER BY statement_date`
- CMA spending (non-transfer): `SELECT category, COUNT(*), SUM(amount) FROM fidelity_cma_transactions WHERE is_transfer=0 AND amount<0 GROUP BY category ORDER BY SUM(amount)`
- Sheri Martin payments: `SELECT category, COUNT(*), SUM(amount) FROM fidelity_cma_transactions WHERE category IN ('Spousal Maintenance','Child Support','Property Settlement','Divorce — Other') GROUP BY category`
- Monthly CMA cash flow: `SELECT strftime('%Y-%m', date) as month, SUM(CASE WHEN amount>0 THEN amount ELSE 0 END) as inflows, SUM(CASE WHEN amount<0 THEN amount ELSE 0 END) as outflows FROM fidelity_cma_transactions GROUP BY month ORDER BY month`
- OFW costs: `SELECT strftime('%Y-%m', date) as month, SUM(amount) FROM fidelity_cma_transactions WHERE category LIKE 'Kids Cost%' GROUP BY month ORDER BY month`

## Backup & Recovery

### Automatic Backup
Every import command (`import`, `import-amazon`, `import-payslips`, `import-tax`, `import-fidelity`) automatically:
1. Creates `Finance/finance.db.bak` (full DB copy, overwritten each time)
2. Exports all categorization rules to `Finance/categorization_rules.json`

The JSON file syncs via Obsidian Sync and is the **only irreplaceable data** — everything else can be reimported from source files.

### Key Files

| File | Purpose | Synced? |
|------|---------|---------|
| `Finance/finance.db` | SQLite database (all financial data) | Yes (Obsidian Sync) |
| `Finance/finance.db.bak` | Last pre-import snapshot | Yes |
| `Finance/categorization_rules.json` | 751 categorization rules (auto-exported) | Yes |
| `Finance/credit-card/processing_log.json` | CC PDF ingestion tracking | Yes |
| `Finance/fidelity-accounts/processing_log.json` | Fidelity PDF ingestion tracking | Yes |
| `Finance/tax/processing_log.json` | Tax PDF ingestion tracking | Yes |

### Manual Commands
- `finance_db.py backup-rules` — export rules to JSON on demand
- `finance_db.py restore-rules` — reimport rules from JSON into DB

### Full Rebuild Procedure
If the database is lost or corrupted, rebuild from scratch:
```bash
PYTHON=Scripts/venv/bin/python3
$PYTHON .claude/scripts/finance_db.py init               # schema + seed data
$PYTHON .claude/scripts/finance_db.py restore-rules       # 751 categorization rules
$PYTHON .claude/scripts/finance_db.py import              # CC transactions
$PYTHON .claude/scripts/finance_db.py categorize          # apply rules to CC txns
$PYTHON .claude/scripts/finance_db.py import-amazon       # Amazon orders
$PYTHON .claude/scripts/finance_db.py import-payslips     # payslips
$PYTHON .claude/scripts/finance_db.py import-tax          # tax documents
$PYTHON .claude/scripts/finance_db.py import-fidelity     # Fidelity accounts + CMA txns
```

### What's Reproducible vs. What's Not

| Data | Rows | Source | Reproducible? |
|------|------|--------|---------------|
| CC transactions | ~5,600 | CC CSVs in `Finance/credit-card/` | Yes — `import` |
| Amazon orders | ~3,200 | CSVs in `~/Dropbox/.../amazon/` | Yes — `import-amazon` |
| Payslips | ~1,000 | YAMLs in `Finance/payslips/` | Yes — `import-payslips` |
| Tax documents | ~900 | YAMLs in `Finance/tax/` | Yes — `import-tax` |
| Fidelity accounts + CMA | ~900 | YAMLs in `Finance/fidelity-accounts/` | Yes — `import-fidelity` |
| Categories + accounts | ~100 | Seed data in Python script | Yes — `init` |
| **Categorization rules** | **~750** | **`categorization_rules.json`** | **Only via `restore-rules`** |

The ~750 categorization rules were built up over many `/finance review` sessions. Only ~230 are in the Python script's seed data. The rest (~520) were added interactively and exist only in the DB and the JSON backup.

## Key Tax Facts

- **Filing status**: Head of Household in odd years (Yi is custodial parent), Single in even years (Sheri is custodial)
- **Dependent claims**: Yi claims Laurence, Sheri claims Ruby — every year (Section 19 of Child Support Order)
- **WA state**: No state income tax
- **Spousal maintenance**: NOT deductible (post-2018 TCJA divorce)
- **Child support** ($1,254/mo): Never deductible

## Query Tips

- Spending queries: `WHERE t.is_transfer = 0` and `ABS(t.amount)` (charges are negative)
- Category grouping: `COALESCE(cp.name, c.name)` for top-level categories
- Cash flow: JOIN payslips (net_pay) with transactions by `strftime('%Y-%m', date)`
- 401k contributions: query `payslip_line_items` WHERE description LIKE '%401%'
- Federal withholding: query `payslip_line_items` WHERE section = 'employee_taxes' AND description LIKE '%Federal%'
- Tax W-2 wages: `SELECT td.tax_year, td.payer_name, li.box_value FROM tax_documents td JOIN tax_line_items li ON li.doc_id=td.id WHERE td.form_type='W-2' AND li.box_name='1_wages'`
- AGI trend: `SELECT td.tax_year, MAX(CASE WHEN li.box_name='summary.adjusted_gross_income' THEN li.box_value END) as AGI FROM tax_documents td JOIN tax_line_items li ON li.doc_id=td.id WHERE td.form_type='1040' GROUP BY td.tax_year`
- Filter Yi's docs only: `AND td.recipient_ssn_last4 = '2622'`
- Investment income (from consolidated 1099s): `SELECT td.payer_name, MAX(CASE WHEN li.box_name='1099-DIV.1a_total_ordinary_dividends' THEN li.box_value END) as dividends, MAX(CASE WHEN li.box_name='1099-INT.1_interest_income' THEN li.box_value END) as interest, MAX(CASE WHEN li.box_name='1099-B.total.gain_loss' THEN li.box_value END) as broker_gain FROM tax_documents td JOIN tax_line_items li ON li.doc_id=td.id WHERE td.form_type='1099-CONSOLIDATED' AND td.tax_year=2025 AND td.recipient_ssn_last4='2622' GROUP BY td.id`
