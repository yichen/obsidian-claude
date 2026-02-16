---
description: Sync materialized views for daily journal sections
---

Synchronize the Journal view files (materialized views) with entries from daily notes.

## How It Works

Daily notes in `Journal/Daily/` contain sections tagged with view references. For example:

```markdown
## Parenting
[[Journal/Parenting Log]]
Content here...
```

This skill scans all daily notes, finds these tagged sections, and updates the corresponding view files with embeds pointing back to each section.

## Instructions

1. **Scan all daily notes** in `Journal/Daily/**/*.md`

2. **For each daily note**, extract the date from the filename (format: `YYYY-MM-DD.md`) and find all sections with view tags:
   - Pattern: `## SectionHeader` followed by `[[Journal/ViewName]]` on the next non-empty line
   - Extract: the section header name and the view name

3. **Build a mapping** of ViewName -> list of (date, section_header) tuples

4. **For each view**, generate and write the view file at `Journal/ViewName.md`:
   - Sort entries by date descending (newest first)
   - Generate one embed per entry: `![[YYYY-MM-DD#SectionHeader]]`
   - Each embed on its own line
   - No extra content - just the embeds

5. **Report results**: List which view files were updated and how many entries each contains

## Example

If daily notes contain:
- `2026-01-20.md` with `## Parenting` tagged `[[Journal/Parenting Log]]`
- `2026-01-21.md` with `## Parenting` tagged `[[Journal/Parenting Log]]`
- `2026-01-21.md` with `## Anxiety` tagged `[[Journal/Anxiety]]`

Then after running:
- `Journal/Parenting Log.md` contains:
  ```
  ![[2026-01-21#Parenting]]
  ![[2026-01-20#Parenting]]
  ```
- `Journal/Anxiety.md` contains:
  ```
  ![[2026-01-21#Anxiety]]
  ```

## Important Notes

- Create view files if they don't exist
- Completely replace existing view file content (don't append)
- Use only the date portion in embeds (e.g., `2026-01-20`), not the full path
- Handle view names with spaces (e.g., "Parenting Log")
