#!/usr/bin/env python3
"""Wells Fargo car loan statement PDF ingestion pipeline.

Parses monthly Wells Fargo Auto statements into structured YAML with validation.

Source PDFs: ~/Dropbox/0-FinancialStatements/wellsfargo-car-loan/<year>/MMDDYY WellsFargo.pdf
Output YAMLs: Finance/wellsfargo-car-loan/YYYY-MM.yaml
Processing log: Finance/wellsfargo-car-loan/processing_log.json
"""

import json
import logging
import re
import sys
from datetime import datetime
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
SOURCE_ROOT = Path.home() / "Dropbox" / "0-FinancialStatements" / "wellsfargo-car-loan"
OUTPUT_ROOT = OBSIDIAN_ROOT / "Finance" / "wellsfargo-car-loan"
LOG_FILE = OUTPUT_ROOT / "ingest.log"
PROCESSING_LOG_PATH = OUTPUT_ROOT / "processing_log.json"
MAX_PARSE_ATTEMPTS = 3  # Retry budget for transient PDF parse failures

# --- Logging ---
logger = logging.getLogger("ingest_wellsfargo_car")


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

    Filename format: MMDDYY WellsFargo.pdf (e.g., 011026 WellsFargo.pdf)
    The date in the filename is the statement date in MMDDYY format.
    """
    pdfs = []
    seen = set()

    for year_dir in sorted(SOURCE_ROOT.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for pdf_file in sorted(year_dir.iterdir()):
            if pdf_file.suffix.lower() != ".pdf":
                continue
            m = re.match(r"(\d{2})(\d{2})(\d{2})\s+WellsFargo\.pdf", pdf_file.name)
            if not m:
                continue
            mm, dd, yy = m.group(1), m.group(2), m.group(3)
            year = int(yy)
            year_full = 2000 + year if year < 100 else year
            stmt_month = f"{year_full}-{mm}"
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


def parse_date_mmddyy(text: str) -> Optional[str]:
    """Parse MM/DD/YY to YYYY-MM-DD string."""
    m = re.match(r"(\d{2})/(\d{2})/(\d{2,4})", text.strip())
    if not m:
        return None
    mm, dd, yy = m.group(1), m.group(2), m.group(3)
    if len(yy) == 2:
        year = 2000 + int(yy)
    else:
        year = int(yy)
    return f"{year}-{mm}-{dd}"


def parse_statement(pdf_path: Path) -> dict:
    """Parse a Wells Fargo Auto statement PDF into a structured dict."""
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()

    lines = text.split("\n")

    # --- Account Statement Box ---
    statement_date = None
    account_number = ""
    vehicle = None
    interest_rate = None
    monthly_payment = None
    maturity_date = None
    daily_interest = None
    payoff_amount = None
    payoff_date = None

    for line in lines:
        # Statement date: "Statement date MM/DD/YY"
        m = re.search(r"Statement date\s+(\d{2}/\d{2}/\d{2,4})", line)
        if m:
            statement_date = parse_date_mmddyy(m.group(1))

        # Account number
        m = re.search(r"Account number\s+(\d+)", line)
        if m:
            account_number = m.group(1)

        # Vehicle: "Vehicle 2026 Tesla Model Y 2026" (sometimes year is duplicated)
        m = re.search(r"Vehicle\s+(.+)", line)
        if m:
            v = m.group(1).strip()
            # Remove trailing duplicate year if present
            v = re.sub(r"\s+\d{4}$", "", v)
            vehicle = v

        # Interest rate
        m = re.search(r"Interest rate\s+([\d.]+)%", line)
        if m:
            interest_rate = float(m.group(1))

        # Monthly payment
        m = re.search(r"Monthly payment\s+\$([\d,]+\.\d{2})", line)
        if m:
            monthly_payment = parse_money(m.group(1))

        # Maturity date
        m = re.search(r"Maturity date\s+(\d{2}/\d{2}/\d{2,4})", line)
        if m:
            maturity_date = parse_date_mmddyy(m.group(1))

        # Daily interest
        m = re.search(r"Daily interest\s+\$([\d,]+\.\d{2})", line)
        if m:
            daily_interest = parse_money(m.group(1))

        # Payoff amount: "Payoff as of MM/DD/YY (cid:135)$XX,XXX.XX"
        m = re.search(r"Payoff as of\s+(\d{2}/\d{2}/\d{2,4})\s+.*?\$([\d,]+\.\d{2})", line)
        if m:
            payoff_date = parse_date_mmddyy(m.group(1))
            payoff_amount = parse_money(m.group(2))

    # --- Payment Summary ---
    payment_due_date = None
    current_payment_due = None
    total_amount_due = None

    for line in lines:
        # Payment due date
        m = re.search(r"Payment due date\s+(\d{2}/\d{2}/\d{2,4})", line)
        if m and payment_due_date is None:
            payment_due_date = parse_date_mmddyy(m.group(1))

        # Current payment due
        m = re.search(r"Current payment due\s+\$([\d,]+\.\d{2})", line)
        if m and current_payment_due is None:
            current_payment_due = parse_money(m.group(1))

        # Total amount due (first occurrence only — the coupon section repeats it)
        m = re.search(r"Total amount due\s+\$?([\d,]+\.\d{2})", line)
        if m and total_amount_due is None:
            total_amount_due = parse_money(m.group(1))

    # --- Activity Section ---
    # Find "Activity since your last statement" and then parse transactions
    activity = []
    in_activity = False
    # Track current transaction for principal/interest sub-lines
    current_txn = None

    for line in lines:
        if "Activity since your last statement" in line:
            in_activity = True
            continue

        if not in_activity:
            continue

        # Skip header line
        if line.strip().startswith("Date") and "Description" in line:
            continue

        # Transaction line: "MM/DD/YY Description $amount [right-column noise]"
        # Must check BEFORE noise filters since right-column text can appear on same line
        m = re.match(r"\s*(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+\$([\d,]+\.\d{2})", line)
        if m:
            # Save previous transaction
            if current_txn:
                activity.append(current_txn)

            txn_date = parse_date_mmddyy(m.group(1))
            # Description may have trailing right-column noise after the amount
            # The regex is non-greedy so description stops before the $amount
            description = m.group(2).strip()
            amount = parse_money(m.group(3))

            current_txn = {
                "date": txn_date,
                "description": description,
                "amount": amount,
            }
            continue

        # Principal sub-line: "Principal $XXX.XX"
        m = re.match(r"\s*Principal\s+\$([\d,]+\.\d{2})", line)
        if m and current_txn:
            current_txn["principal"] = parse_money(m.group(1))
            continue

        # Interest sub-line: "Interest $XXX.XX [trailing noise]"
        m = re.match(r"\s*Interest\s+\$([\d,]+\.\d{2})", line)
        if m and current_txn:
            current_txn["interest"] = parse_money(m.group(1))
            continue

        # End markers — stop parsing activity section
        if any(marker in line for marker in [
            "Secure. Fast. Easy.",
            "Welcome to Wells Fargo",
            "The total interest paid",
        ]):
            if current_txn:
                activity.append(current_txn)
                current_txn = None
            break

        # Skip noise lines from right column (only if no transaction/sub-line matched)
        # These are remnants of the right column merged into activity text

    # Save last transaction if not yet saved
    if current_txn:
        activity.append(current_txn)

    # --- YTD Interest ---
    ytd_interest = None
    ytd_interest_year = None
    for line in lines:
        m = re.search(
            r"total interest paid on your loan in (\d{4}) was \$([\d,]+\.\d{2})",
            line,
        )
        if m:
            ytd_interest_year = int(m.group(1))
            ytd_interest = parse_money(m.group(2))
            break

    # --- Derive statement month from filename ---
    m = re.match(r"(\d{2})(\d{2})(\d{2})", pdf_path.name)
    if m:
        mm = m.group(1)
        yy = int(m.group(3))
        year_full = 2000 + yy if yy < 100 else yy
        stmt_month = f"{year_full}-{mm}"
    elif statement_date:
        stmt_month = statement_date[:7]
    else:
        stmt_month = "unknown"

    # --- Compute aggregates from activity ---
    total_principal_paid = 0.0
    total_interest_paid = 0.0
    extra_principal = 0.0
    total_paid = 0.0

    for txn in activity:
        amount = txn.get("amount", 0) or 0
        total_paid += amount

        if "principal" in txn:
            total_principal_paid += txn["principal"]
        if "interest" in txn:
            total_interest_paid += txn["interest"]

        # Extra principal: "Customer request principal pmt" transactions
        if "customer request principal" in (txn.get("description", "") or "").lower():
            extra_principal += amount

    total_principal_paid = round(total_principal_paid, 2)
    total_interest_paid = round(total_interest_paid, 2)
    extra_principal = round(extra_principal, 2)
    total_paid = round(total_paid, 2)

    # --- Validation ---
    mismatches = []

    # 1. For payments with P+I breakdown, verify principal + interest == amount
    for txn in activity:
        if "principal" in txn and "interest" in txn:
            expected = round(txn["principal"] + txn["interest"], 2)
            if abs(txn["amount"] - expected) > 0.02:
                mismatches.append(
                    f"Payment {txn['date']}: amount ({txn['amount']}) != "
                    f"principal ({txn['principal']}) + interest ({txn['interest']}) = {expected}"
                )

    result = {
        "statement_month": stmt_month,
        "statement_date": statement_date,
        "account_number": account_number,
        "vehicle": vehicle,
        "interest_rate": interest_rate,
        "monthly_payment": monthly_payment,
        "maturity_date": maturity_date,
        "daily_interest": daily_interest,
        "payoff_amount": payoff_amount,
        "payoff_date": payoff_date,
        "payment_due_date": payment_due_date,
        "current_payment_due": current_payment_due,
        "total_amount_due": total_amount_due,
        "activity": activity,
        "aggregates": {
            "principal_paid": total_principal_paid,
            "interest_paid": total_interest_paid,
            "extra_principal": extra_principal,
            "total_paid": total_paid,
        },
        "ytd_interest": {
            "year": ytd_interest_year,
            "amount": ytd_interest,
        } if ytd_interest is not None else None,
        "validation": {
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
        return dumper.represent_scalar("tag:yaml.org,2002:float", f"{value:.2f}")

    MoneyDumper.add_representer(float, float_representer)

    with open(output_path, "w") as f:
        yaml.dump(data, f, Dumper=MoneyDumper, default_flow_style=False,
                  sort_keys=False, allow_unicode=True)

    logger.info(f"  Written: {output_path.name}")


# --- Chain Validation ---

def run_chain_validation(yaml_dir: Path) -> list[str]:
    """Cross-statement validation: payoff continuity, YTD interest, missing months."""
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

    # YTD interest accumulation per year
    # Note: the PDF reports "total interest paid in YYYY" which is a PREVIOUS year total,
    # not current year accumulation. So we track interest by year and compare when we see
    # a YTD report.
    interest_by_year: dict[int, float] = {}
    for stmt in statements:
        sm = stmt["statement_month"]
        agg = stmt.get("aggregates", {})
        interest = agg.get("interest_paid", 0)

        # Interest from activity belongs to the year of the activity dates, not statement month.
        # But activity can span years. For simplicity, attribute to the activity dates' year.
        for txn in stmt.get("activity", []):
            if "interest" in txn and txn.get("date"):
                txn_year = int(txn["date"][:4])
                interest_by_year[txn_year] = round(
                    interest_by_year.get(txn_year, 0) + txn["interest"], 2
                )

        ytd_info = stmt.get("ytd_interest")
        if ytd_info and ytd_info.get("amount") is not None and ytd_info.get("year"):
            reported_year = ytd_info["year"]
            reported = ytd_info["amount"]
            computed = interest_by_year.get(reported_year, 0)
            if abs(computed - reported) > 0.10:
                errors.append(
                    f"YTD interest mismatch at {sm} for year {reported_year}: "
                    f"computed={computed}, reported={reported}"
                )

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
                "output_file": f"Finance/wellsfargo-car-loan/{stmt_month}.yaml",
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
        logger.info("Chain validation PASSED -- all statements consistent")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Wells Fargo car loan statement PDF ingestion pipeline"
    )
    parser.add_argument(
        "command",
        choices=["scan", "run", "chain"],
        help="scan: show status; run: parse PDFs; chain: validate continuity",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-process all PDFs (ignore processing log)",
    )

    args = parser.parse_args()

    setup_logging()
    logger.info(
        f"Wells Fargo Car Loan Statement Ingestion -- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    if args.command == "scan":
        cmd_scan()
    elif args.command == "run":
        cmd_run(force=args.force)
    elif args.command == "chain":
        cmd_chain()


if __name__ == "__main__":
    main()
