---
description: Ingest Amazon order history CSV into finance database
---

# /ingest-amazon — Amazon Order History Ingestion

Import Amazon purchase history CSV from `~/Dropbox/0-FinancialStatements/amazon/` into the `amazon_orders` table in `Finance/finance.db`.

## Steps

1. Run `python3 .claude/scripts/finance_db.py import-amazon` to import new orders
2. Run `python3 .claude/scripts/finance_db.py categorize-amazon` to apply keyword rules to product names
3. Display the import summary and categorization results to the user
4. If there are many uncategorized orders, suggest running `/finance review` to add Amazon-specific keyword rules

## Notes

- The CSV is a **full snapshot** — the pipeline uses a date watermark + UNIQUE constraint for deduplication
- Re-running is safe and idempotent (0 new rows on second run)
- Payment method is parsed to extract card_type and card_last4 for cross-referencing with credit card transactions
- Source CSVs: `~/Dropbox/0-FinancialStatements/amazon/*.csv`
