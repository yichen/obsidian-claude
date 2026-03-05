# /commit — Commit and push to main

Commit all local changes in the Obsidian vault and push to the remote `main` branch.

## Arguments

- `$ARGUMENTS` — Optional commit message. If empty, auto-generate one from the changes.

## Workflow

### Step 1: Check status

Run `git status` (never use `-uall`) and `git diff --stat` to see what changed.

If there are no changes (no untracked files, no modifications), tell the user "Nothing to commit" and stop.

### Step 2: Stage all changes

Run `git add -A` to stage everything. This is a personal Obsidian vault — there are no secrets to worry about.

### Step 3: Create commit message

- If `$ARGUMENTS` is provided, use it as the commit message.
- Otherwise, generate a short commit message summarizing the changes (e.g., "Update daily journal and trip notes", "Add new LeetCode entries").

### Step 4: Commit

Create the commit. Do NOT include a Co-Authored-By line — this is a personal vault.

### Step 5: Push to main

Push to the remote `main` branch:

```
git push origin main
```

### Step 6: Confirm

Display:
- Number of files changed
- The commit message
- Confirmation that it was pushed to `origin/main`
