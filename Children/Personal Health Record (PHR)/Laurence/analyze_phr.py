#!/usr/bin/env python3
"""
Analyze C-CDA XML PHR files to determine data duplication and incremental changes.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json

# Define namespace mappings for C-CDA
NS = {
    'cda': 'urn:hl7-org:v3',
    'sdtc': 'urn:hl7-org:sdtc',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

def parse_xml_file(filepath):
    """Parse a C-CDA XML file and extract key sections."""
    tree = ET.parse(filepath)
    root = tree.getroot()

    data = {
        'filename': filepath.name,
        'encounters': [],
        'immunizations': [],
        'medications': [],
        'problems': [],
        'allergies': [],
        'vitals': []
    }

    # Find all sections in the document
    sections = root.findall('.//cda:section', NS)

    for section in sections:
        # Get section code to identify type
        code = section.find('.//cda:code', NS)
        if code is None:
            continue

        code_val = code.get('code')

        # Encounters section (46240-8)
        if code_val == '46240-8':
            entries = section.findall('.//cda:entry', NS)
            for entry in entries:
                enc_data = extract_encounter(entry)
                if enc_data:
                    data['encounters'].append(enc_data)

        # Immunizations section (11369-6)
        elif code_val == '11369-6':
            entries = section.findall('.//cda:entry', NS)
            for entry in entries:
                imm_data = extract_immunization(entry)
                if imm_data:
                    data['immunizations'].append(imm_data)

        # Medications section (10160-0)
        elif code_val == '10160-0':
            entries = section.findall('.//cda:entry', NS)
            for entry in entries:
                med_data = extract_medication(entry)
                if med_data:
                    data['medications'].append(med_data)

        # Problem list section (11450-4)
        elif code_val == '11450-4':
            entries = section.findall('.//cda:entry', NS)
            for entry in entries:
                prob_data = extract_problem(entry)
                if prob_data:
                    data['problems'].append(prob_data)

        # Allergies section (48765-2)
        elif code_val == '48765-2':
            entries = section.findall('.//cda:entry', NS)
            for entry in entries:
                allergy_data = extract_allergy(entry)
                if allergy_data:
                    data['allergies'].append(allergy_data)

        # Vital signs section (8716-3)
        elif code_val == '8716-3':
            entries = section.findall('.//cda:entry', NS)
            for entry in entries:
                vital_data = extract_vital(entry)
                if vital_data:
                    data['vitals'].append(vital_data)

    return data

def extract_encounter(entry):
    """Extract encounter information."""
    encounter = entry.find('.//cda:encounter', NS)
    if encounter is None:
        return None

    # Get encounter date
    date_elem = encounter.find('.//cda:effectiveTime', NS)
    date_str = ''
    if date_elem is not None:
        low = date_elem.find('cda:low', NS)
        if low is not None:
            date_str = low.get('value', '')

    # Get encounter type/description
    code = encounter.find('.//cda:code', NS)
    desc = ''
    if code is not None:
        desc = code.get('displayName', code.get('code', ''))

    # Get encounter ID
    id_elem = encounter.find('.//cda:id', NS)
    enc_id = ''
    if id_elem is not None:
        enc_id = id_elem.get('extension', '')

    return {
        'id': enc_id,
        'date': date_str,
        'description': desc
    }

def extract_immunization(entry):
    """Extract immunization information."""
    substanceAdministration = entry.find('.//cda:substanceAdministration', NS)
    if substanceAdministration is None:
        return None

    # Get immunization date
    date_elem = substanceAdministration.find('.//cda:effectiveTime', NS)
    date_str = date_elem.get('value', '') if date_elem is not None else ''

    # Get vaccine name
    code = substanceAdministration.find('.//cda:consumable//cda:code', NS)
    vaccine_name = ''
    if code is not None:
        vaccine_name = code.get('displayName', code.get('code', ''))

    # Get ID
    id_elem = substanceAdministration.find('.//cda:id', NS)
    imm_id = ''
    if id_elem is not None:
        imm_id = id_elem.get('extension', '')

    return {
        'id': imm_id,
        'date': date_str,
        'vaccine': vaccine_name
    }

def extract_medication(entry):
    """Extract medication information."""
    substanceAdministration = entry.find('.//cda:substanceAdministration', NS)
    if substanceAdministration is None:
        return None

    # Get medication name
    code = substanceAdministration.find('.//cda:consumable//cda:code', NS)
    med_name = ''
    if code is not None:
        med_name = code.get('displayName', code.get('code', ''))

    # Get date range
    date_elem = substanceAdministration.find('.//cda:effectiveTime[@xsi:type="IVL_TS"]', NS)
    if date_elem is None:
        date_elem = substanceAdministration.find('.//cda:effectiveTime', NS)

    date_str = ''
    if date_elem is not None:
        low = date_elem.find('cda:low', NS)
        high = date_elem.find('cda:high', NS)
        if low is not None:
            date_str = low.get('value', '')
        if high is not None and high.get('value'):
            date_str += ' to ' + high.get('value', '')

    # Get status
    status_elem = substanceAdministration.find('.//cda:statusCode', NS)
    status = status_elem.get('code', '') if status_elem is not None else ''

    return {
        'medication': med_name,
        'date_range': date_str,
        'status': status
    }

def extract_problem(entry):
    """Extract problem/diagnosis information."""
    observation = entry.find('.//cda:observation', NS)
    if observation is None:
        return None

    # Get problem name
    value = observation.find('.//cda:value', NS)
    problem_name = ''
    if value is not None:
        problem_name = value.get('displayName', value.get('code', ''))

    # Get date
    date_elem = observation.find('.//cda:effectiveTime//cda:low', NS)
    date_str = date_elem.get('value', '') if date_elem is not None else ''

    # Get status
    status_elem = observation.find('.//cda:statusCode', NS)
    status = status_elem.get('code', '') if status_elem is not None else ''

    return {
        'problem': problem_name,
        'date': date_str,
        'status': status
    }

def extract_allergy(entry):
    """Extract allergy information."""
    observation = entry.find('.//cda:observation', NS)
    if observation is None:
        return None

    # Get allergen
    participant = observation.find('.//cda:participant//cda:code', NS)
    allergen = ''
    if participant is not None:
        allergen = participant.get('displayName', participant.get('code', ''))

    # Get reaction
    value = observation.find('.//cda:value', NS)
    reaction = ''
    if value is not None:
        reaction = value.get('displayName', value.get('code', ''))

    return {
        'allergen': allergen,
        'reaction': reaction
    }

def extract_vital(entry):
    """Extract vital sign information."""
    organizer = entry.find('.//cda:organizer', NS)
    if organizer is None:
        return None

    # Get date
    date_elem = organizer.find('.//cda:effectiveTime', NS)
    date_str = date_elem.get('value', '') if date_elem is not None else ''

    # Get all vital observations
    observations = organizer.findall('.//cda:observation', NS)
    vitals = {'date': date_str}

    for obs in observations:
        code = obs.find('.//cda:code', NS)
        value = obs.find('.//cda:value', NS)

        if code is not None and value is not None:
            vital_name = code.get('displayName', code.get('code', ''))
            vital_value = value.get('value', '')
            vital_unit = value.get('unit', '')
            vitals[vital_name] = f"{vital_value} {vital_unit}".strip()

    return vitals

def format_date(date_str):
    """Format CCDA date string to readable format."""
    if not date_str or len(date_str) < 8:
        return date_str
    try:
        return datetime.strptime(date_str[:8], '%Y%m%d').strftime('%Y-%m-%d')
    except:
        return date_str

def compare_files(files_data):
    """Compare multiple PHR files to identify duplicates and incremental changes."""

    print("=" * 80)
    print("PHR FILE COMPARISON ANALYSIS")
    print("=" * 80)

    # Sort files by date
    files_data_sorted = sorted(files_data, key=lambda x: x['filename'])

    print(f"\nAnalyzing {len(files_data_sorted)} files:")
    for i, data in enumerate(files_data_sorted):
        print(f"  {i+1}. {data['filename']}")

    print("\n" + "=" * 80)
    print("SECTION SUMMARY")
    print("=" * 80)

    # Track counts per file
    for i, data in enumerate(files_data_sorted):
        print(f"\n{i+1}. {data['filename']}:")
        print(f"   Encounters:    {len(data['encounters'])}")
        print(f"   Immunizations: {len(data['immunizations'])}")
        print(f"   Medications:   {len(data['medications'])}")
        print(f"   Problems:      {len(data['problems'])}")
        print(f"   Allergies:     {len(data['allergies'])}")
        print(f"   Vital Signs:   {len(data['vitals'])}")

    # Detailed comparison for each section
    for section in ['encounters', 'immunizations', 'medications', 'problems', 'allergies']:
        print("\n" + "=" * 80)
        print(f"{section.upper()} ANALYSIS")
        print("=" * 80)

        # Create unique identifiers for each item
        all_items = {}
        for i, data in enumerate(files_data_sorted):
            file_num = i + 1
            for item in data[section]:
                item_key = json.dumps(item, sort_keys=True)
                if item_key not in all_items:
                    all_items[item_key] = {'item': item, 'files': []}
                all_items[item_key]['files'].append(file_num)

        # Categorize items
        in_all_files = []
        incremental = defaultdict(list)

        for item_key, item_info in all_items.items():
            files = item_info['files']
            if len(files) == len(files_data_sorted):
                in_all_files.append(item_info['item'])
            else:
                first_appearance = min(files)
                incremental[first_appearance].append(item_info['item'])

        print(f"\nTotal unique {section}: {len(all_items)}")
        print(f"Present in ALL files (duplicated): {len(in_all_files)}")

        for file_num in range(1, len(files_data_sorted) + 1):
            new_count = len(incremental.get(file_num, []))
            if new_count > 0:
                print(f"New in file {file_num} ({files_data_sorted[file_num-1]['filename']}): {new_count}")

        # Show details for incremental items
        if section in ['encounters', 'immunizations']:
            for file_num in range(1, len(files_data_sorted) + 1):
                new_items = incremental.get(file_num, [])
                if new_items:
                    print(f"\n  New {section} in file {file_num}:")
                    for item in new_items[:5]:  # Show first 5
                        if section == 'encounters':
                            print(f"    - {format_date(item['date'])}: {item['description']}")
                        elif section == 'immunizations':
                            print(f"    - {format_date(item['date'])}: {item['vaccine']}")
                    if len(new_items) > 5:
                        print(f"    ... and {len(new_items) - 5} more")

    # Calculate duplication statistics
    print("\n" + "=" * 80)
    print("DUPLICATION STATISTICS")
    print("=" * 80)

    total_items = 0
    duplicate_items = 0

    for section in ['encounters', 'immunizations', 'medications', 'problems', 'allergies']:
        all_items_set = {}
        for i, data in enumerate(files_data_sorted):
            for item in data[section]:
                item_key = json.dumps(item, sort_keys=True)
                if item_key not in all_items_set:
                    all_items_set[item_key] = 0
                all_items_set[item_key] += 1

        section_total = sum(all_items_set.values())
        section_unique = len(all_items_set)
        section_duplicate = section_total - section_unique

        total_items += section_total
        duplicate_items += section_duplicate

        if section_total > 0:
            dup_pct = (section_duplicate / section_total) * 100
            print(f"\n{section.capitalize()}:")
            print(f"  Total items across all files: {section_total}")
            print(f"  Unique items: {section_unique}")
            print(f"  Duplicate instances: {section_duplicate}")
            print(f"  Duplication rate: {dup_pct:.1f}%")

    if total_items > 0:
        overall_dup_pct = (duplicate_items / total_items) * 100
        print(f"\nOVERALL DUPLICATION RATE: {overall_dup_pct:.1f}%")
        print(f"Total items: {total_items}, Unique: {total_items - duplicate_items}, Duplicates: {duplicate_items}")

def main():
    # Base directory
    base_dir = Path("/Users/yichen/Obsidian/Children/Personal Health Record (PHR)/Laurence/")

    # Select 4 files from 2025 at different time points
    files_to_analyze = [
        "2025-03-05 LAURENCE CHEN_health-summary.xml",
        "2025-04-09 LAURENCE CHEN_health-summary.xml",  # This one is notably larger
        "2025-08-04 LAURENCE CHEN_health-summary.xml",
        "2025-09-29 LAURENCE CHEN_health-summary.xml"
    ]

    files_data = []
    for filename in files_to_analyze:
        filepath = base_dir / filename
        if filepath.exists():
            print(f"Parsing {filename}...")
            data = parse_xml_file(filepath)
            files_data.append(data)
        else:
            print(f"Warning: {filename} not found")

    if len(files_data) < 2:
        print("Error: Need at least 2 files to compare")
        return

    compare_files(files_data)

    print("\n" + "=" * 80)
    print("CONCLUSIONS & RECOMMENDATIONS")
    print("=" * 80)
    print("""
1. FILE STRUCTURE:
   These appear to be CUMULATIVE SNAPSHOTS - each file contains the complete
   health record history up to that point in time.

2. DUPLICATION PATTERN:
   - Historical data (old encounters, immunizations, etc.) is repeated in every file
   - Each new file adds incremental new data (recent visits, new immunizations)
   - The bulk of each file is duplicated from previous files

3. NEW DATA IN EACH FILE:
   - New encounters (doctor visits, ER visits, etc.) since last download
   - New immunizations (if any were administered)
   - Updated medication lists (changes in prescriptions)
   - New vital signs from recent visits

4. STORAGE RECOMMENDATIONS:

   OPTION A - Keep Most Recent + Archive Select Files:
   - Keep the MOST RECENT file (has complete history)
   - Archive 1-2 files per year for backup/verification
   - Delete intermediate files
   - Pros: Minimal storage, still have complete data
   - Cons: Lose ability to see exactly what changed when

   OPTION B - Convert to Incremental Markdown:
   - Create a master markdown file with complete history from most recent XML
   - For each older file, create a small markdown showing only NEW items
   - Keep ONE most recent XML file
   - Pros: Human-readable, clear change tracking, minimal duplication
   - Cons: Initial conversion effort, lose raw XML data

   OPTION C - Keep All XML Files (Current State):
   - Useful only if you need legal/medical verification of exact record state at specific dates
   - Pros: Complete audit trail
   - Cons: High duplication, storage waste, hard to see changes

   RECOMMENDED: Option B (Incremental Markdown) or Option A (Keep Recent + Archive)

5. VALUE OF INCREMENTAL MARKDOWN:
   - HIGH VALUE: Makes it easy to see what changed between visits
   - Easier to search and review than XML
   - Better for sharing with schools, therapists, etc.
   - Can organize by year/category for quick reference
    """)

if __name__ == "__main__":
    main()
