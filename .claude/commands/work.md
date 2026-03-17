# /work — Find and Load a Project

Search memory first (fast), then fall back to folder search. Load all context from the matched project.

## Arguments

- `$ARGUMENTS` — A search term describing the project (e.g., "fairbridge", "rental", "finance llm", "summer camp").

## Workflow

### Step 1: Search Memory First (MANDATORY — do this BEFORE any Glob/Grep/Agent calls)

Memory files are already loaded in context at session start. Search them **without any tool calls**:

1. `memory/MEMORY.md` — scan Active Context and Key Learnings sections
2. Today's and yesterday's daily logs in `memory/`

Look for the search term or synonyms in these already-loaded files. If a folder path is found, skip directly to Step 3. Do NOT proceed to Step 2 unless memory produced zero matches.

### Step 2: Fall Back to Folder Search

**Only if Step 1 produced zero matches.** Search these directories:

1. `Projects/` — Active projects

Search strategy:
- Match folder names first (case-insensitive)
- If no folder name matches, grep file contents
- If exactly 1 match: proceed to Step 3
- If multiple matches: list them and ask the user to pick one
- If no matches: tell the user and suggest similar names if any

### Step 3: Load Context and Summarize

Read all `.md` files in the matched folder (skip `.py`, `.json`, `.yaml`, `.csv` and other non-doc files). Present a status summary:

**1. Header**

```
## [Project Name]
**Folder**: `path/to/folder`
**Status**: [derived from status indicators below]
```

**2. Status detection** (check in order, use first match):

| Indicator | Status |
|-----------|--------|
| `STATUS` file exists in folder | Use its contents verbatim |
| `*_final.md` or `*-final.md` exists | **Completed** — final deliverable ready |
| `MVP-Definition.md` or spec exists with implementation started | **In Progress** |
| `market-research.md` or analysis exists | **Research Complete** |
| Only planning/brief files | **Planning** |
| Empty folder or only a stub | **Not Started** |

**3. Key files** (show as clickable full absolute paths):

```
**Deliverable**: `/full/path/to/main-doc.md`
**Other files**: [list remaining .md files]
```

Only show the deliverable line for the highest-priority file. Don't list it again under "Other files".

**4. Brief summary** — Read the deliverable file's first ~30 lines and produce a 2-3 sentence summary of what the project is about.

**5. Prompt**: "What would you like to do with this?"
