#!/usr/bin/env python3
"""Credit card statement PDF ingestion pipeline.

Extracts transactions from credit card statement PDFs and saves as CSVs.

Supported cards:
  - Apple Card
  - Chase Prime (1158), Sapphire (2341), Freedom (1350)
  - Fidelity Rewards, Fidelity Credit Card
  - Bank of America Atmos Rewards (7982)
"""

import argparse
import calendar
import csv
import json
import logging
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed. Run: pip install pdfplumber", file=sys.stderr)
    sys.exit(1)

# --- Path Resolution ---
# Script lives at .claude/scripts/ — Obsidian root is two levels up
SCRIPT_DIR = Path(__file__).parent.resolve()
OBSIDIAN_ROOT = SCRIPT_DIR.parent.parent
SOURCE_ROOT = Path.home() / "Dropbox" / "0-FinancialStatements" / "credit-cards"
OUTPUT_ROOT = OBSIDIAN_ROOT / "Finance" / "credit-card"
LOG_FILE = OUTPUT_ROOT / "ingest.log"
PROCESSING_LOG_PATH = OUTPUT_ROOT / "processing_log.json"

# --- Retry Settings ---
MISMATCH_THRESHOLD = 0.001  # 0.1% — triggers retry if mismatch ratio exceeds this
RETRY_SETTINGS = [
    {"x_tolerance": 1},
    {"layout": True},
    {"x_tolerance": 5},
]
MAX_PARSE_ATTEMPTS = 3  # Retry budget for transient PDF parse failures

# --- Logging ---
logger = logging.getLogger("ingest_cc")


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


# --- Data Types ---
@dataclass
class Transaction:
    date: date
    description: str
    amount: float  # negative = charge, positive = payment/credit
    category: str = ""


@dataclass
class CardConfig:
    name: str
    source_dir: str  # relative to SOURCE_ROOT
    filename_pattern: str  # regex
    parser_class: str
    has_year_subfolders: bool = True
    account_suffix: str | None = None  # last 4 digits of card number for BofA regex


# --- Card Registry ---
CARD_CONFIGS = {
    "apple-card": CardConfig(
        name="apple-card",
        source_dir="apple card",
        filename_pattern=r"Apple Card Statement - (\w+) (\d{4})\.pdf$",
        parser_class="AppleCardParser",
        has_year_subfolders=True,
    ),
    "chase-prime-1158": CardConfig(
        name="chase-prime-1158",
        source_dir="chase-prime-cc",
        filename_pattern=r"(\d{8})-statements-1158-\.pdf$",
        parser_class="ChaseParser",
        has_year_subfolders=True,
    ),
    "chase-sapphire-2341": CardConfig(
        name="chase-sapphire-2341",
        source_dir="chase-sapphire-cc",
        filename_pattern=r"(\d{8})-statements-2341-\.pdf$",
        parser_class="ChaseParser",
        has_year_subfolders=True,
    ),
    "chase-freedom-1350": CardConfig(
        name="chase-freedom-1350",
        source_dir="chase-freedom-1350",
        filename_pattern=r"(\d{8})-statements-1350-\.pdf$",
        parser_class="ChaseParser",
        has_year_subfolders=True,
    ),
    "fidelity-credit-card": CardConfig(
        name="fidelity-credit-card",
        source_dir="fidelity-credit-card",
        filename_pattern=r"^(\d{4}-\d{2}-\d{2}).*\.pdf$",
        parser_class="FidelityParser",
        has_year_subfolders=True,
    ),
    "bofa-atmos-7982": CardConfig(
        name="bofa-atmos-7982",
        source_dir="bank-of-america-atmos-rewards",
        filename_pattern=r"eStmt_(\d{4}-\d{2}-\d{2})\.pdf$",
        parser_class="BankOfAmericaParser",
        has_year_subfolders=True,
        account_suffix="7982",
    ),
    "bofa-rewards-visa": CardConfig(
        name="bofa-rewards-visa",
        source_dir="bank-of-america-rewards-visa-signature",
        filename_pattern=r"eStmt_(\d{4}-\d{2}-\d{2})\.pdf$",
        parser_class="BankOfAmericaParser",
        has_year_subfolders=True,
    ),
}


# --- Processing Log ---
def load_processing_log() -> dict:
    if PROCESSING_LOG_PATH.exists():
        with open(PROCESSING_LOG_PATH) as f:
            return json.load(f)
    return {"version": 1, "last_run": None, "cards": {}}


def save_processing_log(log: dict):
    PROCESSING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log["last_run"] = datetime.now().isoformat(timespec="seconds")
    with open(PROCESSING_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


# --- PDF Discovery ---
def discover_pdfs(config: CardConfig) -> list[tuple[Path, str]]:
    """Returns list of (pdf_path, pdf_filename) for a card config.
    Deduplicates by filename (handles misfiled PDFs in wrong year folders).
    """
    source_dir = SOURCE_ROOT / config.source_dir
    if not source_dir.exists():
        logger.warning(f"Source directory not found: {source_dir}")
        return []

    pdfs = []
    seen_filenames = set()

    if config.has_year_subfolders:
        for year_dir in sorted(source_dir.iterdir()):
            if year_dir.is_dir() and year_dir.name.isdigit():
                for pdf_file in sorted(year_dir.iterdir()):
                    if (
                        pdf_file.suffix.lower() == ".pdf"
                        and re.search(config.filename_pattern, pdf_file.name)
                        and pdf_file.name not in seen_filenames
                    ):
                        seen_filenames.add(pdf_file.name)
                        pdfs.append((pdf_file, pdf_file.name))
    else:
        for pdf_file in sorted(source_dir.iterdir()):
            if (
                pdf_file.suffix.lower() == ".pdf"
                and re.search(config.filename_pattern, pdf_file.name)
                and pdf_file.name not in seen_filenames
            ):
                seen_filenames.add(pdf_file.name)
                pdfs.append((pdf_file, pdf_file.name))

    return pdfs


def get_new_pdfs(
    config: CardConfig, processing_log: dict, skip_errors: bool = False
) -> list[tuple[Path, str]]:
    """Returns PDFs not yet successfully processed."""
    all_pdfs = discover_pdfs(config)
    card_log = processing_log.get("cards", {}).get(config.name, {})
    processed = card_log.get("processed", {})
    errors = card_log.get("errors", {})

    new_pdfs = []
    for pdf_path, filename in all_pdfs:
        if filename in processed:
            continue
        if skip_errors and filename in errors:
            continue
        new_pdfs.append((pdf_path, filename))

    return new_pdfs


# --- Parsers ---
class BaseParser(ABC):
    def __init__(self, pdf_path: Path, config: CardConfig):
        self.pdf_path = pdf_path
        self.config = config

    @abstractmethod
    def extract_statement_date(self) -> date:
        ...

    @abstractmethod
    def extract_transactions(self, text: str | None = None) -> tuple[list[Transaction], list[str]]:
        """Extract transactions and return (transactions, warnings).

        If text is provided, parse from that text instead of extracting from PDF.
        Populates internal expected totals used by compute_mismatch().
        """
        ...

    @abstractmethod
    def compute_mismatch(self, transactions: list[Transaction]) -> tuple[float, float]:
        """Returns (max_absolute_mismatch, expected_total_for_ratio_denominator).

        Must be called after extract_transactions() which populates expected totals.
        """
        ...

    def extract_balance_summary(self, text: str) -> dict | None:
        """Extract previous_balance and new_balance from statement text.

        Returns {"previous_balance": float, "new_balance": float} or None.
        Used for post-import DB validation: previous_balance + sum(txns) = new_balance.
        """
        return None  # Override in subclasses

    def _extract_full_text(self, **extract_kwargs) -> str:
        text_parts = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(**extract_kwargs)
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    def _infer_year(self, tx_month: int, stmt_date: date) -> int:
        """Infer transaction year from statement date.
        Handles Dec->Jan rollover (e.g., Dec transaction on Jan statement).
        """
        year = stmt_date.year
        if tx_month > stmt_date.month and (tx_month - stmt_date.month) > 6:
            year -= 1
        return year


class ChaseParser(BaseParser):
    """Parser for Chase credit card statements (Prime, Sapphire, Freedom).

    Transaction format: MM/DD  Description  Amount
    - Payments section: amounts are negative in PDF
    - Purchases section: amounts are positive in PDF
    - Sign convention: negate all raw amounts (charges->negative, payments->positive)
    """

    TX_RE = re.compile(r"^(\d{2}/\d{2})\s+(.+?)\s+([-]?[\d,]+\.\d{2})$")

    def __init__(self, pdf_path: Path, config: CardConfig):
        super().__init__(pdf_path, config)
        self._expected_totals: dict = {}

    def extract_statement_date(self) -> date:
        match = re.search(r"(\d{8})-statements", self.pdf_path.name)
        if not match:
            raise ValueError(f"Cannot parse statement date from: {self.pdf_path.name}")
        return datetime.strptime(match.group(1), "%Y%m%d").date()

    def extract_balance_summary(self, text: str) -> dict | None:
        prev = re.search(r"Previous Balance\s+\$?([\d,]+\.\d{2})", text)
        new = re.search(r"New Balance\s+\$?([\d,]+\.\d{2})", text)
        if prev and new:
            return {
                "previous_balance": float(prev.group(1).replace(",", "")),
                "new_balance": float(new.group(1).replace(",", "")),
            }
        return None

    def _extract_expected_totals(self, text: str) -> dict:
        """Extract expected totals from Account Summary for validation."""
        totals = {}
        m = re.search(r"Purchases\s+\+?\$?([\d,]+\.\d{2})", text)
        if m:
            totals["purchases"] = float(m.group(1).replace(",", ""))
        m = re.search(r"Payment, Credits\s+[-]?\$?([\d,]+\.\d{2})", text)
        if m:
            totals["payments"] = float(m.group(1).replace(",", ""))
        m = re.search(r"Interest Charged\s+\+?\$?([\d,]+\.\d{2})", text)
        if m:
            totals["interest"] = float(m.group(1).replace(",", ""))
        m = re.search(r"Fees Charged\s+\+?\$?([\d,]+\.\d{2})", text)
        if m:
            totals["fees"] = float(m.group(1).replace(",", ""))
        return totals

    def extract_transactions(self, text: str | None = None) -> tuple[list[Transaction], list[str]]:
        if text is None:
            text = self._extract_full_text()
        stmt_date = self.extract_statement_date()
        transactions = []
        warnings = []

        self._expected_totals = self._extract_expected_totals(text)

        in_activity = False

        for line in text.split("\n"):
            line = line.strip()

            # Chase PDFs render some headers with doubled characters
            # e.g., "AACCCCOOUUNNTT AACCTTIIVVIITTYY" instead of "ACCOUNT ACTIVITY"
            if "ACCOUNT ACTIVITY" in line or "AACCCCOOUUNNTT" in line:
                # Stop at "SHOP WITH POINTS ACTIVITY" (doubled: SSHHOOPP...)
                if "SHOP WITH POINTS" in line or "SSHHOOPP" in line:
                    break
                in_activity = True
                continue
            if not in_activity:
                continue

            # Stop markers
            if any(
                marker in line
                for marker in [
                    "Year-to-Date",
                    "Interest Charge Calculation",
                    "INTEREST CHARGE CALCULATION",
                    "SHOP WITH POINTS",
                    "SSHHOOPP",
                ]
            ):
                break

            if line.startswith("TOTAL"):
                continue

            m = self.TX_RE.match(line)
            if not m:
                continue

            date_str = m.group(1)
            desc = m.group(2).strip()
            raw_amount = float(m.group(3).replace(",", ""))

            tx_month, tx_day = int(date_str[:2]), int(date_str[3:5])
            year = self._infer_year(tx_month, stmt_date)

            try:
                tx_date = date(year, tx_month, tx_day)
            except ValueError:
                warnings.append(
                    f"Invalid date {year}-{tx_month:02d}-{tx_day:02d} in {self.pdf_path.name}"
                )
                continue

            # Negate: PDF payments are negative->positive, purchases positive->negative
            csv_amount = round(-raw_amount, 2)

            transactions.append(
                Transaction(date=tx_date, description=desc, amount=csv_amount)
            )

        return transactions, warnings

    def compute_mismatch(self, transactions: list[Transaction]) -> tuple[float, float]:
        expected = self._expected_totals
        mismatches = []

        expected_total_charges = (
            expected.get("purchases", 0)
            + expected.get("fees", 0)
            + expected.get("interest", 0)
        )
        if expected_total_charges > 0:
            actual_charges = round(
                sum(-t.amount for t in transactions if t.amount < 0), 2
            )
            mismatches.append(
                (abs(actual_charges - expected_total_charges), expected_total_charges)
            )

        if expected.get("payments") is not None and expected["payments"] > 0:
            actual_payments = round(
                sum(t.amount for t in transactions if t.amount > 0), 2
            )
            mismatches.append(
                (abs(actual_payments - expected["payments"]), expected["payments"])
            )

        if not mismatches:
            return (0.0, 0.0)
        return max(mismatches, key=lambda x: x[0])


class AppleCardParser(BaseParser):
    """Parser for Apple Card statements.

    Transactions have Daily Cash columns: MM/DD/YYYY desc N% $cashback $amount
    Payments: MM/DD/YYYY desc -$amount
    """

    # Transaction with Daily Cash: date desc N% $cashback $amount
    TX_RE = re.compile(
        r"^(\d{2}/\d{2}/\d{4})\s+(.+)\s+\d+%\s+\$[\d,.]+\s+\$([\d,.]+)$"
    )
    # Payment: date desc -$amount
    PAY_RE = re.compile(r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?\$[\d,.]+)$")

    def extract_balance_summary(self, text: str) -> dict | None:
        prev = re.search(r"Previous Monthly Balance\s+\$?([\d,]+\.\d{2})", text)
        # Apple uses "minimum payment balance of $X" for new balance
        new = re.search(
            r"minimum payment balance of \$?([\d,]+\.\d{2})", text
        )
        if not new:
            # Fallback: Apple Card transactions amount
            new = re.search(
                r"Apple Card transactions\s+\$?([\d,]+\.\d{2})", text
            )
        # Monthly Installments (device plans) affect balance but aren't
        # in the regular transaction section — must be accounted for
        installments = re.search(
            r"Apple Card Monthly Installments\s+\$?([\d,]+\.\d{2})", text
        )
        if prev and new:
            result = {
                "previous_balance": float(prev.group(1).replace(",", "")),
                "new_balance": float(new.group(1).replace(",", "")),
            }
            if installments:
                result["installments"] = float(
                    installments.group(1).replace(",", "")
                )
            return result
        return None

    def __init__(self, pdf_path: Path, config: CardConfig):
        super().__init__(pdf_path, config)
        self._expected_charges: float | None = None
        self._expected_payments: float | None = None

    def extract_statement_date(self) -> date:
        match = re.search(r"Apple Card Statement - (\w+) (\d{4})", self.pdf_path.name)
        if not match:
            raise ValueError(f"Cannot parse statement date from: {self.pdf_path.name}")
        month_name = match.group(1)
        year = int(match.group(2))
        month = datetime.strptime(month_name, "%B").month
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, last_day)

    def extract_transactions(self, text: str | None = None) -> tuple[list[Transaction], list[str]]:
        if text is None:
            text = self._extract_full_text()
        transactions = []
        warnings = []

        section = None  # 'payments' or 'transactions'
        self._expected_charges = None
        self._expected_payments = None

        for line in text.split("\n"):
            line = line.strip()

            # Section headers
            if line == "Payments":
                section = "payments"
                continue
            elif line == "Transactions":
                section = "transactions"
                continue
            elif line in (
                "Apple Card Monthly Installments",
                "Daily Cash",
                "Legal",
            ):
                section = None
                continue

            # Extract expected totals for validation
            m = re.match(
                r"Total charges, credits and returns\s+\$?([\d,.]+)", line
            )
            if m:
                self._expected_charges = float(m.group(1).replace(",", ""))
                continue
            m = re.match(
                r"Total payments for this period\s+(-?\$?[\d,.]+)", line
            )
            if m:
                self._expected_payments = abs(
                    float(m.group(1).replace("$", "").replace(",", ""))
                )
                continue

            if section is None:
                continue

            # Skip non-transaction lines
            if line.startswith("Date") or line.startswith("Total") or line.startswith("If "):
                continue

            if section == "transactions":
                m = self.TX_RE.match(line)
                if m:
                    tx_date = datetime.strptime(m.group(1), "%m/%d/%Y").date()
                    desc = m.group(2).strip()
                    # Remove trailing Daily Cash percentage from description
                    desc = re.sub(r"\s+\d+$", "", desc)
                    amount = float(m.group(3).replace(",", ""))
                    transactions.append(
                        Transaction(
                            date=tx_date, description=desc, amount=round(-amount, 2)
                        )
                    )
                else:
                    # Returns/credits in transactions section have no Daily Cash
                    # e.g., "02/06/2024 REI #116 ... (RETURN) -$55.05"
                    m = self.PAY_RE.match(line)
                    if m:
                        tx_date = datetime.strptime(m.group(1), "%m/%d/%Y").date()
                        desc = m.group(2).strip()
                        amount_str = m.group(3).replace("$", "").replace(",", "")
                        amount = float(amount_str)
                        transactions.append(
                            Transaction(
                                date=tx_date,
                                description=desc,
                                amount=round(-amount, 2),
                            )
                        )

            elif section == "payments":
                m = self.PAY_RE.match(line)
                if m:
                    tx_date = datetime.strptime(m.group(1), "%m/%d/%Y").date()
                    desc = m.group(2).strip()
                    amount_str = m.group(3).replace("$", "").replace(",", "")
                    amount = float(amount_str)
                    # Payments are negative in PDF -> negate -> positive in CSV
                    transactions.append(
                        Transaction(
                            date=tx_date, description=desc, amount=round(-amount, 2)
                        )
                    )

        return transactions, warnings

    def compute_mismatch(self, transactions: list[Transaction]) -> tuple[float, float]:
        mismatches = []

        if self._expected_charges is not None:
            tx_amounts = [
                t.amount for t in transactions
                if not any(kw in t.description.upper() for kw in ("ACH DEPOSIT", "PAYMENT"))
            ]
            actual_net = round(sum(-a for a in tx_amounts), 2)
            mismatches.append(
                (abs(actual_net - self._expected_charges), self._expected_charges)
            )

        if self._expected_payments is not None and self._expected_payments > 0:
            actual_payments = round(
                sum(
                    t.amount for t in transactions
                    if any(kw in t.description.upper() for kw in ("ACH DEPOSIT", "PAYMENT"))
                ),
                2,
            )
            mismatches.append(
                (abs(actual_payments - self._expected_payments), self._expected_payments)
            )

        if not mismatches:
            return (0.0, 0.0)
        return max(mismatches, key=lambda x: x[0])


class FidelityParser(BaseParser):
    """Parser for Fidelity credit card statements (Rewards and Credit Card).

    Two-date format: MM/DD MM/DD REF# Description $Amount[CR]
    Interest: MM/DD Description $Amount
    """

    # Two-date transaction: post_date trans_date ref# desc $amount[CR]
    TX_RE = re.compile(
        r"^(\d{2}/\d{2})\s+(\d{2}/\d{2})\s+\S+\s+(.+?)\s+\$([\d,]+\.\d{2})(CR)?$"
    )
    # Single-date: MM/DD [optional ref#] desc $amount[CR]
    # Used for credit/debit adjustments, charge-offs, interest charges, fees
    ALT_RE = re.compile(
        r"^(\d{2}/\d{2})\s+(?:\d{2,}\s+)?(.+?)\s+\$([\d,]+\.\d{2})(CR)?$"
    )

    def __init__(self, pdf_path: Path, config: CardConfig):
        super().__init__(pdf_path, config)
        self._expected_credits: float | None = None
        self._expected_debits: float | None = None
        self._expected_interest: float | None = None
        self._expected_fees: float | None = None

    def extract_balance_summary(self, text: str) -> dict | None:
        # "Previous Balance + $2,856.09" or "Previous Balance - $4,444.97CR"
        prev = re.search(
            r"Previous Balance\s*[+-]?\s*\$?([\d,]+\.\d{2})(CR)?", text
        )
        new = re.search(r"New Balance\s*=\s*\$?([\d,]+\.\d{2})(CR)?", text)
        if prev and new:
            prev_val = float(prev.group(1).replace(",", ""))
            if prev.group(2) == "CR" or (
                "Previous Balance -" in text.split("Previous Balance")[1][:20]
            ):
                prev_val = -prev_val
            new_val = float(new.group(1).replace(",", ""))
            if new.group(2) == "CR":
                new_val = -new_val
            return {
                "previous_balance": prev_val,
                "new_balance": new_val,
            }
        return None

    def extract_statement_date(self) -> date:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", self.pdf_path.name)
        if not match:
            raise ValueError(f"Cannot parse statement date from: {self.pdf_path.name}")
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()

    def extract_transactions(self, text: str | None = None) -> tuple[list[Transaction], list[str]]:
        if text is None:
            text = self._extract_full_text()
        stmt_date = self.extract_statement_date()
        transactions = []
        warnings = []

        section = None  # 'credits', 'debits', 'interest'
        self._expected_credits = None
        self._expected_debits = None
        self._expected_interest = None
        self._expected_fees = None

        for line in text.split("\n"):
            line = line.strip()

            # Section detection
            if "Payments and Other Credits" in line:
                section = "credits"
                continue
            elif "Purchases and Other Debits" in line:
                section = "debits"
                continue
            elif re.match(r"^Interest Charged$", line):
                section = "interest"
                continue
            elif line.startswith("End of Statement") or "Interest Charge Calculation" in line:
                section = None
                continue

            # Extract expected totals from TOTAL lines
            total_match = re.match(
                r"TOTAL (?:THIS PERIOD|INTEREST THIS PERIOD|FEES THIS PERIOD)\s+\$?([\d,]+\.\d{2})(CR)?",
                line,
            )
            if total_match:
                total_val = float(total_match.group(1).replace(",", ""))
                if "FEES THIS PERIOD" in line:
                    self._expected_fees = total_val
                elif "INTEREST THIS PERIOD" in line:
                    self._expected_interest = total_val
                elif section == "credits":
                    self._expected_credits = total_val
                elif section == "debits":
                    self._expected_debits = total_val
                continue

            if section is None:
                continue

            # Skip headers, totals, continuation lines
            if any(
                line.startswith(prefix)
                for prefix in ("Post", "Date", "TOTAL", "Continued")
            ):
                continue
            if any(
                skip in line
                for skip in (
                    "MERCHANDISE/SERVICE RETURN",
                    "CREDIT ADJUSTMENT",
                    "DEBIT ADJUSTMENT",
                )
            ):
                continue
            if "Year-to-Date" in line:
                section = None
                continue

            # Try two-date pattern (normal transactions)
            m = self.TX_RE.match(line)
            if m:
                trans_date_str = m.group(2)  # transaction date, not post date
                desc = m.group(3).strip()
                amount = float(m.group(4).replace(",", ""))
                is_credit = m.group(5) == "CR"

                tx_month, tx_day = int(trans_date_str[:2]), int(trans_date_str[3:5])
                year = self._infer_year(tx_month, stmt_date)

                try:
                    tx_date = date(year, tx_month, tx_day)
                except ValueError:
                    warnings.append(
                        f"Invalid date {year}-{tx_month:02d}-{tx_day:02d} in {self.pdf_path.name}"
                    )
                    continue

                csv_amount = round(amount if is_credit else -amount, 2)
                transactions.append(
                    Transaction(date=tx_date, description=desc, amount=csv_amount)
                )
                continue

            # Try single-date pattern (adjustments, charge-offs, interest, fees)
            m = self.ALT_RE.match(line)
            if m:
                date_str = m.group(1)
                desc = m.group(2).strip()
                amount = float(m.group(3).replace(",", ""))
                is_credit = m.group(4) == "CR"

                # Skip zero-amount entries (e.g., CHARGE OFF $0.00CR)
                if amount == 0:
                    continue

                tx_month, tx_day = int(date_str[:2]), int(date_str[3:5])
                year = self._infer_year(tx_month, stmt_date)

                # For single-date entries, use the section context to determine
                # credit vs debit if CR flag is ambiguous
                if section == "credits" and not is_credit:
                    # Some credits section entries don't have CR suffix
                    is_credit = True

                try:
                    tx_date = date(year, tx_month, tx_day)
                except ValueError:
                    continue

                csv_amount = round(amount if is_credit else -amount, 2)
                transactions.append(
                    Transaction(date=tx_date, description=desc, amount=csv_amount)
                )

        return transactions, warnings

    def compute_mismatch(self, transactions: list[Transaction]) -> tuple[float, float]:
        mismatches = []

        expected_total_debits = (self._expected_debits or 0) + (self._expected_fees or 0)
        if expected_total_debits > 0:
            actual_debits = round(
                sum(
                    -t.amount
                    for t in transactions
                    if t.amount < 0 and "INTEREST" not in t.description.upper()
                ),
                2,
            )
            mismatches.append(
                (abs(actual_debits - expected_total_debits), expected_total_debits)
            )

        if self._expected_credits is not None:
            actual_credits = round(
                sum(t.amount for t in transactions if t.amount > 0), 2
            )
            mismatches.append(
                (abs(actual_credits - self._expected_credits), self._expected_credits)
            )

        if self._expected_interest is not None and self._expected_interest > 0:
            actual_interest = round(
                sum(
                    -t.amount
                    for t in transactions
                    if t.amount < 0 and "INTEREST" in t.description.upper()
                ),
                2,
            )
            mismatches.append(
                (abs(actual_interest - self._expected_interest), self._expected_interest)
            )

        if not mismatches:
            return (0.0, 0.0)
        return max(mismatches, key=lambda x: x[0])


class BankOfAmericaParser(BaseParser):
    """Parser for Bank of America credit card statements.

    Transaction format: MM/DD MM/DD Description RefNum AcctSuffix Amount
    - Payments section: amounts are negative in PDF
    - Purchases section: amounts are positive in PDF
    - Fees: positive, may lack separate refnum
    - Interest: positive, no refnum or account number
    - Sign convention: negate all raw amounts (charges->negative, payments->positive)
    - account_suffix from CardConfig anchors the regex; defaults to \\d{4} if not set
    """

    # Interest-style: date date desc amount (no refnum, no account) — not suffix-dependent
    INT_RE = re.compile(
        r"^(\d{2}/\d{2})\s+\d{2}/\d{2}\s+(.+?)\s+([-]?[\d,]+\.\d{2})\s*$"
    )

    def extract_balance_summary(self, text: str) -> dict | None:
        prev = re.search(r"Previous Balance\s+\$?([\d,]+\.\d{2})", text)
        # BofA uses "New Balance Total" which can be negative (credit)
        new = re.search(r"New Balance Total\s+[-]?\$?([\d,]+\.\d{2})", text)
        if prev and new:
            prev_val = float(prev.group(1).replace(",", ""))
            new_val = float(new.group(1).replace(",", ""))
            # Check for negative/credit balance
            new_match = re.search(r"New Balance Total\s+(-)\$?[\d,]+\.\d{2}", text)
            if new_match:
                new_val = -new_val
            return {
                "previous_balance": prev_val,
                "new_balance": new_val,
            }
        return None

    def __init__(self, pdf_path: Path, config: CardConfig):
        super().__init__(pdf_path, config)
        self._expected_purchases: float | None = None
        self._expected_payments: float | None = None
        self._expected_fees: float | None = None
        self._expected_interest: float | None = None
        self._expected_balance_transfers: float | None = None
        # Build suffix-dependent regexes from config (or use \d{4} for any 4-digit suffix)
        suffix = config.account_suffix or r"\d{4}"
        # Standard transaction: date date desc refnum suffix amount
        self.TX_RE = re.compile(
            rf"^(\d{{2}}/\d{{2}})\s+\d{{2}}/\d{{2}}\s+(.+?)\s+\d{{3,5}}\s+{suffix}\s+([-]?[\d,]+\.\d{{2}})\s*$"
        )
        # Fee-style: date date desc suffix amount (no separate refnum)
        self.FEE_RE = re.compile(
            rf"^(\d{{2}}/\d{{2}})\s+\d{{2}}/\d{{2}}\s+(.+?)\s+{suffix}\s+([-]?[\d,]+\.\d{{2}})\s*$"
        )

    def extract_statement_date(self) -> date:
        match = re.search(r"eStmt_(\d{4}-\d{2}-\d{2})\.pdf", self.pdf_path.name)
        if not match:
            raise ValueError(f"Cannot parse statement date from: {self.pdf_path.name}")
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()

    def extract_transactions(self, text: str | None = None) -> tuple[list[Transaction], list[str]]:
        if text is None:
            text = self._extract_full_text()
        stmt_date = self.extract_statement_date()
        transactions = []
        warnings = []

        # Reset expected totals
        self._expected_purchases = None
        self._expected_payments = None
        self._expected_fees = None
        self._expected_interest = None

        # Extract expected totals from page 1 summary (first occurrence in text)
        m = re.search(r"Purchases and Adjustments\s+[-]?\$?([\d,]+\.\d{2})", text)
        if m:
            self._expected_purchases = float(m.group(1).replace(",", ""))
        m = re.search(r"Payments and Other Credits\s+[-]?\$?([\d,]+\.\d{2})", text)
        if m:
            self._expected_payments = float(m.group(1).replace(",", ""))
        m = re.search(r"Fees Charged\s+\$?([\d,]+\.\d{2})", text)
        if m:
            self._expected_fees = float(m.group(1).replace(",", ""))
        m = re.search(r"Interest Charged\s+\$?([\d,]+\.\d{2})", text)
        if m:
            self._expected_interest = float(m.group(1).replace(",", ""))
        m = re.search(r"Balance Transfers\s+\$([\d,]+\.\d{2})", text)
        if m:
            self._expected_balance_transfers = float(m.group(1).replace(",", ""))

        section = None
        in_transactions = False

        for line in text.split("\n"):
            line = line.strip()

            # Detect start of Transactions area (page 3+)
            if line in ("Transactions", "Transactions Continued"):
                in_transactions = True
                continue

            if not in_transactions:
                continue

            # Stop markers
            if "Year-to-Date" in line or "Interest Charge Calculation" in line:
                in_transactions = False
                section = None
                continue

            # Section detection (these appear WITHOUT amounts, unlike page 1 summary)
            if line == "Payments and Other Credits":
                section = "payments"
                continue
            elif line == "Purchases and Adjustments":
                section = "purchases"
                continue
            elif line == "Balance Transfers":
                section = "balance_transfers"
                continue
            elif line == "Fees":
                section = "fees"
                continue
            elif line == "Interest Charged":
                section = "interest"
                continue

            # Skip headers, totals, continuation markers
            if line.startswith("TOTAL") or line.startswith("Transaction") or line.startswith("Date"):
                continue
            if line.startswith("continued") or line.startswith("Page "):
                continue

            if section is None:
                continue

            # Skip zero-amount interest placeholders
            if section == "interest" and line.endswith("0.00"):
                continue

            # Try matching patterns in order of specificity
            m = self.TX_RE.match(line)
            if not m:
                m = self.FEE_RE.match(line)
            if not m:
                m = self.INT_RE.match(line)
            if not m:
                continue

            date_str = m.group(1)
            desc = m.group(2).strip()
            raw_amount = float(m.group(3).replace(",", ""))

            tx_month, tx_day = int(date_str[:2]), int(date_str[3:5])
            year = self._infer_year(tx_month, stmt_date)

            try:
                tx_date = date(year, tx_month, tx_day)
            except ValueError:
                warnings.append(
                    f"Invalid date {year}-{tx_month:02d}-{tx_day:02d} in {self.pdf_path.name}"
                )
                continue

            # Negate all raw amounts: purchases positive->negative, payments negative->positive
            csv_amount = round(-raw_amount, 2)
            transactions.append(
                Transaction(date=tx_date, description=desc, amount=csv_amount)
            )

        return transactions, warnings

    def compute_mismatch(self, transactions: list[Transaction]) -> tuple[float, float]:
        mismatches = []

        # Total charges: purchases + fees + interest + balance transfers (all negative in CSV)
        expected_charges = (
            (self._expected_purchases or 0)
            + (self._expected_fees or 0)
            + (self._expected_interest or 0)
            + (self._expected_balance_transfers or 0)
        )
        if expected_charges > 0:
            actual_charges = round(
                sum(-t.amount for t in transactions if t.amount < 0), 2
            )
            mismatches.append(
                (abs(actual_charges - expected_charges), expected_charges)
            )

        # Total payments/credits (positive in CSV)
        if self._expected_payments is not None and self._expected_payments > 0:
            actual_payments = round(
                sum(t.amount for t in transactions if t.amount > 0), 2
            )
            mismatches.append(
                (abs(actual_payments - self._expected_payments), self._expected_payments)
            )

        if not mismatches:
            return (0.0, 0.0)
        return max(mismatches, key=lambda x: x[0])


# --- Parser Registry ---
PARSER_CLASSES = {
    "ChaseParser": ChaseParser,
    "AppleCardParser": AppleCardParser,
    "FidelityParser": FidelityParser,
    "BankOfAmericaParser": BankOfAmericaParser,
}


# --- CSV Writer ---
def write_csv(transactions: list[Transaction], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "description", "amount", "category"])
        for tx in sorted(transactions, key=lambda t: t.date):
            writer.writerow([
                tx.date.isoformat(),
                tx.description,
                f"{tx.amount:.2f}",
                tx.category,
            ])


# --- Mismatch Warning Generation ---
def generate_mismatch_warnings(parser: BaseParser, transactions: list[Transaction]) -> list[str]:
    """Generate human-readable mismatch warnings after retry loop completes.

    Called in process_pdf() instead of inside each parser's extract_transactions(),
    so warnings reflect the best extraction result and aren't duplicated across retries.
    """
    warnings = []

    if isinstance(parser, ChaseParser):
        expected = parser._expected_totals
        expected_total_charges = (
            expected.get("purchases", 0)
            + expected.get("fees", 0)
            + expected.get("interest", 0)
        )
        if expected_total_charges > 0:
            actual_charges = round(
                sum(-t.amount for t in transactions if t.amount < 0), 2
            )
            if abs(actual_charges - expected_total_charges) > 0.02:
                warnings.append(
                    f"Charges total mismatch: parsed ${actual_charges:.2f} "
                    f"vs expected ${expected_total_charges:.2f} "
                    f"(purchases=${expected.get('purchases', 0):.2f} "
                    f"+ fees=${expected.get('fees', 0):.2f} "
                    f"+ interest=${expected.get('interest', 0):.2f})"
                )
        if expected.get("payments") is not None and expected["payments"] > 0:
            actual_payments = round(
                sum(t.amount for t in transactions if t.amount > 0), 2
            )
            if abs(actual_payments - expected["payments"]) > 0.02:
                warnings.append(
                    f"Payment total mismatch: parsed ${actual_payments:.2f} "
                    f"vs expected ${expected['payments']:.2f}"
                )

    elif isinstance(parser, AppleCardParser):
        if parser._expected_charges is not None:
            tx_amounts = [
                t.amount for t in transactions
                if not any(kw in t.description.upper() for kw in ("ACH DEPOSIT", "PAYMENT"))
            ]
            actual_net = round(sum(-a for a in tx_amounts), 2)
            if abs(actual_net - parser._expected_charges) > 0.02:
                warnings.append(
                    f"Charges total mismatch: parsed net ${actual_net:.2f} "
                    f"vs expected ${parser._expected_charges:.2f}"
                )
        if parser._expected_payments is not None and parser._expected_payments > 0:
            actual_payments = round(
                sum(
                    t.amount for t in transactions
                    if any(kw in t.description.upper() for kw in ("ACH DEPOSIT", "PAYMENT"))
                ),
                2,
            )
            if abs(actual_payments - parser._expected_payments) > 0.02:
                warnings.append(
                    f"Payment total mismatch: parsed ${actual_payments:.2f} "
                    f"vs expected ${parser._expected_payments:.2f}"
                )

    elif isinstance(parser, FidelityParser):
        expected_total_debits = (parser._expected_debits or 0) + (parser._expected_fees or 0)
        if expected_total_debits > 0:
            actual_debits = round(
                sum(
                    -t.amount
                    for t in transactions
                    if t.amount < 0 and "INTEREST" not in t.description.upper()
                ),
                2,
            )
            if abs(actual_debits - expected_total_debits) > 0.02:
                warnings.append(
                    f"Charges total mismatch: parsed ${actual_debits:.2f} "
                    f"vs expected ${expected_total_debits:.2f}"
                )
        if parser._expected_credits is not None:
            actual_credits = round(
                sum(t.amount for t in transactions if t.amount > 0), 2
            )
            if abs(actual_credits - parser._expected_credits) > 0.02:
                warnings.append(
                    f"Credits total mismatch: parsed ${actual_credits:.2f} "
                    f"vs expected ${parser._expected_credits:.2f}"
                )
        if parser._expected_interest is not None and parser._expected_interest > 0:
            actual_interest = round(
                sum(
                    -t.amount
                    for t in transactions
                    if t.amount < 0 and "INTEREST" in t.description.upper()
                ),
                2,
            )
            if abs(actual_interest - parser._expected_interest) > 0.02:
                warnings.append(
                    f"Interest total mismatch: parsed ${actual_interest:.2f} "
                    f"vs expected ${parser._expected_interest:.2f}"
                )

    elif isinstance(parser, BankOfAmericaParser):
        expected_charges = (
            (parser._expected_purchases or 0)
            + (parser._expected_fees or 0)
            + (parser._expected_interest or 0)
            + (parser._expected_balance_transfers or 0)
        )
        if expected_charges > 0:
            actual_charges = round(
                sum(-t.amount for t in transactions if t.amount < 0), 2
            )
            if abs(actual_charges - expected_charges) > 0.02:
                bt_str = f" + balance_transfers=${parser._expected_balance_transfers or 0:.2f}" if parser._expected_balance_transfers else ""
                warnings.append(
                    f"Charges total mismatch: parsed ${actual_charges:.2f} "
                    f"vs expected ${expected_charges:.2f} "
                    f"(purchases=${parser._expected_purchases or 0:.2f} "
                    f"+ fees=${parser._expected_fees or 0:.2f} "
                    f"+ interest=${parser._expected_interest or 0:.2f}"
                    f"{bt_str})"
                )
        if parser._expected_payments is not None and parser._expected_payments > 0:
            actual_payments = round(
                sum(t.amount for t in transactions if t.amount > 0), 2
            )
            if abs(actual_payments - parser._expected_payments) > 0.02:
                warnings.append(
                    f"Payment total mismatch: parsed ${actual_payments:.2f} "
                    f"vs expected ${parser._expected_payments:.2f}"
                )

    return warnings


# --- Balance Verification ---
def verify_all_balances(
    processing_log: dict, card_filter: Optional[str] = None
) -> list[dict]:
    """Verify balance consistency across all processed statements.

    For each statement with balance_summary data:
      1. Per-statement check: previous_balance - sum(CSV txns) + installments = new_balance
      2. Chain check: each statement's previous_balance = prior statement's new_balance

    Reads transaction sums from the output CSVs (not DB), so this works
    immediately after ingestion without needing a DB import.

    Returns list of error dicts. Empty list = all checks passed.
    """
    errors = []

    for card_name, card_data in sorted(processing_log.get("cards", {}).items()):
        if card_filter and card_name != card_filter:
            continue

        # Collect statements with balance data, sorted by date
        statements = []
        for filename, result in sorted(card_data.get("processed", {}).items()):
            balance = result.get("balance_summary")
            if not balance:
                continue
            # Read CSV to get transaction sum
            csv_path = OUTPUT_ROOT / card_name / result["output_csv"]
            csv_sum = 0.0
            if csv_path.exists():
                import csv as csv_mod

                with open(csv_path) as f:
                    for row in csv_mod.DictReader(f):
                        csv_sum += float(row["amount"])
                csv_sum = round(csv_sum, 2)

            installments = balance.get("installments", 0)
            expected_new = round(
                balance["previous_balance"] - csv_sum + installments, 2
            )
            diff = abs(expected_new - balance["new_balance"])

            statements.append({
                "source_file": f"{card_name}/{result['output_csv']}",
                "statement_date": result["statement_date"],
                "previous_balance": balance["previous_balance"],
                "new_balance": balance["new_balance"],
                "installments": installments,
                "csv_sum": csv_sum,
                "computed_new": expected_new,
            })

            if diff > 3.0:
                errors.append({
                    "type": "balance_mismatch",
                    "source_file": f"{card_name}/{result['output_csv']}",
                    "previous_balance": balance["previous_balance"],
                    "csv_sum": csv_sum,
                    "computed_new": expected_new,
                    "pdf_new_balance": balance["new_balance"],
                    "diff": diff,
                })

        # Chain check
        statements.sort(key=lambda s: s["statement_date"])
        for i in range(1, len(statements)):
            prev_new = statements[i - 1]["new_balance"]
            curr_prev = statements[i]["previous_balance"]
            diff = abs(prev_new - curr_prev)
            if diff > 0.01:
                errors.append({
                    "type": "chain_break",
                    "statement": statements[i]["source_file"],
                    "expected_previous": prev_new,
                    "actual_previous": curr_prev,
                    "diff": diff,
                })

    return errors


# --- Gap Detection ---
def detect_gaps(card_filter: Optional[str] = None) -> int:
    """Check for missing monthly statements (gaps in the sequence).

    Returns the total number of missing months across all cards.
    """
    total_missing = 0

    for card_name, config in CARD_CONFIGS.items():
        if card_filter and card_name != card_filter:
            continue

        all_pdfs = discover_pdfs(config)
        if len(all_pdfs) < 2:
            continue

        # Extract statement dates from filenames (no PDF read needed)
        parser_cls = PARSER_CLASSES[config.parser_class]
        stmt_months: set[tuple[int, int]] = set()
        for pdf_path, filename in all_pdfs:
            try:
                parser = parser_cls(pdf_path, config)
                stmt_date = parser.extract_statement_date()
                stmt_months.add((stmt_date.year, stmt_date.month))
            except ValueError:
                continue

        if len(stmt_months) < 2:
            continue

        sorted_months = sorted(stmt_months)
        first_y, first_m = sorted_months[0]
        last_y, last_m = sorted_months[-1]

        # Generate all expected months from first to last
        expected: set[tuple[int, int]] = set()
        y, m = first_y, first_m
        while (y, m) <= (last_y, last_m):
            expected.add((y, m))
            m += 1
            if m > 12:
                m = 1
                y += 1

        missing = sorted(expected - stmt_months)
        if missing:
            total_missing += len(missing)
            logger.warning(
                f"\033[31m  {card_name}: {len(missing)} MISSING statement(s) "
                f"(range {first_y}-{first_m:02d} to {last_y}-{last_m:02d}):\033[0m"
            )
            for y, m in missing:
                logger.warning(f"\033[31m    -> {y}-{m:02d}\033[0m")

    return total_missing


# --- Main Processing ---
def process_pdf(pdf_path: Path, config: CardConfig) -> dict:
    """Process a single PDF with retry-on-mismatch. Returns result dict for processing log."""
    parser_cls = PARSER_CLASSES[config.parser_class]
    parser = parser_cls(pdf_path, config)

    stmt_date = parser.extract_statement_date()

    # First attempt: default extraction settings
    default_text = parser._extract_full_text()
    transactions, warnings = parser.extract_transactions(text=default_text)
    abs_mismatch, expected_total = parser.compute_mismatch(transactions)

    best_transactions = transactions
    best_warnings = warnings
    best_mismatch = abs_mismatch
    best_expected = expected_total
    best_settings: dict = {}
    best_text = default_text
    retries = 0

    # Retry with different extraction settings if mismatch exceeds threshold
    if expected_total > 0 and abs_mismatch / expected_total > MISMATCH_THRESHOLD:
        for settings in RETRY_SETTINGS:
            retries += 1
            retry_text = parser._extract_full_text(**settings)
            retry_transactions, retry_warnings = parser.extract_transactions(text=retry_text)
            retry_mismatch, retry_expected = parser.compute_mismatch(retry_transactions)

            logger.debug(
                f"Retry with {settings}: mismatch ${best_mismatch:.2f} -> ${retry_mismatch:.2f}"
            )

            if retry_mismatch < best_mismatch:
                best_transactions = retry_transactions
                best_warnings = retry_warnings
                best_mismatch = retry_mismatch
                best_expected = retry_expected
                best_settings = settings
                best_text = retry_text

            # Stop early on exact match
            if best_mismatch <= 0.01:
                break

    # Log retry improvement
    if retries > 0 and best_settings:
        logger.info(
            f"    Retry improved mismatch: ${abs_mismatch:.2f} -> ${best_mismatch:.2f} "
            f"(settings: {best_settings})"
        )

    # Re-parse with best text to set parser state for warning generation
    if retries > 0:
        parser.extract_transactions(text=best_text)

    # Generate mismatch warnings from best result (after retry loop)
    mismatch_warnings = generate_mismatch_warnings(parser, best_transactions)
    best_warnings.extend(mismatch_warnings)

    transactions = best_transactions
    warnings = best_warnings

    # Date range validation
    for tx in transactions:
        delta = (stmt_date - tx.date).days
        if delta < -5 or delta > 60:
            warnings.append(
                f"Transaction date {tx.date} out of range for statement {stmt_date}"
            )

    # Duplicate detection within statement
    seen = set()
    for tx in transactions:
        key = (tx.date, tx.description, tx.amount)
        if key in seen:
            warnings.append(f"Possible duplicate: {tx.date} {tx.description} {tx.amount}")
        seen.add(key)

    # Write CSV
    output_dir = OUTPUT_ROOT / config.name
    csv_path = output_dir / f"{stmt_date.isoformat()}.csv"
    write_csv(transactions, csv_path)

    total_charges = round(sum(-t.amount for t in transactions if t.amount < 0), 2)
    total_credits = round(sum(t.amount for t in transactions if t.amount > 0), 2)

    # Extract balance summary from PDF for post-import DB validation
    balance_summary = parser.extract_balance_summary(best_text)

    # Self-check: verify balance equation against parsed transactions
    # Credit card balance = what you owe. Payments (positive in CSV) reduce it,
    # charges (negative in CSV) increase it. So: new = previous - sum(txns)
    # Apple Card: installments are charged to balance but not in transaction list
    if balance_summary:
        txn_sum = round(sum(t.amount for t in transactions), 2)
        installments = balance_summary.get("installments", 0)
        expected_new = round(
            balance_summary["previous_balance"] - txn_sum + installments, 2
        )
        balance_diff = abs(expected_new - balance_summary["new_balance"])
        if balance_diff > 3.0:  # allow small PDF text extraction rounding
            warnings.append(
                f"Balance check: previous({balance_summary['previous_balance']}) "
                f"- txns({txn_sum}) + installments({installments}) "
                f"= {expected_new}, expected new_balance={balance_summary['new_balance']} "
                f"(diff=${balance_diff:.2f})"
            )

    # Build verification block
    verification = {
        "mismatch": round(best_mismatch, 2),
        "mismatch_ratio": round(best_mismatch / best_expected, 4) if best_expected > 0 else 0.0,
        "retries": retries,
        "extraction_settings": best_settings,
    }

    result = {
        "statement_date": stmt_date.isoformat(),
        "output_csv": f"{stmt_date.isoformat()}.csv",
        "transaction_count": len(transactions),
        "total_charges": total_charges,
        "total_credits": total_credits,
        "verification": verification,
        "processed_at": datetime.now().isoformat(timespec="seconds"),
        "status": "success",
        "warnings": warnings,
    }
    if balance_summary:
        result["balance_summary"] = balance_summary

    return result


def run_scan(card_filter: Optional[str] = None, force: bool = False):
    """Scan for new PDFs and report counts."""
    processing_log = (
        load_processing_log()
        if not force
        else {"version": 1, "last_run": None, "cards": {}}
    )

    total_new = 0
    total_all = 0

    for card_name, config in CARD_CONFIGS.items():
        if card_filter and card_name != card_filter:
            continue

        all_pdfs = discover_pdfs(config)
        new_pdfs = all_pdfs if force else get_new_pdfs(config, processing_log)

        total_all += len(all_pdfs)
        total_new += len(new_pdfs)

        status = f"  {card_name}: {len(new_pdfs)} new / {len(all_pdfs)} total"
        if new_pdfs:
            logger.info(f"\033[33m{status}\033[0m")
            for pdf_path, filename in new_pdfs[:3]:
                logger.info(f"    -> {filename}")
            if len(new_pdfs) > 3:
                logger.info(f"    ... and {len(new_pdfs) - 3} more")
        else:
            logger.info(status)

    logger.info(f"\n  Total: {total_new} new / {total_all} total PDFs")

    # Gap detection
    logger.info("\n  Checking for missing statements...")
    gap_count = detect_gaps(card_filter=card_filter)
    if gap_count == 0:
        logger.info("  No gaps found.")
    else:
        logger.warning(
            f"\033[31m  {gap_count} missing statement(s) detected! "
            f"Check source PDFs in {SOURCE_ROOT}\033[0m"
        )


def run_ingest(
    card_filter: Optional[str] = None,
    force: bool = False,
    skip_errors: bool = False,
):
    """Process new PDFs and write CSVs."""
    processing_log = (
        load_processing_log()
        if not force
        else {"version": 1, "last_run": None, "cards": {}}
    )

    total_success = 0
    total_errors = 0
    total_warnings = 0

    for card_name, config in CARD_CONFIGS.items():
        if card_filter and card_name != card_filter:
            continue

        new_pdfs = (
            discover_pdfs(config)
            if force
            else get_new_pdfs(config, processing_log, skip_errors=skip_errors)
        )

        if not new_pdfs:
            continue

        logger.info(f"\n  Processing {card_name} ({len(new_pdfs)} PDFs)...")

        if card_name not in processing_log.setdefault("cards", {}):
            processing_log["cards"][card_name] = {"processed": {}, "errors": {}}
        card_log = processing_log["cards"][card_name]

        for pdf_path, filename in new_pdfs:
            try:
                for _attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
                    try:
                        result = process_pdf(pdf_path, config)
                        break
                    except Exception as e:
                        if _attempt == MAX_PARSE_ATTEMPTS:
                            raise
                        print(f"  Attempt {_attempt}/{MAX_PARSE_ATTEMPTS} failed: {e}, retrying...")
                card_log["processed"][filename] = result
                card_log["errors"].pop(filename, None)

                warn_count = len(result["warnings"])
                warn_str = f" \033[33m({warn_count} warnings)\033[0m" if warn_count else ""
                retry_str = ""
                v = result.get("verification", {})
                if v.get("retries", 0) > 0:
                    retry_str = f" [retried {v['retries']}x, mismatch=${v['mismatch']:.2f}]"
                logger.info(
                    f"    OK {filename} -> {result['output_csv']} "
                    f"({result['transaction_count']} txns, "
                    f"charges=${result['total_charges']:.2f}, "
                    f"credits=${result['total_credits']:.2f}){retry_str}{warn_str}"
                )

                for w in result["warnings"]:
                    logger.warning(f"       WARNING: {w}")
                    total_warnings += 1

                total_success += 1

            except Exception as e:
                card_log["errors"][filename] = {
                    "error": str(e),
                    "attempted_at": datetime.now().isoformat(timespec="seconds"),
                }
                logger.error(f"    FAIL {filename}: {e}")
                total_errors += 1

        # Save after each card (incremental progress)
        save_processing_log(processing_log)

    logger.info(
        f"\n  Done: {total_success} succeeded, {total_errors} errors, {total_warnings} warnings"
    )

    # Gap detection after ingestion
    logger.info("\n  Checking for missing statements...")
    gap_count = detect_gaps(card_filter=card_filter)
    if gap_count == 0:
        logger.info("  No gaps found.")
    else:
        logger.warning(
            f"\033[31m  {gap_count} missing statement(s) detected! "
            f"Check source PDFs in {SOURCE_ROOT}\033[0m"
        )

    # Balance verification across all processed statements
    logger.info("\n  Verifying statement balances...")
    balance_errors = verify_all_balances(processing_log, card_filter=card_filter)
    if not balance_errors:
        logger.info("  \033[32mAll balance checks passed.\033[0m")
    else:
        for err in balance_errors:
            if err["type"] == "balance_mismatch":
                logger.warning(
                    f"\033[31m  BALANCE MISMATCH {err['source_file']}: "
                    f"prev({err['previous_balance']}) - txns + installments "
                    f"= {err['computed_new']}, expected {err['pdf_new_balance']} "
                    f"(diff=${err['diff']:.2f})\033[0m"
                )
            elif err["type"] == "chain_break":
                logger.warning(
                    f"\033[31m  CHAIN BREAK at {err['statement']}: "
                    f"prior new_balance={err['expected_previous']} != "
                    f"this previous_balance={err['actual_previous']} "
                    f"(diff=${err['diff']:.2f})\033[0m"
                )
        logger.warning(
            f"\033[31m  {len(balance_errors)} balance issue(s) found!\033[0m"
        )


# --- Year-End Reconciliation ---
def parse_year_end_total(pdf_path: Path) -> tuple[int | None, float | None]:
    """Parse year and total spent from a year-end summary PDF.
    Returns (year, total_spent) or (None, None) if unparseable.
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:2]:
            text = page.extract_text()
            if not text:
                continue
            year_match = re.search(r"(\d{4}) year-end summary", text)
            # Amount may be on same line or next line after "Total spent"
            total_match = re.search(
                r"Total spent[\s\S]*?\$([\d,]+\.\d{2})", text
            )
            if year_match and total_match:
                return (
                    int(year_match.group(1)),
                    float(total_match.group(1).replace(",", "")),
                )
    return None, None


def run_reconcile(card_filter: Optional[str] = None):
    """Reconcile year-end summaries against ingested CSVs."""
    found_any = False

    for card_name, config in CARD_CONFIGS.items():
        if card_filter and card_name != card_filter:
            continue

        source_dir = SOURCE_ROOT / config.source_dir
        if not source_dir.exists():
            continue

        # Find YearEndSummary PDFs
        year_end_pdfs = sorted(source_dir.rglob("YearEndSummary*.pdf"))
        if not year_end_pdfs:
            continue

        found_any = True
        for ye_pdf in year_end_pdfs:
            summary_year, ye_total = parse_year_end_total(ye_pdf)
            if summary_year is None or ye_total is None:
                logger.warning(f"  Could not parse year-end total from {ye_pdf.name}")
                continue

            # Read all CSVs for this card and sum charges for the summary year
            csv_dir = OUTPUT_ROOT / card_name
            if not csv_dir.exists():
                logger.warning(f"  No CSV directory found for {card_name}")
                continue

            csv_total = 0.0
            tx_count = 0
            for csv_file in sorted(csv_dir.glob("*.csv")):
                with open(csv_file) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        tx_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                        if tx_date.year != summary_year:
                            continue
                        amount = float(row["amount"])
                        desc = row["description"].upper()
                        # Year-end "Total spent" = purchases net of refunds,
                        # excluding card payments, fees, and interest
                        if "INTEREST CHARGED" in desc:
                            continue
                        if "ANNUAL FEE" in desc or "LATE FEE" in desc:
                            continue
                        if amount > 0 and "PAYMENT" in desc:
                            continue  # skip actual card payments
                        if amount < 0:
                            csv_total += abs(amount)  # charge
                        else:
                            csv_total -= amount  # refund/credit reduces total
                        tx_count += 1

            csv_total = round(csv_total, 2)
            diff = round(abs(csv_total - ye_total), 2)

            if diff <= 0.02:
                logger.info(
                    f"  {card_name} {summary_year}: MATCH — "
                    f"year-end ${ye_total:,.2f} = CSV ${csv_total:,.2f} ({tx_count} txns)"
                )
            else:
                logger.warning(
                    f"  {card_name} {summary_year}: MISMATCH — "
                    f"year-end ${ye_total:,.2f} vs CSV ${csv_total:,.2f} "
                    f"(diff ${diff:.2f}, {tx_count} txns)"
                )

    if not found_any:
        logger.info("  No year-end summary PDFs found for any card.")


# --- CLI ---
def main():
    parser = argparse.ArgumentParser(
        description="Credit card statement PDF ingestion pipeline",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scan", action="store_true", help="Show new PDFs (no processing)")
    group.add_argument("--run", action="store_true", help="Process new PDFs")
    group.add_argument(
        "--reconcile",
        action="store_true",
        help="Reconcile year-end summaries against ingested CSVs",
    )

    parser.add_argument(
        "--card",
        type=str,
        choices=list(CARD_CONFIGS.keys()),
        help="Process only this card",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-process everything (ignore processing log)",
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="Skip previously errored PDFs",
    )

    args = parser.parse_args()

    setup_logging()
    logger.info(
        f"Credit Card Statement Ingestion — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    if args.scan:
        run_scan(card_filter=args.card, force=args.force)
    elif args.run:
        run_ingest(
            card_filter=args.card, force=args.force, skip_errors=args.skip_errors
        )
    elif args.reconcile:
        run_reconcile(card_filter=args.card)


if __name__ == "__main__":
    main()
