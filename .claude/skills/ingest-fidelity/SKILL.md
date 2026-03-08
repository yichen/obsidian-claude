---
name: ingest-fidelity
description: "Ingest Fidelity combined account statement PDFs into structured YAML data"
---

Run the Fidelity account statement ingestion script to parse monthly investment report PDFs and save as YAML.

**Process:**
1. Run `Scripts/venv/bin/python3 .claude/scripts/ingest_fidelity_accounts.py <subcommand> $ARGUMENTS` from the Obsidian root
2. If no arguments provided, default to `scan` to show what's new
3. Report the results — number of PDFs processed, validation status, any warnings

**Common usage:**
- `/ingest-fidelity scan` — Show available PDFs and processing status
- `/ingest-fidelity scan --year 2025` — Show PDFs for a specific year
- `/ingest-fidelity run` — Process all new PDFs
- `/ingest-fidelity run --year 2025 --force` — Re-process all PDFs for a year
- `/ingest-fidelity chain` — Validate monthly continuity (ending == next beginning)
- `/ingest-fidelity reconcile --year 2025` — Compare monthly YAMLs against year-end report

**Output location:** `Finance/fidelity-accounts/YYYY-MM-DD.yaml`

**After ingestion, import to DB:**
Run `Scripts/venv/bin/python3 .claude/scripts/finance_db.py import-fidelity` to load YAMLs into SQLite.

**Accounts covered:** 9 accounts (brokerage, CMA, IRA, Roth IRA, 401k, 2x UTMA, HSA)
**Source:** `~/Dropbox/0-FinancialStatements/fidelity-accounts/<year>/`
