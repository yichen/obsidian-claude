#!/usr/bin/env python3
"""SoFi Personal Line of Credit statement PDF ingestion pipeline.

Parses monthly SoFi loan statements into structured YAML with validation.

Source PDFs: ~/Dropbox/0-FinancialStatements/sofi-loan/<year>/Statement-MM-YYYY_*.pdf
Output YAMLs: Finance/sofi-loan/YYYY-MM.yaml
Processing log: Finance/sofi-loan/processing_log.json
"""

import json
import logging
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed. Run: pip install pdfplumber", file=sys.stderr)
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# --- Path Resolution ---
SCRIPT_DIR = Path(__file__).parent.resolve()
OBSIDIAN_ROOT = SCRIPT_DIR.parent.parent
SOURCE_ROOT = Path.home() / "Dropbox" / "0-FinancialStatements" / "sofi-loan"
OUTPUT_ROOT = OBSIDIAN_ROOT / "Finance" / "sofi-loan"
LOG_FILE = OUTPUT_ROOT / "ingest.log"
PROCESSING_LOG_PATH = OUTPUT_ROOT / "processing_log.json"
MAX_PARSE_ATTEMPTS = 3  # Retry budget for transient PDF parse failures

# --- Logging ---
logger = logging.getLogger("ingest_sofi_loan")


def setup_logging():
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    fh = logging.FileHandler(LOG_FILE, mode="a")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)


# --- Processing Log ---

def load_processing_log() -> dict:
    if PROCESSING_LOG_PATH.exists():
        with open(PROCESSING_LOG_PATH) as f:
            return json.load(f)
    return {"version": 1, "last_run": None, "pdfs": {}}


def save_processing_log(log: dict):
    PROCESSING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log["last_run"] = datetime.now().isoformat(timespec="seconds")
    with open(PROCESSING_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


# --- PDF Discovery ---

def discover_pdfs() -> list[tuple[Path, str, str]]:
    """Returns list of (pdf_path, pdf_filename, statement_month YYYY-MM).

    Filename format: Statement-MM-YYYY_<hash>.pdf
    """
    pdfs = []
    seen = set()

    for year_dir in sorted(SOURCE_ROOT.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for pdf_file in sorted(year_dir.iterdir()):
            if pdf_file.suffix.lower() != ".pdf":
                continue
            m = re.match(r"Statement-(\d{2})-(\d{4})_", pdf_file.name)
            if not m:
                continue
            month, year = m.group(1), m.group(2)
            stmt_month = f"{year}-{month}"
            if stmt_month in seen:
                continue
            seen.add(stmt_month)
            pdfs.append((pdf_file, pdf_file.name, stmt_month))

    return pdfs


# --- PDF Parsing ---

def parse_money(text: str) -> Optional[float]:
    """Parse money string like '$1,234.56' to float."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    if text in ("-", "$-", "", "--"):
        return None
    text = text.replace("$", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def parse_date_mmddyyyy(text: str) -> Optional[str]:
    """Parse MM/DD/YYYY to YYYY-MM-DD string."""
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", text.strip())
    if not m:
        return None
    return f"{m.group(3)}-{m.group(1)}-{m.group(2)}"


def find_value_after_label(lines: list[str], label: str) -> Optional[str]:
    """Find the money value on the same line after a label."""
    for line in lines:
        if label in line:
            # Find dollar amounts on this line
            amounts = re.findall(r"\$[\d,]+\.\d{2}", line)
            if amounts:
                return amounts[-1]  # last amount on the line
    return None


def parse_statement(pdf_path: Path) -> dict:
    """Parse a SoFi loan statement PDF into a structured dict."""
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()

    lines = text.split("\n")

    # Account number
    account_number = ""
    for line in lines:
        if "Account Number:" in line:
            account_number = line.split("Account Number:")[-1].strip()
            break

    # Helper: find amount after a label
    def get_amount(label: str) -> Optional[float]:
        val = find_value_after_label(lines, label)
        return parse_money(val) if val else None

    current_balance = get_amount("Current Loan Balance")
    credit_limit = get_amount("Total Credit Limit")
    past_due = get_amount("Past Due Amount")
    total_payment_due = get_amount("Total Payment Due")

    # Current Payment Due appears twice — first is the breakdown amount, second context may vary
    # We need the first occurrence specifically
    payment_due = None
    for line in lines:
        if "Current Payment Due" in line and "Date" not in line:
            amounts = re.findall(r"\$[\d,]+\.\d{2}", line)
            if amounts:
                payment_due = parse_money(amounts[-1])
                break

    # Due date
    due_date = None
    for line in lines:
        if "Current Payment Due Date" in line:
            m = re.search(r"(\d{2}/\d{2}/\d{4})", line)
            if m:
                due_date = parse_date_mmddyyyy(m.group(1))
            break

    # Interest, Principal, Fees from the ACCOUNT SUMMARY section
    # These appear as single-word labels with amounts
    interest = None
    principal = None
    fees = None
    ytd_interest = None

    in_summary = False
    for line in lines:
        if "ACCOUNT SUMMARY" in line:
            in_summary = True
            continue
        if "LAST TRANSACTION" in line:
            break
        if not in_summary:
            continue

        # Match lines like "Interest $71.38" or "Principal $1,692.29"
        stripped = line.strip()
        if stripped.startswith("Interest ") and interest is None:
            amounts = re.findall(r"\$[\d,]+\.\d{2}", stripped)
            if amounts:
                interest = parse_money(amounts[-1])
        elif stripped.startswith("Principal ") and principal is None:
            amounts = re.findall(r"\$[\d,]+\.\d{2}", stripped)
            if amounts:
                principal = parse_money(amounts[-1])
        elif stripped.startswith("Fees ") and fees is None:
            amounts = re.findall(r"\$[\d,]+\.\d{2}", stripped)
            if amounts:
                fees = parse_money(amounts[-1])
        elif "Year to Date Interest Paid" in stripped:
            amounts = re.findall(r"\$[\d,]+\.\d{2}", stripped)
            if amounts:
                ytd_interest = parse_money(amounts[-1])

    # LAST TRANSACTION table
    # Format: Date Principal Interest Fees Total
    # Then: MM/DD/YYYY $X $X $X $X
    last_txn = {}
    found_last_txn_header = False
    for line in lines:
        if "LAST TRANSACTION" in line:
            found_last_txn_header = True
            continue
        if found_last_txn_header:
            # Skip the "Date Principal Interest Fees Total" header line
            if line.strip().startswith("Date"):
                continue
            # Parse the data line
            m = re.match(
                r"\s*(\d{2}/\d{2}/\d{4})\s+"
                r"\$?([\d,]+\.\d{2})\s+"
                r"\$?([\d,]+\.\d{2})\s+"
                r"\$?([\d,]+\.\d{2})\s+"
                r"\$?([\d,]+\.\d{2})",
                line,
            )
            if m:
                last_txn = {
                    "date": parse_date_mmddyyyy(m.group(1)),
                    "principal": float(m.group(2).replace(",", "")),
                    "interest": float(m.group(3).replace(",", "")),
                    "fees": float(m.group(4).replace(",", "")),
                    "total": float(m.group(5).replace(",", "")),
                }
            break

    # Derive statement_month from the due_date (statement is for the month before due date)
    # Or from filename
    stmt_month_from_file = re.match(r"Statement-(\d{2})-(\d{4})", pdf_path.name)
    if stmt_month_from_file:
        stmt_month = f"{stmt_month_from_file.group(2)}-{stmt_month_from_file.group(1)}"
    elif due_date:
        d = date.fromisoformat(due_date)
        # Statement month is the month before the due date
        if d.month == 1:
            stmt_month = f"{d.year - 1}-12"
        else:
            stmt_month = f"{d.year}-{d.month - 1:02d}"
    else:
        stmt_month = "unknown"

    # --- Validation ---
    mismatches = []

    # 1. payment_due == principal + interest + fees
    if payment_due is not None and principal is not None and interest is not None and fees is not None:
        expected = round(principal + interest + fees, 2)
        payment_eq = abs(payment_due - expected) < 0.02
        if not payment_eq:
            mismatches.append(
                f"payment_due ({payment_due}) != principal ({principal}) + interest ({interest}) + fees ({fees}) = {expected}"
            )
    else:
        payment_eq = None

    # 2. last_txn total == total_payment_due
    if last_txn and total_payment_due is not None:
        last_txn_eq = abs(last_txn["total"] - total_payment_due) < 0.02
        if not last_txn_eq:
            mismatches.append(
                f"last_txn_total ({last_txn['total']}) != total_payment_due ({total_payment_due})"
            )
    else:
        last_txn_eq = None

    # 3. last_txn breakdown: principal + interest + fees == total
    if last_txn:
        lt_expected = round(last_txn["principal"] + last_txn["interest"] + last_txn["fees"], 2)
        lt_breakdown_ok = abs(last_txn["total"] - lt_expected) < 0.02
        if not lt_breakdown_ok:
            mismatches.append(
                f"last_txn breakdown mismatch: {last_txn['principal']} + {last_txn['interest']} + {last_txn['fees']} = {lt_expected} != {last_txn['total']}"
            )
    else:
        lt_breakdown_ok = None

    result = {
        "statement_month": stmt_month,
        "account_number": account_number,
        "account_type": "Personal Line of Credit",
        "current_balance": current_balance,
        "credit_limit": credit_limit,
        "payment_due": payment_due,
        "past_due": past_due,
        "total_payment_due": total_payment_due,
        "due_date": due_date,
        "breakdown": {
            "principal": principal,
            "interest": interest,
            "fees": fees,
        },
        "ytd_interest_paid": ytd_interest,
        "last_transaction": last_txn if last_txn else None,
        "validation": {
            "principal_plus_interest_eq_payment": payment_eq,
            "last_txn_total_eq_payment": last_txn_eq,
            "last_txn_breakdown_ok": lt_breakdown_ok,
            "mismatches": mismatches,
        },
        "source": {
            "file": pdf_path.name,
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        },
    }

    return result


# --- YAML Output ---

def write_yaml(data: dict, output_path: Path):
    """Write statement data to YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    class MoneyDumper(yaml.SafeDumper):
        pass

    def float_representer(dumper, value):
        if value == int(value):
            return dumper.represent_scalar("tag:yaml.org,2002:float", f"{value:.2f}")
        return dumper.represent_scalar("tag:yaml.org,2002:float", f"{value:.2f}")

    MoneyDumper.add_representer(float, float_representer)

    with open(output_path, "w") as f:
        yaml.dump(data, f, Dumper=MoneyDumper, default_flow_style=False,
                  sort_keys=False, allow_unicode=True)

    logger.info(f"  Written: {output_path.name}")


# --- Chain Validation ---

def run_chain_validation(yaml_dir: Path) -> list[str]:
    """Cross-statement validation: balance continuity, YTD interest, missing months."""
    yaml_files = sorted(yaml_dir.glob("*.yaml"))
    if not yaml_files:
        logger.info("No YAML files found for chain validation.")
        return []

    statements = []
    for yf in yaml_files:
        with open(yf) as f:
            data = yaml.safe_load(f)
        if data:
            statements.append(data)

    statements.sort(key=lambda s: s["statement_month"])
    errors = []

    # Check for missing months
    for i in range(1, len(statements)):
        prev_month = statements[i - 1]["statement_month"]
        curr_month = statements[i]["statement_month"]
        py, pm = int(prev_month[:4]), int(prev_month[5:7])
        cy, cm = int(curr_month[:4]), int(curr_month[5:7])
        expected_y, expected_m = (py, pm + 1) if pm < 12 else (py + 1, 1)
        if cy != expected_y or cm != expected_m:
            errors.append(f"Missing month gap: {prev_month} -> {curr_month}")

    # Balance continuity: prev_balance - curr_last_txn_principal ≈ current_balance
    # Note: last_transaction shows the ACTUAL payment applied this month;
    # breakdown shows the NEXT month's projected allocation.
    for i in range(1, len(statements)):
        prev = statements[i - 1]
        curr = statements[i]
        prev_bal = prev.get("current_balance")
        curr_bal = curr.get("current_balance")
        last_txn = curr.get("last_transaction") or {}
        curr_principal = last_txn.get("principal")

        if prev_bal is not None and curr_bal is not None and curr_principal is not None:
            expected_bal = round(prev_bal - curr_principal, 2)
            diff = abs(expected_bal - curr_bal)
            if diff > 0.05:
                errors.append(
                    f"Balance chain break at {curr['statement_month']}: "
                    f"prev_balance ({prev_bal}) - last_txn_principal ({curr_principal}) = {expected_bal} "
                    f"!= current_balance ({curr_bal}), diff={diff:.2f}"
                )

    # YTD interest accumulation (resets each Jan)
    # Uses last_txn_interest (actual interest paid) not breakdown.interest (projected)
    ytd_sum = 0.0
    current_year = None
    for stmt in statements:
        sm = stmt["statement_month"]
        y = int(sm[:4])
        last_txn = stmt.get("last_transaction") or {}
        interest = last_txn.get("interest")
        ytd_reported = stmt.get("ytd_interest_paid")

        if current_year is None or y != current_year:
            current_year = y
            ytd_sum = 0.0

        if interest is not None:
            ytd_sum = round(ytd_sum + interest, 2)

        if ytd_reported is not None and abs(ytd_sum - ytd_reported) > 0.10:
            errors.append(
                f"YTD interest mismatch at {sm}: computed={ytd_sum}, reported={ytd_reported}"
            )

    return errors


# --- CMA Reconciliation ---

def run_reconcile(yaml_dir: Path) -> list[str]:
    """Cross-check SoFi payments against CMA transactions."""
    import sqlite3

    db_path = OBSIDIAN_ROOT / "Finance" / "finance.db"
    if not db_path.exists():
        return ["Finance database not found — run import-fidelity first"]

    yaml_files = sorted(yaml_dir.glob("*.yaml"))
    if not yaml_files:
        return ["No YAML files found"]

    conn = sqlite3.connect(str(db_path))
    errors = []
    matched = 0

    for yf in yaml_files:
        with open(yf) as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        last_txn = data.get("last_transaction")
        if not last_txn or not last_txn.get("date"):
            continue

        txn_date = last_txn["date"]
        txn_total = last_txn["total"]

        # CMA settlement dates lag SoFi payment dates by 1-8 days (bank processing)
        # Match within a 10-day window after the SoFi payment date
        rows = conn.execute(
            """SELECT date, amount, description, category
               FROM fidelity_cma_transactions
               WHERE date BETWEEN ? AND date(?, '+10 days')
                 AND ABS(ABS(amount) - ?) < 0.02""",
            (txn_date, txn_date, txn_total),
        ).fetchall()

        if rows:
            matched += 1
            logger.debug(f"  {data['statement_month']}: matched CMA txn on {txn_date}")
        else:
            errors.append(
                f"{data['statement_month']}: no CMA match for ${txn_total:.2f} on {txn_date}"
            )

    conn.close()
    logger.info(f"Reconciliation: {matched} matched, {len(errors)} unmatched")
    return errors


# --- CLI Commands ---

def cmd_scan():
    """List available PDFs and their processing status."""
    pdfs = discover_pdfs()
    log = load_processing_log()
    processed = set(log.get("pdfs", {}).keys())

    logger.info(f"Source: {SOURCE_ROOT}")
    logger.info(f"Found {len(pdfs)} statement PDFs\n")

    new_count = 0
    for pdf_path, filename, stmt_month in pdfs:
        status = "processed" if filename in processed else "NEW"
        if status == "NEW":
            new_count += 1
        logger.info(f"  {stmt_month}  {status:>10}  {filename}")

    logger.info(f"\n{new_count} new / {len(pdfs)} total")


def cmd_run(force: bool = False):
    """Parse PDFs and generate YAMLs."""
    pdfs = discover_pdfs()
    log = load_processing_log()
    processed = set(log.get("pdfs", {}).keys())

    to_process = pdfs if force else [(p, f, m) for p, f, m in pdfs if f not in processed]

    if not to_process:
        logger.info("No new PDFs to process.")
        return

    logger.info(f"Processing {len(to_process)} PDFs...")
    success = 0
    errors = 0

    for pdf_path, filename, stmt_month in to_process:
        logger.info(f"\n--- {stmt_month} ({filename}) ---")
        try:
            for _attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
                try:
                    data = parse_statement(pdf_path)
                    break
                except Exception as e:
                    if _attempt == MAX_PARSE_ATTEMPTS:
                        raise
                    print(f"  Attempt {_attempt}/{MAX_PARSE_ATTEMPTS} failed: {e}, retrying...")
            output_path = OUTPUT_ROOT / f"{stmt_month}.yaml"
            write_yaml(data, output_path)

            validation = data.get("validation", {})
            mismatches = validation.get("mismatches", [])
            if mismatches:
                for mm in mismatches:
                    logger.warning(f"  VALIDATION: {mm}")

            log.setdefault("pdfs", {})[filename] = {
                "statement_month": stmt_month,
                "output_file": f"Finance/sofi-loan/{stmt_month}.yaml",
                "processed_at": datetime.now().isoformat(timespec="seconds"),
                "validation_passed": len(mismatches) == 0,
            }
            save_processing_log(log)
            success += 1

        except Exception as e:
            logger.error(f"  ERROR: {e}")
            errors += 1

    logger.info(f"\nDone: {success} processed, {errors} errors")


def cmd_chain():
    """Run cross-statement chain validation."""
    errors = run_chain_validation(OUTPUT_ROOT)
    if errors:
        logger.info("Chain validation FAILED:")
        for e in errors:
            logger.warning(f"  {e}")
    else:
        logger.info("Chain validation PASSED — all statements consistent")


def cmd_reconcile():
    """Cross-check against CMA transactions."""
    errors = run_reconcile(OUTPUT_ROOT)
    if errors:
        logger.info("Reconciliation issues:")
        for e in errors:
            logger.warning(f"  {e}")
    else:
        logger.info("All SoFi payments matched in CMA transactions")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="SoFi loan statement PDF ingestion pipeline"
    )
    parser.add_argument(
        "command",
        choices=["scan", "run", "chain", "reconcile"],
        help="scan: show status; run: parse PDFs; chain: validate continuity; reconcile: match CMA",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-process all PDFs (ignore processing log)",
    )

    args = parser.parse_args()

    setup_logging()
    logger.info(
        f"SoFi Loan Statement Ingestion — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    if args.command == "scan":
        cmd_scan()
    elif args.command == "run":
        cmd_run(force=args.force)
    elif args.command == "chain":
        cmd_chain()
    elif args.command == "reconcile":
        cmd_reconcile()


if __name__ == "__main__":
    main()
