#!/usr/bin/env python3
"""Tax document PDF ingestion pipeline.

Extracts structured data from tax PDFs (W-2, 1099-R, 1098, etc.) and saves
as validated YAML files.

Source PDFs:
  - Prepare folder: ~/Dropbox/1-Tax/2-prepare/<year>/  (CPA inputs)
  - Archive folder: ~/Dropbox/1-Tax/3-archive/<year>/  (filed returns)

Output:
  - Finance/tax/prepare/<year>/<form>-<payer>.yaml
  - Finance/tax/archive/<year>/<form>-summary.yaml
"""

import argparse
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
PREPARE_SOURCE = Path.home() / "Dropbox" / "1-Tax" / "2-prepare"
ARCHIVE_SOURCE = Path.home() / "Dropbox" / "1-Tax" / "3-archive"
OUTPUT_ROOT = OBSIDIAN_ROOT / "Finance" / "tax"
PREPARE_OUTPUT = OUTPUT_ROOT / "prepare"
ARCHIVE_OUTPUT = OUTPUT_ROOT / "archive"
LOG_FILE = OUTPUT_ROOT / "ingest.log"
PROCESSING_LOG_PATH = OUTPUT_ROOT / "processing_log.json"

YEARS = [2025, 2024, 2023, 2022]  # Process newest first

# --- Logging ---
logger = logging.getLogger("ingest_tax")


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


# --- YAML Helpers ---
def float_representer(dumper, value):
    """Format floats with 2 decimal places for dollar amounts."""
    if value == int(value):
        return dumper.represent_scalar("tag:yaml.org,2002:float", f"{value:.2f}")
    return dumper.represent_scalar("tag:yaml.org,2002:float", f"{value:.2f}")


yaml.add_representer(float, float_representer)


def write_yaml(data: dict, output_path: Path):
    """Write data dict to YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


# --- Processing Log ---
def load_processing_log() -> dict:
    if PROCESSING_LOG_PATH.exists():
        with open(PROCESSING_LOG_PATH) as f:
            return json.load(f)
    return {"version": 1, "last_run": None, "files": {}}


def save_processing_log(log: dict):
    PROCESSING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log["last_run"] = datetime.now().isoformat(timespec="seconds")
    with open(PROCESSING_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def is_processed(log: dict, pdf_path: Path) -> bool:
    """Check if a PDF has been successfully processed."""
    key = str(pdf_path)
    entry = log.get("files", {}).get(key, {})
    return entry.get("status") == "success"


def record_result(log: dict, pdf_path: Path, result: dict):
    """Record processing result for a PDF."""
    log.setdefault("files", {})[str(pdf_path)] = result


# --- PDF Discovery ---
def discover_prepare_pdfs(year: int) -> list[Path]:
    """Find all PDFs in a prepare year folder (recursively)."""
    year_dir = PREPARE_SOURCE / str(year)
    if not year_dir.exists():
        return []
    pdfs = sorted(year_dir.rglob("*.pdf"), key=lambda p: p.name.lower())
    # Also check for .PDF extension
    pdfs += sorted(year_dir.rglob("*.PDF"), key=lambda p: p.name.lower())
    # Deduplicate (rglob with different cases might overlap on case-insensitive FS)
    seen = set()
    unique = []
    for p in pdfs:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


def discover_archive_pdfs(year: int) -> list[Path]:
    """Find all PDFs in an archive year folder."""
    year_dir = ARCHIVE_SOURCE / str(year)
    if not year_dir.exists():
        return []
    pdfs = sorted(year_dir.rglob("*.pdf"), key=lambda p: p.name.lower())
    pdfs += sorted(year_dir.rglob("*.PDF"), key=lambda p: p.name.lower())
    seen = set()
    unique = []
    for p in pdfs:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


# --- Form Type Detection ---
def detect_form_type(pdf_path: Path) -> Optional[str]:
    """Detect the IRS form type from filename and PDF content.

    Returns form type string or None if unsupported.
    """
    name = pdf_path.name.lower()

    # Non-tax documents to skip (vehicle registrations, etc.)
    skip_keywords = ["renew", "tabs", "acura", "trailer", "vehicle"]
    if any(kw in name for kw in skip_keywords):
        return None

    # Filename-based detection
    # W-2: match "w-2" or "w2" as a word boundary (avoid "renew-2024" false positive)
    if re.search(r"(?:^|[\s_.-])w-?2(?:[\s_.-]|$)", name):
        return "W-2"
    if "1099-r" in name or "1099r" in name:
        return "1099-R"
    if "1098" in name:
        return "1098"
    if "1099-div" in name:
        return "1099-DIV"
    if "1099-int" in name:
        return "1099-INT"
    if "1099-misc" in name or "1099-nec" in name:
        return "1099-MISC"
    if "1099-b" in name:
        return "1099-B"
    if "consolidated-form-1099" in name or "1099-cons" in name:
        return "1099-CONSOLIDATED"
    if "1099-sa" in name or "1099sa" in name:
        return "1099-SA"
    if "5498-sa" in name or "5498sa" in name:
        return "5498-SA"
    if "5498" in name:
        return "5498"
    if "schedule_h" in name or "schedule-h" in name:
        return "Schedule-H"
    if "1095" in name:
        return "1095-C"
    if "3922" in name:
        return "3922"

    # Content-based detection for ambiguous filenames
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return None
            text = pdf.pages[0].extract_text() or ""
            text_lower = text.lower()

            if "w-2" in text_lower and ("wage and tax" in text_lower or "wages, tips" in text_lower):
                return "W-2"
            if "1099-r" in text_lower or "form 1099-r" in text_lower:
                return "1099-R"
            if "form 1098" in text_lower or ("mortgage interest" in text_lower and "1098" in text_lower):
                return "1098"
            if "1099-div" in text_lower:
                return "1099-DIV"
            if "1099-int" in text_lower:
                return "1099-INT"
            if "schedule h" in text_lower and "household" in text_lower:
                return "Schedule-H"
            if "1099-sa" in text_lower or "form 1099-sa" in text_lower:
                return "1099-SA"
            if "5498-sa" in text_lower or "form 5498-sa" in text_lower:
                return "5498-SA"
            if ("5498" in text_lower or "form 5498" in text_lower) and "ira contribution" in text_lower:
                return "5498"
    except Exception:
        pass

    return None


# --- SSN Masking ---
def mask_ssn(ssn: str) -> str:
    """Mask SSN to show only last 4 digits: ***-**-XXXX."""
    digits = re.sub(r"[^0-9]", "", ssn)
    if len(digits) >= 4:
        return f"***-**-{digits[-4:]}"
    return ssn


# --- Dollar Amount Parsing ---
def parse_amount(s: str) -> Optional[float]:
    """Parse a dollar amount string like '$1,234.56' or '1234.56' to float."""
    if not s:
        return None
    s = s.strip().replace("$", "").replace(",", "").replace(" ", "")
    # Handle parenthesized negatives
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return round(float(s), 2)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# W-2 Parser
# ---------------------------------------------------------------------------

def _extract_value_chars(page, max_y: float = 310) -> list[dict]:
    """Extract characters that are likely form-fill values (Courier font)."""
    return [
        c for c in page.chars
        if c["top"] < max_y
        and "courier" in c.get("fontname", "").lower()
    ]


def _build_tokens(chars: list[dict], y_tolerance: float = 5.0) -> list[dict]:
    """Group adjacent characters into tokens with position info.

    First clusters characters into lines by y-position, then within each line
    groups horizontally adjacent characters into tokens.

    Returns list of {text, x0, top, x1, bottom}.
    """
    if not chars:
        return []

    # Step 1: Cluster characters into lines by y-position
    chars_sorted = sorted(chars, key=lambda c: c["top"])
    lines = []
    current_line = [chars_sorted[0]]
    for c in chars_sorted[1:]:
        if abs(c["top"] - current_line[0]["top"]) <= y_tolerance:
            current_line.append(c)
        else:
            lines.append(current_line)
            current_line = [c]
    lines.append(current_line)

    # Step 2: Within each line, sort by x and group into tokens
    tokens = []
    for line_chars in lines:
        line_chars.sort(key=lambda c: c["x0"])
        current = {
            "text": line_chars[0]["text"],
            "x0": line_chars[0]["x0"],
            "top": line_chars[0]["top"],
            "x1": line_chars[0]["x0"] + line_chars[0].get("width", 5),
            "bottom": line_chars[0]["bottom"],
        }
        for c in line_chars[1:]:
            gap = c["x0"] - current["x1"]
            if gap < 8:  # Adjacent or overlapping
                current["text"] += c["text"]
                current["x1"] = max(current["x1"], c["x0"] + c.get("width", 5))
                current["bottom"] = max(current["bottom"], c["bottom"])
            else:
                tokens.append(current)
                current = {
                    "text": c["text"],
                    "x0": c["x0"],
                    "top": c["top"],
                    "x1": c["x0"] + c.get("width", 5),
                    "bottom": c["bottom"],
                }
        tokens.append(current)

    return sorted(tokens, key=lambda t: (t["top"], t["x0"]))


def _parse_w2_salesforce(pdf_path: Path, tax_year: int) -> dict:
    """Parse Salesforce-format W-2 (IRS form with Courier values overlaid on form template).

    The PDF has 4 copies per page (Copy C, Copy 2, Copy B, Copy D) laid out vertically,
    with some pages having 2 copies side-by-side. We extract Courier-font characters
    from a single copy and map amounts to W-2 boxes by position.
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]

        # Use the first page, first copy: filter to left half (x < 300)
        # The first copy extends to about 1/3 page height (includes box 13-14 area)
        copy_height = page.height / 3  # Generous: includes boxes 13, 14, 15
        x_boundary = page.width * 0.5

        # Extract ALL Courier characters from one copy (left half)
        value_chars = [
            c for c in page.chars
            if c["top"] < copy_height
            and c["x0"] < x_boundary
            and "courier" in c.get("fontname", "").lower()
        ]

        if not value_chars:
            raise ValueError("No Courier-font value characters found in first W-2 copy")

        tokens = _build_tokens(value_chars)

        # Classify each token
        boxes = {}
        employer = {"name": "Salesforce, Inc.", "ein": ""}
        employee = {"name": "Yi Chen", "ssn_last4": ""}
        box12 = []
        box14_other = []
        retirement_plan = False
        box10 = None

        # Known W-2 box 12 code descriptions
        CODE_DESCRIPTIONS = {
            "C": "Group-term life insurance over $50K",
            "D": "401(k) elective deferrals",
            "E": "403(b) elective deferrals",
            "AA": "Designated Roth 401(k)",
            "BB": "Designated Roth 403(b)",
            "DD": "Health coverage cost (employer + employee)",
            "W": "HSA employer contributions",
            "G": "457(b) elective deferrals",
        }

        # Separate tokens into categories
        amounts = []  # (amount, x, y)
        codes = []  # (code, x, y)
        text_tokens = []  # everything else

        for t in tokens:
            text = t["text"].strip()

            # SSN
            if re.match(r"\d{3}-\d{2}-\d{4}$", text):
                employee["ssn_last4"] = text[-4:]
                continue
            if re.match(r"XXX-XX-\d{4}$", text):
                employee["ssn_last4"] = text[-4:]
                continue

            # EIN
            if re.match(r"\d{2}-\d{7}$", text):
                employer["ein"] = text
                continue

            # Box 12 code+amount combined: "D19975.00" or "AA11025.00"
            m = re.match(r"^([A-Z]{1,2})([\d,]+\.\d{2})$", text)
            if m and m.group(1) in CODE_DESCRIPTIONS:
                box12.append({
                    "code": m.group(1),
                    "amount": float(m.group(2).replace(",", "")),
                    "description": CODE_DESCRIPTIONS[m.group(1)],
                })
                continue

            # Standalone code letter (next to a separate amount token)
            if re.match(r"^[A-Z]{1,2}$", text) and text in CODE_DESCRIPTIONS:
                codes.append({"code": text, "x": t["x0"], "y": t["top"]})
                continue

            # Dollar amount
            clean = text.replace(",", "")
            if re.match(r"^\d+\.\d{2}$", clean):
                amounts.append({"amount": float(clean), "x": t["x0"], "y": t["top"]})
                continue

            # Retirement plan checkbox
            if text == "X":
                retirement_plan = True
                continue

            # Box 14 text: "ESPP GAINS13408.81" or "RS235456.56"
            m = re.search(r"(?:ESPP\s*GAINS|GAINS)\s*([\d,]+\.\d{2})", text)
            if m:
                box14_other.append(f"ESPP GAINS {m.group(1)}")
                continue
            m = re.match(r"RS([\d,]+\.\d{2})", text)
            if m:
                box14_other.append(f"RSU {m.group(1)}")
                continue

            # Employer name detection
            if "SALESFORCE" in text.upper():
                employer["name"] = "Salesforce, Inc."

            text_tokens.append(t)

        # Pair standalone codes with adjacent amounts
        for code_tok in codes:
            # Find the nearest amount token on the same y-band
            best = None
            for a in amounts:
                if abs(a["y"] - code_tok["y"]) < 5 and a["x"] > code_tok["x"]:
                    if best is None or a["x"] < best["x"]:
                        best = a
            if best and code_tok["code"] in CODE_DESCRIPTIONS:
                box12.append({
                    "code": code_tok["code"],
                    "amount": best["amount"],
                    "description": CODE_DESCRIPTIONS[code_tok["code"]],
                })
                amounts.remove(best)

        # Sort remaining amounts by y then x — first 6 are boxes 1-6
        amounts.sort(key=lambda a: (a["y"], a["x"]))

        # The W-2 box layout has pairs: (1,2) on row 1, (3,4) on row 2, (5,6) on row 3
        # Group amounts by y-position (within 5pt tolerance)
        y_groups = []
        if amounts:
            current_group = [amounts[0]]
            for a in amounts[1:]:
                if abs(a["y"] - current_group[0]["y"]) < 5:
                    current_group.append(a)
                else:
                    y_groups.append(sorted(current_group, key=lambda a: a["x"]))
                    current_group = [a]
            y_groups.append(sorted(current_group, key=lambda a: a["x"]))

        # Map first 3 groups with 2+ amounts to box pairs
        box_pairs = [(1, 2), (3, 4), (5, 6)]
        pair_idx = 0
        remaining_amounts = []
        for group in y_groups:
            if pair_idx >= len(box_pairs):
                remaining_amounts.extend(group)
                continue
            if len(group) >= 2:
                left_box, right_box = box_pairs[pair_idx]
                boxes[left_box] = group[0]["amount"]
                boxes[right_box] = group[1]["amount"]
                pair_idx += 1
            else:
                remaining_amounts.extend(group)

        # Extract Box 10 from remaining amounts (dependent care, typically < $5000)
        box12_amounts = {b["amount"] for b in box12}
        for a in remaining_amounts:
            if a["amount"] <= 5000 and a["amount"] not in box12_amounts:
                if box10 is None:
                    box10 = a["amount"]
                    break

    return _build_w2_yaml(
        tax_year=tax_year,
        employer=employer,
        employee=employee,
        boxes=boxes,
        box12=box12,
        box14_other=box14_other,
        retirement_plan=retirement_plan,
        box10=box10,
        pdf_path=pdf_path,
    )




def _parse_w2_paylocity(pdf_path: Path, tax_year: int) -> dict:
    """Parse Paylocity-format W-2 (ServiceTitan, Stripe).

    This format has 2 copies side-by-side, all Courier font at different sizes.
    Layout: SSN + Box1 + Box2 on first row, Box3 + Box4 on second, EIN + Box5 + Box6 on third.
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        page_mid_x = page.width / 2

        # Get all Courier characters from the first copy (left half of page)
        value_chars = [
            c for c in page.chars
            if c["x0"] < page_mid_x
            and "courier" in c.get("fontname", "").lower()
        ]

        if not value_chars:
            raise ValueError("No Courier-font characters found")

        # Separate by font size
        size_groups = {}
        for c in value_chars:
            size = round(c.get("size", 0), 0)
            size_groups.setdefault(size, []).append(c)

        # The largest font size group has the box values + SSN/EIN + employer info
        main_size = max(size_groups.keys(), key=lambda s: len(size_groups[s]))
        main_chars = size_groups[main_size]

        tokens = _build_tokens(main_chars)

        boxes = {}
        employer = {"name": "", "ein": ""}
        employee = {"name": "Yi Chen", "ssn_last4": ""}

        # Classify tokens
        amounts = []
        for t in tokens:
            text = t["text"].strip()
            if re.match(r"XXX-XX-\d{4}$", text) or re.match(r"\d{3}-\d{2}-\d{4}$", text):
                employee["ssn_last4"] = text[-4:]
            elif re.match(r"\d{2}-\d{7}$", text):
                employer["ein"] = text
            elif re.match(r"^[\d,]+\.\d{2}$", text.replace(",", "")):
                amounts.append({"amount": float(text.replace(",", "")), "x": t["x0"], "y": t["top"]})
            elif any(name in text for name in ["ServiceTitan", "Stripe", "Salesforce"]):
                employer["name"] = text.split(",")[0].strip()
            elif "Yi Chen" in text or "YI CHEN" in text.upper():
                employee["name"] = "Yi Chen"

        # Group amounts by y-position and map to boxes
        amounts.sort(key=lambda a: (a["y"], a["x"]))
        y_groups = []
        if amounts:
            current = [amounts[0]]
            for a in amounts[1:]:
                if abs(a["y"] - current[0]["y"]) < 5:
                    current.append(a)
                else:
                    y_groups.append(sorted(current, key=lambda a: a["x"]))
                    current = [a]
            y_groups.append(sorted(current, key=lambda a: a["x"]))

        box_pairs = [(1, 2), (3, 4), (5, 6)]
        for i, (left_box, right_box) in enumerate(box_pairs):
            if i < len(y_groups) and len(y_groups[i]) >= 2:
                boxes[left_box] = y_groups[i][0]["amount"]
                boxes[right_box] = y_groups[i][1]["amount"]

        # Extract Box 12 codes from smaller font characters
        box12 = []
        CODE_DESCRIPTIONS = {
            "C": "Group-term life insurance over $50K",
            "D": "401(k) elective deferrals",
            "DD": "Health coverage cost (employer + employee)",
            "W": "HSA employer contributions",
            "AA": "Designated Roth 401(k)",
        }

        for size, chars_list in size_groups.items():
            if size == main_size:
                continue
            small_tokens = _build_tokens(chars_list)

            small_codes = []
            small_amounts = []
            for t in small_tokens:
                text = t["text"].strip()
                # Combined code+amount
                m = re.match(r"^([A-Z]{1,2})([\d,]+\.\d{2})$", text)
                if m and m.group(1) in CODE_DESCRIPTIONS:
                    box12.append({
                        "code": m.group(1),
                        "amount": float(m.group(2).replace(",", "")),
                        "description": CODE_DESCRIPTIONS[m.group(1)],
                    })
                    continue
                # Standalone code
                if re.match(r"^[A-Z]{1,2}$", text) and text in CODE_DESCRIPTIONS:
                    small_codes.append({"code": text, "x": t["x0"], "y": t["top"]})
                    continue
                # Standalone amount
                clean = text.replace(",", "")
                if re.match(r"^\d+\.\d{2}$", clean):
                    small_amounts.append({"amount": float(clean), "x": t["x0"], "y": t["top"]})

            # Pair codes with nearby amounts
            for code_tok in small_codes:
                best = None
                for a in small_amounts:
                    if abs(a["y"] - code_tok["y"]) < 5 and a["x"] > code_tok["x"]:
                        if best is None or a["x"] < best["x"]:
                            best = a
                if best:
                    box12.append({
                        "code": code_tok["code"],
                        "amount": best["amount"],
                        "description": CODE_DESCRIPTIONS[code_tok["code"]],
                    })
                    small_amounts.remove(best)

        # Check retirement plan (X in smaller font chars)
        retirement_plan = False
        for size, chars_list in size_groups.items():
            if size == main_size:
                continue
            for c in chars_list:
                if c["text"].strip() == "X":
                    retirement_plan = True
                    break

        # Detect employer name from all font size tokens
        if not employer["name"]:
            for size, chars_list in size_groups.items():
                all_tokens = _build_tokens(chars_list)
                for t in all_tokens:
                    text = t["text"].strip()
                    if "ServiceTitan" in text:
                        employer["name"] = "ServiceTitan, Inc."
                        break
                    if "Stripe" in text:
                        employer["name"] = "Stripe, Inc."
                        break
                if employer["name"]:
                    break
        if not employer["name"]:
            name_lower = pdf_path.name.lower()
            if "servicetitan" in name_lower:
                employer["name"] = "ServiceTitan, Inc."
            elif "stripe" in name_lower:
                employer["name"] = "Stripe, Inc."

        # Deduplicate Box 12 entries
        seen_codes = set()
        unique_box12 = []
        for entry in box12:
            key = (entry["code"], entry["amount"])
            if key not in seen_codes:
                seen_codes.add(key)
                unique_box12.append(entry)
        box12 = unique_box12

    return _build_w2_yaml(
        tax_year=tax_year,
        employer=employer,
        employee=employee,
        boxes=boxes,
        box12=box12,
        box14_other=[],
        retirement_plan=retirement_plan,
        box10=None,
        pdf_path=pdf_path,
    )


def _parse_w2_adp(pdf_path: Path, tax_year: int) -> dict:
    """Parse ADP-format W-2 (Airbnb, Meta) — has earnings summary section.

    This format uses all Helvetica fonts. We parse using regex on the full text.
    The ADP W-2 has labeled sections like:
      GROSS PAY 371,142.69
      FED. INCOME 79,609.86 / TAX WITHHELD (various boxes)
    Plus the standard W-2 boxes further down.
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text(layout=True) or ""

    boxes = {}
    employer = {"name": "", "ein": ""}
    employee = {"name": "", "ssn_last4": ""}
    box12 = []
    box14_other = []
    retirement_plan = False
    box10 = None

    # Parse the W-2 form section (usually second half of the page)
    # Look for labeled box values using regex

    # SSN
    ssn_m = re.search(r"(?:XXX-XX-|[\d*]{3}-[\d*]{2}-)(\d{4})", text)
    if ssn_m:
        employee["ssn_last4"] = ssn_m.group(1)

    # EIN
    ein_m = re.search(r"(\d{2}-\d{7})", text)
    if ein_m:
        employer["ein"] = ein_m.group(1)

    # Employer name — look for known employer patterns
    if "AIRBNB" in text.upper():
        employer["name"] = "Airbnb Inc"
    elif "META" in text.upper():
        employer["name"] = "Meta Platforms Inc"
    elif "STRIPE" in text.upper():
        employer["name"] = "Stripe, Inc."

    # Employee name
    name_m = re.search(r"YI\s*CHEN", text)
    if name_m:
        employee["name"] = "Yi Chen"

    # Extract box values from the W-2 section
    # The ADP format has labeled values like "1 Wages, tips, other comp. 2 Federal income tax withheld"
    # followed by the actual amounts on the next line

    # Use character-level extraction for more reliable amount parsing
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        chars = page.chars
        page_mid_x = page.width / 2

        # Group chars by y-position bands
        bands = {}
        for c in chars:
            if c["x0"] > page_mid_x:  # Skip right-side summary
                continue
            y = round(c["top"], -1)
            bands.setdefault(y, []).append(c)

        # Build text for each band
        band_texts = {}
        for y in sorted(bands.keys()):
            band_chars = sorted(bands[y], key=lambda c: c["x0"])
            band_text = "".join(c["text"] for c in band_chars)
            band_texts[y] = band_text

        # Search for box values in bands
        for y, band_text in band_texts.items():
            # Box 1 (Wages) — look for pattern near "Wages,tips" label
            if "Wages,tips" in band_text or "Wagesandtips" in band_text:
                # The amounts might be on this line or the next
                amounts = re.findall(r"(\d[\d,]*\.\d{2})", band_text)
                if amounts:
                    # First amount after the label is Box 1
                    pass  # Will extract from next line

            # Direct extraction: look for labeled amounts
            # Box 3 + 4 line
            m = re.match(r".*?(\d[\d,]*\.\d{2}).*?(\d[\d,]*\.\d{2})", band_text)
            if m and "Socialsecurity" in band_text:
                boxes.setdefault(3, parse_amount(m.group(1)))
                boxes.setdefault(4, parse_amount(m.group(2)))

        # Also try regex on layout text for cleaner extraction
        lines = text.split("\n")
        for i, line in enumerate(lines):
            line_clean = line.strip()

            # Look for dollar amounts with $ signs
            # Box 1 and 2 pattern
            m = re.search(r"1\s+Wages.*?\$?([\d,]+\.\d{2}).*?2\s+Federal.*?\$?([\d,]+\.\d{2})", line_clean)
            if m:
                boxes[1] = parse_amount(m.group(1))
                boxes[2] = parse_amount(m.group(2))

            # Box 3 and 4
            m = re.search(r"3\s+Social security wages.*?\$?([\d,]+\.\d{2}).*?4\s+Social security tax.*?\$?([\d,]+\.\d{2})", line_clean)
            if m:
                boxes[3] = parse_amount(m.group(1))
                boxes[4] = parse_amount(m.group(2))

            # Box 5 and 6
            m = re.search(r"5\s+Medicare wages.*?\$?([\d,]+\.\d{2}).*?6\s+Medicare tax.*?\$?([\d,]+\.\d{2})", line_clean)
            if m:
                boxes[5] = parse_amount(m.group(1))
                boxes[6] = parse_amount(m.group(2))

    # If regex didn't work, try extracting from the earnings summary section
    if 1 not in boxes:
        for y, band_text in band_texts.items():
            # GROSSPAY followed by amount
            m = re.search(r"GROSSPAY\s*([\d,]+\.\d{2})", band_text)
            if m:
                boxes[1] = parse_amount(m.group(1))

            m = re.search(r"FED\.?\s*INCOME\s*([\d,]+\.\d{2})", band_text)
            if m:
                boxes[2] = parse_amount(m.group(1))

            m = re.search(r"SOCIALSECURITY\s*([\d,]+\.\d{2})", band_text)
            if m:
                boxes[4] = parse_amount(m.group(1))

            m = re.search(r"MEDICARETAX\s*([\d,]+\.\d{2})", band_text)
            if m:
                boxes[6] = parse_amount(m.group(1))

    # Box 12 codes
    for y, band_text in band_texts.items():
        for m in re.finditer(r"([A-Z]{1,2})([\d,]+\.\d{2})", band_text):
            code = m.group(1)
            amount = parse_amount(m.group(2))
            code_descriptions = {
                "C": "Group-term life insurance over $50K",
                "D": "401(k) elective deferrals",
                "DD": "Health coverage cost (employer + employee)",
                "W": "HSA employer contributions",
                "AA": "Designated Roth 401(k)",
            }
            if code in code_descriptions and amount:
                # Avoid duplicates
                if not any(b["code"] == code and b["amount"] == amount for b in box12):
                    box12.append({"code": code, "amount": amount, "description": code_descriptions[code]})

    return _build_w2_yaml(
        tax_year=tax_year,
        employer=employer,
        employee=employee,
        boxes=boxes,
        box12=box12,
        box14_other=box14_other,
        retirement_plan=retirement_plan,
        box10=box10,
        pdf_path=pdf_path,
    )


def _parse_w2_nanny(pdf_path: Path, tax_year: int) -> dict:
    """Parse HomePay nanny W-2 — standard IRS W-2 form, well-formatted layout text."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text(layout=True) or ""

    boxes = {}
    employer = {"name": "Yi Chen", "ein": ""}
    employee = {"name": "", "ssn_last4": ""}
    box12 = []
    retirement_plan = False

    lines = text.split("\n")
    for i, line in enumerate(lines):
        # EIN
        m = re.search(r"(\d{2}-\d{7})", line)
        if m and not employer["ein"]:
            employer["ein"] = m.group(1)

        # SSN (masked or not)
        m = re.search(r"(\d{3})-?(\d{2})-?(\d{4})", line)
        if m and not employee["ssn_last4"]:
            employee["ssn_last4"] = m.group(3)

        # Box values — look for numeric values after labels
        # The nanny W-2 layout has amounts aligned in columns
        # "1 Wages, tips, other compensation 2 Federal income tax withheld"
        # followed by a line with the values

        # Look for value lines: numbers aligned in columns
        amounts = re.findall(r"(\d[\d,]*\.\d{2})", line)
        if len(amounts) >= 2 and i > 3:
            # Check the previous line for box labels
            prev = lines[i - 1] if i > 0 else ""
            if "Wages" in prev and "Federal" in prev:
                boxes[1] = parse_amount(amounts[0])
                boxes[2] = parse_amount(amounts[1])
            elif "Social security wages" in prev:
                boxes[3] = parse_amount(amounts[0])
                boxes[4] = parse_amount(amounts[1])
            elif "Medicare wages" in prev:
                boxes[5] = parse_amount(amounts[0])
                boxes[6] = parse_amount(amounts[1])

    # Employee name
    for line in lines:
        m = re.search(r"(?:Margaret|Diana)\s+\w+", line)
        if m:
            employee["name"] = m.group(0)
            break

    return _build_w2_yaml(
        tax_year=tax_year,
        employer=employer,
        employee=employee,
        boxes=boxes,
        box12=box12,
        box14_other=[],
        retirement_plan=retirement_plan,
        box10=None,
        pdf_path=pdf_path,
    )


def _parse_w2_lincoln(pdf_path: Path, tax_year: int) -> dict:
    """Parse Lincoln Life W-2 — poor quality text extraction, small amounts."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text(layout=True) or ""

    boxes = {}
    employer = {"name": "Lincoln National Life Insurance Co", "ein": ""}
    employee = {"name": "Yi Chen", "ssn_last4": "2622"}

    # Lincoln Life W-2 has OCR-like quality issues
    # Look for patterns like "$1,005.42" or "$1.005.42" (period instead of comma)
    # EIN
    ein_m = re.search(r"(\d{2}-\d{7})", text)
    if ein_m:
        employer["ein"] = ein_m.group(1)

    # Extract all dollar-like amounts from the first copy
    # The Lincoln W-2 has values like "$1,005.42", "$62.34", "$14.58"
    amounts = []
    for m in re.finditer(r"\$\s*([\d,.]+)", text):
        val_str = m.group(1)
        # Fix OCR issue: "$1.005.42" → "$1,005.42" (period as thousands separator)
        parts = val_str.split(".")
        if len(parts) == 3:
            # "1.005.42" → "1005.42"
            val_str = parts[0] + parts[1] + "." + parts[2]
        val = parse_amount(val_str)
        if val is not None:
            amounts.append(val)

    # Lincoln Life W-2 typically has: Box 1 = wages, Box 3 = SS wages, Box 5 = Medicare wages (all same)
    # Box 2 = fed tax withheld, Box 4 = SS tax, Box 6 = Medicare tax
    # For a life insurance W-2, Box 1 = Box 3 = Box 5 typically
    if amounts:
        # Find the most common amount (likely the wages value appearing in boxes 1,3,5)
        from collections import Counter
        amount_counts = Counter(amounts)
        most_common = amount_counts.most_common()
        if most_common:
            wage_val = most_common[0][0]
            boxes[1] = wage_val
            boxes[3] = wage_val
            boxes[5] = wage_val

            # The remaining amounts are taxes
            other_amounts = sorted([a for a in amounts if a != wage_val], reverse=True)
            if len(other_amounts) >= 1:
                boxes[2] = 0.0  # Lincoln Life typically has no fed withholding
            if len(other_amounts) >= 1:
                boxes[4] = other_amounts[0] if other_amounts[0] < wage_val * 0.1 else 0.0
            if len(other_amounts) >= 2:
                boxes[6] = other_amounts[1] if other_amounts[1] < wage_val * 0.05 else 0.0

    # Third-party sick pay checkbox
    third_party_sick_pay = "Third-party" in text and "X" in text

    return _build_w2_yaml(
        tax_year=tax_year,
        employer=employer,
        employee=employee,
        boxes=boxes,
        box12=[],
        box14_other=[],
        retirement_plan=False,
        box10=None,
        pdf_path=pdf_path,
        third_party_sick_pay=third_party_sick_pay,
    )


def _build_w2_yaml(
    tax_year: int,
    employer: dict,
    employee: dict,
    boxes: dict,
    box12: list,
    box14_other: list,
    retirement_plan: bool,
    box10: Optional[float],
    pdf_path: Path,
    third_party_sick_pay: bool = False,
) -> dict:
    """Build the W-2 YAML output dict with validation."""
    # Validate: Box 4 should be ~6.2% of Box 3, Box 6 should be ~1.45% of Box 5
    mismatches = []

    box3 = boxes.get(3, 0)
    box4 = boxes.get(4, 0)
    box5 = boxes.get(5, 0)
    box6 = boxes.get(6, 0)

    box4_expected = round(box3 * 0.062, 2)
    box6_expected = round(box5 * 0.0145, 2)

    # Allow for Additional Medicare Tax (0.9% above $200K) and rounding
    box4_check = abs(box4 - box4_expected) <= 1.0 if box3 > 0 else True
    # Box 6 includes regular Medicare (1.45%) + Additional Medicare (0.9% over $200K)
    # So box6 can be higher than box5 * 0.0145 for high earners
    box6_check = box6 >= box6_expected - 1.0 if box5 > 0 else True

    if not box4_check:
        mismatches.append(f"Box 4 ({box4}) != Box 3 ({box3}) * 6.2% = {box4_expected}")
    if not box6_check:
        mismatches.append(f"Box 6 ({box6}) < Box 5 ({box5}) * 1.45% = {box6_expected}")

    result = {
        "form_type": "W-2",
        "tax_year": tax_year,
        "employer": {
            "name": employer.get("name", ""),
            "ein": employer.get("ein", ""),
        },
        "employee": {
            "name": employee.get("name", "Yi Chen"),
            "ssn_last4": employee.get("ssn_last4", ""),
        },
        "boxes": {
            "1_wages": boxes.get(1, 0.0),
            "2_fed_tax_withheld": boxes.get(2, 0.0),
            "3_ss_wages": boxes.get(3, 0.0),
            "4_ss_tax_withheld": boxes.get(4, 0.0),
            "5_medicare_wages": boxes.get(5, 0.0),
            "6_medicare_tax_withheld": boxes.get(6, 0.0),
        },
    }

    if box10 is not None:
        result["boxes"]["10_dependent_care"] = box10

    if box12:
        result["boxes"]["12"] = box12

    result["boxes"]["13"] = {
        "retirement_plan": retirement_plan,
        "statutory_employee": False,
        "third_party_sick_pay": third_party_sick_pay,
    }

    if box14_other:
        result["boxes"]["14_other"] = box14_other

    result["boxes"]["15_state"] = "WA"
    result["boxes"]["16_state_wages"] = 0.0
    result["boxes"]["17_state_tax"] = 0.0

    result["validation"] = {
        "box4_check": box4_check,
        "box6_check": box6_check,
        "mismatches": mismatches,
    }

    result["source"] = {
        "file": str(pdf_path),
        "pages": [1],
        "processed_at": datetime.now().isoformat(timespec="seconds"),
    }

    return result


def _detect_w2_format(pdf_path: Path) -> str:
    """Detect W-2 format variant based on filename and content."""
    name = pdf_path.name.lower()

    # Known employer patterns from filename
    if "salesforce" in name:
        return "salesforce"
    if "servicetitan" in name or ("w-2_form" in name and "chen" in name and "ess" in name.lower()):
        return "paylocity"
    if "stripe" in name:
        return "paylocity"  # Same format as ServiceTitan
    if "airbnb" in name:
        return "adp"
    if "meta" in name:
        return "adp"
    if "lincoln" in name:
        return "lincoln"
    if "schedule_h" in name or "schedule-h" in name:
        return None  # Not a W-2
    if name.startswith("w2.") or "childcare" in str(pdf_path).lower() or "nanny" in str(pdf_path).lower():
        return "nanny"

    # Content-based detection
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text = (page.extract_text() or "").upper()
            if "AIRBNB" in text:
                return "adp"
            if "META PLATFORMS" in text:
                return "adp"
            if "LINCOLN" in text and "LIFE" in text:
                return "lincoln"
            # Check font composition
            fonts = set()
            for c in page.chars[:200]:
                fonts.add(c.get("fontname", "").lower())
            font_str = " ".join(fonts)
            if "courier" in font_str and "arial" in font_str:
                return "salesforce"
            if "courier" in font_str:
                return "paylocity"
            if "helvetica" in font_str:
                return "adp"
    except Exception:
        pass

    return "generic"


def parse_w2(pdf_path: Path, tax_year: int) -> dict:
    """Main W-2 parser dispatcher."""
    fmt = _detect_w2_format(pdf_path)
    logger.debug(f"  W-2 format detected: {fmt} for {pdf_path.name}")

    if fmt == "salesforce":
        return _parse_w2_salesforce(pdf_path, tax_year)
    elif fmt == "paylocity":
        return _parse_w2_paylocity(pdf_path, tax_year)
    elif fmt == "adp":
        return _parse_w2_adp(pdf_path, tax_year)
    elif fmt == "nanny":
        return _parse_w2_nanny(pdf_path, tax_year)
    elif fmt == "lincoln":
        return _parse_w2_lincoln(pdf_path, tax_year)
    else:
        raise ValueError(f"Unknown W-2 format for {pdf_path.name}")


# ---------------------------------------------------------------------------
# 1099-R Parser
# ---------------------------------------------------------------------------

def parse_1099r(pdf_path: Path, tax_year: int) -> dict:
    """Parse Form 1099-R (Distributions From Pensions, Annuities, etc.).

    Handles two layouts:
    1. Fidelity 401k/employer plans: values on the line AFTER box labels
    2. Fidelity IRA: values inline with labels
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text(layout=True) or ""

    # Limit to first copy only (stop at "Form1099-R" or "Department of the Treasury")
    first_copy = []
    for line in text.split("\n"):
        if first_copy and ("Form1099-R" in line or "Form 1099-R" in line) and len(first_copy) > 10:
            break
        first_copy.append(line)
    text = "\n".join(first_copy)

    payer = {"name": "", "tin": ""}
    recipient = {"name": "Yi Chen", "ssn_last4": "2622"}
    boxes = {}
    mismatches = []
    text_upper = text.upper()

    # Payer name
    if "FIDELITY" in text_upper:
        # Determine plan type from filename or text
        fname = pdf_path.name.upper()
        if "SALESFORCE" in text_upper or "SALESFORCE" in fname:
            payer["name"] = "Fidelity - Salesforce 401K"
        elif "SERVICETITAN" in text_upper or "SERVICETITAN" in fname:
            payer["name"] = "Fidelity - ServiceTitan 401K"
        elif "401K" in text_upper or "401(K)" in text_upper:
            payer["name"] = "Fidelity Investments (401k)"
        else:
            payer["name"] = "Fidelity Investments (IRA)"
    elif "STATE FARM" in text_upper:
        payer["name"] = "State Farm Life Insurance"

    # Payer TIN
    tin_matches = re.findall(r"(\d{2}-\d{7})", text)
    if tin_matches:
        payer["tin"] = tin_matches[0]

    # Recipient SSN
    ssn_m = re.search(r"(?:\*{3}-\*{2}-|xxx-xx-)(\d{4})", text, re.IGNORECASE)
    if ssn_m:
        recipient["ssn_last4"] = ssn_m.group(1)

    # Account number — look for the line AFTER "Account number (see instructions)"
    account_number = ""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "Account number" in line and "see instructions" in line:
            # Account number is on the next line
            if i + 1 < len(lines):
                m = re.search(r"(\d{10,})", lines[i + 1])
                if m:
                    account_number = m.group(1)
            break

    # Extract ALL dollar amounts in order from the first copy
    # The 1099-R has a consistent positional layout:
    # Line with "1 Gross distribution": next dollar amount = Box 1
    # Line with "2a Taxable amount": next dollar amount = Box 2a
    # Line with "3 Capital gain" + "4 Federal": next two amounts = Box 3, Box 4
    # Line with "5 Employee" + "6 Net unrealized": next two amounts = Box 5, Box 6
    # Line with distribution code letter = Box 7

    all_amounts = []
    for i, line in enumerate(lines):
        for m in re.finditer(r"\$\s*([\d,]+\.\d{2})", line):
            all_amounts.append({
                "amount": parse_amount(m.group(1)),
                "line": i,
                "pos": m.start(),
            })

    # Find box labels and map to amounts
    label_lines = {}
    for i, line in enumerate(lines):
        if "1 Gross distribution" in line:
            label_lines["box1"] = i
        if "2a Taxable amount" in line:
            label_lines["box2a"] = i
        if "3 Capital gain" in line:
            label_lines["box3_4"] = i
        if ("5 Employee" in line or "5 Empl" in line) and ("6 Net" in line or "6 " in line):
            label_lines["box5_6"] = i
        if "7 Distribution" in line or "code(s)" in line:
            label_lines["box7"] = i

    def _find_amounts_near(label_line: int) -> list[float]:
        """Find dollar amounts on the label line and the next 2 lines."""
        result = []
        for a in all_amounts:
            if label_line <= a["line"] <= label_line + 2:
                result.append(a["amount"])
        return result

    # Box 1
    if "box1" in label_lines:
        amts = _find_amounts_near(label_lines["box1"])
        if amts:
            boxes[1] = amts[0]

    # Box 2a
    if "box2a" in label_lines:
        amts = _find_amounts_near(label_lines["box2a"])
        if amts:
            boxes["2a"] = amts[0]

    # Box 3 + 4 (on the same label line, amounts nearby)
    if "box3_4" in label_lines:
        amts = _find_amounts_near(label_lines["box3_4"])
        if len(amts) >= 2:
            boxes[3] = amts[0]
            boxes[4] = amts[1]
        elif len(amts) == 1:
            boxes[3] = amts[0]

    # Box 5 + 6
    if "box5_6" in label_lines:
        amts = _find_amounts_near(label_lines["box5_6"])
        if len(amts) >= 2:
            boxes[5] = amts[0]
            boxes[6] = amts[1]
        elif len(amts) == 1:
            boxes[5] = amts[0]

    # Box 2b checkboxes
    boxes["2b_not_determined"] = bool(re.search(r"not determined.*?X|X.*?not determined", text))
    boxes["2b_total_distribution"] = bool(re.search(r"total distribution.*?X|X.*?total distribution", text, re.IGNORECASE))

    # Box 7: Distribution code — look for a standalone code near the label
    distribution_code = ""
    if "box7" in label_lines:
        # Search lines around box 7 label for a distribution code
        # Valid 1099-R codes: 1-7, A, B, C, D, E, F, G, H, J, K, L, M, N, P, Q, R, S, T, U, W
        valid_codes = set("1234567ABCDEFGHJKLMNPQRSTUW")
        for i in range(label_lines["box7"], min(label_lines["box7"] + 4, len(lines))):
            line = lines[i]
            # Skip the label line's box numbers (e.g., "7 Distribution" has "7" as label)
            if i == label_lines["box7"]:
                continue
            # Look for standalone code characters (preceded/followed by whitespace or $)
            for m in re.finditer(r"(?:^|\s)([1-7A-HJ-NPQRSTUW])(?:\s|$)", line):
                code = m.group(1)
                if code in valid_codes:
                    distribution_code = code
                    break
            if distribution_code:
                break

    # IRA/SEP/SIMPLE checkbox — check 2-3 lines around the code area
    ira_sep_simple = False
    if "box7" in label_lines:
        for i in range(label_lines["box7"], min(label_lines["box7"] + 4, len(lines))):
            line = lines[i]
            if "IRA" in line or "SEP" in line or "SIMPLE" in line:
                if "X" in line:
                    ira_sep_simple = True
                    break

    # Plan type detection
    plan_type = "unknown"
    if "401" in text_upper and ("K" in text_upper or "(K)" in text_upper):
        plan_type = "401(k)"
        # Identify the specific employer plan
        if "SALESFORCE" in text_upper:
            plan_type = "401(k) - Salesforce"
        elif "SERVICETITAN" in text_upper:
            plan_type = "401(k) - ServiceTitan"
    elif "TRADITIONAL" in pdf_path.name.upper() or ("TRADITIONAL" in text_upper and "IRA" in text_upper):
        plan_type = "Traditional IRA"
    elif "ROTH" in text_upper and "IRA" in text_upper:
        plan_type = "Roth IRA"
    elif "IRA" in text_upper:
        plan_type = "IRA"
    elif "LIFE" in text_upper and "INSURANCE" in text_upper:
        plan_type = "Life Insurance"

    # Validation
    if boxes.get(1) and boxes.get("2a"):
        if boxes["2a"] > boxes[1]:
            mismatches.append(f"Box 2a ({boxes['2a']}) > Box 1 ({boxes[1]})")

    result = {
        "form_type": "1099-R",
        "tax_year": tax_year,
        "payer": payer,
        "recipient": recipient,
        "plan_type": plan_type,
        "boxes": {
            "1_gross_distribution": boxes.get(1, 0.0),
            "2a_taxable_amount": boxes.get("2a", 0.0),
            "2b_taxable_not_determined": boxes.get("2b_not_determined", False),
            "2b_total_distribution": boxes.get("2b_total_distribution", False),
            "3_capital_gain": boxes.get(3, 0.0),
            "4_fed_tax_withheld": boxes.get(4, 0.0),
            "5_employee_contributions": boxes.get(5, 0.0),
            "6_net_unrealized_appreciation": boxes.get(6, 0.0),
            "7_distribution_code": distribution_code,
            "7_ira_sep_simple": ira_sep_simple,
        },
        "validation": {
            "taxable_le_gross": boxes.get("2a", 0) <= boxes.get(1, 0) if boxes.get(1) else True,
            "mismatches": mismatches,
        },
        "source": {
            "file": str(pdf_path),
            "pages": [1],
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        },
    }

    if account_number:
        result["account_number"] = account_number

    return result


# ---------------------------------------------------------------------------
# 1098 Parser (Mortgage Interest Statement)
# ---------------------------------------------------------------------------

def parse_1098(pdf_path: Path, tax_year: int) -> dict:
    """Parse Form 1098 (Mortgage Interest Statement)."""
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        # Combine text from all pages (some 1098s have cover pages)
        text = ""
        for page in pdf.pages:
            text += (page.extract_text(layout=True) or "") + "\n"

    lender = {"name": "", "tin": ""}
    borrower = {"name": "Yi Chen", "ssn_last4": "2622"}

    boxes = {}
    mismatches = []

    text_upper = text.upper()

    # Lender name
    if "ROCKET" in text_upper or "MRCOOPER" in text_upper or "MR. COOPER" in text_upper:
        lender["name"] = "Rocket Mortgage" if "ROCKET" in text_upper else "Mr. Cooper"
    elif "FLAGSTAR" in text_upper:
        lender["name"] = "Flagstar Bank"
    elif "LOANDEPOT" in text_upper or "LOAN DEPOT" in text_upper:
        lender["name"] = "loanDepot"

    # Lender TIN
    tin_m = re.search(r"TIN[#:]?\s*(\d{2}-\d{7})", text)
    if tin_m:
        lender["tin"] = tin_m.group(1)

    # Box 1: Mortgage interest received
    m = re.search(r"(?:Box 1|1\s+Mortgage interest|INTEREST RECEIVED FROM.*?PAYER.*?BORROWER).*?\$\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        boxes[1] = parse_amount(m.group(1))
    else:
        # Also check for "INTEREST PAID" on the cover page
        m = re.search(r"INTEREST PAID:\s*\$\s*([\d,]+\.\d{2})", text)
        if m:
            boxes["interest_paid"] = parse_amount(m.group(1))

    # Box 2: Outstanding mortgage principal
    m = re.search(r"(?:Box 2|2\s+Outstanding mortgage|BEG BAL).*?\$\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        boxes[2] = parse_amount(m.group(1))

    # Box 5: Mortgage insurance premiums
    m = re.search(r"(?:Box 5|5\s+Mortgage insurance).*?\$\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        boxes[5] = parse_amount(m.group(1))

    # Box 10: Property taxes
    m = re.search(r"(?:Box 10|10\s+(?:Real estate|Property) tax|PROPERTY TAXES).*?\$\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        boxes[10] = parse_amount(m.group(1))

    # Loan number
    loan_number = ""
    m = re.search(r"Loan\s*Number\s*(\d+)", text, re.IGNORECASE)
    if m:
        loan_number = m.group(1)
    elif re.search(r"ACCT\s*#:\s*(\d+)", text):
        loan_number = re.search(r"ACCT\s*#:\s*(\d+)", text).group(1)

    # Property address
    property_address = ""
    m = re.search(r"Property Address\s*\n?\s*(.+)", text)
    if m:
        property_address = m.group(1).strip()

    # Principal reconciliation
    ending_balance = None
    m = re.search(r"ENDING BAL:\s*\$\s*([\d,]+\.\d{2})", text)
    if m:
        ending_balance = parse_amount(m.group(1))

    applied_principal = None
    m = re.search(r"APPLIED BALANCE:\s*\$\s*([\d,]+\.\d{2})", text)
    if m:
        applied_principal = parse_amount(m.group(1))

    result = {
        "form_type": "1098",
        "tax_year": tax_year,
        "lender": lender,
        "borrower": {
            "name": borrower["name"],
            "ssn_last4": borrower["ssn_last4"],
        },
        "boxes": {
            "1_mortgage_interest": boxes.get(1, boxes.get("interest_paid", 0.0)),
            "2_outstanding_principal": boxes.get(2, 0.0),
            "5_mortgage_insurance": boxes.get(5, 0.0),
            "10_property_tax": boxes.get(10, 0.0),
        },
        "validation": {
            "has_interest": boxes.get(1, 0) > 0 or boxes.get("interest_paid", 0) > 0,
            "mismatches": mismatches,
        },
        "source": {
            "file": str(pdf_path),
            "pages": list(range(1, num_pages + 1)),
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        },
    }

    if loan_number:
        result["loan_number"] = loan_number
    if property_address:
        result["property_address"] = property_address
    if ending_balance is not None:
        result["ending_balance"] = ending_balance
    if applied_principal is not None:
        result["principal_applied"] = applied_principal

    return result


# ---------------------------------------------------------------------------
# 1099-INT Parser (Interest Income)
# ---------------------------------------------------------------------------

def parse_1099int(pdf_path: Path, tax_year: int) -> dict:
    """Parse Form 1099-INT (Interest Income).

    Handles BECU-style layout where box values appear inline with labels:
      1 Interest income ... $18.22
      2 Early withdrawal penalty
      3 Interest on U.S. Savings Bonds and Treasury obligations
      4 Federal income tax withheld
    Also checks for a summary table at the bottom of the page.
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text(layout=True) or ""
            text += page_text + "\n"
            # Only need the first page for form data
            if "Form 1099-INT" in page_text or "1099-INT" in page_text:
                break

    payer = {"name": "", "tin": ""}
    recipient = {"name": "Yi Chen", "ssn_last4": "2622"}
    boxes = {}
    account_number = ""

    text_upper = text.upper()

    # Payer name
    if "BOEING EMPLOYEES CREDIT UNION" in text_upper or "BECU" in text_upper:
        payer["name"] = "Boeing Employees Credit Union"
    elif "CAPITAL ONE" in text_upper:
        payer["name"] = "Capital One"
    elif "FIDELITY" in text_upper:
        payer["name"] = "Fidelity Investments"
    elif "CHASE" in text_upper:
        payer["name"] = "JPMorgan Chase"
    else:
        # Try to extract payer name from the first few lines
        for line in text.split("\n")[:15]:
            line = line.strip()
            if line and len(line) > 5 and not line.startswith("PAYER") and not line.startswith("RECIPIENT"):
                if re.match(r"^[A-Z][A-Z\s&.,]+$", line):
                    payer["name"] = line.title()
                    break

    # Payer TIN
    tin_matches = re.findall(r"(\d{2}-\d{7})", text)
    if tin_matches:
        payer["tin"] = tin_matches[0]

    # Recipient SSN
    ssn_m = re.search(r"(?:\*{3}-\*{2}-|xxx-xx-)(\d{4})", text, re.IGNORECASE)
    if ssn_m:
        recipient["ssn_last4"] = ssn_m.group(1)

    # Account number
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "Account number" in line and "see instructions" in line:
            # Account number may be on same line or next line
            m = re.search(r"(\d{8,})", line)
            if m:
                account_number = m.group(1)
            elif i + 1 < len(lines):
                m = re.search(r"(\d{8,})", lines[i + 1])
                if m:
                    account_number = m.group(1)
            break
    # Also check summary table for account number
    if not account_number:
        for line in lines:
            if "Account" in line and "Number" in line:
                continue
            m = re.search(r"^\s+(\d{8,})", line)
            if m:
                account_number = m.group(1)
                break

    # Calendar year
    year_m = re.search(r"(?:calendar year|For calendar year)\s*\n?\s*(\d{4})", text)
    if year_m:
        detected_year = int(year_m.group(1))
        if detected_year != tax_year:
            logger.warning(f"  1099-INT year mismatch: detected {detected_year}, expected {tax_year}")

    # Box 1: Interest income — look for dollar amount near "1 Interest income"
    m = re.search(r"1\s+Interest income.*?\$\s*([\d,]+\.\d{2})", text)
    if m:
        boxes[1] = parse_amount(m.group(1))

    # Box 2: Early withdrawal penalty
    m = re.search(r"2\s+Early withdrawal penalty.*?\$\s*([\d,]+\.\d{2})", text)
    if m:
        boxes[2] = parse_amount(m.group(1))

    # Box 3: Interest on U.S. Savings Bonds
    m = re.search(r"3\s+Interest on U\.?S\.?\s+Savings.*?\$\s*([\d,]+\.\d{2})", text)
    if m:
        boxes[3] = parse_amount(m.group(1))

    # Box 4: Federal income tax withheld
    m = re.search(r"4\s+Federal income tax withheld.*?\$\s*([\d,]+\.\d{2})", text)
    if m:
        boxes[4] = parse_amount(m.group(1))

    # Box 8: Tax-exempt interest
    m = re.search(r"8\s+Tax-exempt interest.*?\$\s*([\d,]+\.\d{2})", text)
    if m:
        boxes[8] = parse_amount(m.group(1))

    # Box 10: Market discount
    m = re.search(r"10\s+Market discount.*?\$\s*([\d,]+\.\d{2})", text)
    if m:
        boxes[10] = parse_amount(m.group(1))

    # Box 11: Bond premium
    m = re.search(r"11\s+Bond premium.*?\$\s*([\d,]+\.\d{2})", text)
    if m:
        boxes[11] = parse_amount(m.group(1))

    # Fallback: check summary table at bottom
    # Pattern: "3588947679  $18.22"
    if 1 not in boxes:
        for line in lines:
            m = re.search(r"\d{8,}\s+\$\s*([\d,]+\.\d{2})", line)
            if m:
                boxes[1] = parse_amount(m.group(1))
                break

    # Build result
    result = {
        "form_type": "1099-INT",
        "tax_year": tax_year,
        "payer": payer,
        "recipient": {
            "name": recipient["name"],
            "ssn_last4": recipient["ssn_last4"],
        },
        "boxes": {
            "1_interest_income": boxes.get(1, 0.0),
            "2_early_withdrawal_penalty": boxes.get(2, 0.0),
            "3_us_savings_bonds": boxes.get(3, 0.0),
            "4_fed_tax_withheld": boxes.get(4, 0.0),
        },
        "validation": {
            "has_interest": boxes.get(1, 0) > 0,
            "mismatches": [],
        },
        "source": {
            "file": str(pdf_path),
            "pages": [1],
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        },
    }

    # Add optional boxes only if they have values
    if boxes.get(8, 0) > 0:
        result["boxes"]["8_tax_exempt_interest"] = boxes[8]
    if boxes.get(10, 0) > 0:
        result["boxes"]["10_market_discount"] = boxes[10]
    if boxes.get(11, 0) > 0:
        result["boxes"]["11_bond_premium"] = boxes[11]
    if account_number:
        result["account_number"] = account_number

    return result


# ---------------------------------------------------------------------------
# 5498-SA Parser (HSA Contributions)
# ---------------------------------------------------------------------------

def parse_5498sa(pdf_path: Path, tax_year: int) -> dict:
    """Parse Form 5498-SA (HSA, Archer MSA, or Medicare Advantage MSA Information).

    Handles two layouts:
    1. Fidelity: labeled lines with dotted leaders (e.g., "2 Total HSA Contributions...7,749.96")
    2. HealthEquity: IRS form layout with positional amounts in boxes
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += (page.extract_text(layout=True) or "") + "\n"

    text_upper = text.upper()
    lines = text.split("\n")

    trustee = {"name": "", "tin": ""}
    participant = {"name": "Yi Chen", "ssn_last4": "2622"}
    boxes = {}
    account_number = ""
    account_type = ""

    # Trustee name
    if "HEALTHEQUITY" in text_upper or "HEALTH EQUITY" in text_upper:
        trustee["name"] = "HealthEquity"
    elif "FIDELITY" in text_upper or "NATIONAL FINANCIAL SERVICES" in text_upper:
        trustee["name"] = "Fidelity Investments"

    # Trustee TIN
    tin_m = re.search(r"TRUSTEE.S TIN[:\s]*(\d{2}-\d{7})", text)
    if tin_m:
        trustee["tin"] = tin_m.group(1)
    else:
        # HealthEquity format: TIN is on a separate line
        tin_matches = re.findall(r"(\d{2}-\d{7})", text)
        if tin_matches:
            trustee["tin"] = tin_matches[0]

    # Participant SSN
    ssn_m = re.search(r"(?:\*{3}-\*{2}-|\*{5}|xxx-xx-)(\d{4})", text, re.IGNORECASE)
    if ssn_m:
        participant["ssn_last4"] = ssn_m.group(1)

    # Participant name
    name_m = re.search(r"YI\s+CHEN", text, re.IGNORECASE)
    if name_m:
        participant["name"] = "Yi Chen"

    # Account number
    for i, line in enumerate(lines):
        if "Account number" in line or "Account No" in line:
            m = re.search(r"(\d[\d-]{4,})", line)
            if m:
                account_number = m.group(1)
            elif i + 1 < len(lines):
                m = re.search(r"(\d[\d-]{4,})", lines[i + 1])
                if m:
                    account_number = m.group(1)
            break
    # Fidelity puts account number in header
    if not account_number:
        m = re.search(r"Account No\.\s*Participant TIN.*?\n\s*.*?(\d{3}-\d{6})", text)
        if m:
            account_number = m.group(1)

    # --- Fidelity format: labeled lines with dotted leaders ---
    # "2 Total HSA Contributions made in 2023.................. 7,749.96"
    for line in lines:
        # Box 1: Employee/self-employed contributions
        m = re.search(r"1[.\s]+(?:Employee|self.employed).*?([\d,]+\.\d{2})\s*$", line)
        if m:
            boxes[1] = parse_amount(m.group(1))
            continue

        # Box 2: Total contributions
        m = re.search(r"2[.\s]+Total.*?(?:HSA\s+)?[Cc]ontributions.*?([\d,]+\.\d{2})\s*$", line)
        if m:
            boxes[2] = parse_amount(m.group(1))
            continue

        # Box 3: Contributions made in following year for current year
        m = re.search(r"3[.\s]+Total.*?(?:HSA|Archer).*?contributions.*?([\d,]+\.\d{2})\s*$", line)
        if m:
            boxes[3] = parse_amount(m.group(1))
            continue

        # Box 4: Rollover contributions
        m = re.search(r"4[.\s]+Rollover.*?([\d,]+\.\d{2})\s*$", line)
        if m:
            boxes[4] = parse_amount(m.group(1))
            continue

        # Box 5: Fair market value
        m = re.search(r"5[.\s]+Fair [Mm]ark(?:et|er) [Vv]alue.*?([\d,]+\.\d{2})\s*$", line)
        if m:
            boxes[5] = parse_amount(m.group(1))
            continue

        # Box 6: Account type (HSA, Archer MSA, MA MSA)
        m = re.search(r"6[.\s]+Account [Tt]ype.*?(HSA|Archer MSA|MA MSA)\s*$", line)
        if m:
            account_type = m.group(1)
            continue

    # --- HealthEquity IRS form format: positional amounts ---
    # Labels and amounts are often on separate lines. Find label lines, then
    # look at the same line or next line(s) for $amounts.
    if not boxes:
        for i, line in enumerate(lines):
            # Box 1: "contributionsmadein<YYYY>" (without "Total" or "for YYYY")
            if (re.search(r"contributions\s*made\s*in\s*\d{4}", line, re.IGNORECASE)
                    and not re.search(r"[Tt]otal", line)
                    and not re.search(r"for\s*\d{4}", line, re.IGNORECASE)
                    and 1 not in boxes):
                m = re.search(r"\$\s*([\d,]+\.\d{2})", line)
                if m:
                    boxes[1] = parse_amount(m.group(1))
                else:
                    for j in range(i + 1, min(i + 3, len(lines))):
                        m = re.search(r"\$\s*([\d,]+\.\d{2})", lines[j])
                        if m:
                            boxes[1] = parse_amount(m.group(1))
                            break

            # Box 2: "Total contributions made in YYYY" or "2Totalcontributions"
            if (re.search(r"[2Tt]otal\s*contributions\s*made\s*in\s*\d{4}", line, re.IGNORECASE)
                    and 2 not in boxes):
                m = re.search(r"\$\s*([\d,]+\.\d{2})", line)
                if m:
                    boxes[2] = parse_amount(m.group(1))
                else:
                    for j in range(i + 1, min(i + 3, len(lines))):
                        m = re.search(r"\$\s*([\d,]+\.\d{2})", lines[j])
                        if m:
                            boxes[2] = parse_amount(m.group(1))
                            break

            # Box 3: "contributions made in YYYY for YYYY"
            if (re.search(r"contributions\s*made\s*in\s*\d{4}\s*for\s*\d{4}", line, re.IGNORECASE)
                    and 3 not in boxes):
                m = re.search(r"\$\s*([\d,]+\.\d{2})", line)
                if m:
                    boxes[3] = parse_amount(m.group(1))
                else:
                    for j in range(i + 1, min(i + 3, len(lines))):
                        m = re.search(r"\$\s*([\d,]+\.\d{2})", lines[j])
                        if m:
                            boxes[3] = parse_amount(m.group(1))
                            break

            # Box 4 + 5: line with "Rollover contributions" label
            if re.search(r"[Rr]ollover\s*contributions", line) and 4 not in boxes:
                for j in range(i, min(i + 6, len(lines))):
                    amounts = re.findall(r"\$?\s*([\d,]+\.\d{2})", lines[j])
                    if len(amounts) >= 2:
                        boxes[4] = parse_amount(amounts[0])
                        boxes[5] = parse_amount(amounts[1])
                        break

    # Account type from checkbox (HealthEquity format: "6HSA   X")
    if not account_type:
        if re.search(r"6\s*HSA\s+X", text) or re.search(r"6HSA\s+X", text):
            account_type = "HSA"
        elif re.search(r"Archer\s*MSA\s+X", text):
            account_type = "Archer MSA"
        elif re.search(r"MA\s*MSA\s+X", text):
            account_type = "MA MSA"
        elif "HSA" in text_upper:
            account_type = "HSA"

    # Validation
    mismatches = []
    # Box 2 should be >= Box 1 (total contributions >= employee contributions)
    if boxes.get(1) and boxes.get(2) and boxes[2] < boxes[1]:
        mismatches.append(f"Box 2 ({boxes[2]}) < Box 1 ({boxes[1]})")

    result = {
        "form_type": "5498-SA",
        "tax_year": tax_year,
        "trustee": trustee,
        "participant": participant,
        "account_type": account_type,
        "boxes": {
            "1_employee_contributions": boxes.get(1, 0.0),
            "2_total_contributions": boxes.get(2, 0.0),
            "3_contributions_following_year": boxes.get(3, 0.0),
            "4_rollover_contributions": boxes.get(4, 0.0),
            "5_fair_market_value": boxes.get(5, 0.0),
        },
        "validation": {
            "has_contributions": boxes.get(1, 0) > 0 or boxes.get(2, 0) > 0,
            "mismatches": mismatches,
        },
        "source": {
            "file": str(pdf_path),
            "pages": [1],
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        },
    }

    if account_number:
        result["account_number"] = account_number

    return result


# ---------------------------------------------------------------------------
# 5498 Parser (IRA Contributions)
# ---------------------------------------------------------------------------

def parse_5498(pdf_path: Path, tax_year: int) -> dict:
    """Parse Form 5498 (IRA Contribution Information).

    Handles Fidelity format: labeled lines with dotted leaders.
    E.g., "1.IRA contributions...........$6,000.00"
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += (page.extract_text(layout=True) or "") + "\n"

    text_upper = text.upper()
    lines = text.split("\n")

    trustee = {"name": "", "tin": ""}
    participant = {"name": "Yi Chen", "ssn_last4": "2622"}
    boxes = {}
    account_number = ""
    ira_type = ""
    mismatches = []

    # Trustee name
    if "NATIONAL FINANCIAL SERVICES" in text_upper or "FIDELITY" in text_upper:
        trustee["name"] = "Fidelity Investments"

    # Trustee TIN
    tin_m = re.search(r"TRUSTEE.S.*?TIN[:\s]*(\d{2}-\d{7})", text)
    if tin_m:
        trustee["tin"] = tin_m.group(1)

    # Participant SSN
    ssn_m = re.search(r"(?:\*{3}-\*{2}-|xxx-xx-)(\d{4})", text, re.IGNORECASE)
    if ssn_m:
        participant["ssn_last4"] = ssn_m.group(1)

    # Account number (Fidelity header: "Account No. Participant TIN\n  226-518097")
    m = re.search(r"Account\s*No\..*?\n\s*.*?(\d{3}-\d{6})", text)
    if m:
        account_number = m.group(1)
    if not account_number:
        m = re.search(r"Account\s*Number\s+(\d{3}-\d{6})", text)
        if m:
            account_number = m.group(1)

    # Parse labeled lines
    for line in lines:
        # Box 1: IRA contributions
        m = re.search(r"1[.\s]+IRA contributions.*?\$\s*([\d,]+\.\d{2})", line)
        if m and 1 not in boxes:
            boxes[1] = parse_amount(m.group(1))

        # Box 2: Rollover contributions
        m = re.search(r"2[.\s]+Rollover contributions.*?\$\s*([\d,]+\.\d{2})", line)
        if m and 2 not in boxes:
            boxes[2] = parse_amount(m.group(1))

        # Box 3: Roth IRA conversion amount
        m = re.search(r"3[.\s]+Roth IRA conversion.*?\$\s*([\d,]+\.\d{2})", line)
        if m and 3 not in boxes:
            boxes[3] = parse_amount(m.group(1))

        # Box 4: Recharacterized contributions
        m = re.search(r"4[.\s]+Recharacterized contributions.*?\$\s*([\d,]+\.\d{2})", line)
        if m and 4 not in boxes:
            boxes[4] = parse_amount(m.group(1))

        # Box 5: Fair market value of account
        m = re.search(r"5[.\s]+Fair market value.*?\$\s*([\d,]+\.\d{2})", line)
        if m and 5 not in boxes:
            boxes[5] = parse_amount(m.group(1))

        # Box 7: IRA type
        m = re.search(r"7[.\s]+IRA [Tt]ype.*?(?:\.\s*){2,}([\w\s]+?)$", line)
        if m and not ira_type:
            ira_type = m.group(1).strip()

        # Box 10: Roth IRA contributions
        m = re.search(r"10[.\s]+Roth IRA contributions.*?\$\s*([\d,]+\.\d{2})", line)
        if m and 10 not in boxes:
            boxes[10] = parse_amount(m.group(1))

        # Box 11: Required minimum distribution
        # (often blank, just check if present)

        # Box 15a: FMV of certain specified assets
        m = re.search(r"15a[.\s]+FMV.*?\$\s*([\d,]+\.\d{2})", line)
        if m and "15a" not in boxes:
            boxes["15a"] = parse_amount(m.group(1))

        # Box 15b: Code(s)
        m = re.search(r"15b[.\s]+Code.*?(?:\.\s*){2,}([A-Z])\s*$", line)
        if m and "15b" not in boxes:
            boxes["15b"] = m.group(1)

    # Determine IRA type from filename or content if not from Box 7
    if not ira_type:
        fname_upper = pdf_path.name.upper()
        if "ROTH" in fname_upper or "ROTH" in text_upper:
            ira_type = "ROTH IRA"
        elif "TRADITIONAL" in fname_upper or ("TRADITIONAL" in text_upper and "IRA" in text_upper):
            ira_type = "IRA"
        elif "SEP" in text_upper:
            ira_type = "SEP IRA"
        elif "SIMPLE" in text_upper:
            ira_type = "SIMPLE IRA"

    result = {
        "form_type": "5498",
        "tax_year": tax_year,
        "trustee": trustee,
        "participant": participant,
        "ira_type": ira_type,
        "boxes": {
            "1_ira_contributions": boxes.get(1, 0.0),
            "2_rollover_contributions": boxes.get(2, 0.0),
            "3_roth_conversion": boxes.get(3, 0.0),
            "4_recharacterized": boxes.get(4, 0.0),
            "5_fair_market_value": boxes.get(5, 0.0),
        },
        "validation": {
            "has_data": any(boxes.get(k, 0) > 0 for k in [1, 2, 3, 5, 10]),
            "mismatches": mismatches,
        },
        "source": {
            "file": str(pdf_path),
            "pages": [1],
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        },
    }

    if boxes.get(10, 0) > 0:
        result["boxes"]["10_roth_ira_contributions"] = boxes[10]
    if boxes.get("15a", 0) > 0:
        result["boxes"]["15a_fmv_specified_assets"] = boxes["15a"]
    if boxes.get("15b"):
        result["boxes"]["15b_code"] = boxes["15b"]

    if account_number:
        result["account_number"] = account_number

    return result


# ---------------------------------------------------------------------------
# 1099-SA Parser (HSA/MSA Distributions)
# ---------------------------------------------------------------------------

def parse_1099sa(pdf_path: Path, tax_year: int) -> dict:
    """Parse Form 1099-SA (Distributions From an HSA, Archer MSA, or Medicare Advantage MSA).

    Handles:
    1. HealthEquity format: IRS form layout with positional amounts
    2. Fidelity format: labeled lines
    3. Blank IRS template forms (returns zeroed data)
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += (page.extract_text(layout=True) or "") + "\n"

    text_upper = text.upper()
    lines = text.split("\n")

    payer = {"name": "", "tin": ""}
    recipient = {"name": "Yi Chen", "ssn_last4": "2622"}
    boxes = {}
    account_number = ""
    account_type = ""

    # Check for blank IRS form template (no filled data)
    all_amounts = re.findall(r"[\d,]+\.\d{2}", text)
    if not all_amounts:
        logger.info(f"    1099-SA appears to be a blank IRS template: {pdf_path.name}")
        return {
            "form_type": "1099-SA",
            "tax_year": tax_year,
            "payer": payer,
            "recipient": recipient,
            "account_type": "HSA",
            "boxes": {
                "1_gross_distribution": 0.0,
                "2_earnings_excess_contributions": 0.0,
                "3_distribution_code": "",
                "4_fmv_on_death": 0.0,
            },
            "validation": {
                "has_distribution": False,
                "is_blank_template": True,
                "mismatches": [],
            },
            "source": {
                "file": str(pdf_path),
                "pages": [1],
                "processed_at": datetime.now().isoformat(timespec="seconds"),
            },
        }

    # Payer name
    if "HEALTHEQUITY" in text_upper or "HEALTH EQUITY" in text_upper:
        payer["name"] = "HealthEquity"
    elif "FIDELITY" in text_upper or "NATIONAL FINANCIAL SERVICES" in text_upper:
        payer["name"] = "Fidelity Investments"

    # Payer TIN
    tin_matches = re.findall(r"(\d{2}-\d{7})", text)
    if tin_matches:
        payer["tin"] = tin_matches[0]

    # Recipient SSN
    ssn_m = re.search(r"(?:\*{3}-\*{2}-|\*{5}|xxx-xx-)(\d{4})", text, re.IGNORECASE)
    if ssn_m:
        recipient["ssn_last4"] = ssn_m.group(1)

    # Account number
    for i, line in enumerate(lines):
        if "Account number" in line or "Account No" in line:
            m = re.search(r"(\d[\d-]{4,})", line)
            if m:
                account_number = m.group(1)
            elif i + 1 < len(lines):
                m = re.search(r"(\d[\d-]{4,})", lines[i + 1])
                if m:
                    account_number = m.group(1)
            break

    # Parse boxes
    for line in lines:
        # Box 1: Gross distribution
        m = re.search(r"1\s+Gross distribution.*?\$\s*([\d,]+\.\d{2})", line)
        if m and 1 not in boxes:
            boxes[1] = parse_amount(m.group(1))

        # Box 2: Earnings on excess contributions
        m = re.search(r"2\s+Earnings on excess.*?\$\s*([\d,]+\.\d{2})", line)
        if m and 2 not in boxes:
            boxes[2] = parse_amount(m.group(1))

        # Box 3: Distribution code
        m = re.search(r"3\s+Distribution code\s+(\d)", line)
        if m and 3 not in boxes:
            boxes[3] = m.group(1)

        # Box 4: FMV on date of death
        m = re.search(r"4\s+FMV.*?death.*?\$\s*([\d,]+\.\d{2})", line)
        if m and 4 not in boxes:
            boxes[4] = parse_amount(m.group(1))

    # Fidelity labeled format fallback
    if not boxes:
        for line in lines:
            m = re.search(r"Gross distribution.*?([\d,]+\.\d{2})", line)
            if m and 1 not in boxes:
                boxes[1] = parse_amount(m.group(1))

            m = re.search(r"Earnings on excess.*?([\d,]+\.\d{2})", line)
            if m and 2 not in boxes:
                boxes[2] = parse_amount(m.group(1))

            m = re.search(r"Distribution code.*?(\d)", line)
            if m and 3 not in boxes:
                boxes[3] = m.group(1)

    # Account type checkbox
    if re.search(r"5\s*HSA\s+X|5HSA\s+X", text):
        account_type = "HSA"
    elif re.search(r"Archer\s*MSA\s+X", text):
        account_type = "Archer MSA"
    elif re.search(r"MA\s*MSA\s+X", text):
        account_type = "MA MSA"
    elif "HSA" in text_upper:
        account_type = "HSA"

    # Distribution code description
    dist_code = str(boxes.get(3, ""))
    code_descriptions = {
        "1": "Normal distribution",
        "2": "Excess contributions",
        "3": "Disability",
        "4": "Death distribution (not to beneficiary)",
        "5": "Prohibited transaction",
        "6": "Death distribution to beneficiary",
    }

    # Validation
    mismatches = []

    result = {
        "form_type": "1099-SA",
        "tax_year": tax_year,
        "payer": payer,
        "recipient": recipient,
        "account_type": account_type,
        "boxes": {
            "1_gross_distribution": boxes.get(1, 0.0),
            "2_earnings_excess_contributions": boxes.get(2, 0.0),
            "3_distribution_code": dist_code,
            "4_fmv_on_death": boxes.get(4, 0.0),
        },
        "validation": {
            "has_distribution": boxes.get(1, 0) > 0,
            "mismatches": mismatches,
        },
        "source": {
            "file": str(pdf_path),
            "pages": [1],
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        },
    }

    if dist_code in code_descriptions:
        result["boxes"]["3_distribution_code_description"] = code_descriptions[dist_code]

    if account_number:
        result["account_number"] = account_number

    return result


# ---------------------------------------------------------------------------
# Schedule H Parser (Household Employment Taxes)
# ---------------------------------------------------------------------------

def parse_schedule_h(pdf_path: Path, tax_year: int) -> dict:
    """Parse Schedule H (Household Employment Taxes).

    The PDF has 3 pages: cover letter (page 1), Part I (page 2), Part II+III (page 3).
    The form layout differs slightly between years:
    - 2024+: Line 1 (no sub-letter), Line 2, Line 8
    - 2023: Line 1a, Line 2a/2b/2c, Line 8a/8d (COVID leave credits sub-lines)
    """
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        # Combine text from pages 2+ (skip cover letter on page 1)
        text = ""
        for page in pdf.pages[1:]:
            text += (page.extract_text(layout=True) or "") + "\n"

    lines_data = {}
    mismatches = []

    # --- Helper: extract the last dollar amount from a line ---
    # Schedule H lines have format: "2 Social security tax. Multiply line 1 by 12.4% (0.124) ... 2 732.84"
    # Using greedy .* ensures we skip past percentages like 0.124 and match the actual value at the end.

    def _last_amount_on_line(pattern: str) -> Optional[float]:
        """Search for pattern and return the last dollar amount on that line."""
        m = re.search(pattern + r".*?(\d[\d,]*\.\d{2})\s*$", text, re.MULTILINE)
        if m:
            return parse_amount(m.group(1))
        return None

    # --- Part I: Social Security, Medicare, and Federal Income Taxes ---

    # Line 1/1a: Total cash wages subject to social security tax
    # 2024 format: "1  Total cash wages..." / 2023 format: "1 a Total cash wages..."
    val = _last_amount_on_line(r"1\s*a?\s+Total cash wages subject to social security tax")
    if val is not None:
        lines_data["1_ss_wages"] = val

    # Line 2/2a: Social security tax
    val = _last_amount_on_line(r"2a?\s+Social security tax\.")
    if val is not None:
        lines_data["2_ss_tax"] = val

    # Line 2c: Total social security tax (2023 format with COVID sub-lines)
    val = _last_amount_on_line(r"2c\s+Total social security tax")
    if val is not None:
        lines_data["2c_total_ss_tax"] = val

    # Line 3: Total cash wages subject to Medicare tax
    val = _last_amount_on_line(r"3\s+Total cash wages subject to Medicare tax")
    if val is not None:
        lines_data["3_medicare_wages"] = val

    # Line 4: Medicare tax
    val = _last_amount_on_line(r"4\s+Medicare tax\.")
    if val is not None:
        lines_data["4_medicare_tax"] = val

    # Line 5: Additional Medicare Tax wages
    val = _last_amount_on_line(r"5\s+Total cash wages subject to Additional Medicare")
    if val is not None:
        lines_data["5_additional_medicare_wages"] = val
    else:
        m = re.search(r"5\s+Total cash wages subject to Additional Medicare.*?\s(\d+)\s*$", text, re.MULTILINE)
        if m:
            lines_data["5_additional_medicare_wages"] = float(m.group(1))

    # Line 6: Additional Medicare Tax withholding
    val = _last_amount_on_line(r"6\s+Additional Medicare Tax withholding")
    if val is not None:
        lines_data["6_additional_medicare_tax"] = val

    # Line 7: Federal income tax withheld
    val = _last_amount_on_line(r"7\s+Federal income tax withheld")
    if val is not None:
        lines_data["7_fed_income_tax_withheld"] = val

    # Line 8/8a: Total SS + Medicare + FIT
    val = _last_amount_on_line(r"8a?\s+Total social security, Medicare")
    if val is not None:
        lines_data["8_total_ss_medicare_fit"] = val

    # --- Part II: FUTA Tax (page 3) ---

    # Line 13: State name
    m = re.search(r"13\s+Name of the state.*?contributions\s+([\w\s]+?)(?:\s*\n|$)", text)
    if m:
        lines_data["13_state"] = m.group(1).strip()

    # Line 14: State unemployment contributions
    val = _last_amount_on_line(r"14\s+(?:Contributions paid|.*unemployment fund)")
    if val is not None:
        lines_data["14_state_unemployment_contributions"] = val

    # Line 15: Total cash wages subject to FUTA tax
    val = _last_amount_on_line(r"15\s+Total cash wages subject to FUTA tax")
    if val is not None:
        lines_data["15_futa_wages"] = val

    # Line 16: FUTA tax
    val = _last_amount_on_line(r"16\s+FUTA tax")
    if val is not None:
        lines_data["16_futa_tax"] = val

    # --- Part III: Total Household Employment Taxes ---

    # Line 25: Amount from line 8/8d
    val = _last_amount_on_line(r"25\s+Enter the amount from line 8")
    if val is not None:
        lines_data["25_subtotal_from_part1"] = val

    # Line 26: Total household employment taxes (line 16 + line 25)
    val = _last_amount_on_line(r"26\s+Add line 16")
    if val is not None:
        lines_data["26_total_household_taxes"] = val

    # --- Employer info ---
    employer_name = ""
    ein = ""
    ssn_last4 = ""

    m = re.search(r"Name of employer\s*\n\s*(.+?)(?:\s{3,}|\n)", text)
    if m:
        employer_name = m.group(1).strip()

    ein_m = re.search(r"Employer identification number\s*\n\s*(\d[\s\d]+)", text)
    if ein_m:
        ein_digits = re.sub(r"\s", "", ein_m.group(1))
        if len(ein_digits) >= 9:
            ein = f"{ein_digits[:2]}-{ein_digits[2:9]}"

    # SSN may be on same line or next line after "Social security number"
    ssn_m = re.search(r"Social security number\s*\n.*?(\d{9})", text, re.DOTALL)
    if not ssn_m:
        ssn_m = re.search(r"Social security number.*?(\d{9})", text)
    if ssn_m:
        ssn_last4 = ssn_m.group(1)[-4:]

    # --- Estimated payments from cover letter ---
    estimated_payments = []
    with pdfplumber.open(pdf_path) as pdf:
        cover_text = pdf.pages[0].extract_text(layout=True) or ""
    for m_pay in re.finditer(r"\|\s*([\w\s]+?\d+)\s*\|\s*\$([\d,]+\.\d{2})\s*\|\s*(\w+\s+\d+,\s*\d{4})\s*\|", cover_text):
        estimated_payments.append({
            "period": m_pay.group(1).strip(),
            "amount": parse_amount(m_pay.group(2)),
            "date_paid": m_pay.group(3).strip(),
        })

    # --- Validation ---
    line1 = lines_data.get("1_ss_wages", 0)
    line2 = lines_data.get("2c_total_ss_tax") or lines_data.get("2_ss_tax", 0)
    line3 = lines_data.get("3_medicare_wages", 0)
    line4 = lines_data.get("4_medicare_tax", 0)
    line6 = lines_data.get("6_additional_medicare_tax", 0)
    line7 = lines_data.get("7_fed_income_tax_withheld", 0)
    line8 = lines_data.get("8_total_ss_medicare_fit", 0)
    line15 = lines_data.get("15_futa_wages", 0)
    line16 = lines_data.get("16_futa_tax", 0)
    line25 = lines_data.get("25_subtotal_from_part1", 0)
    line26 = lines_data.get("26_total_household_taxes", 0)

    if line1 and line2:
        expected_ss = round(line1 * 0.124, 2)
        if abs(line2 - expected_ss) > 1.0:
            mismatches.append(f"Line 2 SS tax ({line2}) != Line 1 ({line1}) * 12.4% = {expected_ss}")

    if line3 and line4:
        expected_med = round(line3 * 0.029, 2)
        if abs(line4 - expected_med) > 1.0:
            mismatches.append(f"Line 4 Medicare tax ({line4}) != Line 3 ({line3}) * 2.9% = {expected_med}")

    if line8:
        expected_8 = round(line2 + line4 + line6 + line7, 2)
        if abs(line8 - expected_8) > 1.0:
            mismatches.append(f"Line 8 ({line8}) != sum of Lines 2+4+6+7 = {expected_8}")

    if line15 and line16:
        expected_futa = round(line15 * 0.006, 2)
        if abs(line16 - expected_futa) > 1.0:
            mismatches.append(f"Line 16 FUTA tax ({line16}) != Line 15 ({line15}) * 0.6% = {expected_futa}")

    if line25 and line26 and line16:
        expected_26 = round(line25 + line16, 2)
        if abs(line26 - expected_26) > 1.0:
            mismatches.append(f"Line 26 ({line26}) != Line 25 ({line25}) + Line 16 ({line16}) = {expected_26}")

    # --- Cross-validation: Schedule H Line 1 vs nanny W-2 Box 1 ---
    cross_validation = {}
    w2_dir = PREPARE_OUTPUT / str(tax_year)
    if w2_dir.exists():
        for yaml_file in sorted(w2_dir.glob("w-2-yi-chen*.yaml")):
            try:
                with open(yaml_file) as f:
                    w2_data = yaml.safe_load(f)
                if (w2_data and w2_data.get("form_type") == "W-2"
                        and w2_data.get("employer", {}).get("name") == "Yi Chen"):
                    w2_box1 = w2_data.get("boxes", {}).get("1_wages", 0)
                    sch_h_line1 = lines_data.get("1_ss_wages", 0)
                    match = abs(w2_box1 - sch_h_line1) < 1.0 if w2_box1 and sch_h_line1 else None
                    cross_validation["nanny_w2_file"] = str(yaml_file.relative_to(OBSIDIAN_ROOT))
                    cross_validation["nanny_w2_box1"] = w2_box1
                    cross_validation["schedule_h_line1"] = sch_h_line1
                    cross_validation["match"] = match
                    if match is False:
                        mismatches.append(
                            f"Schedule H Line 1 ({sch_h_line1}) != nanny W-2 Box 1 ({w2_box1})"
                        )
                    break
            except Exception:
                pass

    result = {
        "form_type": "Schedule-H",
        "tax_year": tax_year,
        "employer": {
            "name": employer_name or "Yi Chen",
            "ein": ein,
            "ssn_last4": ssn_last4,
        },
        "part1_ss_medicare_fit": {
            "1_ss_wages": lines_data.get("1_ss_wages", 0.0),
            "2_ss_tax": lines_data.get("2c_total_ss_tax") or lines_data.get("2_ss_tax", 0.0),
            "3_medicare_wages": lines_data.get("3_medicare_wages", 0.0),
            "4_medicare_tax": lines_data.get("4_medicare_tax", 0.0),
            "5_additional_medicare_wages": lines_data.get("5_additional_medicare_wages", 0.0),
            "6_additional_medicare_tax": lines_data.get("6_additional_medicare_tax", 0.0),
            "7_fed_income_tax_withheld": lines_data.get("7_fed_income_tax_withheld", 0.0),
            "8_total": lines_data.get("8_total_ss_medicare_fit", 0.0),
        },
        "part2_futa": {
            "13_state": lines_data.get("13_state", ""),
            "14_state_unemployment_contributions": lines_data.get("14_state_unemployment_contributions", 0.0),
            "15_futa_wages": lines_data.get("15_futa_wages", 0.0),
            "16_futa_tax": lines_data.get("16_futa_tax", 0.0),
        },
        "part3_total": {
            "25_subtotal_from_part1": lines_data.get("25_subtotal_from_part1", 0.0),
            "26_total_household_taxes": lines_data.get("26_total_household_taxes", 0.0),
        },
        "validation": {
            "ss_tax_check": abs(line2 - round(line1 * 0.124, 2)) <= 1.0 if line1 else True,
            "medicare_tax_check": abs(line4 - round(line3 * 0.029, 2)) <= 1.0 if line3 else True,
            "mismatches": mismatches,
        },
        "source": {
            "file": str(pdf_path),
            "pages": list(range(2, num_pages + 1)),
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        },
    }

    if cross_validation:
        result["cross_validation"] = cross_validation

    if estimated_payments:
        result["estimated_payments"] = estimated_payments

    return result




# ---------------------------------------------------------------------------
# Form 1040 Parser (Filed Tax Returns from Archive)
# ---------------------------------------------------------------------------

def _find_1040_pages(pdf) -> tuple[Optional[int], Optional[int]]:
    """Find the page indices for 1040 page 1 (income) and page 2 (tax/payments)."""
    page1_idx = None
    page2_idx = None
    for i, page in enumerate(pdf.pages):
        text = page.extract_text(layout=True) or ""
        if page1_idx is None and "1a" in text and "W-2" in text and (
            "total income" in text.lower() or "taxable income" in text.lower()
        ):
            page1_idx = i
        if page2_idx is None and "total tax" in text.lower() and (
            "total payments" in text.lower() or "25a" in text
        ):
            page2_idx = i
        if page1_idx is not None and page2_idx is not None:
            break
    return page1_idx, page2_idx


def parse_1040(pdf_path: Path, tax_year: int) -> dict:
    """Parse Form 1040 from a complete filed tax return PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        page1_idx, page2_idx = _find_1040_pages(pdf)
        if page1_idx is None:
            raise ValueError(f"Could not find 1040 page 1 in {pdf_path.name}")
        if page2_idx is None:
            raise ValueError(f"Could not find 1040 page 2 in {pdf_path.name}")
        page1_text = pdf.pages[page1_idx].extract_text(layout=True) or ""
        page2_text = pdf.pages[page2_idx].extract_text(layout=True) or ""
        cover_text = pdf.pages[0].extract_text(layout=True) or ""

    def extract_amount(text: str, line_prefix: str, keywords: list[str]) -> Optional[float]:
        """Extract dollar amount for a 1040 line, handling multiple CPA formats.

        Looks for the rightmost dollar amount on the matching line. If none found,
        checks the next line (for 2022 format where values are on separate lines),
        but only if that next line doesn't start a new form line.
        """
        lines_list = text.split("\n")
        for i, line in enumerate(lines_list):
            if not re.search(rf"\b{re.escape(line_prefix)}\b", line):
                continue
            if not any(kw.lower() in line.lower() for kw in keywords):
                continue
            # Find dollar amounts on this line — skip small numbers that are
            # form line references (e.g., "line 24" in "Subtract line 33 from line 24")
            amounts = re.findall(r"(-?[\d,]+\.\d{0,2})", line)
            # Filter: keep only amounts that look like real dollar values
            # (at least 2 digits before decimal, or preceded by $)
            real_amounts = []
            for amt_str in amounts:
                clean = amt_str.replace(",", "").lstrip("-")
                # Skip amounts that are just "N." where N < 100 and appear mid-line
                # (these are usually form line references like "24.")
                if clean.endswith(".") and len(clean.rstrip(".")) <= 2:
                    # Check if this is at end of line (real value) vs mid-line (reference)
                    pos = line.rfind(amt_str)
                    rest = line[pos + len(amt_str):].strip(". \t")
                    if rest:  # More text after it — likely a form reference
                        continue
                real_amounts.append(amt_str)
            if real_amounts:
                val_str = real_amounts[-1]
                if val_str.endswith("."):
                    val_str += "00"
                return parse_amount(val_str)

            # No amounts on the label line — check next line (2022 format)
            if i + 1 < len(lines_list):
                next_line = lines_list[i + 1]
                # Only use next line if it doesn't contain a new form label
                # (form labels have patterns like "11 Subtract" or "22 Subtract")
                if not re.match(r"\s*\d{1,2}\s+[A-Z]", next_line.strip()):
                    next_amounts = re.findall(r"(-?[\d,]+\.\d{0,2})", next_line)
                    if next_amounts:
                        val_str = next_amounts[-1]
                        if val_str.endswith("."):
                            val_str += "00"
                        return parse_amount(val_str)
        return None

    # Filing Status
    filing_status = "Unknown"
    if re.search(r"X\s*Married filing jointly", page1_text):
        filing_status = "Married Filing Jointly"
    elif re.search(r"X\s*Single", page1_text):
        filing_status = "Single"
    elif re.search(r"X\s*Head of household", page1_text):
        filing_status = "Head of Household"
    elif re.search(r"X\s*Married filing separately", page1_text):
        filing_status = "Married Filing Separately"
    elif re.search(r"X\s*Qualifying surviving spouse", page1_text):
        filing_status = "Qualifying Surviving Spouse"

    # Taxpayer and Spouse
    taxpayer = {"name": "Yi Chen", "ssn_last4": "2622"}
    spouse = {}
    if "515-94-3457" in page1_text:
        spouse = {"name": "Sheri Martin", "ssn_last4": "3457"}

    # Dependents
    dependents = []
    for dep_m in re.finditer(
        r"(Laurence|Ruby)\s+M?\s*Chen\s+(\d{3}-\d{2}-\d{4})\s+(\w+)", page1_text
    ):
        dependents.append({
            "name": f"{dep_m.group(1)} Chen",
            "ssn_last4": dep_m.group(2)[-4:],
            "relationship": dep_m.group(3),
        })

    # Income Lines (page 1)
    income = {}
    for key, prefix, kws in [
        ("1a_w2_wages", "1a", ["W-2", "Wages"]),
        ("1z_total_wages", "1z", ["Add lines"]),
        ("2b_taxable_interest", "2b", ["Taxable interest"]),
        ("3b_ordinary_dividends", "3b", ["Ordinary dividends", "dividends"]),
        ("4b_taxable_ira", "4b", ["Taxable amount"]),
        ("7_capital_gain_loss", "7", ["Capital gain"]),
        ("8_additional_income", "8", ["Additional income", "Schedule 1", "Other income"]),
    ]:
        val = extract_amount(page1_text, prefix, kws)
        if val is not None:
            income[key] = val

    # Summary Lines (page 1 + page 2)
    summary = {}
    for key, prefix, kws, src in [
        ("total_income", "9", ["total income"], page1_text),
        ("adjustments", "10", ["Adjustments"], page1_text),
        ("adjusted_gross_income", "11", ["adjusted gross income"], page1_text),
        ("deductions", "12", ["deduction", "Schedule A"], page1_text),
        ("taxable_income", "15", ["taxable income"], page1_text),
        ("tax_line16", "16", ["Tax"], page2_text),
        ("total_tax", "24", ["total tax"], page2_text),
        ("w2_withholding", "25a", ["W-2"], page2_text),
        ("total_withholding", "25d", ["Add lines"], page2_text),
        ("estimated_payments", "26", ["estimated tax"], page2_text),
        ("total_payments", "33", ["total payments"], page2_text),
    ]:
        val = extract_amount(src, prefix, kws)
        if val is not None:
            summary[key] = val

    # Refund / amount owed
    overpaid = extract_amount(page2_text, "34", ["overpaid", "overpay"])
    owed = extract_amount(page2_text, "37", ["amount you owe"])
    if owed and owed > 0:
        summary["refund_or_owed"] = owed
    elif overpaid and overpaid > 0:
        summary["refund_or_owed"] = -overpaid
    else:
        summary["refund_or_owed"] = 0.0

    # Cross-check with cover letter
    cover_owed = None
    cover_refund = None
    m = re.search(r"amount you owe.*?\$([\d,]+)", cover_text, re.IGNORECASE)
    if m:
        cover_owed = parse_amount(m.group(1))
    m = re.search(r"(?:overpaid|refund).*?\$([\d,]+)", cover_text, re.IGNORECASE)
    if m:
        cover_refund = parse_amount(m.group(1))

    # Validation
    mismatches = []
    if summary.get("total_income") and summary.get("adjusted_gross_income"):
        adj = summary.get("adjustments", 0)
        expected_agi = summary["total_income"] - adj
        if abs(expected_agi - summary["adjusted_gross_income"]) > 1:
            mismatches.append(
                f"AGI ({summary['adjusted_gross_income']}) != total_income ({summary['total_income']}) - adjustments ({adj})"
            )
    if summary.get("total_tax") is not None and summary["total_tax"] == 0:
        mismatches.append("Total tax is 0 -- may indicate extraction failure")
    if cover_owed and owed and abs(cover_owed - owed) > 1:
        mismatches.append(f"Cover letter owed (${cover_owed}) != line 37 (${owed})")
    if cover_refund and overpaid and abs(cover_refund - overpaid) > 1:
        mismatches.append(f"Cover letter refund (${cover_refund}) != line 34 (${overpaid})")

    result = {
        "form_type": "1040",
        "tax_year": tax_year,
        "filing_status": filing_status,
        "taxpayer": taxpayer,
    }
    if spouse:
        result["spouse"] = spouse
    if dependents:
        result["dependents"] = dependents
    result["income"] = income
    result["summary"] = summary
    result["validation"] = {
        "all_key_fields_present": all([
            summary.get("adjusted_gross_income"),
            summary.get("taxable_income"),
            summary.get("total_tax"),
            summary.get("total_payments"),
        ]),
        "mismatches": mismatches,
    }
    result["source"] = {
        "file": str(pdf_path),
        "pages": [page1_idx + 1, page2_idx + 1],
        "processed_at": datetime.now().isoformat(timespec="seconds"),
    }
    return result


def process_archive_pdf(pdf_path: Path, year: int) -> dict:
    """Process an archive PDF (complete filed tax return)."""
    name_lower = pdf_path.name.lower()

    skip_keywords = ["receipt", "extension", "payment", "ack"]
    if any(kw in name_lower for kw in skip_keywords):
        return {
            "status": "skipped",
            "reason": "non_return_archive_file",
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        }

    is_return = any(kw in name_lower for kw in ["tax return", "tax_return", "tax-final", "1040"])
    if not is_return:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i in range(min(10, len(pdf.pages))):
                    text = pdf.pages[i].extract_text(layout=True) or ""
                    if "Form 1040" in text or "mroF 1040" in text or "U.S. Individual Income Tax Return" in text:
                        is_return = True
                        break
        except Exception:
            pass

    if not is_return:
        return {
            "status": "skipped",
            "reason": "not_a_tax_return",
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        }

    data = parse_1040(pdf_path, year)
    output_path = ARCHIVE_OUTPUT / str(year) / "1040-summary.yaml"
    write_yaml(data, output_path)

    validation = data.get("validation", {})
    has_mismatches = bool(validation.get("mismatches"))

    return {
        "status": "success",
        "form_type": "1040",
        "output_file": str(output_path.relative_to(OBSIDIAN_ROOT)),
        "validation_ok": not has_mismatches,
        "mismatches": validation.get("mismatches", []),
        "processed_at": datetime.now().isoformat(timespec="seconds"),
    }


# ---------------------------------------------------------------------------
# Main Processing
# ---------------------------------------------------------------------------

SUPPORTED_FORMS = {"W-2", "1099-R", "1098", "1099-INT", "5498-SA", "5498", "1099-SA", "Schedule-H"}
SKIP_FORMS = {"1095-C", "3922"}  # Informational only, not needed for tax filing

# Filename patterns that are NOT tax forms (vehicle registrations, etc.)
NON_TAX_FILENAME_PATTERNS = ["renew", "tabs", "acura", "trailer", "vehicle"]


def process_pdf(pdf_path: Path, year: int) -> dict:
    """Process a single tax PDF. Returns result dict."""
    form_type = detect_form_type(pdf_path)

    if form_type is None:
        return {
            "status": "skipped",
            "reason": "unrecognized_form",
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        }

    if form_type in SKIP_FORMS:
        return {
            "status": "skipped",
            "reason": f"form_{form_type}_not_needed",
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        }

    if form_type not in SUPPORTED_FORMS:
        return {
            "status": "skipped",
            "reason": f"unsupported_form_{form_type}",
            "form_type": form_type,
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        }

    # Parse
    if form_type == "W-2":
        data = parse_w2(pdf_path, year)
    elif form_type == "1099-R":
        data = parse_1099r(pdf_path, year)
    elif form_type == "1098":
        data = parse_1098(pdf_path, year)
    elif form_type == "1099-INT":
        data = parse_1099int(pdf_path, year)
    elif form_type == "5498-SA":
        data = parse_5498sa(pdf_path, year)
    elif form_type == "5498":
        data = parse_5498(pdf_path, year)
    elif form_type == "1099-SA":
        data = parse_1099sa(pdf_path, year)
    elif form_type == "Schedule-H":
        data = parse_schedule_h(pdf_path, year)
    else:
        return {"status": "skipped", "reason": f"no_parser_for_{form_type}"}

    # Determine output filename
    slug = _make_output_slug(form_type, data, pdf_path)
    output_path = PREPARE_OUTPUT / str(year) / f"{slug}.yaml"

    # Write YAML
    write_yaml(data, output_path)

    # Check for validation failures
    validation = data.get("validation", {})
    has_mismatches = bool(validation.get("mismatches"))

    return {
        "status": "success",
        "form_type": form_type,
        "output_file": str(output_path.relative_to(OBSIDIAN_ROOT)),
        "validation_ok": not has_mismatches,
        "mismatches": validation.get("mismatches", []),
        "processed_at": datetime.now().isoformat(timespec="seconds"),
    }


def _make_output_slug(form_type: str, data: dict, pdf_path: Path) -> str:
    """Generate a descriptive filename slug for the output YAML.

    Must be unique per source PDF to avoid collisions (e.g. multiple 1099-Rs).
    """
    parts = [form_type.lower()]

    if form_type == "W-2":
        emp_name = data.get("employer", {}).get("name", "")
        if emp_name:
            slug = re.sub(r"[^a-z0-9]", "-", emp_name.lower()).strip("-")
            slug = re.sub(r"-+", "-", slug)
            parts.append(slug[:30])
        else:
            parts.append(_sanitize_stem(pdf_path.stem))
    elif form_type == "1099-R":
        payer = data.get("payer", {}).get("name", "")
        plan = data.get("plan_type", "")
        if payer:
            slug = re.sub(r"[^a-z0-9]", "-", payer.lower()).strip("-")
            slug = re.sub(r"-+", "-", slug)
            parts.append(slug[:30])
        # Add plan type or source filename to ensure uniqueness
        if plan:
            parts.append(re.sub(r"[^a-z0-9]", "-", plan.lower()).strip("-"))
        else:
            parts.append(_sanitize_stem(pdf_path.stem)[:20])
    elif form_type == "1098":
        lender = data.get("lender", {}).get("name", "")
        if lender:
            slug = re.sub(r"[^a-z0-9]", "-", lender.lower()).strip("-")
            slug = re.sub(r"-+", "-", slug)
            parts.append(slug[:30])
        else:
            parts.append(_sanitize_stem(pdf_path.stem))
        # Add loan number for uniqueness (multiple mortgages)
        loan = data.get("loan_number", "")
        if loan:
            parts.append(loan[-6:])
    elif form_type == "1099-INT":
        payer = data.get("payer", {}).get("name", "")
        if payer:
            slug = re.sub(r"[^a-z0-9]", "-", payer.lower()).strip("-")
            slug = re.sub(r"-+", "-", slug)
            parts.append(slug[:30])
        else:
            parts.append(_sanitize_stem(pdf_path.stem))
        # Add account number for uniqueness (multiple accounts at same institution)
        acct = data.get("account_number", "")
        if acct:
            parts.append(acct[-6:])
    elif form_type == "5498-SA":
        trustee = data.get("trustee", {}).get("name", "")
        if trustee:
            slug = re.sub(r"[^a-z0-9]", "-", trustee.lower()).strip("-")
            slug = re.sub(r"-+", "-", slug)
            parts.append(slug[:30])
        else:
            parts.append(_sanitize_stem(pdf_path.stem))
        acct = data.get("account_number", "")
        if acct:
            parts.append(acct[-6:])
    elif form_type == "5498":
        trustee = data.get("trustee", {}).get("name", "")
        if trustee:
            slug = re.sub(r"[^a-z0-9]", "-", trustee.lower()).strip("-")
            slug = re.sub(r"-+", "-", slug)
            parts.append(slug[:30])
        # Add IRA type for uniqueness (Roth vs Traditional)
        ira_type = data.get("ira_type", "")
        if ira_type:
            parts.append(re.sub(r"[^a-z0-9]", "-", ira_type.lower()).strip("-"))
        else:
            parts.append(_sanitize_stem(pdf_path.stem)[:20])
        acct = data.get("account_number", "")
        if acct:
            parts.append(acct[-6:])
    elif form_type == "1099-SA":
        payer_name = data.get("payer", {}).get("name", "")
        if payer_name:
            slug = re.sub(r"[^a-z0-9]", "-", payer_name.lower()).strip("-")
            slug = re.sub(r"-+", "-", slug)
            parts.append(slug[:30])
        else:
            parts.append(_sanitize_stem(pdf_path.stem))
        acct = data.get("account_number", "")
        if acct:
            parts.append(acct[-6:])
    elif form_type == "Schedule-H":
        # Only one Schedule H per year, so just use employer name
        emp_name = data.get("employer", {}).get("name", "")
        if emp_name:
            slug = re.sub(r"[^a-z0-9]", "-", emp_name.lower()).strip("-")
            slug = re.sub(r"-+", "-", slug)
            parts.append(slug[:30])

    return "-".join(parts)


def _sanitize_stem(stem: str) -> str:
    """Convert a filename stem to a safe slug."""
    slug = re.sub(r"[^a-z0-9]", "-", stem.lower()).strip("-")
    return re.sub(r"-+", "-", slug)[:30]


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------

def run_scan(year_filter: Optional[int] = None, source: str = "prepare"):
    """Scan for tax PDFs and report what's found."""
    processing_log = load_processing_log()
    years = [year_filter] if year_filter else YEARS

    total_pdfs = 0
    total_new = 0
    total_supported = 0
    total_unsupported = 0

    for year in years:
        if source == "prepare":
            pdfs = discover_prepare_pdfs(year)
        else:
            pdfs = discover_archive_pdfs(year)

        if not pdfs:
            continue

        new_pdfs = [p for p in pdfs if not is_processed(processing_log, p)]
        logger.info(f"\n  {year}: {len(new_pdfs)} new / {len(pdfs)} total PDFs")

        for pdf_path in pdfs:
            form_type = detect_form_type(pdf_path)
            processed = is_processed(processing_log, pdf_path)
            status = "OK" if processed else "NEW"
            supported = form_type in SUPPORTED_FORMS if form_type else False

            if form_type in SKIP_FORMS:
                form_label = f"{form_type} (skip)"
            elif form_type and supported:
                form_label = form_type
                total_supported += 1
            elif form_type:
                form_label = f"{form_type} (unsupported)"
                total_unsupported += 1
            else:
                form_label = "???"
                total_unsupported += 1

            color = "\033[32m" if processed else ("\033[33m" if supported else "\033[90m")
            logger.info(f"    {color}{status:3s}\033[0m [{form_label:20s}] {pdf_path.name}")

            total_pdfs += 1
            if not processed:
                total_new += 1

    logger.info(f"\n  Total: {total_new} new / {total_pdfs} total PDFs ({total_supported} supported, {total_unsupported} unsupported/unknown)")


def run_ingest(year_filter: Optional[int] = None, source: str = "prepare", force: bool = False):
    """Process tax PDFs and generate YAML files."""
    processing_log = load_processing_log() if not force else {"version": 1, "last_run": None, "files": {}}
    years = [year_filter] if year_filter else YEARS

    total_success = 0
    total_skipped = 0
    total_errors = 0
    validation_failures = []

    for year in years:
        if source == "prepare":
            pdfs = discover_prepare_pdfs(year)
        else:
            pdfs = discover_archive_pdfs(year)

        if not pdfs:
            continue

        new_pdfs = [p for p in pdfs if force or not is_processed(processing_log, p)]
        if not new_pdfs:
            continue

        logger.info(f"\n  Processing {year} ({len(new_pdfs)} PDFs)...")

        for pdf_path in new_pdfs:
            try:
                if source == "archive":
                    result = process_archive_pdf(pdf_path, year)
                else:
                    result = process_pdf(pdf_path, year)
                record_result(processing_log, pdf_path, result)

                if result["status"] == "success":
                    total_success += 1
                    warn = ""
                    if not result.get("validation_ok", True):
                        warn = f" \033[33m⚠ VALIDATION: {result['mismatches']}\033[0m"
                        validation_failures.append((pdf_path.name, result["mismatches"]))
                    logger.info(f"    \033[32mOK\033[0m [{result['form_type']:8s}] {pdf_path.name} -> {result['output_file']}{warn}")
                elif result["status"] == "skipped":
                    total_skipped += 1
                    logger.info(f"    \033[90mSKIP\033[0m {pdf_path.name} ({result.get('reason', '')})")

            except Exception as e:
                total_errors += 1
                record_result(processing_log, pdf_path, {
                    "status": "error",
                    "error": str(e),
                    "processed_at": datetime.now().isoformat(timespec="seconds"),
                })
                logger.error(f"    \033[31mFAIL\033[0m {pdf_path.name}: {e}")

        # Save after each year
        save_processing_log(processing_log)

    logger.info(f"\n  Done: {total_success} succeeded, {total_skipped} skipped, {total_errors} errors")

    if validation_failures:
        logger.warning("\n  ⚠ VALIDATION FAILURES:")
        for name, issues in validation_failures:
            for issue in issues:
                logger.warning(f"    {name}: {issue}")


# --- CLI ---
def main():
    parser = argparse.ArgumentParser(
        description="Tax document PDF ingestion pipeline",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scan", action="store_true", help="Show tax PDFs and their form types (no processing)")
    group.add_argument("--run", action="store_true", help="Process new PDFs and generate YAML")

    parser.add_argument("--year", type=int, choices=YEARS, help="Process only this year")
    parser.add_argument("--source", choices=["prepare", "archive"], default="prepare", help="Which folder to process")
    parser.add_argument("--force", action="store_true", help="Re-process everything (ignore processing log)")

    args = parser.parse_args()

    setup_logging()
    logger.info(f"Tax Document Ingestion — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if args.scan:
        run_scan(year_filter=args.year, source=args.source)
    elif args.run:
        run_ingest(year_filter=args.year, source=args.source, force=args.force)


if __name__ == "__main__":
    main()
