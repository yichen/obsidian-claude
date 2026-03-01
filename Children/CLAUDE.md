# Children's Educational Records

This directory contains educational records, assessments, and progress reports for Laurence Martin Chen and Ruby Martin Chen (twins, born Nov 9, 2017).

## TODO - Action Items
**IMPORTANT: Always display this TODO section at the start of every session in this project.**

- [ ] Follow up with school about 504 plan modification for Ruby and Laurence based on the September 2025 iReady assessment
  - Draft emails saved in: `504-plan-request-ruby.md` and `504-plan-request-laurence.md`
  - Key concerns: Ruby's reading comprehension decline (82nd → 63rd percentile); Laurence's informational text comprehension + behavioral issues

---

## Directory Structure

### Naming Conventions
- **Date-prefixed folders**: `YYYY-MM-DD_Description` format (e.g., `2025-01-31_Report-Card`)
- **Date-prefixed files**: Files within folders follow similar date conventions (e.g., `ruby-2025-01-31-report-card.pdf`)
- **School-specific folders**: Named by institution (e.g., `InternationalFriendsSchool`)

### Current Organization
```
Children/
├── YYYY-MM-DD_Report-Card/          # Semester report cards
├── YYYY-MM-DD_iReady/               # iReady assessment reports
├── neuropsych report/               # Neuropsychological evaluations
├── 504-plans/                       # 504 plan documents and research
├── Personal Health Record (PHR)/    # Machine-readable health records from hospital
├── coparenting/                     # Coparenting schedule, custody, finances, conflicts with Sheri
├── [SchoolName]/                    # Historical records by school
├── parenting-schedule-2-2-5-5.md    # Custody schedule (2-2-5-5 pattern)
├── NOTES.md                         # Periodic analysis and summaries
└── CLAUDE.md                        # This file
```

## Document Types

### Assessment Reports
- **iReady Assessments**: Diagnostic assessments for reading and math
  - Contains scale scores, percentile rankings, and domain-specific performance
  - Typically administered 2-3 times per school year

- **Report Cards**: Semester or trimester academic progress reports
  - Academic performance by subject area
  - Behavioral and social-emotional learning indicators
  - Teacher comments and observations

- **Neuropsychological Reports**: Comprehensive evaluations (located in `neuropsych report/`)
  - `2025-03-18 Laurence neuropsych report(2024.12.12).md` - Laurence's full evaluation
  - `2025-03-18 Ruby neuropsych report (2024.12.12).md` - Ruby's full evaluation
  - Complete test results and scores (WISC-V, WIAT-4, ADOS-2, RCFT, BASC-3, Vineland-3)
  - Diagnostic impressions and DSM-5-TR criteria
  - Developmental, medical, and academic history
  - IEP/504 plan accommodation recommendations
  - Therapy and medication recommendations

- **504 Plan Documents** (located in `504-plans/`)
  - `emails/` - Email conversation records with the school
    - Each markdown file contains one email thread
    - File naming convention: `YYYY-MM-DD_email-thread-title.md`
  - `docs/` - Markdown versions of official documents (extracted from files/)
    - Use these for reading and analysis
    - Contains PDFs, DOCX, and PPTX files converted to markdown format
  - `files/` - Original raw files (PDFs, DOCX, PPTX)
    - Original source documents from the school district
    - Do not use directly; refer to extracted markdown versions in docs/ instead
  - Root level - Research findings, reference documents, and other 504-related materials
  - **Important:** Always use the markdown files in `docs/` folder rather than the raw files in `files/` folder

- **Personal Health Records (PHR)** (located in `Personal Health Record (PHR)/`)
  - **Structure (converted to markdown for easy access):**
    - `Laurence/`
      - `master-medical-record.md` - Complete immunizations, medications, problems/diagnoses, allergies
      - `encounters/` - Individual visit summaries (one per encounter)
      - `backup-xml/` - Original C-CDA XML files from Virginia Mason hospital
    - `Ruby/`
      - `master-medical-record.md` - Complete immunizations, medications, problems/diagnoses, allergies
      - `encounters/` - Individual visit summaries (one per encounter)
      - `backup-xml/` - Original C-CDA XML files from Virginia Mason hospital

  - **Using the PHR data:**
    - **For cumulative medical history:** Read `master-medical-record.md`
    - **For specific visits:** Browse `encounters/` folder (files named `YYYY-MM-DD-reason.md`)
    - **For original data:** XML files in `backup-xml/` (C-CDA format)

  - **Important notes:**
    - Master records are extracted from most recent hospital download
    - Each XML file contains complete historical data (75% duplication across files)
    - Converted to markdown to enable cross-referencing with 504 plans and educational records
    - Vital signs (height, weight, BMI) may only appear in well-child visit encounters
    - To update: Download new XML from hospital, re-run conversion script (stored in backup-xml/)

- **Coparenting Documents** (located in `coparenting/`)
  - **Purpose:** Documents related to coparenting coordination with Sheri (children's mother)
  - **Contents:**
    - Custody schedules and calendars
    - Parenting schedule (2-2-5-5 pattern) details
    - Financial agreements and expense sharing
    - Communication records about scheduling conflicts
    - Documentation of coparenting discussions and decisions
  - **When to reference:**
    - Discussing schedule changes or conflicts with Sheri
    - Planning trips or activities that affect custody time
    - Reviewing financial responsibilities for children's expenses
    - Documenting agreements or resolving disputes

### File Formats
- Most documents are in **PDF format**
- Some historical documents may be in `.docx` format

## ⚠️ Mandatory Context for Scheduling & Parenting

**When answering questions about:**
- **Schedules**: Holidays, no-school days, daily timing
- **Custody/Parenting Time**: 2-2-5-5 rotation, exchanges, drop-off times
- **Activities & Camps**: Booking processes, decision-making rules, payment splitting

**You MUST scan ALL files in `Children/coparenting/`**, specifically:
- `parenting-schedule-2-2-5-5.md` (Current custody rotation and routine)
- `2025-05-29-final-parenting-plan.md` (Legal rules for holidays, camps, decision making, and exchanges)

## Usage Guidelines

### For AI Analysis
When analyzing student progress:
1. **Check NOTES.md first** for previous analyses and historical context
2. **Look for date-prefixed folders** matching the assessment period
3. **Compare across time periods** to identify trends
4. **Consider multiple data sources**: report cards, standardized assessments, and teacher feedback
5. **Focus on growth patterns**, not just absolute performance

### Key Analysis Areas
- **Academic performance trends**: Compare semester-to-semester changes
- **Standardized test results**: Track percentile rankings and scale scores
- **Social-emotional development**: Review behavioral indicators
- **Teacher feedback**: Extract actionable insights from comments
- **Strengths and growth areas**: Identify patterns across multiple assessments

## Historical Records

### Schools Attended
- **International Friends School**: Early elementary records (Kindergarten - Grade 1, 2023-24)
- **Endeavour Elementary**: Current school (Grade 1-present, 2024-25)

## Notes and Analysis

- **NOTES.md**: Contains periodic comprehensive analyses with date stamps
  - Review summaries comparing multiple assessment types
  - Longitudinal progress tracking
  - Actionable recommendations for parents and educators

### Latest Progress Reports (September 2025)
- **2025-09-11_iReady/2025-09-laurence-progress.md**: Comprehensive 2-year progress analysis for Laurence
  - Covers Fall 2024 - September 2025
  - Compares iReady assessments, report cards, and neuropsych evaluations
  - Identifies reading comprehension (informational text) as primary area of concern

- **2025-09-11_iReady/2025-09-ruby-progress.md**: Comprehensive 2-year progress analysis for Ruby
  - Covers Fall 2024 - September 2025
  - Compares iReady assessments, report cards, and neuropsych evaluations
  - Identifies critical decline in reading comprehension (literary text) as urgent concern

## Privacy Note
This directory contains sensitive educational records. Handle with appropriate confidentiality.