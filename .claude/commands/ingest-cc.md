---
description: Ingest credit card statement PDFs into CSV transaction data
---

Run the credit card statement ingestion script to extract transactions from PDF statements and save as CSVs.

**Process:**
1. Run `Scripts/venv/bin/python3 .claude/scripts/ingest_cc_statements.py $ARGUMENTS` from the Obsidian root
2. If no arguments provided, default to `--scan` to show what's new
3. Report the results — number of PDFs processed, any warnings or errors

**Common usage:**
- `/ingest-cc --scan` — Show new unprocessed PDFs (no changes)
- `/ingest-cc --run` — Process all new PDFs
- `/ingest-cc --run --card apple-card` — Process only one card
- `/ingest-cc --run --force` — Re-process everything from scratch
- `/ingest-cc --run --skip-errors` — Skip previously errored PDFs
- `/ingest-cc --reconcile` — Reconcile year-end summaries against ingested CSVs

**Output location:** `Finance/credit-card/<card-name>/YYYY-MM-DD.csv`

**Cards supported:** apple-card, chase-prime-1158, chase-sapphire-2341, chase-freedom-1350, fidelity-rewards, fidelity-credit-card, bofa-atmos-7982
