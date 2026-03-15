#!/usr/bin/env python3
"""Payslip PDF ingestion pipeline.

Extracts structured data from payslip PDFs and saves as YAML files.

Supported employers:
  - Salesforce (semi-monthly, including RSU/ESPP/Bonus payslips)
  - ServiceTitan (bi-weekly)
"""

import argparse
import json
import logging
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed. Run: Scripts/venv/bin/pip install pdfplumber", file=sys.stderr)
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: Scripts/venv/bin/pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# --- Path Resolution ---
SCRIPT_DIR = Path(__file__).parent.resolve()
OBSIDIAN_ROOT = SCRIPT_DIR.parent.parent
SOURCE_ROOT = Path.home() / "Dropbox" / "0-FinancialStatements" / "payslips"
OUTPUT_ROOT = OBSIDIAN_ROOT / "Finance" / "payslips"
LOG_FILE = OUTPUT_ROOT / "ingest.log"
PROCESSING_LOG_PATH = OUTPUT_ROOT / "processing_log.json"
MAX_PARSE_ATTEMPTS = 3  # Retry budget for transient PDF parse failures

# --- Logging ---
logger = logging.getLogger("ingest_payslips")


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
class LineItem:
    description: str
    amount: float
    ytd: float
    dates: str = ""
    hours: float = 0.0
    rate: float = 0.0


@dataclass
class DepositInfo:
    bank: str
    account: str
    amount: float


@dataclass
class Payslip:
    employer: str
    employee_id: str
    pay_period_start: str  # YYYY-MM-DD
    pay_period_end: str
    pay_date: str
    pay_type: str  # salary, rsu, espp, bonus, void

    # Summary
    hours_worked: float
    gross_pay: float
    pre_tax_deductions: float
    employee_taxes: float
    post_tax_deductions: float
    net_pay: float

    # YTD summary
    ytd_hours_worked: float = 0.0
    ytd_gross_pay: float = 0.0
    ytd_pre_tax_deductions: float = 0.0
    ytd_employee_taxes: float = 0.0
    ytd_post_tax_deductions: float = 0.0
    ytd_net_pay: float = 0.0

    # Line items
    earnings: list = field(default_factory=list)
    total_earnings: float = 0.0
    employee_taxes_items: list = field(default_factory=list)
    total_employee_taxes: float = 0.0
    pre_tax_items: list = field(default_factory=list)
    total_pre_tax: float = 0.0
    post_tax_items: list = field(default_factory=list)
    total_post_tax: float = 0.0
    employer_benefits: list = field(default_factory=list)
    total_employer_benefits: float = 0.0

    # Deposit
    deposit: Optional[DepositInfo] = None

    # Validation
    validation: dict = field(default_factory=dict)

    # Source
    source_file: str = ""
    source_pages: list = field(default_factory=list)

    @property
    def dedup_key(self) -> str:
        """5-tuple dedup key: employer|pay_date|period_start|period_end|gross_pay"""
        return f"{self.pay_date}|{self.pay_period_start}|{self.pay_period_end}|{self.gross_pay}"


@dataclass
class EmployerConfig:
    name: str
    source_dir: str
    display_name: str
    employee_id_label: str


# --- Employer Registry ---
EMPLOYER_CONFIGS = {
    "salesforce": EmployerConfig(
        name="salesforce",
        source_dir="Salesforce",
        display_name="Salesforce",
        employee_id_label="Employee ID",
    ),
    "servicetitan": EmployerConfig(
        name="servicetitan",
        source_dir="ServiceTitan",
        display_name="ServiceTitan",
        employee_id_label="Employee ID",
    ),
}


# --- Processing Log ---
def load_processing_log() -> dict:
    if PROCESSING_LOG_PATH.exists():
        with open(PROCESSING_LOG_PATH) as f:
            return json.load(f)
    return {"version": 1, "last_run": None, "employers": {}}


def save_processing_log(log: dict):
    PROCESSING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log["last_run"] = datetime.now().isoformat(timespec="seconds")
    with open(PROCESSING_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


# --- PDF Discovery ---
def discover_pdfs(config: EmployerConfig) -> list[Path]:
    source_dir = SOURCE_ROOT / config.source_dir
    if not source_dir.exists():
        logger.warning(f"Source directory not found: {source_dir}")
        return []
    return sorted(p for p in source_dir.iterdir() if p.suffix.lower() == ".pdf")


# --- Validation ---
TOLERANCE = 0.02


def validate_payslip(ps: Payslip) -> dict:
    """Run 5 arithmetic checks on a payslip. Returns validation dict."""
    checks = {}
    mismatches = []

    # 1. Earnings sum
    if ps.earnings and ps.total_earnings > 0:
        calc = round(sum(e.amount for e in ps.earnings), 2)
        ok = abs(calc - ps.total_earnings) <= TOLERANCE
        checks["earnings_sum_check"] = ok
        if not ok:
            mismatches.append(f"earnings sum: {calc} vs total {ps.total_earnings}")

    # 2. Taxes sum
    if ps.employee_taxes_items:
        calc = round(sum(t.amount for t in ps.employee_taxes_items), 2)
        ok = abs(calc - ps.total_employee_taxes) <= TOLERANCE
        checks["taxes_sum_check"] = ok
        if not ok:
            mismatches.append(f"taxes sum: {calc} vs total {ps.total_employee_taxes}")

    # 3. Pre-tax deductions sum
    if ps.pre_tax_items and ps.total_pre_tax > 0:
        calc = round(sum(d.amount for d in ps.pre_tax_items), 2)
        ok = abs(calc - ps.total_pre_tax) <= TOLERANCE
        checks["pre_tax_sum_check"] = ok
        if not ok:
            mismatches.append(f"pre-tax sum: {calc} vs total {ps.total_pre_tax}")

    # 4. Post-tax deductions sum
    if ps.post_tax_items and ps.total_post_tax > 0:
        calc = round(sum(d.amount for d in ps.post_tax_items), 2)
        ok = abs(calc - ps.total_post_tax) <= TOLERANCE
        checks["post_tax_sum_check"] = ok
        if not ok:
            mismatches.append(f"post-tax sum: {calc} vs total {ps.total_post_tax}")

    # 5. Net pay check: net = gross - pre_tax - taxes - post_tax
    # Some employers (ServiceTitan) use total_earnings instead of gross_pay
    expected_net = round(ps.gross_pay - ps.pre_tax_deductions - ps.employee_taxes - ps.post_tax_deductions, 2)
    expected_net_alt = round(ps.total_earnings - ps.pre_tax_deductions - ps.employee_taxes - ps.post_tax_deductions, 2) if ps.total_earnings > 0 else None
    ok = abs(expected_net - ps.net_pay) <= TOLERANCE
    if not ok and expected_net_alt is not None:
        ok = abs(expected_net_alt - ps.net_pay) <= TOLERANCE
    checks["net_pay_check"] = ok
    if not ok:
        mismatches.append(f"net pay: {expected_net} calculated vs {ps.net_pay} stated")

    checks["mismatches"] = mismatches
    return checks


# --- YAML Writer ---
def payslip_to_dict(ps: Payslip) -> dict:
    """Convert payslip to ordered dict for YAML output."""
    d = {
        "employer": ps.employer,
        "employee_id": ps.employee_id,
        "pay_period_start": ps.pay_period_start,
        "pay_period_end": ps.pay_period_end,
        "pay_date": ps.pay_date,
        "pay_type": ps.pay_type,
    }

    d["summary"] = {
        "current": {
            "hours_worked": ps.hours_worked,
            "gross_pay": ps.gross_pay,
            "pre_tax_deductions": ps.pre_tax_deductions,
            "employee_taxes": ps.employee_taxes,
            "post_tax_deductions": ps.post_tax_deductions,
            "net_pay": ps.net_pay,
        },
        "ytd": {
            "hours_worked": ps.ytd_hours_worked,
            "gross_pay": ps.ytd_gross_pay,
            "pre_tax_deductions": ps.ytd_pre_tax_deductions,
            "employee_taxes": ps.ytd_employee_taxes,
            "post_tax_deductions": ps.ytd_post_tax_deductions,
            "net_pay": ps.ytd_net_pay,
        },
    }

    def items_to_list(items):
        result = []
        for item in items:
            entry = {"description": item.description, "amount": item.amount, "ytd": item.ytd}
            if item.dates:
                entry["dates"] = item.dates
            if item.hours:
                entry["hours"] = item.hours
            if item.rate:
                entry["rate"] = item.rate
            return_entry = {}
            # Ensure description first
            return_entry["description"] = entry["description"]
            if "dates" in entry:
                return_entry["dates"] = entry["dates"]
            if "hours" in entry:
                return_entry["hours"] = entry["hours"]
            if "rate" in entry:
                return_entry["rate"] = entry["rate"]
            return_entry["amount"] = entry["amount"]
            return_entry["ytd"] = entry["ytd"]
            result.append(return_entry)
        return result

    d["earnings"] = items_to_list(ps.earnings)
    d["total_earnings"] = ps.total_earnings

    d["employee_taxes"] = items_to_list(ps.employee_taxes_items)
    d["total_employee_taxes"] = ps.total_employee_taxes

    d["pre_tax_deductions"] = items_to_list(ps.pre_tax_items)
    d["total_pre_tax_deductions"] = ps.total_pre_tax

    d["post_tax_deductions"] = items_to_list(ps.post_tax_items)
    d["total_post_tax_deductions"] = ps.total_post_tax

    d["employer_paid_benefits"] = items_to_list(ps.employer_benefits)
    d["total_employer_paid_benefits"] = ps.total_employer_benefits

    if ps.deposit:
        d["deposit"] = {
            "bank": ps.deposit.bank,
            "account": ps.deposit.account,
            "amount": ps.deposit.amount,
        }

    d["validation"] = ps.validation

    d["source"] = {
        "file": ps.source_file,
        "pages": ps.source_pages,
        "processed_at": datetime.now().isoformat(timespec="seconds"),
    }

    return d


def write_yaml(ps: Payslip, output_dir: Path) -> Path:
    """Write payslip to YAML file. Returns output path."""
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = ps.pay_date
    output_path = output_dir / f"{base_name}.yaml"

    # Handle collisions (e.g., RSU + salary on same pay date)
    if output_path.exists():
        suffix = 2
        while True:
            output_path = output_dir / f"{base_name}-{suffix}.yaml"
            if not output_path.exists():
                break
            suffix += 1

    d = payslip_to_dict(ps)

    # Custom YAML representer for floats to avoid scientific notation
    def float_representer(dumper, value):
        if value == int(value):
            return dumper.represent_scalar("tag:yaml.org,2002:float", f"{value:.2f}")
        return dumper.represent_scalar("tag:yaml.org,2002:float", f"{value:.2f}")

    yaml.add_representer(float, float_representer)

    with open(output_path, "w") as f:
        yaml.dump(d, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return output_path


# --- Parsers ---
class BaseParser(ABC):
    def __init__(self, config: EmployerConfig):
        self.config = config

    @abstractmethod
    def extract_payslips(self, pdf_path: Path) -> list[Payslip]:
        """Extract all payslips from a PDF file."""
        ...

    def _parse_amount(self, s: str) -> float:
        """Parse dollar amount string, handling commas and parens."""
        s = s.strip().replace(",", "").replace("$", "")
        if s.startswith("(") and s.endswith(")"):
            return -float(s[1:-1])
        if not s or s == "-":
            return 0.0
        return float(s)

    def _parse_date(self, s: str) -> str:
        """Convert MM/DD/YYYY to YYYY-MM-DD."""
        parts = s.strip().split("/")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
        return s


# --- Known tax keywords for dual-column splitting ---
TAX_KEYWORDS = [
    "OASDI", "Social Security", "Medicare", "Federal Withholding",
    "WA PFL", "WSPFL", "WACRF", "WACF", "State Withholding",
    "Employee Taxes", "Total Employee",
]

# Regex fragment for dollar amounts (handles negative and comma-separated)
AMT = r"-?[\d,]+\.\d{2}"


def _split_dual_column(line: str, in_section: str) -> tuple[str, str]:
    """Split a dual-column line into left (earnings) and right (taxes) parts.

    Returns (left_part, right_part). Either may be empty.
    """
    # Try to find a tax keyword boundary
    for kw in TAX_KEYWORDS:
        idx = line.find(kw)
        if idx > 0:
            return line[:idx].rstrip(), line[idx:].strip()
        elif idx == 0:
            # Line starts with a tax keyword — entire line is right column
            return "", line

    # No tax keyword found — entire line is left column
    return line, ""


# --- Salesforce Parser ---
class SalesforceParser(BaseParser):
    """Parser for Salesforce payslips.

    Each payslip = 2 pages (earnings statement + payment advice).
    Multi-payslip PDFs are split by detecting "Earnings Statement" headers.
    Dual-column layout: earnings on left, taxes on right.
    """

    # Earnings line: Description [dates] [hours] [rate] amount ytd [tax_desc tax_amt tax_ytd]
    # We parse these after splitting dual columns.

    def extract_payslips(self, pdf_path: Path) -> list[Payslip]:
        payslips = []

        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages
            total_pages = len(pages)

            # Split into page pairs (each payslip = 2 pages)
            i = 0
            while i < total_pages:
                page1_text = pages[i].extract_text() or ""

                if "Earnings Statement" not in page1_text:
                    i += 1
                    continue

                page2_text = ""
                if i + 1 < total_pages:
                    page2_text = pages[i + 1].extract_text() or ""

                page_nums = [i + 1, i + 2] if page2_text else [i + 1]

                try:
                    ps = self._parse_payslip(page1_text, page2_text, pdf_path.name, page_nums)
                    payslips.append(ps)
                except Exception as e:
                    logger.warning(f"Failed to parse payslip at pages {page_nums} in {pdf_path.name}: {e}")

                i += 2

        return payslips

    def _parse_payslip(self, page1: str, page2: str, filename: str, page_nums: list) -> Payslip:
        lines = page1.split("\n")

        # --- Header extraction ---
        period_start = period_end = pay_date = ""
        employee_id = ""
        pay_rate_type = ""

        for line in lines:
            m = re.search(r"Period Beginning:\s*(\d{2}/\d{2}/\d{4})", line)
            if m:
                period_start = self._parse_date(m.group(1))
            m = re.search(r"Period Ending:\s*(\d{2}/\d{2}/\d{4})", line)
            if m:
                period_end = self._parse_date(m.group(1))
            m = re.search(r"Pay Date:\s*(\d{2}/\d{2}/\d{4})", line)
            if m:
                pay_date = self._parse_date(m.group(1))
            m = re.search(r"Employee ID:\s*(\d+)", line)
            if m:
                employee_id = m.group(1)
            if "Pay Rate Type" in line:
                pay_rate_type = line.strip()

        # --- Summary row (Current / YTD) ---
        hours = gross = pre_tax = taxes = post_tax = net = 0.0
        ytd_hours = ytd_gross = ytd_pre_tax = ytd_taxes = ytd_post_tax = ytd_net = 0.0

        for line in lines:
            if line.strip().startswith("Current"):
                nums = re.findall(r"[\d,]+\.\d{2}", line)
                if len(nums) >= 6:
                    hours = self._parse_amount(nums[0])
                    gross = self._parse_amount(nums[1])
                    pre_tax = self._parse_amount(nums[2])
                    taxes = self._parse_amount(nums[3])
                    post_tax = self._parse_amount(nums[4])
                    net = self._parse_amount(nums[5])
            elif line.strip().startswith("YTD"):
                nums = re.findall(r"[\d,]+\.\d{2}", line)
                if len(nums) >= 6:
                    ytd_hours = self._parse_amount(nums[0])
                    ytd_gross = self._parse_amount(nums[1])
                    ytd_pre_tax = self._parse_amount(nums[2])
                    ytd_taxes = self._parse_amount(nums[3])
                    ytd_post_tax = self._parse_amount(nums[4])
                    ytd_net = self._parse_amount(nums[5])

        # --- Determine pay type ---
        pay_type = self._determine_pay_type(lines, pay_rate_type, gross, hours)

        # --- Parse sections ---
        earnings, total_earnings, tax_items, total_taxes = self._parse_earnings_and_taxes(lines)
        pre_tax_items, total_pre_tax_parsed, post_tax_items, total_post_tax_parsed = self._parse_deductions(lines)
        employer_items, total_employer = self._parse_employer_benefits(lines)

        # --- Parse deposit from page 2 ---
        deposit = self._parse_deposit(page2)

        ps = Payslip(
            employer="Salesforce",
            employee_id=employee_id,
            pay_period_start=period_start,
            pay_period_end=period_end,
            pay_date=pay_date,
            pay_type=pay_type,
            hours_worked=hours,
            gross_pay=gross,
            pre_tax_deductions=pre_tax,
            employee_taxes=taxes,
            post_tax_deductions=post_tax,
            net_pay=net,
            ytd_hours_worked=ytd_hours,
            ytd_gross_pay=ytd_gross,
            ytd_pre_tax_deductions=ytd_pre_tax,
            ytd_employee_taxes=ytd_taxes,
            ytd_post_tax_deductions=ytd_post_tax,
            ytd_net_pay=ytd_net,
            earnings=earnings,
            total_earnings=total_earnings,
            employee_taxes_items=tax_items,
            total_employee_taxes=total_taxes,
            pre_tax_items=pre_tax_items,
            total_pre_tax=total_pre_tax_parsed,
            post_tax_items=post_tax_items,
            total_post_tax=total_post_tax_parsed,
            employer_benefits=employer_items,
            total_employer_benefits=total_employer,
            deposit=deposit,
            source_file=filename,
            source_pages=page_nums,
        )

        ps.validation = validate_payslip(ps)
        return ps

    def _determine_pay_type(self, lines: list[str], pay_rate_type: str, gross: float, hours: float) -> str:
        """Determine pay type from payslip content."""
        text = "\n".join(lines)

        if gross == 0.0 and hours == 0.0:
            # Check if it has any earnings at all
            if "Rest Stock Unit Gain" not in text and "Annual Performance" not in text:
                return "void"

        # Check for RSU — look for RSU earnings with current amount
        rsu_match = re.search(r"Rest Stock Unit Gain\s+\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4}\s+\d+\s+\d+\s+([\d,]+\.\d{2})", text)
        if rsu_match:
            rsu_amount = self._parse_amount(rsu_match.group(1))
            if rsu_amount > 0 and rsu_amount == gross:
                return "rsu"

        # RSU without dates (just "Rest Stock Unit Gain 0 0 amount")
        rsu_match2 = re.search(r"Rest Stock Unit Gain\s+0\s+0\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})", text)
        if rsu_match2:
            rsu_current = self._parse_amount(rsu_match2.group(1))
            if rsu_current > 0 and rsu_current == gross:
                return "rsu"

        # Check for bonus-only payslip: Annual Performance Bonus is the primary earning
        # "Salary" may appear as YTD-only line — check if there's a Salary with current dates
        if "Annual Performance" in text:
            has_salary_current = bool(re.search(r"Salary\s+\d{2}/\d{2}/\d{4}", text))
            if not has_salary_current:
                bonus_match = re.search(r"Annual Performance\s+.*?0\s+0\s+([\d,]+\.\d{2})", text)
                if bonus_match:
                    bonus_amount = self._parse_amount(bonus_match.group(1))
                    if bonus_amount > 0 and abs(bonus_amount - gross) < 1.0:
                        return "bonus"

        return "salary"

    def _parse_earnings_and_taxes(self, lines: list[str]) -> tuple[list, float, list, float]:
        """Parse the dual-column Earnings / Employee Taxes section."""
        earnings = []
        tax_items = []
        total_earnings = 0.0
        total_taxes = 0.0
        in_section = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Handle totals row BEFORE section detection (totals line can match header pattern)
            if in_section and ("Total Earnings" in stripped or "Total Employee" in stripped
                              or (stripped.startswith("Earnings") and re.search(r"\d", stripped))):
                left, right = _split_dual_column(stripped, "earnings")

                # "Total Employee" could end up in left if no split happened
                if "Total Employee" in left and "Total Earnings" not in left:
                    right = left
                    left = ""

                if left:
                    nums = re.findall(r"[\d,]+\.\d{2}", left)
                    if nums:
                        total_earnings = self._parse_amount(nums[0])

                if right and ("Total Employee" in right or "Employee Taxes" in right):
                    nums = re.findall(r"[\d,]+\.\d{2}", right)
                    if nums:
                        total_taxes = self._parse_amount(nums[0])

                in_section = False
                continue

            # Detect section start (must NOT contain digits — that would be a totals line)
            if not in_section and ("Earnings Employee Taxes" in stripped or
                                   (stripped.startswith("Earnings") and "Employee Taxes" in stripped)):
                if not re.search(r"\d", stripped):
                    in_section = True
                    continue

            # Skip header row
            if in_section and stripped.startswith("Description") and "Dates" in stripped:
                continue

            # Detect section end
            if in_section and (stripped.startswith("Pre Tax Deductions") or stripped.startswith("Pre Tax")):
                in_section = False
                continue

            if not in_section:
                continue

            # Handle continuation line for "Social Security\n(OASDI)"
            if stripped == "(OASDI)":
                if tax_items:
                    tax_items[-1].description = "Social Security (OASDI)"
                continue

            # Handle "Wellness\nReimbursement" continuation
            if stripped == "Reimbursement" and earnings and "Wellness" in earnings[-1].description:
                earnings[-1].description = "Wellness Reimbursement"
                continue

            # Handle "Annual Performance\nBonus" continuation
            if stripped == "Bonus" and earnings and "Annual Performance" in earnings[-1].description:
                earnings[-1].description = "Annual Performance Bonus"
                continue

            # Handle "and Commission" continuation
            if stripped == "and Commission":
                continue

            # Handle "Taxes" continuation after "Total Employee" on previous line
            if stripped == "Taxes":
                continue

            # Split dual columns
            left, right = _split_dual_column(stripped, "earnings")

            # Parse left column (earnings)
            if left:
                earning = self._parse_earning_line(left)
                if earning:
                    earnings.append(earning)

            # Parse right column (taxes)
            if right:
                tax = self._parse_tax_line(right)
                if tax:
                    tax_items.append(tax)

        return earnings, total_earnings, tax_items, total_taxes

    def _parse_earning_line(self, text: str) -> Optional[LineItem]:
        """Parse a single earnings line."""
        # Pattern: Description [MM/DD/YYYY - MM/DD/YYYY] [hours] [rate] amount ytd
        # Or: Description [MM/DD/YYYY - MM/DD/YYYY] hours rate amount ytd
        # Or: Description [YTD-only amount] (for YTD-only rows on RSU/void payslips)

        # Skip if it's a total line or header
        if text.startswith("Total") or text.startswith("Description"):
            return None

        # Try: desc dates hours rate amount ytd
        m = re.match(
            r"^(.+?)\s+(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$",
            text,
        )
        if m:
            return LineItem(
                description=m.group(1).strip(),
                dates=m.group(2).strip(),
                hours=float(m.group(3)),
                rate=float(m.group(4)),
                amount=self._parse_amount(m.group(5)),
                ytd=self._parse_amount(m.group(6)),
            )

        # Try: desc 0 0 amount ytd (no dates)
        m = re.match(r"^(.+?)\s+0\s+0\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$", text)
        if m:
            return LineItem(
                description=m.group(1).strip(),
                amount=self._parse_amount(m.group(2)),
                ytd=self._parse_amount(m.group(3)),
            )

        # Try: desc ytd-only (for void payslips or RSU where current=0)
        m = re.match(r"^(.+?)\s+([\d,]+\.\d{2})$", text)
        if m:
            desc = m.group(1).strip()
            # Make sure desc doesn't end with a number that could be part of the pattern
            if not re.search(r"\d$", desc.rstrip()):
                return LineItem(
                    description=desc,
                    amount=0.0,
                    ytd=self._parse_amount(m.group(2)),
                )
            # Could be "desc amount" where there's no ytd — try as ytd-only
            return LineItem(
                description=desc,
                amount=0.0,
                ytd=self._parse_amount(m.group(2)),
            )

        return None

    def _parse_tax_line(self, text: str) -> Optional[LineItem]:
        """Parse a single tax line from the right column."""
        if text.startswith("Total") or text.startswith("Description"):
            return None

        # Pattern: Description amount ytd (amounts can be negative)
        m = re.match(rf"^(.+?)\s+({AMT})\s+({AMT})$", text)
        if m:
            return LineItem(
                description=m.group(1).strip(),
                amount=self._parse_amount(m.group(2)),
                ytd=self._parse_amount(m.group(3)),
            )

        # YTD-only (for void/RSU payslips where current=0)
        m = re.match(rf"^(.+?)\s+({AMT})$", text)
        if m:
            return LineItem(
                description=m.group(1).strip(),
                amount=0.0,
                ytd=self._parse_amount(m.group(2)),
            )

        return None

    def _parse_deductions(self, lines: list[str]) -> tuple[list, float, list, float]:
        """Parse Pre Tax Deductions and Post Tax Deductions sections."""
        pre_tax_items = []
        post_tax_items = []
        total_pre_tax = 0.0
        total_post_tax = 0.0

        in_section = False
        section_type = None  # 'pre' or 'post' or 'both'

        for line in lines:
            stripped = line.strip()

            # Handle totals BEFORE section detection (totals line matches section pattern)
            if "Total Pre Tax" in stripped or "Total Post Tax" in stripped:
                pre_m = re.search(r"Total Pre Tax Deductions\s+([\d,]+\.\d{2})", stripped)
                post_m = re.search(r"Total Post Tax Deductions\s+([\d,]+\.\d{2})", stripped)
                if pre_m:
                    total_pre_tax = self._parse_amount(pre_m.group(1))
                if post_m:
                    total_post_tax = self._parse_amount(post_m.group(1))
                in_section = False
                continue

            # Detect dual-column deductions header (must not contain "Total")
            if not in_section and "Pre Tax Deductions" in stripped and "Post Tax Deductions" in stripped:
                in_section = True
                section_type = "both"
                continue

            # Skip header row
            if in_section and stripped.startswith("Description") and "Amount" in stripped:
                continue

            # Detect section end
            if in_section and (
                stripped.startswith("Employer Paid Benefits")
                or stripped.startswith("Taxable")
                or stripped.startswith("Federal State")
            ):
                in_section = False
                continue

            if not in_section:
                continue

            if section_type == "both":
                # Split by known post-tax deduction keywords
                left, right = self._split_deduction_columns(stripped)

                if left:
                    item = self._parse_deduction_line(left)
                    if item:
                        pre_tax_items.append(item)

                if right:
                    item = self._parse_deduction_line(right)
                    if item:
                        post_tax_items.append(item)
            elif section_type == "pre":
                item = self._parse_deduction_line(stripped)
                if item:
                    pre_tax_items.append(item)
            elif section_type == "post":
                item = self._parse_deduction_line(stripped)
                if item:
                    post_tax_items.append(item)

        return pre_tax_items, total_pre_tax, post_tax_items, total_post_tax

    def _split_deduction_columns(self, line: str) -> tuple[str, str]:
        """Split a dual-column deductions line into left (pre-tax) and right (post-tax)."""
        # Known post-tax keywords
        post_tax_keywords = [
            "Child Supp AD&D",
            "EE Supp AD&D",
            "401(k) After Tax",
            "Child Suppl Life",
            "ESPP",
            "Metlife Legal",
            "RSU After Tax",
            "401(k) Roth",
        ]

        for kw in post_tax_keywords:
            idx = line.find(kw)
            if idx > 0:
                return line[:idx].rstrip(), line[idx:].strip()
            elif idx == 0:
                # Line starts with post-tax keyword — entire line is post-tax
                return "", line

        # No split found — check if the line starts with a pre-tax keyword
        pre_tax_keywords = ["Dental", "FSA", "EE Hlth", "Medical", "401(k)"]
        for kw in pre_tax_keywords:
            if line.startswith(kw):
                return line, ""

        return line, ""

    def _parse_deduction_line(self, text: str) -> Optional[LineItem]:
        """Parse a single deduction line."""
        if text.startswith("Total") or text.startswith("Description"):
            return None

        # Pattern: Description [date-range] amount ytd (amounts can be negative)
        m = re.match(rf"^(.+?)\s+({AMT})\s+({AMT})$", text)
        if m:
            return LineItem(
                description=m.group(1).strip(),
                amount=self._parse_amount(m.group(2)),
                ytd=self._parse_amount(m.group(3)),
            )

        # YTD-only
        m = re.match(rf"^(.+?)\s+({AMT})$", text)
        if m:
            return LineItem(
                description=m.group(1).strip(),
                amount=0.0,
                ytd=self._parse_amount(m.group(2)),
            )

        return None

    def _parse_employer_benefits(self, lines: list[str]) -> tuple[list, float]:
        """Parse Employer Paid Benefits section."""
        items = []
        total = 0.0
        in_section = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("Employer Paid Benefits"):
                in_section = True
                continue

            if in_section and stripped.startswith("Description") and "Amount" in stripped:
                continue

            if in_section and (
                stripped.startswith("Taxable")
                or stripped.startswith("Federal State")
                or stripped.startswith("Marital")
                or stripped.startswith("Allowances")
            ):
                in_section = False
                continue

            if not in_section:
                continue

            if "Total Employer Paid Benefits" in stripped:
                nums = re.findall(r"[\d,]+\.\d{2}", stripped)
                if nums:
                    total = self._parse_amount(nums[0])
                in_section = False
                continue

            item = self._parse_deduction_line(stripped)
            if item:
                items.append(item)

        return items, total

    def _parse_deposit(self, page2: str) -> Optional[DepositInfo]:
        """Parse deposit information from page 2."""
        if not page2:
            return None

        # Look for amount on the deposit line
        # Pattern varies: "UMB, NA UMB, NA ******4983 ******4983 2,032.54 USD"
        # Or: "0.00 USD" (for RSU/void)
        m = re.search(r"([\d,]+\.\d{2})\s+USD", page2)
        amount = self._parse_amount(m.group(1)) if m else 0.0

        # Extract bank name and account
        bank = ""
        account = ""
        m = re.search(r"(UMB,?\s*NA)", page2)
        if m:
            bank = "UMB, NA"
        m = re.search(r"(\*{4,}\d+)", page2)
        if m:
            account = m.group(1)

        return DepositInfo(bank=bank, account=account, amount=amount)


# --- ServiceTitan Parser ---
class ServiceTitanParser(BaseParser):
    """Parser for ServiceTitan payslips.

    Each PDF = single page, single payslip.
    Dual-column layout: earnings on left, taxes on right.
    """

    def extract_payslips(self, pdf_path: Path) -> list[Payslip]:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return []
            text = pdf.pages[0].extract_text() or ""

        try:
            ps = self._parse_payslip(text, pdf_path.name)
            return [ps]
        except Exception as e:
            logger.warning(f"Failed to parse {pdf_path.name}: {e}")
            return []

    def _parse_payslip(self, text: str, filename: str) -> Payslip:
        lines = text.split("\n")

        # --- Header ---
        employee_id = ""
        period_start = period_end = pay_date = ""

        for line in lines:
            # Header is on a single dense line:
            # "Yi Chen ServiceTitan, Inc. 1400006870 02/09/2026 02/22/2026 02/27/2026"
            m = re.search(r"(\d{10,})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})", line)
            if m:
                employee_id = m.group(1)
                period_start = self._parse_date(m.group(2))
                period_end = self._parse_date(m.group(3))
                pay_date = self._parse_date(m.group(4))
                break

        # --- Summary row ---
        hours = gross = pre_tax = taxes = post_tax = net = 0.0
        ytd_hours = ytd_gross = ytd_pre_tax = ytd_taxes = ytd_post_tax = ytd_net = 0.0

        for line in lines:
            if line.strip().startswith("Current"):
                nums = re.findall(r"[\d,]+\.\d{2}", line)
                if len(nums) >= 6:
                    hours = self._parse_amount(nums[0])
                    gross = self._parse_amount(nums[1])
                    pre_tax = self._parse_amount(nums[2])
                    taxes = self._parse_amount(nums[3])
                    post_tax = self._parse_amount(nums[4])
                    net = self._parse_amount(nums[5])
            elif line.strip().startswith("YTD"):
                nums = re.findall(r"[\d,]+\.\d{2}", line)
                if len(nums) >= 6:
                    ytd_hours = self._parse_amount(nums[0])
                    ytd_gross = self._parse_amount(nums[1])
                    ytd_pre_tax = self._parse_amount(nums[2])
                    ytd_taxes = self._parse_amount(nums[3])
                    ytd_post_tax = self._parse_amount(nums[4])
                    ytd_net = self._parse_amount(nums[5])

        # --- Parse sections ---
        earnings, total_earnings, tax_items, total_taxes = self._parse_earnings_and_taxes(lines)
        pre_tax_items, total_pre_tax_parsed, post_tax_items, total_post_tax_parsed = self._parse_deductions(lines)
        employer_items, total_employer = self._parse_employer_benefits(lines)
        deposit = self._parse_deposit(lines)

        ps = Payslip(
            employer="ServiceTitan",
            employee_id=employee_id,
            pay_period_start=period_start,
            pay_period_end=period_end,
            pay_date=pay_date,
            pay_type="salary",
            hours_worked=hours,
            gross_pay=gross,
            pre_tax_deductions=pre_tax,
            employee_taxes=taxes,
            post_tax_deductions=post_tax,
            net_pay=net,
            ytd_hours_worked=ytd_hours,
            ytd_gross_pay=ytd_gross,
            ytd_pre_tax_deductions=ytd_pre_tax,
            ytd_employee_taxes=ytd_taxes,
            ytd_post_tax_deductions=ytd_post_tax,
            ytd_net_pay=ytd_net,
            earnings=earnings,
            total_earnings=total_earnings,
            employee_taxes_items=tax_items,
            total_employee_taxes=total_taxes,
            pre_tax_items=pre_tax_items,
            total_pre_tax=total_pre_tax_parsed,
            post_tax_items=post_tax_items,
            total_post_tax=total_post_tax_parsed,
            employer_benefits=employer_items,
            total_employer_benefits=total_employer,
            deposit=deposit,
            source_file=filename,
            source_pages=[1],
        )

        ps.validation = validate_payslip(ps)
        return ps

    def _parse_earnings_and_taxes(self, lines: list[str]) -> tuple[list, float, list, float]:
        """Parse dual-column Earnings / Employee Taxes."""
        earnings = []
        tax_items = []
        total_earnings = 0.0
        total_taxes = 0.0
        in_section = False

        for line in lines:
            stripped = line.strip()

            # Handle totals BEFORE section detection (totals line matches header pattern)
            if in_section and (stripped.startswith("Earnings") and re.search(r"\d", stripped)):
                left, right = _split_dual_column(stripped, "earnings")

                # "Employee Taxes" could be the entire left if no earnings split
                if "Employee Taxes" in left and "Earnings " not in left:
                    right = left
                    left = ""

                if left:
                    nums = re.findall(r"[\d,]+\.\d{2}", left)
                    if nums:
                        total_earnings = self._parse_amount(nums[0])

                if right and ("Employee Taxes" in right or "Total Employee" in right):
                    nums = re.findall(r"[\d,]+\.\d{2}", right)
                    if nums:
                        total_taxes = self._parse_amount(nums[0])

                in_section = False
                continue

            # Section start (must NOT contain digits)
            if not in_section and (stripped == "Earnings Employee Taxes" or
                                   (stripped.startswith("Earnings") and "Employee Taxes" in stripped)):
                if not re.search(r"\d", stripped):
                    in_section = True
                    continue

            if in_section and stripped.startswith("Description") and "Dates" in stripped:
                continue

            if in_section and (stripped.startswith("Pre Tax") or stripped.startswith("Employer Paid")):
                in_section = False
                continue

            if not in_section:
                continue

            # Split dual columns
            left, right = _split_dual_column(stripped, "earnings")

            if left:
                earning = self._parse_earning_line(left)
                if earning:
                    earnings.append(earning)

            if right:
                tax = self._parse_tax_line(right)
                if tax:
                    tax_items.append(tax)

        return earnings, total_earnings, tax_items, total_taxes

    def _parse_earning_line(self, text: str) -> Optional[LineItem]:
        """Parse a ServiceTitan earnings line."""
        if text.startswith("Total") or text.startswith("Description"):
            return None

        # Pattern: desc MM/DD/YYYY-MM/DD/YYYY hours rate amount ytd
        m = re.match(
            r"^(.+?)\s+(\d{2}/\d{2}/\d{4}-\d{2}/\d{2}/\d{4})\s+(\d+)\s+(\d+(?:\.\d+)?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$",
            text,
        )
        if m:
            return LineItem(
                description=m.group(1).strip(),
                dates=m.group(2).strip(),
                hours=float(m.group(3)),
                rate=float(m.group(4)),
                amount=self._parse_amount(m.group(5)),
                ytd=self._parse_amount(m.group(6)),
            )

        # YTD-only pattern: desc ytd_amount
        m = re.match(r"^(.+?)\s+([\d,]+\.\d{2})$", text)
        if m:
            return LineItem(
                description=m.group(1).strip(),
                amount=0.0,
                ytd=self._parse_amount(m.group(2)),
            )

        return None

    def _parse_tax_line(self, text: str) -> Optional[LineItem]:
        """Parse a tax line."""
        if text.startswith("Total") or text.startswith("Description"):
            return None

        m = re.match(rf"^(.+?)\s+({AMT})\s+({AMT})$", text)
        if m:
            return LineItem(
                description=m.group(1).strip(),
                amount=self._parse_amount(m.group(2)),
                ytd=self._parse_amount(m.group(3)),
            )

        return None

    def _parse_deductions(self, lines: list[str]) -> tuple[list, float, list, float]:
        """Parse deductions sections."""
        pre_tax_items = []
        post_tax_items = []
        total_pre_tax = 0.0
        total_post_tax = 0.0
        in_section = False

        for line in lines:
            stripped = line.strip()

            # Handle totals BEFORE section detection (totals line matches section pattern)
            if "Pre Tax Deductions" in stripped and re.search(r"[\d,]+\.\d{2}", stripped):
                pre_m = re.search(r"Pre Tax Deductions\s+([\d,]+\.\d{2})", stripped)
                post_m = re.search(r"Post Tax Deductions\s+([\d,]+\.\d{2})", stripped)
                if pre_m:
                    total_pre_tax = self._parse_amount(pre_m.group(1))
                if post_m:
                    total_post_tax = self._parse_amount(post_m.group(1))
                in_section = False
                continue

            # Section header: must START with "Pre Tax" (not embedded in summary header)
            # and contain no digits (to distinguish from totals line)
            if not in_section and stripped.startswith("Pre Tax Deductions") and "Post Tax Deductions" in stripped:
                if not re.search(r"\d", stripped):
                    in_section = True
                    continue

            if in_section and stripped.startswith("Description") and "Amount" in stripped:
                continue

            if in_section and (
                stripped.startswith("Employer Paid")
                or stripped.startswith("Taxable")
                or stripped.startswith("Federal State")
            ):
                in_section = False
                continue

            if not in_section:
                continue

            # ServiceTitan deductions: split by post-tax keyword
            left, right = self._split_deduction_columns(stripped)

            if left:
                item = self._parse_deduction_item(left)
                if item:
                    pre_tax_items.append(item)
            if right:
                item = self._parse_deduction_item(right)
                if item:
                    post_tax_items.append(item)

        return pre_tax_items, total_pre_tax, post_tax_items, total_post_tax

    def _split_deduction_columns(self, line: str) -> tuple[str, str]:
        """Split deductions dual column."""
        post_tax_kw = ["401k After Tax", "401(k) After Tax"]
        for kw in post_tax_kw:
            idx = line.find(kw)
            if idx > 0:
                return line[:idx].rstrip(), line[idx:].strip()
        return line, ""

    def _parse_deduction_item(self, text: str) -> Optional[LineItem]:
        if text.startswith("Total") or text.startswith("Description"):
            return None

        m = re.match(rf"^(.+?)\s+({AMT})\s+({AMT})$", text)
        if m:
            return LineItem(
                description=m.group(1).strip(),
                amount=self._parse_amount(m.group(2)),
                ytd=self._parse_amount(m.group(3)),
            )
        return None

    def _parse_employer_benefits(self, lines: list[str]) -> tuple[list, float]:
        items = []
        total = 0.0
        in_section = False

        for line in lines:
            stripped = line.strip()

            # Handle "Employer Paid Benefits" or "Employer Paid Benefits Taxable Wages" header
            if stripped.startswith("Employer Paid Benefits") and not re.search(r"\d", stripped):
                in_section = True
                continue

            if in_section and stripped.startswith("Description") and "Amount" in stripped:
                continue

            # ServiceTitan has "Employer Paid Benefits" and "Taxable Wages" side by side
            if in_section and (
                stripped.startswith("Federal State")
                or stripped.startswith("Marital")
                or stripped.startswith("Payment Information")
            ):
                in_section = False
                continue

            if not in_section:
                continue

            # The employer benefits and taxable wages are dual-column
            # Split at "Taxable Wages" boundary or known taxable keywords
            left = stripped
            right = ""
            for kw in ["Federal Withholding - Taxable", "Taxable Wages"]:
                idx = stripped.find(kw)
                if idx > 0:
                    left = stripped[:idx].rstrip()
                    right = stripped[idx:].strip()
                    break

            if "Employer Paid Benefits" in left and re.search(r"[\d,]+\.\d{2}", left):
                nums = re.findall(r"[\d,]+\.\d{2}", left)
                if nums:
                    total = self._parse_amount(nums[0])
                in_section = False
                continue

            item = self._parse_deduction_item(left)
            if item:
                items.append(item)

        return items, total

    def _parse_deposit(self, lines: list[str]) -> Optional[DepositInfo]:
        """Parse deposit from Payment Information section."""
        in_section = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("Payment Information"):
                in_section = True
                continue
            if stripped.startswith("Bank") and "Account" in stripped:
                continue
            if in_section and re.search(r"[\d,]+\.\d{2}", stripped):
                # Extract amount
                m = re.search(r"([\d,]+\.\d{2})\s+USD", stripped)
                if not m:
                    m = re.search(r"([\d,]+\.\d{2})", stripped)
                amount = self._parse_amount(m.group(1)) if m else 0.0

                # Extract account
                acct_m = re.search(r"(\*{4,}\d+)", stripped)
                account = acct_m.group(1) if acct_m else ""

                # Bank name is garbled in ServiceTitan PDFs
                bank = "Fidelity/UMB"

                return DepositInfo(bank=bank, account=account, amount=amount)

        return None


# --- Parser Registry ---
PARSER_CLASSES = {
    "salesforce": SalesforceParser,
    "servicetitan": ServiceTitanParser,
}


# --- Orchestration ---
def get_employer_log(processing_log: dict, employer: str) -> dict:
    employers = processing_log.setdefault("employers", {})
    if employer not in employers:
        employers[employer] = {"files_scanned": {}, "payslips": {}}
    return employers[employer]


def make_dedup_key(ps: Payslip) -> str:
    return ps.dedup_key


def run_scan(employer_filter: Optional[str] = None, force: bool = False):
    """Scan for PDFs and report what would be processed."""
    processing_log = load_processing_log() if not force else {"version": 1, "last_run": None, "employers": {}}

    total_pdfs = 0
    total_payslips = 0
    total_new = 0

    for emp_name, config in EMPLOYER_CONFIGS.items():
        if employer_filter and emp_name != employer_filter:
            continue

        pdfs = discover_pdfs(config)
        emp_log = get_employer_log(processing_log, emp_name)
        known_keys = set(emp_log.get("payslips", {}).keys())

        logger.info(f"\n  {config.display_name}: {len(pdfs)} PDFs")

        emp_payslip_count = 0
        emp_new_count = 0

        for pdf_path in pdfs:
            parser = PARSER_CLASSES[emp_name](config)
            try:
                payslips = parser.extract_payslips(pdf_path)
                new_count = 0
                for ps in payslips:
                    key = make_dedup_key(ps)
                    if force or key not in known_keys:
                        new_count += 1

                status = f"    {pdf_path.name}: {len(payslips)} payslips"
                if new_count > 0:
                    status += f" ({new_count} new)"
                    logger.info(f"\033[33m{status}\033[0m")
                else:
                    logger.info(status)

                emp_payslip_count += len(payslips)
                emp_new_count += new_count

            except Exception as e:
                logger.error(f"    {pdf_path.name}: ERROR - {e}")

        total_pdfs += len(pdfs)
        total_payslips += emp_payslip_count
        total_new += emp_new_count

    logger.info(f"\n  Total: {total_pdfs} PDFs, {total_payslips} payslips ({total_new} new)")


def run_ingest(
    employer_filter: Optional[str] = None,
    force: bool = False,
    skip_errors: bool = False,
):
    """Process PDFs and write YAML files."""
    processing_log = load_processing_log() if not force else {"version": 1, "last_run": None, "employers": {}}

    total_success = 0
    total_skipped = 0
    total_errors = 0
    total_validation_issues = 0

    for emp_name, config in EMPLOYER_CONFIGS.items():
        if employer_filter and emp_name != employer_filter:
            continue

        pdfs = discover_pdfs(config)
        if not pdfs:
            continue

        emp_log = get_employer_log(processing_log, emp_name)
        known_keys = set(emp_log.get("payslips", {}).keys())
        output_dir = OUTPUT_ROOT / emp_name

        logger.info(f"\n  Processing {config.display_name} ({len(pdfs)} PDFs)...")

        # Track which output files exist for collision handling
        existing_outputs = set()
        if output_dir.exists():
            existing_outputs = {f.name for f in output_dir.iterdir() if f.suffix == ".yaml"}

        for pdf_path in pdfs:
            parser = PARSER_CLASSES[emp_name](config)

            try:
                for _attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
                    try:
                        payslips = parser.extract_payslips(pdf_path)
                        break
                    except Exception as e:
                        if _attempt == MAX_PARSE_ATTEMPTS:
                            raise
                        print(f"  Attempt {_attempt}/{MAX_PARSE_ATTEMPTS} failed: {e}, retrying...")
            except Exception as e:
                logger.error(f"    FAIL {pdf_path.name}: {e}")
                total_errors += 1
                continue

            for ps in payslips:
                key = make_dedup_key(ps)

                if not force and key in known_keys:
                    total_skipped += 1
                    continue

                # Write YAML
                try:
                    output_path = write_yaml(ps, output_dir)
                    existing_outputs.add(output_path.name)

                    # Log result
                    validation_ok = all(
                        v for k, v in ps.validation.items()
                        if k != "mismatches" and isinstance(v, bool)
                    )
                    validation_issues = ps.validation.get("mismatches", [])

                    emp_log["payslips"][key] = {
                        "output_file": output_path.name,
                        "source_file": ps.source_file,
                        "source_pages": ps.source_pages,
                        "pay_type": ps.pay_type,
                        "gross_pay": ps.gross_pay,
                        "net_pay": ps.net_pay,
                        "validation_passed": validation_ok,
                        "processed_at": datetime.now().isoformat(timespec="seconds"),
                    }

                    # Update file scan info
                    if ps.source_file not in emp_log.setdefault("files_scanned", {}):
                        emp_log["files_scanned"][ps.source_file] = {
                            "scanned_at": datetime.now().isoformat(timespec="seconds"),
                            "payslips_found": 0,
                            "new": 0,
                            "duplicates": 0,
                        }
                    emp_log["files_scanned"][ps.source_file]["payslips_found"] += 1
                    emp_log["files_scanned"][ps.source_file]["new"] += 1

                    known_keys.add(key)

                    warn_str = ""
                    if validation_issues:
                        warn_str = f" \033[33m({len(validation_issues)} validation issues)\033[0m"
                        total_validation_issues += len(validation_issues)

                    logger.info(
                        f"    OK {ps.source_file} p{ps.source_pages} -> {output_path.name} "
                        f"[{ps.pay_type}] gross=${ps.gross_pay:,.2f} net=${ps.net_pay:,.2f}{warn_str}"
                    )

                    for issue in validation_issues:
                        logger.warning(f"       VALIDATION: {issue}")

                    total_success += 1

                except Exception as e:
                    logger.error(f"    FAIL writing {ps.pay_date} from {pdf_path.name}: {e}")
                    total_errors += 1

        # Save after each employer
        save_processing_log(processing_log)

    logger.info(
        f"\n  Done: {total_success} written, {total_skipped} skipped (dedup), "
        f"{total_errors} errors, {total_validation_issues} validation issues"
    )


# --- CLI ---
def main():
    parser = argparse.ArgumentParser(description="Payslip PDF ingestion pipeline")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scan", action="store_true", help="Show PDFs and payslip counts (no processing)")
    group.add_argument("--run", action="store_true", help="Process PDFs and write YAML files")

    parser.add_argument(
        "--employer",
        type=str,
        choices=list(EMPLOYER_CONFIGS.keys()),
        help="Process only this employer",
    )
    parser.add_argument("--force", action="store_true", help="Re-process everything (ignore dedup)")
    parser.add_argument("--skip-errors", action="store_true", help="Skip previously errored files")

    args = parser.parse_args()

    setup_logging()
    logger.info(f"Payslip Ingestion — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if args.scan:
        run_scan(employer_filter=args.employer, force=args.force)
    elif args.run:
        run_ingest(employer_filter=args.employer, force=args.force, skip_errors=args.skip_errors)


if __name__ == "__main__":
    main()
