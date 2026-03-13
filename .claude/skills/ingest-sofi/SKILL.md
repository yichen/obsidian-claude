---
name: ingest-sofi
description: "Ingest SoFi loan statement PDFs into structured YAML data"
---

Run the SoFi loan statement ingestion script to parse monthly loan PDFs and save as YAML.

**Process:**
1. Run `Scripts/venv/bin/python3 .claude/scripts/ingest_sofi_loan.py <subcommand> $ARGUMENTS` from the Obsidian root
2. If no arguments provided, default to `scan` to show what's new
3. Report the results — number of PDFs processed, validation status, any warnings

**Common usage:**
- `/ingest-sofi scan` — Show available PDFs and processing status
- `/ingest-sofi run` — Process all new PDFs
- `/ingest-sofi run --force` — Re-process all PDFs
- `/ingest-sofi chain` — Validate balance continuity across all months
- `/ingest-sofi reconcile` — Cross-check against CMA transactions

**Output location:** `Finance/sofi-loan/YYYY-MM.yaml`

**After ingestion, import to DB:**
Run `Scripts/venv/bin/python3 .claude/scripts/finance_db.py import-sofi` to load YAMLs into SQLite.

**Source:** `~/Dropbox/0-FinancialStatements/sofi-loan/<year>/`
