# Project Context

**⚠️ IMPORTANT: This file is the SINGLE SOURCE OF TRUTH for this Obsidian vault.**
- **Always read this file first** at the start of any conversation or task
- **Do not maintain duplicate context files** - this is the only instruction file needed
- When the user mentions "CLAUDE.md", they mean this root-level file
- This file contains all context, preferences, and instructions for working with this vault

This is my personal Obsidian vault. As such, you'll find Obsidian-related hashtags and content throughout the files.

## File & Directory Naming

- **Never use spaces in new file or directory names.** Use hyphens instead (e.g., `Spring-Break-with-Kids` not `Spring Break with Kids`).
- Reason: User runs Claude Code in Warp terminal, which auto-detects absolute file paths and makes them clickable — but spaces break path detection.
- When outputting file paths, always use the **full absolute path** so Warp can detect and link them.

## Key Information

- My twins are Laurence Martin Chen and Ruby Martin Chen. They were born on Nov 9, 2017.
- **Parenting Schedule**: See [Children/parenting-schedule-2-2-5-5.md](Children/parenting-schedule-2-2-5-5.md) for custody schedule (2-2-5-5 pattern).

## Daily Journal

- **Location**: `Journal/Daily/`
- **Format**: One note per day using Obsidian's daily note feature (filename format: `YYYY-MM-DD.md`)
- **Contents**: Mixed topics including health, mental health, kids, coparenting, and general life events
- **Finding date-related context**: When looking for events or context from a specific date, read the corresponding daily note at `Journal/Daily/YYYY-MM-DD.md`

### Materialized Views

Daily notes can contain sections tagged with view references to create "materialized views" - aggregated views of related content across multiple daily notes.

**How to tag a section in a daily note:**
```markdown
## Parenting
[[Journal/Parenting Log]]
Your content here...
```

**View files** (e.g., `Journal/Parenting Log.md`) contain embeds that pull in each tagged section:
```markdown
![[2026-01-21#Parenting]]
![[2026-01-20#Parenting]]
```

**To sync views with daily notes**, run `/sync-notes`. This scans all daily notes, finds tagged sections, and updates the corresponding view files with embeds in reverse chronological order (newest first).

## 🧠 Context Routing (Auto-Load Rules)

**Detailed Instructions are located in subfolders. You MUST read the specific local CLAUDE.md when the topic matches:**

1.  **Trips & Travel**
    - **Triggers**: Words like "Trip", "Travel", "Hike", "Itinerary", "Packing", "Flight", "Hotel", or specific destinations.
    - **Action**: Read `Trips/CLAUDE.md` immediately. It contains strict safety protocols, packing lists, and itinerary formats.

2.  **Children & Parenting**
    - **Triggers**: "Laurence", "Ruby", "School", "Kids", "Parenting".
    - **Action**: Read `Children/CLAUDE.md`.

3.  **Date-Specific Context**
    - **Triggers**: Specific dates, "yesterday", "last week", "on [date]", or questions about what happened when.
    - **Action**: Read the corresponding daily note(s) at `Journal/Daily/YYYY-MM-DD.md`. For date ranges, read multiple daily notes.

4.  **Implementation Intentions & Mental Protocols**
    - **Triggers**: "Implementation intention", "If-then plan", "Protocol", "Anxiety plan", "Grey rock".
    - **Action**: Read `Life/Implementation Intentions.md`.

5.  **Finance & Income**
    - **Triggers**: "Spending", "Budget", "Payslip", "Salary", "Income", "W-4", "Withholding", "Tax", "401k", "Cash flow", "Credit card statement", "Amazon orders".
    - **Action**: Read `Finance/CLAUDE.md`. It documents the finance database schema, data sources, and query patterns.
    - **Tax commands**: Use `/tax` for all tax operations (ingestion, validation, 1040 computation, issues tracking). `/tax` is the unified front-end; `/ingest-tax` still works for ingestion only.

6.  **Divorce & Legal Requirements**
    - **Triggers**: "Divorce", "Settlement", "Custody", "Child support", "Parenting plan", "Legal", "Court order", "OFW", "OurFamilyWizard", "Sheri" (ex-wife).
    - **Action**: Search `Children/coparenting/` directory. Key documents:
      - `divorce_settlement_agreement.md` - Financial terms, property, spousal maintenance, child support
      - `2025-05-29-final-parenting-plan.md` - Custody schedule, decision-making, communication requirements, travel rules

## Proactive Seasonal Alerts

**Two-stage alert system for China travel during Chinese New Year:**

These rules fire during ANY conversation, not just trip planning. **Core rule: If a school break overlaps with Chinese New Year, ALWAYS travel to China** — either with the kids (if custody) or solo (if kids are with mom).

### Stage 1: School Calendar Check (September-October)
**Trigger**: Current date is in September or October.
**Action**: Proactively ask the user:
> "Has the kids' school calendar been released for this year? Let's check if any breaks overlap with Chinese New Year. If they do, you should plan a China trip — with the kids if you have custody, or solo if you don't."

Once the user provides break dates, check against:
- **Chinese New Year** (Spring Festival): varies Jan 21 – Feb 20 each year
  - 2027: Feb 6 | 2028: Jan 26 | 2029: Feb 13 | 2030: Feb 3 | 2031: Jan 23
- **Custody**: Check parenting schedule to determine if kids are with dad during the overlapping break
  - **Kids with dad** → Plan family China trip
  - **Kids with mom** → Plan solo China trip
- Create a note in `Trips/PLAN-FUTURE/` documenting the plan for that school year

### Stage 2: Pre-Break Reminder (3 months before the break)
**Trigger**: Current date is ~3 months before a school break that overlaps with Chinese New Year.
**Action**: Proactively mention:
> "Reminder: The kids' [break name] ([dates]) overlaps with Chinese New Year. Per your rule, you should travel to China. [With kids / Solo] based on custody schedule. Now is the time to book flights and accommodation. See Trips/Lessons Learned.md for China travel tips."

**Key insight (Feb 2026)**: School breaks that overlap Chinese New Year = always go to China. One-week breaks are viable for international travel. Don't assume short breaks = domestic only. Other families routinely do this.

## Session Memory

Claude Code maintains a three-tier memory system at `memory/` in the vault root. This directory syncs across machines via Obsidian Sync. The Claude Code auto-memory path (`~/.claude/projects/.../memory/`) is a symlink to this location.

### Memory Tiers

| Tier | Location | Purpose | Retention | Loaded |
|------|----------|---------|-----------|--------|
| Core Memory | `memory/MEMORY.md` | Key learnings, user preferences, active context | **Evergreen** — never auto-pruned | Every session start |
| Topic Details | `memory/topics/<slug>.md` | Extracted deep-dives for topics that outgrew MEMORY.md | **Evergreen** — permanent reference | On demand |
| Daily Logs | `memory/YYYY-MM-DD.md` | Verbose session-by-session activity logs with Retain facts | **Ephemeral** — archived after 30 days by `/memory-compress` | Today + yesterday at session start |
| Archive | `memory/archive/YYYY-MM-DD.md` | Old daily logs preserved for manual reference | Cold storage — never loaded automatically | Manual only |

### MEMORY.md Structure

| Section | Purpose |
|---------|---------|
| `# Key Learnings` | Technical gotchas, root causes, architecture decisions (### per topic with date) |
| `## User Preferences` | Behavioral corrections — things Claude should always/never do in this vault |
| `# Active Context` | Ongoing work with status markers: `(active)`, `(COMPLETED)`, `(stale — prune candidate)` |

### Session Start Protocol

At the beginning of every session, read these files (skip any that don't exist):
1. `memory/MEMORY.md` — full file, contains all core knowledge
2. `memory/<today's date>.md` — today's daily log for session continuity
3. `memory/<yesterday's date>.md` — yesterday's log for recent context

### Memory Commands

| Command | Purpose |
|---------|---------|
| `/memorize` | Extract learnings from conversation, update MEMORY.md, create/append daily log |
| `/memorize <note>` | Store an explicit note directly |
| `/memory-compress` | Reduce MEMORY.md size by extracting verbose topics and pruning stale entries |

### Other Commands

| Command | Purpose |
|---------|---------|
| `/leetcode` | Log LeetCode daily learnings to `Work/LeetCode/YYYY-MM-DD.md` — captures problem, approach, learnings, mistakes, and time |
| `/sync-notes` | Scan daily notes for tagged sections and update materialized view files in reverse chronological order |

### Guidelines

- **MEMORY.md target**: Under 500 lines. Warn at 500, strongly recommend `/memory-compress` at 800.
- **Active Context**: Use status markers — `(active)`, `(COMPLETED)`, `(stale — prune candidate)`. Prune completed/stale items and items older than 7 days during `/memory-compress`.
- **Topic extraction**: Key Learnings topics exceeding 8 lines should be extracted to `memory/topics/`
- **Daily logs**: Multiple sessions in one day append new `## HH:MM` sections. Each entry ends with a **Retain** section of 2-5 self-contained narrative facts.

---

## Search Strategy

This vault is indexed for semantic search. **Always use semantic search first** when the index is fresh (updated within the last 10 days):

1. Check index status using `mcp__claude-context__get_indexing_status`
2. If the index was updated within the last 10 days, use `mcp__claude-context__search_code` for queries
3. Only fall back to `Grep` for very specific literal string matches if semantic search doesn't yield results

Semantic search is better at understanding conceptual relationships and finding relevant content even when exact keywords don't match.

**Health folder is separately indexed**: The `Health/` folder has its own dedicated index. For health-related queries (medical records, test results, cholesterol, etc.), always use the path `/Users/chen.y/Obsidian/Health` in semantic search to get better results. The separate index prevents health records from being drowned out by the larger volume of career-related documents in the main vault index.

## Indexing Behavior - DO NOT RE-INDEX WITHOUT CHECKING

**⚠️ CRITICAL: ALWAYS check index status BEFORE attempting to index this vault.**

**Rules for indexing this vault:**

1. **MUST run `mcp__claude-context__get_indexing_status` first** before any indexing operation
2. **DO NOT run `mcp__claude-context__index_codebase` unless:**
   - Index doesn't exist (status returns "not indexed"), OR
   - User explicitly requests re-indexing with `force=True`, OR
   - Index is stale (>10 days old for this vault) and user confirms
3. **If index exists and is recent (<10 days):**
   - Inform user that a recent index exists (show last updated date)
   - Ask user to confirm before re-indexing
   - Use the existing index for searches

**Why this matters for this vault:** This Obsidian vault is frequently updated but doesn't change dramatically. Unnecessary re-indexing wastes time and overwrites a perfectly good index. The user typically re-indexes this vault manually every 7-10 days or when significant content changes occur.
