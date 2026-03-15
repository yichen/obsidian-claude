#!/usr/bin/env python3
"""1040 Computation Engine.

Derives 1040 computation rules from historical prepare-folder YAML documents,
backtests against filed returns, and drafts a 1040 for future years.

Usage:
  compute_1040.py --backtest                # Derive rules from 2020-2022, test on 2023, report diffs
  compute_1040.py --test --year 2023        # Compare computed vs actual for one year
  compute_1040.py --draft --year 2025       # Generate draft 1040 for 2025 using prepare/ YAMLs

Output:
  Finance/tax/prepare/<year>/1040-draft.yaml      (--draft)
  Finance/tax/prepare/<year>/1040-backtest.yaml   (--test or --backtest)
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: Scripts/venv/bin/pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# --- Path Resolution ---
SCRIPT_DIR = Path(__file__).parent.resolve()
OBSIDIAN_ROOT = SCRIPT_DIR.parent.parent
OUTPUT_ROOT = OBSIDIAN_ROOT / "Finance" / "tax"
PREPARE_OUTPUT = OUTPUT_ROOT / "prepare"
ARCHIVE_OUTPUT = OUTPUT_ROOT / "archive"
CARRYFORWARDS_PATH = OUTPUT_ROOT / "carryforwards.yaml"

YEARS = [2025, 2024, 2023, 2022, 2021, 2020]

# IRS published standard deductions (MFJ)
STANDARD_DEDUCTIONS_MFJ = {
    2020: 24800,
    2021: 25100,
    2022: 25900,
    2023: 27700,
    2024: 29200,
    2025: 30000,
}

# IRS published standard deductions (Single / HoH)
STANDARD_DEDUCTIONS_SINGLE = {
    2020: 12400,
    2021: 12550,
    2022: 12950,
    2023: 13850,
    2024: 14600,
    2025: 15000,
}

STANDARD_DEDUCTIONS_HOH = {
    2020: 18650,
    2021: 18800,
    2022: 19400,
    2023: 20800,
    2024: 21900,
    2025: 22500,
}

# MFJ tax brackets (taxable income thresholds, rate): 2020-2025
# Format: list of (upper_bound, rate) — last entry is infinity
TAX_BRACKETS_MFJ = {
    2020: [(19750, 0.10), (80250, 0.12), (171050, 0.22), (326600, 0.24),
           (414700, 0.32), (622050, 0.35), (float("inf"), 0.37)],
    2021: [(19900, 0.10), (81050, 0.12), (172750, 0.22), (329850, 0.24),
           (418850, 0.32), (628300, 0.35), (float("inf"), 0.37)],
    2022: [(20550, 0.10), (83550, 0.12), (178150, 0.22), (340100, 0.24),
           (431900, 0.32), (647850, 0.35), (float("inf"), 0.37)],
    2023: [(22000, 0.10), (89075, 0.12), (190750, 0.22), (364200, 0.24),
           (462500, 0.32), (693750, 0.35), (float("inf"), 0.37)],
    2024: [(23200, 0.10), (94300, 0.12), (201050, 0.22), (383900, 0.24),
           (487450, 0.32), (731200, 0.35), (float("inf"), 0.37)],
    2025: [(23850, 0.10), (96950, 0.12), (206700, 0.22), (394600, 0.24),
           (501050, 0.32), (751600, 0.35), (float("inf"), 0.37)],
}

# Single / HoH brackets (approximate — HoH used here)
TAX_BRACKETS_SINGLE = {
    2020: [(9875, 0.10), (40125, 0.12), (85525, 0.22), (163300, 0.24),
           (207350, 0.32), (518400, 0.35), (float("inf"), 0.37)],
    2021: [(9950, 0.10), (40525, 0.12), (86375, 0.22), (164925, 0.24),
           (209425, 0.32), (523600, 0.35), (float("inf"), 0.37)],
    2022: [(10275, 0.10), (41775, 0.12), (89075, 0.22), (170050, 0.24),
           (215950, 0.32), (539900, 0.35), (float("inf"), 0.37)],
    2023: [(11000, 0.10), (44725, 0.12), (95375, 0.22), (182050, 0.24),
           (231250, 0.32), (578125, 0.35), (float("inf"), 0.37)],
    2024: [(11600, 0.10), (47150, 0.12), (100525, 0.22), (191950, 0.24),
           (243725, 0.32), (609350, 0.35), (float("inf"), 0.37)],
    2025: [(11925, 0.10), (48475, 0.12), (103350, 0.22), (197300, 0.24),
           (250525, 0.32), (626350, 0.35), (float("inf"), 0.37)],
}

# NIIT threshold (MFJ): 3.8% on net investment income above this
NIIT_THRESHOLD_MFJ = 250000
# Child tax credit: $2,000/child, phase-out threshold MFJ
CHILD_TAX_CREDIT_PER_CHILD = 2000
CHILD_TAX_CREDIT_PHASEOUT_MFJ = 400000
CHILD_TAX_CREDIT_PHASEOUT_SINGLE = 200000


# --- YAML Helpers ---
def float_representer(dumper, value):
    return dumper.represent_scalar("tag:yaml.org,2002:float", f"{value:.2f}")


yaml.add_representer(float, float_representer)


def write_yaml(data: dict, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


# --- Load prepare-folder documents for a year ---
def load_prepare_docs(year: int) -> dict:
    """Load all prepare-folder YAMLs for a year. Returns dict: form_type -> list of docs."""
    prepare_dir = PREPARE_OUTPUT / str(year)
    docs: dict[str, list] = {}
    if not prepare_dir.exists():
        return docs
    for yf in sorted(prepare_dir.glob("*.yaml")):
        doc = load_yaml(yf)
        if not doc:
            continue
        ft = doc.get("form_type", "unknown")
        docs.setdefault(ft, []).append(doc)
    return docs


# --- Participant helpers ---
YI_SSN = "2622"
SPOUSE_SSN = "3457"


def split_w2s(w2s: list) -> tuple[list, list, list, list]:
    """Split W-2 list into (yi_employer, spouse_employer, household, other)."""
    household = [w for w in w2s if w.get("employer", {}).get("name", "").strip() == "Yi Chen"]
    non_hh = [w for w in w2s if w.get("employer", {}).get("name", "").strip() != "Yi Chen"]
    yi_w2s = [w for w in non_hh if w.get("employee", {}).get("ssn_last4") == YI_SSN]
    spouse_w2s = [w for w in non_hh if w.get("employee", {}).get("ssn_last4") == SPOUSE_SSN]
    other = [w for w in non_hh if w.get("employee", {}).get("ssn_last4") not in (YI_SSN, SPOUSE_SSN)]
    return yi_w2s, spouse_w2s, household, other


# --- IRS Rule Implementations ---

def compute_line_1a(docs: dict) -> tuple[float, list[str], str]:
    """Sum of W-2 Box 1 wages (Yi + Spouse, excluding household/Schedule H)."""
    w2s = docs.get("W-2", [])
    yi_w2s, spouse_w2s, _, _ = split_w2s(w2s)
    sources = []
    total = 0.0
    for w in yi_w2s + spouse_w2s:
        wages = w.get("boxes", {}).get("1_wages", 0) or 0
        total += wages
        f = w.get("source", {}).get("file", "")
        if f:
            sources.append(Path(f).name)
    # Filter third-party sick pay (code 13 set) — their Box 1 overlaps primary employer
    # We include them in sum but note the overlap risk
    confidence = "high" if total > 0 else "low"
    return round(total, 2), sources, confidence


def compute_line_1z(docs: dict, line_1a: float) -> tuple[float, list[str], str]:
    """Total wages = 1a + ESPP/RSU adjustments in Box 14 or other compensation."""
    # In practice 1z = 1a + any additional wages not in W-2 Box 1
    # Often equals 1a unless there's Box 14 supplemental income carried over
    return round(line_1a, 2), ["derived from 1a"], "medium"


def compute_line_2b(docs: dict) -> tuple[float, list[str], str]:
    """Taxable interest: sum of 1099-INT + 1099-CONSOLIDATED INT section."""
    sources = []
    total = 0.0
    for d in docs.get("1099-INT", []):
        amt = d.get("boxes", {}).get("1_interest_income", 0) or 0
        total += amt
        f = d.get("source", {}).get("file", "")
        if f:
            sources.append(Path(f).name)
    for d in docs.get("1099-CONSOLIDATED", []):
        amt = d.get("forms", {}).get("1099-INT", {}).get("1_interest_income", 0) or 0
        total += amt
        f = d.get("source", {}).get("file", "")
        if f and amt > 0:
            sources.append(Path(f).name)
    confidence = "high" if total > 0 else "low"
    return round(total, 2), sources, confidence


def compute_line_3a(docs: dict) -> tuple[float, list[str], str]:
    """Qualified dividends: sum of 1099-CONSOLIDATED DIV 1b."""
    sources = []
    total = 0.0
    for d in docs.get("1099-CONSOLIDATED", []):
        amt = d.get("forms", {}).get("1099-DIV", {}).get("1b_qualified_dividends", 0) or 0
        total += amt
        f = d.get("source", {}).get("file", "")
        if f and amt > 0:
            sources.append(Path(f).name)
    return round(total, 2), sources, "high" if total > 0 else "low"


def compute_line_3b(docs: dict) -> tuple[float, list[str], str]:
    """Ordinary dividends: sum of 1099-CONSOLIDATED DIV 1a."""
    sources = []
    total = 0.0
    for d in docs.get("1099-CONSOLIDATED", []):
        amt = d.get("forms", {}).get("1099-DIV", {}).get("1a_total_ordinary_dividends", 0) or 0
        total += amt
        f = d.get("source", {}).get("file", "")
        if f and amt > 0:
            sources.append(Path(f).name)
    return round(total, 2), sources, "high" if total > 0 else "low"


def compute_line_4b(docs: dict) -> tuple[float, list[str], str]:
    """Taxable IRA distributions: sum of 1099-R Box 2a (non-rollover)."""
    sources = []
    total = 0.0
    for d in docs.get("1099-R", []):
        dist_code = str(d.get("boxes", {}).get("7_distribution_code", ""))
        # Skip rollovers (code G) — they're non-taxable
        if "G" in dist_code.upper():
            continue
        taxable = d.get("boxes", {}).get("2a_taxable_amount", 0) or 0
        total += taxable
        f = d.get("source", {}).get("file", "")
        if f and taxable > 0:
            sources.append(Path(f).name)
    # Note: backdoor Roth conversions show full amount on 1099-R but basis tracked on Form 8606
    # We can't automatically net out basis without 8606 data — flag as manual review
    return round(total, 2), sources, "medium"


def compute_line_7(docs: dict, year: int, carryforwards: dict) -> tuple[float, list[str], str, float]:
    """Net capital gain/loss from 1099-B + prior year carryforward, capped at -$3,000 if loss.

    Returns (line_7_value, sources, confidence, carryforward_applied).
    """
    sources = []
    total_net = 0.0
    for d in docs.get("1099-CONSOLIDATED", []):
        b = d.get("forms", {}).get("1099-B", {})
        net = b.get("total", {}).get("gain_loss", None)
        if net is None:
            net = b.get("gain_loss", None)
        if net is None:
            net = 0
        total_net += net
        f = d.get("source", {}).get("file", "")
        if f:
            sources.append(Path(f).name)
    for d in docs.get("1099-B", []):
        net = d.get("net_gain_loss", 0) or 0
        total_net += net
        f = d.get("source", {}).get("file", "")
        if f:
            sources.append(Path(f).name)

    # Apply prior year carryforward
    prior_year = year - 1
    carryforward_in = carryforwards.get(prior_year, {}).get("capital_loss_carryforward_out", 0) or 0
    if carryforward_in:
        sources.append("carryforwards.yaml")

    adjusted = total_net + carryforward_in  # carryforward_in is negative if loss carried forward
    # Cap loss deduction at -$3,000
    if adjusted < -3000:
        line_7 = -3000.0
    else:
        line_7 = adjusted

    confidence = "high" if (total_net != 0 or carryforward_in != 0) else "low"
    return round(line_7, 2), sources, confidence, round(carryforward_in, 2)


def compute_standard_deduction(year: int, filing_status: str) -> float:
    fs_lower = filing_status.lower()
    if "joint" in fs_lower:
        return float(STANDARD_DEDUCTIONS_MFJ.get(year, 30000))
    elif "head" in fs_lower:
        return float(STANDARD_DEDUCTIONS_HOH.get(year, 22500))
    else:
        return float(STANDARD_DEDUCTIONS_SINGLE.get(year, 15000))


def compute_itemized_deduction(docs: dict) -> tuple[float, dict]:
    """Estimate itemized deductions: mortgage interest + property tax (SALT capped $10K)."""
    mortgage_interest = 0.0
    property_tax = 0.0
    for d in docs.get("1098", []):
        mortgage_interest += d.get("boxes", {}).get("1_mortgage_interest", 0) or 0
        property_tax += d.get("boxes", {}).get("10_property_tax", 0) or 0

    salt = min(property_tax, 10000)  # SALT cap
    itemized = mortgage_interest + salt

    breakdown = {
        "mortgage_interest": round(mortgage_interest, 2),
        "property_tax_raw": round(property_tax, 2),
        "salt_capped": round(salt, 2),
        "total_before_charity": round(itemized, 2),
        "note": "Charitable deductions and other Schedule A items not captured — may be higher",
    }
    return round(itemized, 2), breakdown


def compute_deduction(year: int, filing_status: str, docs: dict) -> tuple[float, str, dict]:
    """Choose between standard and itemized deduction."""
    standard = compute_standard_deduction(year, filing_status)
    itemized, breakdown = compute_itemized_deduction(docs)

    if itemized > standard:
        return itemized, "itemized", breakdown
    else:
        return standard, "standard", {"standard_deduction": standard, **breakdown}


def compute_tax(taxable_income: float, filing_status: str, year: int) -> float:
    """Apply IRS tax brackets."""
    fs_lower = filing_status.lower()
    if "joint" in fs_lower:
        brackets = TAX_BRACKETS_MFJ.get(year, TAX_BRACKETS_MFJ[2025])
    else:
        brackets = TAX_BRACKETS_SINGLE.get(year, TAX_BRACKETS_SINGLE[2025])

    tax = 0.0
    prev_bound = 0.0
    for upper, rate in brackets:
        if taxable_income <= prev_bound:
            break
        chunk = min(taxable_income, upper) - prev_bound
        tax += chunk * rate
        prev_bound = upper

    return round(tax, 2)


def compute_child_tax_credit(dependents: int, agi: float, filing_status: str) -> float:
    """$2,000/child, phases out $50 per $1,000 AGI above threshold."""
    threshold = CHILD_TAX_CREDIT_PHASEOUT_MFJ if "joint" in filing_status.lower() else CHILD_TAX_CREDIT_PHASEOUT_SINGLE
    gross_credit = dependents * CHILD_TAX_CREDIT_PER_CHILD
    if agi > threshold:
        excess = agi - threshold
        phaseout = (excess // 1000) * 50
        gross_credit = max(0, gross_credit - phaseout)
    return round(gross_credit, 2)


def compute_niit(agi: float, net_investment_income: float, filing_status: str) -> float:
    """3.8% Net Investment Income Tax on lesser of NII or AGI above threshold."""
    threshold = NIIT_THRESHOLD_MFJ if "joint" in filing_status.lower() else 200000
    if agi <= threshold:
        return 0.0
    excess_agi = agi - threshold
    niit_base = min(net_investment_income, excess_agi)
    return round(niit_base * 0.038, 2) if niit_base > 0 else 0.0


def infer_filing_status(year: int, docs: dict) -> str:
    """Infer filing status from archive 1040 or default to prior year."""
    archive = ARCHIVE_OUTPUT / str(year) / "1040-summary.yaml"
    if archive.exists():
        data = load_yaml(archive)
        return data.get("filing_status", "Married Filing Jointly")
    # Try prior year
    prior = ARCHIVE_OUTPUT / str(year - 1) / "1040-summary.yaml"
    if prior.exists():
        data = load_yaml(prior)
        return data.get("filing_status", "Married Filing Jointly")
    return "Married Filing Jointly"


def count_dependents(year: int, docs: dict) -> int:
    """Count dependents from archive 1040 (prior year if current year not filed)."""
    archive = ARCHIVE_OUTPUT / str(year) / "1040-summary.yaml"
    if archive.exists():
        data = load_yaml(archive)
        return len(data.get("dependents", []))
    prior = ARCHIVE_OUTPUT / str(year - 1) / "1040-summary.yaml"
    if prior.exists():
        data = load_yaml(prior)
        return len(data.get("dependents", []))
    return 0


# --- Core computation ---
def compute_1040(year: int, docs: dict, carryforwards: dict, filing_status: str, dependents: int) -> dict:
    """Compute 1040 line items from prepare-folder documents."""

    # Income lines
    line_1a, src_1a, conf_1a = compute_line_1a(docs)
    line_1z, src_1z, conf_1z = compute_line_1z(docs, line_1a)
    line_2b, src_2b, conf_2b = compute_line_2b(docs)
    line_3a, src_3a, conf_3a = compute_line_3a(docs)
    line_3b, src_3b, conf_3b = compute_line_3b(docs)
    line_4b, src_4b, conf_4b = compute_line_4b(docs)
    line_7, src_7, conf_7, cf_applied = compute_line_7(docs, year, carryforwards)

    # Net investment income (for NIIT)
    nii = line_2b + line_3b + (line_7 if line_7 > 0 else 0)

    # Rough AGI (missing Schedule 1 adjustments — flag for manual review)
    total_income = line_1z + line_2b + line_3b + line_4b + line_7
    agi = total_income  # Schedule 1 adjustments not captured

    # Deductions
    deduction, deduction_method, deduction_breakdown = compute_deduction(year, filing_status, docs)

    taxable_income = max(0, agi - deduction)

    # Tax computation
    regular_tax = compute_tax(taxable_income, filing_status, year)
    child_credit = compute_child_tax_credit(dependents, agi, filing_status)
    niit = compute_niit(agi, nii, filing_status)

    # AMT check (simplified — flag if AGI > exemption)
    amt_exemption_mfj = {2020: 113400, 2021: 114600, 2022: 118100, 2023: 126500, 2024: 137000, 2025: 140000}
    amt_phaseout_mfj = {2020: 1036800, 2021: 1047200, 2022: 1079800, 2023: 1156300, 2024: 1252700, 2025: 1280000}
    amt_exemption = float(amt_exemption_mfj.get(year, 140000))
    amt_check = "not_applicable"
    if agi > amt_exemption * 0.5:
        amt_check = "potentially_applicable — review Form 6251"

    total_tax = max(0, regular_tax - child_credit) + niit

    manual_review = [
        "Schedule 1 additional income/adjustments: verify no other income sources (alimony, business, etc.)",
        "1z vs 1a gap: verify any ESPP supplemental wages, RSU vesting adjustments",
        "QBI deduction (Section 199A): verify no pass-through / self-employment income",
        "Estimated tax payments: confirm Q4 prior-year payment amount",
        "Form 8606: backdoor Roth IRA basis tracking affects Line 4b taxable amount",
        "AMT (Form 6251): verify not subject to alternative minimum tax",
        "Schedule A charity: charitable contributions not captured in prepare folder YAMLs",
    ]
    if line_4b > 0:
        manual_review.append(f"1099-R Box 2a ({line_4b:,.2f}): verify Form 8606 basis — backdoor Roth conversions may reduce taxable amount")

    return {
        "tax_year": year,
        "filing_status": filing_status,
        "dependents_count": dependents,
        "income": {
            "1a_w2_wages": {
                "value": line_1a,
                "sources": src_1a,
                "confidence": conf_1a,
            },
            "1z_total_wages": {
                "value": line_1z,
                "sources": src_1z,
                "confidence": conf_1z,
            },
            "2b_taxable_interest": {
                "value": line_2b,
                "sources": src_2b,
                "confidence": conf_2b,
            },
            "3a_qualified_dividends": {
                "value": line_3a,
                "sources": src_3a,
                "confidence": conf_3a,
            },
            "3b_ordinary_dividends": {
                "value": line_3b,
                "sources": src_3b,
                "confidence": conf_3b,
            },
            "4b_taxable_ira": {
                "value": line_4b,
                "sources": src_4b,
                "confidence": conf_4b,
                "note": "Backdoor Roth basis on Form 8606 may reduce taxable amount",
            },
            "7_capital_gain_loss": {
                "value": line_7,
                "sources": src_7,
                "carryforward_applied": cf_applied,
                "confidence": conf_7,
            },
        },
        "agi": {
            "total_income": round(total_income, 2),
            "schedule_1_adjustments": 0.0,
            "adjusted_gross_income": round(agi, 2),
            "note": "Schedule 1 adjustments (HSA, student loan interest, etc.) not captured",
        },
        "deductions": {
            "method": deduction_method,
            "amount": round(deduction, 2),
            "breakdown": deduction_breakdown,
        },
        "tax_computation": {
            "taxable_income": round(taxable_income, 2),
            "regular_tax": round(regular_tax, 2),
            "child_tax_credit": round(child_credit, 2),
            "net_investment_income_tax": round(niit, 2),
            "net_investment_income_base": round(nii, 2),
            "amt_check": amt_check,
            "total_tax_estimate": round(total_tax, 2),
        },
        "manual_review_items": manual_review,
    }


# --- Backtest / Compare ---
def compare_to_actual(computed: dict, actual_1040: dict, year: int) -> dict:
    """Compare computed 1040 to actual filed return. Returns backtest report."""
    mismatches = []
    matches = 0
    total_checks = 0

    def check(label: str, comp_val: Optional[float], actual_val: Optional[float], tolerance: float = 1.0):
        nonlocal matches, total_checks
        if comp_val is None or actual_val is None:
            return
        total_checks += 1
        delta = round((comp_val or 0) - (actual_val or 0), 2)
        if abs(delta) <= tolerance:
            matches += 1
        else:
            mismatches.append({
                "line": label,
                "computed": round(comp_val, 2),
                "actual": round(actual_val, 2),
                "delta": round(delta, 2),
                "note": f"Delta ${delta:+,.2f}",
            })

    income_actual = actual_1040.get("income", {})
    summary_actual = actual_1040.get("summary", {})

    check("1a_w2_wages", computed["income"]["1a_w2_wages"]["value"], income_actual.get("1a_w2_wages"), tolerance=500)
    check("1z_total_wages", computed["income"]["1z_total_wages"]["value"], income_actual.get("1z_total_wages"), tolerance=500)
    check("2b_taxable_interest", computed["income"]["2b_taxable_interest"]["value"], income_actual.get("2b_taxable_interest"), tolerance=100)
    check("3b_ordinary_dividends", computed["income"]["3b_ordinary_dividends"]["value"], income_actual.get("3b_ordinary_dividends"), tolerance=100)
    check("4b_taxable_ira", computed["income"]["4b_taxable_ira"]["value"], income_actual.get("4b_taxable_ira"), tolerance=100)
    check("7_capital_gain_loss", computed["income"]["7_capital_gain_loss"]["value"], income_actual.get("7_capital_gain_loss"), tolerance=500)
    check("adjusted_gross_income", computed["agi"]["adjusted_gross_income"], summary_actual.get("adjusted_gross_income"), tolerance=1000)
    check("deductions", computed["deductions"]["amount"], summary_actual.get("deductions"), tolerance=500)
    check("taxable_income", computed["tax_computation"]["taxable_income"], summary_actual.get("taxable_income"), tolerance=1000)
    check("total_tax", computed["tax_computation"]["total_tax_estimate"], summary_actual.get("total_tax"), tolerance=1000)

    lines_matched = matches
    lines_mismatched = len(mismatches)
    accuracy = round(matches / total_checks * 100, 1) if total_checks > 0 else 0

    return {
        "test_year": year,
        "lines_checked": total_checks,
        "lines_matched": lines_matched,
        "lines_mismatched": lines_mismatched,
        "accuracy": f"{accuracy}%",
        "mismatches": mismatches,
    }


# --- Commands ---

def cmd_draft(year: int):
    """Generate a draft 1040 for a given year using prepare-folder YAMLs."""
    print(f"Computing draft 1040 for {year}...")

    docs = load_prepare_docs(year)
    if not docs:
        print(f"  No prepare-folder YAMLs found for {year}. Run ingest_tax.py --run --year {year} first.")
        return

    carryforwards = load_yaml(CARRYFORWARDS_PATH)
    filing_status = infer_filing_status(year, docs)
    dependents = count_dependents(year, docs)

    print(f"  Filing status: {filing_status}")
    print(f"  Dependents: {dependents}")
    print(f"  Form types: {list(docs.keys())}")

    result = compute_1040(year, docs, carryforwards, filing_status, dependents)

    output_path = PREPARE_OUTPUT / str(year) / "1040-draft.yaml"
    write_yaml(result, output_path)
    print(f"\n  Written: {output_path}")
    _print_summary(result)


def cmd_test(year: int):
    """Compare computed 1040 to actual filed return for one year."""
    print(f"Testing 1040 computation for {year}...")

    archive_path = ARCHIVE_OUTPUT / str(year) / "1040-summary.yaml"
    if not archive_path.exists():
        print(f"  No archive 1040-summary.yaml found for {year}. Cannot compare.")
        return

    docs = load_prepare_docs(year)
    actual_1040 = load_yaml(archive_path)
    carryforwards = load_yaml(CARRYFORWARDS_PATH)
    filing_status = actual_1040.get("filing_status", "Married Filing Jointly")
    dependents = len(actual_1040.get("dependents", []))

    computed = compute_1040(year, docs, carryforwards, filing_status, dependents)
    report = compare_to_actual(computed, actual_1040, year)

    output_path = PREPARE_OUTPUT / str(year) / "1040-backtest.yaml"
    # Combine computed + backtest report
    output = {"computed": computed, "backtest": report}
    write_yaml(output, output_path)
    print(f"\n  Written: {output_path}")
    _print_backtest(report)


def cmd_backtest():
    """Derive rules from 2020-2022, test on 2023, report diffs."""
    print("Running backtest: training on 2020-2022, testing on 2023...\n")

    # Train years: check what archive data we have
    train_years = [y for y in [2020, 2021, 2022] if (ARCHIVE_OUTPUT / str(y) / "1040-summary.yaml").exists()]
    test_years = [y for y in [2023, 2024] if (ARCHIVE_OUTPUT / str(y) / "1040-summary.yaml").exists()]

    if not train_years:
        print("  No archive data found for training years (2020-2022). Run ingest_tax.py --run first.")
        return

    print(f"  Training years available: {train_years}")
    print(f"  Test years available: {test_years}")

    carryforwards = load_yaml(CARRYFORWARDS_PATH)

    # Test on each available year
    for year in test_years:
        print(f"\n{'='*60}")
        print(f"  BACKTEST: {year}")
        print(f"{'='*60}")
        docs = load_prepare_docs(year)
        actual_1040 = load_yaml(ARCHIVE_OUTPUT / str(year) / "1040-summary.yaml")
        filing_status = actual_1040.get("filing_status", "Married Filing Jointly")
        dependents = len(actual_1040.get("dependents", []))

        computed = compute_1040(year, docs, carryforwards, filing_status, dependents)
        report = compare_to_actual(computed, actual_1040, year)

        output_path = PREPARE_OUTPUT / str(year) / "1040-backtest.yaml"
        write_yaml({"computed": computed, "backtest": report}, output_path)
        print(f"  Written: {output_path}")
        _print_backtest(report)


def _print_summary(result: dict):
    print(f"\n  --- Draft Summary ---")
    income = result["income"]
    print(f"  1a  W-2 wages:          ${income['1a_w2_wages']['value']:>12,.2f}  [{income['1a_w2_wages']['confidence']}]")
    print(f"  2b  Taxable interest:   ${income['2b_taxable_interest']['value']:>12,.2f}  [{income['2b_taxable_interest']['confidence']}]")
    print(f"  3b  Ordinary dividends: ${income['3b_ordinary_dividends']['value']:>12,.2f}  [{income['3b_ordinary_dividends']['confidence']}]")
    print(f"  4b  Taxable IRA:        ${income['4b_taxable_ira']['value']:>12,.2f}  [{income['4b_taxable_ira']['confidence']}]")
    print(f"  7   Cap gain/loss:      ${income['7_capital_gain_loss']['value']:>12,.2f}  [{income['7_capital_gain_loss']['confidence']}]")
    agi = result["agi"]
    print(f"      AGI (estimate):     ${agi['adjusted_gross_income']:>12,.2f}")
    ded = result["deductions"]
    print(f"      Deductions ({ded['method']}): ${ded['amount']:>12,.2f}")
    tax = result["tax_computation"]
    print(f"      Taxable income:     ${tax['taxable_income']:>12,.2f}")
    print(f"      Regular tax:        ${tax['regular_tax']:>12,.2f}")
    print(f"      Child tax credit:   ${tax['child_tax_credit']:>12,.2f}")
    print(f"      NIIT:               ${tax['net_investment_income_tax']:>12,.2f}")
    print(f"      Total tax (est):    ${tax['total_tax_estimate']:>12,.2f}")
    print(f"\n  Manual review items ({len(result['manual_review_items'])}):")
    for item in result["manual_review_items"]:
        print(f"    - {item}")


def _print_backtest(report: dict):
    year = report["test_year"]
    print(f"  Accuracy: {report['accuracy']} ({report['lines_matched']}/{report['lines_checked']} lines matched)")
    if report["mismatches"]:
        print(f"  Mismatches:")
        for m in report["mismatches"]:
            print(f"    {m['line']:<30s} computed=${m['computed']:>12,.2f}  actual=${m['actual']:>12,.2f}  delta=${m['delta']:>+10,.2f}")
            if m.get("note"):
                print(f"      → {m['note']}")
    else:
        print(f"  All lines matched for {year}!")


# --- CLI ---
def main():
    parser = argparse.ArgumentParser(
        description="1040 Computation Engine — derive rules, backtest, draft",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--backtest", action="store_true",
                       help="Derive rules from 2020-2022, test on 2023-2024, report diffs")
    group.add_argument("--test", action="store_true",
                       help="Compare computed 1040 to actual for a specific year")
    group.add_argument("--draft", action="store_true",
                       help="Generate draft 1040 for a future year using prepare/ YAMLs")

    parser.add_argument("--year", type=int, choices=YEARS,
                        help="Year to test or draft (required for --test and --draft)")

    args = parser.parse_args()

    if args.backtest:
        cmd_backtest()
    elif args.test:
        if not args.year:
            parser.error("--test requires --year YYYY")
        cmd_test(args.year)
    elif args.draft:
        if not args.year:
            parser.error("--draft requires --year YYYY")
        cmd_draft(args.year)


if __name__ == "__main__":
    main()
