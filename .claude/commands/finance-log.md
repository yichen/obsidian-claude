---
description: Log and track finance-related activities (FSA claims, reimbursements, applications, etc.)
---

# /finance-log — Finance Activity Tracker

Track financial actions that need follow-up: reimbursement requests, applications, disputes, payments, etc.

**Log file**: `Finance/activity-log.md`

## Arguments

- `$ARGUMENTS` — the action description, a subcommand, or empty

## Workflow

### Parse the input

Determine what the user wants:

1. **No arguments or "status" or "pending"** → Show all PENDING entries from the log
2. **"all"** → Show all entries (all statuses)
3. **"update \<id\> \<status\> [note]"** → Update an existing entry's status
4. **Anything else** → Log a new PENDING activity

### For new entries

1. Read `Finance/activity-log.md` (create if it doesn't exist)
2. Determine the next ID: scan existing entries for the highest `#nnn` and increment
3. Prepend a new entry at the top of the file (reverse chronological) using this format:

```markdown
### #001 | 2026-03-01 | PENDING
**FSA Dependent Care Reimbursement Request**
- Submitted $2,400 claim for Q1 2026
- Expected processing: 5-10 business days

---
```

4. Confirm what was logged

### For status updates

1. Read the log file
2. Find the entry matching `#<id>`
3. Change the status tag (PENDING → APPROVED / DENIED / COMPLETED / CANCELLED)
4. Append an update line with the date and any note:
```markdown
- **2026-03-15 → APPROVED**: Funds deposited to checking
```
5. Confirm the update

### For status queries

1. Read the log file
2. Filter entries by status (PENDING for default, or all)
3. Display a summary table:

```
| # | Date | Status | Description |
|---|------|--------|-------------|
| 003 | 2026-03-01 | PENDING | FSA dependent care reimbursement |
| 001 | 2026-02-15 | APPROVED | W-4 extra withholding update |
```

## Valid Statuses

| Status | Meaning |
|--------|---------|
| PENDING | Submitted/initiated, awaiting outcome |
| APPROVED | Request was approved |
| DENIED | Request was denied |
| COMPLETED | Action finished (no approval needed) |
| CANCELLED | Withdrawn or no longer relevant |

## Notes

- IDs are sequential integers, zero-padded to 3 digits (#001, #002, ...)
- Entries are reverse chronological (newest first)
- Each entry separated by `---`
- Keep descriptions concise — 1 bold title line + 1-3 bullet details
- When logging, ask the user for any missing context (amount, provider, deadline) if the input is vague
