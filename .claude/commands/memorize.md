# /memorize — Consolidate Session Learnings

You are a memory consolidation agent. Your job is to extract learnings from this conversation and persist them to the project memory system.

## Arguments

- `$ARGUMENTS` — Optional explicit note to memorize. If provided, store this note directly. If empty, extract learnings from the conversation.

## Workflow

### Step 1: Read Current State

Read these files (skip if they don't exist):
1. `memory/MEMORY.md` — current core memory
2. `memory/$(date +%Y-%m-%d).md` — today's daily log (may not exist yet)

### Step 2: Extract Learnings

If `$ARGUMENTS` is provided:
- Use the explicit note as the primary learning to store

If `$ARGUMENTS` is empty:
- Review the conversation and extract entries for each category:

| Category | What to Extract | Example |
|----------|----------------|---------|
| Key Learnings | Technical gotchas, root causes, "aha" moments | "Obsidian embeds don't work with relative paths from subfolders" |
| Decisions | Architecture/tool choices with rationale | "Using materialized views pattern for daily log aggregation" |
| File Locations | Important paths discovered | "Parenting schedule: `Children/parenting-schedule-2-2-5-5.md`" |
| User Preferences | Behavioral corrections, workflow preferences | "Prefers investigation and data before recommendations" |
| Active Context | Ongoing work, open threads (with status marker) | "Reorganizing Health folder structure `(active)`" |

### Step 3: Deduplicate

Compare extracted items against existing `memory/MEMORY.md` entries:
- Skip items that are already recorded (same fact, even if worded differently)
- Update items where the new version has more detail or corrects the existing entry
- Flag items that contradict existing entries (present both, ask user to resolve)

### Step 4: Update MEMORY.md

Add new entries to the appropriate sections in `memory/MEMORY.md`:
- Each Key Learning entry includes a topic heading with date: `### Topic Name (YYYY-MM-DD)`
- Each Decision entry includes rationale
- Keep entries concise (2-5 bullet points per topic)
- Maintain reverse-chronological order within sections (newest first)
- **User Preferences** go under `## User Preferences` — these are behavioral corrections (things Claude should always/never do). Deduplicate against existing entries before adding.
- **Active Context** items include a status marker: `(active)`, `(COMPLETED)`, or `(stale — prune candidate)`

After updating, check the line count:
- If >500 lines: warn the user and suggest running `/memory-compress`
- If >800 lines: strongly recommend running `/memory-compress` before next session

### Step 5: Create/Append Daily Log

Write to `memory/YYYY-MM-DD.md` using today's date.

If the file already exists, **append** a new session section. If it doesn't exist, create it.

Use this format for each session entry:

```
## HH:MM — Brief Description

**What was done**:
- [bullet list of activities]

**What was learned**:
- [raw detail, more verbose than MEMORY.md entries]

**What was decided**:
- [decisions + rationale]

**Open threads**:
- [unfinished work, things to follow up on]

**Files touched**:
- [paths + what changed]

**Retain**:
- [2-5 self-contained narrative facts that would be useful if encountered out of context]
- Each fact should standalone — include enough context to understand without reading the full entry
- Focus on insights, corrections, and decisions — not routine actions

---
```

Use the current time (PST) for the `HH:MM` header.

### Step 6: Report

Output a **concise** summary. **Only include sections that have non-zero items.** Omit any section where the count is zero or there is nothing to report.

Possible sections (include only if applicable):
- **Added** — what was added to MEMORY.md (always show if anything was added)
- **Updated** — what was modified in existing entries
- **Skipped** — duplicates already recorded
- **Daily log** — confirm the file path (always show)
- **MEMORY.md** — line count (always show; warn if >500)

## Important Notes

- All timestamps should use PST (America/Los_Angeles)
- Keep MEMORY.md entries concise — daily logs hold the verbose details
- When in doubt about whether something is worth remembering, include it — `/memory-compress` will clean up later
- Active Context items should include a date so they can be pruned when stale
