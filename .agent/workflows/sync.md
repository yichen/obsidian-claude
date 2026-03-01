---
description: Fetch, rebase, commit, and push all changes to git repo
---

# Git Sync Workflow

This workflow fetches the latest changes, rebases your current work, commits all changes, and pushes to the remote repository.

// turbo-all

1. Fetch the latest changes from the remote repository
```bash
git fetch origin
```

2. Stage all changes (new, modified, and deleted files)
```bash
git add -A
```

3. Commit the changes with a timestamp message
```bash
git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')"
```

4. Rebase on top of the remote branch
```bash
git pull --rebase origin master
```

5. Auto-resolve any rebase conflicts by taking the local version
```bash
# Resolve all conflicted files by keeping the local version
git diff --name-only --diff-filter=U | xargs -r git checkout --ours
# Stage the resolved files
git add -A
# Continue the rebase (ignore errors if already finished)
GIT_EDITOR=true git rebase --continue || true
```

6. Push the changes to the remote repository
```bash
git push origin master
```

## Notes

- The `// turbo-all` annotation means all command steps will auto-run without requiring approval
- This workflow is configured for the `master` branch
- If merge conflicts occur during rebase, step 5 automatically resolves them by taking the local (`ours`) version
- The `GIT_EDITOR=true` setting allows rebase to continue without opening an editor
