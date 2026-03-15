---
name: ingest-payslips
description: "Ingest payslip PDFs into structured YAML data"
---

Run the payslip ingestion script to extract structured data from payslip PDFs and save as YAML files.

**Process:**
1. Run `Scripts/venv/bin/python3 .claude/scripts/ingest_payslips.py $ARGUMENTS` from the Obsidian root
2. If no arguments provided, default to `--scan` to show what's new
3. Report the results — number of payslips processed, any warnings or errors

**Common usage:**
- `/ingest-payslips --scan` — Show PDFs and payslip counts (no changes)
- `/ingest-payslips --run` — Process all new payslips
- `/ingest-payslips --run --employer salesforce` — Process only one employer
- `/ingest-payslips --run --force` — Re-process everything from scratch
- `/ingest-payslips --run --skip-errors` — Skip previously errored files

**Output location:** `Finance/payslips/<employer>/YYYY-MM-DD.yaml`

**Employers supported:** salesforce, servicetitan

**YAML schema per payslip:** employer, employee_id, pay period, pay date, pay type (salary/rsu/espp/bonus/void), summary (current + YTD), earnings, taxes, deductions, employer benefits, deposit info, 5 validation checks.

**Dedup:** Uses 5-tuple key (pay_date, period_start, period_end, gross_pay) — same payslip in multiple PDFs is recognized as duplicate.
