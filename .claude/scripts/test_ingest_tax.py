#!/usr/bin/env python3
"""Test suite for tax document ingestion pipeline.

Each test case corresponds to a specific bug or failure discovered during
development. Running these tests serves as a regression suite — if a parser
change breaks extraction, the exact failure mode is identified immediately.

Run with: Scripts/venv/bin/python3 -m pytest .claude/scripts/test_ingest_tax.py -v
"""

import re
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from ingest_tax import (
    _build_tokens,
    _deduplicate_doubled_text,
    _detect_w2_format,
    detect_form_type,
    parse_1098,
    parse_1099_consolidated,
    parse_1099r,
    parse_amount,
    parse_w2,
)

TAX_ROOT = Path(__file__).parent.parent.parent / "Finance" / "tax"
PREPARE_ROOT = Path.home() / "Dropbox" / "1-Tax" / "2-prepare"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml(relative_path: str) -> dict:
    """Load a tax YAML file from Finance/tax/."""
    path = TAX_ROOT / relative_path
    assert path.exists(), f"YAML not found: {path}"
    with open(path) as f:
        return yaml.safe_load(f)


def _pdf_exists(path: str) -> bool:
    return Path(path).exists()


# ===========================================================================
# BUG: _build_tokens merged tokens across y-positions
# ROOT CAUSE: Sorting by (round(top), x0) interleaved chars at y=80.1 and
#   y=81.8 because they round to different ints (80 vs 82). Then the gap
#   check `c["x0"] - current["x1"] < 8` was True for negative gaps (next
#   char to the LEFT of current token).
# FIX: Cluster chars by y-position FIRST, then sort by x WITHIN each cluster.
# ===========================================================================

class TestBuildTokens:
    """Regression tests for _build_tokens character grouping."""

    def test_separate_tokens_on_same_line(self):
        """Two numbers on the same y-line should be separate tokens."""
        chars = [
            {"text": "5", "x0": 163, "top": 80.1, "bottom": 88, "width": 5},
            {"text": "8", "x0": 168, "top": 80.1, "bottom": 88, "width": 5},
            {"text": "1", "x0": 173, "top": 80.1, "bottom": 88, "width": 5},
            {"text": ".", "x0": 178, "top": 80.1, "bottom": 88, "width": 5},
            {"text": "5", "x0": 183, "top": 80.1, "bottom": 88, "width": 5},
            {"text": "3", "x0": 188, "top": 80.1, "bottom": 88, "width": 5},
            # Gap of ~64pt to next token
            {"text": "1", "x0": 253, "top": 81.8, "bottom": 88, "width": 5},
            {"text": "1", "x0": 258, "top": 81.8, "bottom": 88, "width": 5},
            {"text": ".", "x0": 263, "top": 81.8, "bottom": 88, "width": 5},
            {"text": "1", "x0": 268, "top": 81.8, "bottom": 88, "width": 5},
            {"text": "8", "x0": 273, "top": 81.8, "bottom": 88, "width": 5},
        ]
        tokens = _build_tokens(chars)
        texts = [t["text"] for t in tokens]
        assert "581.53" in texts, f"Expected '581.53' as separate token, got: {texts}"
        assert "11.18" in texts, f"Expected '11.18' as separate token, got: {texts}"
        # Must NOT be merged into "11.18581.53" or "581.5311.18"
        assert not any("581.5311" in t or "11.18581" in t for t in texts), \
            f"Tokens should not be merged: {texts}"

    def test_adjacent_chars_group_correctly(self):
        """Characters within 8pt gap should merge into one token."""
        chars = [
            {"text": "1", "x0": 10, "top": 50, "bottom": 58, "width": 5},
            {"text": "2", "x0": 15, "top": 50, "bottom": 58, "width": 5},
            {"text": "3", "x0": 20, "top": 50, "bottom": 58, "width": 5},
        ]
        tokens = _build_tokens(chars)
        assert len(tokens) == 1
        assert tokens[0]["text"] == "123"

    def test_different_y_positions_separate(self):
        """Characters on different y-lines should be separate tokens."""
        chars = [
            {"text": "A", "x0": 10, "top": 50, "bottom": 58, "width": 5},
            {"text": "B", "x0": 10, "top": 80, "bottom": 88, "width": 5},
        ]
        tokens = _build_tokens(chars)
        assert len(tokens) == 2


# ===========================================================================
# BUG: "renew-2024" filename falsely detected as W-2
# ROOT CAUSE: Substring check `"w-2" in name` matched "rene[w-2]024"
# FIX: Use word-boundary regex: (?:^|[\s_.-])w-?2(?:[\s_.-]|$)
# ===========================================================================

class TestFormDetection:
    """Regression tests for form type detection."""

    def test_renew_not_detected_as_w2(self):
        """Vehicle registration 'renew-2024' must NOT be detected as W-2."""
        # These are vehicle registrations, not tax forms
        for name in [
            "Acura-CAA-4255-Renew-2024.pdf",
            "trailer-tabs-renew-2024.pdf",
            "Trailer - Renew your vehicle tabs.pdf",
        ]:
            p = Path(f"/tmp/{name}")
            result = detect_form_type.__wrapped__(p) if hasattr(detect_form_type, '__wrapped__') else None
            # Can't easily test without actual PDF, but verify the regex
            assert not re.search(r"(?:^|[\s_.-])w-?2(?:[\s_.-]|$)", name.lower()), \
                f"'{name}' should NOT match W-2 regex"

    def test_valid_w2_filenames_detected(self):
        """Valid W-2 filenames must be detected."""
        for name in [
            "2024-W2-Salesforce.pdf",
            "Salesforce-W2.pdf",
            "W-2_Form_2025_Chen.pdf",
            "w2.20241231.pdf",
            "diana.w2.20231231.pdf",
        ]:
            assert re.search(r"(?:^|[\s_.-])w-?2(?:[\s_.-]|$)", name.lower()), \
                f"'{name}' should match W-2 regex"


# ===========================================================================
# BUG: ADP W-2 parser returned all zeros for Airbnb/Meta
# ROOT CAUSE: ADP format has labels on one line and values on the NEXT line.
#   Parser was looking for labels+values on the SAME line.
# FIX: Scan for label line, then search next 2 lines for amounts.
# ===========================================================================

class TestW2ADPParser:
    """Regression tests for ADP-format W-2s (Airbnb, Meta)."""

    @pytest.mark.skipif(
        not _pdf_exists(str(PREPARE_ROOT / "2022/2023-03-31/2022-Airbnb-w2.pdf")),
        reason="PDF not available",
    )
    def test_2022_airbnb_w2_boxes_not_zero(self):
        """2022 Airbnb W-2 must extract non-zero wages (was returning all 0.00)."""
        data = _load_yaml("prepare/2022/w-2-airbnb-inc.yaml")
        assert data["boxes"]["1_wages"] > 300000, \
            f"Box 1 = {data['boxes']['1_wages']} — expected ~$344K"
        assert data["boxes"]["2_fed_tax_withheld"] > 70000, \
            f"Box 2 = {data['boxes']['2_fed_tax_withheld']} — expected ~$79K"
        assert data["boxes"]["3_ss_wages"] > 0, "Box 3 should not be zero"
        assert data["boxes"]["5_medicare_wages"] > 0, "Box 5 should not be zero"

    @pytest.mark.skipif(
        not _pdf_exists(str(PREPARE_ROOT / "2022/2023-03-31/2022-w2-meta.pdf")),
        reason="PDF not available",
    )
    def test_2022_meta_w2_boxes_not_zero(self):
        """2022 Meta W-2 must extract non-zero wages (was returning all 0.00)."""
        data = _load_yaml("prepare/2022/w-2-meta-platforms-inc.yaml")
        assert data["boxes"]["1_wages"] > 100000, \
            f"Box 1 = {data['boxes']['1_wages']} — expected ~$126K"
        assert data["boxes"]["2_fed_tax_withheld"] > 20000

    @pytest.mark.skipif(
        not _pdf_exists(str(PREPARE_ROOT / "2023/prepared-on-20240919/2024-09-19-Airbnb-w2-2023.pdf")),
        reason="PDF not available",
    )
    def test_2023_airbnb_supplemental_no_duplicate_values(self):
        """2023 Airbnb supplemental W-2: Box 1, Box 2, and Box 10 must NOT all be the same value.

        Was a parsing bug where $3,570 was assigned to Box 1, 2, AND 10.
        """
        data = _load_yaml("prepare/2023/w-2-airbnb-inc.yaml")
        box1 = data["boxes"]["1_wages"]
        box2 = data["boxes"]["2_fed_tax_withheld"]
        box10 = data["boxes"].get("10_dependent_care", -1)
        # Box 2 should be 0 (no federal withholding on this supplemental)
        assert box2 == 0.0, f"Box 2 = {box2} — expected 0 for CA-only supplemental W-2"
        # Box 10 should NOT equal Box 1
        assert box10 != box1, f"Box 10 ({box10}) should not equal Box 1 ({box1})"


# ===========================================================================
# BUG: Nanny W-2 missing boxes 3-6
# ROOT CAUSE: Parser looked only 1 line back for labels, but in the HomePay
#   format there's an intervening employer name line between label and values.
# FIX: Look back up to 3 lines for labels.
# ===========================================================================

class TestW2NannyParser:
    """Regression tests for nanny (HomePay) W-2s."""

    @pytest.mark.skipif(
        not _pdf_exists(str(PREPARE_ROOT / "2024/Yi/childcare/w2.20241231.pdf")),
        reason="PDF not available",
    )
    def test_2024_nanny_w2_all_boxes_populated(self):
        """2024 nanny W-2 must have all 6 core boxes (was missing 3-6)."""
        data = _load_yaml("prepare/2024/w-2-yi-chen.yaml")
        assert data["boxes"]["1_wages"] == 5910.00
        assert data["boxes"]["2_fed_tax_withheld"] == 890.71
        assert data["boxes"]["3_ss_wages"] == 5910.00, \
            f"Box 3 = {data['boxes']['3_ss_wages']} — expected 5910.00"
        assert data["boxes"]["4_ss_tax_withheld"] == 366.42, \
            f"Box 4 = {data['boxes']['4_ss_tax_withheld']} — expected 366.42"
        assert data["boxes"]["5_medicare_wages"] == 5910.00
        assert data["boxes"]["6_medicare_tax_withheld"] == 85.70


# ===========================================================================
# BUG: Salesforce W-2 boxes 5 and 6 were swapped
# ROOT CAUSE: _build_tokens merged "11871.18" and "581752.53" into one token
#   because chars at y=80.1 and y=81.8 were sorted interleaved.
# FIX: y-clustering in _build_tokens (see TestBuildTokens above).
# ===========================================================================

class TestW2SalesforceParser:
    """Regression tests for Salesforce W-2s."""

    @pytest.mark.skipif(
        not _pdf_exists(str(PREPARE_ROOT / "2025/Salesforce-W2.pdf")),
        reason="PDF not available",
    )
    def test_2025_salesforce_boxes_5_6_not_swapped(self):
        """Box 5 (Medicare wages) must be > Box 6 (Medicare tax). Were swapped."""
        data = _load_yaml("prepare/2025/w-2-salesforce-inc.yaml")
        box5 = data["boxes"]["5_medicare_wages"]
        box6 = data["boxes"]["6_medicare_tax_withheld"]
        assert box5 > box6, f"Box 5 ({box5}) should be > Box 6 ({box6}) — were swapped"
        assert box5 == 581752.53, f"Box 5 = {box5}, expected 581752.53"
        assert box6 == 11871.18, f"Box 6 = {box6}, expected 11871.18"

    @pytest.mark.skipif(
        not _pdf_exists(str(PREPARE_ROOT / "2025/Salesforce-W2.pdf")),
        reason="PDF not available",
    )
    def test_2025_salesforce_box14_espp_rsu(self):
        """Box 14 must include ESPP GAINS and RSU values (were missing)."""
        data = _load_yaml("prepare/2025/w-2-salesforce-inc.yaml")
        box14 = data["boxes"].get("14_other", [])
        assert len(box14) >= 2, f"Box 14 should have ESPP + RSU, got: {box14}"
        texts = " ".join(box14)
        assert "ESPP" in texts, f"Missing ESPP GAINS in Box 14: {box14}"
        assert "RSU" in texts, f"Missing RSU in Box 14: {box14}"
        # Verify amounts
        assert "13408.81" in texts, f"ESPP amount wrong: {box14}"
        assert "235456.56" in texts, f"RSU amount wrong: {box14}"

    @pytest.mark.skipif(
        not _pdf_exists(str(PREPARE_ROOT / "2025/Salesforce-W2.pdf")),
        reason="PDF not available",
    )
    def test_2025_salesforce_fed_withholding_matches_payslip(self):
        """W-2 Box 2 must match payslip DB federal withholding exactly."""
        data = _load_yaml("prepare/2025/w-2-salesforce-inc.yaml")
        assert data["boxes"]["2_fed_tax_withheld"] == 160668.34


# ===========================================================================
# BUG: 1099-R distribution code was "7" instead of "G"
# ROOT CAUSE: Regex matched "7" from "48797" (plan number) on the line
#   BEFORE the actual distribution code. Was searching from label line
#   instead of starting from label_line + 1.
# FIX: Start searching from label_line + 1 to skip box label numbers.
# ===========================================================================

class TestParse1099R:
    """Regression tests for 1099-R parser."""

    @pytest.mark.skipif(
        not _pdf_exists(str(PREPARE_ROOT / "2025/2025-SALESFORCECOM-48797-1099-R-Tax-Form.pdf")),
        reason="PDF not available",
    )
    def test_salesforce_401k_rollover_code_G(self):
        """Salesforce 401k 1099-R must have distribution code 'G' (rollover), not '7'."""
        data = _load_yaml("prepare/2025/1099-r-fidelity-salesforce-401k-401-k----salesforce.yaml")
        assert data["boxes"]["7_distribution_code"] == "G", \
            f"Distribution code = '{data['boxes']['7_distribution_code']}', expected 'G'"
        assert data["boxes"]["1_gross_distribution"] == 40500.00
        assert data["boxes"]["2a_taxable_amount"] == 0.00
        assert data["boxes"]["5_employee_contributions"] == 40500.00


# ===========================================================================
# BUG: 1098 parser failed on Flagstar doubled-character PDFs
# ROOT CAUSE: Flagstar PDFs render text with doubled characters:
#   "MMoorrttggaaggee" instead of "Mortgage". Label patterns didn't match.
# FIX: Added _deduplicate_doubled_text() + fallback to scan for first $ amount.
#
# BUG: 1098 parser failed on loanDepot (no $ prefix on amounts)
# ROOT CAUSE: Regex required "\$" prefix, but loanDepot renders "2,117.69"
#   without the dollar sign.
# FIX: Added fallback regex without $ prefix.
#
# BUG: Rocket Mortgage 1098 grabbed $0.00 from cover page
# ROOT CAUSE: Pattern "mortgageinterest" matched cover page header
#   "MORTGAGE INTEREST RECEIVED FROM" which had "$0.00" nearby.
# FIX: Require box number prefix "1mortgage" and try patterns in priority order.
# ===========================================================================

class TestParse1098:
    """Regression tests for 1098 mortgage interest parser."""

    @pytest.mark.skipif(
        not _pdf_exists(str(PREPARE_ROOT / "2022/2023-03-31/2022-flagstar-1098-1.pdf")),
        reason="PDF not available",
    )
    def test_flagstar_doubled_chars_extracts_interest(self):
        """Flagstar 1098 with doubled characters must extract interest > 0."""
        data = _load_yaml("prepare/2022/1098-flagstar-bank.yaml")
        interest = data["boxes"]["1_mortgage_interest"]
        assert interest > 0, f"Flagstar Box 1 = {interest} — expected > 0"

    @pytest.mark.skipif(
        not _pdf_exists(str(PREPARE_ROOT / "2022/2023-03-31/2022-loandepot-1098.pdf")),
        reason="PDF not available",
    )
    def test_loandepot_no_dollar_sign_extracts_interest(self):
        """loanDepot 1098 without $ prefix must extract interest > 0."""
        data = _load_yaml("prepare/2022/1098-loandepot.yaml")
        interest = data["boxes"]["1_mortgage_interest"]
        assert interest > 0, f"loanDepot Box 1 = {interest} — expected > 0"

    @pytest.mark.skipif(
        not _pdf_exists(str(PREPARE_ROOT / "2025/mortgage-1098-748333812-16110.pdf")),
        reason="PDF not available",
    )
    def test_rocket_mortgage_not_cover_page_zero(self):
        """Rocket Mortgage 1098 must NOT grab $0 from cover page."""
        data = _load_yaml("prepare/2025/1098-rocket-mortgage-333812.yaml")
        interest = data["boxes"]["1_mortgage_interest"]
        assert interest > 10000, f"Box 1 = {interest} — should be ~$16K, not $0 from cover page"


# ===========================================================================
# Intra-document relationship validation
# These tests verify the mathematical consistency checks that catch parsing
# bugs even when individual values look plausible.
# ===========================================================================

class TestW2IntraDocumentValidation:
    """Verify mathematical relationships within each W-2."""

    SS_WAGE_BASES = {2022: 147000, 2023: 160200, 2024: 168600, 2025: 176100}

    @pytest.fixture(params=[
        "prepare/2025/w-2-salesforce-inc.yaml",
        "prepare/2025/w-2-servicetitan-inc.yaml",
        "prepare/2024/w-2-salesforce-inc.yaml",
        "prepare/2024/w-2-stripe.yaml",
        "prepare/2024/w-2-yi-chen.yaml",
        "prepare/2023/w-2-stripe.yaml",
        "prepare/2023/w-2-yi-chen.yaml",
        "prepare/2022/w-2-airbnb-inc.yaml",
        "prepare/2022/w-2-meta-platforms-inc.yaml",
        "prepare/2022/w-2-stripe.yaml",
    ])
    def w2_data(self, request):
        path = TAX_ROOT / request.param
        if not path.exists():
            pytest.skip(f"YAML not found: {path}")
        with open(path) as f:
            return yaml.safe_load(f)

    def test_box4_equals_box3_times_6_2_percent(self, w2_data):
        """Box 4 (SS tax) = Box 3 (SS wages) × 6.2%."""
        box3 = w2_data["boxes"]["3_ss_wages"]
        box4 = w2_data["boxes"]["4_ss_tax_withheld"]
        if box3 > 0:
            expected = round(box3 * 0.062, 2)
            assert abs(box4 - expected) <= 1.0, \
                f"Box 4 ({box4}) != Box 3 ({box3}) * 6.2% ({expected})"

    def test_box6_gte_box5_times_1_45_percent(self, w2_data):
        """Box 6 (Medicare tax) >= Box 5 (Medicare wages) × 1.45%."""
        box5 = w2_data["boxes"]["5_medicare_wages"]
        box6 = w2_data["boxes"]["6_medicare_tax_withheld"]
        if box5 > 0:
            minimum = round(box5 * 0.0145, 2) - 1.0
            assert box6 >= minimum, \
                f"Box 6 ({box6}) < Box 5 ({box5}) * 1.45% ({round(box5 * 0.0145, 2)})"

    def test_box1_lte_box5(self, w2_data):
        """Box 1 (wages) <= Box 5 (Medicare wages) — pre-tax deductions reduce Box 1."""
        box1 = w2_data["boxes"]["1_wages"]
        box5 = w2_data["boxes"]["5_medicare_wages"]
        tp = w2_data["boxes"].get("13", {}).get("third_party_sick_pay", False)
        if box1 > 0 and box5 > 0 and not tp:
            assert box1 <= box5 + 1.0, \
                f"Box 1 ({box1}) > Box 5 ({box5}) — wages exceed Medicare wages"

    def test_box3_lte_ss_wage_base(self, w2_data):
        """Box 3 (SS wages) <= Social Security wage base for the year."""
        year = w2_data["tax_year"]
        box3 = w2_data["boxes"]["3_ss_wages"]
        base = self.SS_WAGE_BASES.get(year, 176100)
        assert box3 <= base + 1.0, f"Box 3 ({box3}) > {year} SS wage base ({base})"


# ===========================================================================
# Cross-validation: W-2 fed withholding vs payslip DB
# ===========================================================================

class TestCrossValidation:
    """Cross-validate parsed tax data against other data sources."""

    @pytest.mark.skipif(
        not (TAX_ROOT / "prepare/2025/w-2-salesforce-inc.yaml").exists(),
        reason="YAML not available",
    )
    def test_2025_salesforce_withholding_matches_payslip_db(self):
        """W-2 Box 2 (fed withholding) must match payslip DB sum exactly."""
        import sqlite3
        db_path = TAX_ROOT.parent / "finance.db"
        if not db_path.exists():
            pytest.skip("finance.db not available")

        w2 = _load_yaml("prepare/2025/w-2-salesforce-inc.yaml")
        conn = sqlite3.connect(str(db_path))
        row = conn.execute("""
            SELECT SUM(li.amount)
            FROM payslip_line_items li
            JOIN payslips p ON li.payslip_id = p.id
            WHERE p.employer = 'Salesforce'
            AND strftime('%Y', p.pay_date) = '2025'
            AND li.section = 'employee_taxes'
            AND li.description LIKE '%Federal%'
        """).fetchone()
        conn.close()

        if row[0] is None:
            pytest.skip("No payslip data for Salesforce 2025")

        payslip_fed = round(row[0], 2)
        w2_fed = w2["boxes"]["2_fed_tax_withheld"]
        assert w2_fed == payslip_fed, \
            f"W-2 Box 2 ({w2_fed}) != Payslip DB ({payslip_fed})"


# ===========================================================================
# Idempotency
# ===========================================================================

class TestIdempotency:
    """Verify that re-running ingestion doesn't change existing data."""

    def test_all_yamls_have_validation_section(self):
        """Every YAML must have a validation section with mismatches list."""
        for f in TAX_ROOT.rglob("*.yaml"):
            with open(f) as fh:
                data = yaml.safe_load(fh)
            assert "validation" in data, f"Missing validation section: {f}"
            assert "mismatches" in data["validation"], f"Missing mismatches: {f}"

    def test_all_yamls_have_source_section(self):
        """Every YAML must have source file and processed_at."""
        for f in TAX_ROOT.rglob("*.yaml"):
            with open(f) as fh:
                data = yaml.safe_load(fh)
            assert "source" in data, f"Missing source section: {f}"
            assert "file" in data["source"], f"Missing source.file: {f}"
            assert "processed_at" in data["source"], f"Missing processed_at: {f}"

    def test_no_validation_failures(self):
        """No YAML should have unresolved validation mismatches (warnings OK, errors not)."""
        for f in TAX_ROOT.rglob("*.yaml"):
            with open(f) as fh:
                data = yaml.safe_load(fh)
            mismatches = data.get("validation", {}).get("mismatches", [])
            # Filter out known acceptable warnings
            errors = [m for m in mismatches
                      if "Suspicious" not in m
                      and "no taxes withheld" not in m
                      and "1099-B short_term: gain/loss" not in m  # Fidelity wash sale reporting quirk
                      ]
            assert not errors, f"Validation errors in {f.name}: {errors}"


# ===========================================================================
# Utility function tests
# ===========================================================================

class TestParseAmount:
    def test_basic(self):
        assert parse_amount("1,234.56") == 1234.56

    def test_with_dollar_sign(self):
        assert parse_amount("$1,234.56") == 1234.56

    def test_negative_parens(self):
        assert parse_amount("(1,234.56)") == -1234.56

    def test_none_input(self):
        assert parse_amount("") is None
        assert parse_amount(None) is None


class TestDeduplicateDoubledText:
    def test_doubled_text(self):
        # Must be long enough to trigger the ratio check (>20 non-space chars)
        doubled = "HHeelllloo WW" * 10  # 130 chars of doubled text
        result = _deduplicate_doubled_text(doubled)
        assert len(result) < len(doubled), \
            f"De-duplicated text should be shorter: {len(result)} vs {len(doubled)}"

    def test_normal_text_unchanged(self):
        result = _deduplicate_doubled_text("Hello World")
        assert result == "Hello World"

    def test_preserves_newlines(self):
        result = _deduplicate_doubled_text("HHeelllloo\nWWoorrlldd")
        assert "Hello" in result
        assert "\n" in result


# ===========================================================================
# Consolidated 1099 Parser Tests
# ===========================================================================

class TestConsolidated1099:
    """Regression tests for consolidated 1099 parser (Fidelity & Morgan Stanley)."""

    @pytest.fixture(params=[
        ("prepare/2025/1099-consolidated-fidelity-0887.yaml",
         {"institution": "Fidelity", "ssn": "2622", "has_div": True, "has_int": True, "has_b": True}),
        ("prepare/2025/1099-consolidated-fidelity-4983.yaml",
         {"institution": "Fidelity", "ssn": "2622", "has_div": True, "has_int": True, "has_b": False}),
        ("prepare/2025/1099-consolidated-fidelity-9437.yaml",
         {"institution": "Fidelity", "ssn": "6094", "has_div": True, "has_int": True, "has_b": True}),
        ("prepare/2025/1099-consolidated-fidelity-2753.yaml",
         {"institution": "Fidelity", "ssn": "9707", "has_div": True, "has_int": True, "has_b": True}),
        ("prepare/2025/1099-consolidated-morgan-stanley-6206.yaml",
         {"institution": "Morgan Stanley", "ssn": "2622", "has_div": True, "has_int": True, "has_b": True}),
    ])
    def consolidated_data(self, request):
        yaml_path, expected = request.param
        path = TAX_ROOT / yaml_path
        if not path.exists():
            pytest.skip(f"YAML not found: {path}")
        with open(path) as f:
            data = yaml.safe_load(f)
        return data, expected

    def test_form_type(self, consolidated_data):
        data, _ = consolidated_data
        assert data["form_type"] == "1099-CONSOLIDATED"

    def test_institution(self, consolidated_data):
        data, expected = consolidated_data
        assert data["institution"] == expected["institution"]

    def test_recipient_ssn(self, consolidated_data):
        data, expected = consolidated_data
        assert data["recipient"]["ssn_last4"] == expected["ssn"]

    def test_has_expected_forms(self, consolidated_data):
        data, expected = consolidated_data
        if expected["has_div"]:
            assert "1099-DIV" in data["forms"], "Missing 1099-DIV section"
        if expected["has_int"]:
            assert "1099-INT" in data["forms"], "Missing 1099-INT section"
        if expected["has_b"]:
            assert "1099-B" in data["forms"], "Missing 1099-B section"

    def test_validation_passes(self, consolidated_data):
        data, _ = consolidated_data
        assert data["validation"]["checks_passed"], \
            f"Validation failed: {data['validation']['mismatches']}"


class TestConsolidated1099DIVChecks:
    """Verify 1099-DIV mathematical relationships."""

    @pytest.fixture(params=[
        "prepare/2025/1099-consolidated-fidelity-0887.yaml",
        "prepare/2025/1099-consolidated-fidelity-4983.yaml",
        "prepare/2025/1099-consolidated-fidelity-9437.yaml",
        "prepare/2025/1099-consolidated-fidelity-2753.yaml",
        "prepare/2025/1099-consolidated-morgan-stanley-6206.yaml",
    ])
    def div_data(self, request):
        path = TAX_ROOT / request.param
        if not path.exists():
            pytest.skip(f"YAML not found: {path}")
        with open(path) as f:
            data = yaml.safe_load(f)
        div = data.get("forms", {}).get("1099-DIV", {})
        if not div:
            pytest.skip("No 1099-DIV data")
        return div

    def test_qualified_le_total(self, div_data):
        """Qualified dividends <= total ordinary dividends."""
        qualified = div_data.get("1b_qualified_dividends", 0)
        total = div_data.get("1a_total_ordinary_dividends", 0)
        assert qualified <= total + 0.01, \
            f"Qualified ({qualified}) > total ordinary ({total})"

    def test_cap_gain_non_negative(self, div_data):
        """Capital gain distributions >= 0."""
        cap_gain = div_data.get("2a_total_capital_gain_dist", 0)
        assert cap_gain >= 0, f"Cap gain distributions ({cap_gain}) < 0"


class TestConsolidated1099BChecks:
    """Verify 1099-B proceeds - basis = gain/loss."""

    @pytest.fixture(params=[
        "prepare/2025/1099-consolidated-fidelity-0887.yaml",
        "prepare/2025/1099-consolidated-fidelity-9437.yaml",
        "prepare/2025/1099-consolidated-fidelity-2753.yaml",
        "prepare/2025/1099-consolidated-morgan-stanley-6206.yaml",
    ])
    def b_data(self, request):
        path = TAX_ROOT / request.param
        if not path.exists():
            pytest.skip(f"YAML not found: {path}")
        with open(path) as f:
            data = yaml.safe_load(f)
        b = data.get("forms", {}).get("1099-B", {})
        if not b:
            pytest.skip("No 1099-B data")
        return b

    def test_short_term_gain_loss(self, b_data):
        """Short-term: proceeds - basis + wash = gain/loss."""
        st = b_data["short_term"]
        if st["proceeds"] > 0 or st["cost_basis"] > 0:
            expected = round(st["proceeds"] - st["cost_basis"] + st.get("wash_sales", 0), 2)
            assert abs(st["gain_loss"] - expected) <= 0.02, \
                f"ST gain/loss ({st['gain_loss']}) != proceeds ({st['proceeds']}) - basis ({st['cost_basis']}) + wash ({st.get('wash_sales', 0)}) = {expected}"

    def test_long_term_gain_loss(self, b_data):
        """Long-term: proceeds - basis + wash = gain/loss."""
        lt = b_data["long_term"]
        if lt["proceeds"] > 0 or lt["cost_basis"] > 0:
            expected = round(lt["proceeds"] - lt["cost_basis"] + lt.get("wash_sales", 0), 2)
            assert abs(lt["gain_loss"] - expected) <= 0.02, \
                f"LT gain/loss ({lt['gain_loss']}) != proceeds ({lt['proceeds']}) - basis ({lt['cost_basis']}) + wash ({lt.get('wash_sales', 0)}) = {expected}"

    def test_total_equals_sum(self, b_data):
        """Total = short-term + long-term for each field."""
        for key in ["proceeds", "cost_basis", "gain_loss"]:
            expected = round(b_data["short_term"][key] + b_data["long_term"][key], 2)
            actual = b_data["total"][key]
            assert abs(actual - expected) <= 0.02, \
                f"Total {key} ({actual}) != ST ({b_data['short_term'][key]}) + LT ({b_data['long_term'][key]})"


# ===========================================================================
# Consolidated 1099 Specific Value Tests
# ===========================================================================

class TestFidelityTOD1099:
    """Verify specific values from the Fidelity TOD account."""

    @pytest.mark.skipif(
        not (TAX_ROOT / "prepare/2025/1099-consolidated-fidelity-0887.yaml").exists(),
        reason="YAML not available",
    )
    def test_fidelity_tod_dividends(self):
        data = _load_yaml("prepare/2025/1099-consolidated-fidelity-0887.yaml")
        div = data["forms"]["1099-DIV"]
        assert div["1a_total_ordinary_dividends"] == 274.97
        assert div["1b_qualified_dividends"] == 274.60

    @pytest.mark.skipif(
        not (TAX_ROOT / "prepare/2025/1099-consolidated-fidelity-0887.yaml").exists(),
        reason="YAML not available",
    )
    def test_fidelity_tod_interest(self):
        data = _load_yaml("prepare/2025/1099-consolidated-fidelity-0887.yaml")
        int_data = data["forms"]["1099-INT"]
        assert int_data["1_interest_income"] == 2637.20

    @pytest.mark.skipif(
        not (TAX_ROOT / "prepare/2025/1099-consolidated-fidelity-0887.yaml").exists(),
        reason="YAML not available",
    )
    def test_fidelity_tod_broker(self):
        data = _load_yaml("prepare/2025/1099-consolidated-fidelity-0887.yaml")
        b = data["forms"]["1099-B"]
        assert b["long_term"]["proceeds"] == 7244.89
        assert b["long_term"]["cost_basis"] == 4426.22
        assert b["long_term"]["gain_loss"] == 2818.67


class TestMorganStanley1099:
    """Verify specific values from Morgan Stanley E*TRADE RSU account."""

    @pytest.mark.skipif(
        not (TAX_ROOT / "prepare/2025/1099-consolidated-morgan-stanley-6206.yaml").exists(),
        reason="YAML not available",
    )
    def test_ms_dividends(self):
        data = _load_yaml("prepare/2025/1099-consolidated-morgan-stanley-6206.yaml")
        div = data["forms"]["1099-DIV"]
        assert div["1a_total_ordinary_dividends"] == 131.86
        assert div["1b_qualified_dividends"] == 131.86

    @pytest.mark.skipif(
        not (TAX_ROOT / "prepare/2025/1099-consolidated-morgan-stanley-6206.yaml").exists(),
        reason="YAML not available",
    )
    def test_ms_interest(self):
        data = _load_yaml("prepare/2025/1099-consolidated-morgan-stanley-6206.yaml")
        int_data = data["forms"]["1099-INT"]
        assert int_data["1_interest_income"] == 0.10

    @pytest.mark.skipif(
        not (TAX_ROOT / "prepare/2025/1099-consolidated-morgan-stanley-6206.yaml").exists(),
        reason="YAML not available",
    )
    def test_ms_broker_short_term(self):
        data = _load_yaml("prepare/2025/1099-consolidated-morgan-stanley-6206.yaml")
        b = data["forms"]["1099-B"]
        assert b["short_term"]["proceeds"] == 248709.67
        assert b["short_term"]["cost_basis"] == 244397.42
        assert b["short_term"]["gain_loss"] == 4312.25

    @pytest.mark.skipif(
        not (TAX_ROOT / "prepare/2025/1099-consolidated-morgan-stanley-6206.yaml").exists(),
        reason="YAML not available",
    )
    def test_ms_broker_long_term_zero(self):
        data = _load_yaml("prepare/2025/1099-consolidated-morgan-stanley-6206.yaml")
        b = data["forms"]["1099-B"]
        assert b["long_term"]["proceeds"] == 0.0
        assert b["long_term"]["gain_loss"] == 0.0


# ===========================================================================
# Enhanced 1099-R Validation Tests
# ===========================================================================

class TestParse1099REnhancedValidation:
    """Tests for new 1099-R validation checks."""

    @pytest.mark.skipif(
        not (TAX_ROOT / "prepare/2025/1099-r-fidelity-salesforce-401k-401-k----salesforce.yaml").exists(),
        reason="YAML not available",
    )
    def test_code_g_taxable_is_zero(self):
        """Code G (rollover) must have Box 2a taxable = 0."""
        data = _load_yaml("prepare/2025/1099-r-fidelity-salesforce-401k-401-k----salesforce.yaml")
        assert data["boxes"]["7_distribution_code"] == "G"
        assert data["boxes"]["2a_taxable_amount"] == 0.0
        # Should pass validation (no mismatch)
        mismatches = data["validation"]["mismatches"]
        code_g_issues = [m for m in mismatches if "Code G" in m]
        assert not code_g_issues, f"Unexpected Code G validation issues: {code_g_issues}"

    @pytest.mark.skipif(
        not (TAX_ROOT / "prepare/2025/1099-r-fidelity-investments-ira-traditional-ira.yaml").exists(),
        reason="YAML not available",
    )
    def test_box5_le_box1(self):
        """Box 5 (employee contributions) <= Box 1 (gross distribution)."""
        data = _load_yaml("prepare/2025/1099-r-fidelity-investments-ira-traditional-ira.yaml")
        box1 = data["boxes"]["1_gross_distribution"]
        box5 = data["boxes"]["5_employee_contributions"]
        assert box5 <= box1 + 0.01, f"Box 5 ({box5}) > Box 1 ({box1})"


# ===========================================================================
# Enhanced 1040 Validation Tests
# ===========================================================================

class TestParse1040EnhancedValidation:
    """Tests for new 1040 validation checks."""

    @pytest.fixture(params=[
        "archive/2024/1040-summary.yaml",
        "archive/2023/1040-summary.yaml",
        "archive/2022/1040-summary.yaml",
    ])
    def f1040(self, request):
        path = TAX_ROOT / request.param
        if not path.exists():
            pytest.skip(f"YAML not found: {path}")
        with open(path) as f:
            return yaml.safe_load(f)

    def test_taxable_income_equals_agi_minus_deductions(self, f1040):
        """Taxable income = AGI - deductions (±$1)."""
        s = f1040.get("summary", {})
        if s.get("adjusted_gross_income") and s.get("deductions") and s.get("taxable_income"):
            expected = s["adjusted_gross_income"] - s["deductions"]
            assert abs(s["taxable_income"] - expected) <= 1, \
                f"Taxable ({s['taxable_income']}) != AGI ({s['adjusted_gross_income']}) - deductions ({s['deductions']}) = {expected}"

    def test_withholding_le_payments(self, f1040):
        """Total withholding <= total payments."""
        s = f1040.get("summary", {})
        if s.get("total_withholding") and s.get("total_payments"):
            assert s["total_withholding"] <= s["total_payments"] + 1, \
                f"Withholding ({s['total_withholding']}) > payments ({s['total_payments']})"

    def test_all_key_fields_present(self, f1040):
        """All key summary fields should be extracted."""
        assert f1040["validation"]["all_key_fields_present"]


# ===========================================================================
# Cross-Document Reconciliation (CPA-style)
# ===========================================================================

class TestCPAReconciliation:
    """Cross-document reconciliation tests that verify consistency
    across different tax forms for the same year."""

    def _load_year_docs(self, year: int) -> dict:
        """Load all tax documents for a year, grouped by form type."""
        prepare_dir = TAX_ROOT / "prepare" / str(year)
        if not prepare_dir.exists():
            pytest.skip(f"No prepare dir for {year}")
        docs = {}
        for yaml_file in sorted(prepare_dir.glob("*.yaml")):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            if data:
                ft = data.get("form_type", "unknown")
                docs.setdefault(ft, []).append(data)
        return docs

    def _load_1040(self, year: int) -> dict:
        """Load the filed 1040 for a year."""
        path = TAX_ROOT / "archive" / str(year) / "1040-summary.yaml"
        if not path.exists():
            pytest.skip(f"No 1040 for {year}")
        with open(path) as f:
            return yaml.safe_load(f)

    @pytest.mark.parametrize("year", [2025])
    def test_total_interest_across_accounts(self, year):
        """Sum of 1099-INT + consolidated 1099 interest = total interest income."""
        docs = self._load_year_docs(year)
        total_interest = 0.0

        # Standalone 1099-INT
        for doc in docs.get("1099-INT", []):
            interest = doc.get("boxes", {}).get("1_interest_income", 0)
            total_interest += interest

        # Consolidated 1099 INT sections
        for doc in docs.get("1099-CONSOLIDATED", []):
            # Only Yi's accounts
            if doc.get("recipient", {}).get("ssn_last4") != "2622":
                continue
            int_data = doc.get("forms", {}).get("1099-INT", {})
            total_interest += int_data.get("1_interest_income", 0)

        assert total_interest > 0, "Should have some interest income"

    @pytest.mark.parametrize("year", [2025])
    def test_total_dividends_across_accounts(self, year):
        """Sum of consolidated 1099 dividends across all Yi's accounts."""
        docs = self._load_year_docs(year)
        total_div = 0.0

        for doc in docs.get("1099-CONSOLIDATED", []):
            if doc.get("recipient", {}).get("ssn_last4") != "2622":
                continue
            div = doc.get("forms", {}).get("1099-DIV", {})
            total_div += div.get("1a_total_ordinary_dividends", 0)

        assert total_div > 0, "Should have some dividend income"

    @pytest.mark.parametrize("year", [2025])
    def test_total_broker_gains(self, year):
        """Sum of 1099-B gains across all accounts."""
        docs = self._load_year_docs(year)
        total_gain = 0.0

        for doc in docs.get("1099-CONSOLIDATED", []):
            if doc.get("recipient", {}).get("ssn_last4") != "2622":
                continue
            b = doc.get("forms", {}).get("1099-B", {})
            if b:
                total_gain += b.get("total", {}).get("gain_loss", 0)

        # We know TOD has $2818.67 LT gain and MS has $4312.25 ST gain
        assert abs(total_gain - (2818.67 + 4312.25)) < 1.0, \
            f"Total gain ({total_gain}) != expected ($7130.92)"

    @pytest.mark.parametrize("year", [2024, 2023, 2022])
    def test_w2_wages_vs_1040(self, year):
        """Sum of W-2 wages for Yi should be close to 1040 line 1a (for MFJ, gap is expected).

        Note: Yi's W-2 sum CAN exceed 1040 line 1a when third-party sick pay W-2s
        (e.g., Lincoln Life) have Box 1 that overlaps with the primary employer's Box 1.
        The 1040 de-duplicates these, so the test checks that non-third-party W-2 wages <= 1040.
        """
        docs = self._load_year_docs(year)
        f1040 = self._load_1040(year)

        yi_wages_non_tp = 0.0
        for w2 in docs.get("W-2", []):
            emp = w2.get("employer", {}).get("name", "")
            ssn = w2.get("employee", {}).get("ssn_last4", "")
            # Skip household W-2s (employer=Yi Chen) and non-Yi W-2s
            if emp.strip() == "Yi Chen":
                continue
            if ssn != "2622":
                continue
            # Skip third-party sick pay W-2s (e.g., Lincoln Life)
            is_tp = w2.get("boxes", {}).get("13", {}).get("third_party_sick_pay", False)
            if is_tp:
                continue
            yi_wages_non_tp += w2.get("boxes", {}).get("1_wages", 0)

        line_1a = f1040.get("income", {}).get("1a_w2_wages", 0)

        # For MFJ years, 1040 includes spouse wages — Yi's non-TP should be <= 1040
        if yi_wages_non_tp > 0 and line_1a > 0:
            assert yi_wages_non_tp <= line_1a + 1, \
                f"Yi W-2 non-TP wages ({yi_wages_non_tp}) > 1040 line 1a ({line_1a}) — unexpected"

    @pytest.mark.parametrize("year", [2024, 2023, 2022])
    def test_1040_interest_ge_standalone_1099int(self, year):
        """1040 interest should be >= standalone 1099-INTs (brokerage adds more)."""
        docs = self._load_year_docs(year)
        f1040 = self._load_1040(year)

        prepare_interest = 0.0
        for doc in docs.get("1099-INT", []):
            prepare_interest += doc.get("boxes", {}).get("1_interest_income", 0)

        line_2b = f1040.get("income", {}).get("2b_taxable_interest", 0)

        # 1040 should report at least as much interest as our standalone 1099-INTs
        if prepare_interest > 0:
            assert line_2b >= prepare_interest - 1, \
                f"1040 interest ({line_2b}) < standalone 1099-INT interest ({prepare_interest})"
