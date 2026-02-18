# /memory-compress — Compress and Clean Project Memory

You are a memory maintenance agent. Your job is to reduce the size of `memory/MEMORY.md` while preserving all important information by extracting details to topic files and pruning stale entries.

## Workflow

### Step 1: Assess Current State

1. Read `memory/MEMORY.md` and count total lines
2. Count lines per section (Key Learnings, Decisions, File Locations, User Preferences, Active Context)
3. List any existing topic files in `memory/topics/`

Report the current state:
```
=== Memory Status ===
Total lines: NNN
  Key Learnings:    NNN lines
  Decisions:        NNN lines
  File Locations:   NNN lines
  User Preferences: NNN lines
  Active Context:   NNN lines

Topic files: N files in memory/topics/
```

### Step 2: Extract Verbose Topics

For each Key Learnings topic that exceeds **8 lines**:

1. Create a topic detail file at `memory/topics/<topic-slug>.md` with the full content
2. Replace the verbose entry in MEMORY.md with a **2-line summary + link**:

**Before** (in MEMORY.md):
```
### Some Verbose Topic (2026-02-10)
- Detail line 1
- Detail line 2
- Detail line 3
- Detail line 4
- Detail line 5
- Detail line 6
- Detail line 7
- Detail line 8
- Detail line 9
```

**After** (in MEMORY.md):
```
### Some Verbose Topic (2026-02-10)
- One-line summary of the key insight
- Details: [memory/topics/some-verbose-topic.md](memory/topics/some-verbose-topic.md)
```

Topic slug format: lowercase, hyphens, no dates (e.g., `obsidian-embeds`, `journal-patterns`).

### Step 3: Prune Active Context

Remove Active Context items where:
- The date is **older than 7 days** from today
- The item has been superseded by a Key Learning or Decision entry

For pruned items:
- If they contain useful learnings not captured elsewhere, move to Key Learnings first
- Then remove from Active Context

### Step 4: Prune Stale Decisions

For Decisions entries **older than 30 days**:
- Check if the decision topic appears in recent daily logs (last 7 days) or Active Context
- If no recent activity: move to `memory/topics/archived-decisions.md` and remove from MEMORY.md
- If still active: keep in MEMORY.md

### Step 5: Deduplicate File Locations

- Remove duplicate paths
- Merge entries that refer to the same location with different descriptions
- Remove paths to files that no longer exist (check with Glob)

### Step 6: Archive Old Daily Logs

Daily logs (`memory/YYYY-MM-DD.md`) are **ephemeral working notes** — their valuable insights should already be captured in MEMORY.md or topic files. Old logs become clutter.

1. List all `memory/YYYY-MM-DD.md` files
2. For each file **older than 30 days** from today:
   a. Scan it for any learnings NOT already in MEMORY.md — if found, extract them to MEMORY.md first
   b. Move the file to `memory/archive/YYYY-MM-DD.md`
3. Create `memory/archive/` directory if it doesn't exist

**Do NOT archive** today's or yesterday's daily logs (they're loaded at session start).

### Step 7: Report

Output a summary:
```
=== Compression Results ===
Before: NNN lines
After:  NNN lines (NN% reduction)

Topics extracted:
  - <topic-slug>: N lines -> 2 lines (saved N lines)

Active Context pruned:
  - <item>: removed (reason)

Decisions archived:
  - <decision>: moved to topics/archived-decisions.md

Daily logs archived:
  - N files moved to memory/archive/ (older than 30 days)
  - N learnings extracted before archiving

Files verified:
  - N paths checked, N removed (not found)
```

## Guidelines

- **Never delete information** — always move to topic files or archive before removing from MEMORY.md
- **Preserve links** — if an entry references a file, keep that reference in both the summary and the detail file
- **Target size**: MEMORY.md should be under 300 lines after compression (aim for 200-300)
- **Topic files have no size limit** — they're loaded on-demand, so verbosity is fine there
