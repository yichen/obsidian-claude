Ingest BECU combined statement PDFs (checking + HELOC) into structured YAML data.

## Usage

Run the script with a subcommand:

```bash
Scripts/venv/bin/python3 .claude/scripts/ingest_becu.py <command>
```

## Commands

| Command | Description |
|---------|-------------|
| `scan` | List available PDFs (Jan 2025+) and processing status |
| `run` | Parse new PDFs, generate YAMLs (skip already processed) |
| `run --force` | Re-parse all PDFs |
| `chain` | Cross-statement validation (balance continuity, YTD interest accumulation) |
| `reconcile` | Cross-check BECU↔Fidelity CMA MONEYLINE transfers |

## After ingestion

Import into the finance database:

```bash
Scripts/venv/bin/python3 .claude/scripts/finance_db.py import-becu
```

$ARGUMENTS
