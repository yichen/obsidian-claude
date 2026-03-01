#!/usr/bin/env python3
"""Fidelity combined account statement PDF ingestion pipeline.

Parses monthly Fidelity investment report PDFs covering multiple accounts
(brokerage, IRA, 401k, UTMA, HSA, CMA) and outputs structured YAML with
per-account summaries, income breakdowns, and holdings snapshots.

Source: ~/Dropbox/0-FinancialStatements/fidelity-accounts/<year>/
Output: Finance/fidelity-accounts/YYYY-MM-DD.yaml
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
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
SOURCE_ROOT = Path.home() / "Dropbox" / "0-FinancialStatements" / "fidelity-accounts"
OUTPUT_ROOT = OBSIDIAN_ROOT / "Finance" / "fidelity-accounts"
LOG_FILE = OUTPUT_ROOT / "ingest.log"
PROCESSING_LOG_PATH = OUTPUT_ROOT / "processing_log.json"

# --- Regex patterns ---
MONTHLY_RE = re.compile(r"^Statement(\d{1,2})(\d{2})(\d{4})\.pdf$")
YEAR_END_RE = re.compile(r"^year-end-report-yi-chen\.pdf$")
ACCOUNT_HEADER_RE = re.compile(r"Account\s+#\s+([A-Z0-9]{3}-\d{6})")
MONEY_RE = re.compile(r"-?\$?[\d,]+\.\d{2}")
DATE_RANGE_RE = re.compile(
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},\s+\d{4}\s*-\s*"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},\s+\d{4}"
)
TICKER_RE = re.compile(r"\(([A-Z]{1,5})\)")

# --- Account type mapping ---
ACCOUNT_TYPE_MAP = {
    "INDIVIDUAL TOD": ("individual_brokerage", "taxable"),
    "INDIVIDUAL - TOD": ("individual_brokerage", "taxable"),
    "CASH MANAGEMENT": ("cash_management", "taxable"),
    "TRADITIONAL IRA": ("traditional_ira", "tax_deferred"),
    "ROTH IRA": ("roth_ira", "tax_free"),
    "ROTH INDIVIDUAL": ("roth_ira", "tax_free"),
    "SELF-EMPLOYED 401K": ("self_employed_401k", "tax_deferred"),
    "HEALTH SAVINGS": ("hsa", "tax_free"),
    "UTMA": ("utma", "taxable"),
}

# Known accounts for beneficiary lookup
KNOWN_ACCOUNTS = {
    "X86-610887": ("individual_brokerage", "taxable", "Yi"),
    "Z26-474983": ("cash_management", "taxable", "Yi"),
    "Z31-859340": ("individual_brokerage", "taxable", "Yi"),
    "249-729024": ("traditional_ira", "tax_deferred", "Yi"),
    "249-733354": ("roth_ira", "tax_free", "Yi"),
    "413-189729": ("self_employed_401k", "tax_deferred", "Yi"),
    "Z06-592753": ("utma", "taxable", "Ruby"),
    "Z08-759437": ("utma", "taxable", "Laurence"),
    "231-574209": ("hsa", "tax_free", "Yi"),
}

# --- Logging ---
logger = logging.getLogger("ingest_fidelity")


def setup_logging():
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(ch)
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    logger.addHandler(fh)


# --- Helper functions ---


def parse_money(val: str) -> Optional[float]:
    """Parse a money string like '$1,234.56' or '-$31,198.64' to float."""
    if not val or not isinstance(val, str):
        return None
    val = val.strip()
    if val in ("-", "$-", "", "--", "not applicable"):
        return None
    # Handle negative formats: -$1,234.56 or ($1,234.56) or −$1,234.56
    val = val.replace("−", "-").replace("(", "-").replace(")", "")
    val = val.replace("$", "").replace(",", "").strip()
    if not val or val == "-":
        return None
    try:
        return float(val)
    except ValueError:
        return None


def extract_money_after(text: str, label: str, line_scope: bool = True) -> Optional[float]:
    """Find a label in text and extract the first money value after it.

    Handles two-column layouts (This Period / Year-to-Date) where a standalone
    '-' means zero in the first column. When there are 2+ money values, returns
    the first. When there's only 1 money value preceded by a standalone dash,
    the first column is zero.
    """
    idx = text.find(label)
    if idx < 0:
        return None
    after = text[idx + len(label):]
    if line_scope:
        nl = after.find("\n")
        if nl >= 0:
            after = after[:nl]

    money_matches = list(MONEY_RE.finditer(after))
    if not money_matches:
        return None

    if len(money_matches) >= 2:
        # Two values: first is This Period
        return parse_money(money_matches[0].group())

    # Only one money value — check if preceded by standalone dash (meaning This Period = 0)
    first_match = money_matches[0]
    before_text = after[:first_match.start()].strip()
    # Standalone dash: just "-" or "- " but NOT part of a negative number
    if before_text == "-":
        return 0.0

    return parse_money(first_match.group())


def extract_all_money(text: str) -> list:
    """Extract all money values from text."""
    return [parse_money(m.group()) for m in MONEY_RE.finditer(text)]


def _extract_this_period_value(line: str) -> Optional[float]:
    """Extract the 'This Period' value from a two-column line.

    Handles the case where This Period is '-' (zero) and only the YTD value
    has a dollar amount. Returns None if no money value found at all.
    """
    money_matches = list(MONEY_RE.finditer(line))
    if not money_matches:
        return None

    if len(money_matches) >= 2:
        # Two values: first is This Period
        return parse_money(money_matches[0].group())

    # One value — check for preceding standalone dash
    first_match = money_matches[0]
    # Find the label part (e.g., "Taxable", "Dividends") and text after it
    # Look at text between any label keyword and the money value
    before_text = line[:first_match.start()].strip()
    # Check if the text ends with a standalone dash (after removing label words)
    # E.g., "Tax-deferred - $1.46" → before "1.46" is "Tax-deferred -"
    # E.g., "Taxable $44.96" → before is "Taxable"
    if before_text.endswith(" -") or before_text.endswith("\t-"):
        return 0.0

    return parse_money(first_match.group())


def close_enough(a: Optional[float], b: Optional[float], tol: float = 0.02) -> bool:
    """Check if two values are close enough (both None counts as close)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(a - b) <= tol


# --- PDF Discovery ---


@dataclass
class PDFInfo:
    path: Path
    statement_date: date
    is_year_end: bool = False

    @property
    def key(self) -> str:
        return self.path.name


def discover_pdfs(year: Optional[int] = None) -> list:
    """Find all Fidelity statement PDFs."""
    results = []
    if not SOURCE_ROOT.exists():
        logger.warning(f"Source directory not found: {SOURCE_ROOT}")
        return results

    year_dirs = []
    if year:
        d = SOURCE_ROOT / str(year)
        if d.exists():
            year_dirs.append(d)
    else:
        for d in sorted(SOURCE_ROOT.iterdir()):
            if d.is_dir() and d.name.isdigit():
                year_dirs.append(d)

    for year_dir in year_dirs:
        for pdf_path in sorted(year_dir.iterdir()):
            if not pdf_path.suffix.lower() == ".pdf":
                continue

            m = MONTHLY_RE.match(pdf_path.name)
            if m:
                month, day, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
                stmt_date = date(yr, month, day)
                results.append(PDFInfo(path=pdf_path, statement_date=stmt_date))
                continue

            if YEAR_END_RE.match(pdf_path.name):
                yr = int(year_dir.name)
                stmt_date = date(yr, 12, 31)
                results.append(PDFInfo(path=pdf_path, statement_date=stmt_date, is_year_end=True))

    return results


def load_processing_log() -> dict:
    """Load the processing log tracking which PDFs have been processed."""
    if PROCESSING_LOG_PATH.exists():
        with open(PROCESSING_LOG_PATH) as f:
            return json.load(f)
    return {}


def save_processing_log(log: dict):
    """Save the processing log."""
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    with open(PROCESSING_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2, default=str)


def get_new_pdfs(pdfs: list, force: bool = False) -> list:
    """Filter to only unprocessed PDFs."""
    if force:
        return pdfs
    log = load_processing_log()
    return [p for p in pdfs if p.key not in log]


# --- Portfolio Summary Parser ---


def parse_portfolio_summary(pages_text: list) -> dict:
    """Parse portfolio-level summary from first page."""
    text = pages_text[0] if pages_text else ""

    result = {}
    # Try "This Period" column values (left column of the two-column layout)
    result["beginning_value"] = extract_money_after(text, "Beginning Portfolio Value")
    result["ending_value"] = extract_money_after(text, "Ending Portfolio Value")

    # For additions/subtractions/change, look for the line and get first money value
    result["additions"] = extract_money_after(text, "Additions")
    result["subtractions"] = extract_money_after(text, "Subtractions")
    result["change_in_investment_value"] = extract_money_after(text, "Change in Investment Value")

    # Year-end reports have extra fields
    result["transaction_costs"] = extract_money_after(text, "Transaction Costs, Fees & Charges")
    result["transfers_between_fidelity"] = extract_money_after(text, "Transfers Between Fidelity Accounts")

    return result


# --- Income Summary Parser ---


def parse_income_summary(pages_text: list) -> dict:
    """Parse portfolio-level income summary (usually page 4)."""
    result = {
        "taxable": {"total": None, "dividends": None, "interest": None},
        "tax_deferred": {"total": None},
        "tax_free": {"total": None},
        "grand_total": None,
    }

    # Scan pages 2-5 for "Income Summary"
    for page_text in pages_text[1:6]:
        if "Income Summary" not in page_text:
            continue
        lines = page_text.split("\n")
        in_income = False
        for i, line in enumerate(lines):
            if "Income Summary" in line:
                in_income = True
                continue
            if not in_income:
                continue
            if "Top Holdings" in line or "Asset Allocation" in line:
                break

            stripped = line.strip()
            first_val = _extract_this_period_value(stripped)
            if first_val is None:
                continue

            if stripped.startswith("Taxable") and "Total" not in stripped:
                result["taxable"]["total"] = first_val
            elif stripped.startswith("Dividends"):
                result["taxable"]["dividends"] = first_val
            elif stripped.startswith("Interest") and "Accrued" not in stripped:
                result["taxable"]["interest"] = first_val
            elif stripped.startswith("Tax-deferred"):
                result["tax_deferred"]["total"] = first_val
            elif stripped.startswith("Tax-free"):
                result["tax_free"]["total"] = first_val
            elif stripped.startswith("Total"):
                result["grand_total"] = first_val
                break

        if result["grand_total"] is not None:
            break

    return result


# --- Account Discovery ---


def discover_accounts_from_table(pages_text: list) -> list:
    """Parse the accounts table from page 2 to get account listing."""
    accounts = []
    # Scan pages 1-3 for the accounts table
    for page_text in pages_text[1:4]:
        # Look for account number patterns with preceding account name text
        for m in ACCOUNT_HEADER_RE.finditer(page_text):
            acct_num = m.group(1)
            if acct_num not in [a["account_number"] for a in accounts]:
                accounts.append({"account_number": acct_num})

    return accounts


def discover_accounts_from_headers(pages_text: list) -> list:
    """Fallback: scan all pages for Account # headers."""
    seen = set()
    accounts = []
    for page_text in pages_text:
        for m in ACCOUNT_HEADER_RE.finditer(page_text):
            acct_num = m.group(1)
            if acct_num not in seen:
                seen.add(acct_num)
                accounts.append({"account_number": acct_num})
    return accounts


# --- Per-Account Section Splitter ---


def split_by_account(pages_text: list) -> dict:
    """Split page texts into per-account sections.

    Returns dict of {account_number: [page_text, ...]} where each page_text
    is the portion of a page belonging to that account.
    """
    # Build a mapping: (page_idx, char_offset) -> account_number
    # Then for each page, split text at account boundaries
    sections = {}
    current_account = None

    for page_idx, page_text in enumerate(pages_text):
        # Find all Account # markers on this page
        markers = list(ACCOUNT_HEADER_RE.finditer(page_text))

        if not markers and current_account:
            # Entire page belongs to current account (unless it's an early page)
            if page_idx >= 4:  # Account sections start around page 5
                sections.setdefault(current_account, []).append(page_text)
            continue

        if not markers:
            continue

        prev_end = 0
        for i, marker in enumerate(markers):
            acct_num = marker.group(1)

            # If there's text before first marker on this page, it belongs to previous account
            if i == 0 and prev_end == 0 and current_account and page_idx >= 4:
                prefix = page_text[:marker.start()]
                if prefix.strip():
                    sections.setdefault(current_account, []).append(prefix)

            current_account = acct_num

            # Text from this marker to next marker (or end of page)
            if i + 1 < len(markers):
                section_text = page_text[marker.start():markers[i + 1].start()]
            else:
                section_text = page_text[marker.start():]

            sections.setdefault(acct_num, []).append(section_text)

    return sections


# --- Account Name/Type Parser ---


def classify_account(account_number: str, section_texts: list) -> dict:
    """Determine account type, tax status, and beneficiary from section text."""
    # Check known accounts first
    if account_number in KNOWN_ACCOUNTS:
        acct_type, tax_status, beneficiary = KNOWN_ACCOUNTS[account_number]
        # Still try to get account name from text
        account_name = _extract_account_name(section_texts)
        return {
            "account_name": account_name or account_number,
            "account_type": acct_type,
            "tax_status": tax_status,
            "beneficiary": beneficiary,
        }

    # Parse from text
    account_name = _extract_account_name(section_texts)
    name_upper = (account_name or "").upper()

    acct_type = "unknown"
    tax_status = "taxable"
    for pattern, (atype, tstatus) in ACCOUNT_TYPE_MAP.items():
        if pattern in name_upper:
            acct_type = atype
            tax_status = tstatus
            break

    # Beneficiary from name
    beneficiary = "Yi"
    if "RUBY" in name_upper:
        beneficiary = "Ruby"
    elif "LAURENCE" in name_upper:
        beneficiary = "Laurence"

    return {
        "account_name": account_name or account_number,
        "account_type": acct_type,
        "tax_status": tax_status,
        "beneficiary": beneficiary,
    }


def _extract_account_name(section_texts: list) -> str:
    """Extract account name from section text (appears after Account Summary or Holdings header)."""
    for text in section_texts:
        # Look for "Account Summary" line, then the name on next line(s)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if "Account Summary" in stripped or "Holdings" in stripped:
                # Name is usually on the next line
                if i + 1 < len(lines):
                    name = lines[i + 1].strip()
                    # Filter out noise lines
                    if name and not name.startswith("Account") and not name.startswith("$"):
                        return name
    return ""


# --- Account Summary Parser ---


def parse_account_summary(section_texts: list) -> dict:
    """Parse account summary (beginning/ending value, additions, subtractions, etc.)."""
    combined = "\n".join(section_texts)
    result = {
        "beginning_value": None,
        "ending_value": None,
        "additions": None,
        "subtractions": None,
        "change_in_investment_value": None,
        "deposits": None,
        "withdrawals": None,
        "exchanges_in": None,
        "exchanges_out": None,
        "transfers_between_fidelity": None,
        "cards_checking_bill_payments": None,
        "transaction_costs": None,
    }

    # Find the "Account Summary" section
    for text in section_texts:
        if "Account Summary" not in text and "Beginning Account Value" not in text:
            continue

        result["beginning_value"] = extract_money_after(text, "Beginning Account Value")
        result["ending_value"] = extract_money_after(text, "Ending Account Value")
        result["additions"] = extract_money_after(text, "Additions")
        result["subtractions"] = extract_money_after(text, "Subtractions")
        result["change_in_investment_value"] = extract_money_after(text, "Change in Investment Value")
        result["deposits"] = extract_money_after(text, "Deposits")
        result["withdrawals"] = extract_money_after(text, "Withdrawals")
        result["exchanges_in"] = extract_money_after(text, "Exchanges In")
        result["exchanges_out"] = extract_money_after(text, "Exchanges Out")
        result["transfers_between_fidelity"] = extract_money_after(text, "Transfers Between Fidelity")
        result["cards_checking_bill_payments"] = extract_money_after(text, "Cards, Checking & Bill Payments")
        result["transaction_costs"] = extract_money_after(text, "Transaction Costs, Fees & Charges")

        if result["beginning_value"] is not None:
            break

    return result


# --- Account Income Parser ---


def parse_account_income(section_texts: list) -> dict:
    """Parse per-account income summary."""
    result = {
        "dividends": None,
        "interest": None,
        "total": None,
    }

    for text in section_texts:
        if "Income Summary" not in text:
            continue

        # Find Income Summary section
        lines = text.split("\n")
        in_income = False
        for line in lines:
            stripped = line.strip()
            if "Income Summary" in stripped:
                in_income = True
                continue
            if not in_income:
                continue
            # Stop at next section — use line-start checks to avoid matching
            # mid-sentence occurrences like "from Other Activity In or Out"
            if any(stripped.startswith(kw) for kw in [
                "Core Account", "Estimated Cash Flow",
            ]):
                break
            # "Holdings" and "Activity" as standalone section headers
            if stripped in ("Holdings", "Activity"):
                break

            first_val = _extract_this_period_value(stripped)
            if first_val is None:
                continue

            if stripped.startswith("Dividends"):
                result["dividends"] = first_val
            elif stripped.startswith("Interest") and "Accrued" not in stripped:
                result["interest"] = first_val
            elif stripped.startswith("Total"):
                result["total"] = first_val
                break

        if result["total"] is not None:
            break

    return result


# --- Holdings Parser ---


@dataclass
class Holding:
    symbol: Optional[str] = None
    description: str = ""
    asset_class: str = ""
    quantity: Optional[float] = None
    price: Optional[float] = None
    market_value: Optional[float] = None
    cost_basis: Optional[float] = None
    unrealized_gain_loss: Optional[float] = None


def parse_holdings(section_texts: list) -> list:
    """Parse holdings from account section.

    Handles multi-line descriptions where the ticker appears on the line AFTER
    the money values. E.g.:
        META PLATFORMS INC CLASS A 87,826.50 150.000 689.1800 103,377.00 ...
        COMMON STOCK (META) 0.290
    """
    holdings = []
    for text in section_texts:
        # Only parse actual Holdings pages (have column headers), not Account Summary
        # pages that incidentally contain "Account Holdings" in pie chart labels
        # or "Core Account" in pie chart text like "100% Core Account ($20,258)"
        if "Holdings" not in text:
            continue
        # Require column headers that appear on actual holdings data pages
        has_column_header = ("Market Value" in text and "Quantity" in text
                            and "Per Unit" in text)
        if not has_column_header:
            continue
        holdings.extend(_parse_holdings_page(text))
    return holdings


def _parse_holdings_page(text: str) -> list:
    """Parse holdings from a single page of holdings text."""
    holdings = []
    lines = text.split("\n")
    current_asset_class = ""
    used_lines = set()  # Track which lines we've consumed

    # First pass: detect asset class zones and find all ticker lines
    asset_class_zones = []  # (line_idx, asset_class)
    ticker_lines = []  # (line_idx, ticker)

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect asset class headers
        if "Total" not in stripped:
            if "Core Account" in stripped:
                asset_class_zones.append((i, "core"))
            elif "Mutual Funds" in stripped:
                asset_class_zones.append((i, "mutual_fund"))
            elif "Exchange Traded Products" in stripped:
                asset_class_zones.append((i, "etp"))
            elif stripped == "Stocks" or (stripped.startswith("Stocks") and "Total" not in stripped):
                asset_class_zones.append((i, "stock"))
            elif "Stock Funds" in stripped:
                asset_class_zones.append((i, "mutual_fund"))
            elif "Equity ETPs" in stripped:
                asset_class_zones.append((i, "etp"))
            elif "Common Stock" == stripped:
                asset_class_zones.append((i, "stock"))

        # Find all ticker references
        m = TICKER_RE.search(stripped)
        if m:
            ticker_lines.append((i, m.group(1)))

    def get_asset_class(line_idx: int) -> str:
        """Get asset class for a given line based on zone headers."""
        cls = ""
        for zi, zc in asset_class_zones:
            if zi <= line_idx:
                cls = zc
        return cls

    # Second pass: for each ticker, find its data line (same line or previous line)
    for tick_idx, ticker in ticker_lines:
        tick_line = lines[tick_idx].strip()

        # Skip "Total" lines and header lines
        if tick_line.startswith("Total") or "Beginning" in tick_line:
            continue

        asset_class = get_asset_class(tick_idx)

        # Count money values on the ticker line
        tick_money = MONEY_RE.findall(tick_line)

        # Check if this is a continuation line (few/no money values, ticker only)
        # vs a self-contained line (ticker + money values together)
        if len(tick_money) >= 4:
            # Self-contained: ticker and data on same line
            data_line = tick_line
            data_idx = tick_idx
        elif tick_idx > 0:
            # Check previous line for money values
            prev_line = lines[tick_idx - 1].strip()
            prev_money = MONEY_RE.findall(prev_line)
            if len(prev_money) >= 3 and prev_line not in ("", ) and "Total" not in prev_line:
                # Data is on previous line, ticker is continuation
                data_line = prev_line
                data_idx = tick_idx - 1
            else:
                data_line = tick_line
                data_idx = tick_idx
        else:
            data_line = tick_line
            data_idx = tick_idx

        if data_idx in used_lines:
            continue
        used_lines.add(data_idx)
        used_lines.add(tick_idx)

        holding = _extract_holding_values(data_line, ticker, asset_class)
        if holding and holding.market_value is not None:
            holdings.append(holding)

    # Third pass: find core positions that may not have tickers
    # Core positions like "CASH $328,738.20 329,566.350 $1.0000 $329,566.35"
    # Must be in an actual core asset class zone (after "Core Account" header)
    in_core_zone = False
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track when we enter/exit core zone
        if "Core Account" in stripped and "Total" not in stripped:
            in_core_zone = True
            continue
        if in_core_zone and stripped.startswith("Total Core Account"):
            in_core_zone = False
            continue
        # Exit core zone if we hit a different asset class
        if in_core_zone and any(kw in stripped for kw in [
            "Mutual Funds", "Exchange Traded Products", "Stocks",
            "Stock Funds", "Equity ETPs", "Total Holdings",
        ]):
            in_core_zone = False

        if not in_core_zone:
            continue
        if i in used_lines:
            continue

        # Core lines start with description and have money values
        money_vals = MONEY_RE.findall(stripped)
        if len(money_vals) < 2:
            continue

        # Skip header/total lines
        if any(kw in stripped for kw in [
            "Beginning", "Total", "Description", "holdings)", "7-day yield",
            "EAI", "account holdings", "Market Value", "Per Unit",
            "Interest rate:", "For balances below",
        ]):
            continue

        # Check if next line has a ticker (wrapped core like SPAXX, FDRXX)
        ticker = None
        if i + 1 < len(lines):
            next_m = TICKER_RE.search(lines[i + 1].strip())
            if next_m and i + 1 not in used_lines:
                ticker = next_m.group(1)
                used_lines.add(i + 1)

        used_lines.add(i)
        holding = _extract_holding_values(stripped, ticker, "core")
        if holding and holding.market_value is not None:
            holdings.append(holding)

    return holdings


def _extract_holding_values(data_line: str, ticker: Optional[str],
                            asset_class: str) -> Optional[Holding]:
    """Extract holding values from a data line."""
    holding = Holding(symbol=ticker, asset_class=asset_class)

    # Extract all money values from the data line
    money_vals = MONEY_RE.findall(data_line)
    nums = []
    for v in money_vals:
        parsed = parse_money(v)
        if parsed is not None:
            nums.append(parsed)

    if not nums:
        return None

    # Clean description: text before the first $ sign
    dollar_idx = data_line.find("$")
    if dollar_idx > 0:
        desc = data_line[:dollar_idx].strip()
    else:
        # No $ — take text before first number
        first_num = MONEY_RE.search(data_line)
        desc = data_line[:first_num.start()].strip() if first_num else data_line
    # Remove ticker from description
    if ticker:
        desc = re.sub(rf"\({ticker}\)", "", desc).strip()
    # Clean trailing punctuation
    desc = desc.strip(" -,")
    holding.description = desc

    # Check if beginning value is "unavailable" (new holdings without prior value)
    has_unavailable = "unavailable" in data_line.lower()

    if has_unavailable:
        # For unavailable lines, re-extract money values with strict boundary check
        # to avoid partial matches of quantity (570.451→570.45) and price (19.2500→19.25)
        clean_nums = []
        for m in MONEY_RE.finditer(data_line):
            end_pos = m.end()
            if end_pos < len(data_line) and data_line[end_pos].isdigit():
                continue  # Skip partial matches
            parsed = parse_money(m.group())
            if parsed is not None:
                clean_nums.append(parsed)
        nums = clean_nums

    if asset_class == "core":
        # Core: beginning_value, quantity, price(1.0), ending_value [, EAI]
        # "not applicable" replaces cost_basis/unrealized
        if has_unavailable:
            # No beginning value: nums are [ending_value, EAI] or [ending_value]
            if nums:
                holding.market_value = nums[0]
                holding.price = 1.0
        elif len(nums) >= 4:
            holding.quantity = nums[1]
            holding.price = nums[2]
            holding.market_value = nums[3]
        elif len(nums) >= 2:
            holding.market_value = nums[-1] if len(nums) <= 3 else nums[3]
            holding.price = 1.0
    else:
        # Non-core: beginning, quantity, price, ending, cost_basis, unrealized [, EAI [, EY]]
        if has_unavailable:
            # No beginning: nums are [market_value, cost_basis, unrealized, EAI, ...]
            if len(nums) >= 3:
                holding.market_value = nums[0]
                holding.cost_basis = nums[1]
                holding.unrealized_gain_loss = nums[2]
            elif len(nums) >= 1:
                holding.market_value = nums[0]
        elif len(nums) >= 6:
            holding.quantity = nums[1]
            holding.price = nums[2]
            holding.market_value = nums[3]
            holding.cost_basis = nums[4]
            holding.unrealized_gain_loss = nums[5]
        elif len(nums) >= 4:
            holding.quantity = nums[1]
            holding.price = nums[2]
            holding.market_value = nums[3]
        elif len(nums) >= 2:
            holding.market_value = nums[-1]

    return holding


# --- CMA Activity Parser ---

# CMA account number
CMA_ACCOUNT = "Z26-474983"

# Regex for activity line: starts with MM/DD
ACTIVITY_DATE_RE = re.compile(r"^(\d{2}/\d{2})\s+")
# Regex for money amount at end of line (with optional leading -)
ACTIVITY_AMOUNT_RE = re.compile(r"-?\$?[\d,]+\.\d{2}$")
# Regex for Checking Activity line: check# date code description amount
CHECK_LINE_RE = re.compile(r"^(\d+)\s+(\d{2}/\d{2})\s+(.+?)\s+(-?\$?[\d,]+\.\d{2})$")

# Categorization rules for CMA transactions
# Priority 1: Sheri Martin payments via Capital One ******0615
# Priority 2: OFW (OurFamilyWizard)
# Priority 3: Other outflow rules
# Priority 4: Inflow rules

CMA_OUTFLOW_RULES = [
    # CC Payments
    (r"APPLECARD", "CC Payment: Apple Card", True),
    (r"CHASE CREDIT|CHASE.*AUTOPAY|CHASE.*EPAY|RETRY PYMT.*CHASE", "CC Payment: Chase", True),
    (r"CARDMEMBER SER", "CC Payment: Fidelity", True),
    (r"BK OF AMER VIS", "CC Payment: BofA", True),
    # Mortgage
    (r"NSM DBAMR", "Mortgage", False),
    (r"FLAGSTAR BANK", "Mortgage (HELOC)", False),
    # Housing
    (r"SAMMAMISH FORE", "HOA", False),
    # Insurance
    (r"PRUDENTIAL", "Life Insurance", False),
    (r"ALLSTATE.*INS|ALLSTATE.*PREM", "Auto/Home Insurance", False),
    (r"STATE FARM", "Auto Insurance", False),
    # Utilities
    (r"PUGET SOUND", "Utilities", False),
    (r"REPUBLICSERVIC", "Utilities", False),
    # Loans
    (r"SoFi Bank", "SoFi Loan", False),
    # Phone/Internet
    (r"SAMMPLAT|Google FI", "Phone/Internet", False),
    # Tax
    (r"TREASURY DIREC|IRS USATAXPYMT|TREAS DRCT", "IRS Estimated Tax", False),
    # DMV / State
    (r"WA STATE DOL", "DMV", False),
    (r"WA DEPT REVENU", "State Tax/Fee", False),
    # Venmo
    (r"VENMO", "Venmo", False),
    # Legal/Professional
    (r"4 Corners Fina", "Legal/Financial Services", False),
    # Check
    (r"Check Paid", "Check", False),
    # Account verification
    (r"ACCTVERIFY", "Bank Fee", False),
]

CMA_INFLOW_RULES = [
    (r"PAYROLL|SFDC INC|sfdc Inc|Salesforce", "Payroll", False),
    (r"(?i)servicetitan", "Payroll", False),
    (r"Solium Inc", "RSU/ESPP Proceeds", False),
    (r"APARTMENTS|APTS SMOTH|Apartments\.c|Apa treas", "Rental Income", False),
    (r"OPTUMCLAIM|CONNECTYOURC|Connectyourc|Optumclaim", "Insurance Reimbursement", False),
    (r"ELAN CARDSVC|Elan Cardsvc", "CC Rewards Redemption", False),
    (r"Allstate Ins.*Prem Ref|ALLSTATE.*PREM REF", "Insurance Refund", False),
    (r"Electronic Funds Transfer Received|Eft Funds Received", "Transfer In", True),
    (r"TRANSFERRED FROM|Transferred From", "Transfer In", True),
    (r"MSPBNA|Mspbna", "Transfer In (Morgan Stanley)", True),
    (r"Mpb Us Inc", "Other Income", False),
]


def categorize_cma_transaction(txn_type: str, description: str, payee: str,
                               amount: float) -> tuple:
    """Categorize a CMA transaction. Returns (category, is_transfer)."""
    desc_upper = (description or "").upper()
    payee_upper = (payee or "").upper()
    combined = f"{desc_upper} {payee_upper}"

    # Priority 1: Sheri Martin (Capital One ******0615)
    if "CAPITAL ONE" in payee_upper and "0615" in payee_upper:
        amt = abs(amount)
        if abs(amt - 1254.00) < 0.01:
            return "Child Support", False
        elif abs(amt - 50000.00) < 0.01:
            return "Property Settlement", False
        elif amt >= 3000:
            return "Spousal Maintenance", False
        else:
            return "Divorce — Other", False

    # Priority 2: OurFamilyWizard
    if "OURFAMILYWIZ" in desc_upper or "OURFAMILYW" in desc_upper:
        if amount >= 0:
            return "Kids Cost (Reimbursement)", False
        else:
            return "Kids Cost", False

    # Priority 3/4: Rule-based
    rules = CMA_OUTFLOW_RULES if amount < 0 else CMA_INFLOW_RULES
    for pattern, category, is_transfer in rules:
        if re.search(pattern, description) or (payee and re.search(pattern, payee)):
            return category, is_transfer

    # Insufficient Funds reversal
    if "Insufficient Funds" in description:
        return "Transfer In (Reversal)", True

    # Deposit Received (generic)
    if "Deposit Received" in description:
        return "Other Income", False

    # Boeing BECU transfers
    if "BOEING" in payee_upper or "BECU" in combined:
        return "Transfer Out (BECU)", True

    return None, False


def parse_cma_activity(section_texts: list, period_end_date: date) -> list:
    """Parse Deposits, Withdrawals, Checking Activity, and Exchanges from CMA sections.

    Returns list of transaction dicts with: date, type, description, amount, payee, category, is_transfer.
    """
    transactions = []
    stmt_year = period_end_date.year
    stmt_month = period_end_date.month

    # Combine all section texts
    combined = "\n".join(section_texts)

    # Find activity sections by scanning for section headers within Activity pages
    # We need to parse: Deposits, Withdrawals, Checking Activity, Exchanges In, Exchanges Out
    lines = combined.split("\n")

    current_section = None
    section_lines = {}
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # Detect section headers
        if stripped == "Deposits" or stripped == "Deposits (continued)":
            current_section = "deposits"
        elif stripped == "Withdrawals" or stripped == "Withdrawals (continued)":
            current_section = "withdrawals"
        elif stripped.startswith("Checking Activity"):
            current_section = "checking"
        elif stripped == "Exchanges In" or stripped == "Exchanges In (continued)":
            current_section = "exchanges_in"
        elif stripped == "Exchanges Out" or stripped == "Exchanges Out (continued)":
            current_section = "exchanges_out"
        elif any(stripped.startswith(s) for s in [
            "Core Fund Activity", "Dividends, Interest",
            "Account Summary", "Holdings", "Income Summary",
            "Top Holdings", "Activity",
        ]):
            if stripped != "Activity":
                current_section = None
        elif stripped.startswith("Date Reference Description") or stripped.startswith("Date Reference"):
            # Column header for deposits/withdrawals — skip
            i += 1
            continue
        elif stripped.startswith("Check Number Post Date"):
            # Column header for checking activity — skip
            i += 1
            continue
        elif stripped.startswith("Symbol/") or (current_section in ("exchanges_in", "exchanges_out")
                                                 and "Security Name" in stripped):
            # Column header for exchanges — skip
            i += 1
            continue

        # Stop sections at Total lines
        if current_section and stripped.startswith("Total "):
            current_section = None
            i += 1
            continue

        if current_section:
            section_lines.setdefault(current_section, []).append(stripped)

        i += 1

    # Parse Deposits
    row_num = 0
    for txn in _parse_deposit_withdrawal_lines(section_lines.get("deposits", []),
                                                "deposit", stmt_year, stmt_month):
        txn["_row"] = row_num
        transactions.append(txn)
        row_num += 1

    # Parse Withdrawals
    for txn in _parse_deposit_withdrawal_lines(section_lines.get("withdrawals", []),
                                                "withdrawal", stmt_year, stmt_month):
        txn["_row"] = row_num
        transactions.append(txn)
        row_num += 1

    # Parse Checking Activity
    for txn in _parse_checking_lines(section_lines.get("checking", []),
                                      stmt_year, stmt_month):
        txn["_row"] = row_num
        transactions.append(txn)
        row_num += 1

    # Parse Exchanges In/Out
    for txn in _parse_exchange_lines(section_lines.get("exchanges_in", []),
                                      "exchange_in", stmt_year, stmt_month):
        txn["_row"] = row_num
        transactions.append(txn)
        row_num += 1

    for txn in _parse_exchange_lines(section_lines.get("exchanges_out", []),
                                      "exchange_out", stmt_year, stmt_month):
        txn["_row"] = row_num
        transactions.append(txn)
        row_num += 1

    # Categorize all transactions (skip those already categorized by exchange parser)
    for txn in transactions:
        if "category" not in txn:
            category, is_transfer = categorize_cma_transaction(
                txn["type"], txn["description"], txn.get("payee"), txn["amount"]
            )
            txn["category"] = category
            txn["is_transfer"] = is_transfer

    return transactions


def _resolve_date(mm_dd: str, stmt_year: int, stmt_month: int) -> str:
    """Convert MM/DD to YYYY-MM-DD, handling Dec→Jan rollover."""
    parts = mm_dd.split("/")
    txn_month = int(parts[0])
    txn_day = int(parts[1])

    # If statement is January but transaction is December → use prior year
    if stmt_month == 1 and txn_month == 12:
        return f"{stmt_year - 1}-{txn_month:02d}-{txn_day:02d}"
    return f"{stmt_year}-{txn_month:02d}-{txn_day:02d}"


def _parse_deposit_withdrawal_lines(lines: list, txn_type: str,
                                     stmt_year: int, stmt_month: int) -> list:
    """Parse deposit or withdrawal lines into transactions.

    Format: MM/DD Description Amount
    Continuation lines (payee info) start without a date.
    Multi-line payee example:
        01/02 Money Line Paid EFT FUNDS PAID AD05316742 /DIRECTED -3,105.00
               SHERI MARTIN
               CAPITAL ONE N.A. ******0615
    """
    transactions = []
    current = None

    for line in lines:
        # Skip blank lines and header-like lines
        if not line or line.startswith("Date ") or line.startswith("of "):
            continue
        # Skip page number lines like "11 of 38"
        if re.match(r"^\d+ of \d+$", line):
            continue

        date_match = ACTIVITY_DATE_RE.match(line)
        if date_match:
            # Save previous transaction
            if current:
                transactions.append(current)

            mm_dd = date_match.group(1)
            rest = line[date_match.end():].strip()

            # Extract amount from end of line
            amount_match = ACTIVITY_AMOUNT_RE.search(rest)
            if amount_match:
                amount_str = amount_match.group()
                description = rest[:amount_match.start()].strip()
                amount = parse_money(amount_str)
            else:
                description = rest
                amount = 0.0

            current = {
                "date": _resolve_date(mm_dd, stmt_year, stmt_month),
                "type": txn_type,
                "description": description,
                "amount": amount or 0.0,
                "payee": None,
            }
        elif current:
            # Continuation line — append to payee
            # Skip page headers and noise lines that appear at page breaks
            if (line and not line.startswith("Date ")
                    and not re.match(r"^\d+ of \d+$", line)
                    and "INVESTMENT REPORT" not in line
                    and "Account #" not in line
                    and "YI CHEN" not in line
                    and not re.match(r"^[A-Z]$", line)  # Single letter artifact
                    and not re.match(r"^\d{8,}$", line)  # Page ID numbers
                    and not re.match(r"^[A-Z_]+$", line)  # Barcode-like artifacts
                    and "EC_RM" not in line
                    and not re.match(r"^(?:January|February|March|April|May|June|July|August|September|October|November|December)\s", line)
                    and not line.startswith("Activity")
                    and "(continued)" not in line
                    ):
                if current["payee"]:
                    current["payee"] += " / " + line.strip()
                else:
                    current["payee"] = line.strip()

    # Don't forget the last transaction
    if current:
        transactions.append(current)

    return transactions


def _parse_checking_lines(lines: list, stmt_year: int, stmt_month: int) -> list:
    """Parse Checking Activity lines.

    Format: CheckNumber MM/DD Code Description Amount
    """
    transactions = []
    for line in lines:
        if not line:
            continue
        m = CHECK_LINE_RE.match(line)
        if m:
            check_num = m.group(1)
            mm_dd = m.group(2)
            desc_and_code = m.group(3).strip()
            amount = parse_money(m.group(4))
            transactions.append({
                "date": _resolve_date(mm_dd, stmt_year, stmt_month),
                "type": "withdrawal",
                "description": f"Check #{check_num} {desc_and_code}",
                "amount": amount or 0.0,
                "payee": None,
            })
    return transactions


def _parse_exchange_lines(lines: list, txn_type: str,
                           stmt_year: int, stmt_month: int) -> list:
    """Parse Exchanges In/Out lines.

    Format: MM/DD SecurityName CUSIP Description Quantity Price Amount
    We only need the date, description, and amount.
    """
    transactions = []
    for line in lines:
        if not line:
            continue
        date_match = ACTIVITY_DATE_RE.match(line)
        if not date_match:
            continue
        mm_dd = date_match.group(1)
        rest = line[date_match.end():].strip()

        # Extract amount from end of line
        amount_match = ACTIVITY_AMOUNT_RE.search(rest)
        if not amount_match:
            continue

        amount_str = amount_match.group()
        description = rest[:amount_match.start()].strip()
        # Clean out quantity/price columns — keep just the meaningful description
        # e.g. "Z31-859340-1 Transferred To - -" → "Transferred To Z31-859340-1"
        amount = parse_money(amount_str)

        is_in = txn_type == "exchange_in"
        transactions.append({
            "date": _resolve_date(mm_dd, stmt_year, stmt_month),
            "type": "exchange_in" if is_in else "exchange_out",
            "description": description,
            "amount": amount or 0.0,
            "payee": None,
            "category": "Transfer In (Fidelity)" if is_in else "Transfer Out (Fidelity)",
            "is_transfer": True,
        })
    return transactions


# --- Year-End Report Parser ---


def parse_year_end_report(pdf_path: Path) -> dict:
    """Parse the year-end summary report for reconciliation."""
    result = {
        "portfolio": {},
        "income_summary": {},
        "accounts": [],
    }

    with pdfplumber.open(pdf_path) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]

    # Portfolio summary from page 1
    text = pages_text[0]
    result["portfolio"]["beginning_value"] = extract_money_after(text, "Beginning Portfolio Value")
    result["portfolio"]["ending_value"] = extract_money_after(text, "Ending Portfolio Value")
    result["portfolio"]["additions"] = extract_money_after(text, "Additions")
    result["portfolio"]["subtractions"] = extract_money_after(text, "Subtractions")
    result["portfolio"]["change_in_investment_value"] = extract_money_after(
        text, "Change in Investment Value"
    )
    result["portfolio"]["transfers_between_fidelity"] = extract_money_after(
        text, "Transfers Between Fidelity Accounts"
    )

    # Income summary (usually page 3)
    result["income_summary"] = parse_income_summary(pages_text)

    # Per-account sections
    sections = split_by_account(pages_text)
    for acct_num, sect_texts in sections.items():
        info = classify_account(acct_num, sect_texts)
        summary = parse_account_summary(sect_texts)
        income = parse_account_income(sect_texts)
        result["accounts"].append({
            "account_number": acct_num,
            **info,
            "summary": summary,
            "income": income,
        })

    return result


# --- Main Statement Parser ---


def parse_statement(pdf_path: Path) -> dict:
    """Parse a monthly Fidelity investment report PDF."""
    logger.info(f"Parsing {pdf_path.name}")

    with pdfplumber.open(pdf_path) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]
        num_pages = len(pdf.pages)

    # Extract date range from first page
    m = DATE_RANGE_RE.search(pages_text[0])
    date_str = m.group() if m else ""
    # Parse statement date from filename
    fm = MONTHLY_RE.match(pdf_path.name)
    if fm:
        month, day, yr = int(fm.group(1)), int(fm.group(2)), int(fm.group(3))
        stmt_date = date(yr, month, day)
        period_start = date(yr, month, 1)
    else:
        stmt_date = date.today()
        period_start = stmt_date.replace(day=1)

    # 1. Portfolio summary
    portfolio = parse_portfolio_summary(pages_text)

    # 2. Income summary
    income_summary = parse_income_summary(pages_text)

    # 3. Split by account sections
    sections = split_by_account(pages_text)
    logger.info(f"  Found {len(sections)} account sections: {list(sections.keys())}")

    # 4. Parse each account
    accounts = []
    for acct_num, sect_texts in sections.items():
        info = classify_account(acct_num, sect_texts)
        summary = parse_account_summary(sect_texts)
        income = parse_account_income(sect_texts)
        holdings_list = parse_holdings(sect_texts)

        holdings_dicts = []
        for h in holdings_list:
            hd = {
                "symbol": h.symbol,
                "description": h.description,
                "asset_class": h.asset_class,
                "quantity": h.quantity,
                "price": h.price,
                "market_value": h.market_value,
            }
            if h.cost_basis is not None:
                hd["cost_basis"] = h.cost_basis
            if h.unrealized_gain_loss is not None:
                hd["unrealized_gain_loss"] = h.unrealized_gain_loss
            holdings_dicts.append(hd)

        acct_data = {
            "account_number": acct_num,
            **info,
            "summary": _clean_summary(summary),
            "income": _clean_dict(income),
            "holdings": holdings_dicts,
        }

        # Parse CMA activity for Z26-474983
        if acct_num == CMA_ACCOUNT:
            activity = parse_cma_activity(sect_texts, stmt_date)
            if activity:
                acct_data["activity"] = [
                    {k: v for k, v in txn.items() if k != "_row" and v is not None}
                    for txn in activity
                ]
                logger.info(f"  CMA activity: {len(activity)} transactions parsed")

        accounts.append(acct_data)

    # 5. Validation
    validation = validate_statement(portfolio, income_summary, accounts)

    # 6. Build result
    result = {
        "statement_date": str(stmt_date),
        "period_start": str(period_start),
        "period_end": str(stmt_date),
        "portfolio": _clean_dict(portfolio),
        "income_summary": _clean_income_summary(income_summary),
        "accounts": accounts,
        "validation": validation,
        "source": {
            "file": pdf_path.name,
            "pages": num_pages,
            "processed_at": datetime.now().isoformat(),
        },
    }

    return result


def _clean_dict(d: dict) -> dict:
    """Remove None values from a dict."""
    return {k: v for k, v in d.items() if v is not None}


def _clean_summary(d: dict) -> dict:
    """Remove None values and zero-value optional fields from summary."""
    result = {}
    for k, v in d.items():
        if v is None:
            continue
        result[k] = v
    return result


def _clean_income_summary(d: dict) -> dict:
    """Clean income summary for YAML output."""
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            cleaned = _clean_dict(v)
            if cleaned:
                result[k] = cleaned
        elif v is not None:
            result[k] = v
    return result


# --- Validation ---


def validate_statement(portfolio: dict, income_summary: dict, accounts: list) -> dict:
    """Run intra-statement validation checks."""
    checks = {
        "portfolio_sum_check": True,
        "income_sum_check": True,
        "account_balance_checks": True,
        "holdings_value_checks": True,
        "checks_passed": True,
        "mismatches": [],
    }

    # Check 1: sum(account endings) ~= portfolio ending
    portfolio_ending = portfolio.get("ending_value")
    if portfolio_ending is not None:
        account_sum = 0
        for acct in accounts:
            ev = acct.get("summary", {}).get("ending_value")
            if ev is not None:
                account_sum += ev
        if not close_enough(account_sum, portfolio_ending, tol=1.0):
            checks["portfolio_sum_check"] = False
            checks["mismatches"].append(
                f"Portfolio ending ${portfolio_ending:,.2f} != sum of accounts ${account_sum:,.2f} "
                f"(diff=${abs(portfolio_ending - account_sum):,.2f})"
            )

    # Check 2: sum(account income) ~= portfolio income total
    grand_total = income_summary.get("grand_total")
    if grand_total is not None:
        income_sum = 0
        for acct in accounts:
            it = acct.get("income", {}).get("total")
            if it is not None:
                income_sum += it
        if not close_enough(income_sum, grand_total, tol=0.05):
            checks["income_sum_check"] = False
            checks["mismatches"].append(
                f"Portfolio income ${grand_total:,.2f} != sum of account income ${income_sum:,.2f}"
            )

    # Check 3: per-account balance equation
    # Note: additions/subtractions are TOP-LEVEL totals. Sub-items like deposits,
    # withdrawals, exchanges, transfers, transaction costs are breakdowns — do NOT add
    # them separately. The equation is: beg + additions + subtractions + change = ending
    # For year-end reports, transfers_between_fidelity and transaction_costs are
    # separate top-level items (not folded into additions/subtractions).
    for acct in accounts:
        s = acct.get("summary", {})
        beg = s.get("beginning_value")
        end = s.get("ending_value")

        if beg is None or end is None:
            continue

        # Use additions/subtractions/change as primary terms
        add = s.get("additions", 0) or 0
        sub = s.get("subtractions", 0) or 0
        chg = s.get("change_in_investment_value", 0) or 0

        # Transaction costs and transfers may be separate (year-end) or part of
        # subtractions (monthly). Only add them if additions+subtractions+change
        # doesn't balance, and the terms exist.
        expected = beg + add + sub + chg
        if close_enough(expected, end, tol=0.05):
            continue

        # Try with additional year-end fields
        txn = s.get("transaction_costs", 0) or 0
        xfr = s.get("transfers_between_fidelity", 0) or 0
        expected_with_extras = expected + txn + xfr
        if close_enough(expected_with_extras, end, tol=0.05):
            continue

        checks["account_balance_checks"] = False
        checks["mismatches"].append(
            f"Account {acct['account_number']}: "
            f"beg(${beg:,.2f}) + add(${add:,.2f}) + sub(${sub:,.2f}) + chg(${chg:,.2f}) "
            f"= ${expected:,.2f} != ending ${end:,.2f} (diff=${abs(expected - end):,.2f})"
        )

    # Check 4: sum(holdings) ~= account ending value
    for acct in accounts:
        end_val = acct.get("summary", {}).get("ending_value")
        if end_val is None:
            continue
        holdings = acct.get("holdings", [])
        if not holdings:
            continue
        holdings_sum = sum(h.get("market_value", 0) or 0 for h in holdings)
        if not close_enough(holdings_sum, end_val, tol=1.0):
            checks["holdings_value_checks"] = False
            checks["mismatches"].append(
                f"Account {acct['account_number']}: "
                f"holdings sum ${holdings_sum:,.2f} != ending value ${end_val:,.2f} "
                f"(diff=${abs(holdings_sum - end_val):,.2f})"
            )

    checks["checks_passed"] = not bool(checks["mismatches"])
    return checks


# --- Chain Validation ---


def validate_chain(yamls_dir: Path) -> list:
    """Validate monthly continuity: each month's ending == next month's beginning."""
    issues = []
    yaml_files = sorted(yamls_dir.glob("*.yaml"))
    if len(yaml_files) < 2:
        return ["Need at least 2 YAML files for chain validation"]

    snapshots = []
    for yf in yaml_files:
        with open(yf) as f:
            data = yaml.safe_load(f)
        if data:
            snapshots.append(data)

    snapshots.sort(key=lambda d: d.get("statement_date", ""))

    for i in range(len(snapshots) - 1):
        curr = snapshots[i]
        nxt = snapshots[i + 1]
        curr_date = curr["statement_date"]
        nxt_date = nxt["statement_date"]

        # Portfolio-level check
        curr_ending = curr.get("portfolio", {}).get("ending_value")
        nxt_beginning = nxt.get("portfolio", {}).get("beginning_value")
        if curr_ending is not None and nxt_beginning is not None:
            if not close_enough(curr_ending, nxt_beginning, tol=0.05):
                issues.append(
                    f"Portfolio: {curr_date} ending ${curr_ending:,.2f} != "
                    f"{nxt_date} beginning ${nxt_beginning:,.2f}"
                )

        # Per-account check
        curr_accounts = {a["account_number"]: a for a in curr.get("accounts", [])}
        nxt_accounts = {a["account_number"]: a for a in nxt.get("accounts", [])}

        for acct_num in set(curr_accounts) & set(nxt_accounts):
            c_end = curr_accounts[acct_num].get("summary", {}).get("ending_value")
            n_beg = nxt_accounts[acct_num].get("summary", {}).get("beginning_value")
            if c_end is not None and n_beg is not None:
                if not close_enough(c_end, n_beg, tol=0.05):
                    issues.append(
                        f"Account {acct_num}: {curr_date} ending ${c_end:,.2f} != "
                        f"{nxt_date} beginning ${n_beg:,.2f}"
                    )

        # Report opened/closed accounts (expected breaks)
        opened = set(nxt_accounts) - set(curr_accounts)
        closed = set(curr_accounts) - set(nxt_accounts)
        for a in opened:
            issues.append(f"INFO: Account {a} opened between {curr_date} and {nxt_date}")
        for a in closed:
            c_end = curr_accounts[a].get("summary", {}).get("ending_value")
            if c_end is not None and c_end > 0.01:
                issues.append(
                    f"WARN: Account {a} closed between {curr_date} and {nxt_date} "
                    f"with ending value ${c_end:,.2f}"
                )
            else:
                issues.append(
                    f"INFO: Account {a} closed between {curr_date} and {nxt_date} (zero balance)"
                )

    return issues


# --- Year-End Reconciliation ---


def reconcile_year_end(yamls_dir: Path, year: int) -> list:
    """Compare monthly YAMLs against year-end report."""
    issues = []

    # Find year-end report
    ye_path = SOURCE_ROOT / str(year) / "year-end-report-yi-chen.pdf"
    if not ye_path.exists():
        return [f"Year-end report not found: {ye_path}"]

    ye_data = parse_year_end_report(ye_path)

    # Load monthly YAMLs for the year
    yaml_files = sorted(yamls_dir.glob("*.yaml"))
    monthlies = []
    for yf in yaml_files:
        with open(yf) as f:
            data = yaml.safe_load(f)
        if data and data.get("statement_date", "").startswith(str(year)):
            monthlies.append(data)

    if not monthlies:
        return [f"No monthly YAMLs found for year {year}"]

    monthlies.sort(key=lambda d: d["statement_date"])
    first = monthlies[0]
    last = monthlies[-1]

    # Check 1: Jan beginning == year-end beginning
    jan_beg = first.get("portfolio", {}).get("beginning_value")
    ye_beg = ye_data.get("portfolio", {}).get("beginning_value")
    if jan_beg is not None and ye_beg is not None:
        if not close_enough(jan_beg, ye_beg, tol=0.05):
            issues.append(
                f"Beginning mismatch: Jan ${jan_beg:,.2f} vs year-end ${ye_beg:,.2f}"
            )
        else:
            issues.append(f"OK: Beginning value matches: ${ye_beg:,.2f}")

    # Check 2: Dec ending == year-end ending
    dec_end = last.get("portfolio", {}).get("ending_value")
    ye_end = ye_data.get("portfolio", {}).get("ending_value")
    if dec_end is not None and ye_end is not None:
        if not close_enough(dec_end, ye_end, tol=0.05):
            issues.append(
                f"Ending mismatch: Dec ${dec_end:,.2f} vs year-end ${ye_end:,.2f}"
            )
        else:
            issues.append(f"OK: Ending value matches: ${ye_end:,.2f}")

    # Check 3: Sum of monthly incomes == year-end income
    ye_income_total = ye_data.get("income_summary", {}).get("grand_total")
    if ye_income_total is not None:
        monthly_income_sum = 0
        for m in monthlies:
            gt = m.get("income_summary", {}).get("grand_total")
            if gt is not None:
                monthly_income_sum += gt
        if not close_enough(monthly_income_sum, ye_income_total, tol=0.10):
            issues.append(
                f"Income mismatch: monthly sum ${monthly_income_sum:,.2f} "
                f"vs year-end ${ye_income_total:,.2f}"
            )
        else:
            issues.append(f"OK: Income total matches: ${ye_income_total:,.2f}")

    # Check 4: Per-account beginning/ending
    ye_accounts = {a["account_number"]: a for a in ye_data.get("accounts", [])}
    first_accounts = {a["account_number"]: a for a in first.get("accounts", [])}
    last_accounts = {a["account_number"]: a for a in last.get("accounts", [])}

    for acct_num, ye_acct in ye_accounts.items():
        ye_beg = ye_acct.get("summary", {}).get("beginning_value")
        ye_end = ye_acct.get("summary", {}).get("ending_value")

        if acct_num in first_accounts:
            m_beg = first_accounts[acct_num].get("summary", {}).get("beginning_value")
            if ye_beg is not None and m_beg is not None:
                if not close_enough(m_beg, ye_beg, tol=0.05):
                    issues.append(
                        f"Account {acct_num} beginning: Jan ${m_beg:,.2f} vs year-end ${ye_beg:,.2f}"
                    )

        if acct_num in last_accounts:
            m_end = last_accounts[acct_num].get("summary", {}).get("ending_value")
            if ye_end is not None and m_end is not None:
                if not close_enough(m_end, ye_end, tol=0.05):
                    issues.append(
                        f"Account {acct_num} ending: Dec ${m_end:,.2f} vs year-end ${ye_end:,.2f}"
                    )

    return issues


# --- Gap Detection ---


def detect_gaps(yamls_dir: Path) -> list:
    """Check for missing months between first and last statement."""
    issues = []
    yaml_files = sorted(yamls_dir.glob("*.yaml"))
    dates = []
    for yf in yaml_files:
        with open(yf) as f:
            data = yaml.safe_load(f)
        if data:
            dates.append(data["statement_date"])

    if len(dates) < 2:
        return issues

    dates.sort()
    # Check each consecutive pair
    for i in range(len(dates) - 1):
        d1 = date.fromisoformat(dates[i])
        d2 = date.fromisoformat(dates[i + 1])
        # Expected gap is ~28-31 days
        gap = (d2 - d1).days
        if gap > 40:
            issues.append(f"Gap detected: {dates[i]} to {dates[i+1]} ({gap} days)")

    return issues


# --- YAML Writer ---


def write_yaml(data: dict, output_path: Path):
    """Write statement data to YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Custom representer to format floats nicely
    class MoneyDumper(yaml.SafeDumper):
        pass

    def float_representer(dumper, value):
        if value == int(value):
            return dumper.represent_float(value)
        return dumper.represent_scalar("tag:yaml.org,2002:float", f"{value:.2f}")

    MoneyDumper.add_representer(float, float_representer)

    with open(output_path, "w") as f:
        yaml.dump(data, f, Dumper=MoneyDumper, default_flow_style=False,
                  sort_keys=False, allow_unicode=True)

    logger.info(f"  Written: {output_path}")


# --- CLI Commands ---


def cmd_scan(year: Optional[int] = None):
    """Show available PDFs and their processing status."""
    pdfs = discover_pdfs(year)
    log = load_processing_log()

    print(f"\nFidelity Account Statements")
    print(f"Source: {SOURCE_ROOT}")
    print(f"Output: {OUTPUT_ROOT}")
    print(f"Found {len(pdfs)} PDFs\n")

    monthly = [p for p in pdfs if not p.is_year_end]
    year_end = [p for p in pdfs if p.is_year_end]
    new_count = len([p for p in pdfs if p.key not in log])

    print(f"Monthly statements: {len(monthly)}")
    for p in sorted(monthly, key=lambda x: x.statement_date):
        status = "processed" if p.key in log else "NEW"
        print(f"  {p.statement_date}  {p.path.name:40s}  [{status}]")

    if year_end:
        print(f"\nYear-end reports: {len(year_end)}")
        for p in year_end:
            status = "processed" if p.key in log else "NEW"
            print(f"  {p.statement_date}  {p.path.name:40s}  [{status}]")

    print(f"\nNew (unprocessed): {new_count}")


def cmd_run(year: Optional[int] = None, force: bool = False):
    """Parse PDFs and generate YAMLs."""
    pdfs = discover_pdfs(year)
    monthly_pdfs = [p for p in pdfs if not p.is_year_end]
    to_process = get_new_pdfs(monthly_pdfs, force)

    if not to_process:
        print("No new PDFs to process.")
        return

    print(f"Processing {len(to_process)} statements...")
    log = load_processing_log()
    success = 0
    errors = 0

    for pdf_info in sorted(to_process, key=lambda x: x.statement_date):
        try:
            data = parse_statement(pdf_info.path)
            output_path = OUTPUT_ROOT / f"{pdf_info.statement_date}.yaml"
            write_yaml(data, output_path)

            # Update processing log
            log[pdf_info.key] = {
                "statement_date": str(pdf_info.statement_date),
                "output_file": str(output_path.relative_to(OBSIDIAN_ROOT)),
                "processed_at": datetime.now().isoformat(),
                "accounts": len(data.get("accounts", [])),
                "validation_passed": data.get("validation", {}).get("checks_passed", False),
            }
            save_processing_log(log)

            # Report validation
            v = data.get("validation", {})
            if v.get("checks_passed"):
                logger.info(f"  Validation: PASSED")
                success += 1
            else:
                logger.warning(f"  Validation: FAILED")
                for m in v.get("mismatches", []):
                    logger.warning(f"    - {m}")
                success += 1  # Still count as processed

        except Exception as e:
            logger.error(f"  Error processing {pdf_info.path.name}: {e}")
            import traceback
            traceback.print_exc()
            errors += 1

    print(f"\nDone: {success} processed, {errors} errors")


def cmd_chain():
    """Run monthly continuity validation."""
    print("Running chain validation...")
    issues = validate_chain(OUTPUT_ROOT)
    gaps = detect_gaps(OUTPUT_ROOT)

    if gaps:
        print("\nGap Detection:")
        for g in gaps:
            print(f"  {g}")

    if issues:
        print("\nChain Validation:")
        for issue in issues:
            tag = "INFO" if issue.startswith("INFO") else ("WARN" if issue.startswith("WARN") else "BREAK")
            print(f"  [{tag}] {issue}")
    else:
        print("  No issues found.")


def cmd_reconcile(year: int):
    """Compare monthly YAMLs against year-end report."""
    print(f"Reconciling year {year}...")
    issues = reconcile_year_end(OUTPUT_ROOT, year)
    for issue in issues:
        print(f"  {issue}")


# --- Main ---


def main():
    parser = argparse.ArgumentParser(description="Fidelity account statement ingestion")
    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="Show available PDFs")
    scan_p.add_argument("--year", type=int, help="Filter by year")

    run_p = sub.add_parser("run", help="Parse PDFs and generate YAMLs")
    run_p.add_argument("--year", type=int, help="Filter by year")
    run_p.add_argument("--force", action="store_true", help="Re-process all PDFs")

    chain_p = sub.add_parser("chain", help="Monthly continuity validation")

    recon_p = sub.add_parser("reconcile", help="Year-end reconciliation")
    recon_p.add_argument("--year", type=int, default=2025, help="Year to reconcile")

    args = parser.parse_args()

    setup_logging()

    if args.command == "scan":
        cmd_scan(args.year)
    elif args.command == "run":
        cmd_run(args.year, args.force)
    elif args.command == "chain":
        cmd_chain()
    elif args.command == "reconcile":
        cmd_reconcile(args.year)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
