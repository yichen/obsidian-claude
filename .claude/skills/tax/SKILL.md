---
name: tax
description: "Unified tax command — ingest documents, compute 1040, backtest, and track issues"
---

# /tax — Unified Tax Command

Routes tax subcommands to the appropriate script or action.

**Scripts**:
- `.claude/scripts/ingest_tax.py` — document ingestion and cross-validation
- `.claude/scripts/compute_1040.py` — 1040 rule engine (backtest, test, draft)

**Issues tracker**: `Finance/tax/tax-issues.yaml`

## Subcommand Routing

Parse `$ARGUMENTS` and route to the matching subcommand below. If no arguments are provided, print the **Usage Summary** section.

### `scan [--year YYYY]`
```bash
Scripts/venv/bin/python3 .claude/scripts/ingest_tax.py --scan [--year YYYY]
```

### `run [--year YYYY] [--force]`
```bash
Scripts/venv/bin/python3 .claude/scripts/ingest_tax.py --run [--year YYYY] [--force]
```

### `validate [--year YYYY]`
```bash
Scripts/venv/bin/python3 .claude/scripts/ingest_tax.py --cross-validate [--year YYYY]
```

### `carryforwards`
```bash
Scripts/venv/bin/python3 .claude/scripts/ingest_tax.py --carryforwards
```

### `backtest`
```bash
Scripts/venv/bin/python3 .claude/scripts/compute_1040.py --backtest
```

### `test --year YYYY`
```bash
Scripts/venv/bin/python3 .claude/scripts/compute_1040.py --test --year YYYY
```
Year is required for this subcommand.

### `draft --year YYYY`
```bash
Scripts/venv/bin/python3 .claude/scripts/compute_1040.py --draft --year YYYY
```
Year is required for this subcommand.

### `issues [...]`
Manage the tax issues tracker at `Finance/tax/tax-issues.yaml`. Claude reads/writes the YAML directly — no script needed.

| Input | Action |
|-------|--------|
| `issues` or `issues list` | Show all OPEN + INVESTIGATING issues as a formatted table |
| `issues all` | Show all issues regardless of status |
| `issues add <description> [--year YYYY] [--category X]` | Append new OPEN issue; auto-assign next ID (TAX-NNN), set created=today. Prompt for hypothesis/resolution_path if not provided. |
| `issues resolve <id> [--note "text"]` | Set status=RESOLVED, resolved_at=today, add resolution_note |
| `issues wontfix <id> [--note "text"]` | Set status=WONT_FIX, resolved_at=today, add resolution_note |

**Valid categories**: `capital_gains`, `ordinary_income`, `deductions`, `credits`, `computation_accuracy`, `data_quality`, `missing_document`, `cpa_adjustment`

**Valid statuses**: `OPEN`, `INVESTIGATING`, `RESOLVED`, `WONT_FIX`

**ID format**: `TAX-NNN` — auto-increment from highest existing ID in the file.

## Usage Summary

When invoked with no arguments, print:

```
/tax — Unified tax command

  scan [--year YYYY]          Scan for unprocessed tax PDFs
  run [--year YYYY] [--force] Ingest tax documents into YAML
  validate [--year YYYY]      Cross-validate forms vs filed 1040
  carryforwards               Compute cross-year carryforwards
  backtest                    Backtest 1040 computation engine
  test --year YYYY            Test computed vs actual for a year
  draft --year YYYY           Draft 1040 estimate for a year
  issues [list|all|add|resolve|wontfix]  Manage tax issues tracker
```

$ARGUMENTS
