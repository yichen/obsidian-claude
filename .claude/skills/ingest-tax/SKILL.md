---
name: ingest-tax
description: "Ingest tax document PDFs into structured YAML data"
---

# Tax Document Ingestion

Run the tax document ingestion pipeline to extract structured data from tax PDFs.

**Script**: `.claude/scripts/ingest_tax.py`
**Source PDFs**: `~/Dropbox/1-Tax/2-prepare/<year>/` (CPA inputs) and `~/Dropbox/1-Tax/3-archive/<year>/` (filed returns)
**Output**: `Finance/tax/prepare/<year>/` and `Finance/tax/archive/<year>/`

## Actions

Based on the user's request, run one of these commands:

### Scan (default — show what's available)
```bash
Scripts/venv/bin/python3 .claude/scripts/ingest_tax.py --scan
```

### Run ingestion
```bash
Scripts/venv/bin/python3 .claude/scripts/ingest_tax.py --run
```

### Cross-validate forms vs. 1040
```bash
Scripts/venv/bin/python3 .claude/scripts/ingest_tax.py --cross-validate [--year YYYY]
```
Compares prepare-folder W-2s, 1099s against the filed 1040. Writes `Finance/tax/archive/<year>/cross-validation.yaml`.

### Compute cross-year carryforwards
```bash
Scripts/venv/bin/python3 .claude/scripts/ingest_tax.py --carryforwards
```
Tracks capital loss carryforwards and IRA rollovers across all years. Writes `Finance/tax/carryforwards.yaml`.

### Options
- `--year YYYY` — process only a specific year (2020-2025)
- `--source prepare|archive` — which folder (default: prepare)
- `--force` — re-process everything (ignore processing log)

## 1040 Computation Engine

**Script**: `.claude/scripts/compute_1040.py`

Derives 1040 values from prepare-folder YAMLs using IRS rules. Can backtest against filed returns and generate draft estimates for future years.

### Commands
```bash
# Backtest: derive rules from 2020-2022, test on 2023-2024
Scripts/venv/bin/python3 .claude/scripts/compute_1040.py --backtest

# Test a specific year (compare computed vs actual filed return)
Scripts/venv/bin/python3 .claude/scripts/compute_1040.py --test --year 2023

# Draft 1040 for an upcoming year using current prepare-folder YAMLs
Scripts/venv/bin/python3 .claude/scripts/compute_1040.py --draft --year 2025
```

### Output files
- `Finance/tax/prepare/<year>/1040-draft.yaml` — estimated 1040 with confidence levels and manual review items
- `Finance/tax/prepare/<year>/1040-backtest.yaml` — computed vs actual comparison with accuracy %

### Rules implemented
- Lines 1a (W-2 wages), 1z (total wages), 2b (interest), 3a/3b (dividends), 4b (IRA dist), 7 (cap gain/loss)
- Standard vs. itemized deduction (from 1098 mortgage interest + SALT cap)
- Tax brackets (MFJ and Single/HoH) for 2020–2025
- Child tax credit ($2,000/child, phase-out above $400K MFJ AGI)
- Net Investment Income Tax (3.8% above $250K MFJ AGI)
- Capital loss carryforward (from `carryforwards.yaml`)

## Supported Form Types (Phase 1)
- **W-2**: Salesforce, ServiceTitan, Stripe, Lincoln Life, nanny, ADP (Airbnb/Meta)
- **1099-R**: Fidelity IRA, Fidelity 401(k) plans
- **1098**: Mortgage interest statements (Rocket Mortgage, Flagstar, Mr. Cooper, BECU)

## Validation
Every YAML includes a `validation` section:
- W-2: Box 4 = Box 3 × 6.2%, Box 6 ≥ Box 5 × 1.45%
- 1099-R: Box 2a ≤ Box 1
- 1098: has_interest check

Cross-validate W-2 wages against payslip data:
```sql
SELECT employer, SUM(gross_pay) FROM payslips WHERE strftime('%Y', pay_date) = '2025' GROUP BY employer;
```

$ARGUMENTS
