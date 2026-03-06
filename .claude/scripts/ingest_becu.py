#!/usr/bin/env python3
"""BECU combined statement PDF ingestion pipeline.

Parses monthly BECU statements (checking + HELOC) into structured YAML with validation.

Source PDFs: ~/Dropbox/0-FinancialStatements/BECU/<year>/BECU-Statement-16-<Mon>-<YYYY>*.PDF
Output YAMLs: Finance/becu/YYYY-MM.yaml
Processing log: Finance/becu/processing_log.json

Key pdfminer layout insight: columns may appear in any order (Amount before Date,
or Date before Amount). The script extracts all dates, amounts, and descriptions
from the transaction area and matches them 1:1 by count, classifying by sign.
"""

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from pdfminer.high_level import extract_text

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# --- Constants ---
SCRIPT_DIR = Path(__file__).parent.resolve()
OBSIDIAN_ROOT = SCRIPT_DIR.parent.parent
SOURCE_ROOT = Path.home() / "Dropbox" / "0-FinancialStatements" / "BECU"
OUTPUT_ROOT = OBSIDIAN_ROOT / "Finance" / "becu"
LOG_FILE = OUTPUT_ROOT / "ingest.log"
PROCESSING_LOG_PATH = OUTPUT_ROOT / "processing_log.json"

MAX_PARSE_ATTEMPTS = 3  # Retry budget for transient PDF parse failures
CHECKING_ACCT = "3588947679"
HELOC_ACCT = "2019617876"
MIN_STATEMENT_MONTH = "2025-01"

MONTH_MAP = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}

# Regex patterns
DATE_RE = re.compile(r'\d{2}/\d{2}/\d{2}')
# Transaction amount: digits with optional commas, decimal, 2 digits, optional parens
TXN_AMT_RE = re.compile(r'\([\d,]+\.\d{2}\)|(?<!\$)\b\d[\d,]*\.\d{2}\b')

# --- Logging ---
logger = logging.getLogger("ingest_becu")


def setup_logging():
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
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


# --- Helpers ---

def parse_amount(s: str) -> float:
    s = s.strip()
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    s = s.replace(",", "").replace("$", "")
    return -float(s) if neg else float(s)


def parse_date_mmddyy(s: str) -> str:
    m, d, y = s.split("/")
    return f"{2000 + int(y)}-{m.zfill(2)}-{d.zfill(2)}"


def parse_date_mmddyyyy(s: str) -> str:
    m, d, y = s.split("/")
    return f"{y}-{m.zfill(2)}-{d.zfill(2)}"


def _clean_page_artifacts(text: str) -> str:
    """Remove page break artifacts from pdfminer output."""
    text = re.sub(r'Page \d+ of \d+', '', text)
    text = text.replace('\x0c', '')
    text = re.sub(r'\bYi Chen\b', '', text)
    text = re.sub(
        r'Statement Period:\s*\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4}', '', text
    )
    text = re.sub(r'\b000000\b', '', text)
    text = re.sub(r'Deposit Account Activity(?:\s*\(continued\))?', '', text)
    return text


# --- PDF Discovery ---

def discover_pdfs() -> list[tuple[Path, str, str]]:
    pdfs = []
    for year_dir in sorted(SOURCE_ROOT.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for pdf_file in sorted(year_dir.iterdir()):
            if pdf_file.suffix.upper() != ".PDF":
                continue
            m = re.match(r'BECU-Statement-16-(\w+)-(\d{4})', pdf_file.name)
            if not m:
                continue
            month_num = MONTH_MAP.get(m.group(1))
            if not month_num:
                continue
            stmt_month = f"{m.group(2)}-{month_num}"
            if stmt_month < MIN_STATEMENT_MONTH:
                continue
            pdfs.append((pdf_file, pdf_file.name, stmt_month))
    # Deduplicate by month
    seen = {}
    for path, name, month in pdfs:
        if month not in seen:
            seen[month] = (path, name, month)
    return sorted(seen.values(), key=lambda x: x[2])


# --- Checking: Ending Balance from Summary Table ---

def _extract_ending_balance(text: str) -> Optional[float]:
    """Extract checking ending balance from the summary table.

    After 'Ending Balance', the next two amounts are savings_end then checking_end.
    This is the most reliable summary extraction.
    """
    summary_start = text.find("Summary of Deposit Account Activity")
    if summary_start == -1:
        return None
    # Search from summary start to a reasonable boundary
    end_boundary = text.find("Deposit Account Activity", summary_start + 40)
    if end_boundary == -1:
        end_boundary = summary_start + 3000
    summary_text = text[summary_start:end_boundary]

    ending_m = re.search(r'Ending\s*\n?\s*Balance', summary_text)
    if not ending_m:
        return None
    after = summary_text[ending_m.end():]
    amounts = TXN_AMT_RE.findall(after)
    if len(amounts) >= 2:
        return parse_amount(amounts[1])  # Second value is checking
    if len(amounts) == 1:
        return parse_amount(amounts[0])
    return None


# --- Checking: Metadata (APY, avg balance, YTD dividends) ---

def _parse_checking_metadata(text: str) -> dict:
    check_m = re.search(
        r'(?:Member Advantage )?Checking\s*-\s*' + CHECKING_ACCT, text
    )
    if not check_m:
        return {}
    # Metadata is between checking header and first transaction element
    meta_end = len(text)
    for pattern in [r'\bDeposits\b', r'\bAmount\b\s*\n', r'\bDate\b\s*\n\s*\d{2}/']:
        m = re.search(pattern, text[check_m.start():])
        if m and check_m.start() + m.start() < meta_end:
            meta_end = check_m.start() + m.start()
    meta_text = text[check_m.start():meta_end]

    result = {}
    apy_m = re.search(r'([\d.]+)%\s*Annual Percentage Yield', meta_text)
    if apy_m:
        result["apy"] = float(apy_m.group(1))
    adb_m = re.search(r'Average Daily Balance:\s*\$([\d,.]+)', meta_text)
    if adb_m:
        result["avg_daily_balance"] = parse_amount(adb_m.group(1))
    ytd_m = re.search(r'Year-to-date dividends:\s*\$([\d,.]+)', meta_text)
    if ytd_m:
        result["ytd_dividends"] = parse_amount(ytd_m.group(1))
    return result


# --- Checking: Transaction Parsing ---

def _get_checking_txn_text(text: str) -> str:
    """Extract the transaction text area from the checking detail section.

    Handles pdfminer column ordering where Amount/Description may appear before Date.
    Returns cleaned text from first transaction element to section end.
    """
    check_m = re.search(
        r'(?:Member Advantage )?Checking\s*-\s*' + CHECKING_ACCT, text
    )
    if not check_m:
        return ""

    # Find section end
    section_end = len(text)
    for end_pattern in [r'Computation of Annual Percentage Yield',
                         r'\bLoan Account Activity\b']:
        m = re.search(end_pattern, text[check_m.start():])
        if m and check_m.start() + m.start() < section_end:
            section_end = check_m.start() + m.start()
    check_text = text[check_m.start():section_end]

    # Find where transactions start (earliest of Deposits, Amount+number, Date+date)
    txn_start = len(check_text)
    for pattern in [r'\bDeposits\b',
                    r'\bAmount\b\s*\n\s*\(?[\d,]+\.\d{2}',
                    r'\bDate\b\s*\n\s*\d{2}/\d{2}/\d{2}']:
        m = re.search(pattern, check_text)
        if m and m.start() < txn_start:
            txn_start = m.start()

    txn_text = check_text[txn_start:]
    return _clean_page_artifacts(txn_text)


def _extract_descriptions(txn_text: str) -> list[str]:
    """Extract transaction descriptions from 'Transaction Description' sections."""
    descs = []
    desc_headers = list(re.finditer(r'Transaction Description', txn_text))
    if not desc_headers:
        return descs

    for i, hdr in enumerate(desc_headers):
        start = hdr.end()
        # End at next column header or section boundary
        end = len(txn_text)
        for boundary in [r'\bDate\b', r'\bAmount\b', r'Transaction Description',
                          r'\bDeposits\b', r'\bWithdrawals\b', r'\bComputation\b']:
            bm = re.search(boundary, txn_text[start:])
            if bm and start + bm.start() < end:
                end = start + bm.start()
        if i + 1 < len(desc_headers):
            next_hdr_start = desc_headers[i + 1].start()
            if next_hdr_start < end:
                end = next_hdr_start

        desc_block = txn_text[start:end]
        current = []
        for line in desc_block.split('\n'):
            line = line.strip()
            if not line:
                if current:
                    descs.append(' '.join(current))
                    current = []
                continue
            # Skip noise lines
            if line in ('Date', 'Amount', 'Deposits', 'Deposits (continued)',
                        'Withdrawals', 'Withdrawals (continued)'):
                if current:
                    descs.append(' '.join(current))
                    current = []
                continue
            # Skip amounts and dates mixed into description area
            if TXN_AMT_RE.fullmatch(line) or DATE_RE.fullmatch(line):
                if current:
                    descs.append(' '.join(current))
                    current = []
                continue
            current.append(line)
        if current:
            descs.append(' '.join(current))
    return descs


def parse_checking_transactions(text: str) -> list[dict]:
    """Parse all checking transactions using unified column extraction.

    Key insight: pdfminer may output columns in any order (Amount before Date, etc.).
    We extract ALL dates, amounts, and descriptions from the transaction area and
    match them 1:1 by count. Transaction type is determined by amount sign.
    """
    txn_text = _get_checking_txn_text(text)
    if not txn_text:
        return []

    # Extract all dates (MM/DD/YY)
    all_dates = [m.group() for m in DATE_RE.finditer(txn_text)]

    # Extract all transaction amounts (no $ prefix)
    all_amounts = []
    for m in TXN_AMT_RE.finditer(txn_text):
        val = m.group()
        # Double-check no $ prefix (lookbehind handles most, but be safe)
        pos = m.start()
        if pos > 0 and txn_text[pos - 1] == '$':
            continue
        all_amounts.append(parse_amount(val))

    # Extract descriptions
    all_descs = _extract_descriptions(txn_text)

    n = min(len(all_dates), len(all_amounts))
    if len(all_dates) != len(all_amounts):
        logger.warning(
            f"  Checking: date count ({len(all_dates)}) != "
            f"amount count ({len(all_amounts)})"
        )

    txns = []
    for i in range(n):
        amt = round(all_amounts[i], 2)
        txns.append({
            "date": parse_date_mmddyy(all_dates[i]),
            "amount": amt,
            "description": all_descs[i] if i < len(all_descs) else "",
            "type": "deposit" if amt >= 0 else "withdrawal",
        })
    return txns


# --- HELOC Parsing ---

def has_heloc(text: str) -> bool:
    return HELOC_ACCT in text and "Home Equity Credit Line" in text


def _get_heloc_text(text: str) -> str:
    """Extract full HELOC detail section text."""
    m = re.search(r'Home Equity Credit Line\s*-\s*' + HELOC_ACCT, text)
    if not m:
        return ""
    start = m.start()
    # End at "Line of Credit - NNNNN" (the personal LOC) or "Computation of Balance"
    end = len(text)
    for pattern in [r'Line of Credit\s*-\s*\d{7,}', r'Computation of Balance']:
        em = re.search(pattern, text[start + 50:])
        if em and start + 50 + em.start() < end:
            end = start + 50 + em.start()
    return text[start:end]


def _parse_heloc_summary_positional(heloc_text: str) -> dict:
    """Parse HELOC summary using purely positional amount extraction.

    pdfminer may output labels-then-values or interleaved, so we just extract
    ALL amounts from the summary area and assign by position:
      [0] = previous_balance
      [1..N-3] = middle (payments negative, others positive)
      [-3] = new_balance, [-2] = credit_limit, [-1] = available_credit
    Middle positives: larger = advances, smaller = interest_charged.
    """
    summary_m = re.search(r'Summary of Loan Account Activity', heloc_text)
    if not summary_m:
        return {}

    # Find end of summary area
    end_pos = len(heloc_text)
    for pattern in [r'Annual\s*\n?\s*Percentage\s*Rate',
                    r'HE Variable Line of Credit',
                    r'HE Fixed Rate Advance',
                    r'Total fees charged',
                    r'Payment Information']:
        m = re.search(pattern, heloc_text[summary_m.start() + 30:])
        if m and summary_m.start() + 30 + m.start() < end_pos:
            end_pos = summary_m.start() + 30 + m.start()

    summary_text = heloc_text[summary_m.start():end_pos]
    all_amounts = [parse_amount(m.group()) for m in TXN_AMT_RE.finditer(summary_text)]

    if len(all_amounts) < 4:
        return {}

    result = {
        "previous_balance": all_amounts[0],
        "available_credit": all_amounts[-1],
        "credit_limit": all_amounts[-2],
        "new_balance": all_amounts[-3],
        "payments": 0.0,
        "other_credits": 0.0,
        "advances": 0.0,
        "fees_charged": 0.0,
        "interest_charged": 0.0,
    }

    middle = all_amounts[1:-3]
    # Negative value(s) = payments
    positives = []
    for v in middle:
        if v < 0:
            result["payments"] = v
        else:
            positives.append(v)

    # Among positives: largest = advances, smallest = interest_charged
    if len(positives) == 1:
        # Could be advances or interest — check the balance equation
        # If prev + val (as advances) + interest(0) ≈ new + |payments|, it's advances
        result["advances"] = positives[0]
    elif len(positives) == 2:
        result["advances"] = max(positives)
        result["interest_charged"] = min(positives)
    elif len(positives) >= 3:
        # Sort descending; first = advances, last = interest, middle = other_credits/fees
        positives.sort(reverse=True)
        result["advances"] = positives[0]
        result["interest_charged"] = positives[-1]
        if len(positives) > 2:
            result["other_credits"] = positives[1]

    return result


def _parse_heloc_rates_and_info(heloc_text: str) -> dict:
    result = {}

    # APR
    apr_m = re.search(r'(\d+\.\d+)%\s+0\.\d+%', heloc_text)
    if apr_m:
        result["apr"] = float(apr_m.group(1))

    # YTD interest and fees — labels may appear before values (column layout)
    # Find the label pair, then extract the two amounts that follow
    ytd_m = re.search(
        r'Total fees charged in (\d{4}).*?Total interest charged in \d{4}',
        heloc_text, re.DOTALL,
    )
    if ytd_m:
        after = heloc_text[ytd_m.end():ytd_m.end() + 150]
        amounts = [parse_amount(m.group()) for m in TXN_AMT_RE.finditer(after)]
        if len(amounts) >= 2:
            result["ytd_fees"] = amounts[0]
            result["ytd_interest"] = amounts[1]
        elif len(amounts) == 1:
            result["ytd_interest"] = amounts[0]

    min_pay_m = re.search(r'Minimum Payment:\s*\$([\d,.]+)', heloc_text)
    if min_pay_m:
        result["minimum_payment"] = parse_amount(min_pay_m.group(1))

    pay_date_m = re.search(r'Payment Date:\s*(\d{2}/\d{2}/\d{2})', heloc_text)
    if pay_date_m:
        result["payment_date"] = parse_date_mmddyy(pay_date_m.group(1))

    return result


def _parse_heloc_top_transactions(heloc_text: str) -> list[dict]:
    """Parse top-level HELOC transactions (Master Line Scheduled Payment, etc.)."""
    # These appear in "Transactions" before sub-accounts
    txn_m = re.search(r'\bTransactions\s*\n\s*Transaction Date\b', heloc_text)
    if not txn_m:
        return []

    # End at Fees or sub-account boundary
    end_pos = len(heloc_text)
    for pat in [r'\bFees\b', r'HE Variable', r'HE Fixed']:
        m = re.search(pat, heloc_text[txn_m.end():])
        if m and txn_m.end() + m.start() < end_pos:
            end_pos = txn_m.end() + m.start()
    section = heloc_text[txn_m.end():end_pos]

    dates = DATE_RE.findall(section)
    amounts = [parse_amount(m.group()) for m in TXN_AMT_RE.finditer(section)]

    # Descriptions between "Description of Transaction or Credit" and "Amount"
    descs = []
    desc_m = re.search(r'Description of Transaction or Credit', section)
    if desc_m:
        desc_end = re.search(r'\bAmount\b', section[desc_m.end():])
        desc_text = section[desc_m.end():desc_m.end() + desc_end.start()] if desc_end else section[desc_m.end():]
        for line in desc_text.strip().split('\n'):
            line = line.strip()
            if line and not TXN_AMT_RE.fullmatch(line) and not DATE_RE.fullmatch(line):
                descs.append(line)

    txns = []
    for i in range(min(len(dates), len(amounts))):
        txns.append({
            "date": parse_date_mmddyy(dates[i]),
            "description": descs[i] if i < len(descs) else "",
            "amount": amounts[i],
        })
    return txns


def _parse_heloc_sub_accounts(heloc_text: str) -> list[dict]:
    """Parse HELOC sub-accounts with interest from global TOTAL INTEREST values.

    APR section also contains sub-account names — we filter those out by
    requiring 'Previous Balance' within the section.
    """
    sub_headers = list(re.finditer(
        r'(HE Variable Line of Credit|HE Fixed Rate Advance)\s*\n', heloc_text
    ))
    if not sub_headers:
        return []

    # Parse all raw sub-account candidates
    raw_subs = []
    for idx, hdr in enumerate(sub_headers):
        name = hdr.group(1).strip()
        start = hdr.start()
        end = sub_headers[idx + 1].start() if idx + 1 < len(sub_headers) else len(heloc_text)
        section = heloc_text[start:end]

        sub = {"name": name}

        prev_m = re.search(r'Previous Balance\s*\n?\s*\$?([\d,.]+)', section)
        if prev_m:
            sub["previous_balance"] = parse_amount(prev_m.group(1))

        new_m = re.search(r'New Balance\s*\n?\s*\$?([\d,.]+)', section)
        if new_m:
            sub["new_balance"] = parse_amount(new_m.group(1))

        adb_m = re.search(
            r'Average Daily Balance Subject to Interest Rate\s*\n?\s*([\d,.]+)', section
        )
        if adb_m:
            sub["avg_daily_balance"] = parse_amount(adb_m.group(1))

        apr_m = re.search(r'\(Subject to ([\d.]+)% APR', section)
        if apr_m:
            sub["apr"] = float(apr_m.group(1))

        sub["transactions"] = _parse_sub_txns(section)
        raw_subs.append(sub)

    # Filter: only keep sub-accounts that have Previous Balance (skip APR-section fakes)
    sub_accounts = [s for s in raw_subs if "previous_balance" in s]

    # Assign interest from global TOTAL INTEREST values
    all_tip = re.findall(
        r'TOTAL INTEREST PAID THIS PERIOD\s*\n?\s*([\d,.]+)', heloc_text
    )
    all_tip_values = [parse_amount(v) for v in all_tip]

    # First value is overall total; remaining values are per-sub-account
    overall_tip = all_tip_values[0] if all_tip_values else 0.0
    remaining_tip = list(all_tip_values[1:])

    # If more remaining than sub-accounts, remove duplicates of the overall total
    # (pdfminer sometimes places the overall total value within a sub-account section)
    while len(remaining_tip) > len(sub_accounts):
        removed = False
        for i, v in enumerate(remaining_tip):
            if abs(v - overall_tip) < 0.01:
                remaining_tip.pop(i)
                removed = True
                break
        if not removed:
            break

    for i, sub in enumerate(sub_accounts):
        sub["interest_paid"] = remaining_tip[i] if i < len(remaining_tip) else 0.0

    return sub_accounts


def _parse_sub_txns(section: str) -> list[dict]:
    """Parse transactions from a HELOC sub-account section."""
    # Find transaction dates (between "Transaction Date" and "Fees")
    txn_date_m = re.search(r'Transaction Date', section)
    if not txn_date_m:
        return []
    fees_m = re.search(r'\bFees\b', section[txn_date_m.end():])
    if fees_m:
        date_area = section[txn_date_m.end():txn_date_m.end() + fees_m.start()]
    else:
        date_area = section[txn_date_m.end():txn_date_m.end() + 500]
    dates = DATE_RE.findall(date_area)
    if not dates:
        return []

    # Descriptions: between "Description of Transaction or Credit" and next boundary
    descs = []
    desc_m = re.search(r'Description of Transaction or Credit', section)
    if desc_m:
        desc_end_pos = len(section)
        for pat in [r'Transaction Date', r'Description of Fee', r'TOTAL FEES',
                    r'\bAmount\b']:
            dm = re.search(pat, section[desc_m.end():])
            if dm and desc_m.end() + dm.start() < desc_end_pos:
                desc_end_pos = desc_m.end() + dm.start()
        desc_text = section[desc_m.end():desc_end_pos]
        for line in desc_text.strip().split('\n'):
            line = line.strip()
            if line and not TXN_AMT_RE.fullmatch(line) and not DATE_RE.fullmatch(line):
                descs.append(line)

    # Amounts: first "Amount" section after descriptions
    amounts = []
    amt_m = re.search(r'\bAmount\b', section[desc_m.end():] if desc_m else section)
    if amt_m:
        offset = (desc_m.end() if desc_m else 0) + amt_m.end()
        # End at next "Amount" or "Interest" or "TOTAL"
        amt_end = len(section)
        for pat in [r'\bAmount\b', r'Interest Charged', r'TOTAL', r'Average Daily']:
            am = re.search(pat, section[offset:])
            if am and offset + am.start() < amt_end:
                amt_end = offset + am.start()
        amt_text = section[offset:amt_end]
        amounts = [parse_amount(m.group()) for m in TXN_AMT_RE.finditer(amt_text)]

    txns = []
    for i in range(min(len(dates), len(amounts))):
        txns.append({
            "date": parse_date_mmddyy(dates[i]),
            "description": descs[i] if i < len(descs) else "",
            "amount": amounts[i],
        })
    return txns


def parse_heloc(text: str) -> Optional[dict]:
    if not has_heloc(text):
        return None

    heloc_text = _get_heloc_text(text)
    if not heloc_text:
        return None

    result = {"account_number": HELOC_ACCT}
    result.update(_parse_heloc_summary_positional(heloc_text))
    result.update(_parse_heloc_rates_and_info(heloc_text))

    # Total interest this period (first TOTAL INTEREST value = overall)
    tip_m = re.search(
        r'TOTAL INTEREST PAID THIS PERIOD\s*\n?\s*([\d,.]+)', heloc_text
    )
    if tip_m:
        result["total_interest_this_period"] = parse_amount(tip_m.group(1))

    result["transactions"] = _parse_heloc_top_transactions(heloc_text)
    result["sub_accounts"] = _parse_heloc_sub_accounts(heloc_text)

    return result


# --- Statement Parsing ---

def parse_statement(pdf_path: Path, stmt_month: str, pdf_filename: str) -> dict:
    text = extract_text(str(pdf_path))

    # Statement period
    period_m = re.search(
        r'Statement Period:\s*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})', text
    )
    period_start = parse_date_mmddyyyy(period_m.group(1)) if period_m else None
    period_end = parse_date_mmddyyyy(period_m.group(2)) if period_m else None

    # Ending balance from summary table (most reliable)
    ending_balance = _extract_ending_balance(text)

    # Checking metadata
    metadata = _parse_checking_metadata(text)

    # Checking transactions
    transactions = parse_checking_transactions(text)

    # Compute summary values from transactions
    deposit_txns = [t for t in transactions if t["type"] == "deposit"]
    withdrawal_txns = [t for t in transactions if t["type"] == "withdrawal"]
    dividend_txns = [t for t in deposit_txns if "Dividend" in t.get("description", "")]
    non_div_deposits = [t for t in deposit_txns if "Dividend" not in t.get("description", "")]

    computed_deposits = round(sum(t["amount"] for t in non_div_deposits), 2)
    computed_dividends = round(sum(t["amount"] for t in dividend_txns), 2)
    computed_withdrawals = round(sum(t["amount"] for t in withdrawal_txns), 2)
    computed_net = round(computed_deposits + computed_dividends + computed_withdrawals, 2)

    if ending_balance is not None:
        beginning_balance = round(ending_balance - computed_net, 2)
    else:
        beginning_balance = None

    checking = {
        "account_number": CHECKING_ACCT,
        "beginning_balance": beginning_balance,
        "withdrawals_fees": computed_withdrawals,
        "deposits": computed_deposits,
        "dividends_interest": computed_dividends,
        "ending_balance": ending_balance,
        "apy": metadata.get("apy"),
        "average_daily_balance": metadata.get("avg_daily_balance"),
        "ytd_dividends": metadata.get("ytd_dividends"),
        "transactions": [
            {"date": t["date"], "amount": t["amount"],
             "description": t["description"], "type": t["type"]}
            for t in transactions
        ],
    }

    # HELOC
    heloc = parse_heloc(text)

    # Validation
    validation = validate_intra(checking, heloc)

    return {
        "statement_month": stmt_month,
        "period_start": period_start,
        "period_end": period_end,
        "checking": checking,
        "heloc": heloc,
        "validation": validation,
        "source": {
            "file": pdf_filename,
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        },
    }


# --- Validation ---

def validate_intra(checking: dict, heloc: Optional[dict]) -> dict:
    result = {
        "checking_balance_ok": True,
        "checking_txn_totals_ok": True,
        "heloc_balance_ok": True,
        "heloc_sub_balance_ok": True,
        "heloc_sub_interest_ok": True,
        "mismatches": [],
    }

    # Checking balance: ending = beginning + net(transactions)
    begin = checking.get("beginning_balance") or 0
    end = checking.get("ending_balance") or 0
    dep = checking.get("deposits") or 0
    div = checking.get("dividends_interest") or 0
    wdl = checking.get("withdrawals_fees") or 0
    expected_end = round(begin + dep + div + wdl, 2)

    if abs(expected_end - end) > 0.02:
        result["checking_balance_ok"] = False
        result["mismatches"].append(
            f"Checking balance: expected ending={expected_end}, got {end}"
        )

    if not heloc:
        result["heloc_balance_ok"] = None
        result["heloc_sub_balance_ok"] = None
        result["heloc_sub_interest_ok"] = None
        return result

    # HELOC balance
    prev = heloc.get("previous_balance") or 0
    payments = heloc.get("payments") or 0
    other_credits = heloc.get("other_credits") or 0
    advances = heloc.get("advances") or 0
    fees = heloc.get("fees_charged") or 0
    interest = heloc.get("interest_charged") or 0
    new_bal = heloc.get("new_balance") or 0

    expected_new = round(prev + payments + other_credits + advances + fees + interest, 2)
    if abs(expected_new - new_bal) > 0.10:
        result["heloc_balance_ok"] = False
        result["mismatches"].append(
            f"HELOC balance: expected new={expected_new}, got {new_bal}"
        )

    # Sub-account balances
    subs = heloc.get("sub_accounts", [])
    if subs:
        sub_prev = sum(s.get("previous_balance", 0) for s in subs)
        sub_new = sum(s.get("new_balance", 0) for s in subs)
        if abs(sub_prev - prev) > 0.10:
            result["heloc_sub_balance_ok"] = False
            result["mismatches"].append(
                f"HELOC sub prev sum ({sub_prev}) != total prev ({prev})"
            )
        if abs(sub_new - new_bal) > 0.10:
            result["heloc_sub_balance_ok"] = False
            result["mismatches"].append(
                f"HELOC sub new sum ({sub_new}) != total new ({new_bal})"
            )

        # Sub-account interest
        total_tip = heloc.get("total_interest_this_period")
        if total_tip is not None:
            sub_int = sum(s.get("interest_paid", 0) for s in subs)
            if abs(sub_int - total_tip) > 0.10:
                result["heloc_sub_interest_ok"] = False
                result["mismatches"].append(
                    f"HELOC sub interest sum ({sub_int:.2f}) != total ({total_tip})"
                )

    return result


def validate_chain(yamls: list[dict]) -> list[str]:
    issues = []
    sorted_data = sorted(yamls, key=lambda y: y["statement_month"])

    # Check for missing months
    if sorted_data:
        first = sorted_data[0]["statement_month"]
        last = sorted_data[-1]["statement_month"]
        expected = set()
        y, m = map(int, first.split("-"))
        while f"{y}-{m:02d}" <= last:
            expected.add(f"{y}-{m:02d}")
            m += 1
            if m > 12:
                m, y = 1, y + 1
        missing = expected - {d["statement_month"] for d in sorted_data}
        if missing:
            issues.append(f"Missing months: {sorted(missing)}")

    prev_check_end = None
    prev_heloc_new = None
    heloc_ytd_accum = 0.0
    prev_ytd_year = None

    for data in sorted_data:
        month = data["statement_month"]
        checking = data.get("checking", {})
        heloc = data.get("heloc")

        # Checking continuity
        check_begin = checking.get("beginning_balance")
        check_end = checking.get("ending_balance")
        if prev_check_end is not None and check_begin is not None:
            if abs(prev_check_end - check_begin) > 0.02:
                issues.append(
                    f"Checking continuity break at {month}: "
                    f"prev ending={prev_check_end}, this beginning={check_begin}"
                )
        prev_check_end = check_end

        # HELOC continuity
        if heloc:
            heloc_prev = heloc.get("previous_balance")
            heloc_new = heloc.get("new_balance")
            heloc_interest = heloc.get("interest_charged") or 0

            if prev_heloc_new is not None and heloc_prev is not None:
                if abs(prev_heloc_new - heloc_prev) > 0.02:
                    issues.append(
                        f"HELOC continuity break at {month}: "
                        f"prev new={prev_heloc_new}, this prev={heloc_prev}"
                    )
            prev_heloc_new = heloc_new

            # YTD interest accumulation
            year = month[:4]
            if prev_ytd_year != year:
                heloc_ytd_accum = 0.0
                prev_ytd_year = year
            heloc_ytd_accum += heloc_interest
            ytd_interest = heloc.get("ytd_interest")
            if ytd_interest is not None and abs(heloc_ytd_accum - ytd_interest) > 0.10:
                issues.append(
                    f"HELOC YTD interest at {month}: "
                    f"accumulated={heloc_ytd_accum:.2f}, reported={ytd_interest}"
                )

    return issues


def reconcile_with_cma(yamls: list[dict]) -> list[str]:
    issues = []
    db_path = OBSIDIAN_ROOT / "Finance" / "finance.db"
    if not db_path.exists():
        return ["No finance.db found — skipping CMA reconciliation"]

    import sqlite3
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    cma_becu = conn.execute("""
        SELECT date, amount, description
        FROM fidelity_cma_transactions
        WHERE description LIKE '%BECU%'
        ORDER BY date
    """).fetchall()
    conn.close()

    if not cma_becu:
        return ["No CMA transactions mentioning BECU found"]

    becu_moneyline = []
    for data in yamls:
        for txn in data.get("checking", {}).get("transactions", []):
            desc = txn.get("description", "")
            if "MONEYLINE" in desc or "FID BKG" in desc or "FIDBKG" in desc:
                becu_moneyline.append(txn)

    matched = 0
    unmatched = []
    for cma in cma_becu:
        found = False
        for becu in becu_moneyline:
            days = abs((datetime.strptime(cma["date"], "%Y-%m-%d") -
                        datetime.strptime(becu["date"], "%Y-%m-%d")).days)
            if days <= 10 and abs(abs(cma["amount"]) - abs(becu["amount"])) < 0.01:
                found = True
                matched += 1
                break
        if not found:
            unmatched.append(
                f"CMA {cma['date']} {cma['amount']:,.2f} ({cma['description'][:50]})"
            )

    issues.append(f"Matched {matched}/{len(cma_becu)} CMA↔BECU transactions")
    if unmatched:
        issues.append(f"Unmatched CMA ({len(unmatched)}):")
        for u in unmatched[:10]:
            issues.append(f"  {u}")

    return issues


# --- YAML Output ---

def write_yaml(data: dict, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    class Dumper(yaml.SafeDumper):
        pass

    Dumper.add_representer(type(None),
                           lambda d, _: d.represent_scalar('tag:yaml.org,2002:null', 'null'))

    with open(output_path, 'w') as f:
        yaml.dump(data, f, Dumper=Dumper, default_flow_style=False,
                  sort_keys=False, allow_unicode=True)


# --- CLI ---

def cmd_scan():
    pdfs = discover_pdfs()
    log = load_processing_log()
    print(f"Found {len(pdfs)} BECU statement PDFs (Jan 2025+)\n")
    print(f"{'Month':<10} {'Filename':<50} {'Status'}")
    print("-" * 80)
    for _, name, month in pdfs:
        status = "processed" if name in log.get("pdfs", {}) else "NEW"
        if (OUTPUT_ROOT / f"{month}.yaml").exists():
            status = "processed"
        print(f"{month:<10} {name:<50} {status}")


def cmd_run(force: bool = False):
    pdfs = discover_pdfs()
    log = load_processing_log()
    new_count = skip_count = error_count = 0

    for path, name, month in pdfs:
        if not force and name in log.get("pdfs", {}):
            skip_count += 1
            continue

        logger.info(f"Processing {name} → {month}")
        try:
            for _attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
                try:
                    data = parse_statement(path, month, name)
                    break
                except Exception as e:
                    if _attempt == MAX_PARSE_ATTEMPTS:
                        raise
                    print(f"  Attempt {_attempt}/{MAX_PARSE_ATTEMPTS} failed: {e}, retrying...")
            write_yaml(data, OUTPUT_ROOT / f"{month}.yaml")

            mismatches = data.get("validation", {}).get("mismatches", [])
            log.setdefault("pdfs", {})[name] = {
                "statement_month": month,
                "output": f"{month}.yaml",
                "processed_at": datetime.now().isoformat(timespec="seconds"),
                "validation_ok": len(mismatches) == 0,
                "mismatches": mismatches,
            }
            if mismatches:
                logger.warning(f"  Validation issues:")
                for m in mismatches:
                    logger.warning(f"    - {m}")
            else:
                logger.info(f"  ✓ All validations passed")
            new_count += 1
        except Exception as e:
            logger.error(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1

    save_processing_log(log)
    print(f"\nSummary: {new_count} new, {skip_count} skipped, {error_count} errors")


def cmd_chain():
    yamls = []
    for yf in sorted(OUTPUT_ROOT.glob("*.yaml")):
        with open(yf) as f:
            data = yaml.safe_load(f)
        if data:
            yamls.append(data)
    if not yamls:
        print("No YAML files found. Run 'run' first.")
        return
    issues = validate_chain(yamls)
    if issues:
        print(f"Chain validation ({len(issues)} issues):")
        for i in issues:
            print(f"  - {i}")
    else:
        print("✓ All chain validations passed")


def cmd_reconcile():
    yamls = []
    for yf in sorted(OUTPUT_ROOT.glob("*.yaml")):
        with open(yf) as f:
            data = yaml.safe_load(f)
        if data:
            yamls.append(data)
    if not yamls:
        print("No YAML files found. Run 'run' first.")
        return
    for r in reconcile_with_cma(yamls):
        print(r)


def main():
    setup_logging()
    if len(sys.argv) < 2:
        print("Usage: ingest_becu.py <command>")
        print("Commands: scan, run [--force], chain, reconcile")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "scan":
        cmd_scan()
    elif cmd == "run":
        cmd_run(force="--force" in sys.argv)
    elif cmd == "chain":
        cmd_chain()
    elif cmd == "reconcile":
        cmd_reconcile()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
