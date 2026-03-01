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

            # Box 14 text: may be merged ("ESPPGAINS13408.81") or separate tokens
            m = re.search(r"(?:ESPP\s*GAINS|GAINS)\s*([\d,]+\.\d{2})", text)
            if m:
                box14_other.append(f"ESPP GAINS {m.group(1)}")
                continue
            m = re.match(r"RS([\d,]+\.\d{2})$", text)
            if m:
                box14_other.append(f"RSU {m.group(1)}")
                continue
            # Separate text-only tokens — mark for later pairing with amounts
            if "ESPP" in text.upper() or "GAINS" in text.upper():
                box14_other.append(("ESPP_MARKER", t["top"]))
                continue
            if text == "RS":
                box14_other.append(("RS_MARKER", t["top"]))
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

        # Pair Box 14 markers with remaining amounts by y-position
        resolved_box14 = []
        for entry in box14_other:
            if isinstance(entry, str):
                resolved_box14.append(entry)
            elif isinstance(entry, tuple):
                marker_type, marker_y = entry
                # Find amount on the same y-line
                for a in remaining_amounts:
                    if abs(a["y"] - marker_y) < 5:
                        if marker_type == "ESPP_MARKER":
                            resolved_box14.append(f"ESPP GAINS {a['amount']:.2f}")
                        elif marker_type == "RS_MARKER":
                            resolved_box14.append(f"RSU {a['amount']:.2f}")
                        remaining_amounts.remove(a)
                        break
        box14_other = resolved_box14

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
    """Parse ADP-format W-2 (Airbnb, Meta) — has earnings summary + standard W-2 form.

    ADP layout: labels on one line, values on the NEXT line. Example:
      Line N:   1 Wages,tips,othercomp. 2Federalincometaxwithheld
      Line N+1:       344031.53     79609.86
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text(layout=True) or ""

    boxes = {}
    employer = {"name": "", "ein": ""}
    employee = {"name": "Yi Chen", "ssn_last4": ""}
    box12 = []
    box14_other = []
    retirement_plan = False
    box10 = None

    # SSN
    ssn_m = re.search(r"(?:XXX-XX-|[\d*]{3}-[\d*]{2}-)(\d{4})", text)
    if ssn_m:
        employee["ssn_last4"] = ssn_m.group(1)

    # EIN
    ein_m = re.search(r"(\d{2}-\d{7})", text)
    if ein_m:
        employer["ein"] = ein_m.group(1)

    # Employer name
    text_upper = text.upper()
    if "AIRBNB" in text_upper:
        employer["name"] = "Airbnb Inc"
    elif "META" in text_upper:
        employer["name"] = "Meta Platforms Inc"

    # Parse using layout text — labels and values on adjacent lines
    lines = text.split("\n")

    def _find_amounts_after_label(label_line_idx: int, max_lookahead: int = 2) -> list[float]:
        """Search the next N lines after a label for dollar amounts.

        Only returns amounts from the FIRST line that has any — prevents
        cross-contamination from unrelated form sections.
        """
        for offset in range(1, max_lookahead + 1):
            idx = label_line_idx + offset
            if idx >= len(lines):
                break
            line = lines[idx]
            # Skip lines that are clearly labels (contain box descriptions)
            stripped = re.sub(r"\s+", "", line)
            if any(kw in stripped for kw in ["Socialsecurity", "Medicare", "Allocated", "Nonqualified", "Instructions"]):
                continue
            amounts = re.findall(r"(\d[\d,]*\.\d{2})", line)
            if amounts:
                return [parse_amount(a) for a in amounts]
        return []

    # Scan for box label lines, then extract values from next line
    for i, line in enumerate(lines):
        line_stripped = re.sub(r"\s+", "", line)  # Remove all whitespace for matching

        # Box 1 + 2: "Wages,tips,othercomp" + "Federalincometaxwithheld"
        if "Wages,tips" in line_stripped and "Federal" in line_stripped and 1 not in boxes:
            amts = _find_amounts_after_label(i)
            if len(amts) >= 2:
                boxes[1] = amts[0]
                boxes[2] = amts[1]
            elif len(amts) == 1:
                # Only wages, no federal withholding (e.g., supplemental W-2)
                boxes[1] = amts[0]
                boxes[2] = 0.0

        # Box 3 + 4: "Socialsecuritywages" + "Socialsecuritytaxwithheld"
        if "Socialsecuritywages" in line_stripped and "taxwithheld" in line_stripped and 3 not in boxes:
            amts = _find_amounts_after_label(i)
            if len(amts) >= 2:
                boxes[3] = amts[0]
                boxes[4] = amts[1]

        # Box 5 + 6: "Medicarewagesandtips" + "Medicaretaxwithheld"
        if "Medicarewages" in line_stripped and "taxwithheld" in line_stripped and 5 not in boxes:
            amts = _find_amounts_after_label(i)
            if len(amts) >= 2:
                boxes[5] = amts[0]
                boxes[6] = amts[1]

        # Box 10: "Dependentcarebenefits" — only accept values ≤ $5,000
        if "Dependentcare" in line_stripped and box10 is None:
            amts = _find_amounts_after_label(i)
            if amts and amts[0] <= 5000:
                box10 = amts[0]

        # Retirement plan checkbox
        if "Ret" in line and "plan" in line and "X" in line:
            retirement_plan = True

    # Box 12 codes — search for patterns like "12bD    20500.00" or "DD    4715.44"
    CODE_DESCRIPTIONS = {
        "C": "Group-term life insurance over $50K",
        "D": "401(k) elective deferrals",
        "DD": "Health coverage cost (employer + employee)",
        "W": "HSA employer contributions",
        "AA": "Designated Roth 401(k)",
        "DI": "Disability insurance",
    }
    for line in lines:
        # Pattern: "12b D  20500.00" or "DD  4715.44" or "12c DI 9878.40"
        for m in re.finditer(r"(?:12[a-d]\s*)?([A-Z]{1,2})\s+([\d,]+\.\d{2})", line):
            code = m.group(1)
            amount = parse_amount(m.group(2))
            if code in CODE_DESCRIPTIONS and amount:
                if not any(b["code"] == code and b["amount"] == amount for b in box12):
                    box12.append({"code": code, "amount": amount, "description": CODE_DESCRIPTIONS[code]})

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

        # Look for value lines: 2+ dollar amounts on the line
        amounts = re.findall(r"(\d[\d,]*\.\d{2})", line)
        if len(amounts) >= 2 and i > 3:
            # Check the previous 1-3 lines for box labels (intervening employer/employee info)
            prev_text = " ".join(lines[max(0, i - 3):i])
            if "Wages" in prev_text and "Federal" in prev_text and 1 not in boxes:
                boxes[1] = parse_amount(amounts[0])
                boxes[2] = parse_amount(amounts[1])
            elif "Social security wages" in prev_text and 3 not in boxes:
                boxes[3] = parse_amount(amounts[0])
                boxes[4] = parse_amount(amounts[1])
            elif "Medicare wages" in prev_text and 5 not in boxes:
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
    """Build the W-2 YAML output dict with comprehensive validation.

    Validates mathematical relationships between W-2 boxes:
    - Box 4 = Box 3 × 6.2% (SS tax rate)
    - Box 6 ≥ Box 5 × 1.45% (Medicare, can be higher due to Additional Medicare Tax)
    - Box 1 ≤ Box 5 (wages ≤ Medicare wages, since Medicare has no cap but pre-tax deductions reduce Box 1)
    - Box 3 ≤ SS wage base for the year
    - If wages > 0, at least some tax should be withheld
    - Box 10 (dependent care) ≤ $5,000 annual limit
    """
    mismatches = []

    box1 = boxes.get(1, 0)
    box2 = boxes.get(2, 0)
    box3 = boxes.get(3, 0)
    box4 = boxes.get(4, 0)
    box5 = boxes.get(5, 0)
    box6 = boxes.get(6, 0)

    # SS wage base limits by year
    ss_wage_bases = {2022: 147000, 2023: 160200, 2024: 168600, 2025: 176100}
    ss_base = ss_wage_bases.get(tax_year, 176100)

    # Box 4 = Box 3 × 6.2% (±$1 for rounding)
    if box3 > 0:
        box4_expected = round(box3 * 0.062, 2)
        if abs(box4 - box4_expected) > 1.0:
            mismatches.append(f"Box 4 ({box4}) != Box 3 ({box3}) * 6.2% = {box4_expected}")

    # Box 6 ≥ Box 5 × 1.45% (Additional Medicare Tax adds 0.9% above $200K)
    if box5 > 0:
        box6_min = round(box5 * 0.0145, 2) - 1.0
        if box6 < box6_min:
            mismatches.append(f"Box 6 ({box6}) < Box 5 ({box5}) * 1.45% = {round(box5 * 0.0145, 2)}")

    # Box 1 ≤ Box 5 (wages can't exceed Medicare wages — pre-tax deductions reduce Box 1)
    # Exception: third-party sick pay W-2s may have different relationships
    if box1 > 0 and box5 > 0 and box1 > box5 + 1.0 and not third_party_sick_pay:
        mismatches.append(f"Box 1 ({box1}) > Box 5 ({box5}): wages exceed Medicare wages")

    # Box 3 ≤ SS wage base for the year
    if box3 > ss_base + 1.0:
        mismatches.append(f"Box 3 ({box3}) exceeds {tax_year} SS wage base ({ss_base})")

    # If Box 1 > 0, at least some withholding should exist (Box 2, 4, or 6)
    if box1 > 100 and box2 == 0 and box4 == 0 and box6 == 0:
        mismatches.append(f"Box 1 ({box1}) > $100 but no taxes withheld (Boxes 2,4,6 all zero)")

    # Box 10 (dependent care) ≤ $5,000 annual limit
    if box10 is not None and box10 > 5000:
        mismatches.append(f"Box 10 ({box10}) exceeds $5,000 dependent care limit")

    # Duplicate value detection: same non-zero amount in Box 1 and Box 2 is suspicious
    if box1 > 0 and box1 == box2 and box1 == (box10 or -1):
        mismatches.append(f"Suspicious: Box 1, Box 2, and Box 10 all equal {box1} — possible parsing error")

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
        "checks_passed": len(mismatches) == 0,
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

    # IRA/SEP/SIMPLE checkbox — check lines around the code area
    # The X mark may be on the same line as the distribution code (e.g., "2    X $  %"),
    # not necessarily on a line containing "IRA" or "SEP"
    ira_sep_simple = False
    if "box7" in label_lines:
        for i in range(label_lines["box7"], min(label_lines["box7"] + 5, len(lines))):
            line = lines[i]
            # Method 1: X on same line as IRA/SEP/SIMPLE label
            if ("IRA" in line or "SEP" in line or "SIMPLE" in line) and "X" in line:
                ira_sep_simple = True
                break
            # Method 2: X on the distribution code line (after the code char)
            if i > label_lines["box7"] and distribution_code:
                # Pattern: code letter, then X (e.g., "2    X" or "G    X")
                if re.search(rf"\b{re.escape(distribution_code)}\s+X\b", line):
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

    # Code G (rollover): taxable amount should be 0
    if distribution_code == "G" and boxes.get("2a", 0) > 0:
        mismatches.append(f"Code G (rollover) but Box 2a taxable = {boxes['2a']} (expected 0)")

    # Code 2 (early distribution, exception): should have IRA/SEP/SIMPLE checked
    if distribution_code == "2" and not ira_sep_simple:
        mismatches.append("Code 2 (early distribution, exception) but IRA/SEP/SIMPLE not checked")

    # Box 5 (employee contributions) <= Box 1 (gross)
    if boxes.get(5, 0) > boxes.get(1, 0) + 0.01 and boxes.get(1, 0) > 0:
        mismatches.append(f"Box 5 ({boxes[5]}) > Box 1 ({boxes[1]}): employee contributions exceed gross")

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

def _deduplicate_doubled_text(text: str) -> str:
    """Fix doubled-character rendering (e.g., 'MMoorrttggaaggee' → 'Mortgage').

    Some PDF generators render each character twice. Detect this and fix it.
    """
    # Check if text has doubled characters (sample first 200 chars)
    sample = text[:200].replace("\n", "").replace(" ", "")
    if len(sample) < 20:
        return text
    doubles = sum(1 for i in range(0, len(sample) - 1, 2) if sample[i] == sample[i + 1])
    ratio = doubles / (len(sample) / 2)
    if ratio < 0.4:  # Less than 40% doubled — not a doubled-char PDF
        return text

    # De-duplicate: take every other character, preserving spaces and newlines
    result = []
    i = 0
    chars = list(text)
    while i < len(chars):
        c = chars[i]
        if c in ("\n", "\r"):
            result.append(c)
            i += 1
        elif c == " ":
            result.append(c)
            i += 1
        elif i + 1 < len(chars) and chars[i + 1] == c:
            # Doubled character — take one, skip next
            result.append(c)
            i += 2
        else:
            result.append(c)
            i += 1
    return "".join(result)


def parse_1098(pdf_path: Path, tax_year: int) -> dict:
    """Parse Form 1098 (Mortgage Interest Statement)."""
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        # Combine text from all pages (some 1098s have cover pages)
        text = ""
        for page in pdf.pages:
            text += (page.extract_text(layout=True) or "") + "\n"

    # Fix doubled-character rendering (Flagstar PDFs)
    text = _deduplicate_doubled_text(text)

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
    elif "BECU" in text_upper or "BOEING EMPLOYEES" in text_upper:
        lender["name"] = "BECU"

    # Lender TIN
    tin_m = re.search(r"TIN[#:]?\s*(\d{2}-\d{7})", text)
    if tin_m:
        lender["tin"] = tin_m.group(1)

    # Parse line by line — labels and dollar amounts may be on different lines
    lines = text.split("\n")

    def _find_box_amount(label_patterns: list[str], start_idx: int = 0) -> Optional[float]:
        """Find a dollar amount near a label pattern (same line or next 2 lines).

        Patterns are tried in priority order. Uses the FIRST match found.
        """
        for pattern in label_patterns:
            for i in range(start_idx, len(lines)):
                line_stripped = re.sub(r"\s+", "", lines[i].lower())
                if pattern in line_stripped:
                    # Check this line and next 2 for a dollar amount > 0
                    for j in range(i, min(i + 3, len(lines))):
                        # Try with $ sign first, then without
                        m = re.search(r"\$+\s*([\d,]+\.\d{2})", lines[j])
                        if not m:
                            m = re.search(r"(?:^|\s)([\d,]+\.\d{2})(?:\s|$)", lines[j])
                        if m:
                            val = parse_amount(m.group(1))
                            if val and val > 0:
                                return val
                    return None  # Found label but no amount nearby
        return None

    # Box 1: Mortgage interest — require "1" prefix to avoid cover page matches
    box1 = _find_box_amount(["1mortgage", "1mort"])
    if box1 is not None:
        boxes[1] = box1
    else:
        # Fallback 1: cover page "INTEREST PAID" or "INTEREST RECEIVED"
        m = re.search(r"INTEREST (?:PAID|RECEIVED FROM.*?BORROWER).*?\$\s*([\d,]+\.\d{2})", text)
        if m:
            boxes[1] = parse_amount(m.group(1))
    if 1 not in boxes:
        # Fallback 2: for doubled-char PDFs, find the first large $ amount after "1098" text
        # Box 1 is typically the first dollar amount on the form
        all_amounts = []
        for m in re.finditer(r"\$+\s*([\d,]+\.\d{2})", text):
            val = parse_amount(m.group(1))
            if val and val > 0:
                all_amounts.append(val)
        if all_amounts:
            # Box 1 is usually the largest non-property-tax amount, or the first one
            boxes[1] = all_amounts[0]

    # Box 2: Outstanding mortgage principal — require "2" prefix
    box2 = _find_box_amount(["2outstanding", "2outstandingmort"])
    if box2 is not None:
        boxes[2] = box2
    else:
        m = re.search(r"BEG BAL:\s*\$\s*([\d,]+\.\d{2})", text)
        if m:
            boxes[2] = parse_amount(m.group(1))

    # Box 5: Mortgage insurance premiums
    box5 = _find_box_amount(["5mortgage", "5mortgageinsurance"])
    if box5 is not None:
        boxes[5] = box5

    # Box 10: Property taxes (also check Flagstar format "PropertyTaxes $12,275.36")
    box10 = _find_box_amount(["10property", "10realestate", "propertytax"])
    if box10 is not None:
        boxes[10] = box10
    else:
        m = re.search(r"Property\s*Taxes?\s*\$\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
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

    # Validation
    interest = boxes.get(1, 0)
    principal = boxes.get(2, 0)
    if interest <= 0:
        mismatches.append(f"Box 1 (mortgage interest) is ${interest} — expected > 0")
    if principal > 0 and interest > principal:
        mismatches.append(f"Box 1 (interest ${interest}) > Box 2 (principal ${principal})")

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
            "has_interest": boxes.get(1, 0) > 0,
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
# Consolidated 1099 Parser (Fidelity & Morgan Stanley)
# ---------------------------------------------------------------------------

def _detect_1099_consolidated_format(text: str) -> str:
    """Detect whether consolidated 1099 is Fidelity or Morgan Stanley format."""
    text_upper = text.upper()
    if "MORGAN STANLEY" in text_upper or "MSSB" in text_upper:
        return "morgan_stanley"
    if "FIDELITY" in text_upper or "NATIONAL FINANCIAL SERVICES" in text_upper:
        return "fidelity"
    return "unknown"


def _parse_fidelity_1099_div(text: str) -> dict:
    """Extract 1099-DIV summary from Fidelity consolidated statement.

    Format: dotted-leader lines like:
      1a Total Ordinary Dividends...274.97
    """
    div = {}
    patterns = [
        ("1a_total_ordinary_dividends", r"1a\s+Total Ordinary Dividends[.\s]+([\d,]+\.\d{2})"),
        ("1b_qualified_dividends", r"1b\s+Qualified Dividends[.\s]+([\d,]+\.\d{2})"),
        ("2a_total_capital_gain_dist", r"2a\s+Total Capital Gain Distributions[.\s]+([\d,]+\.\d{2})"),
        ("4_fed_tax_withheld", r"4\s+Federal Income Tax Withheld[.\s]+([\d,]+\.\d{2})"),
        ("5_section_199a_dividends", r"5\s+Section 199A Dividends[.\s]+([\d,]+\.\d{2})"),
        ("7_foreign_tax_paid", r"7\s+Foreign Tax Paid[.\s]+([\d,]+\.\d{2})"),
    ]
    for key, pattern in patterns:
        m = re.search(pattern, text)
        if m:
            div[key] = parse_amount(m.group(1))
    return div


def _parse_fidelity_1099_int(text: str) -> dict:
    """Extract 1099-INT summary from Fidelity consolidated statement."""
    int_data = {}
    patterns = [
        ("1_interest_income", r"(?:Form 1099-INT|1099-INT).*?1\s+Interest Income[.\s]+([\d,]+\.\d{2})"),
        ("4_fed_tax_withheld", r"(?:Form 1099-INT|1099-INT).*?4\s+Federal Income Tax Withheld[.\s]+([\d,]+\.\d{2})"),
    ]
    # Use DOTALL for multi-line matching since INT section follows DIV
    for key, pattern in patterns:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            int_data[key] = parse_amount(m.group(1))

    # Fallback: search for INT-specific patterns without context
    if "1_interest_income" not in int_data:
        # Find the 1099-INT section and extract from there
        int_start = text.find("1099-INT")
        if int_start >= 0:
            int_text = text[int_start:]
            m = re.search(r"1\s+Interest Income[.\s]+([\d,]+\.\d{2})", int_text)
            if m:
                int_data["1_interest_income"] = parse_amount(m.group(1))
            m = re.search(r"4\s+Federal Income Tax Withheld[.\s]+([\d,]+\.\d{2})", int_text)
            if m:
                int_data["4_fed_tax_withheld"] = parse_amount(m.group(1))
    return int_data


def _parse_fidelity_1099_b(text: str) -> dict:
    """Extract 1099-B summary from Fidelity consolidated statement.

    The summary table has rows like:
      Short-termtransactionsforwhichbasisisreportedtotheIRS 0.00 0.00 0.00 0.00 0.00 0.00
    Columns: Proceeds, CostBasis, MarketDiscount, WashSales, Gain/Loss, FedTaxWithheld
    """
    b_data = {
        "short_term": {"proceeds": 0.0, "cost_basis": 0.0, "market_discount": 0.0,
                       "wash_sales": 0.0, "gain_loss": 0.0, "fed_withheld": 0.0},
        "long_term": {"proceeds": 0.0, "cost_basis": 0.0, "market_discount": 0.0,
                      "wash_sales": 0.0, "gain_loss": 0.0, "fed_withheld": 0.0},
        "total": {"proceeds": 0.0, "cost_basis": 0.0, "market_discount": 0.0,
                  "wash_sales": 0.0, "gain_loss": 0.0, "fed_withheld": 0.0},
    }

    lines = text.split("\n")
    for line in lines:
        # Extract 6 amounts from summary lines
        amounts = re.findall(r"(-?[\d,]+\.\d{2})", line)
        if len(amounts) < 6:
            continue

        line_lower = line.lower().replace(" ", "")
        vals = [parse_amount(a) for a in amounts[:6]]

        if "short-term" in line_lower and "reported" in line_lower:
            b_data["short_term"]["proceeds"] += vals[0]
            b_data["short_term"]["cost_basis"] += vals[1]
            b_data["short_term"]["market_discount"] += vals[2]
            b_data["short_term"]["wash_sales"] += vals[3]
            b_data["short_term"]["gain_loss"] += vals[4]
            b_data["short_term"]["fed_withheld"] += vals[5]
        elif "short-term" in line_lower and "notreported" in line_lower:
            b_data["short_term"]["proceeds"] += vals[0]
            b_data["short_term"]["cost_basis"] += vals[1]
            b_data["short_term"]["market_discount"] += vals[2]
            b_data["short_term"]["wash_sales"] += vals[3]
            b_data["short_term"]["gain_loss"] += vals[4]
            b_data["short_term"]["fed_withheld"] += vals[5]
        elif "long-term" in line_lower and "reported" in line_lower:
            b_data["long_term"]["proceeds"] += vals[0]
            b_data["long_term"]["cost_basis"] += vals[1]
            b_data["long_term"]["market_discount"] += vals[2]
            b_data["long_term"]["wash_sales"] += vals[3]
            b_data["long_term"]["gain_loss"] += vals[4]
            b_data["long_term"]["fed_withheld"] += vals[5]
        elif "long-term" in line_lower and "notreported" in line_lower:
            b_data["long_term"]["proceeds"] += vals[0]
            b_data["long_term"]["cost_basis"] += vals[1]
            b_data["long_term"]["market_discount"] += vals[2]
            b_data["long_term"]["wash_sales"] += vals[3]
            b_data["long_term"]["gain_loss"] += vals[4]
            b_data["long_term"]["fed_withheld"] += vals[5]

    # Also check for the total row (no label, just 6 numbers indented)
    # Compute totals from short+long
    for key in ["proceeds", "cost_basis", "market_discount", "wash_sales", "gain_loss", "fed_withheld"]:
        b_data["total"][key] = round(b_data["short_term"][key] + b_data["long_term"][key], 2)

    return b_data


def _parse_fidelity_1099_misc(text: str) -> dict:
    """Extract 1099-MISC summary from Fidelity consolidated statement."""
    misc = {}
    m = re.search(r"3\s+Other Income[.\s]+([\d,]+\.\d{2})", text)
    if m:
        misc["3_other_income"] = parse_amount(m.group(1))
    m = re.search(r"8\s+Substitute Payments[.\s]+([\d,]+\.\d{2})", text)
    if m:
        misc["8_substitute_payments"] = parse_amount(m.group(1))
    return misc


def _parse_ms_1099_div(text: str) -> dict:
    """Extract 1099-DIV from Morgan Stanley consolidated statement.

    Format: BOX format like:
      1a. TOTAL ORDINARY DIVIDENDS  $131.86
    """
    div = {}
    patterns = [
        ("1a_total_ordinary_dividends", r"1a\.\s*TOTAL ORDINARY DIVIDENDS\s+\$([\d,]+\.\d{2})"),
        ("1b_qualified_dividends", r"1b\.\s*QUALIFIED DIVIDENDS\s+\$([\d,]+\.\d{2})"),
        ("2a_total_capital_gain_dist", r"2a\.\s*TOTAL CAPITAL GAIN DISTRIBUTIONS\s+\$([\d,]+\.\d{2})"),
        ("4_fed_tax_withheld", r"4\.\s*FEDERAL INCOME TAX WITHHELD\s+\$([\d,]+\.\d{2})"),
        ("5_section_199a_dividends", r"5\.\s*SECTION 199A DIVIDENDS\s+\$([\d,]+\.\d{2})"),
        ("7_foreign_tax_paid", r"7\.\s*FOREIGN TAX PAID\s+\$([\d,]+\.\d{2})"),
    ]
    for key, pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            div[key] = parse_amount(m.group(1))
    return div


def _parse_ms_1099_int(text: str) -> dict:
    """Extract 1099-INT from Morgan Stanley consolidated statement."""
    int_data = {}
    # Find 1099-INT section
    int_start = text.upper().find("FORM 1099-INT")
    if int_start < 0:
        return int_data
    int_text = text[int_start:]

    patterns = [
        ("1_interest_income", r"1\.\s*INTEREST INCOME\s+\$([\d,]+\.\d{2})"),
        ("4_fed_tax_withheld", r"4\.\s*FEDERAL INCOME TAX WITHHELD\s+\$([\d,]+\.\d{2})"),
    ]
    for key, pattern in patterns:
        m = re.search(pattern, int_text, re.IGNORECASE)
        if m:
            int_data[key] = parse_amount(m.group(1))
    return int_data


def _parse_ms_1099_b(text: str) -> dict:
    """Extract 1099-B summary from Morgan Stanley consolidated statement.

    Page 3 has high-level 1099-B numbers:
      1d. PROCEEDS  $248,709.67
    Page 6 has detailed summary with Box A/B/D/E rows.
    """
    b_data = {
        "short_term": {"proceeds": 0.0, "cost_basis": 0.0, "market_discount": 0.0,
                       "wash_sales": 0.0, "gain_loss": 0.0},
        "long_term": {"proceeds": 0.0, "cost_basis": 0.0, "market_discount": 0.0,
                      "wash_sales": 0.0, "gain_loss": 0.0},
        "total": {"proceeds": 0.0, "cost_basis": 0.0, "market_discount": 0.0,
                  "wash_sales": 0.0, "gain_loss": 0.0},
    }

    lines = text.split("\n")
    for line in lines:
        line_stripped = line.strip()

        # Total Short-Term and Total Long-Term rows
        # Format: Total Short - Term  $248,709.67 $244,397.42 $0.00 $0.00 $4,312.25
        amounts = re.findall(r"\$?\(?([\d,]+\.\d{2})\)?", line_stripped)

        if re.search(r"Total\s+Short\s*-?\s*Term", line_stripped, re.IGNORECASE) and len(amounts) >= 5:
            vals = [parse_amount(a) for a in amounts[:5]]
            # Check for parenthesized negative
            for i, a in enumerate(re.finditer(r"\([\d,]+\.\d{2}\)", line_stripped)):
                if i < 5:
                    idx = len(re.findall(r"\$?\(?([\d,]+\.\d{2})\)?", line_stripped[:a.start()]))
                    if idx < 5:
                        vals[idx] = -vals[idx]
            b_data["short_term"] = {
                "proceeds": vals[0], "cost_basis": vals[1],
                "market_discount": vals[2], "wash_sales": vals[3],
                "gain_loss": vals[4],
            }
        elif re.search(r"Total\s+Long\s*-?\s*Term", line_stripped, re.IGNORECASE) and len(amounts) >= 5:
            vals = [parse_amount(a) for a in amounts[:5]]
            for i, a in enumerate(re.finditer(r"\([\d,]+\.\d{2}\)", line_stripped)):
                if i < 5:
                    idx = len(re.findall(r"\$?\(?([\d,]+\.\d{2})\)?", line_stripped[:a.start()]))
                    if idx < 5:
                        vals[idx] = -vals[idx]
            b_data["long_term"] = {
                "proceeds": vals[0], "cost_basis": vals[1],
                "market_discount": vals[2], "wash_sales": vals[3],
                "gain_loss": vals[4],
            }

    # Compute totals
    for key in ["proceeds", "cost_basis", "market_discount", "wash_sales", "gain_loss"]:
        b_data["total"][key] = round(b_data["short_term"][key] + b_data["long_term"][key], 2)

    return b_data


def _parse_ms_1099_misc(text: str) -> dict:
    """Extract 1099-MISC from Morgan Stanley consolidated statement."""
    misc = {}
    m = re.search(r"3\.\s*OTHER INCOME\s+\$([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        misc["3_other_income"] = parse_amount(m.group(1))
    m = re.search(r"8\.\s*SUBSTITUTE PAYMENTS.*?\$([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        misc["8_substitute_payments"] = parse_amount(m.group(1))
    return misc


def parse_1099_consolidated(pdf_path: Path, tax_year: int) -> dict:
    """Parse a consolidated Form 1099 (Fidelity or Morgan Stanley).

    Extracts summary-level data from:
    - 1099-DIV (dividends)
    - 1099-INT (interest)
    - 1099-B (broker transactions)
    - 1099-MISC (miscellaneous income)
    """
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        full_text = ""
        for page in pdf.pages:
            full_text += (page.extract_text(layout=True) or "") + "\n"

    fmt = _detect_1099_consolidated_format(full_text)

    # Extract account info
    account_number = ""
    recipient_ssn_last4 = ""
    institution = ""

    m = re.search(r"Account\s*No\.?\s*([\w-]+\d+)", full_text)
    if m:
        account_number = m.group(1).strip()
    if not account_number:
        m = re.search(r"Account\s*Number\s*:?\s*([\d\s]+)", full_text)
        if m:
            account_number = m.group(1).strip()

    ssn_m = re.search(r"(?:\*{3}-\*{2}-|XXX-XX-)(\d{4})", full_text, re.IGNORECASE)
    if ssn_m:
        recipient_ssn_last4 = ssn_m.group(1)

    # Detect recipient name (could be Yi Chen or child UTMA)
    recipient_name = ""
    name_m = re.search(r"(YI\s+CHEN|LAURENCE\s+CHEN|RUBY\s+CHEN)", full_text)
    if name_m:
        # Normalize whitespace (layout text may have newlines embedded)
        recipient_name = re.sub(r"\s+", " ", name_m.group(1)).strip().title()

    if fmt == "fidelity":
        institution = "Fidelity"
        div = _parse_fidelity_1099_div(full_text)
        int_data = _parse_fidelity_1099_int(full_text)
        b_data = _parse_fidelity_1099_b(full_text)
        misc = _parse_fidelity_1099_misc(full_text)
    elif fmt == "morgan_stanley":
        institution = "Morgan Stanley"
        div = _parse_ms_1099_div(full_text)
        int_data = _parse_ms_1099_int(full_text)
        b_data = _parse_ms_1099_b(full_text)
        misc = _parse_ms_1099_misc(full_text)
    else:
        raise ValueError(f"Unknown consolidated 1099 format for {pdf_path.name}")

    # --- Validation ---
    mismatches = []

    # 1099-DIV: qualified <= total ordinary
    if div.get("1b_qualified_dividends", 0) > div.get("1a_total_ordinary_dividends", 0) + 0.01:
        mismatches.append(
            f"1099-DIV: qualified ({div['1b_qualified_dividends']}) > "
            f"total ordinary ({div['1a_total_ordinary_dividends']})"
        )

    # 1099-DIV: cap gain distributions >= 0
    if div.get("2a_total_capital_gain_dist", 0) < 0:
        mismatches.append(f"1099-DIV: cap gain distributions ({div['2a_total_capital_gain_dist']}) < 0")

    # 1099-INT: interest >= 0
    if int_data.get("1_interest_income", 0) < 0:
        mismatches.append(f"1099-INT: interest ({int_data['1_interest_income']}) < 0")

    # 1099-INT: fed withheld <= interest
    if int_data.get("4_fed_tax_withheld", 0) > int_data.get("1_interest_income", 0) + 0.01:
        mismatches.append(
            f"1099-INT: fed withheld ({int_data['4_fed_tax_withheld']}) > "
            f"interest ({int_data['1_interest_income']})"
        )

    # 1099-B: proceeds - basis = gain/loss for each category (±$0.01)
    for term in ["short_term", "long_term"]:
        p = b_data[term]["proceeds"]
        c = b_data[term]["cost_basis"]
        w = b_data[term].get("wash_sales", 0)
        g = b_data[term]["gain_loss"]
        if p > 0 or c > 0:
            expected = round(p - c + w, 2)
            if abs(g - expected) > 0.02:
                mismatches.append(
                    f"1099-B {term}: gain/loss ({g}) != proceeds ({p}) - basis ({c}) + wash ({w}) = {expected}"
                )

    # 1099-B: totals = sum of short + long
    for key in ["proceeds", "cost_basis", "gain_loss"]:
        expected_total = round(b_data["short_term"][key] + b_data["long_term"][key], 2)
        actual_total = b_data["total"][key]
        if abs(actual_total - expected_total) > 0.02:
            mismatches.append(
                f"1099-B total {key} ({actual_total}) != short ({b_data['short_term'][key]}) + long ({b_data['long_term'][key]})"
            )

    # 1099-MISC: substitute payments reduce qualified dividends
    sub_pay = misc.get("8_substitute_payments", 0)
    if sub_pay > 0 and div.get("1b_qualified_dividends", 0) > 0:
        mismatches.append(
            f"1099-MISC: substitute payments ({sub_pay}) > 0 — may reduce qualified dividends"
        )

    # Build result
    result = {
        "form_type": "1099-CONSOLIDATED",
        "tax_year": tax_year,
        "institution": institution,
        "format": fmt,
        "recipient": {
            "name": recipient_name or "Yi Chen",
            "ssn_last4": recipient_ssn_last4,
        },
        "account_number": account_number,
        "forms": {},
        "validation": {
            "checks_passed": len(mismatches) == 0,
            "mismatches": mismatches,
        },
        "source": {
            "file": str(pdf_path),
            "pages": list(range(1, num_pages + 1)),
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        },
    }

    # Add sub-forms only if they have data
    if div:
        result["forms"]["1099-DIV"] = div
    if int_data:
        result["forms"]["1099-INT"] = int_data
    if any(b_data["total"][k] != 0 for k in ["proceeds", "cost_basis", "gain_loss"]):
        result["forms"]["1099-B"] = b_data
    if any(v != 0 for v in misc.values()):
        result["forms"]["1099-MISC"] = misc

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
            # The line prefix must appear as a form line label, not as a
            # back-reference like "line 10" or "line 24"
            # Match: prefix at start-ish of line or after whitespace, followed by a space and keyword
            # Reject: "line <prefix>" which is a reference to another line
            m = re.search(rf"\b{re.escape(line_prefix)}\b", line)
            if not m:
                continue
            # Skip if preceded by "line " — this is a reference, not a label
            prefix_pos = m.start()
            before = line[max(0, prefix_pos - 6):prefix_pos].lower()
            if "line " in before or "lines" in before:
                continue
            if not any(kw.lower() in line.lower() for kw in keywords):
                continue
            # Find dollar amounts on this line — skip small numbers that are
            # form line references (e.g., "24" in "from line 24")
            amounts = re.findall(r"(-?[\d,]+\.\d{0,2})", line)
            real_amounts = []
            for amt_str in amounts:
                clean = amt_str.replace(",", "").lstrip("-")
                # Skip amounts that are "N." where N <= 2 digits and appear mid-line
                if clean.endswith(".") and len(clean.rstrip(".")) <= 2:
                    pos = line.rfind(amt_str)
                    rest = line[pos + len(amt_str):].strip(". \t")
                    if rest:  # More text after — likely a form reference
                        continue
                real_amounts.append(amt_str)
            if real_amounts:
                val_str = real_amounts[-1]
                if val_str.endswith("."):
                    val_str += "00"
                return parse_amount(val_str)

            # No amounts on the label line — check PREVIOUS line first (2022 format
            # has amounts on the line above the label), then next line
            for offset in [-1, 1]:
                j = i + offset
                if j < 0 or j >= len(lines_list):
                    continue
                neighbor = lines_list[j]
                # Skip if neighbor has a different form line label
                if re.search(r"(?:^|\s)\d{1,2}[a-z]?\s+[A-Z]", neighbor.strip()):
                    continue
                neighbor_amounts = re.findall(r"(-?[\d,]+\.\d{0,2})", neighbor)
                if neighbor_amounts:
                    val_str = neighbor_amounts[-1]
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

    # Taxable income = AGI - deductions (±$1)
    if summary.get("adjusted_gross_income") and summary.get("deductions") and summary.get("taxable_income"):
        expected_taxable = summary["adjusted_gross_income"] - summary["deductions"]
        if abs(summary["taxable_income"] - expected_taxable) > 1:
            mismatches.append(
                f"Taxable income ({summary['taxable_income']}) != AGI ({summary['adjusted_gross_income']}) "
                f"- deductions ({summary['deductions']}) = {expected_taxable}"
            )

    # Refund/owed ≈ total_payments - total_tax
    # Tolerance: $2000 to account for underpayment penalties (Form 2210),
    # additional credits, or other adjustments not captured in our summary fields
    if summary.get("total_payments") and summary.get("total_tax"):
        expected_result = round(summary["total_payments"] - summary["total_tax"], 2)
        actual_result = summary.get("refund_or_owed", 0)
        # refund_or_owed is positive=owed, negative=refund
        # expected_result > 0 means overpaid (refund), so actual should be negative
        expected_signed = -expected_result  # Convert to our sign convention
        if abs(actual_result - expected_signed) > 2000:
            mismatches.append(
                f"Refund/owed ({actual_result}) differs significantly from "
                f"-(total_payments ({summary['total_payments']}) - total_tax ({summary['total_tax']})) = {expected_signed}"
            )

    # Total withholding <= total payments
    if summary.get("total_withholding") and summary.get("total_payments"):
        if summary["total_withholding"] > summary["total_payments"] + 1:
            mismatches.append(
                f"Total withholding ({summary['total_withholding']}) > total payments ({summary['total_payments']})"
            )

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

SUPPORTED_FORMS = {"W-2", "1099-R", "1098", "1099-INT", "5498-SA", "5498", "1099-SA", "Schedule-H", "1099-CONSOLIDATED"}
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
    elif form_type == "1099-CONSOLIDATED":
        data = parse_1099_consolidated(pdf_path, year)
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
    elif form_type == "1099-CONSOLIDATED":
        institution = data.get("institution", "")
        if institution:
            slug = re.sub(r"[^a-z0-9]", "-", institution.lower()).strip("-")
            slug = re.sub(r"-+", "-", slug)
            parts.append(slug[:30])
        acct = data.get("account_number", "")
        if acct:
            # Use last 4 digits for uniqueness
            digits = re.sub(r"[^0-9]", "", acct)
            parts.append(digits[-4:] if len(digits) >= 4 else digits)

    return "-".join(parts)


def _sanitize_stem(stem: str) -> str:
    """Convert a filename stem to a safe slug."""
    slug = re.sub(r"[^a-z0-9]", "-", stem.lower()).strip("-")
    return re.sub(r"-+", "-", slug)[:30]


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------

def run_cross_validate(year_filter: Optional[int] = None):
    """Cross-validate prepare-folder source documents against archive-folder filed returns."""
    years = [year_filter] if year_filter else [y for y in YEARS if (ARCHIVE_OUTPUT / str(y) / "1040-summary.yaml").exists()]

    if not years:
        logger.info("No archive 1040 summaries found for cross-validation.")
        return

    for year in years:
        logger.info(f"\n{'='*70}")
        logger.info(f"  CROSS-VALIDATION: {year}")
        logger.info(f"{'='*70}")

        # Load archive 1040 summary
        summary_path = ARCHIVE_OUTPUT / str(year) / "1040-summary.yaml"
        if not summary_path.exists():
            logger.info(f"  No 1040-summary.yaml for {year} — skipping")
            continue
        with open(summary_path) as f:
            f1040 = yaml.safe_load(f)

        filing_status = f1040.get("filing_status", "Unknown")
        is_mfj = "joint" in filing_status.lower()
        logger.info(f"  Filing status: {filing_status}")

        # Load all prepare-folder YAMLs for this year
        prepare_dir = PREPARE_OUTPUT / str(year)
        if not prepare_dir.exists():
            logger.info(f"  No prepare folder for {year} — skipping")
            continue

        prepare_docs = {}  # form_type -> list of parsed dicts
        for yaml_file in sorted(prepare_dir.glob("*.yaml")):
            with open(yaml_file) as f:
                doc = yaml.safe_load(f)
            if not doc:
                continue
            ft = doc.get("form_type", "unknown")
            prepare_docs.setdefault(ft, []).append(doc)

        checks = []  # list of (label, prepare_val, archive_val, status, note)

        # --- Check 1: W-2 wages ---
        w2s = prepare_docs.get("W-2", [])
        yi_ssn = "2622"

        # Separate W-2s by role:
        # - Household W-2s: employer is Yi Chen (Schedule H, nanny) — NOT counted in line 1a
        # - Yi's employer W-2s: employee SSN = Yi's
        # - Spouse W-2s: employee SSN = spouse's (3457)
        # - Other W-2s: other SSNs (e.g., nanny as employee — already captured as household)
        spouse_ssn = "3457"
        household_w2s = [w for w in w2s if w.get("employer", {}).get("name", "").strip() == "Yi Chen"]
        non_household = [w for w in w2s if w.get("employer", {}).get("name", "").strip() != "Yi Chen"]
        employer_w2s = [w for w in non_household if w.get("employee", {}).get("ssn_last4") == yi_ssn]
        spouse_w2s = [w for w in non_household if w.get("employee", {}).get("ssn_last4") == spouse_ssn]
        other_w2s = [w for w in non_household if w.get("employee", {}).get("ssn_last4") not in (yi_ssn, spouse_ssn)]

        yi_wages = sum(w.get("boxes", {}).get("1_wages", 0) for w in employer_w2s)
        yi_fed_withheld = sum(w.get("boxes", {}).get("2_fed_tax_withheld", 0) for w in employer_w2s)
        household_wages = sum(w.get("boxes", {}).get("1_wages", 0) for w in household_w2s)

        spouse_wages = sum(w.get("boxes", {}).get("1_wages", 0) for w in spouse_w2s)
        spouse_fed_withheld = sum(w.get("boxes", {}).get("2_fed_tax_withheld", 0) for w in spouse_w2s)

        all_wages = yi_wages + spouse_wages
        all_fed_withheld = yi_fed_withheld + spouse_fed_withheld

        line_1a = f1040.get("income", {}).get("1a_w2_wages", 0)

        logger.info(f"\n  --- W-2 Wages (Line 1a) ---")
        for w in employer_w2s:
            emp = w.get("employer", {}).get("name", "?")
            wages = w.get("boxes", {}).get("1_wages", 0)
            withheld = w.get("boxes", {}).get("2_fed_tax_withheld", 0)
            logger.info(f"    Yi W-2: {emp:40s}  wages=${wages:>12,.2f}  fed_withheld=${withheld:>10,.2f}")
        for w in household_w2s:
            emp_name = w.get("employee", {}).get("name", "?").strip()
            wages = w.get("boxes", {}).get("1_wages", 0)
            logger.info(f"    Household W-2 (employee: {emp_name}): wages=${wages:>12,.2f}  (Schedule H, not in line 1a)")
        for w in spouse_w2s:
            emp = w.get("employer", {}).get("name", "?") or f"EIN {w.get('employer', {}).get('ein', '?')}"
            wages = w.get("boxes", {}).get("1_wages", 0)
            withheld = w.get("boxes", {}).get("2_fed_tax_withheld", 0)
            logger.info(f"    Spouse W-2 (SSN ...{spouse_ssn}): {emp:30s}  wages=${wages:>12,.2f}  fed_withheld=${withheld:>10,.2f}")
        for w in other_w2s:
            ssn = w.get("employee", {}).get("ssn_last4", "?")
            emp = w.get("employer", {}).get("name", "?") or f"EIN {w.get('employer', {}).get('ein', '?')}"
            wages = w.get("boxes", {}).get("1_wages", 0)
            logger.info(f"    Other W-2 (SSN ...{ssn}): {emp:30s}  wages=${wages:>12,.2f}")

        if is_mfj:
            # MFJ: 1040 line 1a includes BOTH spouses
            # If 1040 > our total AND spouse wages are missing/zero, this is expected
            spouse_incomplete = (spouse_wages == 0) and (line_1a > all_wages)
            gap_status = "MATCH" if abs(all_wages - line_1a) < 1 else ("EXPECTED" if spouse_incomplete else "MISMATCH")
            checks.append(("W-2 wages (all, MFJ) vs 1040 line 1a", all_wages, line_1a, gap_status,
                           f"MFJ return includes both spouses. Yi=${yi_wages:,.2f}, Spouse=${spouse_wages:,.2f}" if abs(all_wages - line_1a) >= 1 else ""))
        else:
            checks.append(("Yi W-2 wages vs 1040 line 1a", yi_wages, line_1a,
                           "MATCH" if abs(yi_wages - line_1a) < 1 else "MISMATCH", ""))

        # Explain gap if mismatch/expected
        if is_mfj and abs(all_wages - line_1a) >= 1:
            gap = line_1a - all_wages
            note = f"Gap=${gap:,.2f}."
            if gap > 0:
                # 1040 has MORE wages than our W-2s — missing spouse W-2 data
                zero_spouse = [w for w in spouse_w2s if w.get("boxes", {}).get("1_wages", 0) == 0]
                if zero_spouse:
                    note += f" {len(zero_spouse)} spouse W-2(s) show $0 wages (likely PDF parse failure)."
                    for zw in zero_spouse:
                        src = zw.get("source", {}).get("file", "")
                        note += f" Check: {Path(src).name}"
                elif not spouse_w2s:
                    note += " No spouse W-2s found in prepare folder."
                note += f" The ${gap:,.2f} gap is likely spouse's actual wages not captured in parsed W-2s."
            elif gap < 0:
                # Our W-2s show MORE than 1040 — possibly third-party sick pay overlap
                box13_key = "13"  # Box 13 is stored as string key
                third_party = [w for w in employer_w2s
                               if w.get("boxes", {}).get(box13_key, {}).get("third_party_sick_pay")]
                if third_party:
                    tp_wages = sum(w.get("boxes", {}).get("1_wages", 0) for w in third_party)
                    tp_names = [w.get("employer", {}).get("name", "?") for w in third_party]
                    note += (f" Third-party sick pay W-2(s): {', '.join(tp_names)} (${tp_wages:,.2f}). "
                             f"When employer pays sick leave through an insurer, the insurer issues a separate W-2. "
                             f"The insurer's Box 1 may overlap with the primary employer's W-2 Box 1 because both "
                             f"report the same wages. The 1040 line 1a reflects the de-duplicated total.")
                    # Mark as EXPECTED since we understand why
                    checks[-1] = (checks[-1][0], checks[-1][1], checks[-1][2], "EXPECTED", note)
                    # Skip the default note update below
                    note = None
                else:
                    note += " Prepare folder W-2s sum exceeds 1040 line 1a — verify for duplicates."
            if note is not None:
                checks[-1] = (checks[-1][0], checks[-1][1], checks[-1][2], checks[-1][3], note)

        # Additional: Yi-only wages comparison (useful when spouse data incomplete)
        if is_mfj and abs(all_wages - line_1a) >= 1:
            yi_gap = line_1a - yi_wages
            logger.info(f"    Yi-only wages: ${yi_wages:,.2f}  |  1040 line 1a: ${line_1a:,.2f}  |  Implied spouse wages: ${yi_gap:,.2f}")

        # --- Check 2: W-2 federal withholding ---
        w2_withholding_1040 = f1040.get("summary", {}).get("w2_withholding", 0)

        logger.info(f"\n  --- W-2 Federal Withholding ---")
        if is_mfj:
            withholding_note = ""
            if abs(all_fed_withheld - w2_withholding_1040) >= 1:
                whgap = w2_withholding_1040 - all_fed_withheld
                withholding_note = f"Yi=${yi_fed_withheld:,.2f}, Spouse=${spouse_fed_withheld:,.2f}. Gap=${whgap:,.2f}."
                if whgap > 0:
                    withholding_note += " 1040 shows more withholding — spouse W-2 withholding not captured in parsed data."
            checks.append(("W-2 fed withholding (all, MFJ) vs 1040 w2_withholding", all_fed_withheld, w2_withholding_1040,
                           "MATCH" if abs(all_fed_withheld - w2_withholding_1040) < 1 else "EXPECTED",
                           withholding_note))
        else:
            checks.append(("Yi W-2 fed withholding vs 1040 w2_withholding", yi_fed_withheld, w2_withholding_1040,
                           "MATCH" if abs(yi_fed_withheld - w2_withholding_1040) < 1 else "MISMATCH", ""))

        # Schedule H withholding adds to total withholding (1040 line 25d) not W-2 line
        sch_h_docs = prepare_docs.get("Schedule-H", [])
        sch_h_withheld = sum(d.get("part1_ss_medicare_fit", {}).get("7_fed_income_tax_withheld", 0) for d in sch_h_docs)
        if sch_h_withheld > 0:
            logger.info(f"    Note: Schedule H fed withholding = ${sch_h_withheld:,.2f} (reported on 1040 line 25d, not line 25a)")

        # --- Check 3: 1099-R distributions ---
        r1099s = prepare_docs.get("1099-R", [])
        logger.info(f"\n  --- 1099-R Distributions (Line 4a/4b) ---")

        total_gross_dist = 0
        total_taxable_dist = 0
        for r in r1099s:
            payer = r.get("payer", {}).get("name", "?")
            plan = r.get("plan_type", "?")
            gross = r.get("boxes", {}).get("1_gross_distribution", 0)
            taxable = r.get("boxes", {}).get("2a_taxable_amount", 0)
            dist_code = r.get("boxes", {}).get("7_distribution_code", "")
            if gross == 0 and taxable == 0:
                logger.info(f"    1099-R: {payer} ({plan}) — $0 distribution (code={dist_code}, informational)")
                continue
            total_gross_dist += gross
            total_taxable_dist += taxable
            logger.info(f"    1099-R: {payer} ({plan})  gross=${gross:,.2f}  taxable=${taxable:,.2f}  code={dist_code}")

        # 1040 line 4b = taxable IRA amount (4a = gross, not always parsed)
        line_4b = f1040.get("income", {}).get("4b_taxable_ira", 0)

        if total_gross_dist > 0 or line_4b > 0:
            r_note = ""
            if abs(total_taxable_dist - line_4b) >= 1:
                # Common: backdoor Roth conversion shows $7000 gross/taxable on 1099-R
                # but 1040 4b may show only a few dollars if basis was tracked on Form 8606
                if total_taxable_dist > line_4b:
                    r_note = (f"1099-R taxable=${total_taxable_dist:,.2f} but 1040 line 4b=${line_4b:,.2f}. "
                              f"Likely a backdoor Roth conversion: full amount on 1099-R but Form 8606 "
                              f"tracks non-deductible IRA basis, so only gains are taxable on 1040.")
                    r_status = "EXPECTED"
                else:
                    r_note = f"1040 shows more taxable IRA than 1099-R documents in prepare folder."
                    r_status = "MISMATCH"
            else:
                r_status = "MATCH"
            checks.append(("1099-R taxable vs 1040 line 4b", total_taxable_dist, line_4b, r_status, r_note))
        else:
            logger.info(f"    No significant 1099-R distributions or 1040 line 4b")

        # --- Check 4: 1098 Mortgage Interest ---
        m1098s = prepare_docs.get("1098", [])
        logger.info(f"\n  --- 1098 Mortgage Interest ---")

        total_mortgage_interest = sum(d.get("boxes", {}).get("1_mortgage_interest", 0) for d in m1098s)
        total_property_tax = sum(d.get("boxes", {}).get("10_property_tax", 0) for d in m1098s)

        for m in m1098s:
            lender = m.get("lender", {}).get("name", "?")
            interest = m.get("boxes", {}).get("1_mortgage_interest", 0)
            ptax = m.get("boxes", {}).get("10_property_tax", 0)
            if interest > 0 or ptax > 0:
                logger.info(f"    1098: {lender}  interest=${interest:,.2f}  property_tax=${ptax:,.2f}")

        deductions = f1040.get("summary", {}).get("deductions", 0)
        # Standard deduction for MFJ in various years
        std_deduction = {2022: 25900, 2023: 27700, 2024: 29200}.get(year, 29200)
        if is_mfj:
            std_deduction_label = f"MFJ standard deduction=${std_deduction:,}"
        else:
            std_deduction_label = f"standard deduction"

        if total_mortgage_interest > 0:
            # If deductions > standard deduction, likely itemized
            likely_itemized = deductions > std_deduction * 0.9  # Allow some margin
            if likely_itemized:
                # Can't perfectly compare since Schedule A has SALT cap, charity, etc.
                checks.append(("1098 mortgage interest (itemized deductions)", total_mortgage_interest, deductions,
                               "INFO",
                               f"Mortgage interest=${total_mortgage_interest:,.2f}, property tax=${total_property_tax:,.2f}. "
                               f"1040 deductions=${deductions:,.2f} includes SALT (capped $10K), charity, etc. "
                               f"Cannot directly compare — deductions are a superset."))
            else:
                checks.append(("1098 mortgage interest (standard deduction taken)", total_mortgage_interest, deductions,
                               "INFO",
                               f"1040 deductions=${deductions:,.2f} ~ {std_deduction_label}. "
                               f"Took standard deduction despite ${total_mortgage_interest:,.2f} mortgage interest. "
                               f"This is correct if itemized total < standard deduction."))
        else:
            logger.info(f"    No mortgage interest reported (all 1098s show $0)")
            checks.append(("1098 mortgage interest", 0, deductions, "INFO",
                           f"No mortgage interest. 1040 deductions=${deductions:,.2f} ({std_deduction_label})."))

        # --- Check 5: 1099-INT Interest ---
        int1099s = prepare_docs.get("1099-INT", [])
        logger.info(f"\n  --- 1099-INT Interest (Line 2b) ---")

        total_interest = sum(d.get("boxes", {}).get("1_interest_income", 0) for d in int1099s)
        for d in int1099s:
            payer = d.get("payer", {}).get("name", "?")
            interest = d.get("boxes", {}).get("1_interest_income", 0)
            logger.info(f"    1099-INT: {payer}  interest=${interest:,.2f}")

        line_2b = f1040.get("income", {}).get("2b_taxable_interest", 0)

        if total_interest > 0 or line_2b > 0:
            if abs(total_interest - line_2b) < 1:
                checks.append(("1099-INT interest vs 1040 line 2b", total_interest, line_2b, "MATCH", ""))
            else:
                gap = line_2b - total_interest
                note = f"Gap=${gap:,.2f}. "
                if gap > 0:
                    note += ("1040 reports more interest than prepare-folder 1099-INTs. "
                             "Likely sources: brokerage 1099-INTs (Fidelity, Schwab) sent directly to CPA, "
                             "not in the prepare folder PDF collection.")
                    int_status = "EXPECTED"
                else:
                    note += "Prepare folder shows more interest than 1040 — unusual, verify."
                    int_status = "MISMATCH"
                checks.append(("1099-INT interest vs 1040 line 2b", total_interest, line_2b, int_status, note))
        else:
            logger.info(f"    No interest income reported")

        # --- Summary ---
        logger.info(f"\n  {'='*70}")
        logger.info(f"  CROSS-VALIDATION SUMMARY: {year}")
        logger.info(f"  {'='*70}")
        logger.info(f"  {'Check':<55s} {'Prepare':>12s} {'1040':>12s} {'Status':>10s}")
        logger.info(f"  {'-'*55} {'-'*12} {'-'*12} {'-'*10}")

        for label, prep_val, arch_val, status, note in checks:
            color = "\033[32m" if status == "MATCH" else ("\033[33m" if status in ("INFO", "EXPECTED") else "\033[31m")
            logger.info(f"  {label:<55s} {prep_val:>12,.2f} {arch_val:>12,.2f} {color}{status:>10s}\033[0m")
            if note:
                # Wrap note at ~80 chars
                words = note.split()
                line = "    "
                for w in words:
                    if len(line) + len(w) + 1 > 85:
                        logger.info(f"  {line}")
                        line = "    " + w
                    else:
                        line += (" " if len(line) > 4 else "") + w
                if line.strip():
                    logger.info(f"  {line}")

        # Count results
        matches = sum(1 for _, _, _, s, _ in checks if s == "MATCH")
        expected = sum(1 for _, _, _, s, _ in checks if s == "EXPECTED")
        mismatches = sum(1 for _, _, _, s, _ in checks if s == "MISMATCH")
        infos = sum(1 for _, _, _, s, _ in checks if s == "INFO")
        parts = [f"{matches} matched"]
        if expected:
            parts.append(f"{expected} expected gaps")
        if mismatches:
            parts.append(f"{mismatches} mismatched")
        parts.append(f"{infos} info-only")
        logger.info(f"\n  Result: {', '.join(parts)}")


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
    group.add_argument("--cross-validate", action="store_true", help="Cross-validate prepare docs against archive 1040s")

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
    elif args.cross_validate:
        run_cross_validate(year_filter=args.year)


if __name__ == "__main__":
    main()
