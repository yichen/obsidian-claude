

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
        """Extract dollar amount for a 1040 line, handling multiple CPA formats."""
        lines_list = text.split("\n")
        for i, line in enumerate(lines_list):
            if not re.search(rf"\b{re.escape(line_prefix)}\b", line):
                continue
            if not any(kw.lower() in line.lower() for kw in keywords):
                continue
            for j in range(i, min(i + 3, len(lines_list))):
                amounts = re.findall(r"-?[\d,]+\.\d{0,2}", lines_list[j])
                if amounts:
                    val_str = amounts[-1]
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
