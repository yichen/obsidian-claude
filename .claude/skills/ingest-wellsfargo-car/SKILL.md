---
name: ingest-wellsfargo-car
description: "Ingest Wells Fargo car loan statement PDFs into structured YAML data"
---

Run the Wells Fargo car loan statement ingestion script to parse monthly loan PDFs and save as YAML.

**Process:**
1. Run `Scripts/venv/bin/python3 .claude/scripts/ingest_wellsfargo_car.py <subcommand> $ARGUMENTS` from the Obsidian root
2. If no arguments provided, default to `scan` to show what's new
3. Report the results -- number of PDFs processed, validation status, any warnings

**Common usage:**
- `/ingest-wellsfargo-car scan` -- Show available PDFs and processing status
- `/ingest-wellsfargo-car run` -- Process all new PDFs
- `/ingest-wellsfargo-car run --force` -- Re-process all PDFs
- `/ingest-wellsfargo-car chain` -- Validate YTD interest continuity across all months

**Output location:** `Finance/wellsfargo-car-loan/YYYY-MM.yaml`

**After ingestion, import to DB:**
Run `Scripts/venv/bin/python3 .claude/scripts/finance_db.py import-wellsfargo-car` to load YAMLs into SQLite.

**Source:** `~/Dropbox/0-FinancialStatements/wellsfargo-car-loan/<year>/`
