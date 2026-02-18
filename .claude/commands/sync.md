---
description: Sync Obsidian repo - fetch, rebase, commit all changes, and push to master
---

Perform a complete git sync of the Obsidian repository:

1. Fetch latest changes from origin/master
2. Rebase current branch on origin/master
3. Add all changes (including untracked files)
4. Create an intelligent commit message based on what changed:
   - If changes are primarily in `Trips/` folder, use: "update trips documents"
   - If changes are primarily in `Children/` folder, use: "update children documents"
   - If changes are primarily in `Health/` folder, use: "update health documents"
   - If changes are in `Life/` folder, use: "update life journal"
   - If changes are mixed or in other folders, use: "update"
5. Push to origin master

**Important:**
- Check git status first to see what files changed
- Only commit if there are actual changes
- If rebase has conflicts, stop and report the conflicts to the user
- Do not use `--force` when pushing

Execute the git commands in the `/Users/ychen2/Obsidian` directory.
