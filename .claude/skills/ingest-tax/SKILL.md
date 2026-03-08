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

### Options
- `--year YYYY` — process only a specific year (2022-2025)
- `--source prepare|archive` — which folder (default: prepare)
- `--force` — re-process everything (ignore processing log)

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
