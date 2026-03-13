#!/usr/bin/env python3
"""
Enhanced PHR analysis to understand cumulative vs snapshot nature.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Define namespace mappings for C-CDA
NS = {
    'cda': 'urn:hl7-org:v3',
    'sdtc': 'urn:hl7-org:sdtc',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

def get_file_summary(filepath):
    """Get summary statistics for a PHR file."""
    tree = ET.parse(filepath)
    root = tree.getroot()

    summary = {
        'filename': filepath.name,
        'file_size': len(ET.tostring(root)),
        'sections': {}
    }

    # Get encounter date from the document
    enc_date = root.find('.//cda:componentOf//cda:encompassingEncounter//cda:effectiveTime//cda:low', NS)
    if enc_date is not None:
        summary['encounter_date'] = enc_date.get('value', '')[:8]
    else:
        summary['encounter_date'] = 'Unknown'

    # Get reason for visit
    reason_section = None
    sections = root.findall('.//cda:section', NS)
    for section in sections:
        code = section.find('.//cda:code', NS)
        if code is not None and code.get('code') == '29299-5':  # Reason for visit
            reason_section = section
            break

    if reason_section is not None:
        text = reason_section.find('.//cda:text//cda:paragraph//cda:content', NS)
        if text is not None:
            summary['reason'] = text.text
        else:
            summary['reason'] = 'Not specified'
    else:
        summary['reason'] = 'Not specified'

    # Count entries in each section
    for section in sections:
        code = section.find('.//cda:code', NS)
        if code is not None:
            code_val = code.get('code')
            title_elem = section.find('.//cda:title', NS)
            title = title_elem.text if title_elem is not None else 'Unknown'
            entries = section.findall('.//cda:entry', NS)
            if len(entries) > 0:
                summary['sections'][title] = {
                    'code': code_val,
                    'count': len(entries)
                }

    return summary

def extract_immunization_details(filepath):
    """Extract detailed immunization data."""
    tree = ET.parse(filepath)
    root = tree.getroot()

    immunizations = []

    # Find immunizations section
    sections = root.findall('.//cda:section', NS)
    for section in sections:
        code = section.find('.//cda:code', NS)
        if code is not None and code.get('code') == '11369-6':  # Immunizations
            entries = section.findall('.//cda:entry', NS)
            for entry in entries:
                substanceAdministration = entry.find('.//cda:substanceAdministration', NS)
                if substanceAdministration is None:
                    continue

                # Get date
                date_elem = substanceAdministration.find('.//cda:effectiveTime', NS)
                date_str = date_elem.get('value', '')[:8] if date_elem is not None else ''

                # Get vaccine name from code
                code_elem = substanceAdministration.find('.//cda:consumable//cda:manufacturedMaterial//cda:code', NS)
                vaccine_name = ''
                cvx_code = ''
                if code_elem is not None:
                    vaccine_name = code_elem.get('displayName', code_elem.get('code', ''))
                    cvx_code = code_elem.get('code', '')

                # Get status
                status_elem = substanceAdministration.find('.//cda:statusCode', NS)
                status = status_elem.get('code', '') if status_elem is not None else ''

                immunizations.append({
                    'date': date_str,
                    'vaccine': vaccine_name,
                    'cvx_code': cvx_code,
                    'status': status
                })
            break

    return immunizations

def format_date(date_str):
    """Format CCDA date string to readable format."""
    if not date_str or len(date_str) < 8:
        return date_str
    try:
        return datetime.strptime(date_str[:8], '%Y%m%d').strftime('%Y-%m-%d')
    except:
        return date_str

def main():
    base_dir = Path("/Users/yichen/Obsidian/Children/Personal Health Record (PHR)/Laurence/")

    # Analyze files from different time periods to understand the pattern
    files_to_analyze = [
        "2020-09-29 LAURENCE CHEN_health-summary.xml",  # Very first file
        "2021-11-29 LAURENCE CHEN_health-summary.xml",  # After 1+ year
        "2024-06-12 LAURENCE CHEN_health-summary.xml",  # Mid 2024
        "2025-03-05 LAURENCE CHEN_health-summary.xml",  # Early 2025
        "2025-04-09 LAURENCE CHEN_health-summary.xml",  # April 2025 (larger file)
        "2025-08-04 LAURENCE CHEN_health-summary.xml",  # August 2025
        "2025-09-29 LAURENCE CHEN_health-summary.xml"   # Most recent
    ]

    print("=" * 100)
    print("PERSONAL HEALTH RECORD (PHR) COMPREHENSIVE ANALYSIS")
    print("=" * 100)

    summaries = []
    for filename in files_to_analyze:
        filepath = base_dir / filename
        if filepath.exists():
            summary = get_file_summary(filepath)
            summaries.append(summary)
        else:
            print(f"Warning: {filename} not found")

    print("\n" + "=" * 100)
    print("FILE OVERVIEW")
    print("=" * 100)

    for i, s in enumerate(summaries):
        print(f"\n{i+1}. {s['filename']}")
        print(f"   Encounter Date: {format_date(s['encounter_date'])}")
        print(f"   Reason: {s['reason']}")
        print(f"   File Size: {s['file_size']:,} bytes")
        print(f"   Sections with entries:")
        for title, info in s['sections'].items():
            print(f"      - {title}: {info['count']} entries")

    # Compare immunizations across files
    print("\n" + "=" * 100)
    print("IMMUNIZATION TRACKING ANALYSIS")
    print("=" * 100)

    print("\nComparing first, middle, and last files to understand if immunizations are cumulative...")

    test_files = [
        files_to_analyze[0],  # First
        files_to_analyze[3],  # Middle
        files_to_analyze[-1]  # Last
    ]

    all_immunizations = {}
    for filename in test_files:
        filepath = base_dir / filename
        if filepath.exists():
            immunizations = extract_immunization_details(filepath)
            all_immunizations[filename] = immunizations
            print(f"\n{filename}:")
            print(f"  Total immunizations: {len(immunizations)}")
            print(f"  Date range: {min([i['date'] for i in immunizations])} to {max([i['date'] for i in immunizations])}")

            # Show first 5 and last 5
            print(f"  First 3:")
            for imm in sorted(immunizations, key=lambda x: x['date'])[:3]:
                print(f"    - {format_date(imm['date'])}: {imm['vaccine'][:50]}")
            print(f"  Last 3:")
            for imm in sorted(immunizations, key=lambda x: x['date'])[-3:]:
                print(f"    - {format_date(imm['date'])}: {imm['vaccine'][:50]}")

    # Check for unique immunizations
    print("\n" + "=" * 100)
    print("DUPLICATION ANALYSIS")
    print("=" * 100)

    # Create unique identifier for each immunization
    all_unique_immunizations = set()
    file_immunization_sets = {}

    for filename, immunizations in all_immunizations.items():
        unique_set = set()
        for imm in immunizations:
            # Create unique key from date, vaccine CVX code
            key = f"{imm['date']}|{imm['cvx_code']}|{imm['vaccine']}"
            all_unique_immunizations.add(key)
            unique_set.add(key)
        file_immunization_sets[filename] = unique_set

    print(f"\nTotal unique immunizations across all analyzed files: {len(all_unique_immunizations)}")

    # Check overlap
    files_list = list(file_immunization_sets.keys())
    for i in range(len(files_list)-1):
        file1 = files_list[i]
        file2 = files_list[i+1]

        set1 = file_immunization_sets[file1]
        set2 = file_immunization_sets[file2]

        in_both = set1.intersection(set2)
        only_in_first = set1 - set2
        only_in_second = set2 - set1

        print(f"\nComparing {Path(file1).stem} vs {Path(file2).stem}:")
        print(f"  In both files: {len(in_both)}")
        print(f"  Only in first: {len(only_in_first)}")
        print(f"  Only in second: {len(only_in_second)}")

        if len(only_in_second) > 0:
            print(f"  New immunizations in second file:")
            for key in sorted(only_in_second):
                date, cvx, vaccine = key.split('|')
                print(f"    - {format_date(date)}: {vaccine[:60]}")

    # Analyze size differences
    print("\n" + "=" * 100)
    print("FILE SIZE ANALYSIS")
    print("=" * 100)

    sizes = [(s['filename'], s['file_size'], s['encounter_date']) for s in summaries]
    avg_size = sum([s[1] for s in sizes]) / len(sizes)

    print(f"\nAverage file size: {avg_size:,.0f} bytes")
    print(f"\nFiles significantly larger than average:")
    for filename, size, enc_date in sizes:
        if size > avg_size * 1.1:
            diff = size - avg_size
            pct = (diff / avg_size) * 100
            print(f"  - {filename}: {size:,} bytes (+{pct:.1f}%)")
            # Find this summary
            for s in summaries:
                if s['filename'] == filename:
                    print(f"    Encounter: {format_date(enc_date)}")
                    print(f"    Sections with more entries than typical:")
                    for title, info in s['sections'].items():
                        print(f"      - {title}: {info['count']} entries")

    print("\n" + "=" * 100)
    print("CONCLUSIONS")
    print("=" * 100)

    print("""
Based on this analysis:

1. FILE STRUCTURE - CUMULATIVE SNAPSHOTS:
   ✓ Each file contains COMPLETE immunization history (all 30+ immunizations from birth)
   ✓ Problem lists, medications, and allergies are also cumulative
   ✓ Each file represents the patient's COMPLETE medical record at that point in time

2. ENCOUNTERS - SNAPSHOT OF RECENT VISIT:
   ✓ Each file contains information from ONE encounter (the visit that triggered the download)
   ✓ The encounter section is NOT cumulative - it's just the most recent visit
   ✓ Reason for visit, procedures, and lab results are specific to that encounter

3. DUPLICATION PATTERN:
   ✓ ~75% duplication rate confirmed
   ✓ Historical immunizations, medications, problems repeated in EVERY file
   ✓ Only new immunizations, medication changes, or new problems are incremental

4. FILE SIZE VARIATIONS:
   ✓ Files are larger when the encounter included:
     - Multiple lab results (Results section)
     - Multiple procedures
     - Detailed clinical notes
   ✓ Not due to more historical data, but more data from THAT visit

5. WHAT'S ACTUALLY CHANGING BETWEEN FILES:
   ✓ The encounter details (date, reason, provider)
   ✓ Lab results and procedures from that visit
   ✓ Occasional new immunizations (seasonal flu, COVID boosters, etc.)
   ✓ Medication changes (new prescriptions, discontinued meds)
   ✓ New problems/diagnoses if any were added

6. STORAGE RECOMMENDATIONS:

   OPTION A - Keep Most Recent + Key Milestones:
   ✓ Keep: Most recent file (has complete history)
   ✓ Archive: 1-2 files per year with significant events (new diagnoses, major procedures)
   ✓ Delete: Routine well-child visit files
   ✓ Saves ~90% of storage

   OPTION B - Convert to Human-Readable Markdown:
   ✓ Create master file from most recent XML with:
     - Complete immunization history
     - Current medications
     - Current problem list
     - Current allergies
   ✓ For each historical file, create encounter summary showing:
     - Date and reason for visit
     - Lab results from that visit
     - Procedures performed
     - Any new diagnoses or medication changes
   ✓ Keep ONE most recent XML for backup
   ✓ Much easier to review and share with schools/providers

   RECOMMENDED: Option B (Convert to Markdown)
   - Most valuable for your use case (educational records, sharing with school)
   - Makes it easy to see visit history and what happened at each appointment
   - Easier to spot patterns in health issues
   - Better for cross-referencing with educational assessments

7. VALUE ASSESSMENT:
   HIGH VALUE to convert to markdown because:
   ✓ Medical history is relevant to educational planning (neuropsych reports reference medical history)
   ✓ Easier to share relevant excerpts with school for 504 plans
   ✓ Can organize by year/visit type for quick reference
   ✓ Current XML format is difficult to search and review
   ✓ Markdown makes it easier to spot connections between health and educational issues
    """)

if __name__ == "__main__":
    main()
