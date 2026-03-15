---
description: Fetch, rebase, commit, and push all changes to git repo
---

# Git Sync Workflow

This workflow fetches the latest changes, rebases your current work, commits all changes, and pushes to the remote repository.

// turbo-all

1. Run full sync process (Fetch, Commit, Rebase, Push)
```bash
git fetch origin && git add -A && (git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')" || true) && (git pull --rebase origin master || (git diff --name-only --diff-filter=U | xargs -r git checkout --ours && git add -A && GIT_EDITOR=true git rebase --continue)) && git push origin master
```

## Notes

- The `// turbo-all` annotation means all command steps will auto-run without requiring approval
- This workflow is configured for the `master` branch
- If merge conflicts occur during rebase, step 5 automatically resolves them by taking the local (`ours`) version
- The `GIT_EDITOR=true` setting allows rebase to continue without opening an editor
